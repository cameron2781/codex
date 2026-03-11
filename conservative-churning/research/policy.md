# Conservative Churning Policy v1

Date: 2026-03-11

## Non-negotiable defaults
- Pay statement balances in full every month.
- No manufactured spending.
- No buying groups/reselling loops.
- No 0% APR float strategy.
- No business cards in v1.
- Use cash-equivalent valuations only.

## Operating guardrails
- Only apply when issuer rule status is `eligible`; `warning` requires manual review.
- Maintain an in-app pay-in-full confirmation check weekly.
- Keep application cadence conservative (default: one personal card every ~90 days).
- Prefer no-annual-fee cards unless projected net bonus value remains strongly positive after fees.

## Lifecycle states
candidate -> applied -> approved -> active minimum-spend window -> bonus earned -> annual-fee review -> downgraded or closed

## Rule-engine output contract
Each issuer evaluation returns:
- `eligible`, `warning`, or `blocked`
- short reason
- rule snapshot date

## Weekly 30-day pilot ritual
1. Enter all posted spend entries.
2. Confirm balances paid in full.
3. Review spend-deadline and annual-fee alerts.
4. Check opportunities queue and issuer rule status.
5. Record any schema pain points for post-pilot refinement.
