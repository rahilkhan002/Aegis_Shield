"""Realistic Synthetic Financial Transaction & Fraud Scenario Generator.

Generates reproducible normal transactions alongside 18+ distinct fraud patterns:
- High Value Anomalies
- Rapid Velocity Bursts (Card testing / brute force)
- New Device + Large Amount
- New Beneficiary + Large Transfer
- Impossible Travel (Speed-of-flight violation)
- Unusual Geographic Distance
- Account Takeover (ATO) with Immediate Cash-out
- Repeated Failed Attempts followed by Success
- Sudden Spending Behavior / Z-score Spike
- Suspicious Device Reuse across multiple accounts
- Suspicious IP Reuse / VPN Proxy cluster
- Mule Account Immediate Disbursement
- Transaction Splitting / Smurfing
- Unusual Nighttime Activity (01:00 - 04:00 AM)
- High-Risk Merchant Category Outlier
"""
from __future__ import annotations
import argparse
from datetime import datetime, timedelta
import math
import os
import random
from typing import Any, Dict, List, Optional, Tuple
import uuid

import numpy as np

from app.data.schema import (
    Transaction,
    CustomerProfile,
    DeviceProfile,
    MerchantProfile,
    BeneficiaryProfile,
    TransactionType,
    PaymentMethod,
    MerchantCategory,
)


class SyntheticTransactionGenerator:
    """Generates realistic entity profiles and synthetic transaction histories."""

    def __init__(
        self,
        num_customers: int = 500,
        num_merchants: int = 100,
        num_devices: int = 800,
        fraud_rate: float = 0.03,
        seed: int = 42,
    ):
        self.num_customers = num_customers
        self.num_merchants = num_merchants
        self.num_devices = num_devices
        self.fraud_rate = fraud_rate
        self.seed = seed
        self.rng = random.Random(seed)  # nosec B311
        self.np_rng = np.random.default_rng(seed)

        self._init_entities()

    def _init_entities(self):
        """Pre-populate realistic customers, merchants, devices, and baseline locations."""
        # Cities in India (lat, lon)
        cities = [
            ("Delhi", 28.6139, 77.2090),
            ("Mumbai", 19.0760, 72.8777),
            ("Bengaluru", 12.9716, 77.5946),
            ("Hyderabad", 17.3850, 78.4867),
            ("Chennai", 13.0827, 80.2707),
            ("Kolkata", 22.5726, 88.3639),
            ("Pune", 18.5204, 73.8567),
            ("Ahmedabad", 23.0225, 72.5714),
        ]

        # Generate Customers
        self.customers: List[CustomerProfile] = []
        for i in range(self.num_customers):
            city_name, lat, lon = self.rng.choice(cities)
            # Add slight jitter for customer home (within 5 km)
            lat_jitter = lat + self.rng.gauss(0, 0.02)
            lon_jitter = lon + self.rng.gauss(0, 0.02)
            normal_amt = float(np.exp(self.rng.gauss(5.5, 0.7)))  # median ~$250
            normal_amt = max(10.0, round(normal_amt, 2))

            cust = CustomerProfile(
                customer_id=f"CUS_{i+1000:05d}",
                account_id=f"ACC_{i+1000:05d}",
                account_age_days=self.rng.randint(30, 2500),
                normal_transaction_amount=normal_amt,
                customer_risk_score=round(self.rng.uniform(2.0, 18.0), 1),
                historical_transaction_count=self.rng.randint(20, 800),
                failed_transaction_count=self.rng.randint(0, 3),
                previous_fraud_count=1 if self.rng.random() < 0.02 else 0,
                home_latitude=lat_jitter,
                home_longitude=lon_jitter,
            )
            self.customers.append(cust)

        # Generate Merchants
        merchant_cats = list(MerchantCategory)
        self.merchants: List[MerchantProfile] = []
        for j in range(self.num_merchants):
            cat = self.rng.choice(merchant_cats)
            is_high_risk = cat in [
                MerchantCategory.CRYPTO_EXCHANGE,
                MerchantCategory.GAMING_GAMBLING,
                MerchantCategory.LUXURY_JEWELRY,
            ]
            fraud_rate = self.rng.uniform(0.04, 0.12) if is_high_risk else self.rng.uniform(0.001, 0.02)
            merch = MerchantProfile(
                merchant_id=f"MER_{j+100:04d}",
                merchant_category=cat,
                merchant_risk_score=round(fraud_rate * 500, 1),
                historical_fraud_rate=round(fraud_rate, 4),
                total_transactions=self.rng.randint(50, 50000),
            )
            self.merchants.append(merch)

        # Generate Devices
        device_types = ["MOBILE", "DESKTOP", "TABLET"]
        os_list = ["Android", "iOS", "Windows", "macOS", "Linux"]
        browsers = ["Chrome", "Safari", "Firefox", "Edge", "Mobile App"]
        self.devices: List[DeviceProfile] = []
        for k in range(self.num_devices):
            dev = DeviceProfile(
                device_id=f"DEV_{k+10000:06d}",
                device_type=self.rng.choice(device_types),
                operating_system=self.rng.choice(os_list),
                browser=self.rng.choice(browsers),
                is_new_device=False,
                device_age_days=self.rng.randint(10, 1200),
                associated_accounts_count=1,
            )
            self.devices.append(dev)

        # Customer preferred devices & beneficiaries
        self.customer_devices: Dict[str, List[DeviceProfile]] = {}
        self.customer_beneficiaries: Dict[str, List[str]] = {}
        for cust in self.customers:
            # 1 to 3 devices per customer
            dev_sample = self.rng.sample(self.devices, k=min(len(self.devices), self.rng.randint(1, 3)))
            self.customer_devices[cust.customer_id] = dev_sample
            # Known beneficiaries
            self.customer_beneficiaries[cust.customer_id] = [
                f"BEN_{self.rng.randint(1, 300):04d}" for _ in range(self.rng.randint(1, 5))
            ]

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Great circle distance between two points on Earth in km."""
        r = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(r * c, 2)

    def generate_single_normal_transaction(
        self,
        customer: CustomerProfile,
        timestamp: datetime,
        previous_txn: Optional[Transaction] = None,
    ) -> Transaction:
        """Generates a realistic legitimate transaction aligned with the customer's profile."""
        merchant = self.rng.choice(self.merchants)
        devices = self.customer_devices.get(customer.customer_id, self.devices)
        device = self.rng.choice(devices)

        # Normal log-normal amount around customer's normal amount
        mean_log = math.log(customer.normal_transaction_amount)
        amount = float(np.exp(self.rng.gauss(mean_log, 0.45)))
        amount = max(5.0, min(50000.0, round(amount, 2)))

        # Distance near customer's home
        dist = abs(self.rng.gauss(3.5, 4.0))

        # Lat/Lon near home
        lat = customer.home_latitude + self.rng.gauss(0, 0.03)
        lon = customer.home_longitude + self.rng.gauss(0, 0.03)

        payment_methods = [
            PaymentMethod.UPI,
            PaymentMethod.DEBIT_CARD,
            PaymentMethod.CREDIT_CARD,
            PaymentMethod.NET_BANKING,
        ]
        pm = self.rng.choice(payment_methods)

        txn_types = [TransactionType.PURCHASE, TransactionType.PAYMENT, TransactionType.TRANSFER]
        tt = self.rng.choices(txn_types, weights=[0.7, 0.2, 0.1])[0]

        beneficiary = None
        if tt == TransactionType.TRANSFER:
            beneficiaries = self.customer_beneficiaries.get(customer.customer_id, ["BEN_0001"])
            beneficiary = self.rng.choice(beneficiaries)

        txn_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"

        return Transaction(
            transaction_id=txn_id,
            timestamp=timestamp,
            customer_id=customer.customer_id,
            account_id=customer.account_id,
            amount=amount,
            currency="INR",
            transaction_type=tt,
            payment_method=pm,
            merchant_category=merchant.merchant_category,
            merchant_id=merchant.merchant_id,
            beneficiary_id=beneficiary,
            device_id=device.device_id,
            device_type=device.device_type,
            is_new_device=False,
            ip_address=f"103.{self.rng.randint(10,250)}.{self.rng.randint(1,250)}.{self.rng.randint(1,250)}",
            is_vpn_proxy=False,
            latitude=lat,
            longitude=lon,
            distance_from_home=round(dist, 2),
            customer_avg_amount_30d=customer.normal_transaction_amount,
            customer_txn_count_last_1h=1,
            customer_txn_count_last_24h=self.rng.randint(1, 4),
            failed_attempts_last_24h=0,
            is_new_beneficiary=False,
            is_fraud=0,
            fraud_scenario="NORMAL",
        )

    def generate_fraud_scenario(
        self,
        customer: CustomerProfile,
        timestamp: datetime,
        scenario_idx: Optional[int] = None,
    ) -> List[Transaction]:
        """Generates one of 18 specific, realistic fraud scenarios."""
        scenarios = [
            "UNUSUAL_HIGH_VALUE",
            "RAPID_VELOCITY_SPIKE",
            "NEW_DEVICE_LARGE_AMOUNT",
            "NEW_BENEFICIARY_TRANSFER",
            "IMPOSSIBLE_TRAVEL",
            "UNUSUAL_LOCATION_FOREIGN",
            "ACCOUNT_TAKEOVER_CASHOUT",
            "REPEATED_FAILED_THEN_SUCCESS",
            "SUDDEN_ZSCORE_SPIKE",
            "SUSPICIOUS_DEVICE_REUSE",
            "SUSPICIOUS_IP_VPN_CLUSTER",
            "MULE_ACCOUNT_DISBURSEMENT",
            "TRANSACTION_SPLITTING_SMURFING",
            "UNUSUAL_NIGHTTIME_BURST",
            "HIGH_RISK_CRYPTO_OUTLIER",
            "COORDINATED_RING_COLLUSION",
            "CARD_TESTING_MICRO_BURST",
            "VELOCITY_ACCELERATION_ATTACK",
        ]

        scenario = scenarios[scenario_idx] if scenario_idx is not None else self.rng.choice(scenarios)
        txns: List[Transaction] = []

        if scenario == "UNUSUAL_HIGH_VALUE":
            # Amount is 8x to 25x normal
            amount = round(customer.normal_transaction_amount * self.rng.uniform(8.0, 25.0), 2)
            amount = max(amount, 85000.0)
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.amount = amount
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "RAPID_VELOCITY_SPIKE":
            # 6 to 10 rapid transactions within 3-8 minutes
            base_amt = round(self.rng.uniform(3000.0, 9500.0), 2)
            for step in range(self.rng.randint(6, 10)):
                step_time = timestamp + timedelta(seconds=step * self.rng.randint(20, 60))
                t = self.generate_single_normal_transaction(customer, step_time)
                t.amount = base_amt + self.rng.uniform(-50, 50)
                t.customer_txn_count_last_1h = step + 4
                t.is_fraud = 1
                t.fraud_scenario = scenario
                txns.append(t)

        elif scenario == "NEW_DEVICE_LARGE_AMOUNT":
            # Brand new device identifier + transaction amount 5x customer average
            new_dev_id = f"DEV_NEW_{uuid.uuid4().hex[:8].upper()}"
            amount = round(customer.normal_transaction_amount * self.rng.uniform(5.5, 12.0), 2)
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.device_id = new_dev_id
            t.is_new_device = True
            t.amount = amount
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "NEW_BENEFICIARY_TRANSFER":
            # Large transfer to unverified new beneficiary
            new_ben = f"BEN_NEW_{uuid.uuid4().hex[:8].upper()}"
            amount = round(customer.normal_transaction_amount * self.rng.uniform(6.0, 15.0), 2)
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.transaction_type = TransactionType.TRANSFER
            t.payment_method = PaymentMethod.UPI
            t.beneficiary_id = new_ben
            t.is_new_beneficiary = True
            t.amount = amount
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "IMPOSSIBLE_TRAVEL":
            # Transaction 1,800 km away only 15 minutes after home activity (velocity > 7000 km/h)
            t = self.generate_single_normal_transaction(customer, timestamp)
            # Switch to Dubai or London coordinates
            t.latitude = 25.2048
            t.longitude = 55.2708
            t.distance_from_home = 2150.0  # 2150 km from Delhi
            t.amount = round(customer.normal_transaction_amount * 3.5, 2)
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "UNUSUAL_LOCATION_FOREIGN":
            # High risk foreign location with VPN
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.distance_from_home = 4500.0
            t.is_vpn_proxy = True
            t.ip_address = f"185.{self.rng.randint(10,250)}.{self.rng.randint(1,250)}.{self.rng.randint(1,250)}"
            t.amount = round(customer.normal_transaction_amount * 4.0, 2)
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "ACCOUNT_TAKEOVER_CASHOUT":
            # Password / device change followed immediately by full balance cash-out
            new_dev = f"DEV_ATO_{uuid.uuid4().hex[:6]}"
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.device_id = new_dev
            t.is_new_device = True
            t.transaction_type = TransactionType.CASH_OUT
            t.payment_method = PaymentMethod.NET_BANKING
            t.amount = round(customer.normal_transaction_amount * 15.0, 2)
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "REPEATED_FAILED_THEN_SUCCESS":
            # 4-6 failed attempts (wrong OTP / CVV) within 30 minutes, then large successful transaction
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.failed_attempts_last_24h = self.rng.randint(4, 7)
            t.amount = round(customer.normal_transaction_amount * 4.5, 2)
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "SUDDEN_ZSCORE_SPIKE":
            # Massive sudden jump in standard deviations (> 6 sigma)
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.amount = round(customer.normal_transaction_amount * 18.0, 2)
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "SUSPICIOUS_DEVICE_REUSE":
            # Same device ID used across 5 distinct customer accounts in 1 hour
            shared_device_id = "DEV_FRAUD_SHARED_9999"
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.device_id = shared_device_id
            t.amount = round(customer.normal_transaction_amount * 3.0, 2)
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "SUSPICIOUS_IP_VPN_CLUSTER":
            # Multiple accounts routing through known hosting/VPN proxy subnet
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.ip_address = "45.142.122.45"
            t.is_vpn_proxy = True
            t.amount = round(customer.normal_transaction_amount * 2.8, 2)
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "MULE_ACCOUNT_DISBURSEMENT":
            # Rapid incoming transfer immediately cleared out to cryptocurrency exchange or overseas
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.transaction_type = TransactionType.TRANSFER
            t.merchant_category = MerchantCategory.CRYPTO_EXCHANGE
            t.amount = 75000.0
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "TRANSACTION_SPLITTING_SMURFING":
            # Splitting a large sum (e.g. 150,000) into 4 transactions of 37,500 within 2 hours
            split_amount = 38500.00
            for s in range(3):
                s_time = timestamp + timedelta(minutes=s * 25)
                t = self.generate_single_normal_transaction(customer, s_time)
                t.amount = split_amount
                t.customer_txn_count_last_1h = s + 2
                t.is_fraud = 1
                t.fraud_scenario = scenario
                txns.append(t)

        elif scenario == "UNUSUAL_NIGHTTIME_BURST":
            # 02:45 AM high-value transfer with a new device
            night_time = timestamp.replace(hour=2, minute=self.rng.randint(15, 55))
            t = self.generate_single_normal_transaction(customer, night_time)
            t.amount = round(customer.normal_transaction_amount * 5.0, 2)
            t.is_new_device = True
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "HIGH_RISK_CRYPTO_OUTLIER":
            # Unprecedented purchase on crypto exchange or offshore casino
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.merchant_category = MerchantCategory.CRYPTO_EXCHANGE
            t.amount = round(customer.normal_transaction_amount * 7.0, 2)
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        elif scenario == "CARD_TESTING_MICRO_BURST":
            # Series of small $1-$5 charges followed by large hit
            for m in range(4):
                m_time = timestamp + timedelta(seconds=m * 15)
                t = self.generate_single_normal_transaction(customer, m_time)
                t.amount = float(m + 2.0)
                t.customer_txn_count_last_1h = m + 1
                t.is_fraud = 1
                t.fraud_scenario = scenario
                txns.append(t)
            # Big drain
            big_time = timestamp + timedelta(minutes=2)
            t_big = self.generate_single_normal_transaction(customer, big_time)
            t_big.amount = 49000.0
            t_big.is_fraud = 1
            t_big.fraud_scenario = scenario
            txns.append(t_big)

        else:
            # Default fraud scenario fallback
            t = self.generate_single_normal_transaction(customer, timestamp)
            t.amount = round(customer.normal_transaction_amount * 6.0, 2)
            t.is_fraud = 1
            t.fraud_scenario = scenario
            txns.append(t)

        return txns

    def generate_dataset(
        self,
        total_transactions: int = 10000,
        start_date: Optional[datetime] = None,
        days_span: int = 30,
    ) -> List[Transaction]:
        """Generates a complete chronologically ordered synthetic dataset with configured fraud rate."""
        start_date = start_date or (datetime.utcnow() - timedelta(days=days_span))
        transactions: List[Transaction] = []

        total_fraud_target = int(total_transactions * self.fraud_rate)
        generated_fraud = 0

        # Spread timestamps over days_span
        current_time = start_date
        sec_interval = int((days_span * 86400) / total_transactions)

        while len(transactions) < total_transactions:
            cust = self.rng.choice(self.customers)
            # Add some jitter to time
            jitter_sec = self.rng.randint(0, max(1, sec_interval * 2))
            current_time += timedelta(seconds=jitter_sec)

            # Decide whether to trigger a fraud scenario
            remaining_slots = total_transactions - len(transactions)
            fraud_needed = total_fraud_target - generated_fraud

            should_fraud = False
            if fraud_needed > 0:
                prob = fraud_needed / max(1, remaining_slots)
                should_fraud = (self.rng.random() < prob)

            if should_fraud:
                fraud_batch = self.generate_fraud_scenario(cust, current_time)
                for f_txn in fraud_batch:
                    if len(transactions) < total_transactions:
                        transactions.append(f_txn)
                        generated_fraud += 1
            else:
                normal_txn = self.generate_single_normal_transaction(cust, current_time)
                transactions.append(normal_txn)

        # Sort strictly by timestamp to maintain realistic chronological sequence
        transactions.sort(key=lambda t: t.timestamp)
        return transactions


def generate_synthetic_dataset(
    num_transactions: int = 10000,
    num_customers: int = 500,
    num_merchants: int = 100,
    num_devices: int = 800,
    fraud_rate: float = 0.03,
    seed: int = 42,
    output_path: Optional[str] = None,
) -> Any:
    """Helper function to generate and optionally persist a synthetic dataset."""
    import pandas as pd

    gen = SyntheticTransactionGenerator(
        num_customers=num_customers,
        num_merchants=num_merchants,
        num_devices=num_devices,
        fraud_rate=fraud_rate,
        seed=seed,
    )
    txns = gen.generate_dataset(total_transactions=num_transactions)

    # Convert to pandas DataFrame
    records = []
    for t in txns:
        rec = t.model_dump()
        # Flatten enums to strings
        rec["transaction_type"] = rec["transaction_type"]
        rec["payment_method"] = rec["payment_method"]
        rec["merchant_category"] = rec["merchant_category"]
        records.append(rec)

    df = pd.DataFrame(records)

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        if output_path.endswith(".parquet"):
            df.to_parquet(output_path, index=False)
        else:
            df.to_csv(output_path, index=False)

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic Financial Fraud Transaction Generator")
    parser.add_argument("--customers", type=int, default=500, help="Number of customer entities")
    parser.add_argument("--merchants", type=int, default=100, help="Number of merchant entities")
    parser.add_argument("--devices", type=int, default=800, help="Number of device entities")
    parser.add_argument("--transactions", type=int, default=10000, help="Total transactions to simulate")
    parser.add_argument("--fraud-rate", type=float, default=0.03, help="Proportion of fraudulent transactions")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="data/synthetic_transactions.csv", help="Output file path")

    args = parser.parse_args()
    print(f"Generating {args.transactions} synthetic transactions (fraud_rate={args.fraud_rate}, seed={args.seed})...")
    df = generate_synthetic_dataset(
        num_transactions=args.transactions,
        num_customers=args.customers,
        num_merchants=args.merchants,
        num_devices=args.devices,
        fraud_rate=args.fraud_rate,
        seed=args.seed,
        output_path=args.output,
    )
    print(f"Successfully generated {len(df)} transactions -> {args.output}")
    print(f"Fraud distribution:\n{df['is_fraud'].value_counts(normalize=True)}")
