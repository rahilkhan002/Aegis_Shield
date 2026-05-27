"""
main.py
-------
FastAPI application entrypoint for the MLOps Fraud Detection microservice.

Endpoints
---------
GET  /               → Health-check (used by Kubernetes liveness/readiness probes)
POST /predict        → Real-time anomaly inference
GET  /metrics        → Prometheus-compatible telemetry scrape endpoint
GET  /model/info     → Returns model metadata for operational observability
"""

import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from typing import Annotated

import numpy as np
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, Field, field_validator

from app.model import load_artifacts

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application State
# ---------------------------------------------------------------------------

# Shared mutable state container — avoids global variables.
class AppState:
    model = None
    scaler = None
    startup_time: float = 0.0
    model_version: str = os.getenv("MODEL_VERSION", "1.0.0")


app_state = AppState()

# ---------------------------------------------------------------------------
# Prometheus Metrics
# ---------------------------------------------------------------------------

REQUEST_COUNT = Counter(
    "fraud_api_requests_total",
    "Total number of HTTP requests received by the fraud detection API.",
    ["method", "endpoint", "http_status"],
)

PREDICTION_COUNT = Counter(
    "fraud_predictions_total",
    "Total number of predictions made, broken down by result.",
    ["result"],  # 'anomaly' or 'normal'
)

PREDICTION_LATENCY = Histogram(
    "fraud_prediction_latency_seconds",
    "End-to-end latency of the /predict endpoint in seconds.",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)

ANOMALY_SCORE_GAUGE = Gauge(
    "fraud_last_anomaly_score",
    "Anomaly score of the most recently processed transaction (lower = more anomalous).",
)

MODEL_INFO_GAUGE = Gauge(
    "fraud_model_loaded",
    "Indicates whether the ML model is currently loaded and ready (1 = ready, 0 = not ready).",
)

# ---------------------------------------------------------------------------
# Lifespan — Model Loading
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Loads the model and scaler artifacts at startup. If artifacts are missing
    or corrupted, the application fails fast with a descriptive error rather
    than silently serving broken predictions.
    """
    logger.info("=== Fraud Detection API starting up ===")
    app_state.startup_time = time.time()

    try:
        app_state.model, app_state.scaler = load_artifacts()
        MODEL_INFO_GAUGE.set(1)
        logger.info(
            "Model v%s loaded successfully. Service is ready.",
            app_state.model_version,
        )
    except FileNotFoundError as exc:
        logger.critical("STARTUP FAILED — Artifact not found: %s", exc)
        MODEL_INFO_GAUGE.set(0)
        # Re-raise so Uvicorn / Kubernetes restarts the pod
        raise RuntimeError(str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        logger.critical("STARTUP FAILED — Artifact load error: %s", exc)
        MODEL_INFO_GAUGE.set(0)
        raise RuntimeError(str(exc)) from exc

    yield  # Application runs here

    logger.info("=== Fraud Detection API shutting down ===")
    MODEL_INFO_GAUGE.set(0)


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Fraud Detection Anomaly API",
    description=(
        "Enterprise-grade, real-time anomaly detection microservice powered by "
        "Isolation Forest. Deployed via Jenkins CI/CD → Docker → Minikube."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Serve static frontend dashboard
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class TransactionRequest(BaseModel):
    """Payload schema for a single transaction to be scored."""

    amount: float = Field(
        ...,
        gt=0,
        le=1_000_000,
        description="Transaction value in USD. Must be positive and ≤ $1,000,000.",
        examples=[250.75],
    )
    distance_from_home: float = Field(
        ...,
        ge=0,
        le=20_000,
        description=(
            "Great-circle distance (km) between the merchant location and the "
            "cardholder's registered home address."
        ),
        examples=[12.4],
    )

    @field_validator("amount")
    @classmethod
    def amount_must_be_finite(cls, v: float) -> float:
        if not np.isfinite(v):
            raise ValueError("'amount' must be a finite number (not NaN or Inf).")
        return round(v, 2)

    @field_validator("distance_from_home")
    @classmethod
    def distance_must_be_finite(cls, v: float) -> float:
        if not np.isfinite(v):
            raise ValueError("'distance_from_home' must be a finite number (not NaN or Inf).")
        return round(v, 4)


class PredictionResponse(BaseModel):
    """Response schema for a scored transaction."""

    is_anomaly: bool = Field(
        ...,
        description="True if the transaction is flagged as anomalous (potential fraud).",
    )
    anomaly_score: float = Field(
        ...,
        description=(
            "Raw anomaly score from IsolationForest. Lower (more negative) values "
            "indicate higher confidence of fraud. Range: approximately -0.5 to +0.5."
        ),
    )
    label: str = Field(
        ...,
        description="Human-readable label: 'ANOMALY' or 'NORMAL'.",
    )
    model_version: str = Field(..., description="Version of the deployed model artifact.")
    processing_time_ms: float = Field(
        ..., description="Server-side inference latency in milliseconds."
    )


# ---------------------------------------------------------------------------
# Middleware — Request Counting
# ---------------------------------------------------------------------------

@app.middleware("http")
async def prometheus_request_middleware(request: Request, call_next):
    """Increment the request counter for every HTTP request."""
    response = await call_next(request)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        http_status=response.status_code,
    ).inc()
    return response


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/",
    summary="Health Check or Showcase Dashboard",
    tags=["Operations", "Frontend"],
    status_code=status.HTTP_200_OK,
)
async def health_check_or_dashboard(request: Request):
    """
    Returns the JSON health check if requested via API (Accept containing application/json),
    otherwise serves the interactive showcase website dashboard (for browsers).
    """
    if app_state.model is None or app_state.scaler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Service is not ready.",
        )

    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        if os.path.exists("app/static/index.html"):
            return FileResponse("app/static/index.html")

    uptime_seconds = round(time.time() - app_state.startup_time, 2)
    return JSONResponse(
        content={
            "status": "healthy",
            "model_loaded": True,
            "model_version": app_state.model_version,
            "uptime_seconds": uptime_seconds,
        }
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict Transaction Anomaly",
    tags=["Inference"],
    status_code=status.HTTP_200_OK,
)
async def predict(transaction: TransactionRequest) -> PredictionResponse:
    """
    Score a single transaction and return an anomaly prediction.

    The raw feature vector ``[amount, distance_from_home]`` is scaled using the
    pre-fitted ``StandardScaler`` before being passed to the ``IsolationForest``.

    - Prediction of ``-1`` → **ANOMALY** (potential fraud).
    - Prediction of ``+1`` → **NORMAL** transaction.
    """
    if app_state.model is None or app_state.scaler is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded. The service is temporarily unavailable.",
        )

    t_start = time.perf_counter()

    try:
        feature_vector = np.array(
            [[transaction.amount, transaction.distance_from_home]], dtype=np.float64
        )
        scaled_features = app_state.scaler.transform(feature_vector)
        raw_prediction: int = int(app_state.model.predict(scaled_features)[0])
        anomaly_score: float = float(
            app_state.model.score_samples(scaled_features)[0]
        )
    except Exception as exc:
        logger.exception("Prediction failed for transaction: %s", transaction.model_dump())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during model inference: {exc}",
        ) from exc

    elapsed_ms = round((time.perf_counter() - t_start) * 1000, 3)
    is_anomaly = raw_prediction == -1
    label = "ANOMALY" if is_anomaly else "NORMAL"

    # Update Prometheus metrics
    PREDICTION_COUNT.labels(result="anomaly" if is_anomaly else "normal").inc()
    PREDICTION_LATENCY.observe(elapsed_ms / 1000)
    ANOMALY_SCORE_GAUGE.set(anomaly_score)

    logger.info(
        "Prediction: amount=%.2f, distance=%.2f → %s (score=%.4f, latency=%.3f ms)",
        transaction.amount,
        transaction.distance_from_home,
        label,
        anomaly_score,
        elapsed_ms,
    )

    return PredictionResponse(
        is_anomaly=is_anomaly,
        anomaly_score=round(anomaly_score, 6),
        label=label,
        model_version=app_state.model_version,
        processing_time_ms=elapsed_ms,
    )


@app.get(
    "/metrics",
    summary="Prometheus Metrics Scrape Endpoint",
    tags=["Operations"],
    response_class=PlainTextResponse,
)
async def metrics() -> PlainTextResponse:
    """
    Expose runtime telemetry in Prometheus text exposition format.

    This endpoint is scraped by the Prometheus server as configured in
    ``config/prometheus.yml``. The Grafana dashboard queries Prometheus to
    visualize these metrics.
    """
    return PlainTextResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get(
    "/model/info",
    summary="Model Metadata",
    tags=["Operations"],
    status_code=status.HTTP_200_OK,
)
async def model_info() -> JSONResponse:
    """Return metadata about the currently loaded model for operational audit trails."""
    if app_state.model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded.",
        )
    model = app_state.model
    return JSONResponse(
        content={
            "model_type": type(model).__name__,
            "model_version": app_state.model_version,
            "n_estimators": model.n_estimators,
            "contamination": model.contamination,
            "max_features": model.max_features,
            "features": ["amount", "distance_from_home"],
            "feature_count": 2,
        }
    )
