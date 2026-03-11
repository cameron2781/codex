from datetime import date, timedelta

from app import db, services


def setup_seeded_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test.sqlite3"
    monkeypatch.setattr(db, "DB_PATH", test_db)
    monkeypatch.setattr(services, "get_connection", lambda: db.get_connection(test_db))
    conn = db.get_connection(test_db)
    db.run_migrations(conn)
    services.seed_if_empty(conn)
    conn.close()
    return test_db


def test_lifecycle_transitions_include_downgrade_and_closed(tmp_path, monkeypatch):
    test_db = setup_seeded_db(tmp_path, monkeypatch)
    conn = db.get_connection(test_db)
    conn.execute("UPDATE open_cards SET status='annual_fee_review' WHERE id='open-current-savor'")
    conn.execute("UPDATE annual_fee_events SET review_status='downgraded' WHERE id='af-current-savor'")
    conn.execute("UPDATE open_cards SET status='downgraded' WHERE id='open-current-savor'")
    conn.execute("UPDATE open_cards SET status='closed', closed_on='2026-04-01' WHERE id='open-current-savor'")
    conn.commit()
    conn.close()

    detail = services.card_detail("open-current-savor")
    assert detail["card"]["status"] == "closed"
    assert detail["card"]["closed_on"] == "2026-04-01"
    assert any(event[1] == "Card closed" for event in detail["timeline"])


def test_date_windows_for_spend_deadline_and_annual_fee(tmp_path, monkeypatch):
    test_db = setup_seeded_db(tmp_path, monkeypatch)
    conn = db.get_connection(test_db)
    soon = (date.today() + timedelta(days=10)).isoformat()
    fee_soon = (date.today() + timedelta(days=30)).isoformat()
    conn.execute("UPDATE signup_bonus_windows SET deadline_on=? WHERE id='window-current-savor'", (soon,))
    conn.execute("UPDATE annual_fee_events SET expected_on=? WHERE id='af-current-savor'", (fee_soon,))
    conn.commit()
    conn.close()

    services.generate_alerts()
    conn = db.get_connection(test_db)
    alerts = conn.execute("SELECT alert_type, message FROM alerts WHERE status='open'").fetchall()
    conn.close()
    assert {a["alert_type"] for a in alerts} >= {"signup_deadline", "annual_fee_review", "pay_in_full_check"}


def test_rule_boundaries_for_chase_5_24(tmp_path, monkeypatch):
    test_db = setup_seeded_db(tmp_path, monkeypatch)
    conn = db.get_connection(test_db)
    # Seed up to 4/24.
    for i in range(2):
        conn.execute(
            "INSERT INTO open_cards VALUES (?, 'card-citi-custom-cash', date('now', '-1 month'), NULL, 'bonus_earned', NULL, NULL, NULL)",
            (f"open-extra-{i}",),
        )
    conn.commit()
    warning = services.evaluate_rules(conn, "Chase")
    assert warning.status == "warning"

    conn.execute(
        "INSERT INTO open_cards VALUES ('open-extra-3', 'card-amex-bce', date('now', '-1 month'), NULL, 'active', NULL, NULL, NULL)"
    )
    conn.commit()
    blocked = services.evaluate_rules(conn, "Chase")
    conn.close()
    assert blocked.status == "blocked"


def test_net_value_calculation_fee_and_no_fee(tmp_path, monkeypatch):
    test_db = setup_seeded_db(tmp_path, monkeypatch)
    conn = db.get_connection(test_db)
    conn.execute(
        "INSERT INTO reward_ledger_entries VALUES ('reward-fee', 'open-current-savor', '2026-03-10', 'bonus', 90000, 9500, 80500, 'Fee-bearing card example')"
    )
    conn.execute(
        "INSERT INTO reward_ledger_entries VALUES ('reward-no-fee', 'open-old-freedom', '2026-03-10', 'cashback', 10000, 0, 10000, 'No-fee example')"
    )
    conn.commit()
    totals = conn.execute("SELECT SUM(gross_value_cents) AS gross, SUM(net_value_cents) AS net FROM reward_ledger_entries").fetchone()
    conn.close()
    assert totals["gross"] > totals["net"]


def test_backfilled_history_affects_dashboard_counts(tmp_path, monkeypatch):
    setup_seeded_db(tmp_path, monkeypatch)
    data = services.dashboard_data()
    assert data["active_cards"] == 2
    assert data["gross"] == 20000
    assert data["net"] == 20000
