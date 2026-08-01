# BCLX-R Q→R preregistration

Frozen before reading the full M→Q result.

## Eligibility

Q→R is executed only if the strict M→Q test passes every preregistered gate.

## State reconstruction

For each strict atomic candidate:

- Stablecoin debt outstanding = cumulative candidate stable Borrow minus same-debt Repay minus debt covered by LiquidationCall.
- Candidate collateral inventory outstanding = atomic non-stable Supply minus Withdraw minus collateral liquidated.
- The account is eligible only while both quantities remain strictly positive.

All event updates are processed in block/log order and are point-in-time.

## Trigger

For an eligible account-asset state, trigger at the first UTC daily close where the mapped USDT perpetual has a seven-calendar-day close-to-close return less than or equal to -10.0%.

No alternate drawdown threshold, lookback, or trigger family will be searched.

## Execution

- Enter at the next UTC daily open.
- Short the candidate asset USDT perpetual.
- Long BTCUSDT in the prior-90-calendar-day beta amount, estimated only from information available before entry.
- Exit at the earlier of:
  1. seven calendar days after entry; or
  2. the first observed same-debt Repay or LiquidationCall after entry.
- Same asset and UTC trigger date are one event cluster.
- Multiple accounts in the same cluster change only the cluster score, not the event count.

## Score and portfolio

Cluster score is predicted remaining deleveraging notional divided by prior-30-day median quote volume. Account contribution is capped so no account exceeds 25% of a cluster score. Position sizes are proportional to cross-sectional score, with equal gross long and short beta-adjusted books.

## Costs

- Double historical taker fee assumption on entry and exit.
- Historical funding where available; otherwise an adverse reserve of 5 bp per leg per day.
- Next-open execution and daily high/low stress equity for drawdown.

## Time contract

- 2022–2023: development only.
- 2024: one-time selection confirmation.
- 2025: final frozen verdict.

## Pass gates

- Continuous-account three-year terminal factor at least 1331.
- Intraperiod stress MDD at most 40%.
- Sharpe at least 1.2.
- At least 60 independent asset-date clusters per year.
- Every calendar year wealth factor at least 3.
- Best year no more than 50% of positive log growth.
- Delete top five clusters: three-year terminal factor at least 512.
- Delete top ten clusters: terminal factor greater than 1.
- Doubled-cost 5% block-bootstrap terminal factor greater than 1.

Any failure closes this expression. Any later modification resets the validation clock.
