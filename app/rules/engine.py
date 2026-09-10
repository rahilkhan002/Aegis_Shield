"""Configurable Declarative Fraud Rule Engine with Safe AST Condition Evaluation.

Evaluates high-priority business and security heuristics against
engineered transaction features without hard-coding logic in routes
or using unsafe eval() calls.
"""
from __future__ import annotations
import ast
import logging
import operator
import os
from typing import Any, Dict, List, Optional, Tuple
import yaml

logger = logging.getLogger(__name__)

_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


def _eval_node(node: ast.AST, scope: Dict[str, Any]) -> Any:
    """Safely evaluates an AST node without invoking eval."""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, scope)
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Name):
        return scope.get(node.id, 0.0)
    elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_eval_node(node.operand, scope)
    elif isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(bool(_eval_node(val, scope)) for val in node.values)
        elif isinstance(node.op, ast.Or):
            return any(bool(_eval_node(val, scope)) for val in node.values)
    elif isinstance(node, ast.Compare):
        left = _eval_node(node.left, scope)
        for op, comparator in zip(node.ops, node.comparators):
            op_fn = _OPERATORS.get(type(op))
            if not op_fn:
                return False
            right = _eval_node(comparator, scope)
            if not op_fn(left, right):
                return False
            left = right
        return True
    return False


def safe_eval_condition(cond_str: str, scope: Dict[str, Any]) -> bool:
    """Parses and safely checks a boolean condition string."""
    try:
        tree = ast.parse(cond_str.strip(), mode="eval")
        return bool(_eval_node(tree, scope))
    except Exception as err:
        logger.debug("Safe condition eval exception: %s", err)
        return False


class RuleEngine:
    """Evaluates declarative fraud rules from YAML configuration."""

    _instance: Optional["RuleEngine"] = None

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules.yaml")
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.risk_thresholds: Dict[str, float] = {"low": 30.0, "medium": 60.0, "high": 80.0}
        self.ensemble_weights: Dict[str, float] = {
            "rule_weight": 0.25,
            "supervised_weight": 0.35,
            "anomaly_weight": 0.20,
            "behavioral_weight": 0.12,
            "network_weight": 0.08,
        }
        self.load_config()

    @classmethod
    def get_instance(cls) -> "RuleEngine":
        if cls._instance is None:
            cls._instance = RuleEngine()
        return cls._instance

    def load_config(self):
        """Load or reload YAML rules definition."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    self.rules = data.get("rules", {})
                    self.risk_thresholds = data.get("risk_thresholds", self.risk_thresholds)
                    self.ensemble_weights = data.get("ensemble_weights", self.ensemble_weights)
            except Exception as e:
                logger.warning("Could not load YAML config, using fallback rules: %s", e)
                self._load_fallback_rules()
        else:
            self._load_fallback_rules()

    def _load_fallback_rules(self):
        self.rules = {
            "RULE_IMPOSSIBLE_TRAVEL": {
                "enabled": True,
                "weight": 25.0,
                "description": "Impossible travel speed detected between consecutive transactions (>850 km/h)",
                "condition": "is_impossible_travel == 1.0",
            },
            "RULE_NEW_DEVICE_HIGH_AMOUNT": {
                "enabled": True,
                "weight": 20.0,
                "description": "High value transaction from an unrecognized new device",
                "condition": "is_new_device == 1.0 and amount_to_avg_ratio >= 3.0",
            },
            "RULE_HIGH_VELOCITY_5M": {
                "enabled": True,
                "weight": 20.0,
                "description": "Abnormal transaction velocity (>5 transactions in 5 minutes)",
                "condition": "txn_count_5m >= 5.0",
            },
            "RULE_AMOUNT_ZSCORE_EXCEEDED": {
                "enabled": True,
                "weight": 18.0,
                "description": "Transaction amount exceeds 4 standard deviations from customer baseline",
                "condition": "amount_zscore >= 4.0",
            },
        }

    def evaluate(self, features: Dict[str, float]) -> Tuple[float, List[str], List[str]]:
        """Evaluate features against all active rules safely.

        Returns:
            rule_score: Normalized 0.0 - 100.0 aggregate rule risk score
            triggered_rules: List of rule IDs that fired
            reasons: Human-readable risk explanations
        """
        raw_score = 0.0
        triggered_rules: List[str] = []
        reasons: List[str] = []

        eval_scope = dict(features)

        for rule_id, rule_def in self.rules.items():
            if not rule_def.get("enabled", True):
                continue

            cond = rule_def.get("condition", "")
            weight = float(rule_def.get("weight", 10.0))
            desc = rule_def.get("description", rule_id)

            matched = safe_eval_condition(cond, eval_scope)
            if matched:
                raw_score += weight
                triggered_rules.append(rule_id)
                reasons.append(desc)

        normalized_score = min(100.0, max(0.0, round(raw_score, 1)))
        return normalized_score, triggered_rules, reasons


def get_rule_engine() -> RuleEngine:
    return RuleEngine.get_instance()
