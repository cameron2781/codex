from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import uuid

from .db import get_connection, run_migrations

DATE_FMT = "%Y-%m-%d"


def today() -> date:
    return date.today()


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, DATE_FMT).date()


def days_until(target: str | None) -> int | None:
    d = parse_date(target)
    if not d:
        return None
    return (d - today()).days


def money(cents: int) -> str:
    return f"${cents / 100:,.2f}"


@dataclass
class RuleResult:
    issuer: str
    status: str
    reason: str
    snapshot_date: str


def init_app_data() -> None:
    conn = get_connection()
    run_migrations(conn)
    seed_if_empty(conn)
    conn.close()


def seed_if_empty(conn) -> None:
    card_count = conn.execute("SELECT COUNT(*) AS c FROM card_products").fetchone()["c"]
    if card_count:
        return

    cards = [
        ("card-chase-freedom-unlimited", "Chase", "Freedom Unlimited", 0, 20000, 50000, 90, "Chase Freedom", 1),
        ("card-cap1-savor", "Capital One", "Savor", 0, 20000, 50000, 90, "Capital One Cashback", 1),
        ("card-citi-custom-cash", "Citi", "Custom Cash", 0, 20000, 150000, 180, "Citi ThankYou", 1),
        ("card-amex-bce", "American Express", "Blue Cash Everyday", 0, 20000, 200000, 180, "AmEx Cashback", 1),
    ]
    conn.executemany(
        """
        INSERT INTO card_products
        (id, issuer, name, annual_fee_cents, bonus_value_cents, spend_requirement_cents, spend_window_days, family, active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        cards,
    )

    snapshots = [
        ("rule-chase-5-24", "Chase", "5/24", "Blocked at 5+ new personal cards in 24 months.", None, 24, 5, "NerdWallet", "https://www.nerdwallet.com/article/travel/chase-5-24-rule-explained", "2026-03-11"),
        ("rule-amex-lifetime", "American Express", "lifetime-language", "Welcome bonus often unavailable if card held before.", 365, None, 1, "Frequent Miler", "https://frequentmiler.com/amex-application-rules/", "2026-03-11"),
        ("rule-citi-family", "Citi", "family-window", "Family bonus restrictions based on prior open/close/bonus windows.", 730, 48, 1, "Doctor of Credit", "https://www.doctorofcredit.com/credit-card-reference-pages/#Citi", "2026-03-11"),
        ("rule-cap1-velocity", "Capital One", "velocity", "Warning when multiple recent applications in a short period.", 180, 6, 2, "NerdWallet", "https://www.nerdwallet.com/", "2026-03-11"),
    ]
    conn.executemany(
        """
        INSERT INTO issuer_rule_snapshots
        (id, issuer, rule_key, summary, cooldown_days, lookback_months, threshold_count, source_name, source_url, captured_on)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        snapshots,
    )

    conn.execute(
        """
        INSERT INTO applications (id, card_product_id, applied_on, status, decision_on, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("app-old-freedom", "card-chase-freedom-unlimited", "2024-08-01", "approved", "2024-08-03", "Backfilled historical approval"),
    )
    conn.execute(
        """
        INSERT INTO open_cards (id, card_product_id, opened_on, closed_on, status, current_credit_limit_cents, pay_in_full_confirmed_on, source_application_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("open-old-freedom", "card-chase-freedom-unlimited", "2024-08-05", None, "bonus_earned", 800000, "2026-03-02", "app-old-freedom"),
    )
    conn.execute(
        """
        INSERT INTO reward_ledger_entries
        (id, open_card_id, entry_on, entry_type, gross_value_cents, annual_fee_cents, net_value_cents, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("reward-old-freedom", "open-old-freedom", "2024-11-10", "bonus", 20000, 0, 20000, "Backfilled bonus"),
    )

    conn.execute(
        """
        INSERT INTO applications (id, card_product_id, applied_on, status, decision_on, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("app-current-savor", "card-cap1-savor", "2026-02-20", "approved", "2026-02-21", "Pilot card"),
    )
    conn.execute(
        """
        INSERT INTO open_cards (id, card_product_id, opened_on, closed_on, status, current_credit_limit_cents, pay_in_full_confirmed_on, source_application_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("open-current-savor", "card-cap1-savor", "2026-02-25", None, "active_min_spend", 1000000, None, "app-current-savor"),
    )
    conn.execute(
        """
        INSERT INTO signup_bonus_windows (id, open_card_id, required_spend_cents, deadline_on, bonus_posted_on, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("window-current-savor", "open-current-savor", 50000, "2026-05-26", None, "active"),
    )
    conn.executemany(
        """
        INSERT INTO spend_entries (id, open_card_id, spent_on, amount_cents, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("spend-1", "open-current-savor", "2026-02-28", 15000, "Groceries"),
            ("spend-2", "open-current-savor", "2026-03-05", 10000, "Utilities"),
        ],
    )
    conn.execute(
        """
        INSERT INTO annual_fee_events (id, open_card_id, expected_on, posted_on, fee_cents, review_status, review_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        ("af-current-savor", "open-current-savor", "2027-02-25", None, 0, "pending", "Review keep/downgrade before anniversary"),
    )
    conn.commit()


def fetch_cards() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT oc.id, cp.issuer, cp.name, oc.opened_on, oc.closed_on, oc.status,
               COALESCE(SUM(se.amount_cents), 0) AS total_spend,
               sbw.required_spend_cents,
               sbw.deadline_on
        FROM open_cards oc
        JOIN card_products cp ON cp.id = oc.card_product_id
        LEFT JOIN spend_entries se ON se.open_card_id = oc.id
        LEFT JOIN signup_bonus_windows sbw ON sbw.open_card_id = oc.id
        GROUP BY oc.id
        ORDER BY oc.opened_on DESC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def evaluate_rules(conn, issuer: str) -> RuleResult:
    snap = conn.execute(
        "SELECT * FROM issuer_rule_snapshots WHERE issuer = ? ORDER BY captured_on DESC LIMIT 1", (issuer,)
    ).fetchone()
    if not snap:
        return RuleResult(issuer, "warning", "No snapshot configured.", "unknown")

    new_cards_24 = conn.execute(
        "SELECT COUNT(*) AS c FROM open_cards WHERE opened_on >= date('now', '-24 months')"
    ).fetchone()["c"]

    if issuer == "Chase" and new_cards_24 >= 5:
        return RuleResult(issuer, "blocked", "At or above 5/24 threshold.", snap["captured_on"])
    if issuer == "Chase" and new_cards_24 == 4:
        return RuleResult(issuer, "warning", "At 4/24; next approval likely blocks Chase cards.", snap["captured_on"])

    recent_apps = conn.execute(
        "SELECT COUNT(*) AS c FROM applications WHERE applied_on >= date('now', '-180 days')"
    ).fetchone()["c"]
    if issuer == "Capital One" and recent_apps >= 2:
        return RuleResult(issuer, "warning", "Recent application velocity may reduce approval odds.", snap["captured_on"])

    return RuleResult(issuer, "eligible", "No conservative rule blocks detected.", snap["captured_on"])


def opportunities() -> list[dict]:
    conn = get_connection()
    cards = conn.execute("SELECT * FROM card_products WHERE active = 1 ORDER BY issuer, name").fetchall()
    out = []
    for row in cards:
        result = evaluate_rules(conn, row["issuer"])
        out.append({
            "card": dict(row),
            "rule": result,
        })
    conn.close()
    return out


def card_detail(card_id: str) -> dict | None:
    conn = get_connection()
    card = conn.execute(
        """
        SELECT oc.*, cp.issuer, cp.name, cp.annual_fee_cents, cp.bonus_value_cents
        FROM open_cards oc JOIN card_products cp ON cp.id = oc.card_product_id
        WHERE oc.id = ?
        """,
        (card_id,),
    ).fetchone()
    if not card:
        conn.close()
        return None

    spends = conn.execute("SELECT * FROM spend_entries WHERE open_card_id = ? ORDER BY spent_on", (card_id,)).fetchall()
    bonus = conn.execute("SELECT * FROM signup_bonus_windows WHERE open_card_id = ?", (card_id,)).fetchone()
    fees = conn.execute("SELECT * FROM annual_fee_events WHERE open_card_id = ? ORDER BY expected_on", (card_id,)).fetchall()
    rewards = conn.execute("SELECT * FROM reward_ledger_entries WHERE open_card_id = ? ORDER BY entry_on", (card_id,)).fetchall()

    timeline = []
    timeline.append((card["opened_on"], f"Opened {card['issuer']} {card['name']}", "active"))
    if bonus:
        timeline.append((bonus["deadline_on"], "Signup bonus deadline", bonus["status"]))
    for fee in fees:
        timeline.append((fee["expected_on"], "Annual fee review", fee["review_status"]))
    if card["closed_on"]:
        timeline.append((card["closed_on"], "Card closed", "closed"))
    timeline.sort(key=lambda item: item[0])

    total_spend = sum([s["amount_cents"] for s in spends])
    conn.close()
    return {
        "card": dict(card),
        "spends": [dict(s) for s in spends],
        "bonus": dict(bonus) if bonus else None,
        "fees": [dict(f) for f in fees],
        "rewards": [dict(r) for r in rewards],
        "timeline": timeline,
        "total_spend": total_spend,
    }


def generate_alerts() -> None:
    conn = get_connection()
    conn.execute("DELETE FROM alerts WHERE status = 'open'")

    cards = conn.execute("SELECT * FROM open_cards WHERE closed_on IS NULL").fetchall()
    created_on = today().strftime(DATE_FMT)

    for card in cards:
        if not card["pay_in_full_confirmed_on"]:
            conn.execute(
                "INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    card["id"],
                    "pay_in_full_check",
                    created_on,
                    "open",
                    "Manual pay-in-full confirmation required this week.",
                    created_on,
                    None,
                ),
            )

    windows = conn.execute("SELECT * FROM signup_bonus_windows WHERE status = 'active'").fetchall()
    for window in windows:
        due = days_until(window["deadline_on"])
        if due is None:
            continue
        if due < 0:
            msg = "Signup spend deadline overdue."
        elif due <= 14:
            msg = f"Signup spend deadline due in {due} days."
        else:
            continue
        conn.execute(
            "INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                window["open_card_id"],
                "signup_deadline",
                window["deadline_on"],
                "open",
                msg,
                created_on,
                None,
            ),
        )

    fees = conn.execute("SELECT * FROM annual_fee_events WHERE review_status = 'pending'").fetchall()
    for fee in fees:
        due = days_until(fee["expected_on"])
        if due is not None and due <= 45:
            conn.execute(
                "INSERT INTO alerts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    fee["open_card_id"],
                    "annual_fee_review",
                    fee["expected_on"],
                    "open",
                    "Annual fee review window is approaching.",
                    created_on,
                    None,
                ),
            )

    conn.commit()
    conn.close()


def dashboard_data() -> dict:
    conn = get_connection()
    generate_alerts()
    alerts = conn.execute("SELECT * FROM alerts WHERE status = 'open' ORDER BY due_on").fetchall()
    active_cards = conn.execute("SELECT COUNT(*) AS c FROM open_cards WHERE closed_on IS NULL").fetchone()["c"]
    rules = conn.execute("SELECT DISTINCT issuer FROM issuer_rule_snapshots ORDER BY issuer").fetchall()
    rule_results = [evaluate_rules(conn, row["issuer"]) for row in rules]
    reward_totals = conn.execute(
        "SELECT COALESCE(SUM(gross_value_cents),0) AS gross, COALESCE(SUM(net_value_cents),0) AS net FROM reward_ledger_entries"
    ).fetchone()
    conn.close()
    return {
        "alerts": [dict(a) for a in alerts],
        "active_cards": active_cards,
        "rule_results": rule_results,
        "gross": reward_totals["gross"],
        "net": reward_totals["net"],
    }


def rules_data() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM issuer_rule_snapshots ORDER BY issuer, captured_on DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]
