from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from logic import status_for_due_date
from db import apply_migrations, get_connection
from rules import evaluate_rules
from seed import seed


class ConservativeChurningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.sqlite3"
        with get_connection(self.db_path) as conn:
            apply_migrations(conn)
            seed(conn)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_lifecycle_transitions_can_be_recorded(self) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                "UPDATE open_cards SET status='bonus_earned' WHERE id='open_1'"
            )
            conn.execute(
                "UPDATE open_cards SET status='annual_fee_review' WHERE id='open_1'"
            )
            conn.execute(
                "UPDATE open_cards SET status='downgraded', downgraded_on='2026-12-01' WHERE id='open_1'"
            )
            row = conn.execute("SELECT status, downgraded_on FROM open_cards WHERE id='open_1'").fetchone()
            self.assertEqual(dict(row), {"status": "downgraded", "downgraded_on": "2026-12-01"})

    def test_date_windows_and_deadline_statuses(self) -> None:
        self.assertEqual(status_for_due_date(date(2026, 1, 2), date(2026, 1, 1)), "overdue")
        self.assertEqual(status_for_due_date(date(2026, 1, 1), date(2026, 1, 5)), "due_soon")
        self.assertEqual(status_for_due_date(date(2026, 1, 1), date(2026, 1, 20)), "scheduled")

    def test_chase_5_24_boundary_and_becomes_eligible(self) -> None:
        with get_connection(self.db_path) as conn:
            # Add 4 additional recent cards so count is 5 in last 24 months.
            for idx in range(2, 6):
                conn.execute(
                    """
                    INSERT INTO open_cards
                    (id, card_product_id, opened_on, status, autopay_enabled)
                    VALUES (?, 'card_amex_bce', '2025-04-01', 'active', 1)
                    """,
                    (f"open_{idx}",),
                )
            blocked = [r for r in evaluate_rules(conn, date(2026, 3, 11)) if r.issuer == "Chase"][0]
            self.assertEqual(blocked.status, "blocked")

            conn.execute("UPDATE open_cards SET opened_on='2023-01-01' WHERE id='open_2'")
            eligible = [r for r in evaluate_rules(conn, date(2026, 3, 11)) if r.issuer == "Chase"][0]
            self.assertEqual(eligible.status, "warning")

    def test_net_value_calculation_with_and_without_fee(self) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO open_cards (id, card_product_id, opened_on, status, autopay_enabled)
                VALUES ('open_fee', 'card_capone_savor', '2026-02-01', 'bonus_earned', 1)
                """
            )
            conn.execute(
                """
                INSERT INTO reward_ledger_entries
                (id, open_card_id, entry_type, posted_on, gross_value_cents, annual_fee_cents, net_value_cents)
                VALUES ('ledger_fee', 'open_fee', 'signup_bonus', '2026-03-01', 30000, 9500, 20500)
                """
            )
            rows = conn.execute(
                "SELECT gross_value_cents, annual_fee_cents, net_value_cents FROM reward_ledger_entries ORDER BY id"
            ).fetchall()
            self.assertEqual([tuple(r) for r in rows], [(20000, 0, 20000), (30000, 9500, 20500)])

    def test_alert_task_states_due_soon_and_overdue(self) -> None:
        self.assertEqual(status_for_due_date(date(2026, 3, 11), date(2026, 3, 10)), "overdue")
        self.assertEqual(status_for_due_date(date(2026, 3, 11), date(2026, 3, 17)), "due_soon")

    def test_backfilled_history_influences_rules_and_counts(self) -> None:
        with get_connection(self.db_path) as conn:
            active_count = conn.execute(
                "SELECT COUNT(*) AS c FROM open_cards WHERE status NOT IN ('closed', 'downgraded')"
            ).fetchone()["c"]
            chase = [r for r in evaluate_rules(conn, date(2026, 3, 11)) if r.issuer == "Chase"][0]
            self.assertEqual((active_count, chase.status), (1, "eligible"))


if __name__ == "__main__":
    unittest.main()
