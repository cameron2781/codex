CREATE TABLE card_products (
  id TEXT PRIMARY KEY,
  issuer TEXT NOT NULL,
  name TEXT NOT NULL,
  network TEXT NOT NULL,
  annual_fee_cents INTEGER NOT NULL,
  bonus_currency TEXT NOT NULL,
  bonus_amount INTEGER NOT NULL,
  cash_value_estimate_cents INTEGER NOT NULL,
  spend_requirement_cents INTEGER NOT NULL,
  spend_window_days INTEGER NOT NULL,
  notes TEXT,
  is_seeded INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE applications (
  id TEXT PRIMARY KEY,
  card_product_id TEXT NOT NULL REFERENCES card_products(id),
  applied_on TEXT NOT NULL,
  status TEXT NOT NULL,
  decision_on TEXT,
  denied_reason TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE open_cards (
  id TEXT PRIMARY KEY,
  card_product_id TEXT NOT NULL REFERENCES card_products(id),
  application_id TEXT REFERENCES applications(id),
  lifecycle_stage TEXT NOT NULL,
  status TEXT NOT NULL,
  open_date TEXT NOT NULL,
  close_date TEXT,
  card_type TEXT NOT NULL DEFAULT 'personal',
  current_credit_limit_cents INTEGER NOT NULL DEFAULT 0,
  autopay_enabled INTEGER NOT NULL DEFAULT 1,
  pay_in_full_confirmed_on TEXT
);

CREATE TABLE signup_bonus_windows (
  id TEXT PRIMARY KEY,
  open_card_id TEXT NOT NULL REFERENCES open_cards(id),
  start_date TEXT NOT NULL,
  deadline_date TEXT NOT NULL,
  required_spend_cents INTEGER NOT NULL,
  status TEXT NOT NULL,
  bonus_awarded_on TEXT
);

CREATE TABLE spend_entries (
  id TEXT PRIMARY KEY,
  open_card_id TEXT NOT NULL REFERENCES open_cards(id),
  txn_date TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  category TEXT NOT NULL,
  memo TEXT
);

CREATE TABLE annual_fee_events (
  id TEXT PRIMARY KEY,
  open_card_id TEXT NOT NULL REFERENCES open_cards(id),
  fee_posted_on TEXT NOT NULL,
  amount_cents INTEGER NOT NULL,
  review_due_on TEXT NOT NULL,
  decision TEXT,
  decision_date TEXT,
  notes TEXT
);

CREATE TABLE issuer_rule_snapshots (
  id TEXT PRIMARY KEY,
  issuer TEXT NOT NULL,
  snapshot_date TEXT NOT NULL,
  source_url TEXT NOT NULL,
  summary TEXT NOT NULL,
  content TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE alerts (
  id TEXT PRIMARY KEY,
  alert_type TEXT NOT NULL,
  status TEXT NOT NULL,
  severity TEXT NOT NULL,
  due_date TEXT,
  message TEXT NOT NULL,
  generated_by_engine INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE reward_ledger_entries (
  id TEXT PRIMARY KEY,
  open_card_id TEXT REFERENCES open_cards(id),
  entry_date TEXT NOT NULL,
  entry_type TEXT NOT NULL,
  gross_value_cents INTEGER NOT NULL,
  annual_fee_cents INTEGER NOT NULL DEFAULT 0,
  net_value_cents INTEGER NOT NULL,
  notes TEXT
);

CREATE TABLE card_timeline_events (
  id TEXT PRIMARY KEY,
  open_card_id TEXT NOT NULL REFERENCES open_cards(id),
  event_date TEXT NOT NULL,
  event_type TEXT NOT NULL,
  details TEXT NOT NULL
);
