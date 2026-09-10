# AegisShield: Complete Project Guide & Engineering Master Manual

> **Purpose of this Document**:  
> This file is your complete, single-source-of-truth manual explaining **every single minor and major detail** of this project in plain English, mathematical depth, architectural structure, and interview-ready defense. Keep this file locally on your laptop for study, project presentations, viva questions, and technical interviews.

---

## 📑 Table of Contents

1. [High-Level Story: What is this project and why does it exist?](#1-high-level-story-what-is-this-project-and-why-does-it-exist)
2. [The Big Picture: How Real-World Fraud Detection Works](#2-the-big-picture-how-real-world-fraud-detection-works)
3. [Step-by-Step Lifecycle of a Transaction](#3-step-by-step-lifecycle-of-a-transaction)
4. [Deep Dive into Every Folder and File](#4-deep-dive-into-every-folder-and-file)
5. [The 36 Features Explained: Category by Category](#5-the-36-features-explained-category-by-category)
6. [The Mathematical & Algorithmic Foundations](#6-the-mathematical--algorithmic-foundations)
7. [The 10 Declarative Business Rules](#7-the-10-declarative-business-rules)
8. [The 4 Decision Tiers & Explainable AI (XAI)](#8-the-4-decision-tiers--explainable-ai-xai)
9. [The Database & Analyst Feedback Learning Loop](#9-the-database--analyst-feedback-learning-loop)
10. [Model Drift & Stability Monitoring (PSI & KS)](#10-model-drift--stability-monitoring-psi--ks)
11. [Frontend Architecture: How the UI Works](#11-frontend-architecture-how-the-ui-works)
12. [Cloud & Serverless Deployment Mechanics (Vercel)](#12-cloud--serverless-deployment-mechanics-vercel)
13. [DevOps Stack: Docker, Kubernetes & Jenkins CI/CD](#13-devops-stack-docker-kubernetes--jenkins-cicd)
14. [Observability: Prometheus Metrics & Grafana](#14-observability-prometheus-metrics--grafana)
15. [How to Run, Test, and Verify Everything Locally](#15-how-to-run-test-and-verify-everything-locally)
16. [Master Viva & Technical Interview Q&A Cheatsheet](#16-master-viva--technical-interview-qa-cheatsheet)

---

## 1. High-Level Story: What is this project and why does it exist?

### The Problem
When you swipe a credit card, initiate a UPI payment on Google Pay/PhonePe, or transfer funds via wire, a bank has **less than 50 milliseconds** to answer one critical question:
> *"Is this legitimate customer activity, or is an attacker stealing money?"*

If the bank is **too lenient**, criminals drain accounts, causing millions in chargeback fraud losses.  
If the bank is **too aggressive**, legitimate customers have cards declined while trying to buy groceries or plane tickets, causing severe frustration and customer churn.

### Why Traditional Solutions Fail
1. **Rule-Only Systems**: Old banks used simple `IF/THEN` rules (e.g. `IF amount > $5000 THEN BLOCK`). Attackers easily bypass this by "smurfing" (sending \$4,999 multiple times).
2. **Pure Machine Learning Prototypes**: A single black-box ML model (like a simple Isolation Forest or Neural Net) outputs a number without explaining *why*. Financial regulations (**FCRA**, **GDPR Article 22**) legally require institutions to tell customers the exact reason their transaction was declined. Furthermore, pure ML struggles with zero-day attacks that rules can stop instantly.

### The Solution: AegisShield
**AegisShield** is a **Hybrid Multi-Engine Platform**. It merges:
- Instant **hard stop business rules** (velocity bursts, impossible travel, sanctioned countries),
- **Unsupervised Anomaly Detection** (Isolation Forest catching novel anomalies),
- **Supervised Machine Learning** (HistGradientBoosting / XGBoost calibrated probabilities),
- **Behavioral Velocity Profiling** (rolling Z-scores against a customer's personal 30-day habits), and
- **Entity Linkage Tracking** (multiple accounts sharing one phone or IP).

Everything is deployed with enterprise DevOps: automated Jenkins CI/CD, multi-stage Docker containers, Kubernetes auto-scaling, Prometheus metrics, and a live Vercel cloud serverless dashboard.

---

## 2. The Big Picture: How Real-World Fraud Detection Works

In systems like **Stripe Radar**, **PayPal Risk**, or **Falcon Fraud Manager**, detection occurs in distinct concentric defensive layers:

```
[ Incoming Transaction Request ]
              │
              ▼
┌───────────────────────────────────────────────┐
│ Layer 1: Deterministic Hard Stop Rules        │  <- Blocks instantly on obvious violations
│ (Impossible travel speed > 800 km/h,          │     (0.5 milliseconds)
│  Sanctioned country, 8 swipes in 2 minutes)   │
└───────────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────────┐
│ Layer 2: Real-Time Feature Store Enrichment   │  <- Pulls customer 30-day average,
│ (Sliding window counts, Z-scores, linkages)   │     recent swipe coordinates, device history
└───────────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────────┐
│ Layer 3: Machine Learning Models              │  <- Isolation Forest (Anomaly Index)
│ (Calibrated class probabilities)              │  <- HistGradientBoosting (Fraud Probability)
└───────────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────────┐
│ Layer 4: Composite Risk Scoring Engine        │  <- Combines all weights into 0 - 100 score
│ (Weighted aggregation & 4-tier decision)      │  <- Generates human-readable reason codes
└───────────────────────────────────────────────┘
              │
              ▼
┌───────────────────────────────────────────────┐
│ Layer 5: Action & Audit Storage               │  <- Returns ALLOW / STEP_UP / REVIEW / BLOCK
│ (SQLite / PostgreSQL DB + Prometheus metrics) │  <- Populates Analyst Triage Queue if high risk
└───────────────────────────────────────────────┘
```

---

## 3. Step-by-Step Lifecycle of a Transaction

Here is the exact millisecond-by-millisecond path of a request:

1. **HTTP Ingestion**: A client sends a POST request to `/predict` (either a rich JSON payload or legacy 2-parameter payload).
2. **Pydantic Validation**: `app/data/schema.py` validates that `amount > 0`, coordinates are finite numbers, and enumerations match (`PURCHASE`, `UPI`, etc.).
3. **State Query**: The `FeatureStore` (`app/features/store.py`) looks up the customer ID:
   - What was their average transaction over the last 30 days?
   - Where were they located during their last transaction 20 minutes ago?
   - How many failed password attempts happened in the last 24 hours?
4. **Feature Vector Assembly**: The 36-feature pipeline (`app/features/pipeline.py`) computes derived numbers:
   - Great-circle Haversine speed between last location and current location.
   - Standard deviation deviation ($Z$-score) of this amount versus baseline.
   - Cyclical trigonometric features for time-of-day ($\sin / \cos$).
5. **Rule Engine Execution**: The declarative rule engine (`app/rules/engine.py`) evaluates the YAML rules against the features. If rules trigger, rule score increases.
6. **ML Inference**:
   - `IsolationForest` outputs calibrated anomaly index ($0.0$ to $1.0$).
   - `HistGradientBoosting` outputs calibrated fraud probability ($0.0$ to $1.0$).
7. **Weighted Ensemble**: `app/risk/engine.py` computes:
   $$\text{Score} = 0.30(\text{Rules}) + 0.30(\text{Supervised}) + 0.20(\text{IsoForest}) + 0.10(\text{Velocity}) + 0.10(\text{Network})$$
8. **Decision Assignment**:
   - If Score $< 30$: `ALLOW`
   - If Score $30 - 59$: `STEP_UP` (Prompt SMS OTP / biometric)
   - If Score $60 - 79$: `MANUAL_REVIEW` (Flag to Human Analyst Triage Queue)
   - If Score $\ge 80$: `BLOCK` (Immediate decline)
9. **Explainability Attribution**: `app/models/explainability.py` identifies the top contributing features and converts them into natural language reasons (e.g. *"Transaction amount ₹48,000 is 8.5x customer 30-day baseline"*).
10. **Database Persistence**: SQLAlchemy logs the transaction record to `fraud_pipeline.db`. If decision is `MANUAL_REVIEW` or `BLOCK`, an open `FraudAlert` is created.
11. **Telemetry**: Prometheus request counter and latency histograms increment.
12. **Response Dispatched**: JSON is returned to the client in **under 15 milliseconds**.

---

## 4. Deep Dive into Every Folder and File

### Root Directory
- **`vercel.json`**: Configuration for Vercel deployment. Defines rewrite rules routing all traffic (`/(.*)`) to the serverless function `api/index.py` and sets environment variables (`VERCEL=1`, `VERCEL_SUPPORT_LARGE_FUNCTIONS=1`).
- **`.vercelignore`**: Tells Vercel which files to exclude from the serverless bundle (tests, terraform, documentation, cache) to keep the deployment under the 500 MB limit.
- **`Dockerfile`**: Defines a hardened multi-stage Docker build. 
  - *Stage 1 (Builder)*: Uses a Python build environment to compile wheels and install dependencies into a virtualenv `/opt/venv`.
  - *Stage 2 (Runtime)*: Uses a clean, slim base image, copies `/opt/venv`, creates an unprivileged non-root user `appuser` (UID 10001), and sets security limits.
- **`.dockerignore`**: Excludes `.git`, `.venv`, test caches, and temporary files from the Docker build context to ensure fast builds and prevent leaking secrets.
- **`Jenkinsfile`**: Declarative 15-stage Jenkins CI/CD pipeline script. Manages virtualenv creation, Bandit SAST security scans, Pytest execution, Docker image packaging, Kubernetes rollout, and automated rollback if health checks fail.
- **`deployment.yaml`**: Kubernetes manifest containing:
  - *Deployment*: 2 replicas of the API container with liveness and readiness probes (`/health`).
  - *Service*: ClusterIP service routing port 80 to port 8000.
  - *HorizontalPodAutoscaler (HPA)*: Automatically scales pods between 2 and 10 replicas when CPU utilization exceeds 70%.
- **`requirements.txt`**: Production runtime dependencies strictly required for live serving (`fastapi`, `uvicorn`, `scikit-learn`, `numpy`, `pandas`, `sqlalchemy`, `pydantic`, `pyyaml`, `prometheus-client`).
- **`requirements-dev.txt`**: Offline development and CI/CD tools (`pytest`, `bandit`, `xgboost`, `httpx`). Keeping this separate avoids bloating the cloud production bundle.
- **`verify.ps1`**: Automated Windows PowerShell verification script that checks Python 3.10+, installs dependencies, trains baseline models, executes all 51 tests, and smoke tests live HTTP endpoints.
- **`train_pipeline.py`**: Standalone training script that generates synthetic datasets or loads public datasets (IEEE-CIS, ULB, PaySim), runs the 36-feature pipeline, trains the supervised classifier, and saves `supervised_model.pkl`.
- **`model.pkl` & `scaler.pkl`**: Pre-bundled baseline model artifacts (Isolation Forest and StandardScaler) ensuring the serverless microservice has zero cold-start delay.

---

### `api/` Directory
- **`api/index.py`**: The serverless entrypoint for Vercel. Contains `VercelPathFixMiddleware`, a custom ASGI middleware that intercepts requests and normalizes internal rewritten paths so FastAPI routes match cleanly without 404 errors.

---

### `app/` Directory
- **`app/main.py`**: The core FastAPI application. Contains:
  - Application lifecycle (`lifespan`) initializing SQLite tables and loading ML models.
  - Prometheus middleware recording HTTP method, path, and status code.
  - Endpoints: `GET /` (serves web console), `GET /health` (probes), `POST /predict` (scoring), `GET /fraud/alerts` (triage queue), `POST /fraud/feedback` (analyst review verdicts), `GET /metrics` (Prometheus scrape).
- **`app/model.py`**: Baseline model module containing functions to generate synthetic 2D training data, train `IsolationForest` and `StandardScaler`, and `get_or_train_artifacts()` which auto-trains in memory if files are missing.
- **`app/rules.yaml`**: Configuration file defining business heuristic rules, their weights, and string conditions evaluated dynamically.

---

### `app/data/` Directory
- **`app/data/schema.py`**: Pydantic v2 schemas. Defines `TransactionEvaluationRequest`, `TransactionEvaluationResponse`, `RiskLevel` (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), and `DecisionType` (`ALLOW`, `STEP_UP`, `MANUAL_REVIEW`, `BLOCK`). Validates that amounts are $>0$ and numbers are finite.
- **`app/data/adapters.py`**: Data ingestion adapters. Translates heterogeneous raw schemas from public benchmarks (**IEEE-CIS Fraud Detection**, **ULB Credit Card Fraud**, and **PaySim mobile money**) into AegisShield's unified transaction schema.
- **`app/data/generator.py`**: Synthetic data generator. Creates statistically realistic financial transactions with realistic fraud distributions (~3.5% fraud) across 18 distinct attack scenarios.

---

### `app/features/` Directory
- **`app/features/pipeline.py`**: The 36-feature engineering pipeline. Converts raw transaction inputs into normalized mathematical feature vectors without temporal lookahead leakage.
- **`app/features/store.py`**: In-memory and Redis-compatible sliding-window feature store. Maintains rolling customer spend totals (1h, 24h), last known GPS coordinates, device-to-account entity maps, and failed login attempt counters.

---

### `app/models/` Directory
- **`app/models/isolation_forest.py`**: Scikit-Learn Isolation Forest wrapper with score calibration converting raw decision function scores into a $0.0 - 1.0$ anomaly index.
- **`app/models/supervised.py`**: Supervised tabular classifier using `HistGradientBoostingClassifier` (and XGBoost when available) with class weighting for extreme fraud imbalance.
- **`app/models/explainability.py`**: Explainable AI (XAI) engine. Computes feature importance contributions and translates numeric deviations into human-readable reason sentences.
- **`app/models/drift.py`**: Data drift monitor. Computes Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) statistics between reference training distributions and live production data.
- **`app/models/comparison.py`**: Benchmark comparison runner evaluating 5 algorithms (Isolation Forest, Logistic Regression, Random Forest, GBDT, and Hybrid Ensemble).

---

### `app/risk/` Directory
- **`app/risk/engine.py`**: The central Risk Scoring Engine. Aggregates rule scores, supervised probabilities, anomaly scores, velocity multipliers, and network collision indices into a unified $0 - 100$ score.
- **`app/risk/decision.py`**: Decision matrix assigning transactions to `ALLOW`, `STEP_UP`, `MANUAL_REVIEW`, or `BLOCK`.

---

### `app/rules/` Directory
- **`app/rules/engine.py`**: Evaluates conditions from `rules.yaml` using safe Python expression parsing. Returns total rule score and list of triggered rule names.

---

### `app/db/` Directory
- **`app/db/models.py`**: SQLAlchemy ORM models:
  - `TransactionRecord`: Full audit trail of evaluated transactions, risk scores, and decisions.
  - `FraudAlert`: High-priority queue entries for transactions requiring human review.
  - `AnalystFeedback`: Logs human analyst verdicts (`CONFIRMED_FRAUD` vs `FALSE_POSITIVE`).
  - `ModelRegistryRecord`: Version tracking of trained models.
- **`app/db/session.py`**: SQLAlchemy engine configuration. Dynamically points to `/tmp/fraud_pipeline.db` on Vercel to allow writes on read-only serverless filesystems, and auto-seeds 9 realistic transactions and 5 triage alerts on fresh boot.

---

### `app/static/` Directory
- **`app/static/index.html`**: HTML markup for the AegisShield console. Features 5 navigation tabs:
  1. *Live Evaluator & Scenarios* (Interactive bench, multi-currency switcher, SVG radial gauge)
  2. *Analyst Triage & Alerts* (Live queue with `[ 🚨 Flag Fraud ]` and `[ ✓ Approve ]` buttons)
  3. *Model Benchmarks & Drift* (PR-AUC comparison table and PSI drift indicator)
  4. *Rule Engine & Weights* (Live table of enabled YAML business rules)
  5. *Metrics & Architecture* (System flow diagram and link to `/metrics`)
- **`app/static/style.css`**: Vanilla CSS design system. Implements modern dark-mode cyber aesthetics, glassmorphism, responsive CSS grid, animated SVG refresh spinners, and row-flash highlights.
- **`app/static/app.js`**: Frontend JavaScript controller. Handles live form evaluations, multi-currency symbol updates, zero-out form resets, preset chip loading, toast notifications, and immediate alert count badge updates on page load.

---

## 5. The 36 Features Explained: Category by Category

Every feature in `app/features/pipeline.py` serves a specific behavioral or risk purpose:

### 1. Monetary Features
1. `amount`: Raw transaction amount.
2. `log_amount`: Natural logarithm $\ln(\text{amount} + 1)$ to compress heavy-tailed financial distributions.
3. `amount_to_avg_ratio`: Ratio of current amount to customer's 30-day average. (e.g., $10.0 = 10\times$ normal spending).
4. `amount_zscore`: How many standard deviations the amount is from the customer's rolling 30-day mean.
5. `is_high_amount_outlier`: Boolean flag ($1.0$ if amount $> 5\times$ baseline).

### 2. Kinematic & Geospatial Features
6. `distance_from_home`: Distance in kilometers from the cardholder's registered home address.
7. `distance_from_last_txn`: Distance in kilometers from the location of the previous transaction.
8. `time_since_last_txn_sec`: Elapsed seconds since the customer's previous swipe.
9. `speed_kmh`: Physical speed required to travel between the last transaction and this one ($d / \Delta t$).
10. `is_impossible_travel`: Boolean flag ($1.0$ if speed $> 800\text{ km/h}$, representing supersonic/impossible physical movement).

### 3. Temporal & Circadian Features
11. `hour_of_day`: Integer hour ($0$ to $23$).
12. `day_of_week`: Integer day ($0 = \text{Monday}$ to $6 = \text{Sunday}$).
13. `hour_sin`: $\sin(2\pi \cdot \text{hour} / 24)$ — captures cyclical daily rhythms (e.g., 23:00 and 01:00 are close in time).
14. `hour_cos`: $\cos(2\pi \cdot \text{hour} / 24)$.
15. `day_sin`: $\sin(2\pi \cdot \text{day} / 7)$ — captures cyclical weekly rhythms.
16. `day_cos`: $\cos(2\pi \cdot \text{day} / 7)$.
17. `is_weekend`: Boolean flag ($1.0$ on Saturday or Sunday).
18. `is_nighttime`: Boolean flag ($1.0$ between 01:00 AM and 05:00 AM, common fraud cashout window).

### 4. Velocity & Burst Features
19. `txn_count_5m`: Number of transactions on this account in the last 5 minutes. (Detects bot testing).
20. `txn_count_1h`: Number of transactions in the last 1 hour.
21. `txn_count_24h`: Number of transactions in the last 24 hours.
22. `txn_amount_1h`: Cumulative money spent in the last 1 hour.
23. `txn_amount_24h`: Cumulative money spent in the last 24 hours.
24. `velocity_burst_ratio`: Ratio of 1-hour frequency to normalized 24-hour frequency (detects sudden spending bursts).

### 5. Device, Network & Entity Linkage Features
25. `is_new_device`: $1.0$ if the hardware device ID has never been used by this customer before.
26. `is_new_ip`: $1.0$ if the IP address has never been seen for this account.
27. `is_new_beneficiary`: $1.0$ if sending money to a newly added, unverified recipient account.
28. `device_associated_accounts`: Count of distinct customer accounts using this same physical device ID. ($>2$ indicates account-farming/mule rings).
29. `ip_associated_accounts`: Count of distinct customer accounts transacting from this IP address.
30. `is_vpn_proxy`: $1.0$ if IP belongs to a commercial VPN, Tor exit node, or anonymous hosting provider.

### 6. Authentication & Categorical Risk
31. `failed_attempts_last_24h`: Number of incorrect passwords or failed OTPs in the last 24 hours.
32. `payment_method_risk`: Risk weight of payment channel (Wire/Crypto $= 0.8$, Credit Card $= 0.4$, UPI $= 0.2$).
33. `merchant_category_risk`: Risk weight of merchant MCC (Cryptocurrency Exchange $= 0.9$, Gaming/Gambling $= 0.85$, Grocery $= 0.1$).
34. `channel_risk`: Risk weight of ingestion method (Direct API $= 0.7$, Web $= 0.4$, POS Chip $= 0.1$).
35. `is_foreign_transaction`: $1.0$ if transaction currency or country differs from home bank.
36. `is_high_risk_country`: $1.0$ if transaction originates in FATF-flagged high-risk jurisdiction.

---

## 6. The Mathematical & Algorithmic Foundations

### 1. The Haversine Formula for Impossible Travel
Standard Euclidean distance ($\sqrt{\Delta x^2 + \Delta y^2}$) cannot be used for geographic coordinates because the Earth is an oblate spheroid. AegisShield calculates great-circle distance:

$$a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)$$

$$c = 2 \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1 - a}\right)$$

$$d = R \cdot c \quad (R = 6371\text{ km})$$

If a card is swiped in New Delhi at 10:00 AM and in London at 10:20 AM ($6,800\text{ km}$ apart in $20\text{ minutes}$):
$$\text{Speed} = \frac{6800\text{ km}}{0.333\text{ h}} = 20,400\text{ km/h}$$
This exceeds the physical speed of commercial aircraft ($800\text{ km/h}$), triggering an instant critical rule violation.

### 2. Rolling Z-Scores for Habitual Spending
Instead of fixed thresholds, every customer has their own baseline mean ($\mu$) and standard deviation ($\sigma$) updated over a rolling 30-day window:
$$Z = \frac{\text{Amount} - \mu_{30\text{d}}}{\max(\sigma_{30\text{d}}, 1.0)}$$
- If a student normally spends ₹300, a ₹15,000 charge produces $Z = 8.5$ (Extreme Outlier).
- If a business owner normally spends ₹50,000, a ₹15,000 charge produces $Z = -0.4$ (Completely Normal).

### 3. Isolation Forest Anomaly Scoring
The Isolation Forest isolates anomalies by randomly selecting a feature and randomly selecting a split value between the minimum and maximum of that feature.
- **Normal points** reside in dense clusters and require many random splits (long path length $h(x)$) to isolate.
- **Anomalous points** reside in sparse regions and are isolated near the root of the tree (short path length $h(x)$).

Score calibration:
$$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
When $E(h(x)) \to 0$, $s \to 1.0$ (High confidence anomaly).

### 4. Precision-Recall AUC (PR-AUC) vs. ROC-AUC
In financial fraud, fraud represents only $0.1\% - 3.5\%$ of all transactions (extreme class imbalance).
- **ROC-AUC** uses False Positive Rate ($\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}}$). Because True Negatives (legitimate transactions) number in the millions, the denominator is huge, making ROC-AUC deceptively high ($0.99+$) even for mediocre models.
- **PR-AUC** uses Precision ($\frac{\text{TP}}{\text{TP} + \text{FP}}$) and Recall ($\frac{\text{TP}}{\text{TP} + \text{FN}}$). It focuses exclusively on the minority fraud class. In AegisShield, PR-AUC is the primary benchmark metric.

---

## 7. The 10 Declarative Business Rules

Configured in `app/rules.yaml`, these rules enforce non-negotiable institutional policies:

1. **`RULE_IMPOSSIBLE_TRAVEL`** (Weight: 30.0): Triggered if speed $> 800\text{ km/h}$.
2. **`RULE_VELOCITY_SPIKE_5M`** (Weight: 20.0): Triggered if $\ge 5$ transactions occur in 5 minutes.
3. **`RULE_AMOUNT_ZSCORE_EXCEEDED`** (Weight: 18.0): Triggered if amount is $\ge 4$ standard deviations from 30-day baseline.
4. **`RULE_NEW_BENEFICIARY_HIGH_TRANSFER`** (Weight: 20.0): Triggered if money is sent to a newly added payee and amount is $\ge 2.5\times$ normal average.
5. **`RULE_RAPID_FAILED_ATTEMPTS`** (Weight: 15.0): Triggered if $\ge 3$ failed logins occurred in 24h and amount $\ge ₹2,000$.
6. **`RULE_UNUSUAL_NIGHTTIME_ACTIVITY`** (Weight: 12.0): Triggered if transaction occurs between 01:00 and 05:00 AM and amount is $\ge 2\times$ average.
7. **`RULE_SUSPICIOUS_DEVICE_SHARING`** (Weight: 18.0): Triggered if $\ge 3$ distinct customer accounts have used this physical device ID.
8. **`RULE_VPN_ANONYMOUS_IP`** (Weight: 14.0): Triggered if transaction originates from a VPN/proxy and amount $\ge ₹5,000$.
9. **`RULE_HIGH_RISK_COUNTRY_OUTFLOW`** (Weight: 25.0): Triggered if capital flows to an AML sanctioned country.
10. **`RULE_NEW_DEVICE_HIGH_AMOUNT`** (Weight: 16.0): Triggered if transaction is from an unrecognized new device and amount is $\ge 3\times$ baseline.

---

## 8. The 4 Decision Tiers & Explainable AI (XAI)

### The 4 Operational Decision Tiers
1. **`ALLOW` (Score 0.0 – 29.9)**:  
   Frictionless approval. No additional customer verification required.
2. **`STEP_UP` (Score 30.0 – 59.9)**:  
   Dynamic 3D-Secure / Step-Up Authentication. Prompts customer for an SMS OTP, email confirmation, or biometric fingerprint swipe on mobile banking app.
3. **`MANUAL_REVIEW` (Score 60.0 – 79.9)**:  
   High suspicion. Payment is placed on temporary hold and routed into the **Analyst Triage Queue** for a human fraud officer to inspect.
4. **`BLOCK` (Score 80.0 – 100.0)**:  
   Hard decline. The transaction is rejected at the gateway. Card may be temporarily locked.

### Explainable AI (XAI)
To comply with regulatory compliance (FCRA, GDPR Article 22), the engine never issues an unexplained decision. `app/models/explainability.py` extracts top mathematical contributors and renders plain language reason codes:
- *"Transaction amount ₹75,000 is 11.5x customer 30-day baseline"*
- *"Calculated speed between consecutive transactions (7,400 km/h) exceeds physical travel limits"*
- *"High-value transaction originating from an anonymous VPN/Tor exit node"*
- *"Multiple authentication failures followed by high value transfer"*

---

## 9. The Database & Analyst Feedback Learning Loop

### Persistence Schema (`app/db/models.py`)
1. **`TransactionRecord`**: Stores every evaluated transaction, including timestamp, customer ID, currency, amount, 0–100 risk score, decision tier, latency in ms, triggered rules, and explanation reasons.
2. **`FraudAlert`**: Created automatically whenever a transaction scores `MANUAL_REVIEW` or `BLOCK`. Contains severity (`CRITICAL` or `HIGH`) and status (`OPEN`, `UNDER_REVIEW`, `RESOLVED`).
3. **`AnalystFeedback`**: Stores decisions made by human analysts in the web console.

### The Feedback Learning Loop
When a human analyst reviews an alert in the console:
- Clicking **`[ 🚨 Flag Fraud ]`** sets verdict to `CONFIRMED_FRAUD`.
- Clicking **`[ ✓ Approve ]`** sets verdict to `FALSE_POSITIVE` (legitimate).

These labeled outcomes are saved into `analyst_feedback`. During periodic retraining cycles (or automated Jenkins triggers), the supervised model trains on these human-verified ground-truth verdicts, continuously improving model precision on false positives.

---

## 10. Model Drift & Stability Monitoring (PSI & KS)

In production, models degrade over time because fraud attack patterns evolve (Concept Drift) or economic factors change spending amounts (Covariate Shift).

AegisShield implements the **Population Stability Index (PSI)** in `app/models/drift.py`:
$$\text{PSI} = \sum_{i=1}^{10} \left( \text{Actual}_i - \text{Expected}_i \right) \times \ln\left(\frac{\text{Actual}_i}{\text{Expected}_i}\right)$$
- **$\text{PSI} < 0.10$**: **Nominal / Stable**. Distribution matches training baseline.
- **$0.10 \le \text{PSI} \le 0.25$**: **Moderate Shift**. Logged to Prometheus as a warning.
- **$\text{PSI} > 0.25$**: **Significant Drift**. Alerts DevOps and triggers an automated retraining job in the Jenkins CI/CD pipeline.

---

## 11. Frontend Architecture: How the UI Works

The web console (`app/static/`) is built using **HTML5, Vanilla CSS, and modern JavaScript**:

1. **Interactive Multi-Currency Selector**:
   - Allows analysts to evaluate in **INR (`₹`)**, **USD (`$`)**, **EUR (`€`)**, **GBP (`£`)**, or **AED (`د.إ`)**.
   - Selecting a currency dynamically updates the input adornment symbol and transmits `currency` in the JSON payload.
2. **Zero-Out Reset Button**:
   - Clicking **Reset** completely zeroes out all numeric inputs (`0.00`), unchecks all risk flags, and resets currency to INR with an informative confirmation toast.
3. **SVG Radial Risk Gauge**:
   - Utilizes SVG circle stroke-dashoffset transitions (440 perimeter) with smooth 800ms easing.
   - Automatically adapts stroke color: Crimson ($\ge 80$), Orange ($60-79$), Amber ($30-59$), Emerald ($<30$).
4. **Analyst Triage & Alerts Feed**:
   - Displays live open fraud alerts with severity tags.
   - Features **`[ 🚨 Flag Fraud ]`** and **`[ ✓ Approve ]`** micro-action buttons with soft glow hover effects.
   - Refresh buttons include spinning SVG keyframe animations and cache-busting timestamps (`?_t=${Date.now()}`) to force fresh queries to the server.
5. **Initial Boot Auto-Sync**:
   - `loadAlerts()` is called immediately on page load (`DOMContentLoaded`), ensuring the alert count badge in the navigation tab displays the true open count (e.g. `5`) without requiring the analyst to click the tab first.

---

## 12. Cloud & Serverless Deployment Mechanics (Vercel)

AegisShield is deployed live on Vercel Serverless Fluid Compute:

1. **Solving the 500 MB Size Limit**:
   - Standard Vercel serverless Python functions have an uncompressed size limit of 500 MB.
   - Heavy offline tools like `xgboost` (350 MB Linux binary wheel) and `bandit` were moved to `requirements-dev.txt`.
   - Production uses `HistGradientBoostingClassifier` natively from `scikit-learn`, keeping the total bundle at **~160 MB** (well under the 500 MB limit).
2. **ASGI Path Normalization (`api/index.py`)**:
   - Vercel rewrites `/(.*)` to `/api/index.py`.
   - `VercelPathFixMiddleware` intercepts incoming requests and rewrites `/api/index.py` back to `/` so FastAPI route handlers match cleanly without 404 errors.
3. **Serverless Filesystem Adaptation (`/tmp`)**:
   - Cloud serverless containers have read-only filesystems except for `/tmp`.
   - `app/db/session.py` automatically routes SQLite to `/tmp/fraud_pipeline.db` when `os.getenv("VERCEL")` is detected, ensuring crash-free database writes.

---

## 13. DevOps Stack: Docker, Kubernetes & Jenkins CI/CD

### 1. Docker Multi-Stage Build (`Dockerfile`)
- **Stage 1 (Builder)**: Installs build tools and compiles Python packages into a virtual environment `/opt/venv`.
- **Stage 2 (Runtime)**: Copies only the compiled virtualenv into a minimal, clean base image.
- **Security**: Creates an unprivileged user `appuser` (UID 10001) and switches to it. The container never runs as `root`.

### 2. Kubernetes Orchestration (`deployment.yaml`)
- **Deployment**: Maintains 2 baseline replicas of the API with resource limits (250m CPU, 512Mi memory) and readiness/liveness health probes against `/health`.
- **Service**: Exposes port 80 to internal cluster traffic via ClusterIP.
- **HorizontalPodAutoscaler (HPA)**: Monitors pod CPU utilization. If average CPU exceeds 70%, it automatically scales out from 2 up to 10 pods to absorb transaction traffic spikes.

### 3. Jenkins CI/CD Pipeline (`Jenkinsfile`)
A 15-stage declarative pipeline:
1. *Checkout SCM*: Pulls latest commit from Git.
2. *Setup Virtualenv*: Prepares Python environment.
3. *Bandit SAST*: Scans code for security vulnerabilities (fails pipeline on Medium/High flaws).
4. *Pytest Execution*: Runs all 51 unit and integration tests (fails pipeline on any test failure).
5. *Feature Store Check*: Validates temporal integrity of 36 features.
6. *Model Training*: Trains and calibrates baseline models.
7. *Quality Gate*: Validates model PR-AUC $\ge 0.85$ and latency $< 50\text{ ms}$.
8. *Docker Build*: Multi-stage container build.
9. *Image Security Audit*: Verifies container runs as non-root user.
10. *Registry Push*: Pushes tagged image to Docker registry.
11. *Kubernetes Rollout*: Executes `kubectl apply -f deployment.yaml`.
12. *HPA Check*: Confirms autoscaler status.
13. *Smoke Test*: Sends test transaction to `/predict` on deployed service.
14. *Rollback Gate*: Automatically rolls back to previous deployment if smoke test fails.
15. *Archive*: Archives test reports and security scan logs.

---

## 14. Observability: Prometheus Metrics & Grafana

The microservice exposes a native `/metrics` endpoint scraped by Prometheus:

### Exposed Prometheus Metrics
- `fraud_requests_total`: Counter tracking total transaction evaluations labeled by HTTP status (`200`, `422`, `503`).
- `fraud_predictions_total`: Counter tracking decisions broken down by tier (`ALLOW`, `STEP_UP`, `MANUAL_REVIEW`, `BLOCK`).
- `fraud_prediction_latency_seconds`: Histogram measuring inference execution time across buckets (`5ms`, `10ms`, `25ms`, `50ms`, `100ms`).
- `fraud_model_loaded`: Gauge ($1$ if models are active in memory, $0$ if unavailable).
- `fraud_score_distribution`: Histogram tracking risk scores across deciles ($0-10, 10-20, \dots, 90-100$).

### Grafana Dashboard (`config/grafana-dashboard.json`)
Pre-configured with 8 real-time visual panels:
1. Transaction Throughput (Req/sec)
2. p50, p90, p99 Inference Latency (ms)
3. Decision Breakdown Pie Chart (Allow vs Block vs Review)
4. Fraud Rate Percentage Over Time
5. HTTP Status Code Ratios (2xx vs 5xx)
6. Model In-Memory Health Indicator
7. Risk Score Distribution Heatmap
8. Population Stability Index (PSI) Drift Monitor

---

## 15. How to Run, Test, and Verify Everything Locally

### 1-Step Automatic Verification (PowerShell)
Open PowerShell in the project directory and run:
```powershell
.\verify.ps1
```
This executes the complete end-to-end verification pipeline: validates Python 3.10+, installs dependencies, trains baseline models, executes all 51 tests, and tests live HTTP endpoints.

### Running Unit Tests
```powershell
.\.venv\Scripts\pytest.exe tests/ -v
```

### Running Security SAST Scan
```powershell
.\.venv\Scripts\bandit.exe -r app/ -f screen
```

### Starting the Local Web Server
```powershell
.\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser to:
- **Web Console**: `http://127.0.0.1:8000/`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Prometheus Metrics**: `http://127.0.0.1:8000/metrics`

---

## 16. Master Viva & Technical Interview Q&A Cheatsheet

### Q1: Why not rely purely on machine learning for fraud detection?
> **Answer**: Pure machine learning has two fatal flaws in financial production:
> 1. **Zero-day vulnerability**: When a new fraud ring launches an attack never seen in historical training data, ML models have no historical pattern to detect it. Hard business rules (e.g. impossible geographic travel speed $> 800\text{ km/h}$ or $\ge 5$ swipes in 5 minutes) catch these instantly.
> 2. **Regulatory explainability**: Financial regulations (FCRA, GDPR Article 22) legally require institutions to explain adverse credit/payment decisions. Rules provide clear, defensible reason codes that pure black-box ML cannot provide alone.

### Q2: Why did you choose a Hybrid Ensemble over a single model?
> **Answer**: Different models excel at different things. Isolation Forest is unsupervised and excels at catching rare structural outliers without needing labels. HistGradientBoosting is supervised and excels at detecting subtle non-linear interactions in labeled tabular data. By taking a weighted combination ($30\%$ Rules, $30\%$ Supervised, $20\%$ Isolation Forest, $10\%$ Velocity, $10\%$ Network), we achieve high sensitivity to known fraud while remaining resilient against novel attack vectors.

### Q3: How did you prevent Data Leakage in the Feature Store?
> **Answer**: Temporal leakage occurs when features computed for a transaction at timestamp $t$ incorporate information from transactions that occurred at or after $t$. In `app/features/pipeline.py`, every sliding window calculation (1-hour count, 24-hour spend, velocity burst ratio) strictly uses the interval $[t - \Delta t, t)$. Future transactions are mathematically excluded from the customer's state at time $t$.

### Q4: Why is PR-AUC preferred over ROC-AUC in financial fraud?
> **Answer**: Financial fraud suffers from extreme class imbalance (typically $\le 1\%$ fraud). ROC-AUC plots True Positive Rate against False Positive Rate. Because True Negatives (legitimate transactions) number in the millions, the False Positive Rate denominator remains overwhelmingly large, keeping ROC-AUC deceptively high ($0.99+$) even when the model generates hundreds of false alarms. Precision-Recall AUC (PR-AUC) evaluates Precision ($\frac{\text{TP}}{\text{TP} + \text{FP}}$) against Recall ($\frac{\text{TP}}{\text{TP} + \text{FN}}$), focusing strictly on the minority fraud class.

### Q5: How is Model Drift detected in production?
> **Answer**: We track the **Population Stability Index (PSI)** in `app/models/drift.py`. The reference training score distribution is segmented into 10 quantile bins. When live transactions arrive, we compute the relative frequency shift across bins. A $\text{PSI} < 0.10$ indicates stability, $0.10 - 0.25$ indicates moderate shift, and $\text{PSI} > 0.25$ triggers automated alerting and retraining via Jenkins.

### Q6: How does the system handle high traffic spikes?
> **Answer**:
> 1. **Stateless Async Microservice**: FastAPI runs asynchronously on Uvicorn, handling concurrent non-blocking I/O.
> 2. **In-Memory Feature Cache**: Sliding windows and baselines are cached in-memory with sub-millisecond lookup latency.
> 3. **Kubernetes HPA**: Horizontal Pod Autoscaler monitors pod CPU utilization and automatically scales out replicas from 2 to 10 when CPU exceeds $70\%$.

### Q7: How does Vercel Serverless handle SQLite database writes?
> **Answer**: Cloud serverless environments (AWS Lambda, Vercel Fluid Compute) have read-only root filesystems where standard local database writes fail with `OperationalError: attempt to write a readonly database`. In `app/db/session.py`, we detect `os.getenv("VERCEL")` and dynamically redirect SQLite to the writable `/tmp/fraud_pipeline.db` path, ensuring seamless transaction auditing and analyst queue logging in cloud production.

---
*Manual compiled and preserved in local repository under `docs/PROJECT_COMPLETE_WALKTHROUGH_GUIDE.md`.*
