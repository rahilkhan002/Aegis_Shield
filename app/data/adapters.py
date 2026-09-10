"""Dataset adapters for standardizing heterogeneous public and internal fraud datasets.

Supports:
- IEEE-CIS Fraud Detection Dataset
- ULB Machine Learning Group Credit Card Dataset (Kaggle)
- PaySim Mobile Money Fraud Simulation Dataset
- Generic CSV / Dict streams
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid

from app.data.schema import (
    Transaction,
    TransactionType,
    PaymentMethod,
    MerchantCategory,
)


class BaseDatasetAdapter(ABC):
    """Abstract base adapter for normalizing external fraud datasets."""

    @abstractmethod
    def adapt(self, record: Dict[str, Any]) -> Transaction:
        """Transform a single record dictionary into the unified Transaction model."""
        pass

    def adapt_batch(self, records: List[Dict[str, Any]]) -> List[Transaction]:
        """Transform a batch of records."""
        return [self.adapt(rec) for rec in records]


class IEEEFraudAdapter(BaseDatasetAdapter):
    """Adapter for IEEE-CIS Fraud Detection dataset.
    
    Expected raw columns include: TransactionID, TransactionDT, TransactionAmt,
    ProductCD, card1-card6, addr1, dist1, isFraud.
    """
    def __init__(self, base_timestamp: Optional[datetime] = None):
        self.base_timestamp = base_timestamp or datetime(2024, 1, 1, 0, 0, 0)

    def adapt(self, record: Dict[str, Any]) -> Transaction:
        txn_id = str(record.get("TransactionID") or uuid.uuid4().hex[:10])
        dt_offset = float(record.get("TransactionDT", 0))
        txn_time = self.base_timestamp + timedelta(seconds=dt_offset)
        amount = float(record.get("TransactionAmt", 50.0))

        # Map ProductCD to Merchant Category
        prod_map = {
            "W": MerchantCategory.ONLINE_RETAIL,
            "C": MerchantCategory.FINANCIAL_SERVICES,
            "R": MerchantCategory.FOOD_DINING,
            "H": MerchantCategory.ENTERTAINMENT,
            "S": MerchantCategory.OTHER,
        }
        product_cd = str(record.get("ProductCD", "W")).upper()
        merchant_cat = prod_map.get(product_cd, MerchantCategory.ONLINE_RETAIL)

        # Card type to Payment Method
        card_type = str(record.get("card6", "credit")).lower()
        pay_method = PaymentMethod.CREDIT_CARD if "credit" in card_type else PaymentMethod.DEBIT_CARD

        dist = float(record.get("dist1") or record.get("dist2") or 0.0)
        card1 = str(record.get("card1", "CUS_UNKNOWN"))
        is_fraud = int(record.get("isFraud", 0)) if "isFraud" in record else None

        return Transaction(
            transaction_id=f"IEEE_{txn_id}",
            timestamp=txn_time,
            customer_id=f"IEEE_CUS_{card1}",
            account_id=f"IEEE_ACC_{card1}",
            amount=amount,
            currency="USD",
            transaction_type=TransactionType.PURCHASE,
            payment_method=pay_method,
            merchant_category=merchant_cat,
            merchant_id=f"MER_{product_cd}",
            distance_from_home=max(0.0, dist),
            is_fraud=is_fraud,
        )


class ULBCreditCardAdapter(BaseDatasetAdapter):
    """Adapter for European Credit Card Fraud Dataset (ULB / Kaggle).
    
    Columns: Time (seconds elapsed from first transaction), V1-V28 (PCA features),
    Amount, Class (1=fraud, 0=legitimate).
    """
    def __init__(self, base_timestamp: Optional[datetime] = None):
        self.base_timestamp = base_timestamp or datetime(2024, 1, 1, 0, 0, 0)

    def adapt(self, record: Dict[str, Any]) -> Transaction:
        time_sec = float(record.get("Time", 0.0))
        txn_time = self.base_timestamp + timedelta(seconds=time_sec)
        amount = max(0.01, float(record.get("Amount", 1.0)))
        is_fraud = int(record.get("Class", 0)) if "Class" in record else None

        txn_id = f"ULB_{int(time_sec)}_{uuid.uuid4().hex[:6]}"

        return Transaction(
            transaction_id=txn_id,
            timestamp=txn_time,
            customer_id=f"ULB_CUS_{int(time_sec) % 1000:04d}",
            account_id=f"ULB_ACC_{int(time_sec) % 1000:04d}",
            amount=amount,
            currency="EUR",
            transaction_type=TransactionType.PURCHASE,
            payment_method=PaymentMethod.CREDIT_CARD,
            merchant_category=MerchantCategory.ONLINE_RETAIL,
            is_fraud=is_fraud,
        )


class PaySimAdapter(BaseDatasetAdapter):
    """Adapter for PaySim Synthetic Financial Datasets for Fraud Detection.
    
    Columns: step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig,
    nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud.
    """
    def __init__(self, base_timestamp: Optional[datetime] = None):
        self.base_timestamp = base_timestamp or datetime(2024, 1, 1, 0, 0, 0)

    def adapt(self, record: Dict[str, Any]) -> Transaction:
        step = int(record.get("step", 1))
        # 1 step = 1 hour
        txn_time = self.base_timestamp + timedelta(hours=step)
        raw_type = str(record.get("type", "PAYMENT")).upper()

        type_map = {
            "PAYMENT": TransactionType.PAYMENT,
            "TRANSFER": TransactionType.TRANSFER,
            "CASH_OUT": TransactionType.CASH_OUT,
            "DEBIT": TransactionType.WITHDRAWAL,
            "CASH_IN": TransactionType.REFUND,
        }
        txn_type = type_map.get(raw_type, TransactionType.PURCHASE)

        amount = float(record.get("amount", 100.0))
        customer = str(record.get("nameOrig", "CUS_PAYSIM"))
        beneficiary = str(record.get("nameDest", "BEN_PAYSIM"))
        is_fraud = int(record.get("isFraud", 0)) if "isFraud" in record else None

        return Transaction(
            transaction_id=f"PAYSIM_{step}_{uuid.uuid4().hex[:6]}",
            timestamp=txn_time,
            customer_id=customer,
            account_id=f"ACC_{customer}",
            beneficiary_id=beneficiary,
            amount=amount,
            currency="USD",
            transaction_type=txn_type,
            payment_method=PaymentMethod.NET_BANKING if txn_type == TransactionType.TRANSFER else PaymentMethod.DEBIT_CARD,
            merchant_category=MerchantCategory.FINANCIAL_SERVICES,
            is_fraud=is_fraud,
        )
