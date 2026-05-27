"""
test_main.py
------------
Pytest unit-test suite for the Fraud Detection FastAPI application.

Test Categories
---------------
1. Health & Liveness endpoint validation
2. Successful inference path (normal and anomalous transactions)
3. Input validation / payload rejection
4. Edge cases and boundary conditions
5. Metrics endpoint availability

Run with:
    pytest tests/test_main.py -v
"""

import os
import sys

# Ensure the project root is on the Python path so that `app` is importable
# regardless of the working directory pytest is invoked from.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.main import app, app_state


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def inject_mock_model():
    """
    Inject a fully-configured mock IsolationForest and StandardScaler into
    the global app_state before each test, then restore original state after.

    This fixture removes the dependency on real serialized artifact files,
    making the test suite hermetically self-contained and deterministic.
    """
    import time
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    # Build a real, trained model on minimal data so isinstance checks pass
    rng = np.random.default_rng(42)
    X = rng.standard_normal((200, 2))

    real_scaler = StandardScaler()
    X_scaled = real_scaler.fit_transform(X)

    real_model = IsolationForest(n_estimators=10, random_state=42, contamination=0.05)
    real_model.fit(X_scaled)

    original_model = app_state.model
    original_scaler = app_state.scaler
    original_startup = app_state.startup_time

    app_state.model = real_model
    app_state.scaler = real_scaler
    app_state.startup_time = time.time()

    yield

    app_state.model = original_model
    app_state.scaler = original_scaler
    app_state.startup_time = original_startup


@pytest.fixture(scope="module")
def client():
    """Return a synchronous TestClient for the FastAPI application."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Helper payloads
# ---------------------------------------------------------------------------

NORMAL_TRANSACTION = {"amount": 45.99, "distance_from_home": 3.5}
SUSPICIOUS_TRANSACTION = {"amount": 4500.00, "distance_from_home": 1200.0}


# ---------------------------------------------------------------------------
# 1. Health Check Endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200_when_model_loaded(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_health_response_schema(self, client):
        response = client.get("/")
        body = response.json()
        assert body["status"] == "healthy"
        assert body["model_loaded"] is True
        assert "model_version" in body
        assert "uptime_seconds" in body
        assert isinstance(body["uptime_seconds"], (int, float))
        assert body["uptime_seconds"] >= 0

    def test_health_returns_503_when_model_not_loaded(self, client):
        original = app_state.model
        app_state.model = None
        try:
            response = client.get("/")
            assert response.status_code == 503
        finally:
            app_state.model = original


# ---------------------------------------------------------------------------
# 2. Prediction Endpoint — Happy Path
# ---------------------------------------------------------------------------

class TestPredictEndpoint:
    def test_predict_returns_200_for_normal_transaction(self, client):
        response = client.post("/predict", json=NORMAL_TRANSACTION)
        assert response.status_code == 200

    def test_predict_returns_200_for_suspicious_transaction(self, client):
        response = client.post("/predict", json=SUSPICIOUS_TRANSACTION)
        assert response.status_code == 200

    def test_predict_response_has_required_fields(self, client):
        response = client.post("/predict", json=NORMAL_TRANSACTION)
        body = response.json()
        required_fields = {
            "is_anomaly",
            "anomaly_score",
            "label",
            "model_version",
            "processing_time_ms",
        }
        assert required_fields.issubset(body.keys()), (
            f"Missing fields: {required_fields - body.keys()}"
        )

    def test_predict_is_anomaly_is_boolean(self, client):
        response = client.post("/predict", json=NORMAL_TRANSACTION)
        assert isinstance(response.json()["is_anomaly"], bool)

    def test_predict_label_is_normal_or_anomaly(self, client):
        response = client.post("/predict", json=NORMAL_TRANSACTION)
        assert response.json()["label"] in ("NORMAL", "ANOMALY")

    def test_predict_label_matches_is_anomaly_flag(self, client):
        response = client.post("/predict", json=NORMAL_TRANSACTION)
        body = response.json()
        if body["is_anomaly"]:
            assert body["label"] == "ANOMALY"
        else:
            assert body["label"] == "NORMAL"

    def test_predict_anomaly_score_is_float(self, client):
        response = client.post("/predict", json=NORMAL_TRANSACTION)
        assert isinstance(response.json()["anomaly_score"], float)

    def test_predict_processing_time_is_positive(self, client):
        response = client.post("/predict", json=NORMAL_TRANSACTION)
        assert response.json()["processing_time_ms"] > 0

    def test_predict_model_version_is_string(self, client):
        response = client.post("/predict", json=NORMAL_TRANSACTION)
        assert isinstance(response.json()["model_version"], str)

    def test_predict_returns_503_when_model_not_loaded(self, client):
        original = app_state.model
        app_state.model = None
        try:
            response = client.post("/predict", json=NORMAL_TRANSACTION)
            assert response.status_code == 503
        finally:
            app_state.model = original


# ---------------------------------------------------------------------------
# 3. Input Validation
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_negative_amount_rejected(self, client):
        payload = {"amount": -10.0, "distance_from_home": 5.0}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_zero_amount_rejected(self, client):
        payload = {"amount": 0.0, "distance_from_home": 5.0}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_amount_exceeding_max_rejected(self, client):
        payload = {"amount": 2_000_000.0, "distance_from_home": 5.0}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_negative_distance_rejected(self, client):
        payload = {"amount": 100.0, "distance_from_home": -5.0}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_distance_exceeding_max_rejected(self, client):
        payload = {"amount": 100.0, "distance_from_home": 25_000.0}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_missing_amount_field_rejected(self, client):
        payload = {"distance_from_home": 10.0}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_missing_distance_field_rejected(self, client):
        payload = {"amount": 150.0}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_empty_body_rejected(self, client):
        response = client.post("/predict", json={})
        assert response.status_code == 422

    def test_non_numeric_amount_rejected(self, client):
        payload = {"amount": "not_a_number", "distance_from_home": 5.0}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_null_amount_rejected(self, client):
        payload = {"amount": None, "distance_from_home": 5.0}
        response = client.post("/predict", json=payload)
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# 4. Edge Cases & Boundary Conditions
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_minimum_valid_amount(self, client):
        """Smallest allowed amount just above zero."""
        response = client.post(
            "/predict", json={"amount": 0.01, "distance_from_home": 0.0}
        )
        assert response.status_code == 200

    def test_maximum_valid_amount(self, client):
        """Largest allowed amount (boundary)."""
        response = client.post(
            "/predict", json={"amount": 1_000_000.0, "distance_from_home": 0.0}
        )
        assert response.status_code == 200

    def test_zero_distance(self, client):
        """Distance of 0 km is valid (transaction at home location)."""
        response = client.post(
            "/predict", json={"amount": 100.0, "distance_from_home": 0.0}
        )
        assert response.status_code == 200

    def test_maximum_valid_distance(self, client):
        """Distance at upper boundary (20,000 km ≈ half Earth circumference)."""
        response = client.post(
            "/predict", json={"amount": 100.0, "distance_from_home": 20_000.0}
        )
        assert response.status_code == 200

    def test_high_precision_float_inputs(self, client):
        """Ensure high-precision floats are accepted without precision errors."""
        response = client.post(
            "/predict",
            json={"amount": 123.456789, "distance_from_home": 78.91011121314},
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 5. Metrics Endpoint
# ---------------------------------------------------------------------------

class TestMetricsEndpoint:
    def test_metrics_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type_is_prometheus(self, client):
        response = client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_contains_request_counter(self, client):
        client.get("/")  # Ensure at least one request has been made
        response = client.get("/metrics")
        assert "fraud_api_requests_total" in response.text

    def test_metrics_contains_model_loaded_gauge(self, client):
        response = client.get("/metrics")
        assert "fraud_model_loaded" in response.text


# ---------------------------------------------------------------------------
# 6. Model Info Endpoint
# ---------------------------------------------------------------------------

class TestModelInfoEndpoint:
    def test_model_info_returns_200(self, client):
        response = client.get("/model/info")
        assert response.status_code == 200

    def test_model_info_response_schema(self, client):
        response = client.get("/model/info")
        body = response.json()
        assert body["model_type"] == "IsolationForest"
        assert "model_version" in body
        assert body["feature_count"] == 2
        assert "amount" in body["features"]
        assert "distance_from_home" in body["features"]

    def test_model_info_returns_503_when_model_not_loaded(self, client):
        original = app_state.model
        app_state.model = None
        try:
            response = client.get("/model/info")
            assert response.status_code == 503
        finally:
            app_state.model = original
