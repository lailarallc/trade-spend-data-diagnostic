# Defensibility Log

Every headline number in this diagnostic is computed from the bundled
SQLite database. Nothing is asserted from memory, and no external
benchmark appears anywhere in the deliverables — every figure can be
reproduced by running a query from `sql/` against
`cinderhaven-data/data/cinderhaven_product_master.db`, and the
workbook's totals are pinned by `validate_workbook.py` (59 checks).
This document walks each number: what it is, exactly how it is
derived, and the answer to the challenge it is most likely to draw.

One disclosure up front: Cinderhaven Provisions is a synthetic
demonstration dataset, not a client. The defensibility standard is
the one a real engagement would face — every figure below is
computed, windowed, and open to attack — but the dollars are
illustrative.

## The two analysis windows, and the week they disagree

**Revenue** is summed over the 52 most recent distinct scan weeks:
`week_ending` 2025-01-04 through 2025-12-27
(`sql/trade_rate/trailing_52_weeks.sql` establishes the window,
`total_revenue.sql` does the sum). **Deductions** are summed over the
trailing 365 days ending at the newest scan week: `deduction_date`
after 2024-12-27, through 2025-12-27.

The windows are constructed differently — 52 weekly periods versus
365 calendar days — and overlap by design rather than by identity.
The mismatch is worth about a week at the boundary. The validation
suite tolerates it explicitly rather than hiding it: dollar pins
carry a stated tolerance (0.5% on most totals, 2% on the waste sum).
A CFO who asks whether the numerator and denominator cover the same
year gets a yes with a one-week caveat, not a shrug.

## Revenue: $32,323,139.62

`SUM(dollars_sold)` over the trailing-52-week window
(`sql/trade_rate/total_revenue.sql`).

**The attack:** scan dollars are consumer takeaway, not invoiced
wholesale revenue. **The answer:** correct, and immaterial to the
finding. Scan data is the only weekly, retailer-comparable series in
the dataset, so it is the denominator for every rate in the
diagnostic. The 9.2% structural rate and the 10.3% all-in rate are
computed against the same base; the 1.1-point gap between them — the
finding — survives any consistent choice of denominator.

## Structural trade: $2,992,224 (9.2%), computed two ways

Structural trade is the negotiated rate card applied to channel
revenue: for each retailer, trailing-52-week scan revenue times the
channel-average trade rate from `sku_costs` — the mean across all 50
SKUs of that channel's `trade_spend_pct_*` column. The rate card is
negotiated at the channel level, so the channel average, not per-SKU
rates, is the right resolution; per-SKU application would add false
precision, not accuracy.

The mapping in full: Walmart (12.0%), Costco (10.0%), Whole Foods
(8.0%), and Sprouts (9.0%) use their dedicated rate columns; Kroger
and Regional Group use the regional average (7.0%).

**The known divergence:** the diagnostic computes this number twice.
The workbook (`workbook/queries.py`, feeding Tabs 1 and 4) uses the
mapping above and gets **$2,992,224 (9.2%)**. The pure-SQL variant
(`sql/trade_rate/structural_trade_amount.sql`) maps the regional natural grocer to the
regional rate instead of its dedicated column and gets **$2,914,207
(9.0%)**. The entire difference is the regional natural grocer: $3,900,857 of channel
revenue times two rate points is $78,017. The memo uses the workbook
figure because the regional natural grocer has a negotiated rate of its own in
`sku_costs`, and averaging a $3.9M channel into "regional" would
understate a known contract. Both figures are computed, both are
disclosed in the query headers, and neither is hand-entered anywhere.

**The residual attack:** `sku_costs` also carries a dedicated Kroger
column (10.0% average) that neither variant uses — the workbook's
channel map predates the column and keeps Kroger at the regional
rate. Adopting it would add roughly $200K and put structural trade
near 9.8%. **The answer:** the structural figure describes the
budgeted side of the ledger, and any of these mappings leaves the
finding intact, because the waste number does not depend on the rate
mapping at all — it is summed directly from deduction line items. A
different mapping would change the size of the known cost; it would
not move $343,281 by a dollar.

## Operational waste: $343,281 across 4,772 events (1.1%)

Every deduction in the trailing-365 window whose type is not
`promo_billback`, summed (`sql/deductions/waste_by_category.sql`).
Billbacks are excluded because they are planned promotional spend
funded through the deduction pipe; counting them as waste would mix
budgeted trade into the leak. They get their own section below.

| Category | Events | Amount | Share |
|----------|-------:|-------:|------:|
| Spoilage | 546 | $53,664 | 15.6% |
| Pricing errors | 547 | $53,224 | 15.5% |
| Damaged goods | 543 | $53,169 | 15.5% |
| Slotting | 532 | $51,879 | 15.1% |
| Pallet fines | 580 | $51,565 | 15.0% |
| Label fines | 532 | $48,861 | 14.2% |
| Short-ship | 1,406 | $28,053 | 8.2% |
| Late delivery | 86 | $2,865 | 0.8% |

Each category draws its own version of "that's just how the business
works." None survives contact with a shipping record:

- **Spoilage — "perishables spoil."** Some do. The disputable
  question is whether the product was in code at delivery and whether
  the retailer's DC held it past sell-by. Cross-referencing $53,664
  of claims against shelf-life and receiving dates is matching work,
  not a research project.
- **Pricing errors — "trivial discrepancies."** $53,224 is not
  trivial, and the signal is worse than the dollars: recurring price
  disputes mean the list the sales team negotiated and the one the
  invoicing system bills have diverged. Fix the master data and the
  category stops.
- **Damaged goods — "stuff breaks in transit."** Packed to spec and
  damaged anyway is a carrier claim. A recurring damage pattern is a
  packaging-design fix. Either way, not a silent write-off.
- **Pallet and label fines — "retailers nitpick."** The specs are
  published in vendor guides. $51,565 and $48,861 a year are the
  price of not having a pre-ship checklist, which costs less.
- **Short-ship — "warehouse shrink."** If the BOL says full and the
  receiving dock says short, someone between the dock doors owes the
  difference — and at $20 a claim, a machine should be the one
  asking (see below).

**The structural attack:** six categories landing within $4,803 of
one another looks engineered. It is — Cinderhaven is synthetic, and
the even spread is the scenario the dataset was built to pose: a
pipeline that leaks a little in every category because no step in it
verifies anything, rather than a villain category that one fix would
cure. The diagnostic's job is to detect and quantify that shape, and
the detection logic — classification, windowing, category totals —
is exactly what would run against real remittance data.

## Short-ship and late delivery: the two rows that break the pattern

Short-ship is high-frequency, low-dollar: 1,406 events — 29% of all
waste events — totaling $28,053, an average of $20 apiece. Late
delivery is 86 events and $2,865. The memo tells Cinderhaven to
automate the first and ignore the second.

**The attack:** "you are telling us to ignore deductions." **The
answer:** triage is not absorption. A $20 charge disputed by hand
costs more in payroll than it recovers; the recommendation is
automated matching against shipment records below a dollar
threshold, with batch dispute or documented write-off as the output.
Late delivery is 0.8% of the waste; attention spent there is
attention taken from the $109K of physical-handling claims that
actually move the number.

## Slotting and the addressable total: $291,402

Slotting ($51,879, 532 events) is counted in the $343,281 waste
figure but excluded from the addressable total: it is the negotiated
price of shelf placement, a contract-time question rather than a
remittance-time one. Addressable waste is $343,281 − $51,879 =
**$291,402**, and the memo's action list draws on that figure.

**The attack:** "if it's negotiated, why call it waste at all?"
**The answer:** the two-bucket model counts everything outside the
rate card, and slotting arrives as a deduction, not as a rate. It is
kept visible in the total, flagged non-addressable, and carries one
live verification question: do the deducted amounts match the
contracted fees? Discrepancies are disputable even when the fee is
not.

## Ghost promos: a calendar that ends while the billing continues

521 promo billbacks totaling $50,055 across the three-year
deduction history have no matching promotion in Cinderhaven's
calendar (`sql/promo_roi/ghost_promo_summary.sql`). The remaining
1,029 billbacks ($95,027) match a promotion window and are
accounted for. A billback matches when the same retailer has a
calendar promotion whose window — 14 days before start through 90
days after end — covers the deduction date. Billbacks carry no
promotion ID, so retailer plus date window is the only join
available.

**The attack:** the matcher is too strict; widen the window and the
ghosts disappear. **The answer:** the trailing-year figure does not
depend on matcher tolerance. The calendar holds 123 promotions and
its last entry ends 2024-11-03; no matching window extends past
early February 2025. Billbacks kept arriving through December 2025 —
513 of 540 trailing-year billbacks ($49,315) hit a calendar with
nothing left to match. The 27 that do match are early-January
deductions still inside the +90 day window of late-2024 promotions.
That is why the memo claims a process failure — either the calendar
stopped being maintained or retailers billed activity that never
ran, and the data cannot say which — rather than accusing anyone of
fraud.

## Double-dips: zero, and the zero is computed

The check (`sql/deductions/double_dip_events.sql`) scans for
deductions flagged as double payment on the same promotion — an
off-invoice discount and a billback both collected. It returns zero
rows.

**The attack:** "you found nothing because you didn't look." **The
answer:** the query is in the library, the empty section prints in
the workbook anyway (Tab 2, Double-Dip Alert), and the validation
suite asserts the zero. Without the check, a duplicate billback is
indistinguishable from a legitimate one; the absence of double-dips
became a statable fact only after the infrastructure to find them
existed.

## Recovery: 41.9 cents per disputed dollar, on 32% of the waste

Cinderhaven filed 5,247 disputes covering $382,579 in deductions and
recovered $160,161 (`sql/reconciliation/dispute_summary.sql`,
`recovery_rate.sql`). That is 41.9% of all disputed dollars, and
49.7% on the disputes that have closed — 1,411 won, 1,478 partial,
1,509 lost, 849 still pending. Both rates are quoted because both
get asked: the first describes the portfolio, the second the
realized win rate.

**The attack:** a 42% recovery rate means the dispute function works
— where is the problem? **The answer:** coverage. Of the trailing
year's $343,281 in waste, $109,726 — 32% — was ever disputed. The
average disputed deduction is $73 ($382,579 across 5,247 filings),
so the effort concentrates on exactly the small-dollar noise the
memo says to automate, while two-thirds of the waste never enters
the process. The win rate is the healthy organ. Coverage is the
disease.

## What this diagnostic does not claim

- **No vague bucket.** All 14,947 deductions in the database carry a
  specific type; the `is_vague` flag is zero on every row. Earlier
  drafts of this analysis ran against a prior scenario database with
  a large unclassifiable category; the regenerated dataset contains
  none, and no current deliverable claims one.
- **No external benchmarks.** No industry-average deduction rate or
  recovery rate is cited anywhere. Every comparison is internal to
  the dataset, where it can be checked.
- **No causal promo claims.** Promotional ROI is a pre/during volume
  comparison with stated assumptions, not causal inference; the
  walkthrough documents the limitation.
- **No real company.** Cinderhaven is generated data. The queries,
  the classification logic, and the validation suite are the
  deliverable; the dollars demonstrate them.
