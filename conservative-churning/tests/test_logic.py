import tempfile
import unittest
from datetime import date
from pathlib import Path

from db import initialize
from logic import (
    annual_fee_review_date,
    evaluate_rules,
    generate_alerts,
    minimum_spend_deadline,
    net_reward_value_cents,
)


class ConservativeChurningTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test.db"
        self.conn = initialize(self.db_path)

    def tearDown(self):
        self.conn.close()
        self.tmpdir.cleanup()

    def test_date_window_calculations(self):
        self.assertEqual(minimum_spend_deadline("2026-01-01", 90).isoformat(), "2026-04-01")
        self.assertEqual(annual_fee_review_date("2025-03-15").isoformat(), "2026-03-15")

    def test_chase_5_24_boundaries(self):
        for idx in range(4):
            self.conn.execute(
                """
                INSERT INTO open_cards (id, card_product_id, lifecycle_stage, status, open_date, card_type)
                VALUES (?, 'cp_chase_flex', 'active', 'active', ?, 'personal')
                """,
                (f"oc_test_{idx}", f"2025-0{idx + 1}-01"),
            )
        self.conn.commit()

        results = {result.issuer: result for result in evaluate_rules(self.conn, date(2026, 1, 20))}
        self.assertEqual(results["Chase"].status, "blocked")

        self.conn.execute("DELETE FROM open_cards WHERE id='oc_test_3'")
        self.conn.commit()
        results = {result.issuer: result for result in evaluate_rules(self.conn, date(2026, 1, 20))}
        self.assertEqual(results["Chase"].status, "warning")

    def test_net_value_calculation_fee_and_no_fee(self):
        self.assertEqual(net_reward_value_cents(self.conn), 40000)
        self.conn.execute(
            """
            INSERT INTO reward_ledger_entries
            (id, open_card_id, entry_date, entry_type, gross_value_cents, annual_fee_cents, net_value_cents, notes)
            VALUES ('rle_fee', 'oc_001', '2026-01-01', 'annual_fee', 0, 9500, -9500, 'annual fee posted')
            """
        )
        self.conn.commit()
        self.assertEqual(net_reward_value_cents(self.conn), 30500)

    def test_alert_generation_due_soon_and_overdue(self):
        self.conn.execute(
            """
            UPDATE signup_bonus_windows
            SET status='active', deadline_date='2026-01-10', required_spend_cents=100000
            WHERE id='sbw_001'
            """
        )
        self.conn.commit()
        generate_alerts(self.conn, date(2026, 1, 1))
        due_soon = self.conn.execute("SELECT * FROM alerts WHERE generated_by_engine = 1").fetchall()
        self.assertTrue(len(due_soon) >= 1)

        generate_alerts(self.conn, date(2026, 2, 1))
        overdue = self.conn.execute(
            "SELECT * FROM alerts WHERE generated_by_engine = 1 AND severity='high'"
        ).fetchall()
        self.assertTrue(len(overdue) >= 1)

    def test_backfilled_history_counts(self):
        count = self.conn.execute("SELECT COUNT(*) AS cnt FROM open_cards WHERE status='active'").fetchone()["cnt"]
        self.assertEqual(count, 1)

    def test_lifecycle_transitions_application_to_closed(self):
        self.conn.execute(
            "INSERT INTO applications (id, card_product_id, applied_on, status, decision_on) VALUES ('app_x', 'cp_cap1_savor', '2026-01-01', 'approved', '2026-01-02')"
        )
        self.conn.execute(
            """
            INSERT INTO open_cards (id, card_product_id, application_id, lifecycle_stage, status, open_date, card_type)
            VALUES ('oc_x', 'cp_cap1_savor', 'app_x', 'active_min_spend_window', 'active', '2026-01-02', 'personal')
            """
        )
        self.conn.execute(
            "INSERT INTO annual_fee_events (id, open_card_id, fee_posted_on, amount_cents, review_due_on) VALUES ('afe_x', 'oc_x', '2027-01-02', 9500, '2027-02-01')"
        )
        self.conn.execute(
            "UPDATE open_cards SET lifecycle_stage='annual_fee_review', status='active' WHERE id='oc_x'"
        )
        self.conn.execute(
            "UPDATE annual_fee_events SET decision='downgrade', decision_date='2027-01-10' WHERE id='afe_x'"
        )
        self.conn.execute(
            "UPDATE open_cards SET lifecycle_stage='downgraded', status='active' WHERE id='oc_x'"
        )
        self.conn.execute(
            "UPDATE open_cards SET lifecycle_stage='closed', status='closed', close_date='2027-03-01' WHERE id='oc_x'"
        )
        self.conn.commit()
        row = self.conn.execute("SELECT lifecycle_stage, status, close_date FROM open_cards WHERE id='oc_x'").fetchone()
        self.assertEqual(dict(row), {'lifecycle_stage': 'closed', 'status': 'closed', 'close_date': '2027-03-01'})


if __name__ == "__main__":
    unittest.main()
