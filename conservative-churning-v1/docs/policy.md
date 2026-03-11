# Conservative Churning Policy (V1)

_Last updated: 2026-03-11_

## Mandatory defaults
1. Pay every statement in full every month.
2. No manufactured spending.
3. No buying groups.
4. No 0% APR float strategy.
5. No business cards in v1.
6. Cash-equivalent valuation only.

## Operational guardrails
- Application pacing: default no more than one personal card application every 90 days unless risk score is explicitly low.
- Stop condition: if utilization > 30% or any missed/late payment event, block new applications.
- Annual fee review: decision task generated 30 days before anniversary and again on fee post.

## Lifecycle states
`candidate -> applied -> approved -> active_min_spend -> bonus_earned -> annual_fee_review -> downgraded|closed`

## Decision priorities
1. Safety and score protection.
2. Predictable net cash-equivalent bonus value.
3. Low operational overhead.
4. Optional optimization only after all safety checks pass.

## Valuation defaults
- Use issuer-specific conservative cpp/cash rates from research snapshots.
- Dashboard must show gross bonus value and net value after fees.

## Rule result contract
Every issuer evaluation returns:
- `status`: `eligible | warning | blocked`
- `reason`: short plain-English explanation
- `snapshot_date`: date string

## Weekly ritual for 30-day pilot
1. Update spend entries for active bonus windows.
2. Confirm "pay in full" manually for all open cards.
3. Review dashboard alerts.
4. Review opportunities queue and rule statuses.
5. Log one retrospective note about friction or missing fields.
