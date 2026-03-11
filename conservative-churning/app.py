from __future__ import annotations

import os
from collections import defaultdict
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from flask import Flask, abort, g, render_template

from db import DEFAULT_DB_PATH, connect, run_migrations


def parse_iso(raw: str | None) -> date | None:
    if not raw:
        return None
    return datetime.strptime(raw, "%Y-%m-%d").date()


def cents_to_dollars(cents: int) -> str:
    return f"${cents / 100:,.2f}"


def create_app(db_path: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = str(db_path or os.getenv("CHURN_DB_PATH") or DEFAULT_DB_PATH)

    @app.template_filter("money")
    def money_filter(cents: int) -> str:
        return cents_to_dollars(cents or 0)

    @app.before_request
    def init_db() -> None:
        if "db" in g:
            return
        g.db = connect(app.config["DB_PATH"])
        run_migrations(g.db)

    @app.teardown_appcontext
    def close_db(_: Any) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def db_rows(query: str, params: tuple[Any, ...] = ()):
        return g.db.execute(query, params).fetchall()

    def trailing_open_count(months: int) -> int:
        cutoff = date.today() - timedelta(days=months * 30)
        row = g.db.execute(
            "SELECT COUNT(*) AS count FROM open_card WHERE opened_on >= ?",
            (cutoff.isoformat(),),
        ).fetchone()
        return int(row["count"])

    def evaluate_rules() -> list[dict[str, Any]]:
        snapshots = db_rows(
            """
            SELECT issuer, rule_name, rule_logic, source_date, source_title
            FROM issuer_rule_snapshot
            ORDER BY issuer, source_date DESC
            """
        )
        by_issuer: dict[str, list[sqlite3.Row]] = defaultdict(list)
        for snap in snapshots:
            by_issuer[snap["issuer"]].append(snap)

        cards_24m = trailing_open_count(24)
        cards_6m = trailing_open_count(6)
        results: list[dict[str, Any]] = []
        for issuer, rules in by_issuer.items():
            status = "eligible"
            reason = "No blocking conditions detected."
            rule_date = rules[0]["source_date"]

            if issuer == "Chase" and cards_24m >= 5:
                status = "blocked"
                reason = f"{cards_24m}/24 in trailing 24 months triggers Chase 5/24 block."
            elif issuer == "Capital One" and cards_6m > 1:
                status = "warning"
                reason = (
                    f"{cards_6m} new cards in trailing 6 months; velocity risk for approvals."
                )
            elif issuer in {"Amex", "Citi"}:
                status = "warning"
                reason = "Manual term review required before applying for welcome bonus."

            results.append(
                {
                    "issuer": issuer,
                    "result": status,
                    "reason": reason,
                    "rule_snapshot_date": rule_date,
                    "rules": rules,
                }
            )
        return sorted(results, key=lambda item: item["issuer"])

    def current_alerts() -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        today = date.today()

        windows = db_rows(
            """
            SELECT sbw.id, sbw.open_card_id, sbw.end_date, sbw.required_spend_cents,
                   COALESCE(SUM(se.amount_cents), 0) AS spent_cents, cp.name
            FROM signup_bonus_window sbw
            JOIN open_card oc ON oc.id = sbw.open_card_id
            JOIN card_product cp ON cp.id = oc.card_product_id
            LEFT JOIN spend_entry se ON se.open_card_id = oc.id
            WHERE sbw.status = 'active'
            GROUP BY sbw.id
            """
        )
        for row in windows:
            days_left = (parse_iso(row["end_date"]) - today).days
            remaining = row["required_spend_cents"] - row["spent_cents"]
            if remaining <= 0:
                continue
            severity = "warning" if days_left <= 14 else "info"
            if days_left < 0:
                severity = "critical"
            alerts.append(
                {
                    "type": "spend_deadline",
                    "severity": severity,
                    "message": f"{row['name']}: {cents_to_dollars(remaining)} remaining with {days_left} days left.",
                }
            )

        fee_events = db_rows(
            """
            SELECT afe.id, afe.review_due_on, afe.action_status, cp.name
            FROM annual_fee_event afe
            JOIN open_card oc ON oc.id = afe.open_card_id
            JOIN card_product cp ON cp.id = oc.card_product_id
            WHERE afe.action_status = 'pending'
            """
        )
        for row in fee_events:
            days_to_review = (parse_iso(row["review_due_on"]) - today).days
            severity = "warning" if days_to_review <= 10 else "info"
            if days_to_review < 0:
                severity = "critical"
            alerts.append(
                {
                    "type": "annual_fee_review",
                    "severity": severity,
                    "message": f"{row['name']}: annual fee review due in {days_to_review} days.",
                }
            )

        pay_in_full = db_rows(
            """
            SELECT oc.id, cp.name, oc.statement_balance_cents, oc.pay_in_full_confirmed_on
            FROM open_card oc
            JOIN card_product cp ON cp.id = oc.card_product_id
            WHERE oc.lifecycle_status IN ('active_min_spend', 'bonus_earned', 'annual_fee_review')
            """
        )
        for row in pay_in_full:
            if row["statement_balance_cents"] <= 0:
                continue
            severity = "warning"
            if not row["pay_in_full_confirmed_on"]:
                severity = "critical"
            alerts.append(
                {
                    "type": "pay_in_full_check",
                    "severity": severity,
                    "message": f"{row['name']}: confirm statement paid in full ({cents_to_dollars(row['statement_balance_cents'])}).",
                }
            )

        return alerts

    @app.route("/")
    @app.route("/dashboard")
    def dashboard():
        active_cards = db_rows(
            """
            SELECT oc.id, oc.lifecycle_status, cp.name,
                   COALESCE(sbw.required_spend_cents, 0) AS required_spend_cents,
                   COALESCE((SELECT SUM(amount_cents) FROM spend_entry se WHERE se.open_card_id = oc.id), 0) AS spent_cents,
                   sbw.end_date
            FROM open_card oc
            JOIN card_product cp ON cp.id = oc.card_product_id
            LEFT JOIN signup_bonus_window sbw ON sbw.open_card_id = oc.id AND sbw.status IN ('active', 'earned', 'expired')
            WHERE oc.lifecycle_status NOT IN ('closed')
            ORDER BY oc.opened_on DESC
            """
        )
        ledger = db_rows(
            "SELECT SUM(gross_value_cents) AS gross, SUM(net_value_cents) AS net FROM reward_ledger_entry"
        )[0]
        return render_template(
            "dashboard.html",
            active_cards=active_cards,
            alerts=current_alerts(),
            gross_value=ledger["gross"] or 0,
            net_value=ledger["net"] or 0,
            rule_results=evaluate_rules(),
        )

    @app.route("/opportunities")
    def opportunities():
        cards = db_rows(
            """
            SELECT cp.*, 
                   COALESCE((SELECT COUNT(*) FROM open_card oc WHERE oc.card_product_id = cp.id), 0) AS prior_holds
            FROM card_product cp
            WHERE cp.active = 1
            ORDER BY conservative_cash_value_cents DESC
            """
        )
        rules = {r["issuer"]: r for r in evaluate_rules()}
        opportunities_data = []
        for card in cards:
            issuer_status = rules.get(card["issuer"], {"result": "eligible", "reason": "No issuer rule snapshot."})
            opportunities_data.append({"card": card, "issuer_status": issuer_status})
        return render_template("opportunities.html", opportunities=opportunities_data)

    @app.route("/cards")
    def cards():
        rows = db_rows(
            """
            SELECT oc.id, cp.name, cp.issuer, oc.lifecycle_status, oc.opened_on, oc.closed_on,
                   COALESCE(sbw.required_spend_cents, 0) AS required_spend_cents,
                   COALESCE((SELECT SUM(amount_cents) FROM spend_entry se WHERE se.open_card_id = oc.id), 0) AS spent_cents,
                   sbw.end_date
            FROM open_card oc
            JOIN card_product cp ON cp.id = oc.card_product_id
            LEFT JOIN signup_bonus_window sbw ON sbw.open_card_id = oc.id
            ORDER BY oc.opened_on DESC
            """
        )
        return render_template("cards.html", cards=rows)

    @app.route("/cards/<card_id>")
    def card_detail(card_id: str):
        card = g.db.execute(
            """
            SELECT oc.*, cp.name, cp.issuer, cp.annual_fee_cents, cp.conservative_cash_value_cents
            FROM open_card oc
            JOIN card_product cp ON cp.id = oc.card_product_id
            WHERE oc.id = ?
            """,
            (card_id,),
        ).fetchone()
        if not card:
            abort(404)

        timeline = db_rows(
            """
            SELECT 'application' AS event_type, applied_on AS event_date, status AS details FROM application WHERE id = ?
            UNION ALL
            SELECT 'bonus_window' AS event_type, start_date AS event_date, status AS details FROM signup_bonus_window WHERE open_card_id = ?
            UNION ALL
            SELECT 'annual_fee' AS event_type, fee_posted_on AS event_date, action_status AS details FROM annual_fee_event WHERE open_card_id = ?
            UNION ALL
            SELECT 'reward' AS event_type, entry_date AS event_date, entry_type AS details FROM reward_ledger_entry WHERE open_card_id = ?
            ORDER BY event_date
            """,
            (card["application_id"], card_id, card_id, card_id),
        )

        spends = db_rows(
            "SELECT posted_on, amount_cents, category, memo FROM spend_entry WHERE open_card_id = ? ORDER BY posted_on",
            (card_id,),
        )
        return render_template("card_detail.html", card=card, timeline=timeline, spends=spends)

    @app.route("/rules")
    def rules():
        return render_template("rules.html", results=evaluate_rules())

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
