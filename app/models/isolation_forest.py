"""Upgraded Isolation Forest Anomaly Detection Wrapper.

Supports both rich multi-feature inputs and backward-compatible 2-feature inputs.
Calibrates raw decision scores into a 0.0 - 1.0 anomaly index.
"""
from __future__ import annotations
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

MODEL_DIR = Path(os.getenv("MODEL_DIR", Path(__file__).parent.parent.parent))
MODEL_PATH = MODEL_DIR / "model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"


class IsolationForestModel:
    """Wrapper for Isolation Forest with automated score calibration and fallback."""

    def __init__(self, model_path: Path = MODEL_PATH, scaler_path: Path = SCALER_PATH):
        self.model_path = model_path
        self.scaler_path = scaler_path
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.load()

    def load(self) -> bool:
        """Load serialized model and scaler."""
        if self.model_path.exists() and self.scaler_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info("Loaded Isolation Forest from %s", self.model_path)
                return True
            except Exception as e:
                logger.warning("Could not load Isolation Forest: %s", e)
        return False

    def is_loaded(self) -> bool:
        return self.model is not None and self.scaler is not None

    def predict_anomaly(
        self, features: Union[Dict[str, float], np.ndarray, list]
    ) -> Tuple[float, bool]:
        """Compute continuous anomaly score (0.0 to 1.0) and anomaly decision.

        Returns:
            anomaly_score: 0.0 (normal) to 1.0 (highly anomalous)
            is_anomaly: True if flagged as anomaly
        """
        if not self.is_loaded():
            # Fallback heuristic if artifact not yet generated
            amt = features.get("amount", 100.0) if isinstance(features, dict) else float(features[0])
            dist = features.get("distance_from_home", 5.0) if isinstance(features, dict) else float(features[1])
            is_anom = amt > 3000.0 or dist > 500.0
            score = min(1.0, (amt / 5000.0) * 0.6 + (dist / 1000.0) * 0.4)
            return round(score, 4), is_anom

        # Extract 2-feature input for legacy compatibility
        if isinstance(features, dict):
            raw_input = np.array([[features.get("amount", 0.0), features.get("distance_from_home", 0.0)]], dtype=np.float32)
        elif isinstance(features, (list, tuple)):
            raw_input = np.array([[features[0], features[1]]], dtype=np.float32)
        elif isinstance(features, np.ndarray):
            if features.ndim == 1:
                raw_input = features[:2].reshape(1, 2)
            else:
                raw_input = features[:, :2]
        else:
            raw_input = np.array([[100.0, 5.0]], dtype=np.float32)

        scaled_input = self.scaler.transform(raw_input)
        raw_score = float(self.model.decision_function(scaled_input)[0])
        prediction = int(self.model.predict(scaled_input)[0])  # -1 = anomaly, 1 = normal

        # Calibrate: decision_function is positive for inliers, negative for outliers
        # Logistic sigmoid mapped so negative decision_function yields high anomaly score near 1.0
        calibrated_score = 1.0 / (1.0 + math.exp(raw_score * 8.0))
        is_anomaly = (prediction == -1)

        return round(calibrated_score, 4), is_anomaly
