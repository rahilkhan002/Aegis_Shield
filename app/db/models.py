"""SQLAlchemy ORM models for Transaction Auditing, Fraud Alerts, and Analyst Feedback."""
from __future__ import annotations
from datetime import datetime
import json
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TransactionRecord(Base):
    """Auditable log of all scored transactions and model outputs."""
    __tablename__ = "transactions"

    transaction_id = Column(String(64), primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    customer_id = Column(String(64), index=True)
    account_id = Column(String(64))
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    transaction_type = Column(String(32), default="PURCHASE")
    payment_method = Column(String(32), default="UPI")
    merchant_category = Column(String(64), default="ONLINE_RETAIL")

    # Evaluation outputs
    risk_score = Column(Float, nullable=False, index=True)
    risk_level = Column(String(16), nullable=False)
    decision = Column(String(32), nullable=False)
    is_suspicious = Column(Boolean, default=False)
    fraud_probability = Column(Float, default=0.0)
    anomaly_score = Column(Float, default=0.0)
    model_version = Column(String(32), default="2.0.0")
    processing_time_ms = Column(Float, default=0.0)

    # Serialized factors
    reasons_json = Column(Text, default="[]")
    rules_triggered_json = Column(Text, default="[]")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "customer_id": self.customer_id,
            "account_id": self.account_id,
            "amount": self.amount,
            "currency": self.currency,
            "transaction_type": self.transaction_type,
            "payment_method": self.payment_method,
            "merchant_category": self.merchant_category,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "decision": self.decision,
            "is_suspicious": self.is_suspicious,
            "fraud_probability": self.fraud_probability,
            "anomaly_score": self.anomaly_score,
            "model_version": self.model_version,
            "processing_time_ms": self.processing_time_ms,
            "reasons": json.loads(self.reasons_json) if self.reasons_json else [],
            "triggered_rules": json.loads(self.rules_triggered_json) if self.rules_triggered_json else [],
        }


class FraudAlert(Base):
    """High-priority alerts for CRITICAL / HIGH risk transactions requiring review."""
    __tablename__ = "fraud_alerts"

    alert_id = Column(String(64), primary_key=True, index=True)
    transaction_id = Column(String(64), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    risk_score = Column(Float, nullable=False)
    risk_level = Column(String(16), nullable=False)
    status = Column(String(32), default="OPEN")  # OPEN, UNDER_REVIEW, RESOLVED
    notes = Column(Text, nullable=True)
    reasons_json = Column(Text, default="[]")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "transaction_id": self.transaction_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "status": self.status,
            "notes": self.notes,
            "reasons": json.loads(self.reasons_json) if self.reasons_json else [],
        }


class AnalystFeedback(Base):
    """Human-in-the-loop ground truth verdicts for model evaluation and retraining."""
    __tablename__ = "analyst_feedback"

    feedback_id = Column(String(64), primary_key=True, index=True)
    transaction_id = Column(String(64), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    verdict = Column(String(32), nullable=False)  # CONFIRMED_FRAUD, FALSE_POSITIVE, LEGITIMATE
    notes = Column(Text, nullable=True)
    analyst_id = Column(String(64), default="SYSTEM")


class ModelRegistryRecord(Base):
    """Versioned model metadata and benchmark metrics."""
    __tablename__ = "model_registry"

    version = Column(String(32), primary_key=True)
    model_type = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    artifact_path = Column(String(255))
    metrics_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)
