# Conservative Churning System v1

Local single-user Flask + SQLite tracker focused on conservative sign-up bonus operations.

## Features
- Research artifacts and policy defaults in `docs/`.
- Manual SQL migrations in `migrations/` with no ORM.
- Core domain tables:
  - `CardProduct`, `Application`, `OpenCard`, `SignupBonusWindow`, `SpendEntry`, `AnnualFeeEvent`, `IssuerRuleSnapshot`, `Alert`, `RewardLedgerEntry`
- Routes:
  - `/dashboard`
  - `/opportunities`
  - `/cards`
  - `/cards/<id>`
  - `/rules`
- Rule statuses per issuer: `eligible`, `warning`, `blocked` with reason and snapshot date.
- In-app alert generation for spend deadlines, annual fee reviews, and pay-in-full checks.

## Quick start
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask
python seed.py
python app.py
```
Then open `http://127.0.0.1:5000/dashboard`.

## 30-day pilot workflow
1. Weekly: add spend entries and verify min-spend trajectory.
2. Weekly: manually confirm pay-in-full for each open card.
3. Weekly: review `/opportunities` and `/rules` before any application.
4. Monthly: resolve annual fee review tasks.
5. Adjust schema only after repeated real usage friction.
