# Conservative Churning Research Notes (Phase 1)

_Last updated: 2026-03-11_

## Scope and framing
This research pass prioritizes issuer-published terms or reputable, frequently updated secondary summaries for conservative planning. The notes below should be periodically revalidated before major application decisions.

## Sources consulted
1. Chase credit card application rules and 5/24 discussion summaries (The Points Guy, NerdWallet) with clear publication/update dates.
2. American Express once-per-lifetime and pop-up language summaries (Amex offer terms, Frequent Miler).
3. Citi family and timing restrictions for ThankYou cards (Citi offer terms, Doctor of Credit summaries).
4. Capital One velocity and bureau pull behavior summaries (issuer language + reputable aggregator updates).
5. FICO educational guidance on payment history, utilization, and hard inquiry effects.
6. CFPB / issuer cardmember agreement references for annual fee posting and cancellation timelines.

## Dated issuer rule snapshots (to capture in app)
- **Chase (snapshot date: 2026-03-11)**
  - 5/24 policy widely reported: approvals are difficult if 5+ personal cards opened in past 24 months.
  - Common conservative interpretation: business cards may not add to count but can still be denied by internal policy; v1 excludes business cards entirely.
  - Practical default: treat `>=5` recent opens as blocked, 4/24 as warning.

- **Amex (snapshot date: 2026-03-11)**
  - Welcome offers are generally once per lifetime per product family, with potential targeted exceptions.
  - Pop-up denial can occur despite eligibility assumptions.
  - Conservative default: block re-application to same family if prior bonus recorded.

- **Citi (snapshot date: 2026-03-11)**
  - ThankYou-family cards often have 24/48 month language around bonus eligibility.
  - Conservative default for v1: 48-month cooldown for same rewards family unless updated terms prove shorter.

- **Capital One (snapshot date: 2026-03-11)**
  - Velocity can be sensitive; anecdotal approvals often improve with spacing.
  - Conservative default: minimum 6 months between applications and max 1 new CapOne card in 12 months.

## Annual fee behavior and downgrade/cancel timing
- Annual fees usually post at first anniversary and each subsequent year.
- Issuer policies often allow fee reversal within a short window (commonly ~30 days; confirm per issuer/card agreement).
- Conservative workflow: set review task 30 days before anniversary and status decision within 30 days of fee post.

## Credit-score and risk guardrails
- Never carry statement balances for rewards optimization.
- Keep utilization low (single-digit preferred, <30% hard ceiling).
- Space applications to reduce inquiry clustering.
- Manual monthly check: payment posted in full and autopay still active.

## Valuation defaults (cash-equivalent)
- Use **cash-out floor values** only, not transfer-partner aspirational redemptions.
- Example defaults for v1:
  - Chase UR: 1.0 cpp
  - Amex MR: 0.8 cpp
  - Citi TY: 1.0 cpp
  - Capital One Miles: 1.0 cpp
  - Cash back points: 1.0 cpp
- Store these defaults as editable policy metadata with source date.

## Out-of-scope tactics (explicit)
- Manufactured spending.
- Buying groups / reselling loops.
- 0% APR float or intentional revolving.
- Business cards.
- Transfer-optimization / award chart maximization.
