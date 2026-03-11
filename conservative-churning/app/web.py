from flask import Flask, abort, render_template

from .services import (
    card_detail,
    dashboard_data,
    fetch_cards,
    init_app_data,
    money,
    opportunities,
    rules_data,
)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.jinja_env.globals["money"] = money

    init_app_data()

    @app.get("/")
    @app.get("/dashboard")
    def dashboard():
        return render_template("dashboard.html", data=dashboard_data())

    @app.get("/opportunities")
    def opportunities_view():
        return render_template("opportunities.html", cards=opportunities())

    @app.get("/cards")
    def cards_view():
        return render_template("cards.html", cards=fetch_cards())

    @app.get("/cards/<card_id>")
    def card_detail_view(card_id: str):
        detail = card_detail(card_id)
        if not detail:
            abort(404)
        return render_template("card_detail.html", detail=detail)

    @app.get("/rules")
    def rules_view():
        return render_template("rules.html", rows=rules_data())

    return app
