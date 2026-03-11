from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import sqlite3


@dataclass
class RuleResult:
    issuer: str
    status: str
    reason: str
    snapshot_date: str


def _parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def minimum_spend_deadline(approval_date: str, window_days: int) -> date:
    return _parse_date(approval_date) + timedelta(days=window_days)


def annual_fee_review_date(open_date: str, year_offset: int = 1) -> date:
    opened = _parse_date(open_date)
    return opened.replace(year=opened.year + year_offset)


def count_5_24_slots_used(conn: sqlite3.Connection, as_of: date) -> int:
    start = as_of - timedelta(days=730)
    row = conn.execute(
        """
        SELECT COUNT(*) AS cnt
        FROM open_cards
        WHERE card_type = 'personal' AND open_date >= ?
        """,
        (start.isoformat(),),
    ).fetchone()
    return int(row["cnt"])


def evaluate_rules(conn: sqlite3.Connection, as_of: date) -> list[RuleResult]:
    snapshots = conn.execute(
        """
        SELECT issuer, snapshot_date, content
        FROM issuer_rule_snapshots
        WHERE is_active = 1
        ORDER BY issuer
        """
    ).fetchall()

    slots_used = count_5_24_slots_used(conn, as_of)
    results: list[RuleResult] = []

    for snapshot in snapshots:
        issuer = snapshot["issuer"]
        if issuer == "Chase":
            if slots_used >= 5:
                status = "blocked"
                reason = f"5/24 slots used: {slots_used}/5"
            elif slots_used == 4:
                status = "warning"
                reason = "At 4/24. Next approval likely blocks future Chase approvals."
            else:
                status = "eligible"
                reason = f"Below 5/24 at {slots_used}/5"
        else:
            status = "warning"
            reason = "Manual verification required for conservative rule interpretation."

        results.append(
            RuleResult(
                issuer=issuer,
                status=status,
                reason=reason,
                snapshot_date=snapshot["snapshot_date"],
            )
        )

    return results


def generate_alerts(conn: sqlite3.Connection, as_of: date) -> None:
    conn.execute("DELETE FROM alerts WHERE generated_by_engine = 1")

    windows = conn.execute(
        """
        SELECT sbw.id, sbw.open_card_id, sbw.deadline_date, sbw.required_spend_cents,
               IFNULL(SUM(se.amount_cents), 0) AS spent_cents
        FROM signup_bonus_windows sbw
        LEFT JOIN spend_entries se ON se.open_card_id = sbw.open_card_id
        WHERE sbw.status = 'active'
        GROUP BY sbw.id
        """
    ).fetchall()

    for window in windows:
        deadline = _parse_date(window["deadline_date"])
        days_left = (deadline - as_of).days
        remaining = window["required_spend_cents"] - window["spent_cents"]
        if remaining <= 0:
            severity = "info"
            message = "Minimum spend complete. Mark bonus as earned after statement close."
        elif days_left < 0:
            severity = "high"
            message = f"Signup bonus spend deadline missed by {-days_left} day(s)."
        elif days_left <= 14:
            severity = "medium"
            message = f"{days_left} day(s) left to spend ${remaining / 100:.2f}."
        else:
            continue

        conn.execute(
            """
            INSERT INTO alerts (id, alert_type, status, severity, due_date, message, generated_by_engine)
            VALUES (lower(hex(randomblob(16))), 'spend_deadline', 'open', ?, ?, ?, 1)
            """,
            (severity, window["deadline_date"], message),
        )

    conn.commit()


def net_reward_value_cents(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT IFNULL(SUM(net_value_cents), 0) AS net_total FROM reward_ledger_entries"
    ).fetchone()
    return int(row["net_total"])
