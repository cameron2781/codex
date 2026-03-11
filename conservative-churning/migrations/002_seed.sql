INSERT INTO card_products (id, issuer, name, network, annual_fee_cents, bonus_currency, bonus_amount, cash_value_estimate_cents, spend_requirement_cents, spend_window_days, notes, is_seeded) VALUES
('cp_chase_flex', 'Chase', 'Freedom Flex', 'Mastercard', 0, 'UR', 20000, 20000, 50000, 90, 'Cash-equivalent at 1 cpp.', 1),
('cp_citi_custom', 'Citi', 'Custom Cash', 'Mastercard', 0, 'TY', 20000, 20000, 150000, 180, 'Cash-equivalent at 1 cpp.', 1),
('cp_cap1_savor', 'Capital One', 'Savor', 'Mastercard', 0, 'cash', 20000, 20000, 50000, 90, 'Direct cash bonus.', 1);

INSERT INTO applications (id, card_product_id, applied_on, status, decision_on) VALUES
('app_001', 'cp_chase_flex', '2024-07-01', 'approved', '2024-07-01'),
('app_002', 'cp_citi_custom', '2023-10-10', 'approved', '2023-10-11');

INSERT INTO open_cards (id, card_product_id, application_id, lifecycle_stage, status, open_date, card_type, current_credit_limit_cents, pay_in_full_confirmed_on) VALUES
('oc_001', 'cp_chase_flex', 'app_001', 'active_min_spend_window', 'active', '2024-07-01', 'personal', 500000, '2025-01-05'),
('oc_002', 'cp_citi_custom', 'app_002', 'bonus_earned', 'bonus_earned', '2023-10-11', 'personal', 700000, '2025-01-05');

INSERT INTO signup_bonus_windows (id, open_card_id, start_date, deadline_date, required_spend_cents, status, bonus_awarded_on) VALUES
('sbw_001', 'oc_001', '2024-07-01', '2024-09-29', 50000, 'completed', '2024-10-15'),
('sbw_002', 'oc_002', '2023-10-11', '2024-04-08', 150000, 'completed', '2024-04-20');

INSERT INTO spend_entries (id, open_card_id, txn_date, amount_cents, category, memo) VALUES
('se_001', 'oc_001', '2024-07-20', 26000, 'groceries', 'normal spend'),
('se_002', 'oc_001', '2024-08-04', 29000, 'utilities', 'normal spend'),
('se_003', 'oc_002', '2023-12-05', 90000, 'insurance', 'normal spend'),
('se_004', 'oc_002', '2024-01-12', 70000, 'travel', 'normal spend');

INSERT INTO annual_fee_events (id, open_card_id, fee_posted_on, amount_cents, review_due_on, decision, decision_date, notes) VALUES
('afe_001', 'oc_002', '2024-10-12', 0, '2024-11-01', 'keep', '2024-10-20', 'No annual fee');

INSERT INTO issuer_rule_snapshots (id, issuer, snapshot_date, source_url, summary, content, is_active) VALUES
('irs_chase_2025q1', 'Chase', '2025-01-15', 'https://thepointsguy.com/credit-cards/chase-5-24-rule/', '5/24 summarized conservatively.', 'Chase generally declines if >=5 personal cards opened in 24 months.', 1),
('irs_citi_2025q1', 'Citi', '2025-01-15', 'https://www.doctorofcredit.com/guide-to-citi-application-rules/', '8/65 and bonus family rules, manual verification required.', 'Conservative queueing with cooldown buffers for repeat applications.', 1),
('irs_cap1_2025q1', 'Capital One', '2025-01-15', 'https://www.nerdwallet.com/article/credit-cards/credit-card-churning', 'General anti-churning posture and conservative pacing.', 'Treat Capital One approvals as less predictable; throttle applications.', 1);

INSERT INTO reward_ledger_entries (id, open_card_id, entry_date, entry_type, gross_value_cents, annual_fee_cents, net_value_cents, notes) VALUES
('rle_001', 'oc_001', '2024-10-15', 'signup_bonus', 20000, 0, 20000, 'Freedom Flex bonus posted'),
('rle_002', 'oc_002', '2024-04-20', 'signup_bonus', 20000, 0, 20000, 'Custom Cash bonus posted');

INSERT INTO card_timeline_events (id, open_card_id, event_date, event_type, details) VALUES
('cte_001', 'oc_001', '2024-07-01', 'approved', 'Application app_001 approved.'),
('cte_002', 'oc_001', '2024-10-15', 'bonus_earned', 'Signup bonus confirmed.'),
('cte_003', 'oc_002', '2023-10-11', 'approved', 'Application app_002 approved.'),
('cte_004', 'oc_002', '2024-04-20', 'bonus_earned', 'Signup bonus confirmed.');
