from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.logging import get_logger
from app.db.session import db_session
from app.models import Posting, ReconciliationRun, Transaction
from app.schemas import ReconciliationSummary
from app.services.connectors.mock_bank import get_bank_feed

LOG = get_logger("reconciliation")

def run_reconciliation() -> ReconciliationSummary:
    """Compare internal cash movements to a bank feed.

    This demo uses **amount-based multiset matching**:
      - internal: net movement of any account whose name includes 'cash'
      - bank: movements from the mock feed
    In production you'd match on identifiers, timestamps, rails, fees, and use richer heuristics.
    """
    with db_session() as s:
        run = ReconciliationRun(status="RUNNING")
        s.add(run)
        s.flush()

        try:
            txs = (
                s.scalars(
                    select(Transaction)
                    .options(joinedload(Transaction.postings).joinedload(Posting.account))
                    .where(Transaction.asset == "USD")
                )
                .unique().all()
            )

            internal_amounts: list[float] = []
            for tx in txs:
                net = 0.0
                for p in tx.postings:
                    if "cash" in p.account.name.lower():
                        amt = float(p.amount)
                        net += amt if p.direction == "DEBIT" else -amt
                if abs(net) > 1e-9:
                    internal_amounts.append(net)

            bank = get_bank_feed("USD", days=14)
            bank_amounts = [float(b.amount) for b in bank]

            def multiset(xs):
                m = defaultdict(int)
                for x in xs:
                    m[round(x, 2)] += 1
                return m

            im = multiset(internal_amounts)
            bm = multiset(bank_amounts)

            matched = 0
            missing_in_bank = 0
            missing_in_ledger = 0

            for amt, cnt in im.items():
                m = min(cnt, bm.get(amt, 0))
                matched += m
                if cnt > m:
                    missing_in_bank += (cnt - m)

            for amt, cnt in bm.items():
                m = min(cnt, im.get(amt, 0))
                if cnt > m:
                    missing_in_ledger += (cnt - m)

            summary = ReconciliationSummary(
                matched=matched,
                missing_in_bank=missing_in_bank,
                missing_in_ledger=missing_in_ledger,
                mismatched_amount=0,
                notes=[
                    "Matching is amount-based (demo). Upgrade to reference/date/rail matching heuristics.",
                    f"internal_cash_movements={len(internal_amounts)} bank_movements={len(bank_amounts)}",
                ],
            )

            run.status = "SUCCEEDED"
            run.finished_at = datetime.now(timezone.utc)
            run.summary_json = json.dumps(summary.model_dump())
            s.add(run)
            return summary
        except Exception as e:
            LOG.error(f"reconciliation failed: {e}", exc_info=True)
            run.status = "FAILED"
            run.finished_at = datetime.now(timezone.utc)
            run.summary_json = json.dumps({"error": str(e)})
            s.add(run)
            raise
