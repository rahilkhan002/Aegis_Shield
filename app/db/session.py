"""Database engine and session management."""
from __future__ import annotations
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.db.models import Base

if os.getenv("VERCEL"):
    DB_PATH = Path(os.getenv("DB_DIR", "/tmp")) / "fraud_pipeline.db"
else:
    DB_PATH = Path(os.getenv("DB_DIR", Path(__file__).parent.parent.parent)) / "fraud_pipeline.db"
DEFAULT_DB_URL = f"sqlite:///{DB_PATH.as_posix()}"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# SQLite concurrency configuration
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create database tables and seed realistic demo records if empty."""
    Base.metadata.create_all(bind=engine)
    try:
        seed_initial_demo_data()
    except Exception:
        pass


def seed_initial_demo_data():
    """Seed initial realistic alerts and transactions if database is fresh."""
    from datetime import datetime, timedelta
    import json
    from app.db.models import TransactionRecord, FraudAlert

    db = SessionLocal()
    try:
        if db.query(TransactionRecord).count() >= 3:
            return

        now = datetime.utcnow()
        sample_txns = [
            TransactionRecord(
                transaction_id="TXN_98F0231",
                timestamp=now - timedelta(minutes=6),
                customer_id="CUS_7809",
                account_id="ACC_4401",
                amount=48000.0,
                currency="INR",
                transaction_type="WIRE_TRANSFER",
                payment_method="NET_BANKING",
                merchant_category="FINANCIAL_SERVICES",
                risk_score=91.2,
                risk_level="CRITICAL",
                decision="BLOCK",
                is_suspicious=True,
                fraud_probability=0.94,
                anomaly_score=0.88,
                processing_time_ms=14.2,
                reasons_json=json.dumps(["Impossible travel: 6,800 km in 18 minutes", "Amount exceeds 10x customer 30-day baseline"]),
                rules_triggered_json=json.dumps(["RULE_IMPOSSIBLE_TRAVEL", "RULE_VELOCITY_SPIKE"]),
            ),
            TransactionRecord(
                transaction_id="TXN_55D1129",
                timestamp=now - timedelta(minutes=14),
                customer_id="CUS_3120",
                account_id="ACC_8819",
                amount=75000.0,
                currency="INR",
                transaction_type="WIRE_TRANSFER",
                payment_method="NET_BANKING",
                merchant_category="CRYPTO_EXCHANGE",
                risk_score=84.6,
                risk_level="CRITICAL",
                decision="BLOCK",
                is_suspicious=True,
                fraud_probability=0.89,
                anomaly_score=0.82,
                processing_time_ms=16.1,
                reasons_json=json.dumps(["Account takeover pattern: Password reset followed by high-value wire", "Unrecognized new device"]),
                rules_triggered_json=json.dumps(["RULE_NEW_DEVICE_HIGH_AMOUNT"]),
            ),
            TransactionRecord(
                transaction_id="TXN_32E8841",
                timestamp=now - timedelta(minutes=22),
                customer_id="CUS_9914",
                account_id="ACC_1209",
                amount=15000.0,
                currency="INR",
                transaction_type="ATM_WITHDRAWAL",
                payment_method="DEBIT_CARD",
                merchant_category="ATM",
                risk_score=76.4,
                risk_level="HIGH",
                decision="MANUAL_REVIEW",
                is_suspicious=True,
                fraud_probability=0.74,
                anomaly_score=0.71,
                processing_time_ms=15.0,
                reasons_json=json.dumps(["Rapid velocity burst: 6 transactions in 10 minutes", "New beneficiary added"]),
                rules_triggered_json=json.dumps(["RULE_RAPID_VELOCITY"]),
            ),
            TransactionRecord(
                transaction_id="TXN_19A4402",
                timestamp=now - timedelta(minutes=31),
                customer_id="CUS_4091",
                account_id="ACC_6654",
                amount=32500.0,
                currency="INR",
                transaction_type="TRANSFER",
                payment_method="UPI",
                merchant_category="CRYPTO_CASHOUT",
                risk_score=68.9,
                risk_level="HIGH",
                decision="MANUAL_REVIEW",
                is_suspicious=True,
                fraud_probability=0.67,
                anomaly_score=0.64,
                processing_time_ms=13.8,
                reasons_json=json.dumps(["High risk merchant category (Crypto Cashout)", "Connected via anonymous VPN exit node"]),
                rules_triggered_json=json.dumps(["RULE_VPN_ANONYMOUS_IP"]),
            ),
            TransactionRecord(
                transaction_id="TXN_08B2199",
                timestamp=now - timedelta(minutes=42),
                customer_id="CUS_1102",
                account_id="ACC_7721",
                amount=9999.0,
                currency="INR",
                transaction_type="PURCHASE",
                payment_method="UPI",
                merchant_category="ELECTRONICS",
                risk_score=62.1,
                risk_level="HIGH",
                decision="MANUAL_REVIEW",
                is_suspicious=True,
                fraud_probability=0.61,
                anomaly_score=0.59,
                processing_time_ms=14.5,
                reasons_json=json.dumps(["Transaction amount is 4 standard deviations from 30-day average"]),
                rules_triggered_json=json.dumps(["RULE_HIGH_Z_SCORE"]),
            ),
            TransactionRecord(
                transaction_id="TXN_69C31C9",
                timestamp=now - timedelta(minutes=48),
                customer_id="CUS_5580",
                account_id="ACC_3390",
                amount=4800.0,
                currency="INR",
                transaction_type="PURCHASE",
                payment_method="CREDIT_CARD",
                merchant_category="TRAVEL",
                risk_score=57.3,
                risk_level="MEDIUM",
                decision="STEP_UP",
                is_suspicious=False,
                fraud_probability=0.48,
                anomaly_score=0.42,
                processing_time_ms=14.0,
                reasons_json=json.dumps(["Step-up biometric verification required for international booking"]),
                rules_triggered_json=json.dumps([]),
            ),
            TransactionRecord(
                transaction_id="TXN_0519E01",
                timestamp=now - timedelta(minutes=55),
                customer_id="CUS_2241",
                account_id="ACC_9011",
                amount=2400.0,
                currency="INR",
                transaction_type="PURCHASE",
                payment_method="UPI",
                merchant_category="ONLINE_RETAIL",
                risk_score=22.0,
                risk_level="LOW",
                decision="ALLOW",
                is_suspicious=False,
                fraud_probability=0.12,
                anomaly_score=0.15,
                processing_time_ms=11.5,
                reasons_json=json.dumps([]),
                rules_triggered_json=json.dumps([]),
            ),
            TransactionRecord(
                transaction_id="TXN_0199A33",
                timestamp=now - timedelta(minutes=62),
                customer_id="CUS_8902",
                account_id="ACC_4420",
                amount=1250.0,
                currency="INR",
                transaction_type="PURCHASE",
                payment_method="UPI",
                merchant_category="FOOD_DELIVERY",
                risk_score=12.4,
                risk_level="LOW",
                decision="ALLOW",
                is_suspicious=False,
                fraud_probability=0.06,
                anomaly_score=0.08,
                processing_time_ms=10.2,
                reasons_json=json.dumps([]),
                rules_triggered_json=json.dumps([]),
            ),
            TransactionRecord(
                transaction_id="TXN_0341C88",
                timestamp=now - timedelta(minutes=70),
                customer_id="CUS_7719",
                account_id="ACC_5502",
                amount=850.0,
                currency="INR",
                transaction_type="PURCHASE",
                payment_method="DEBIT_CARD",
                merchant_category="GROCERY",
                risk_score=5.1,
                risk_level="LOW",
                decision="ALLOW",
                is_suspicious=False,
                fraud_probability=0.02,
                anomaly_score=0.04,
                processing_time_ms=9.8,
                reasons_json=json.dumps([]),
                rules_triggered_json=json.dumps([]),
            ),
        ]
        db.add_all(sample_txns)

        sample_alerts = [
            FraudAlert(
                alert_id="ALT_98F0231",
                transaction_id="TXN_98F0231",
                created_at=now - timedelta(minutes=6),
                risk_score=91.2,
                risk_level="CRITICAL",
                status="OPEN",
                reasons_json=json.dumps(["Impossible travel: 6,800 km in 18 minutes", "Amount exceeds 10x customer baseline"]),
            ),
            FraudAlert(
                alert_id="ALT_55D1129",
                transaction_id="TXN_55D1129",
                created_at=now - timedelta(minutes=14),
                risk_score=84.6,
                risk_level="CRITICAL",
                status="OPEN",
                reasons_json=json.dumps(["Account takeover: Password reset followed by high-value wire", "Unrecognized device"]),
            ),
            FraudAlert(
                alert_id="ALT_32E8841",
                transaction_id="TXN_32E8841",
                created_at=now - timedelta(minutes=22),
                risk_score=76.4,
                risk_level="HIGH",
                status="OPEN",
                reasons_json=json.dumps(["Rapid velocity burst: 6 transactions in 10 minutes", "New beneficiary added"]),
            ),
            FraudAlert(
                alert_id="ALT_19A4402",
                transaction_id="TXN_19A4402",
                created_at=now - timedelta(minutes=31),
                risk_score=68.9,
                risk_level="HIGH",
                status="OPEN",
                reasons_json=json.dumps(["High risk merchant category (Crypto Cashout)", "Anonymous VPN exit node"]),
            ),
            FraudAlert(
                alert_id="ALT_08B2199",
                transaction_id="TXN_08B2199",
                created_at=now - timedelta(minutes=42),
                risk_score=62.1,
                risk_level="HIGH",
                status="OPEN",
                reasons_json=json.dumps(["Transaction amount is 4 standard deviations from 30-day average"]),
            ),
        ]
        db.add_all(sample_alerts)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
