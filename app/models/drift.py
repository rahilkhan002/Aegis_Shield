"""Drift Detection and Distribution Monitoring.

Computes Population Stability Index (PSI) and Kolmogorov-Smirnov (KS) metrics
to track feature distribution drift, prediction drift, and anomaly-rate drift.
"""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.stats import ks_2samp


class DriftDetector:
    """Computes distribution stability and statistical drift between baseline and production data."""

    def __init__(self, num_bins: int = 10):
        self.num_bins = num_bins
        # Reference distributions for key features
        self.reference_data: Dict[str, np.ndarray] = {}

    def set_reference(self, feature_name: str, values: np.ndarray):
        """Set baseline training distribution for a feature or risk score."""
        clean = np.asarray(values, dtype=np.float64)
        clean = clean[~np.isnan(clean)]
        self.reference_data[feature_name] = clean

    def calculate_psi(
        self,
        reference: np.ndarray,
        current: np.ndarray,
        epsilon: float = 1e-4,
    ) -> float:
        """Calculate Population Stability Index (PSI).

        PSI < 0.10: No significant shift (Stable)
        0.10 <= PSI < 0.25: Moderate shift (Monitor)
        PSI >= 0.25: Significant distributional drift (Retraining Alert)
        """
        ref = np.asarray(reference, dtype=np.float64)
        cur = np.asarray(current, dtype=np.float64)

        if len(ref) < 10 or len(cur) < 10:
            return 0.0

        # Create quantile bins based on reference distribution
        percentiles = np.linspace(0, 100, self.num_bins + 1)
        bin_edges = np.percentile(ref, percentiles)
        bin_edges = np.unique(bin_edges)

        if len(bin_edges) < 2:
            return 0.0

        # Frequency counts
        ref_counts, _ = np.histogram(ref, bins=bin_edges)
        cur_counts, _ = np.histogram(cur, bins=bin_edges)

        ref_pct = (ref_counts / len(ref)) + epsilon
        cur_pct = (cur_counts / len(cur)) + epsilon

        # Normalize probabilities
        ref_pct /= np.sum(ref_pct)
        cur_pct /= np.sum(cur_pct)

        psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        return round(float(psi), 4)

    def calculate_ks(self, reference: np.ndarray, current: np.ndarray) -> Tuple[float, float]:
        """Perform two-sample Kolmogorov-Smirnov test.

        Returns (statistic, p_value).
        """
        ref = np.asarray(reference, dtype=np.float64)
        cur = np.asarray(current, dtype=np.float64)

        if len(ref) < 5 or len(cur) < 5:
            return 0.0, 1.0

        res = ks_2samp(ref, cur)
        return round(float(res.statistic), 4), round(float(res.pvalue), 6)

    def check_drift(
        self, feature_name: str, current_values: np.ndarray
    ) -> Dict[str, Any]:
        """Check whether a feature has experienced significant drift."""
        ref = self.reference_data.get(feature_name)
        if ref is None:
            return {
                "feature": feature_name,
                "status": "NO_BASELINE",
                "psi": 0.0,
                "ks_stat": 0.0,
                "drift_detected": False,
            }

        psi = self.calculate_psi(ref, current_values)
        ks_stat, p_val = self.calculate_ks(ref, current_values)

        drift_detected = (psi >= 0.20) or (ks_stat >= 0.15 and p_val < 0.01)
        status = "CRITICAL_DRIFT" if psi >= 0.25 else ("MODERATE_DRIFT" if psi >= 0.10 else "STABLE")

        return {
            "feature": feature_name,
            "status": status,
            "psi": psi,
            "ks_stat": ks_stat,
            "p_value": p_val,
            "drift_detected": drift_detected,
        }
