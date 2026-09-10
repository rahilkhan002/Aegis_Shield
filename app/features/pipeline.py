"""Leakage-free Feature Engineering Pipeline.

Extracts normalized numerical feature vectors for model training and real-time inference.
Guarantees temporal ordering: only observations prior to the transaction timestamp are used.
"""
from __future__ import annotations
from datetime import datetime
import math
from typing import Any, Dict, List, Optional, Union
import numpy as np

from app.data.schema import (
    Transaction,
    TransactionEvaluationRequest,
    TransactionType,
    PaymentMethod,
    MerchantCategory,
)
from app.features.store import FeatureStore, get_feature_store


# Canonical list of ordered feature names used by models
FEATURE_NAMES: List[str] = [
    "amount",
    "log_amount",
    "distance_from_home",
    "hour_of_day",
    "hour_sin",
    "hour_cos",
    "day_of_week",
    "is_weekend",
    "is_nighttime",
    "txn_count_1m",
    "txn_count_5m",
    "txn_count_1h",
    "txn_count_24h",
    "txn_amount_sum_1h",
    "txn_amount_sum_24h",
    "amount_to_avg_ratio",
    "amount_zscore",
    "amount_deviation",
    "is_new_device",
    "is_vpn_proxy",
    "device_associated_accounts",
    "ip_associated_accounts",
    "distance_from_prev_km",
    "travel_speed_kmh",
    "is_impossible_travel",
    "failed_attempts_last_24h",
    "is_new_beneficiary",
    "is_type_transfer",
    "is_type_cash_out",
    "is_type_purchase",
    "is_method_upi",
    "is_method_credit",
    "is_method_net_banking",
    "is_cat_crypto",
    "is_cat_gambling",
    "is_cat_luxury",
]


class FeaturePipeline:
    """Transforms raw transactions into leakage-free numerical feature vectors."""

    def __init__(self, store: Optional[FeatureStore] = None):
        self.store = store or get_feature_store()

    def extract_features(
        self,
        txn: Union[Transaction, TransactionEvaluationRequest, Dict[str, Any]],
        update_store_after: bool = False,
    ) -> Dict[str, float]:
        """Extract a full dictionary of engineered features."""
        # Normalize input to dict or attributes
        if isinstance(txn, dict):
            t_amount = float(txn.get("amount", 100.0))
            t_dist = float(txn.get("distance_from_home", 5.0))
            t_time = txn.get("timestamp") or datetime.utcnow()
            if isinstance(t_time, str):
                try:
                    t_time = datetime.fromisoformat(t_time.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    t_time = datetime.utcnow()
            customer_id = str(txn.get("customer_id", "CUS_DEFAULT"))
            account_id = str(txn.get("account_id", "ACC_DEFAULT"))
            device_id = txn.get("device_id")
            ip_address = txn.get("ip_address")
            beneficiary_id = txn.get("beneficiary_id")
            merchant_id = txn.get("merchant_id")
            lat = txn.get("latitude")
            lon = txn.get("longitude")
            is_new_dev = bool(txn.get("is_new_device", False))
            is_vpn = bool(txn.get("is_vpn_proxy", False))
            is_new_ben = bool(txn.get("is_new_beneficiary", False))
            txn_type = str(txn.get("transaction_type", "PURCHASE"))
            pay_method = str(txn.get("payment_method", "UPI"))
            merch_cat = str(txn.get("merchant_category", "ONLINE_RETAIL"))
            override_avg = txn.get("customer_avg_amount_30d")
            override_cnt_1h = txn.get("customer_txn_count_last_1h")
            override_cnt_24h = txn.get("customer_txn_count_last_24h")
            override_failed = txn.get("failed_attempts_last_24h")
        else:
            t_amount = float(txn.amount)
            t_dist = float(txn.distance_from_home or 0.0)
            t_time = txn.timestamp or datetime.utcnow()
            if hasattr(t_time, "tzinfo") and t_time.tzinfo is not None:
                t_time = t_time.replace(tzinfo=None)
            customer_id = getattr(txn, "customer_id", "CUS_DEFAULT") or "CUS_DEFAULT"
            account_id = getattr(txn, "account_id", "ACC_DEFAULT") or "ACC_DEFAULT"
            device_id = getattr(txn, "device_id", None)
            ip_address = getattr(txn, "ip_address", None)
            beneficiary_id = getattr(txn, "beneficiary_id", None)
            merchant_id = getattr(txn, "merchant_id", None)
            lat = getattr(txn, "latitude", None)
            lon = getattr(txn, "longitude", None)
            is_new_dev = bool(getattr(txn, "is_new_device", False))
            is_vpn = bool(getattr(txn, "is_vpn_proxy", False))
            is_new_ben = bool(getattr(txn, "is_new_beneficiary", False))
            txn_type = str(getattr(txn, "transaction_type", "PURCHASE").value if hasattr(getattr(txn, "transaction_type", ""), "value") else getattr(txn, "transaction_type", "PURCHASE"))
            pay_method = str(getattr(txn, "payment_method", "UPI").value if hasattr(getattr(txn, "payment_method", ""), "value") else getattr(txn, "payment_method", "UPI"))
            merch_cat = str(getattr(txn, "merchant_category", "ONLINE_RETAIL").value if hasattr(getattr(txn, "merchant_category", ""), "value") else getattr(txn, "merchant_category", "ONLINE_RETAIL"))
            override_avg = getattr(txn, "customer_avg_amount_30d", None)
            override_cnt_1h = getattr(txn, "customer_txn_count_last_1h", None)
            override_cnt_24h = getattr(txn, "customer_txn_count_last_24h", None)
            override_failed = getattr(txn, "failed_attempts_last_24h", None)

        # 1. Base & Log Amount
        log_amount = math.log1p(max(0.0, t_amount))

        # 2. Temporal Features
        hour = float(t_time.hour)
        hour_rad = 2.0 * math.pi * hour / 24.0
        hour_sin = math.sin(hour_rad)
        hour_cos = math.cos(hour_rad)
        dow = float(t_time.weekday())
        is_weekend = 1.0 if dow in [5, 6] else 0.0
        is_nighttime = 1.0 if hour in [1, 2, 3, 4] else 0.0

        # 3. Velocity & Store Features
        velocities = self.store.get_velocity_features(customer_id, t_time)
        if override_cnt_1h is not None:
            velocities["txn_count_1h"] = float(override_cnt_1h)
        if override_cnt_24h is not None:
            velocities["txn_count_24h"] = float(override_cnt_24h)

        # 4. Behavioral Deviations & Z-Scores
        baseline = self.store.get_customer_baseline(customer_id)
        cust_mean = float(override_avg) if override_avg is not None else baseline["mean"]
        cust_std = max(10.0, baseline.get("std", cust_mean * 0.35))

        amount_to_avg = round(t_amount / max(1.0, cust_mean), 2)
        amount_deviation = round(t_amount - cust_mean, 2)
        zscore = (t_amount - cust_mean) / cust_std
        zscore_clipped = max(-4.0, min(15.0, round(zscore, 2)))

        # 5. Entity Linkages
        linkages = self.store.get_entity_linkages(device_id, ip_address, customer_id)
        if linkages["is_known_device_for_customer"] == 0 and device_id:
            is_new_dev = True

        # 6. Location & Travel
        loc_delta = self.store.get_location_delta(customer_id, lat, lon, t_time)

        # 7. Failed Attempts
        failed_count = override_failed if override_failed is not None else self.store.get_failed_attempts_count(customer_id, t_time)

        # 8. Beneficiary
        if not is_new_ben and beneficiary_id:
            is_new_ben = not self.store.is_known_beneficiary(customer_id, beneficiary_id)

        features: Dict[str, float] = {
            "amount": round(t_amount, 2),
            "log_amount": round(log_amount, 4),
            "distance_from_home": round(t_dist, 2),
            "hour_of_day": hour,
            "hour_sin": round(hour_sin, 4),
            "hour_cos": round(hour_cos, 4),
            "day_of_week": dow,
            "is_weekend": is_weekend,
            "is_nighttime": is_nighttime,
            "txn_count_1m": velocities["txn_count_1m"],
            "txn_count_5m": velocities["txn_count_5m"],
            "txn_count_1h": velocities["txn_count_1h"],
            "txn_count_24h": velocities["txn_count_24h"],
            "txn_amount_sum_1h": round(velocities["txn_amount_sum_1h"], 2),
            "txn_amount_sum_24h": round(velocities["txn_amount_sum_24h"], 2),
            "amount_to_avg_ratio": amount_to_avg,
            "amount_zscore": zscore_clipped,
            "amount_deviation": amount_deviation,
            "is_new_device": 1.0 if is_new_dev else 0.0,
            "is_vpn_proxy": 1.0 if is_vpn else 0.0,
            "device_associated_accounts": float(linkages["device_associated_accounts"]),
            "ip_associated_accounts": float(linkages["ip_associated_accounts"]),
            "distance_from_prev_km": loc_delta["distance_from_prev_km"],
            "travel_speed_kmh": loc_delta["travel_speed_kmh"],
            "is_impossible_travel": loc_delta["is_impossible_travel"],
            "failed_attempts_last_24h": float(failed_count),
            "is_new_beneficiary": 1.0 if is_new_ben else 0.0,
            "is_type_transfer": 1.0 if "TRANSFER" in txn_type else 0.0,
            "is_type_cash_out": 1.0 if "CASH_OUT" in txn_type else 0.0,
            "is_type_purchase": 1.0 if "PURCHASE" in txn_type else 0.0,
            "is_method_upi": 1.0 if "UPI" in pay_method else 0.0,
            "is_method_credit": 1.0 if "CREDIT" in pay_method else 0.0,
            "is_method_net_banking": 1.0 if "NET_BANKING" in pay_method else 0.0,
            "is_cat_crypto": 1.0 if "CRYPTO" in merch_cat else 0.0,
            "is_cat_gambling": 1.0 if "GAMING" in merch_cat or "GAMBLING" in merch_cat else 0.0,
            "is_cat_luxury": 1.0 if "LUXURY" in merch_cat else 0.0,
        }

        if update_store_after:
            self.store.update_with_transaction(
                customer_id=customer_id,
                account_id=account_id,
                amount=t_amount,
                timestamp=t_time,
                device_id=device_id,
                ip_address=ip_address,
                beneficiary_id=beneficiary_id,
                merchant_id=merchant_id,
                latitude=lat,
                longitude=lon,
            )

        return features

    def extract_feature_vector(
        self,
        txn: Union[Transaction, TransactionEvaluationRequest, Dict[str, Any]],
        update_store_after: bool = False,
    ) -> np.ndarray:
        """Return a strictly ordered 1D numpy array corresponding to FEATURE_NAMES."""
        feat_dict = self.extract_features(txn, update_store_after=update_store_after)
        return np.array([feat_dict[k] for k in FEATURE_NAMES], dtype=np.float32)

    def extract_batch_vectors(
        self, txns: List[Union[Transaction, Dict[str, Any]]]
    ) -> Tuple[np.ndarray, List[str]]:
        """Extract a 2D numpy array for a batch of transactions and return feature names."""
        matrix = []
        for t in txns:
            # We do not automatically update store in batch mode unless sequential
            vec = self.extract_feature_vector(t, update_store_after=False)
            matrix.append(vec)
        return np.array(matrix, dtype=np.float32), FEATURE_NAMES
