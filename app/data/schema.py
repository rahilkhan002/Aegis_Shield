"""Unified Data Model and API Schemas for Fraud Detection Platform.

Defines standardized Pydantic models for transactions, customer profiles,
devices, networks, merchants, beneficiaries, and prediction requests/responses.
"""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator


class TransactionType(str, Enum):
    PURCHASE = "PURCHASE"
    TRANSFER = "TRANSFER"
    WITHDRAWAL = "WITHDRAWAL"
    PAYMENT = "PAYMENT"
    REFUND = "REFUND"
    CASH_OUT = "CASH_OUT"


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    NET_BANKING = "NET_BANKING"
    WALLET = "WALLET"
    CRYPTO = "CRYPTO"


class MerchantCategory(str, Enum):
    ONLINE_RETAIL = "ONLINE_RETAIL"
    GROCERY = "GROCERY"
    TRAVEL_AIRLINE = "TRAVEL_AIRLINE"
    GAMING_GAMBLING = "GAMING_GAMBLING"
    LUXURY_JEWELRY = "LUXURY_JEWELRY"
    ELECTRONICS = "ELECTRONICS"
    CRYPTO_EXCHANGE = "CRYPTO_EXCHANGE"
    FOOD_DINING = "FOOD_DINING"
    ENTERTAINMENT = "ENTERTAINMENT"
    FINANCIAL_SERVICES = "FINANCIAL_SERVICES"
    OTHER = "OTHER"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DecisionType(str, Enum):
    ALLOW = "ALLOW"
    STEP_UP = "STEP_UP"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    BLOCK = "BLOCK"


# ---------------------------------------------------------------------------
# Entity Profiles
# ---------------------------------------------------------------------------

class CustomerProfile(BaseModel):
    customer_id: str = Field(..., description="Unique customer identifier")
    account_id: str = Field(..., description="Primary account identifier")
    account_age_days: int = Field(default=365, ge=0, description="Age of account in days")
    normal_transaction_amount: float = Field(default=500.0, ge=0.0)
    customer_risk_score: float = Field(default=10.0, ge=0.0, le=100.0)
    historical_transaction_count: int = Field(default=50, ge=0)
    failed_transaction_count: int = Field(default=0, ge=0)
    previous_fraud_count: int = Field(default=0, ge=0)
    home_latitude: float = Field(default=28.6139)
    home_longitude: float = Field(default=77.2090)


class DeviceProfile(BaseModel):
    device_id: str = Field(..., description="Unique hardware or browser fingerprint")
    device_type: str = Field(default="MOBILE", description="MOBILE, DESKTOP, TABLET, BOT")
    operating_system: str = Field(default="Android")
    browser: str = Field(default="Chrome")
    is_new_device: bool = Field(default=False)
    device_age_days: int = Field(default=180, ge=0)
    associated_accounts_count: int = Field(default=1, ge=1)


class NetworkProfile(BaseModel):
    ip_address: str = Field(default="127.0.0.1")
    country: str = Field(default="IN")
    region: Optional[str] = Field(default="Delhi")
    city: Optional[str] = Field(default="New Delhi")
    latitude: float = Field(default=28.6139)
    longitude: float = Field(default=77.2090)
    is_vpn_or_proxy: bool = Field(default=False)
    ip_associated_accounts_count: int = Field(default=1, ge=1)


class MerchantProfile(BaseModel):
    merchant_id: str = Field(..., description="Merchant identifier")
    merchant_category: MerchantCategory = Field(default=MerchantCategory.ONLINE_RETAIL)
    merchant_risk_score: float = Field(default=15.0, ge=0.0, le=100.0)
    historical_fraud_rate: float = Field(default=0.01, ge=0.0, le=1.0)
    total_transactions: int = Field(default=1000, ge=0)


class BeneficiaryProfile(BaseModel):
    beneficiary_id: str = Field(..., description="Destination beneficiary account")
    beneficiary_risk_score: float = Field(default=10.0, ge=0.0, le=100.0)
    is_new_beneficiary: bool = Field(default=False)
    historical_received_count: int = Field(default=5, ge=0)


# ---------------------------------------------------------------------------
# Unified Core Transaction Model
# ---------------------------------------------------------------------------

class Transaction(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    customer_id: str = Field(..., description="Customer identifier")
    account_id: str = Field(..., description="Account identifier")
    amount: float = Field(..., gt=0.0, description="Monetary transaction amount")
    currency: str = Field(default="INR", description="ISO currency code")
    transaction_type: TransactionType = Field(default=TransactionType.PURCHASE)
    payment_method: PaymentMethod = Field(default=PaymentMethod.UPI)
    merchant_category: MerchantCategory = Field(default=MerchantCategory.ONLINE_RETAIL)

    # Identifiers
    merchant_id: Optional[str] = Field(default="MERCH_GENERIC")
    beneficiary_id: Optional[str] = Field(default=None)

    # Device & Network context
    device_id: Optional[str] = Field(default="DEV_DEFAULT")
    device_type: Optional[str] = Field(default="MOBILE")
    is_new_device: bool = Field(default=False)

    ip_address: Optional[str] = Field(default="127.0.0.1")
    is_vpn_proxy: bool = Field(default=False)

    # Geo location
    latitude: Optional[float] = Field(default=28.6139)
    longitude: Optional[float] = Field(default=77.2090)
    distance_from_home: Optional[float] = Field(default=0.0, ge=0.0)

    # Contextual behavioral snapshot (if provided directly)
    customer_avg_amount_30d: Optional[float] = Field(default=None, ge=0.0)
    customer_txn_count_last_1h: Optional[int] = Field(default=None, ge=0)
    customer_txn_count_last_24h: Optional[int] = Field(default=None, ge=0)
    failed_attempts_last_24h: Optional[int] = Field(default=0, ge=0)
    is_new_beneficiary: bool = Field(default=False)

    # Ground truth (if historical dataset)
    is_fraud: Optional[int] = Field(default=None, description="0 for legitimate, 1 for fraud")
    fraud_scenario: Optional[str] = Field(default=None)


# ---------------------------------------------------------------------------
# API Request / Response Models
# ---------------------------------------------------------------------------

class LegacyTransactionRequest(BaseModel):
    """Legacy 2-feature schema for strict backward compatibility."""
    amount: float = Field(..., gt=0.0, description="Transaction amount")
    distance_from_home: float = Field(..., ge=0.0, description="Distance in km")


class TransactionEvaluationRequest(BaseModel):
    """Rich enterprise fraud evaluation request."""
    transaction_id: Optional[str] = Field(default=None)
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    customer_id: Optional[str] = Field(default="CUS_DEFAULT")
    account_id: Optional[str] = Field(default="ACC_DEFAULT")
    merchant_id: Optional[str] = Field(default="MER_DEFAULT")
    beneficiary_id: Optional[str] = Field(default=None)
    amount: float = Field(..., gt=0.0, description="Transaction amount in currency units")
    currency: str = Field(default="INR")
    transaction_type: TransactionType = Field(default=TransactionType.PURCHASE)
    payment_method: PaymentMethod = Field(default=PaymentMethod.UPI)
    merchant_category: MerchantCategory = Field(default=MerchantCategory.ONLINE_RETAIL)

    device_id: Optional[str] = Field(default="DEV_DEFAULT")
    device_type: Optional[str] = Field(default="MOBILE")
    is_new_device: bool = Field(default=False)

    ip_address: Optional[str] = Field(default="127.0.0.1")
    is_vpn_proxy: bool = Field(default=False)

    latitude: Optional[float] = Field(default=28.6139)
    longitude: Optional[float] = Field(default=77.2090)
    distance_from_home: Optional[float] = Field(default=5.0, ge=0.0)

    # Contextual behavioral overrides (optional for simulation/testing)
    customer_avg_amount_30d: Optional[float] = Field(default=None)
    customer_txn_count_last_1h: Optional[int] = Field(default=None)
    customer_txn_count_last_24h: Optional[int] = Field(default=None)
    failed_attempts_last_24h: Optional[int] = Field(default=0)
    is_new_beneficiary: bool = Field(default=False)


class TransactionEvaluationResponse(BaseModel):
    """Standardized response from the fraud evaluation platform."""
    model_config = {"protected_namespaces": ()}

    transaction_id: str
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Normalized risk score (0-100)")
    risk_level: RiskLevel
    decision: DecisionType
    is_suspicious: bool
    fraud_probability: float = Field(..., ge=0.0, le=1.0, description="Calibrated ML probability")
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Isolation Forest anomaly score")
    rule_score: float = Field(..., ge=0.0, le=100.0, description="Rule violations score")
    behavior_score: float = Field(..., ge=0.0, le=100.0, description="Behavioral anomaly score")
    network_score: float = Field(..., ge=0.0, le=100.0, description="Network / entity risk score")
    model_version: str
    processing_time_ms: float
    reasons: List[str] = Field(default_factory=list, description="Human-readable risk factors")
    triggered_rules: List[str] = Field(default_factory=list, description="Identifiers of violated rules")
    feature_contributions: Optional[Dict[str, float]] = Field(default=None)

    # Backward-compatible fields for existing clients
    is_anomaly: Optional[bool] = Field(default=None)


class AnalystFeedbackRequest(BaseModel):
    transaction_id: str
    verdict: str = Field(..., description="CONFIRMED_FRAUD, FALSE_POSITIVE, or LEGITIMATE")
    notes: Optional[str] = Field(default=None)
    analyst_id: Optional[str] = Field(default="ANALYST_DEFAULT")
