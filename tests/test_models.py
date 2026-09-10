"""Unit tests for ML models, drift detection, and explainability."""
import numpy as np
import pytest

from app.models.isolation_forest import IsolationForestModel
from app.models.supervised import SupervisedFraudModel
from app.models.explainability import ExplainabilityEngine
from app.models.drift import DriftDetector


def test_isolation_forest_calibrated_scoring():
    iso = IsolationForestModel()
    score, is_anom = iso.predict_anomaly({"amount": 100.0, "distance_from_home": 5.0})
    assert 0.0 <= score <= 1.0
    assert isinstance(is_anom, bool)


def test_supervised_classifier_training_and_probability():
    # Synthetic small dataset
    rng = np.random.default_rng(42)
    X = rng.standard_normal((100, 36)).astype(np.float32)
    y = np.array([0] * 90 + [1] * 10)  # Imbalanced

    model = SupervisedFraudModel()
    metrics = model.train(X[:80], y[:80], X[80:], y[80:])
    assert "pr_auc" in metrics or model.is_loaded()

    prob = model.predict_probability(X[0])
    assert 0.0 <= prob <= 1.0


def test_drift_detector_psi_calculation():
    detector = DriftDetector(num_bins=5)
    rng = np.random.default_rng(42)
    baseline = rng.normal(100.0, 15.0, 1000)
    current_stable = rng.normal(101.0, 15.0, 1000)
    current_drifted = rng.normal(250.0, 40.0, 1000)

    detector.set_reference("amount", baseline)

    res_stable = detector.check_drift("amount", current_stable)
    assert res_stable["psi"] < 0.15
    assert not res_stable["drift_detected"]

    res_drift = detector.check_drift("amount", current_drifted)
    assert res_drift["psi"] >= 0.20
    assert res_drift["drift_detected"]


def test_explainability_engine_generates_concrete_reasons():
    explainer = ExplainabilityEngine()
    features = {
        "amount": 48000.0,
        "amount_to_avg_ratio": 8.5,
        "amount_zscore": 6.2,
        "distance_from_prev_km": 1850.0,
        "travel_speed_kmh": 7400.0,
        "txn_count_5m": 6.0,
        "failed_attempts_last_24h": 4.0,
        "is_new_device": 1.0,
        "is_new_beneficiary": 1.0,
    }
    reasons, contribs = explainer.explain(
        features=features,
        rule_reasons=["Rule: Rapid failed attempts"],
        fraud_prob=0.92,
        anomaly_score=0.88,
    )
    assert len(reasons) >= 3
    assert any("48,000" in r or "8.5x" in r for r in reasons)
    assert any("7,400" in r for r in reasons)
    assert sum(contribs.values()) > 0
