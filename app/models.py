from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    asset: Mapped[str] = mapped_column(String(16), nullable=False)
    type: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # ASSET/LIABILITY/INCOME/EXPENSE/EQUITY
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    postings: Mapped[list[Posting]] = relationship(back_populates="account")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(256), nullable=True)
    asset: Mapped[str] = mapped_column(String(16), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )

    postings: Mapped[list[Posting]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )


class Posting(Base):
    __tablename__ = "postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"), index=True, nullable=False
    )
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True, nullable=False)

    direction: Mapped[str] = mapped_column(String(6), nullable=False)  # DEBIT/CREDIT
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)

    transaction: Mapped[Transaction] = relationship(back_populates="postings")
    account: Mapped[Account] = relationship(back_populates="postings")


class EventOutbox(Base):
    __tablename__ = "events_outbox"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReconciliationRun(Base):
    __tablename__ = "reconciliation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)  # RUNNING/SUCCEEDED/FAILED
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary_json: Mapped[str | None] = mapped_column(Text, nullable=True)
