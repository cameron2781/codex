INSERT INTO card_product (id, issuer, name, network, annual_fee_cents, bonus_amount, bonus_currency, conservative_cash_value_cents, min_spend_cents, min_spend_days, notes, created_at)
VALUES
('card_chase_flex', 'Chase', 'Freedom Flex', 'Mastercard', 0, 20000, 'UR', 20000, 50000, 90, 'Conservative cash-out at 1 cent per point.', date('now')),
('card_chase_sapphire_preferred', 'Chase', 'Sapphire Preferred', 'Visa', 9500, 60000, 'UR', 60000, 400000, 90, 'Cash equivalent valuation only for v1.', date('now')),
('card_citi_double_cash', 'Citi', 'Double Cash', 'Mastercard', 0, 20000, 'TY', 20000, 150000, 180, 'Simple cash-back setup for low-maintenance rewards.', date('now')),
('card_capitalone_quicksilver', 'Capital One', 'Quicksilver', 'Visa', 0, 20000, 'cash', 20000, 50000, 90, 'Flat cash-back bonus with no annual fee.', date('now'))
ON CONFLICT(id) DO NOTHING;

INSERT INTO issuer_rule_snapshot (id, issuer, rule_name, rule_logic, source_url, source_title, source_date, captured_at)
VALUES
('rule_chase_5_24_2025_01', 'Chase', '5/24', 'blocked when personal cards opened in trailing 24 months >= 5', 'https://www.doctorofcredit.com/chase-524-rule-explained-detail-need-know/', 'Doctor of Credit - Chase 5/24', '2025-01-15', date('now')),
('rule_amex_once_lifetime_2025_01', 'Amex', 'Welcome bonus once per lifetime', 'warning when card was previously held; assume likely ineligible for new bonus', 'https://www.americanexpress.com/us/credit-cards/card-application-terms/', 'American Express Card Application Terms', '2025-01-15', date('now')),
('rule_citi_family_48m_2025_01', 'Citi', '48 month family restriction', 'blocked when same-family bonus was received in trailing 48 months', 'https://www.citi.com/credit-cards/compare/view-all-credit-cards', 'Citi credit card terms pages', '2025-01-15', date('now')),
('rule_cap1_velocity_2025_01', 'Capital One', 'Capital One velocity', 'warning when more than one approval in trailing 6 months', 'https://thepointsguy.com/credit-cards/credit-card-application-rules/', 'The Points Guy - issuer application rules', '2025-01-15', date('now'))
ON CONFLICT(id) DO NOTHING;

INSERT INTO application (id, card_product_id, status, applied_on, approved_on, notes)
VALUES
('app_2024_csp', 'card_chase_sapphire_preferred', 'approved', '2024-02-02', '2024-02-03', 'Backfilled baseline history.'),
('app_2024_flex', 'card_chase_flex', 'approved', '2024-08-10', '2024-08-11', 'Backfilled baseline history.')
ON CONFLICT(id) DO NOTHING;

INSERT INTO open_card (id, card_product_id, application_id, lifecycle_status, opened_on, autopay_enabled, pay_in_full_confirmed_on, statement_balance_cents, created_at)
VALUES
('open_2024_csp', 'card_chase_sapphire_preferred', 'app_2024_csp', 'bonus_earned', '2024-02-05', 1, '2025-01-31', 0, date('now')),
('open_2024_flex', 'card_chase_flex', 'app_2024_flex', 'active_min_spend', '2024-08-15', 1, '2025-01-31', 0, date('now'))
ON CONFLICT(id) DO NOTHING;

INSERT INTO signup_bonus_window (id, open_card_id, start_date, end_date, required_spend_cents, earned_on, status)
VALUES
('sbw_2024_csp', 'open_2024_csp', '2024-02-05', '2024-05-05', 400000, '2024-04-18', 'earned'),
('sbw_2024_flex', 'open_2024_flex', '2024-08-15', '2024-11-13', 50000, NULL, 'expired')
ON CONFLICT(id) DO NOTHING;

INSERT INTO spend_entry (id, open_card_id, posted_on, amount_cents, category, memo)
VALUES
('spend_1', 'open_2024_csp', '2024-03-10', 220000, 'groceries', 'normal household spend'),
('spend_2', 'open_2024_csp', '2024-04-02', 190000, 'utilities', 'bonus threshold completion'),
('spend_3', 'open_2024_flex', '2024-09-12', 25000, 'groceries', 'partial spend')
ON CONFLICT(id) DO NOTHING;

INSERT INTO annual_fee_event (id, open_card_id, fee_posted_on, fee_cents, anniversary_date, review_due_on, action_status, notes)
VALUES
('afe_2025_csp', 'open_2024_csp', '2025-02-10', 9500, '2025-02-05', '2025-03-01', 'pending', 'Review retention offer or downgrade.' )
ON CONFLICT(id) DO NOTHING;

INSERT INTO reward_ledger_entry (id, open_card_id, entry_date, entry_type, gross_value_cents, annual_fee_cents, net_value_cents, notes)
VALUES
('rle_2024_csp_bonus', 'open_2024_csp', '2024-04-22', 'signup_bonus', 60000, 9500, 50500, 'Conservative 1cpp valuation less first annual fee')
ON CONFLICT(id) DO NOTHING;
