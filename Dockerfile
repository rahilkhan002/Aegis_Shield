# =============================================================================
# Dockerfile — MLOps Fraud Detection API
# =============================================================================
#
# Strategy: Multi-stage build
#   Stage 1 (builder): Install all dependencies into an isolated virtual env
#                      and pre-train the model artifacts.
#   Stage 2 (runtime): Minimal, non-root production image — copies only the
#                      venv and artifacts from the builder stage.
#
# Target architecture: linux/amd64 (x86_64) — compatible with Minikube on
# Windows/Docker Desktop and standard CI runners.
#
# Security hardening applied:
#   - Non-root user `appuser` (UID 1001)
#   - Read-only virtual-env layer
#   - No build tools in the final image
#   - Pinned base image digest via explicit tag
# =============================================================================

# ── Stage 1: Builder ─────────────────────────────────────────────────────────
FROM python:3.10-slim AS builder

# Metadata labels (OCI standard)
LABEL org.opencontainers.image.title="fraud-detection-api"
LABEL org.opencontainers.image.description="MLOps Intelligent Fraud Detection & Anomaly platform"
LABEL org.opencontainers.image.version="2.0.0"

# Prevent Python from writing .pyc files and enable unbuffered stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Isolate pip from the system Python
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Copy only the dependency manifest first to exploit Docker layer caching.
COPY requirements.txt .

# Create a dedicated virtual environment and install all dependencies into it.
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy application source and training pipeline
COPY app/ ./app/
COPY train_pipeline.py .

# Pre-train both Isolation Forest and Supervised Model artifacts
ENV MODEL_DIR=/build
RUN /opt/venv/bin/python -m app.model && \
    /opt/venv/bin/python train_pipeline.py


# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM python:3.10-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Point the running application at the venv
    PATH="/opt/venv/bin:$PATH" \
    # Allow overriding model version at deploy time (injected by Kubernetes)
    MODEL_VERSION="2.0.0" \
    # Artifact directory — must match MODEL_DIR in model.py
    MODEL_DIR=/app

WORKDIR /app

# Create a non-root system user and group for process isolation.
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/false --no-create-home appuser

# Copy the virtual environment from the builder (no build tools included)
COPY --from=builder /opt/venv /opt/venv

# Copy only the application source and serialized model artifacts
COPY --from=builder /build/app ./app
COPY --from=builder /build/model.pkl ./model.pkl
COPY --from=builder /build/scaler.pkl ./scaler.pkl
COPY --from=builder /build/supervised_model.pkl ./supervised_model.pkl

# Transfer ownership of the application directory to the non-root user
RUN chown -R appuser:appgroup /app

# Drop root privileges
USER appuser

# Expose the FastAPI default port
EXPOSE 8000

# Health-check for Docker-native orchestration (Kubernetes uses its own probes)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

# Start Uvicorn with:
#   --host 0.0.0.0        → bind to all interfaces inside the container
#   --port 8000           → standard FastAPI port
#   --workers 2           → one worker per replica CPU budget defined in k8s
#   --log-level info      → structured JSON-compatible logging
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info"]
