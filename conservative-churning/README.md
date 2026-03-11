# Conservative Churning System v1

Local Flask + SQLite tracker for conservative credit-card churning.

## Routes
- `/dashboard`
- `/opportunities`
- `/cards`
- `/cards/<id>`
- `/rules`

## Domain entities
Tables mirror the core model:
`card_products`, `applications`, `open_cards`, `signup_bonus_windows`, `spend_entries`, `annual_fee_events`, `issuer_rule_snapshots`, `alerts`, `reward_ledger_entries`.

## Run locally
```bash
cd conservative-churning
python3 -m venv .venv
source .venv/bin/activate
pip install flask
python app.py
```

## Rule engine output
Each issuer evaluation emits:
- `eligible`
- `warning`
- `blocked`

Along with a reason and snapshot date.

## Tests
```bash
cd conservative-churning
python -m unittest discover -s tests -p 'test_*.py'
```
