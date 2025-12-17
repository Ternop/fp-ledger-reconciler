from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    asset: str = Field(min_length=1, max_length=16)
    type: str = Field(pattern="^(ASSET|LIABILITY|INCOME|EXPENSE|EQUITY)$")


class AccountOut(BaseModel):
    id: int
    name: str
    asset: str
    type: str


class PostingIn(BaseModel):
    account_name: str
    direction: str = Field(pattern="^(DEBIT|CREDIT)$")
    amount: Decimal = Field(gt=0)


class TransactionIn(BaseModel):
    reference: str = Field(min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=256)
    asset: str = Field(min_length=1, max_length=16)
    postings: list[PostingIn] = Field(min_length=2)


class PostingOut(BaseModel):
    account_name: str
    direction: str
    amount: Decimal


class TransactionOut(BaseModel):
    id: int
    reference: str
    description: str | None
    asset: str
    created_at: str
    postings: list[PostingOut]


class ReconciliationSummary(BaseModel):
    matched: int
    missing_in_bank: int
    missing_in_ledger: int
    mismatched_amount: int
    notes: list[str] = []
