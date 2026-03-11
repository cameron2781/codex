from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import sqlite3

from flask import Flask, abort, g, render_template

from db import apply_migrations, get_connection
from rules import evaluate_rules
from logic import status_for_due_date

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "churning.sqlite3"


def create_app(db_path: Path = DB_PATH) -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path

    @app.before_request
    def before_request() -> None:
        g.db = get_connection(app.config["DB_PATH"])

    @app.teardown_request
    def teardown_request(_: Exception | None) -> None:
        db = getattr(g, "db", None)
        if db is not None:
            db.close()

    @app.route("/")
    @app.route("/dashboard")
    def dashboard():
        today = date.today()
        alerts = _compute_alerts(g.db, today)
        rules = evaluate_rules(g.db, today)
        totals = _dashboard_totals(g.db)
        return render_template("dashboard.html", alerts=alerts, rules=rules, totals=totals, today=today)

    @app.route("/opportunities")
    def opportunities():
        today = date.today()
        rules = {r.issuer: r for r in evaluate_rules(g.db, today)}
        cards = g.db.execute(
            "SELECT * FROM card_products ORDER BY issuer, annual_fee_cents ASC"
        ).fetchall()
        rows = []
        for card in cards:
            rule = rules.get(card["issuer"])
            gross = int(card["bonus_points"] * card["valuation_cpp"])
            net = gross - card["annual_fee_cents"]
            rows.append({"card": card, "rule": rule, "gross": gross, "net": net})
        return render_template("opportunities.html", rows=rows)

    @app.route("/cards")
    def cards():
        rows = g.db.execute(
            """
            SELECT o.*, p.name, p.issuer,
                   COALESCE(SUM(s.amount_cents), 0) AS spent_cents
            FROM open_cards o
            JOIN card_products p ON p.id = o.card_product_id
            LEFT JOIN spend_entries s ON s.open_card_id = o.id
            GROUP BY o.id
            ORDER BY o.opened_on DESC
            """
        ).fetchall()
        windows = {
            row["open_card_id"]: row
            for row in g.db.execute(
                "SELECT * FROM signup_bonus_windows WHERE status != 'expired'"
            ).fetchall()
        }
        return render_template("cards.html", rows=rows, windows=windows)

    @app.route("/cards/<card_id>")
    def card_detail(card_id: str):
        card = g.db.execute(
            """
            SELECT o.*, p.name, p.issuer, p.family, p.annual_fee_cents
            FROM open_cards o
            JOIN card_products p ON p.id = o.card_product_id
            WHERE o.id = ?
            """,
            (card_id,),
        ).fetchone()
        if not card:
            abort(404)
        spends = g.db.execute(
            "SELECT * FROM spend_entries WHERE open_card_id = ? ORDER BY spent_on",
            (card_id,),
        ).fetchall()
        bonus = g.db.execute(
            "SELECT * FROM signup_bonus_windows WHERE open_card_id = ?",
            (card_id,),
        ).fetchone()
        fees = g.db.execute(
            "SELECT * FROM annual_fee_events WHERE open_card_id = ? ORDER BY fee_posted_on",
            (card_id,),
        ).fetchall()
        ledger = g.db.execute(
            "SELECT * FROM reward_ledger_entries WHERE open_card_id = ? ORDER BY posted_on",
            (card_id,),
        ).fetchall()
        return render_template("card_detail.html", card=card, spends=spends, bonus=bonus, fees=fees, ledger=ledger)

    @app.route("/rules")
    def rules():
        results = evaluate_rules(g.db, date.today())
        raw_snapshots = g.db.execute(
            "SELECT * FROM issuer_rule_snapshots ORDER BY issuer, snapshot_date DESC"
        ).fetchall()
        return render_template("rules.html", results=results, snapshots=raw_snapshots)

    return app


def _dashboard_totals(conn: sqlite3.Connection) -> dict[str, int]:
    active_cards = conn.execute(
        "SELECT COUNT(*) AS c FROM open_cards WHERE status NOT IN ('closed', 'downgraded')"
    ).fetchone()["c"]
    rewards = conn.execute(
        "SELECT COALESCE(SUM(net_value_cents), 0) AS net FROM reward_ledger_entries"
    ).fetchone()["net"]
    pending_alerts = conn.execute(
        "SELECT COUNT(*) AS c FROM alerts WHERE status IN ('due_soon', 'overdue')"
    ).fetchone()["c"]
    return {"active_cards": active_cards, "net_rewards": rewards, "pending_alerts": pending_alerts}


def _compute_alerts(conn: sqlite3.Connection, today: date) -> list[dict]:
    generated: list[dict] = []
    windows = conn.execute("SELECT * FROM signup_bonus_windows WHERE status = 'active'").fetchall()
    for window in windows:
        due = date.fromisoformat(window["ends_on"])
        status = status_for_due_date(today, due)
        generated.append(
            {
                "title": "Minimum spend deadline",
                "detail": f"Window {window['id']} ends {window['ends_on']}",
                "due_on": window["ends_on"],
                "status": status,
            }
        )
    fees = conn.execute(
        "SELECT * FROM annual_fee_events WHERE resolved_on IS NULL"
    ).fetchall()
    for fee in fees:
        due = date.fromisoformat(fee["due_review_on"])
        generated.append(
            {
                "title": "Annual fee review",
                "detail": f"Fee event {fee['id']} review due",
                "due_on": fee["due_review_on"],
                "status": status_for_due_date(today, due),
            }
        )
    monthly_check_due = today.replace(day=1) + timedelta(days=27)
    generated.append(
        {
            "title": "Pay in full confirmed",
            "detail": "Manual monthly safety check",
            "due_on": monthly_check_due.isoformat(),
            "status": status_for_due_date(today, monthly_check_due),
        }
    )
    return sorted(generated, key=lambda item: item["due_on"])



if __name__ == "__main__":
    app = create_app()
    with get_connection(DB_PATH) as conn:
        apply_migrations(conn)
    app.run(debug=True)
