# Model Comparison & Evaluation Benchmark Results

Evaluation performed on held-out temporal validation test set with extreme class imbalance (~3.5% fraud).

| Model Architecture | Model Category | PR-AUC | F1 Score | ROC-AUC | Latency (ms) |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Baseline Isolation Forest** | Unsupervised Anomaly | **0.4678** | 0.3299 | 0.8742 | 5.59 ms |
| **Logistic Regression** | Linear Supervised | **0.9736** | 0.6316 | 0.9995 | 0.00 ms |
| **Random Forest** | Ensemble Trees | **0.9909** | 0.7895 | 0.9998 | 0.01 ms |
| **Gradient Boosted Classifier (XGBoost)** | Gradient Boosting | **1.0000** | 0.9831 | 1.0000 | 0.00 ms |
| **Hybrid Risk Engine (Production)** | Multi-Engine Ensemble | **0.9979** | 0.9831 | 1.0000 | 5.59 ms |

> [!IMPORTANT]
> **Metric Selection Rationale**: In highly imbalanced financial fraud datasets, **PR-AUC (Precision-Recall Area Under Curve)** is significantly more informative than ROC-AUC because it focuses on the minority positive fraud class without being inflated by overwhelming true negatives.