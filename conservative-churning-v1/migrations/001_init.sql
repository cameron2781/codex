PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS card_products (
    id TEXT PRIMARY KEY,
    issuer TEXT NOT NULL,
    name TEXT NOT NULL,
    family TEXT NOT NULL,
    annual_fee_cents INTEGER NOT NULL,
    bonus_points INTEGER NOT NULL,
    min_spend_cents INTEGER NOT NULL,
    window_days INTEGER NOT NULL,
    valuation_cpp REAL NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    card_product_id TEXT NOT NULL,
    applied_on TEXT NOT NULL,
    status TEXT NOT NULL,
    decision_on TEXT,
    approved_credit_limit_cents INTEGER,
    notes TEXT,
    FOREIGN KEY(card_product_id) REFERENCES card_products(id)
);

CREATE TABLE IF NOT EXISTS open_cards (
    id TEXT PRIMARY KEY,
    card_product_id TEXT NOT NULL,
    opened_on TEXT NOT NULL,
    status TEXT NOT NULL,
    closed_on TEXT,
    downgraded_on TEXT,
    pay_in_full_confirmed_on TEXT,
    autopay_enabled INTEGER NOT NULL DEFAULT 1,
    origin_application_id TEXT,
    FOREIGN KEY(card_product_id) REFERENCES card_products(id),
    FOREIGN KEY(origin_application_id) REFERENCES applications(id)
);

CREATE TABLE IF NOT EXISTS signup_bonus_windows (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL,
    starts_on TEXT NOT NULL,
    ends_on TEXT NOT NULL,
    min_spend_cents INTEGER NOT NULL,
    target_bonus_points INTEGER NOT NULL,
    bonus_awarded_on TEXT,
    status TEXT NOT NULL,
    FOREIGN KEY(open_card_id) REFERENCES open_cards(id)
);

CREATE TABLE IF NOT EXISTS spend_entries (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL,
    spent_on TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    memo TEXT,
    FOREIGN KEY(open_card_id) REFERENCES open_cards(id)
);

CREATE TABLE IF NOT EXISTS annual_fee_events (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL,
    fee_posted_on TEXT NOT NULL,
    fee_cents INTEGER NOT NULL,
    due_review_on TEXT NOT NULL,
    waived INTEGER NOT NULL DEFAULT 0,
    resolved_on TEXT,
    resolution TEXT,
    FOREIGN KEY(open_card_id) REFERENCES open_cards(id)
);

CREATE TABLE IF NOT EXISTS issuer_rule_snapshots (
    id TEXT PRIMARY KEY,
    issuer TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    rule_value TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_note TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id TEXT PRIMARY KEY,
    alert_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    title TEXT NOT NULL,
    due_on TEXT NOT NULL,
    status TEXT NOT NULL,
    detail TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_on TEXT
);

CREATE TABLE IF NOT EXISTS reward_ledger_entries (
    id TEXT PRIMARY KEY,
    open_card_id TEXT NOT NULL,
    entry_type TEXT NOT NULL,
    posted_on TEXT NOT NULL,
    gross_value_cents INTEGER NOT NULL,
    annual_fee_cents INTEGER NOT NULL DEFAULT 0,
    net_value_cents INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY(open_card_id) REFERENCES open_cards(id)
);
