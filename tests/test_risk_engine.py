"""Unit tests for Hybrid Risk Engine and Decision Classification."""
import pytest
from app.risk.engine import RiskEngine
from app.risk.decision import classify_risk
from app.data.schema import RiskLevel, DecisionType


def test_classify_risk_thresholds():
    thresholds = {"low": 30.0, "medium": 60.0, "high": 80.0}

    # Low / Allow
    lvl, dec, is_susp = classify_risk(18.5, thresholds)
    assert lvl == RiskLevel.LOW
    assert dec == DecisionType.ALLOW
    assert not is_susp

    # Medium / Step-up
    lvl, dec, is_susp = classify_risk(45.0, thresholds)
    assert lvl == RiskLevel.MEDIUM
    assert dec == DecisionType.STEP_UP
    assert not is_susp

    # High / Manual review
    lvl, dec, is_susp = classify_risk(72.0, thresholds)
    assert lvl == RiskLevel.HIGH
    assert dec == DecisionType.MANUAL_REVIEW
    assert is_susp

    # Critical / Block
    lvl, dec, is_susp = classify_risk(92.5, thresholds)
    assert lvl == RiskLevel.CRITICAL
    assert dec == DecisionType.BLOCK
    assert is_susp


def test_risk_engine_full_evaluation():
    engine = RiskEngine()
    txn = {
        "transaction_id": "TXN_TEST_FULL_EVAL",
        "amount": 250.0,
        "distance_from_home": 3.0,
        "customer_id": "CUS_NORMAL",
        "account_id": "ACC_NORMAL",
        "customer_avg_amount_30d": 300.0,
        "customer_txn_count_last_1h": 1,
        "failed_attempts_last_24h": 0,
    }
    response = engine.evaluate_transaction(txn)
    assert 0.0 <= response.risk_score <= 100.0
    assert response.decision in [DecisionType.ALLOW, DecisionType.STEP_UP, DecisionType.MANUAL_REVIEW, DecisionType.BLOCK]
    assert len(response.reasons) > 0
