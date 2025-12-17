from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from app.core.logging import get_logger
from app.schemas import (
    AccountCreate,
    AccountOut,
    ReconciliationSummary,
    TransactionIn,
    TransactionOut,
)
from app.services.ledger import create_account, create_transaction, list_accounts, list_transactions
from app.services.reconciliation import run_reconciliation

LOG = get_logger("routes")
router = APIRouter()


@router.post("/accounts", response_model=AccountOut)
def create_account_route(payload: AccountCreate):
    try:
        return create_account(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts_route():
    return list_accounts()


@router.post("/transactions", response_model=TransactionOut)
def create_transaction_route(
    payload: TransactionIn,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key header")
    try:
        return create_transaction(payload, idempotency_key=idempotency_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions_route(limit: int = 50):
    return list_transactions(limit=limit)


@router.post("/reconciliation/run", response_model=ReconciliationSummary)
def reconciliation_run_route():
    return run_reconciliation()
