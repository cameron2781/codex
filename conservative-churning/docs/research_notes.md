# Research Notes (Phase 1)

Date compiled: 2026-03-11.

## Sources and conservative interpretation

1. Chase 5/24 overview — The Points Guy.
   - URL: https://thepointsguy.com/credit-cards/chase-5-24-rule/
   - Notes: Use as a directional guardrail only. V1 treats 5/24 as hard blocked and 4/24 as warning.

2. Citi application rule guide — Doctor of Credit.
   - URL: https://www.doctorofcredit.com/guide-to-citi-application-rules/
   - Notes: Rule complexity varies by product family; V1 marks Citi as warning/manual review.

3. Churning risks and best practices — NerdWallet.
   - URL: https://www.nerdwallet.com/article/credit-cards/credit-card-churning
   - Notes: Supports conservative discipline: avoid overspending, protect credit profile, and track timing.

4. Credit score factors and utilization basics — CFPB.
   - URL: https://www.consumerfinance.gov/ask-cfpb/what-is-a-credit-score-en-315/
   - Notes: V1 includes a monthly pay-in-full confirmation alert and discourages utilization spikes.

5. Cardmember agreement and terms pages from issuers (product-specific, manual reading required).
   - Notes: Snapshot record should include source date and summary to keep rule assumptions auditable.

## Draft defaults for valuation

- Cash-equivalent point valuation default: **1.0 cent per point** unless issuer pays fixed cash statement credit.
- Gross reward value and net reward value are both stored in the ledger.
- Net value subtracts annual fee in the same ledger entry (or linked annual fee events).
