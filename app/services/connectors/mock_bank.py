from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import random

@dataclass(frozen=True)
class BankMovement:
    reference: str
    booked_at: datetime
    amount: Decimal  # positive for incoming, negative for outgoing
    currency: str

def get_bank_feed(currency: str, days: int = 14) -> list[BankMovement]:
    """Mock bank feed generator.

    In a real system this would call an external provider (bank APIs, aggregators, etc.).
    We generate deterministic-ish data for demos.
    """
    now = datetime.now(timezone.utc)
    random.seed(currency + str(days))
    out: list[BankMovement] = []
    for i in range(15):
        amt = Decimal(str(random.choice([25, 50, 75, 100, 150, 200]))) * Decimal("1.00")
        if random.random() < 0.35:
            amt = -amt
        out.append(
            BankMovement(
                reference=f"BANK-{i:04d}",
                booked_at=now - timedelta(days=random.randint(0, days)),
                amount=amt,
                currency=currency,
            )
        )
    return out
