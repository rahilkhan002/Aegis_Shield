"""Unit tests for Declarative Rule Engine and heuristics."""
import pytest
from app.rules.engine import RuleEngine


def test_rule_engine_normal_features_no_triggers():
    engine = RuleEngine()
    normal_features = {
        "amount": 250.0,
        "amount_to_avg_ratio": 0.8,
        "amount_zscore": 0.2,
        "is_impossible_travel": 0.0,
        "is_new_device": 0.0,
        "txn_count_5m": 1.0,
        "failed_attempts_last_24h": 0.0,
        "is_nighttime": 0.0,
        "device_associated_accounts": 1.0,
        "is_vpn_proxy": 0.0,
        "distance_from_home": 5.0,
        "is_new_beneficiary": 0.0,
        "is_cat_crypto": 0.0,
    }
    score, rules, reasons = engine.evaluate(normal_features)
    assert score == 0.0
    assert len(rules) == 0
    assert len(reasons) == 0


def test_rule_engine_impossible_travel_trigger():
    engine = RuleEngine()
    features = {
        "is_impossible_travel": 1.0,
        "amount_to_avg_ratio": 1.0,
        "amount_zscore": 0.0,
        "txn_count_5m": 1.0,
        "is_new_device": 0.0,
        "failed_attempts_last_24h": 0.0,
        "device_associated_accounts": 1.0,
        "is_vpn_proxy": 0.0,
        "distance_from_home": 1500.0,
        "is_new_beneficiary": 0.0,
        "is_nighttime": 0.0,
        "is_cat_crypto": 0.0,
    }
    score, rules, reasons = engine.evaluate(features)
    assert "RULE_IMPOSSIBLE_TRAVEL" in rules
    assert score >= 25.0
    assert any("impossible travel" in r.lower() for r in reasons)


def test_rule_engine_new_device_high_amount():
    engine = RuleEngine()
    features = {
        "is_new_device": 1.0,
        "amount_to_avg_ratio": 4.5,
        "amount_zscore": 2.1,
        "is_impossible_travel": 0.0,
        "txn_count_5m": 1.0,
        "failed_attempts_last_24h": 0.0,
        "device_associated_accounts": 1.0,
        "is_vpn_proxy": 0.0,
        "distance_from_home": 50.0,
        "is_new_beneficiary": 0.0,
        "is_nighttime": 0.0,
        "is_cat_crypto": 0.0,
    }
    score, rules, reasons = engine.evaluate(features)
    assert "RULE_NEW_DEVICE_HIGH_AMOUNT" in rules
    assert score >= 20.0
