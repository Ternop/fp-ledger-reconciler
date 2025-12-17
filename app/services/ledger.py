from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.logging import get_logger
from app.db.session import db_session
from app.models import Account, EventOutbox, Posting, Transaction
from app.schemas import AccountCreate, AccountOut, PostingOut, TransactionIn, TransactionOut

LOG = get_logger("ledger")


def _as_iso(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def create_account(payload: AccountCreate) -> AccountOut:
    with db_session() as s:
        exists = s.scalar(select(Account).where(Account.name == payload.name))
        if exists:
            raise ValueError(f"Account already exists: {payload.name}")
        acc = Account(name=payload.name, asset=payload.asset, type=payload.type)
        s.add(acc)
        s.flush()
        return AccountOut(id=acc.id, name=acc.name, asset=acc.asset, type=acc.type)


def list_accounts() -> list[AccountOut]:
    with db_session() as s:
        rows = s.scalars(select(Account).order_by(Account.id)).all()
        return [AccountOut(id=a.id, name=a.name, asset=a.asset, type=a.type) for a in rows]


def create_transaction(payload: TransactionIn, idempotency_key: str) -> TransactionOut:
    # Validate balanced double-entry
    total_debits = sum((p.amount for p in payload.postings if p.direction == "DEBIT"), Decimal("0"))
    total_credits = sum(
        (p.amount for p in payload.postings if p.direction == "CREDIT"), Decimal("0")
    )
    if total_debits != total_credits:
        raise ValueError(f"Transaction not balanced: debits={total_debits} credits={total_credits}")

    with db_session() as s:
        existing = s.scalar(
            select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        )
        if existing:
            existing = s.scalar(
                select(Transaction)
                .options(joinedload(Transaction.postings).joinedload(Posting.account))
                .where(Transaction.id == existing.id)
            )
            assert existing
            return _tx_out(existing)

        tx = Transaction(
            reference=payload.reference,
            description=payload.description,
            asset=payload.asset,
            idempotency_key=idempotency_key,
        )
        s.add(tx)
        s.flush()

        # Attach postings
        for p in payload.postings:
            acct = s.scalar(select(Account).where(Account.name == p.account_name))
            if not acct:
                raise ValueError(f"Unknown account: {p.account_name}")
            if acct.asset != payload.asset:
                raise ValueError(
                    f"Asset mismatch for {acct.name}: account={acct.asset} tx={payload.asset}"
                )
            tx.postings.append(Posting(account_id=acct.id, direction=p.direction, amount=p.amount))

        # Outbox event (for downstream processing)
        s.add(
            EventOutbox(
                event_type="transaction.created",
                payload_json=json.dumps(
                    {"transaction_id": tx.id, "reference": tx.reference, "asset": tx.asset}
                ),
            )
        )
        s.flush()
        s.refresh(tx)

        tx = s.scalar(
            select(Transaction)
            .options(joinedload(Transaction.postings).joinedload(Posting.account))
            .where(Transaction.id == tx.id)
        )
        assert tx
        return _tx_out(tx)


def _tx_out(tx: Transaction) -> TransactionOut:
    postings = [
        PostingOut(account_name=p.account.name, direction=p.direction, amount=p.amount)
        for p in tx.postings
    ]
    return TransactionOut(
        id=tx.id,
        reference=tx.reference,
        description=tx.description,
        asset=tx.asset,
        created_at=_as_iso(tx.created_at),
        postings=postings,
    )


def list_transactions(limit: int = 50) -> list[TransactionOut]:
    limit = max(1, min(limit, 500))
    with db_session() as s:
        txs = (
            s.scalars(
                select(Transaction)
                .options(joinedload(Transaction.postings).joinedload(Posting.account))
                .order_by(Transaction.id.desc())
                .limit(limit)
            )
            .unique()
            .all()
        )
        return [_tx_out(tx) for tx in txs]
