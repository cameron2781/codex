from __future__ import annotations

from pathlib import Path
import sqlite3

from db import apply_migrations, get_connection

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "churning.sqlite3"


def seed(conn: sqlite3.Connection) -> None:
    card_products = [
        ("card_chase_freedom_unlimited", "Chase", "Freedom Unlimited", "Ultimate Rewards", 0, 20000, 50000, 90, 1.0, "Conservative cash-out baseline"),
        ("card_amex_bce", "Amex", "Blue Cash Everyday", "Cash Back", 0, 20000, 200000, 180, 1.0, "Cash-back simplicity"),
        ("card_citi_custom_cash", "Citi", "Custom Cash", "ThankYou", 0, 20000, 150000, 180, 1.0, "Category cap card"),
        ("card_capone_savor", "Capital One", "Savor", "Cash Back", 9500, 30000, 300000, 90, 1.0, "Fee-bearing example"),
    ]
    conn.executemany(
        """
        INSERT OR REPLACE INTO card_products
        (id, issuer, name, family, annual_fee_cents, bonus_points, min_spend_cents, window_days, valuation_cpp, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        card_products,
    )

    snapshots = [
        ("rule_chase_2026_03_11", "Chase", "2026-03-11", "5/24", "blocked_at_5", "https://thepointsguy.com", "Conservative working threshold"),
        ("rule_amex_2026_03_11", "Amex", "2026-03-11", "once_per_lifetime", "warning_if_prior_bonus", "https://www.americanexpress.com", "General offer-language baseline"),
        ("rule_citi_2026_03_11", "Citi", "2026-03-11", "thankyou_cooldown", "48_months", "https://www.citi.com", "Conservative family cooldown"),
        ("rule_capone_2026_03_11", "Capital One", "2026-03-11", "velocity", "6m_spacing_1y_limit", "https://www.capitalone.com", "Conservative velocity spacing"),
    ]
    conn.executemany(
        """
        INSERT OR REPLACE INTO issuer_rule_snapshots
        (id, issuer, snapshot_date, rule_name, rule_value, source_url, source_note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        snapshots,
    )

    conn.execute(
        """
        INSERT OR REPLACE INTO applications
        (id, card_product_id, applied_on, status, decision_on, approved_credit_limit_cents, notes)
        VALUES ('app_1', 'card_chase_freedom_unlimited', '2025-10-01', 'approved', '2025-10-03', 1200000, 'Backfilled history')
        """
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO open_cards
        (id, card_product_id, opened_on, status, pay_in_full_confirmed_on, autopay_enabled, origin_application_id)
        VALUES ('open_1', 'card_chase_freedom_unlimited', '2025-10-05', 'active_min_spend', '2026-03-01', 1, 'app_1')
        """
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO signup_bonus_windows
        (id, open_card_id, starts_on, ends_on, min_spend_cents, target_bonus_points, status)
        VALUES ('bonus_1', 'open_1', '2025-10-05', '2026-01-03', 50000, 20000, 'completed')
        """
    )
    conn.executemany(
        """
        INSERT OR REPLACE INTO spend_entries
        (id, open_card_id, spent_on, amount_cents, memo)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("spend_1", "open_1", "2025-10-20", 30000, "Groceries and utilities"),
            ("spend_2", "open_1", "2025-11-09", 25000, "Insurance prepay"),
        ],
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO reward_ledger_entries
        (id, open_card_id, entry_type, posted_on, gross_value_cents, annual_fee_cents, net_value_cents, notes)
        VALUES ('ledger_1', 'open_1', 'signup_bonus', '2026-01-20', 20000, 0, 20000, 'Cash-equivalent bonus value')
        """
    )
    conn.execute(
        """
        INSERT OR REPLACE INTO annual_fee_events
        (id, open_card_id, fee_posted_on, fee_cents, due_review_on, resolved_on, resolution)
        VALUES ('fee_1', 'open_1', '2026-10-05', 0, '2026-11-04', NULL, NULL)
        """
    )
    conn.commit()


if __name__ == "__main__":
    with get_connection(DB_PATH) as connection:
        apply_migrations(connection)
        seed(connection)
