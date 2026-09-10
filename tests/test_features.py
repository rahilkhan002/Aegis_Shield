"""Unit tests for Feature Pipeline and Sliding Window Feature Store."""
from datetime import datetime, timedelta
import numpy as np
import pytest

from app.features.pipeline import FeaturePipeline, FEATURE_NAMES
from app.features.store import FeatureStore


def test_feature_pipeline_names_and_shape():
    store = FeatureStore()
    pipeline = FeaturePipeline(store=store)
    
    txn = {
        "amount": 2500.0,
        "distance_from_home": 15.0,
        "customer_id": "CUS_TEST_01",
        "account_id": "ACC_TEST_01",
        "timestamp": datetime.utcnow(),
    }
    
    vec = pipeline.extract_feature_vector(txn)
    assert isinstance(vec, np.ndarray)
    assert len(vec) == len(FEATURE_NAMES)
    assert np.all(np.isfinite(vec))


def test_feature_store_prevents_temporal_leakage():
    store = FeatureStore()
    now = datetime(2025, 1, 15, 12, 0, 0)
    customer_id = "CUS_LEAK_TEST"

    # Transaction 1: 10 minutes prior
    store.update_with_transaction(
        customer_id=customer_id,
        account_id="ACC_01",
        amount=100.0,
        timestamp=now - timedelta(minutes=10),
    )

    # Future transaction (should NEVER be counted)
    store.update_with_transaction(
        customer_id=customer_id,
        account_id="ACC_01",
        amount=5000.0,
        timestamp=now + timedelta(minutes=5),
    )

    velocities = store.get_velocity_features(customer_id, now)
    assert velocities["txn_count_1h"] == 1.0
    assert velocities["txn_amount_sum_1h"] == 100.0
    # The 5000.0 future transaction was NOT included in sum
    assert velocities["txn_amount_sum_24h"] == 100.0


def test_impossible_travel_calculation():
    store = FeatureStore()
    customer_id = "CUS_TRAVEL_TEST"
    t1 = datetime(2025, 1, 15, 10, 0, 0)
    t2 = datetime(2025, 1, 15, 10, 15, 0) # 15 minutes later

    # Location 1: Delhi (28.6139, 77.2090)
    store.update_with_transaction(
        customer_id=customer_id,
        account_id="ACC_01",
        amount=150.0,
        timestamp=t1,
        latitude=28.6139,
        longitude=77.2090,
    )

    # Location 2: Dubai (25.2048, 55.2708) ~2150 km away in 15 mins -> speed ~8,600 km/h
    delta = store.get_location_delta(customer_id, 25.2048, 55.2708, t2)
    assert delta["distance_from_prev_km"] > 2000.0
    assert delta["travel_speed_kmh"] > 7000.0
    assert delta["is_impossible_travel"] == 1.0
