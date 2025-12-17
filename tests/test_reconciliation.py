from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_reconciliation_runs():
    r = client.post("/reconciliation/run")
    assert r.status_code == 200
    body = r.json()
    assert "matched" in body
