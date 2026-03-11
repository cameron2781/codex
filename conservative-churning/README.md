# Conservative Churning System v1

Local, single-user Flask + SQLite tracker for conservative credit-card churning.

## Scope

- Research-first workflow with dated issuer rule snapshots.
- Conservative policy defaults (no manufactured spend, no business cards, pay in full monthly, cash-equivalent valuations).
- Deterministic lifecycle and in-app task/alert generation.

## Quick start

```bash
cd conservative-churning
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Then open <http://127.0.0.1:5000/dashboard>.

## Data model

Core entities are implemented directly as SQLite tables via migration SQL files:

- `card_products`
- `applications`
- `open_cards`
- `signup_bonus_windows`
- `spend_entries`
- `annual_fee_events`
- `issuer_rule_snapshots`
- `alerts`
- `reward_ledger_entries`

## Routes

- `/dashboard`
- `/opportunities`
- `/cards`
- `/cards/<id>`
- `/rules`

## Testing

```bash
python -m pytest
```
