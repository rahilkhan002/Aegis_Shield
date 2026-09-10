# SYNOPSIS

## Topic:
### MLOps-Driven Fraud Detection Pipeline with Automated CI/CD, Containerized ML Inference, Infrastructure as Code, and Observability

---

**Department of Computer Science and Engineering**

**Lovely Professional University, Phagwara, Punjab**

**INT378 – Advancements in Cloud and DevOps**

---

| | |
|---|---|
| **Submitted By:** | **Submitted To:** |
| Name: Rahil Khan | Mr. Ajay Kumar Badhan |
| Reg. No: 12309489 | |
| Section: K302312 | |

---

## Table of Contents

1. [Abstract](#1-abstract)
2. [Introduction](#2-introduction)
3. [Problem Statement](#3-problem-statement)
4. [Objective](#4-objective)
5. [Scope of the Project](#5-scope-of-the-project)
6. [System Requirements](#6-system-requirements)
7. [Technologies Used](#7-technologies-used)
8. [System Architecture](#8-system-architecture)
9. [System Modules](#9-system-modules)
10. [DevOps & MLOps Fundamentals Used](#10-devops--mlops-fundamentals-used)
11. [Testing](#11-testing)
12. [Results](#12-results)
13. [Future Enhancements](#13-future-enhancements)
14. [Conclusion](#14-conclusion)

---

## 1. Abstract

This project demonstrates a production-grade, end-to-end MLOps pipeline that carries a machine-learning model — an Isolation Forest trained for real-time credit-card fraud detection — from training through automated build, security scan, containerized deployment and continuous monitoring, so that the engineering emphasis falls on the pipeline infrastructure rather than on application complexity. The application is a FastAPI microservice that accepts transaction features (amount and distance from home), applies a pre-fitted StandardScaler and an Isolation Forest model, and returns a real-time anomaly prediction with confidence scores via a REST API. Around this service, a complete CI/CD pipeline is constructed using Git and Jenkins for continuous integration and delivery, Bandit SAST for static security analysis, pytest for automated testing, Docker multi-stage builds for secure containerization, a local Docker registry for image distribution, Kubernetes (Minikube) for container orchestration with Horizontal Pod Autoscaling, Terraform and Google Cloud Platform for Infrastructure as Code, and Prometheus plus Grafana for full-stack observability. The result is a compact but thorough demonstration of every stage of a modern, secure, MLOps-driven deployment workflow — from a developer's commit to a monitored, auto-scaling, production-ready inference service.

---

## 2. Introduction

Modern machine-learning systems are judged not only by the accuracy of their models but, more critically, by how reliably, securely and reproducibly those models can be trained, versioned, deployed and monitored in production. Industry leaders such as Google, Netflix and Uber invest heavily in MLOps infrastructure — automated pipelines, infrastructure automation, continuous monitoring and model lifecycle management — because these practices, not the models' accuracy metrics alone, are what enable them to ship ML systems safely at scale.

This project is designed around that same principle. Rather than building an elaborate multi-feature application, it uses a focused, well-scoped machine-learning microservice purely as a vehicle to exercise every stage of a professional MLOps pipeline: version control, continuous integration, automated static security analysis, comprehensive unit testing, secure multi-stage containerization, container image registry management, Kubernetes-based orchestration with auto-scaling, Infrastructure as Code with Terraform, and full-stack observability with Prometheus and Grafana.

The chosen application — a Real-Time Fraud Detection API — uses an Isolation Forest (unsupervised anomaly detection) trained on synthetically generated financial transaction data. The model accepts two features — transaction amount (USD) and distance from home (km) — and returns a binary anomaly classification with a continuous anomaly score. Everything of technical significance in this project lies in what happens to that model and service after they are written: how they move automatically and securely from a Git commit to a monitored, auto-scaling deployment on Kubernetes and the cloud.

---

## 3. Problem Statement

Many student and early-stage machine-learning projects focus disproportionate effort on model training and accuracy metrics while treating deployment as an afterthought — the trained model is tested in a Jupyter notebook, manually copied to a server, wrapped in an ad-hoc script, and left unmonitored. This mirrors a widespread real-world failure pattern known as the "last mile of ML" problem, and results in:

- **No repeatable, automated path** from code commit to model deployment — deployments are manual, error-prone and unreproducible.
- **Security checks entirely absent** — no static analysis, dependency scanning or container vulnerability scanning at any stage.
- **No model versioning or artifact management** — it is impossible to roll back to a previous model version if a new deployment degrades.
- **Infrastructure created ad-hoc** — cloud resources provisioned by hand through the console, with no version history, reproducibility or peer review.
- **No observability** — once deployed, there is no visibility into inference latency, prediction distribution, resource consumption or model drift.
- **No auto-scaling or self-healing** — the service cannot recover from pod failure or handle traffic spikes without manual intervention.

This project addresses the gap by building a complete, automated, secure and observable MLOps deployment pipeline around a focused ML microservice — proving that the pipeline itself, not the model, is the true deliverable and the true demonstration of DevOps and MLOps competency.

---

## 4. Objective

The primary objectives of this project are to:

1. **Train and serialize an Isolation Forest anomaly detection model** on synthetically generated financial transaction data, with a StandardScaler pre-processing pipeline, and expose inference via a FastAPI REST API.
2. **Version the application using Git** and host it on GitHub, with webhook/poll-triggered automation.
3. **Implement a fully automated 7-stage CI/CD pipeline in Jenkins** covering checkout, static security analysis (Bandit SAST), unit testing (pytest), Docker image build, registry push, Kubernetes deployment, and post-deployment smoke testing.
4. **Embed DevSecOps practices** directly into the pipeline: Bandit static code analysis gates the build on HIGH severity findings, preventing insecure code from ever reaching production.
5. **Containerize the application** using a secure, multi-stage Docker build with a non-root user, read-only layers, and no build tools in the final image, then push versioned images to a local Docker registry.
6. **Provision cloud infrastructure declaratively** using Terraform targeting Google Cloud Platform (Artifact Registry + Cloud Run), demonstrating Infrastructure as Code principles.
7. **Deploy and orchestrate the containerized service** using Kubernetes (Minikube) with Deployments, Services (NodePort), liveness/readiness probes, rolling updates with zero downtime, automatic rollback on failure, and Horizontal Pod Autoscaling (2→5 replicas on CPU/memory load).
8. **Implement continuous observability** using custom Prometheus metrics (prediction count, anomaly rate, inference latency histogram, model status), a Prometheus scrape server, and Grafana dashboards for real-time visualization.

---

## 5. Scope of the Project

The scope of this project covers the complete MLOps lifecycle of a single, containerized machine-learning microservice, deployed within a local Kubernetes cluster (Minikube) and optionally to Google Cloud Platform (Cloud Run), suitable for academic demonstration. It includes:

- A **single-service Fraud Detection FastAPI application** (health check, real-time inference, Prometheus metrics, model info endpoints) as the deployment target.
- An **Isolation Forest model** trained on synthetic financial transaction data with StandardScaler pre-processing, serialized via Joblib.
- A **7-stage Jenkins pipeline** automating checkout, security scan, unit test, Docker build, registry push, Kubernetes deploy, and smoke test on every Git commit.
- **Secure multi-stage Docker builds** with non-root user execution, layer caching optimization, and build-tool exclusion from runtime images.
- **Kubernetes-based orchestration** with Deployment, Service (NodePort), HPA, liveness/readiness probes, rolling updates, and automatic rollback.
- **Infrastructure as Code** using Terraform for GCP Artifact Registry and Cloud Run provisioning.
- A **monitoring stack** (Prometheus + Grafana) providing custom ML-specific dashboards, metrics and alerting capabilities.

The project intentionally excludes multi-model ensemble architectures, real-world labeled fraud datasets, feature stores, A/B testing frameworks, and production-grade model registries (e.g., MLflow) — these are noted as future enhancements so the core MLOps pipeline demonstration remains achievable within a short timeframe.

---

## 6. System Requirements

### 6.1 Hardware Requirements

| Component | Minimum Specification |
|-----------|----------------------|
| Processor | Intel i5 / AMD Ryzen 5 (or equivalent), 4 cores |
| RAM | 8 GB (16 GB recommended for local Docker + Minikube) |
| Storage | 30 GB free disk space (SSD preferred) |
| Network | Stable broadband internet connection |

### 6.2 Software Requirements

| Category | Software / Service |
|----------|-------------------|
| Operating System | Windows 11 with WSL2 / Ubuntu 22.04 LTS |
| Application Stack | Python 3.10+, FastAPI, Uvicorn, scikit-learn |
| Version Control | Git, GitHub |
| CI/CD Server | Jenkins (LTS, JDK 17) |
| Containerization | Docker Engine (≥ 4.x), Local Docker Registry |
| Orchestration | Kubernetes — Minikube (≥ 1.35), kubectl (≥ 1.29) |
| IaC Tools | Terraform (≥ 1.0) |
| Cloud Platform | Google Cloud Platform (Cloud Run, Artifact Registry) |
| Monitoring | Prometheus, Grafana |
| Security Tools | Bandit (Python SAST) |

---

## 7. Technologies Used

| Layer | Technology | Purpose |
|-------|-----------|---------|
| ML / Data Science | scikit-learn (IsolationForest), NumPy, Joblib | Unsupervised anomaly detection, feature scaling, model serialization |
| Application | FastAPI, Uvicorn, Pydantic | High-performance REST API, request validation, async serving |
| Observability SDK | prometheus-client | Custom counters, histograms and gauges exposed at /metrics |
| Version Control | Git & GitHub | Source code management and pipeline trigger via polling/webhooks |
| CI/CD | Jenkins (Declarative Pipeline) | 7-stage pipeline orchestration: scan → test → build → deploy → verify |
| DevSecOps | Bandit (SAST) | Static security analysis; HIGH severity findings gate the build |
| Containerization | Docker (Multi-Stage Build) | Secure, minimal runtime image (~200 MB); non-root user (UID 1001) |
| Image Registry | Local Docker Registry (localhost:5000) | Storing and distributing versioned container images |
| IaC | Terraform (Google Provider) | Declarative provisioning of GCP Artifact Registry and Cloud Run |
| Orchestration | Kubernetes (Minikube) | Deployment, Service, HPA, rolling updates, probes, auto-rollback |
| Monitoring | Prometheus | Metrics scraping from the FastAPI /metrics endpoint |
| Visualization | Grafana | Dashboards: prediction rate, anomaly rate, p99 latency, model status |
| Testing | pytest, httpx, FastAPI TestClient | 30+ automated tests covering all endpoints and edge cases |

---

## 8. System Architecture

The architecture is deliberately structured so that the ML model and API sit at the very top of the pipeline as a simple input, while the real technical depth lies in the automated path that carries them to a secure, observable, auto-scaling state on Kubernetes. The complete end-to-end flow proceeds from the application through source control, CI/CD, the DevSecOps security gate, unit testing, containerization, registry management, Kubernetes deployment, and finally observability.

### 8.1 End-to-End MLOps CI/CD Pipeline Architecture

```
Git Push (GitHub)
     │
     ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  Jenkins CI/CD Pipeline (7 Stages)                                        │
│                                                                            │
│  1. Checkout → 2. Bandit SAST → 3. pytest → 4. Docker Build              │
│  → 5. Registry Push → 6. kubectl Deploy → 7. Smoke Test                  │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                  ┌─────────────────┘
                  ▼
     ┌──────────────────────────────┐
     │  Minikube (Kubernetes)       │
     │                              │
     │  ┌────────────────────────┐  │
     │  │  Pod 1 (FastAPI + ML)  │  │◄── NodePort :30800
     │  └────────────────────────┘  │
     │  ┌────────────────────────┐  │
     │  │  Pod 2 (FastAPI + ML)  │  │    HPA: 2→5 replicas
     │  └────────────────────────┘  │
     └──────────────────────────────┘
                  │
     ┌────────────┴────────────┐
     ▼                         ▼
Prometheus :9090         Grafana :3000
(scrapes /metrics)   (visualises metrics)
```

**Figure 1: End-to-End MLOps CI/CD Pipeline Architecture**

A commit to GitHub triggers the Jenkins pipeline (via SCM polling). Jenkins first runs the DevSecOps gate — Bandit SAST scanning the `app/` directory for security vulnerabilities — and gates the build on any HIGH severity findings. Only after passing the security gate and the full pytest suite (30+ tests) is the application containerized using a secure, multi-stage Docker build and pushed to the local Docker registry. The pipeline then deploys to Kubernetes via `kubectl apply`, sets the exact build-tagged image, waits for the rollout to complete (with automatic rollback on failure), and runs a post-deployment smoke test that validates both the health endpoint and the inference endpoint's response schema. Once live, the application is continuously observed through Prometheus scraping custom ML metrics and Grafana providing real-time dashboards.

### 8.2 Application Module Overview

Within the application itself, functionality is kept intentionally focused so that it can be built quickly, leaving the majority of project effort for the MLOps pipeline. The application consists of four core modules:

```
┌─────────────────────────────────────────────────────┐
│           Fraud Detection FastAPI Application        │
│                                                      │
│  ┌──────────────┐   ┌──────────────────────────┐    │
│  │  Model Layer │   │  API Layer (FastAPI)      │    │
│  │              │   │                           │    │
│  │  • Train     │   │  GET  /        (health)   │    │
│  │  • Serialize │   │  POST /predict (infer)    │    │
│  │  • Load      │   │  GET  /metrics (prom)     │    │
│  │  • Predict   │   │  GET  /model/info         │    │
│  └──────────────┘   └──────────────────────────┘    │
│                                                      │
│  ┌──────────────────────────────────────────────┐    │
│  │  Observability Layer (prometheus-client)      │    │
│  │  • fraud_predictions_total (Counter)          │    │
│  │  • fraud_prediction_latency_seconds (Hist)    │    │
│  │  • fraud_last_anomaly_score (Gauge)           │    │
│  │  • fraud_model_loaded (Gauge)                 │    │
│  │  • fraud_api_requests_total (Counter)         │    │
│  └──────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Figure 2: Application Module Overview — Fraud Detection Microservice**

### 8.3 Data Flow Diagram — Level 0 (Context Diagram)

The context diagram identifies the system as a single process interacting with four external entities: the End User (sending transactions for scoring), the Developer/MLOps Engineer (committing code and monitoring pipelines), the Monitoring Stack (Prometheus/Grafana scraping metrics), and the Kubernetes Cluster (orchestrating and scaling the service).

```
                    ┌─────────────┐
                    │  End User   │
                    │  (Client)   │
                    └──────┬──────┘
                           │ POST /predict
                           ▼
┌──────────────┐   ┌──────────────────┐   ┌──────────────────┐
│  Developer / │──▶│  Fraud Detection │──▶│  Kubernetes      │
│  MLOps Eng.  │   │  Pipeline System │   │  Cluster         │
└──────────────┘   └──────────────────┘   └──────────────────┘
                           │
                           ▼
                   ┌──────────────────┐
                   │  Prometheus +    │
                   │  Grafana         │
                   └──────────────────┘
```

**Figure 3: DFD Level 0 — Context Diagram**

### 8.4 Data Flow Diagram — Level 1 (Application Data Flow)

The Level 1 DFD decomposes the application's internal behaviour into four core processes: model loading at startup, request validation via Pydantic schemas, feature scaling and Isolation Forest inference, and Prometheus metric instrumentation that records every prediction's result, latency and anomaly score.

```
                    Transaction Request
                           │
                           ▼
               ┌───────────────────────┐
               │ 1. Pydantic Validation│
               │    (Schema Check)     │
               └───────────┬───────────┘
                           │ Valid features
                           ▼
               ┌───────────────────────┐
               │ 2. StandardScaler     │
               │    .transform()       │
               └───────────┬───────────┘
                           │ Scaled features
                           ▼
               ┌───────────────────────┐
               │ 3. IsolationForest    │
               │    .predict() +       │
               │    .score_samples()   │
               └───────────┬───────────┘
                           │ Prediction + Score
                           ▼
               ┌───────────────────────┐
               │ 4. Prometheus Metrics │
               │    Update + Response  │
               └───────────────────────┘
```

**Figure 4: DFD Level 1 — Application Data Flow**

---

## 9. System Modules

### 9.1 ML Model Training Module
Generates synthetic credit-card transaction data (10,000 normal + 400 anomalous samples), fits a StandardScaler for feature normalization, trains an Isolation Forest (200 estimators, 4% contamination), and serializes both artifacts to disk via Joblib with compression. The module is runnable as a standalone CLI script (`python -m app.model`) and is also invoked automatically during the Docker build stage.

### 9.2 FastAPI Inference Module
Serves four HTTP endpoints: a health check (`GET /`) used by Kubernetes liveness and readiness probes, a real-time anomaly prediction endpoint (`POST /predict`) that accepts transaction amount and distance, a Prometheus metrics scrape endpoint (`GET /metrics`), and a model metadata endpoint (`GET /model/info`) for operational audit. Pydantic v2 enforces strict input validation (positive, finite, bounded values).

### 9.3 Prometheus Observability Module
Instruments the application with five custom Prometheus metrics: `fraud_predictions_total` (Counter by result), `fraud_prediction_latency_seconds` (Histogram with 10 latency buckets), `fraud_last_anomaly_score` (Gauge), `fraud_model_loaded` (Gauge for readiness), and `fraud_api_requests_total` (Counter by method/endpoint/status). HTTP middleware automatically counts every request.

### 9.4 Source Control & Trigger Module
Manages application source code in Git/GitHub. Jenkins polls the SCM every 5 minutes (`H/5 * * * *`) for new commits, automatically triggering the full 7-stage pipeline on detection of changes to the main branch.

### 9.5 CI/CD Orchestration Module (Jenkinsfile)
A 375-line declarative Jenkinsfile defines seven pipeline stages — Checkout, Static Analysis & Security Scan, Unit Tests, Build Docker Image, Push to Local Registry, Deploy to Kubernetes, and Smoke Test — with each stage reporting status, archiving artifacts (Bandit JSON report, pytest JUnit XML), and handling failures with automatic rollback. Pipeline-level options include a 30-minute timeout, build log rotation, timestamp injection, and concurrent build prevention.

### 9.6 DevSecOps Security Module
Runs Bandit SAST against the `app/` directory with medium severity/confidence thresholds. The JSON report is parsed programmatically; if any HIGH severity issues are detected, the pipeline exits with a non-zero code, preventing insecure code from progressing to the Docker build stage. The Bandit report is archived as a Jenkins build artifact for audit.

### 9.7 Containerization Module
Builds a secure, multi-stage Docker image: Stage 1 (builder) installs all Python dependencies into an isolated virtual environment and pre-trains the Isolation Forest model; Stage 2 (runtime) copies only the venv and serialized artifacts into a minimal `python:3.10-slim` image, runs as non-root user `appuser` (UID 1001), and includes a built-in Docker HEALTHCHECK. Images are tagged by Jenkins build number and pushed to a local Docker registry at `localhost:5000`.

### 9.8 Infrastructure as Code Module
Provisions Google Cloud Platform resources using Terraform with the Google provider (~5.0): enables required APIs (Cloud Run, Artifact Registry), creates a Docker repository in Artifact Registry, deploys a serverless Cloud Run v2 service with resource limits (1 CPU, 512Mi memory), scale-to-zero capability, and public unauthenticated access. Outputs include the service URL and repository path.

### 9.9 Kubernetes Orchestration Module
Four Kubernetes resources are declared in a single manifest: a Namespace (`mlops`), a Deployment (2 replicas, rolling updates with `maxUnavailable: 0` for zero-downtime, liveness/readiness probes, resource requests/limits, non-root security context), a Service (NodePort 30800), and a HorizontalPodAutoscaler (2→5 replicas on 70% CPU / 80% memory utilization, with stabilization windows for controlled scale-up/down).

### 9.10 Monitoring & Visualization Module
Prometheus is configured via `prometheus.yml` with three scrape jobs: self-monitoring, Minikube NodePort target, and local development target. A pre-built Grafana dashboard JSON (`grafana-dashboard.json`) provides panels for total predictions/min, anomaly rate %, p99 inference latency, request rate, and model loaded status using PromQL queries.

---

## 10. DevOps & MLOps Fundamentals Used

| Fundamental | Application in this Project |
|-------------|---------------------------|
| Continuous Integration (CI) | Every Git commit automatically triggers a Jenkins build encompassing security scan, unit tests and Docker image build |
| Continuous Delivery (CD) | Verified, scanned images are automatically deployed to Kubernetes with rolling updates and smoke tests |
| Infrastructure as Code | Terraform provisions GCP Artifact Registry and Cloud Run; Kubernetes manifests declare all cluster resources |
| Containerization | Multi-stage Docker builds ensure a consistent, secure, minimal runtime environment across all stages |
| Container Orchestration | Kubernetes manages deployment, rolling updates, self-healing (liveness probes), and horizontal auto-scaling |
| DevSecOps (Shift-Left Security) | Bandit SAST gates every build on HIGH severity findings; non-root container user prevents privilege escalation |
| ML Model Lifecycle | Automated model training during Docker build; versioned artifacts serialized via Joblib; model metadata exposed at /model/info |
| Observability | Custom Prometheus metrics (counters, histograms, gauges) scraped by Prometheus server and visualized in Grafana dashboards |
| Auto-Scaling | HPA scales 2→5 replicas based on CPU/memory utilization thresholds with stabilization windows |
| Zero-Downtime Deployment | Rolling update strategy with maxUnavailable: 0; automatic rollback in Jenkins post-failure block |

---

## 11. Testing

A multi-layered testing strategy is applied throughout the pipeline to catch issues as early as possible:

| Test Type | Tool / Technique | Purpose |
|-----------|-----------------|---------|
| Unit Testing | pytest (30+ tests), FastAPI TestClient, httpx | Validate health check, prediction (normal + anomalous), input validation, edge cases, metrics endpoint |
| Static Code Analysis (SAST) | Bandit | Detect security vulnerabilities, insecure patterns; HIGH severity findings block the pipeline |
| Input Validation Testing | Pydantic v2 field validators | Reject NaN, Inf, negative, out-of-range, and missing-field payloads at the API boundary |
| Boundary Testing | pytest parametrized tests | Test minimum, maximum, and edge-case values for amount (≤$1M) and distance (≤20,000 km) |
| Container Health Testing | Docker HEALTHCHECK directive | Verify the container's HTTP endpoint responds inside the running container |
| Kubernetes Probe Testing | Liveness & Readiness probes (httpGet /) | Kubernetes automatically restarts unresponsive pods and withholds traffic from unready pods |
| Pipeline / Integration Testing | Jenkins 7-stage pipeline | Verify the end-to-end flow: checkout → scan → test → build → push → deploy → smoke test |
| Post-Deployment Smoke Test | curl + Python JSON schema validation | Confirm the deployed service responds correctly and returns all expected response fields |
| Infrastructure Validation | `terraform plan` | Preview and validate GCP infrastructure changes before apply |

---

## 12. Results

On completion, the pipeline demonstrates the following measurable outcomes:

- **End-to-end deployment time** reduced from a manual process taking 15–25 minutes to an automated pipeline completing in under 5 minutes.
- **100% of commits** to the main branch are automatically checked out, security-scanned, unit-tested, containerized, deployed and smoke-tested without any manual intervention.
- **Bandit SAST security reports** generated for every build, with HIGH severity issues blocking deployment automatically — zero insecure code reaches production.
- **30+ pytest unit tests** pass on every build, covering all API endpoints, input validation, boundary conditions, and error handling paths, with JUnit XML results published to the Jenkins dashboard.
- **Live Grafana dashboards** displaying total predictions per minute, anomaly rate percentage, p99 inference latency, per-endpoint request rates, and model loaded status in real-time.
- **Kubernetes HPA** successfully auto-scaling from 2 to 5 replicas under simulated CPU load, and scaling back down after the stabilization window.
- **Zero-downtime rolling updates** verified — old pods remain live until new pods pass readiness probes; automatic rollback triggered on deployment failure.
- **Terraform-provisioned GCP infrastructure** (Artifact Registry + Cloud Run) created declaratively with `terraform apply`, demonstrating Infrastructure as Code principles.

These results validate that a focused ML microservice, paired with a rigorous MLOps CI/CD pipeline, is sufficient to demonstrate mastery of every core concept in the course syllabus.

---

## 13. Future Enhancements

- Migrate the orchestration layer to a managed Kubernetes service (Google GKE / Amazon EKS) for production-grade auto-scaling and self-healing.
- Integrate a model registry (MLflow / Weights & Biases) for model versioning, experiment tracking, and A/B testing of model versions.
- Add real-world labeled fraud datasets (e.g., IEEE-CIS Fraud Detection) and implement supervised models alongside the unsupervised Isolation Forest for comparative evaluation.
- Extend the pipeline to support blue-green or canary deployment strategies for zero-downtime model rollouts.
- Introduce automated model drift detection by monitoring prediction distributions over time in Prometheus/Grafana.
- Add container image vulnerability scanning (Trivy) as an additional DevSecOps gate before registry push.
- Implement multi-environment promotion (dev → staging → production) with environment-specific approvals and Terraform workspaces.
- Incorporate feature stores (Feast) for real-time feature serving and feature lineage tracking.
- Add Alertmanager integration for automated incident notification when anomaly rates exceed thresholds.

---

## 14. Conclusion

This project demonstrates that the depth of a DevOps and MLOps project lies not in the complexity of the model it deploys, but in the rigor, automation and security of the pipeline that carries it from source code to a running, monitored, auto-scaling inference service. By pairing a deliberately focused Isolation Forest anomaly detection microservice with a complete MLOps CI/CD pipeline — covering Git, Jenkins (7-stage declarative pipeline), Bandit SAST, pytest (30+ automated tests), Docker (secure multi-stage builds), a local Docker registry, Kubernetes (Minikube with Deployments, Services, HPA, probes and rolling updates), Terraform (GCP Artifact Registry + Cloud Run), Prometheus (custom ML metrics), and Grafana (real-time dashboards) — the project provides a practical, achievable, and thorough demonstration of every core concept covered in this course, establishing a solid foundation for production-grade MLOps practices.

---
