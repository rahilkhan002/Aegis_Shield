# MLOps Fraud Detection Pipeline

> **Enterprise-grade, end-to-end automated ML deployment pipeline** — from Isolation Forest model training to a live, monitored Kubernetes microservice, driven by a Jenkins CI/CD pipeline with DevSecOps controls.

---

## Architecture Overview

```
Git Push
   │
   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  Jenkins CI/CD Pipeline                                                   │
│                                                                           │
│  Checkout → Bandit SAST → pytest → Docker Build → Registry Push → k8s   │
└──────────────────────────────────────────────────────────────────────────┘
                                               │
                          ┌────────────────────┘
                          ▼
              ┌───────────────────────────┐
              │  Minikube (Kubernetes)     │
              │                           │
              │  ┌──────────────────────┐ │
              │  │  Pod 1 (FastAPI)     │ │◄── NodePort :30800
              │  └──────────────────────┘ │
              │  ┌──────────────────────┐ │
              │  │  Pod 2 (FastAPI)     │ │
              │  └──────────────────────┘ │
              └───────────────────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       Prometheus :9090          Grafana :3000
       (scrapes /metrics)   (visualises metrics)
```

## Project Structure

```
mlops-fraud-pipeline/
│
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI server — /predict, /metrics, health probes
│   └── model.py            # IsolationForest training + joblib serialization
│
├── tests/
│   └── test_main.py        # 30+ pytest tests covering all endpoints
│
├── config/
│   └── prometheus.yml      # Prometheus scrape targets
│
├── requirements.txt        # Pinned Python 3.10+ dependencies
├── Dockerfile              # Secure multi-stage build (non-root, AMD64)
├── deployment.yaml         # Kubernetes: Deployment + Service + HPA
├── Jenkinsfile             # 7-stage declarative CI/CD pipeline
├── .gitignore
└── .dockerignore
```

---

## Prerequisites

| Tool            | Version   | Purpose                              |
|-----------------|-----------|--------------------------------------|
| Python          | ≥ 3.10    | Application runtime                  |
| Docker Desktop  | ≥ 4.x     | Container engine (Windows)           |
| Minikube        | ≥ 1.35    | Local Kubernetes cluster             |
| kubectl         | ≥ 1.29    | Cluster management CLI               |
| Jenkins         | ≥ 2.440   | CI/CD automation server              |

---

## Quick Start

### 1 · Bootstrap the environment

```powershell
# Clone the repository and enter the project
cd mlops-fraud-pipeline

# Install Python dependencies into a virtual environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2 · Train and serialise the model locally

```powershell
python -m app.model
# Outputs: model.pkl and scaler.pkl in the project root
```

### 3 · Run the API locally

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Test the API:
```powershell
# Health check
curl http://localhost:8000/

# Inference — normal transaction
curl -X POST http://localhost:8000/predict `
     -H "Content-Type: application/json" `
     -d '{"amount": 45.99, "distance_from_home": 3.5}'

# Inference — suspicious transaction
curl -X POST http://localhost:8000/predict `
     -H "Content-Type: application/json" `
     -d '{"amount": 4800.00, "distance_from_home": 1350.0}'
```

### 4 · Run unit tests

```powershell
pytest tests/ -v
```

### 5 · Build the Docker image

```powershell
docker build --platform linux/amd64 -t fraud-detection-api:latest .
```

The multi-stage build will:
1. Install all Python dependencies into an isolated venv
2. Train the IsolationForest and serialise `model.pkl` + `scaler.pkl`
3. Copy only the venv and artifacts into a minimal runtime image
4. Run the server as non-root user `appuser` (UID 1001)

### 6 · Start Minikube

```powershell
# Start with Docker driver (recommended on Windows)
minikube start --driver=docker --memory=4096 --cpus=2

# Enable the metrics server (required for HPA)
minikube addons enable metrics-server

# Get the cluster IP (needed for Prometheus config)
minikube ip
```

### 7 · Start a local Docker registry

```powershell
docker run -d -p 5000:5000 --name registry registry:2

# Push the image to the local registry
docker tag fraud-detection-api:latest localhost:5000/fraud-detection-api:latest
docker push localhost:5000/fraud-detection-api:latest
```

### 8 · Deploy to Kubernetes

```powershell
kubectl apply -f deployment.yaml

# Watch the rollout
kubectl rollout status deployment/fraud-detection-deployment -n mlops

# Check pod health
kubectl get pods -n mlops -o wide

# Get the service URL
minikube service fraud-detection-svc -n mlops --url
# → http://192.168.49.2:30800
```

### 9 · Start Prometheus

Update `config/prometheus.yml` with your actual Minikube IP, then:

```powershell
docker run -d `
  --name prometheus `
  -p 9090:9090 `
  -v "${PWD}/config/prometheus.yml:/etc/prometheus/prometheus.yml" `
  prom/prometheus:latest
```

Access: http://localhost:9090

### 10 · Start Grafana

```powershell
docker run -d `
  --name grafana `
  -p 3000:3000 `
  -e "GF_SECURITY_ADMIN_PASSWORD=admin" `
  grafana/grafana:latest
```

Access: http://localhost:3000 (admin / admin)

**Add Prometheus as a Data Source:**
1. Settings → Data Sources → Add data source → Prometheus
2. URL: `http://host.docker.internal:9090`
3. Save & Test

**Recommended Grafana Panels:**

| Metric | PromQL |
|--------|--------|
| Total predictions/min | `rate(fraud_predictions_total[1m]) * 60` |
| Anomaly rate % | `rate(fraud_predictions_total{result="anomaly"}[5m]) / rate(fraud_predictions_total[5m]) * 100` |
| p99 inference latency | `histogram_quantile(0.99, rate(fraud_prediction_latency_seconds_bucket[5m]))` |
| Request rate | `rate(fraud_api_requests_total[1m])` |
| Model loaded status | `fraud_model_loaded` |

### 11 · Set up Jenkins

```powershell
# Run Jenkins in Docker with Docker-in-Docker socket access
docker run -d `
  --name jenkins `
  -p 8080:8080 -p 50000:50000 `
  -v jenkins_home:/var/jenkins_home `
  -v /var/run/docker.sock:/var/run/docker.sock `
  jenkins/jenkins:lts-jdk17
```

Access: http://localhost:8080

**Post-install steps:**
1. Retrieve the initial admin password: `docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword`
2. Install suggested plugins
3. Create a new Pipeline job pointing to your Git repository
4. Set Script Path to `Jenkinsfile`
5. Trigger a build — the pipeline handles everything from checkout to deployment.

---

## API Reference

### `GET /`
Health check — used by Kubernetes liveness and readiness probes.

```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "1.0.0",
  "uptime_seconds": 142.5
}
```

### `POST /predict`
Score a transaction for anomaly (fraud) probability.

**Request:**
```json
{
  "amount": 4800.00,
  "distance_from_home": 1350.0
}
```

**Response:**
```json
{
  "is_anomaly": true,
  "anomaly_score": -0.312847,
  "label": "ANOMALY",
  "model_version": "1.0.0",
  "processing_time_ms": 1.243
}
```

### `GET /metrics`
Prometheus scrape endpoint (text exposition format).

### `GET /model/info`
Returns model metadata for operational audit.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **IsolationForest** | Unsupervised — no labelled fraud data required; robust on high-dimensional tabular data |
| **StandardScaler in pipeline** | Amount (USD) and distance (km) have very different magnitudes; normalising improves tree split quality |
| **Multi-stage Dockerfile** | Keeps the runtime image lean (~200MB vs ~800MB); build tools don't ship to production |
| **Non-root container user** | Principle of least privilege — prevents container escape → host escalation |
| **Kubernetes HPA** | Automatically scales 2→5 replicas on CPU load without manual intervention |
| **Rolling update (maxUnavailable: 0)** | Zero-downtime deployments; old pods stay alive until new ones pass readiness probes |
| **Bandit HIGH severity gate** | CI fails on HIGH severity findings only — avoids false-positive noise from LOW/MEDIUM |
| **Automatic rollback on deploy failure** | `kubectl rollout undo` is called in the Jenkins `post { failure }` block |

---

## Port Reference

| Service | Port | Access URL |
|---------|------|-----------|
| FastAPI (local) | 8000 | http://localhost:8000 |
| FastAPI (Minikube NodePort) | 30800 | http://\<minikube-ip\>:30800 |
| Jenkins | 8080 | http://localhost:8080 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |
| Local Docker Registry | 5000 | http://localhost:5000 |
