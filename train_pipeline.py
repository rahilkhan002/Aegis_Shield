"""Full End-to-End Training, Evaluation, and Benchmarking Pipeline.

Generates realistic multi-scenario transactions, engineers 36 features,
trains Supervised XGBoost / Gradient Boosted classifier, benchmarks
against baseline models, and persists artifacts.
"""
import os
import sys
from pathlib import Path
import numpy as np

from app.data.generator import SyntheticTransactionGenerator
from app.features.pipeline import FeaturePipeline, FEATURE_NAMES
from app.models.supervised import SupervisedFraudModel
from app.models.comparison import run_model_benchmark


def main():
    print("=" * 70)
    print("  AEGISSHIELD MLOPS FRAUD DETECTION — TRAINING & BENCHMARK PIPELINE")
    print("=" * 70)

    # 1. Generate Synthetic Transactions
    print("\n[Step 1/5] Generating 10,000 realistic transactions with 18 fraud scenarios...")
    gen = SyntheticTransactionGenerator(
        num_customers=500,
        num_merchants=100,
        num_devices=800,
        fraud_rate=0.035,
        seed=42,
    )
    transactions = gen.generate_dataset(total_transactions=10000)
    fraud_count = sum(1 for t in transactions if t.is_fraud == 1)
    print(f"Generated {len(transactions)} transactions ({fraud_count} fraud, {len(transactions)-fraud_count} normal).")

    # 2. Extract Features
    print("\n[Step 2/5] Engineering 36 leakage-free features...")
    pipeline = FeaturePipeline()
    X_list = []
    y_list = []
    for t in transactions:
        vec = pipeline.extract_feature_vector(t, update_store_after=True)
        X_list.append(vec)
        y_list.append(t.is_fraud or 0)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    print(f"Feature matrix shape: {X.shape}, labels distribution: {np.bincount(y)}")

    # 3. Temporal Train / Validation Split (80% train, 20% test)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    print(f"Train set: {len(X_train)} samples ({sum(y_train)} fraud)")
    print(f"Test set:  {len(X_test)} samples ({sum(y_test)} fraud)")

    # 4. Train Supervised Classifier
    print("\n[Step 3/5] Training Supervised Fraud Classifier (XGBoost / HistGradientBoosting)...")
    sup_model = SupervisedFraudModel()
    metrics = sup_model.train(X_train, y_train, X_test, y_test, version="2.0.0")
    print(f"Model saved -> {sup_model.model_path}")
    print(f"Supervised Metrics: PR-AUC={metrics.get('pr_auc')}, ROC-AUC={metrics.get('roc_auc')}, F1={metrics.get('f1')}")

    # 5. Model Comparison Benchmark
    print("\n[Step 4/5] Running Multi-Model Benchmark Comparison...")
    benchmarks = run_model_benchmark(X_train, y_train, X_test, y_test)

    # Format Markdown comparison table
    md_lines = [
        "# Model Comparison & Evaluation Benchmark Results",
        "",
        "Evaluation performed on held-out temporal validation test set with extreme class imbalance (~3.5% fraud).",
        "",
        "| Model Architecture | Model Category | PR-AUC | F1 Score | ROC-AUC | Latency (ms) |",
        "| :--- | :--- | :---: | :---: | :---: | :---: |",
    ]
    for b in benchmarks:
        md_lines.append(
            f"| **{b['model']}** | {b['type']} | **{b['pr_auc']:.4f}** | {b['f1']:.4f} | {b['roc_auc']:.4f} | {b['latency_ms']:.2f} ms |"
        )

    md_lines.extend([
        "",
        "> [!IMPORTANT]",
        "> **Metric Selection Rationale**: In highly imbalanced financial fraud datasets, **PR-AUC (Precision-Recall Area Under Curve)** is significantly more informative than ROC-AUC because it focuses on the minority positive fraud class without being inflated by overwhelming true negatives.",
    ])

    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    benchmark_path = docs_dir / "MODEL_BENCHMARK.md"
    benchmark_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"\nSaved benchmark comparison table -> {benchmark_path}")

    print("\n[Step 5/5] Benchmark Summary:")
    for b in benchmarks:
        print(f"  * {b['model']:<35} PR-AUC: {b['pr_auc']:.4f} | F1: {b['f1']:.4f} | Latency: {b['latency_ms']:.2f} ms")

    print("\n" + "=" * 70)
    print("  TRAINING & BENCHMARK COMPLETED SUCCESSFULLY")
    print("=" * 70)


if __name__ == "__main__":
    main()
