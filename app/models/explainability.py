"""Explainability Engine for Financial Fraud Decisions.

Translates model probabilities, tree split importances, and rule triggers
into concrete, human-readable explanations with actual figures.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


class ExplainabilityEngine:
    """Generates human-readable risk reasons and feature importance breakdowns."""

    def __init__(self):
        pass

    def explain(
        self,
        features: Dict[str, float],
        rule_reasons: List[str],
        fraud_prob: float,
        anomaly_score: float,
        feature_importances: Optional[Dict[str, float]] = None,
    ) -> Tuple[List[str], Dict[str, float]]:
        """Synthesize explainable factors into ranked risk reasons and relative contributions."""
        reasons: List[str] = list(rule_reasons)
        contributions: Dict[str, float] = {}

        amt = features.get("amount", 0.0)
        amt_ratio = features.get("amount_to_avg_ratio", 1.0)
        zscore = features.get("amount_zscore", 0.0)
        speed = features.get("travel_speed_kmh", 0.0)
        dist_prev = features.get("distance_from_prev_km", 0.0)
        dist_home = features.get("distance_from_home", 0.0)
        v_5m = features.get("txn_count_5m", 0.0)
        v_1h = features.get("txn_count_1h", 0.0)
        failed = features.get("failed_attempts_last_24h", 0.0)
        is_new_dev = features.get("is_new_device", 0.0)
        is_new_ben = features.get("is_new_beneficiary", 0.0)
        is_night = features.get("is_nighttime", 0.0)
        dev_accounts = features.get("device_associated_accounts", 1.0)
        is_vpn = features.get("is_vpn_proxy", 0.0)

        # Dynamic specific reasons with concrete numbers
        if amt_ratio >= 3.0 and not any("customer" in r.lower() for r in reasons):
            reasons.append(
                f"Transaction amount ({amt:,.2f}) is {amt_ratio:.1f}x the customer's 30-day average baseline"
            )

        if speed > 850.0 and dist_prev > 150.0 and not any("impossible travel" in r.lower() for r in reasons):
            reasons.append(
                f"Impossible travel speed: {dist_prev:,.0f} km away with implied velocity of {speed:,.0f} km/h"
            )

        if v_5m >= 4.0 and not any("velocity" in r.lower() for r in reasons):
            reasons.append(
                f"Severe velocity spike: {int(v_5m)} transactions executed in the last 5 minutes"
            )

        if failed >= 3.0 and not any("failed" in r.lower() for r in reasons):
            reasons.append(
                f"{int(failed)} failed authentication attempts recorded within the last 24 hours"
            )

        if is_new_dev == 1.0 and not any("new device" in r.lower() for r in reasons):
            reasons.append("Transaction originated from an unrecognized new device")

        if is_new_ben == 1.0 and not any("new beneficiary" in r.lower() for r in reasons):
            reasons.append("Fund transfer directed to an unverified new beneficiary")

        if dev_accounts >= 3.0 and not any("device associated" in r.lower() for r in reasons):
            reasons.append(f"Device fingerprint linked to {int(dev_accounts)} separate customer accounts")

        if is_vpn == 1.0 and not any("vpn" in r.lower() for r in reasons):
            reasons.append("Transaction executed via hosting provider or VPN proxy exit node")

        if is_night == 1.0 and amt_ratio >= 2.0 and not any("night" in r.lower() for r in reasons):
            reasons.append("Unusual high-value activity during nighttime hours (01:00 - 05:00 AM)")

        # Compute relative feature contributions for visual charts
        raw_contrib = {
            "Amount Baseline Deviation": max(0.0, (amt_ratio - 1.0) * 8.0 + max(0.0, zscore * 5.0)),
            "Travel / Geo Velocity": min(40.0, (speed / 100.0) * 4.0 + (dist_home / 500.0) * 2.0),
            "Transaction Velocity": min(35.0, v_5m * 6.0 + v_1h * 2.0),
            "Device & Network Risk": (is_new_dev * 18.0) + (is_vpn * 12.0) + (max(0.0, dev_accounts - 1.0) * 10.0),
            "Failed Attempts": min(25.0, failed * 8.0),
            "Beneficiary & Entity Risk": (is_new_ben * 20.0),
            "ML Model Anomaly Score": anomaly_score * 30.0,
        }

        total_c = sum(raw_contrib.values())
        if total_c > 0:
            contributions = {k: round((v / total_c) * 100.0, 1) for k, v in raw_contrib.items() if v > 0}
        else:
            contributions = {"Normal Baseline": 100.0}

        if not reasons and fraud_prob < 0.2:
            reasons.append("All behavioral indicators, velocity counters, and device checks within normal parameters")

        return reasons, contributions
