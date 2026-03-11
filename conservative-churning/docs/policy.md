# Conservative Churning Policy v1

_Last updated: 2026-03-11_

## Non-negotiable defaults

1. Pay statement balances in full every month.
2. No manufactured spending.
3. No buying groups or resale loops.
4. No 0% APR float strategy.
5. No business cards in v1.
6. Value rewards in cash-equivalent dollars only.

## Valuation defaults

- Cashback: face value.
- Transferable points: assign conservative cash-equivalent cents-per-point (cpp), default **1.0 cpp** unless documented cash-out route supports higher certainty.
- Airline/hotel points: treat at **0.8 cpp** unless directly cash-redeemable and historically used by this user.
- Net value = gross bonus value - annual fees paid.

## Application discipline

- Prefer one active minimum-spend window at a time.
- Enforce cooldown after each approval (default 90 days unless stricter issuer rule applies).
- Block opportunities if any “pay in full confirmed” task is overdue.

## Rule evaluation output

Each issuer decision returns:

- `eligible`, `warning`, or `blocked`
- concise reason
- `snapshot_date` from rule source record

## Weekly review ritual (30-day pilot)

Every week:

1. Enter spend activity.
2. Confirm all statements paid in full.
3. Review due-soon spend and annual-fee events.
4. Review rule-based opportunities.
5. Defer schema changes unless repeated friction appears.
