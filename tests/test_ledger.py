from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_account_and_tx_idempotent():
    # Create accounts
    r = client.post("/accounts", json={"name": "Operating Cash", "asset": "USD", "type": "ASSET"})
    assert r.status_code in (200, 400)  # already exists is fine across repeated test runs

    r = client.post("/accounts", json={"name": "Revenue", "asset": "USD", "type": "INCOME"})
    assert r.status_code in (200, 400)

    payload = {
        "reference": "INV-1",
        "description": "payment",
        "asset": "USD",
        "postings": [
            {"account_name": "Operating Cash", "direction": "DEBIT", "amount": "10.00"},
            {"account_name": "Revenue", "direction": "CREDIT", "amount": "10.00"},
        ],
    }
    r1 = client.post("/transactions", json=payload, headers={"Idempotency-Key": "k1"})
    assert r1.status_code == 200
    tx1 = r1.json()
    r2 = client.post("/transactions", json=payload, headers={"Idempotency-Key": "k1"})
    assert r2.status_code == 200
    tx2 = r2.json()
    assert tx1["id"] == tx2["id"]
    assert Decimal(tx1["postings"][0]["amount"]) == Decimal("10.00")


def test_unbalanced_rejected():
    payload = {
        "reference": "INV-2",
        "description": "bad",
        "asset": "USD",
        "postings": [
            {"account_name": "Operating Cash", "direction": "DEBIT", "amount": "10.00"},
            {"account_name": "Revenue", "direction": "CREDIT", "amount": "9.00"},
        ],
    }
    r = client.post("/transactions", json=payload, headers={"Idempotency-Key": "k2"})
    assert r.status_code == 400
