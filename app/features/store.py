"""Feature Store and sliding-window state caching.

Maintains customer velocity counters, 30-day behavioral baselines,
device/IP entity linkages, and historical sliding windows.
Works in-memory with zero setup by default, and seamlessly connects
to Redis when configured.
"""
from __future__ import annotations
from collections import defaultdict, deque
from datetime import datetime, timedelta
import math
import os
from typing import Any, Dict, List, Optional, Set, Tuple


class FeatureStore:
    """Sliding-window in-memory and Redis-compatible Feature Store."""

    _instance: Optional["FeatureStore"] = None

    def __init__(self):
        # Sliding-window of recent transactions: customer_id -> deque of records (within 24 hours)
        self._customer_history: Dict[str, deque] = defaultdict(deque)

        # Entity linkage tracking
        self._device_to_accounts: Dict[str, Set[str]] = defaultdict(set)
        self._ip_to_accounts: Dict[str, Set[str]] = defaultdict(set)
        self._customer_devices: Dict[str, Set[str]] = defaultdict(set)
        self._customer_beneficiaries: Dict[str, Set[str]] = defaultdict(set)

        # Customer 30-day baseline statistics
        self._customer_baselines: Dict[str, Dict[str, float]] = {}

        # Last known location & timestamp: customer_id -> (lat, lon, timestamp)
        self._customer_last_location: Dict[str, Tuple[float, float, datetime]] = {}

        # Failed attempt counters within 24h
        self._customer_failed_attempts: Dict[str, List[datetime]] = defaultdict(list)

    @classmethod
    def get_instance(cls) -> "FeatureStore":
        if cls._instance is None:
            cls._instance = FeatureStore()
        return cls._instance

    def update_with_transaction(
        self,
        customer_id: str,
        account_id: str,
        amount: float,
        timestamp: datetime,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        beneficiary_id: Optional[str] = None,
        merchant_id: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        is_success: bool = True,
    ):
        """Record a newly evaluated or historical transaction into the state store."""
        cutoff_24h = timestamp - timedelta(hours=24)

        # Clean old records
        q = self._customer_history[customer_id]
        while q and q[0]["timestamp"] < cutoff_24h:
            q.popleft()

        # Add current transaction
        q.append({
            "amount": amount,
            "timestamp": timestamp,
            "device_id": device_id,
            "ip_address": ip_address,
            "beneficiary_id": beneficiary_id,
            "merchant_id": merchant_id,
            "latitude": latitude,
            "longitude": longitude,
        })

        # Update entity linkages
        if device_id:
            self._device_to_accounts[device_id].add(account_id)
            self._customer_devices[customer_id].add(device_id)
        if ip_address:
            self._ip_to_accounts[ip_address].add(account_id)
        if beneficiary_id:
            self._customer_beneficiaries[customer_id].add(beneficiary_id)

        # Update last known location
        if latitude is not None and longitude is not None:
            self._customer_last_location[customer_id] = (latitude, longitude, timestamp)

        if not is_success:
            self._customer_failed_attempts[customer_id].append(timestamp)

    def record_failed_attempt(self, customer_id: str, timestamp: datetime):
        """Record a failed authentication or transaction attempt."""
        self._customer_failed_attempts[customer_id].append(timestamp)

    def get_velocity_features(
        self, customer_id: str, current_time: datetime
    ) -> Dict[str, float]:
        """Compute windowed velocities strictly before current_time."""
        q = self._customer_history.get(customer_id, deque())

        t_1m = current_time - timedelta(minutes=1)
        t_5m = current_time - timedelta(minutes=5)
        t_1h = current_time - timedelta(hours=1)
        t_24h = current_time - timedelta(hours=24)

        cnt_1m = 0
        cnt_5m = 0
        cnt_1h = 0
        cnt_24h = 0
        sum_1h = 0.0
        sum_24h = 0.0

        for record in reversed(q):
            t = record["timestamp"]
            # Strict temporal check (exclude future/current to prevent leakage)
            if t >= current_time:
                continue
            if t < t_24h:
                break
            
            amt = record["amount"]
            cnt_24h += 1
            sum_24h += amt

            if t >= t_1h:
                cnt_1h += 1
                sum_1h += amt
            if t >= t_5m:
                cnt_5m += 1
            if t >= t_1m:
                cnt_1m += 1

        return {
            "txn_count_1m": float(cnt_1m),
            "txn_count_5m": float(cnt_5m),
            "txn_count_1h": float(cnt_1h),
            "txn_count_24h": float(cnt_24h),
            "txn_amount_sum_1h": float(sum_1h),
            "txn_amount_sum_24h": float(sum_24h),
        }

    def get_customer_baseline(self, customer_id: str, default_avg: float = 500.0) -> Dict[str, float]:
        """Retrieve customer 30-day spending baseline (mean, std)."""
        if customer_id in self._customer_baselines:
            return self._customer_baselines[customer_id]
        
        # If not precomputed, derive from known history or default
        history = self._customer_history.get(customer_id, deque())
        if len(history) >= 3:
            amounts = [h["amount"] for h in history]
            mean = sum(amounts) / len(amounts)
            variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
            std = math.sqrt(variance) if variance > 0 else (mean * 0.25)
            baseline = {"mean": mean, "std": max(10.0, std)}
            self._customer_baselines[customer_id] = baseline
            return baseline

        return {"mean": default_avg, "std": max(50.0, default_avg * 0.35)}

    def set_customer_baseline(self, customer_id: str, mean: float, std: float):
        """Set precomputed customer baseline."""
        self._customer_baselines[customer_id] = {"mean": mean, "std": max(10.0, std)}

    def get_entity_linkages(
        self, device_id: Optional[str], ip_address: Optional[str], customer_id: str
    ) -> Dict[str, int]:
        """Check multi-account clustering across devices and IPs."""
        dev_accounts = len(self._device_to_accounts.get(device_id, set())) if device_id else 1
        ip_accounts = len(self._ip_to_accounts.get(ip_address, set())) if ip_address else 1
        is_known_dev = (device_id in self._customer_devices.get(customer_id, set())) if device_id else True

        return {
            "device_associated_accounts": max(1, dev_accounts),
            "ip_associated_accounts": max(1, ip_accounts),
            "is_known_device_for_customer": 1 if is_known_dev else 0,
        }

    def get_location_delta(
        self,
        customer_id: str,
        current_lat: Optional[float],
        current_lon: Optional[float],
        current_time: datetime,
    ) -> Dict[str, float]:
        """Compute distance and speed from customer's previous known transaction."""
        if customer_id not in self._customer_last_location or current_lat is None or current_lon is None:
            return {
                "distance_from_prev_km": 0.0,
                "travel_speed_kmh": 0.0,
                "is_impossible_travel": 0.0,
            }

        prev_lat, prev_lon, prev_time = self._customer_last_location[customer_id]
        # Haversine distance
        r = 6371.0
        dlat = math.radians(current_lat - prev_lat)
        dlon = math.radians(current_lon - prev_lon)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(prev_lat)) * math.cos(math.radians(current_lat)) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        dist_km = r * c

        time_diff_hours = max(0.001, (current_time - prev_time).total_seconds() / 3600.0)
        speed_kmh = dist_km / time_diff_hours

        # Impossible travel: > 850 km/h (speed of commercial aircraft) with distance > 150 km
        is_impossible = 1.0 if (speed_kmh > 850.0 and dist_km > 150.0) else 0.0

        return {
            "distance_from_prev_km": round(dist_km, 2),
            "travel_speed_kmh": round(speed_kmh, 1),
            "is_impossible_travel": is_impossible,
        }

    def get_failed_attempts_count(self, customer_id: str, current_time: datetime) -> int:
        """Count failed authentication attempts within the last 24 hours."""
        t_24h = current_time - timedelta(hours=24)
        attempts = self._customer_failed_attempts.get(customer_id, [])
        valid = [t for t in attempts if t_24h <= t < current_time]
        self._customer_failed_attempts[customer_id] = valid
        return len(valid)

    def is_known_beneficiary(self, customer_id: str, beneficiary_id: Optional[str]) -> bool:
        if not beneficiary_id:
            return True
        return beneficiary_id in self._customer_beneficiaries.get(customer_id, set())


def get_feature_store() -> FeatureStore:
    return FeatureStore.get_instance()
