PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS card_products (
    id TEXT PRIMARY KEY,
    issuer TEXT NOT NULL,
    name TEXT NOT NULL,
    annual_fee_cents INTEGER NOT NULL,
    bonus_value_cents INTEGER NOT NULL,
    spend_requirement_cents INTEGER NOT NULL,
    spend_window_days INTEGER NOT NULL,
    family TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    card_product_id TEXT NOT NULL,
    applied_on TEXT NOT NULL,
    status TEXT NOT NULL,
    decision_on TEXT,
    notes TEXT,
    FOREIGN KEY(card_product_id) REFERENCES card_products(id)
);

CREATE TABLE IF NOT EXISTS open_cards (
    id TEXT PRIMARY KEY,
    card_product_id TEXT NOT NULL,
    opened_on TEXT NOT NULL,
    closed_on TEXT,
    status TEXT NOT NULL,
    current_credit_limit_cents INTEGER,
    pay_in_full_confirmed_on TEXT,
    source_application_id TEXT,
    FOREIGN KEY(card_product_id) REFERENCES card_products(id),
    FOREIGN KEY(source_application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS signup_bonus_windows (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL,
    required_spend_cents INTEGER NOT NULL,
    deadline_on TEXT NOT NULL,
    bonus_posted_on TEXT,
    status TEXT NOT NULL,
    FOREIGN KEY(open_card_id) REFERENCES open_cards(id)
);

CREATE TABLE IF NOT EXISTS spend_entries (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL,
    spent_on TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    note TEXT,
    FOREIGN KEY(open_card_id) REFERENCES open_cards(id)
);

CREATE TABLE IF NOT EXISTS annual_fee_events (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL,
    expected_on TEXT NOT NULL,
    posted_on TEXT,
    fee_cents INTEGER NOT NULL,
    review_status TEXT NOT NULL,
    review_notes TEXT,
    FOREIGN KEY(open_card_id) REFERENCES open_cards(id)
);

CREATE TABLE IF NOT EXISTS issuer_rule_snapshots (
    id TEXT PRIMARY KEY,
    issuer TEXT NOT NULL,
    rule_key TEXT NOT NULL,
    summary TEXT NOT NULL,
    cooldown_days INTEGER,
    lookback_months INTEGER,
    threshold_count INTEGER,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    captured_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    open_card_id TEXT,
    alert_type TEXT NOT NULL,
    due_on TEXT,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    created_on TEXT NOT NULL,
    completed_on TEXT,
    FOREIGN KEY(open_card_id) REFERENCES open_cards(id)
);

CREATE TABLE IF NOT EXISTS reward_ledger_entries (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL,
    entry_on TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    gross_value_cents INTEGER NOT NULL,
    annual_fee_cents INTEGER NOT NULL,
    net_value_cents INTEGER NOT NULL,
    note TEXT,
    FOREIGN KEY(open_card_id) REFERENCES open_cards(id)
);
