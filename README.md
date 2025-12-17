# FP Ledger Reconciler (Canonical Financial Record Demo)

A production-style **double-entry ledger** + **bank feed reconciliation** service inspired by Finance Primitives teams:
- Canonical ledger primitives (accounts, journal entries, postings)
- Idempotent transaction ingestion (idempotency keys)
- Reconciliation job that compares internal ledger vs an external bank feed
- REST API (FastAPI), SQLAlchemy 2.0, Alembic migrations
- Metrics endpoint (Prometheus), structured logs, health checks
- Docker + docker-compose (Postgres included)
- CI (pytest + ruff) via GitHub Actions

> This is a portfolio project: it's intentionally simplified but built with real patterns (idempotency, outbox-style events table, reconciliation).

## Quickstart (local)
```bash
# 1) Create venv + install
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

# 2) Run migrations (SQLite by default)
alembic upgrade head

# 3) Run API
uvicorn app.main:app --reload
```

Open:
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Metrics: http://127.0.0.1:8000/metrics

## Docker (recommended)
```bash
docker compose up --build
```

## Example flow
```bash
# Create 2 accounts
curl -s -X POST http://localhost:8000/accounts -H "content-type: application/json" \
  -d '{"name":"Operating Cash","asset":"USD","type":"ASSET"}' | jq

curl -s -X POST http://localhost:8000/accounts -H "content-type: application/json" \
  -d '{"name":"Revenue","asset":"USD","type":"INCOME"}' | jq

# Post a payment (double entry) with an idempotency key
curl -s -X POST http://localhost:8000/transactions \
  -H "content-type: application/json" \
  -H "Idempotency-Key: demo-001" \
  -d '{
    "reference":"INV-1001",
    "description":"Customer payment",
    "asset":"USD",
    "postings":[
      {"account_name":"Operating Cash","direction":"DEBIT","amount":"100.00"},
      {"account_name":"Revenue","direction":"CREDIT","amount":"100.00"}
    ]
  }' | jq

# Run reconciliation (compares internal ledger cash movements vs mock bank feed)
curl -s -X POST http://localhost:8000/reconciliation/run | jq
```

## Tech
Python 3.11+, FastAPI, SQLAlchemy, Alembic, Postgres/SQLite, Prometheus, GitHub Actions, Docker.
