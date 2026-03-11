from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from app import create_app
from db import connect, run_migrations


class ConservativeChurningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.sqlite3"
        conn = connect(self.db_path)
        run_migrations(conn)
        conn.close()
        self.app = create_app(self.db_path)
        self.client = self.app.test_client()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _conn(self):
        return connect(self.db_path)

    def test_lifecycle_transitions_include_downgrade_and_closed(self) -> None:
        conn = self._conn()
        conn.execute(
            "UPDATE open_card SET lifecycle_status = 'annual_fee_review', downgrade_product_name = 'Freedom Unlimited' WHERE id = 'open_2024_csp'"
        )
        conn.execute(
            "UPDATE open_card SET lifecycle_status = 'closed', closed_on = '2026-01-10' WHERE id = 'open_2024_flex'"
        )
        conn.commit()
        statuses = [
            row["lifecycle_status"]
            for row in conn.execute("SELECT lifecycle_status FROM open_card ORDER BY id").fetchall()
        ]
        self.assertEqual(statuses, ["annual_fee_review", "closed"])
        conn.close()

    def test_date_windows_for_bonus_and_fees(self) -> None:
        conn = self._conn()
        end_date = conn.execute(
            "SELECT end_date FROM signup_bonus_window WHERE id = 'sbw_2024_csp'"
        ).fetchone()["end_date"]
        fee_due = conn.execute(
            "SELECT review_due_on FROM annual_fee_event WHERE id = 'afe_2025_csp'"
        ).fetchone()["review_due_on"]
        self.assertEqual(end_date, "2024-05-05")
        self.assertEqual(fee_due, "2025-03-01")
        conn.close()

    def test_chase_5_24_block_boundary_and_transition(self) -> None:
        conn = self._conn()
        today = date.today()
        for i in range(4):
            conn.execute(
                "INSERT INTO open_card(id, card_product_id, lifecycle_status, opened_on, statement_balance_cents, created_at) VALUES (?, 'card_citi_double_cash', 'active_min_spend', ?, 0, date('now'))",
                (f"open_extra_{i}", (today - timedelta(days=30 * i)).isoformat()),
            )
        conn.commit()
        page = self.client.get("/rules").get_data(as_text=True)
        self.assertIn("Chase — blocked", page)

        conn.execute("DELETE FROM open_card WHERE id = 'open_extra_3'")
        conn.commit()
        page_after = self.client.get("/rules").get_data(as_text=True)
        self.assertIn("Chase — eligible", page_after)
        conn.close()

    def test_net_value_calculation_fee_and_no_fee_cards(self) -> None:
        conn = self._conn()
        conn.execute(
            "INSERT INTO reward_ledger_entry(id, open_card_id, entry_date, entry_type, gross_value_cents, annual_fee_cents, net_value_cents, notes) VALUES ('rle_cash', 'open_2024_flex', '2024-10-01', 'signup_bonus', 20000, 0, 20000, 'no fee bonus')"
        )
        conn.commit()
        totals = conn.execute(
            "SELECT SUM(gross_value_cents) AS gross, SUM(net_value_cents) AS net FROM reward_ledger_entry"
        ).fetchone()
        self.assertEqual((totals["gross"], totals["net"]), (80000, 70500))
        conn.close()

    def test_alert_generation_overdue_due_soon_and_clear(self) -> None:
        conn = self._conn()
        conn.execute("UPDATE signup_bonus_window SET status = 'active', end_date = ? WHERE id = 'sbw_2024_flex'", ((date.today() - timedelta(days=2)).isoformat(),))
        conn.execute("UPDATE open_card SET statement_balance_cents = 12345, pay_in_full_confirmed_on = NULL WHERE id = 'open_2024_csp'")
        conn.commit()
        dashboard = self.client.get("/dashboard").get_data(as_text=True)
        self.assertIn("critical", dashboard)
        self.assertIn("confirm statement paid in full", dashboard)
        conn.close()

    def test_backfilled_history_keeps_counts_and_eligibility_visible(self) -> None:
        cards_page = self.client.get("/cards").get_data(as_text=True)
        rules_page = self.client.get("/rules").get_data(as_text=True)
        self.assertIn("Sapphire Preferred", cards_page)
        self.assertIn("Freedom Flex", cards_page)
        self.assertIn("Chase", rules_page)


if __name__ == "__main__":
    unittest.main()
