PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS card_product (
    id TEXT PRIMARY KEY,
    issuer TEXT NOT NULL,
    name TEXT NOT NULL,
    network TEXT NOT NULL,
    annual_fee_cents INTEGER NOT NULL,
    bonus_amount INTEGER NOT NULL,
    bonus_currency TEXT NOT NULL,
    conservative_cash_value_cents INTEGER NOT NULL,
    min_spend_cents INTEGER NOT NULL,
    min_spend_days INTEGER NOT NULL,
    notes TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS issuer_rule_snapshot (
    id TEXT PRIMARY KEY,
    issuer TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    rule_logic TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_title TEXT NOT NULL,
    source_date TEXT NOT NULL,
    captured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS application (
    id TEXT PRIMARY KEY,
    card_product_id TEXT NOT NULL REFERENCES card_product(id),
    status TEXT NOT NULL,
    applied_on TEXT NOT NULL,
    approved_on TEXT,
    declined_on TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS open_card (
    id TEXT PRIMARY KEY,
    card_product_id TEXT NOT NULL REFERENCES card_product(id),
    application_id TEXT REFERENCES application(id),
    lifecycle_status TEXT NOT NULL,
    opened_on TEXT NOT NULL,
    closed_on TEXT,
    downgrade_product_name TEXT,
    autopay_enabled INTEGER NOT NULL DEFAULT 0,
    pay_in_full_confirmed_on TEXT,
    statement_balance_cents INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signup_bonus_window (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL REFERENCES open_card(id),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    required_spend_cents INTEGER NOT NULL,
    earned_on TEXT,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS spend_entry (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL REFERENCES open_card(id),
    posted_on TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    category TEXT NOT NULL,
    memo TEXT
);

CREATE TABLE IF NOT EXISTS annual_fee_event (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL REFERENCES open_card(id),
    fee_posted_on TEXT NOT NULL,
    fee_cents INTEGER NOT NULL,
    anniversary_date TEXT NOT NULL,
    review_due_on TEXT NOT NULL,
    action_status TEXT NOT NULL,
    action_taken_on TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS alert (
    id TEXT PRIMARY KEY,
    open_card_id TEXT REFERENCES open_card(id),
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    due_on TEXT,
    state TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_on TEXT
);

CREATE TABLE IF NOT EXISTS reward_ledger_entry (
    id TEXT PRIMARY KEY,
    open_card_id TEXT REFERENCES open_card(id),
    entry_date TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    gross_value_cents INTEGER NOT NULL,
    annual_fee_cents INTEGER NOT NULL,
    net_value_cents INTEGER NOT NULL,
    notes TEXT
);
