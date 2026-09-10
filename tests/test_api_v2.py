"""Integration tests for upgraded Platform API endpoints."""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_api_presets_endpoint(client):
    response = client.get("/api/presets")
    assert response.status_code == 200
    presets = response.json()
    assert isinstance(presets, list)
    assert len(presets) >= 4
    preset_ids = [p["id"] for p in presets]
    assert "legit_coffee" in preset_ids
    assert "impossible_travel" in preset_ids


def test_system_status_endpoint(client):
    response = client.get("/system/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "components" in body
    assert body["components"]["api"] == "UP"


def test_model_performance_endpoint(client):
    response = client.get("/model/performance")
    assert response.status_code == 200
    body = response.json()
    assert "metrics" in body
    assert "benchmarks" in body
    assert len(body["benchmarks"]) >= 4


def test_feedback_and_alerts_lifecycle(client):
    test_txn_id = f"TXN_ALERT_TEST_{uuid.uuid4().hex[:6].upper()}"

    # 1. Send high-risk transaction that generates an alert
    suspicious_payload = {
        "transaction_id": test_txn_id,
        "amount": 85000.0,
        "distance_from_home": 4500.0,
        "is_new_device": True,
        "is_vpn_proxy": True,
        "customer_avg_amount_30d": 400.0,
        "failed_attempts_last_24h": 5,
    }
    pred_res = client.post("/predict", json=suspicious_payload)
    assert pred_res.status_code == 200
    assert pred_res.json()["risk_score"] >= 60.0

    # 2. Check that fraud alerts contains the transaction
    alerts_res = client.get("/fraud/alerts")
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert any(a["transaction_id"] == test_txn_id for a in alerts)

    # 3. Submit human feedback
    feedback_payload = {
        "transaction_id": test_txn_id,
        "verdict": "CONFIRMED_FRAUD",
        "notes": "Verified unauthorized ATO from overseas VPN IP",
        "analyst_id": "ANALYST_JANE",
    }
    fb_res = client.post("/feedback", json=feedback_payload)
    assert fb_res.status_code == 200
    assert fb_res.json()["status"] == "success"

    # 4. Check recent transactions
    recent_res = client.get("/transactions/recent")
    assert recent_res.status_code == 200
    recent = recent_res.json()
    assert any(r["transaction_id"] == test_txn_id for r in recent)
