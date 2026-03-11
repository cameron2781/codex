from __future__ import annotations

from datetime import date
from pathlib import Path
from flask import Flask, abort, g, render_template

from db import initialize
from logic import evaluate_rules, generate_alerts, net_reward_value_cents


BASE_DIR = Path(__file__).resolve().parent


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))
    app.config["DATABASE"] = BASE_DIR / "churning.db"

    @app.before_request
    def before_request() -> None:
        if "db" not in g:
            g.db = initialize(app.config["DATABASE"])

    @app.teardown_appcontext
    def teardown_db(exception: BaseException | None) -> None:
        db_conn = g.pop("db", None)
        if db_conn is not None:
            db_conn.close()

    @app.route("/")
    @app.route("/dashboard")
    def dashboard():
        today = date.today()
        generate_alerts(g.db, today)
        rules = evaluate_rules(g.db, today)
        alerts = g.db.execute(
            "SELECT * FROM alerts WHERE status = 'open' ORDER BY severity DESC, due_date"
        ).fetchall()
        active_cards = g.db.execute(
            "SELECT oc.*, cp.name FROM open_cards oc JOIN card_products cp ON cp.id = oc.card_product_id WHERE oc.status IN ('active','bonus_earned')"
        ).fetchall()
        return render_template(
            "dashboard.html",
            alerts=alerts,
            active_cards=active_cards,
            rules=rules,
            net_value=net_reward_value_cents(g.db),
        )

    @app.route("/opportunities")
    def opportunities():
        today = date.today()
        rules = evaluate_rules(g.db, today)
        cards = g.db.execute(
            "SELECT * FROM card_products WHERE is_seeded = 1 ORDER BY issuer, name"
        ).fetchall()
        return render_template("opportunities.html", cards=cards, rules=rules)

    @app.route("/cards")
    def cards():
        rows = g.db.execute(
            """
            SELECT oc.id, oc.status, oc.open_date, oc.close_date, oc.current_credit_limit_cents,
                   cp.name, cp.issuer
            FROM open_cards oc
            JOIN card_products cp ON cp.id = oc.card_product_id
            ORDER BY oc.open_date DESC
            """
        ).fetchall()
        return render_template("cards.html", cards=rows)

    @app.route("/cards/<card_id>")
    def card_detail(card_id: str):
        card = g.db.execute(
            """
            SELECT oc.*, cp.name, cp.issuer, cp.annual_fee_cents
            FROM open_cards oc
            JOIN card_products cp ON cp.id = oc.card_product_id
            WHERE oc.id = ?
            """,
            (card_id,),
        ).fetchone()
        if card is None:
            abort(404)

        timeline = g.db.execute(
            """
            SELECT event_date, event_type, details
            FROM card_timeline_events
            WHERE open_card_id = ?
            ORDER BY event_date
            """,
            (card_id,),
        ).fetchall()

        spend_progress = g.db.execute(
            """
            SELECT sbw.required_spend_cents, sbw.deadline_date, IFNULL(SUM(se.amount_cents), 0) AS spent_cents
            FROM signup_bonus_windows sbw
            LEFT JOIN spend_entries se ON se.open_card_id = sbw.open_card_id
            WHERE sbw.open_card_id = ?
            GROUP BY sbw.id
            """,
            (card_id,),
        ).fetchone()

        return render_template(
            "card_detail.html", card=card, timeline=timeline, spend_progress=spend_progress
        )

    @app.route("/rules")
    def rules():
        today = date.today()
        snapshots = g.db.execute(
            "SELECT issuer, snapshot_date, source_url, summary FROM issuer_rule_snapshots ORDER BY issuer"
        ).fetchall()
        results = evaluate_rules(g.db, today)
        return render_template("rules.html", snapshots=snapshots, results=results)

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5001)
