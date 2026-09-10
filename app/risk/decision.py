"""Decision Engine mapping Risk Scores (0-100) to operational actions."""
from __future__ import annotations
from typing import Dict, Tuple
from app.data.schema import RiskLevel, DecisionType


def classify_risk(
    risk_score: float, thresholds: Dict[str, float]
) -> Tuple[RiskLevel, DecisionType, bool]:
    """Classify 0-100 risk score into risk levels and automated business decisions.

    Thresholds:
      low: default 30.0 -> LOW, ALLOW
      medium: default 60.0 -> MEDIUM, STEP_UP (OTP, 3DS, Biometric)
      high: default 80.0 -> HIGH, MANUAL_REVIEW (Analyst queue)
      >= high -> CRITICAL, BLOCK (Immediate rejection & alert)

    Returns:
        (risk_level, decision_type, is_suspicious)
    """
    t_low = float(thresholds.get("low", 30.0))
    t_med = float(thresholds.get("medium", 60.0))
    t_high = float(thresholds.get("high", 80.0))

    if risk_score < t_low:
        return RiskLevel.LOW, DecisionType.ALLOW, False
    elif risk_score < t_med:
        return RiskLevel.MEDIUM, DecisionType.STEP_UP, False
    elif risk_score < t_high:
        return RiskLevel.HIGH, DecisionType.MANUAL_REVIEW, True
    else:
        return RiskLevel.CRITICAL, DecisionType.BLOCK, True
