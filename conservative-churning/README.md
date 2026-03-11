# Conservative Churning System v1 (Local)

Single-user local Flask + SQLite tracker for conservative sign-up-bonus operations.

## Run locally

```bash
cd conservative-churning
python -m venv .venv
source .venv/bin/activate
pip install flask
python app.py
```

Then open:
- `/dashboard`
- `/opportunities`
- `/cards`
- `/cards/<id>`
- `/rules`

## Data model
Core tables map directly to:
- `CardProduct`
- `Application`
- `OpenCard`
- `SignupBonusWindow`
- `SpendEntry`
- `AnnualFeeEvent`
- `IssuerRuleSnapshot`
- `Alert`
- `RewardLedgerEntry`

Schema is managed by manual SQL migrations in `migrations/`.

## Pilot workflow
Use `research/policy.md` for weekly review discipline during the first 30-day pilot.
