from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import sqlite3


@dataclass
class RuleResult:
    issuer: str
    status: str
    reason: str
    snapshot_date: str


def _latest_snapshot_dates(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute(
        """
        SELECT issuer, MAX(snapshot_date) AS snapshot_date
        FROM issuer_rule_snapshots
        GROUP BY issuer
        """
    ).fetchall()
    return {row["issuer"]: row["snapshot_date"] for row in rows}


def evaluate_rules(conn: sqlite3.Connection, as_of: date) -> list[RuleResult]:
    snapshots = _latest_snapshot_dates(conn)
    return [
        _eval_chase(conn, as_of, snapshots.get("Chase", "unknown")),
        _eval_amex(conn, snapshots.get("Amex", "unknown")),
        _eval_citi(conn, as_of, snapshots.get("Citi", "unknown")),
        _eval_capital_one(conn, as_of, snapshots.get("Capital One", "unknown")),
    ]


def _eval_chase(conn: sqlite3.Connection, as_of: date, snapshot_date: str) -> RuleResult:
    since = as_of - timedelta(days=730)
    count = conn.execute(
        "SELECT COUNT(*) AS c FROM open_cards WHERE opened_on >= ?",
        (since.isoformat(),),
    ).fetchone()["c"]
    if count >= 5:
        return RuleResult("Chase", "blocked", f"{count}/24 in last 24 months", snapshot_date)
    if count == 4:
        return RuleResult("Chase", "warning", "4/24; next approval risk is elevated", snapshot_date)
    return RuleResult("Chase", "eligible", f"{count}/24 currently", snapshot_date)


def _eval_amex(conn: sqlite3.Connection, snapshot_date: str) -> RuleResult:
    prior = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM reward_ledger_entries r
        JOIN open_cards o ON o.id = r.open_card_id
        JOIN card_products p ON p.id = o.card_product_id
        WHERE p.issuer = 'Amex' AND r.entry_type = 'signup_bonus'
        """
    ).fetchone()["c"]
    if prior > 0:
        return RuleResult("Amex", "warning", "Prior Amex bonus exists; once-per-lifetime risk", snapshot_date)
    return RuleResult("Amex", "eligible", "No prior Amex bonus recorded", snapshot_date)


def _eval_citi(conn: sqlite3.Connection, as_of: date, snapshot_date: str) -> RuleResult:
    since = as_of - timedelta(days=1460)
    prior = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM open_cards o
        JOIN card_products p ON p.id = o.card_product_id
        WHERE p.issuer = 'Citi' AND p.family = 'ThankYou' AND o.opened_on >= ?
        """,
        (since.isoformat(),),
    ).fetchone()["c"]
    if prior > 0:
        return RuleResult("Citi", "blocked", "ThankYou family cooldown active (<48 months)", snapshot_date)
    return RuleResult("Citi", "eligible", "No ThankYou-family open in 48 months", snapshot_date)


def _eval_capital_one(conn: sqlite3.Connection, as_of: date, snapshot_date: str) -> RuleResult:
    six_months_ago = as_of - timedelta(days=183)
    twelve_months_ago = as_of - timedelta(days=365)
    recent = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM open_cards o
        JOIN card_products p ON p.id = o.card_product_id
        WHERE p.issuer = 'Capital One' AND o.opened_on >= ?
        """,
        (six_months_ago.isoformat(),),
    ).fetchone()["c"]
    yearly = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM open_cards o
        JOIN card_products p ON p.id = o.card_product_id
        WHERE p.issuer = 'Capital One' AND o.opened_on >= ?
        """,
        (twelve_months_ago.isoformat(),),
    ).fetchone()["c"]
    if recent > 0:
        return RuleResult("Capital One", "blocked", "Opened Capital One card within 6 months", snapshot_date)
    if yearly >= 1:
        return RuleResult("Capital One", "warning", "1 Capital One card in last 12 months", snapshot_date)
    return RuleResult("Capital One", "eligible", "No recent Capital One velocity concerns", snapshot_date)
