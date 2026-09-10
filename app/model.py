"""
model.py
--------
Isolation Forest model training and serialization module.

This script is designed to be run as a standalone entrypoint to generate the
model artifact (model.pkl). It is also importable so that `main.py` can load
the serialized model at startup.

Usage:
    python -m app.model           # Trains and serializes the model
"""

import logging
import os
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default artifact path — resolvable both inside the container (/app/model.pkl)
# and from the project root during local development.
MODEL_DIR = Path(os.getenv("MODEL_DIR", Path(__file__).parent.parent))
MODEL_PATH = MODEL_DIR / "model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"

# Random seed for reproducibility
RANDOM_STATE = 42

# IsolationForest hyperparameters tuned for a financial fraud use-case where
# anomalies represent ~2-5% of total transactions.
CONTAMINATION = 0.04
N_ESTIMATORS = 200
MAX_SAMPLES = "auto"
MAX_FEATURES = 1.0

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Training data generation
# ---------------------------------------------------------------------------

def generate_synthetic_training_data(
    n_normal: int = 10_000,
    n_anomalies: int = 400,
    random_state: int = RANDOM_STATE,
) -> np.ndarray:
    """
    Generate synthetic credit-card transaction data.

    Features
    --------
    - ``amount``              : Transaction value in USD.
    - ``distance_from_home``  : Geographic distance (km) between merchant and
                                cardholder's registered home address.

    Normal transactions cluster around low-to-medium amounts and short
    distances from home. Anomalous (fraudulent) transactions are characterized
    by unusually high amounts and/or unusually large distances.

    Returns
    -------
    np.ndarray
        Shape (n_normal + n_anomalies, 2).
    """
    rng = np.random.default_rng(random_state)

    # Legitimate transactions
    normal_amount = rng.lognormal(mean=4.5, sigma=0.8, size=n_normal)       # ~$50–300 range
    normal_distance = rng.lognormal(mean=2.0, sigma=1.0, size=n_normal)     # ~1–50 km

    # Fraudulent transactions — deliberately in tail regions
    fraud_amount = rng.uniform(low=800, high=5_000, size=n_anomalies)
    fraud_distance = rng.uniform(low=200, high=1_500, size=n_anomalies)

    normal_data = np.column_stack([normal_amount, normal_distance])
    fraud_data = np.column_stack([fraud_amount, fraud_distance])

    data = np.vstack([normal_data, fraud_data])
    logger.info(
        "Generated training dataset: %d normal + %d anomalous = %d total samples.",
        n_normal,
        n_anomalies,
        len(data),
    )
    return data


# ---------------------------------------------------------------------------
# Model training
# ---------------------------------------------------------------------------

def train_model(data: np.ndarray) -> tuple[IsolationForest, StandardScaler]:
    """
    Fit a ``StandardScaler`` and an ``IsolationForest`` on the supplied data.

    The scaler is fitted first so that the Isolation Forest operates on
    zero-mean, unit-variance features — this improves split quality when
    features have very different magnitudes (e.g. amount vs. distance).

    Parameters
    ----------
    data : np.ndarray
        Raw feature matrix of shape (n_samples, 2).

    Returns
    -------
    tuple[IsolationForest, StandardScaler]
        Trained model and fitted scaler, respectively.
    """
    logger.info("Fitting StandardScaler ...")
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)

    logger.info(
        "Training IsolationForest (n_estimators=%d, contamination=%.2f) ...",
        N_ESTIMATORS,
        CONTAMINATION,
    )
    model = IsolationForest(
        n_estimators=N_ESTIMATORS,
        max_samples=MAX_SAMPLES,
        max_features=MAX_FEATURES,
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(scaled_data)
    logger.info("Model training complete.")
    return model, scaler


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def save_artifacts(model: IsolationForest, scaler: StandardScaler) -> None:
    """Serialize the trained model and scaler to disk using Joblib."""
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, MODEL_PATH, compress=3)
    logger.info("Model artifact saved -> %s", MODEL_PATH)

    joblib.dump(scaler, SCALER_PATH, compress=3)
    logger.info("Scaler artifact saved -> %s", SCALER_PATH)


def load_artifacts() -> tuple[IsolationForest, StandardScaler]:
    """
    Load the serialized model and scaler from disk.

    Raises
    ------
    FileNotFoundError
        If either artifact file is absent.
    ValueError
        If the loaded object is not the expected type (guards against
        corrupted or tampered pickle files).
    RuntimeError
        Wraps any unexpected deserialization errors.
    """
    for path, label in [(MODEL_PATH, "model"), (SCALER_PATH, "scaler")]:
        if not path.exists():
            raise FileNotFoundError(
                f"Required artifact not found: '{path}'. "
                "Run `python -m app.model` to generate it before starting the server."
            )

    try:
        model: IsolationForest = joblib.load(MODEL_PATH)
        scaler: StandardScaler = joblib.load(SCALER_PATH)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to deserialize artifacts from '{MODEL_PATH}' / '{SCALER_PATH}'. "
            "The files may be corrupted. Delete them and re-run `python -m app.model`."
        ) from exc

    if not isinstance(model, IsolationForest):
        raise ValueError(
            f"Loaded object from '{MODEL_PATH}' is not an IsolationForest instance "
            f"(got {type(model).__name__}). Artifact may be corrupted or from an "
            "incompatible version."
        )
    if not isinstance(scaler, StandardScaler):
        raise ValueError(
            f"Loaded object from '{SCALER_PATH}' is not a StandardScaler instance "
            f"(got {type(scaler).__name__}). Artifact may be corrupted."
        )

    logger.info("Artifacts loaded successfully from '%s'.", MODEL_DIR)
    return model, scaler


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("=== MLOps Fraud Detection - Model Training Script ===")
    training_data = generate_synthetic_training_data()
    trained_model, fitted_scaler = train_model(training_data)
    save_artifacts(trained_model, fitted_scaler)
    logger.info("All artifacts saved. Ready for deployment.")
