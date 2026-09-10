"""Hybrid Multi-Engine Risk Aggregator.

Combines Rule Engine violations, Supervised ML probability, Unsupervised Anomaly
scoring, Behavioral deviation, and Network/Entity linkage into a single
normalized 0.0 - 100.0 risk score.
"""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from app.data.schema import (
    Transaction,
    TransactionEvaluationRequest,
    TransactionEvaluationResponse,
    RiskLevel,
    DecisionType,
)
from app.features.pipeline import FeaturePipeline
from app.features.store import get_feature_store
from app.rules.engine import get_rule_engine
from app.models.isolation_forest import IsolationForestModel
from app.models.supervised import SupervisedFraudModel
from app.models.explainability import ExplainabilityEngine
from app.risk.decision import classify_risk


class RiskEngine:
    """Central risk scoring orchestration engine."""

    _instance: Optional["RiskEngine"] = None

    def __init__(self):
        self.feature_pipeline = FeaturePipeline(store=get_feature_store())
        self.rule_engine = get_rule_engine()
        self.isolation_model = IsolationForestModel()
        self.supervised_model = SupervisedFraudModel()
        self.explainability_engine = ExplainabilityEngine()

    @classmethod
    def get_instance(cls) -> "RiskEngine":
        if cls._instance is None:
            cls._instance = RiskEngine()
        return cls._instance

    def compute_behavior_score(self, features: Dict[str, float]) -> float:
        """Compute behavioral anomaly risk (0.0 to 100.0)."""
        amt_ratio = features.get("amount_to_avg_ratio", 1.0)
        zscore = max(0.0, features.get("amount_zscore", 0.0))
        v_5m = features.get("txn_count_5m", 0.0)
        failed = features.get("failed_attempts_last_24h", 0.0)

        score = (
            min(40.0, (amt_ratio - 1.0) * 10.0 if amt_ratio > 1.0 else 0.0)
            + min(30.0, zscore * 6.0)
            + min(20.0, v_5m * 4.0)
            + min(15.0, failed * 5.0)
        )
        return min(100.0, max(0.0, round(score, 1)))

    def compute_network_score(self, features: Dict[str, float]) -> float:
        """Compute graph / network linkage risk (0.0 to 100.0)."""
        dev_accounts = features.get("device_associated_accounts", 1.0)
        ip_accounts = features.get("ip_associated_accounts", 1.0)
        is_vpn = features.get("is_vpn_proxy", 0.0)
        is_new_ben = features.get("is_new_beneficiary", 0.0)
        is_new_dev = features.get("is_new_device", 0.0)

        score = (
            min(40.0, (dev_accounts - 1.0) * 15.0 if dev_accounts > 1 else 0.0)
            + min(30.0, (ip_accounts - 1.0) * 10.0 if ip_accounts > 1 else 0.0)
            + (is_vpn * 20.0)
            + (is_new_dev * 15.0)
            + (is_new_ben * 15.0)
        )
        return min(100.0, max(0.0, round(score, 1)))

    def evaluate_transaction(
        self,
        txn: Union[Transaction, TransactionEvaluationRequest, Dict[str, Any]],
        update_feature_store: bool = True,
    ) -> TransactionEvaluationResponse:
        """Full multi-engine evaluation returning comprehensive risk score and decision."""
        # 1. Feature Engineering
        features = self.feature_pipeline.extract_features(txn, update_store_after=update_feature_store)

        # 2. Rule Engine Evaluation
        rule_score, triggered_rules, rule_reasons = self.rule_engine.evaluate(features)

        # 3. Supervised Model Probability
        fraud_prob = self.supervised_model.predict_probability(features)
        supervised_score = round(fraud_prob * 100.0, 1)

        # 4. Unsupervised Anomaly Scoring (Isolation Forest)
        anomaly_score, is_iso_anomaly = self.isolation_model.predict_anomaly(features)
        anomaly_risk_score = round(anomaly_score * 100.0, 1)

        # 5. Behavioral & Network Sub-Scores
        behavior_score = self.compute_behavior_score(features)
        network_score = self.compute_network_score(features)

        # 6. Weighted Hybrid Ensemble
        weights = self.rule_engine.ensemble_weights
        w_rule = weights.get("rule_weight", 0.25)
        w_sup = weights.get("supervised_weight", 0.35)
        w_anom = weights.get("anomaly_weight", 0.20)
        w_beh = weights.get("behavioral_weight", 0.12)
        w_net = weights.get("network_weight", 0.08)

        raw_final_score = (
            (w_rule * rule_score)
            + (w_sup * supervised_score)
            + (w_anom * anomaly_risk_score)
            + (w_beh * behavior_score)
            + (w_net * network_score)
        )

        # If rules detect high risk violations, ensure final score respects rule threshold
        if rule_score >= 50.0:
            raw_final_score = max(raw_final_score, rule_score * 0.9)

        # Critical rule overrides (e.g. impossible travel automatically pushes to CRITICAL tier)
        if "RULE_IMPOSSIBLE_TRAVEL" in triggered_rules:
            raw_final_score = max(raw_final_score, 88.0)

        final_risk_score = min(100.0, max(0.0, round(raw_final_score, 1)))

        # 7. Decision Tier Classification
        risk_level, decision, is_suspicious = classify_risk(final_risk_score, self.rule_engine.risk_thresholds)

        # 8. Explainability Synthesis
        importances = self.supervised_model.get_feature_importances()
        reasons, contributions = self.explainability_engine.explain(
            features=features,
            rule_reasons=rule_reasons,
            fraud_prob=fraud_prob,
            anomaly_score=anomaly_score,
            feature_importances=importances,
        )

        txn_id = (
            getattr(txn, "transaction_id", None)
            or (txn.get("transaction_id") if isinstance(txn, dict) else None)
            or "TXN_SIMULATED"
        )

        return TransactionEvaluationResponse(
            transaction_id=str(txn_id),
            risk_score=final_risk_score,
            risk_level=risk_level,
            decision=decision,
            is_suspicious=is_suspicious,
            fraud_probability=fraud_prob,
            anomaly_score=anomaly_score,
            rule_score=rule_score,
            behavior_score=behavior_score,
            network_score=network_score,
            model_version=self.supervised_model.model_version,
            processing_time_ms=0.0,
            reasons=reasons,
            triggered_rules=triggered_rules,
            feature_contributions=contributions,
            is_anomaly=is_suspicious,
        )


def get_risk_engine() -> RiskEngine:
    return RiskEngine.get_instance()
