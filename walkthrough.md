# Trade Spend Diagnostic — Walkthrough

Cinderhaven Provisions, a specialty food company with $32.3 million
in trailing-52-week scan revenue (CY2025), carries a structural trade rate
of 9.8% (~$3.2M). All-in trade cost including operational
deductions is 10.9%. The rate card is not the problem. The
1.1-point gap above it is: $343K per year in operational waste
buried inside the deductions — spoilage and damage claims, pricing
errors, pallet and label fines, short-ship charges — spread so
evenly across eight categories that six of them land within $4,800
of one another. Cinderhaven recovers 41.9% of the dollars it
disputes; the trouble is that only about a third of the waste is
ever disputed at all. The rest expires unverified.

This walkthrough explains how the diagnostic was built, what it
found, and what each deliverable does. It is written for someone
evaluating whether this kind of analysis is worth commissioning for
their own data.

---

## 1. The problem

CPG companies in the $15M–$30M revenue band occupy an uncomfortable
middle ground in trade spend management. They are large enough to
sell through four or five retail channels, each with its own deduction
mechanics, code taxonomies, and billing timelines. They are too small
to justify dedicated trade promotion management software, which
typically requires $50K+ in annual licensing and a full-time analyst
to operate. The controller reconciles trade spend in Excel, working
from mismatched sources: a rate card negotiated by sales, deduction
remittances arriving from retailers in proprietary formats, promotional
calendars maintained in spreadsheets or email threads, and POS scan
data available through retailer portals with varying lag times and
granularity.

The structural result is that most companies at this scale know what
they *planned* to spend on trade but not what they *actually* lost
to operational waste. The planned rate — the channel-by-channel
allowance in the rate card — is visible because someone negotiated
it. The unplanned cost — compliance fines, short-ship charges,
pricing errors, spoilage claims nobody checks — is invisible
because it arrives as line items on remittance statements that no
one has time to classify, cross-reference, or dispute before the
filing window closes.

The waste is measurable, and the measurement is the point of this
diagnostic. Cinderhaven's numbers are representative of the pattern:
a 9.8% structural trade rate that everyone can see, and $343K per
year in operational waste (1.1% of scan revenue) that did not
appear in any report until the infrastructure to calculate it was
built. The all-in trade cost is 10.9% — the 1.1-point delta above
the structural rate is not a rate problem, but a magnitude problem
hiding in the noise.

---

## 2. The methodology

### Two-bucket framing

Trade spend divides into two categories. **Structural trade** is
the planned, negotiated cost of doing business with each retailer —
the rate-card percentage applied to wholesale revenue. It is known
in advance, budgeted, and largely non-negotiable in the short term.
**Operational waste** is everything else: deductions taken by
retailers beyond the rate card, covering compliance fines, logistics
chargebacks, labeling penalties, spoilage claims, pricing errors,
and slotting fees.

An earlier version of the analysis attempted a three-bucket model,
separating promotional trade from structural and operational.
Investigation revealed that off-invoice allowances — the primary
promotional funding mechanism in Cinderhaven's contracts — are
already embedded in the rate card. Treating them as a separate
bucket double-counts. The detail tabs break out promotional
performance separately; the executive framing stays at two buckets.

### Data sources

Six source types feed the diagnostic, unified into 21 tables in a
single SQLite database:

- **SKU cost tables** — 50 products with COGS, wholesale prices by
  channel, and per-channel trade spend percentages. The structural
  trade calculation uses the channel-average rate (mean across all
  SKUs per channel), not per-SKU rates. The rate card is negotiated
  at the channel level; per-SKU application introduces false
  precision.
- **Deduction log** — 5,309 trailing-365-day deductions across 6
  retailers, each carrying a retailer-specific code, an amount, and
  a date. These are the raw material for the operational waste
  calculation.
- **Promotions calendar** — 123 planned promotions across five types
  (TPR, BOGO, ad circular, digital coupon, endcap), with planned
  costs and funding mechanisms.
- **POS scan data** — weekly point-of-sale records from 6
  retailers, used to measure promotional lift.
- **Dispute records** — 5,247 filed disputes with outcomes and
  recovery amounts.
- **Deduction code crosswalk** — retailer-specific codes mapped
  to a common taxonomy. Fuzzy matching (via rapidfuzz)
  handles naming inconsistencies across retailers — "WFM" versus
  "Whole Foods," "short ship" versus "shipping shortage."

### Promotion measurement

Promotional ROI uses a pre/during/post volume comparison against POS
scan data. Baseline volume is the average weekly units in the
pre-period window (adjustable from 1 to 12 weeks; default 4).
Incremental revenue is the lift in during-period volume over
baseline, multiplied by the average selling price. This is arithmetic
with stated assumptions, not causal inference. It does not control
for seasonality, competitor activity, or distribution changes. The
limitation is acknowledged; it is the appropriate methodology for a
diagnostic-level engagement.

---

## 3. The findings

### The headline

Cinderhaven's structural trade rate is 9.8% of trailing-52-week
retailer scan revenue ($32,323,139.62, CY2025 — verified against
production 2026-07-29) — ~$3.2M in planned trade. The all-in trade
cost, including operational deductions, is 10.9% ($3.52M). The
operational waste layer is $343K trailing-365-day, representing
1.1% of scan revenue — the 1.1-point gap between the structural
rate and the all-in rate (see Tab 1: Executive Pulse).

The rate is not the story. The magnitude of waste — $343K per
year in charges that are avoidable, contestable, or unjustifiable —
is the story.

### Where the waste comes from

Eight deduction categories compose the operational waste, and none
of them dominates it (query: `deductions/waste_by_category.sql`):

| Category | Count | Amount | Share |
|----------|------:|-------:|------:|
| Spoilage claims | 546 | $53,664 | 15.6% |
| Pricing errors | 547 | $53,224 | 15.5% |
| Damaged goods | 543 | $53,169 | 15.5% |
| Slotting fees | 532 | $51,879 | 15.1% |
| Pallet fines | 580 | $51,565 | 15.0% |
| Label fines | 532 | $48,861 | 14.2% |
| Short-ship charges | 1,406 | $28,053 | 8.2% |
| Late delivery | 86 | $2,865 | 0.8% |

The evenness is itself a diagnostic finding. Six categories land
between $48,861 and $53,664 — within $4,800 of one another — and
the largest is 15.6% of the total. There is no single villain, no
one contract or retailer program to fix. Waste distributed this
evenly means the deduction pipeline has no verification layer at
any step: every category leaks at roughly the same rate. Short-ship
is the frequency outlier — 1,406 events averaging $20, a case for
automated matching rather than manual dispute — and late delivery,
at $2,865, is negligible (see Tab 2: Leak Diagnostic).

### Double-dip detection

The matching infrastructure built for this diagnostic — linking
deductions back to specific promotions by retailer, date window,
and amount — found zero double-payment events in the current
dataset. The check matters even when it returns nothing: without
it, a duplicate billback is indistinguishable from a legitimate one,
and the absence of double-dips could not be stated with confidence
(query: `deductions/double_dip_events.sql`).

### Ghost promotions

521 promo-billback deductions totaling $50,055 across the
three-year deduction history reference promotions that do not
appear in Cinderhaven's promotion calendar. The remaining 1,029
billbacks ($95,027) fall inside a promotion window. In the trailing
year, 513 of 540 promo billbacks ($49,315) lack a matching calendar
entry — the calendar's last promotion ends 2024-11-03. These "ghost
promos" have two possible explanations: the promotion existed but
was never recorded in the calendar, or the retailer billed for
promotional activity that did not take place. Both explanations
indicate a process gap — either in promotion planning or in
deduction validation (see Tab 3: Promo Efficacy; query:
`promo_roi/ghost_promo_summary.sql`).

### Retailer margin spread

Net-net effective margin — gross margin minus all trade costs as a
percentage of revenue — varies significantly across the retailer
portfolio. DTC carries no trade spend and represents the zero-trade
benchmark. Excluding DTC, the spread reflects both the structural
rate negotiated with each channel and the operational deductions
layered on top (see Tab 4: Retailer Risk; query:
`retailer/net_net_margin.sql`).

### Dispute recovery

Cinderhaven filed 5,247 disputes covering $382,579 in deductions
and recovered $160,161 — 41.9% of disputed dollars, 49.7% on
disputes that have closed (1,411 won, 1,478 partial, 1,509 lost,
849 pending). The recovery rate is respectable; the coverage is
not. Only $109,726 of the trailing year's $343K in operational
waste — 32% — was ever disputed, and the average disputed deduction
is $73. An adjustable recovery model in the workbook shows the
addressable improvement at higher dispute coverage (query:
`reconciliation/recovery_rate.sql`).

### Data quality

Some trailing-year deductions have no crosswalk translation — the
retailer's code does not appear in the deduction code table. These
unmapped deductions still carry a dollar amount and a category
assignment from the raw data, but the human-readable translation is
missing. Both this and any promotions with no POS data represent
measurement gaps that point to incomplete integration between
Cinderhaven's internal records and retailer-provided data (see
Tab 6: Deduction Code Crosswalk).

---

## 4. The deliverables

Three artifacts consume the same underlying database. Each is built
for a different user and a different moment.

**The Excel workbook** (7 tabs) is the static diagnostic. It opens
cold — no database connection, no setup. Tab 1 (Executive Pulse)
leads with the waste-magnitude punchline: 9.8% structural,
1.1% operational waste, $343K trailing-365, 10.9% all-in. Tabs 2 through 4
(Leak Diagnostic, Promo Efficacy, Retailer Risk) provide the
supporting detail with adjustable inputs — a target recovery rate,
a promo comparison window, and per-retailer what-if trade rates.
Tab 5 (Deduction Ledger) is the full trailing-year data with
auto-filters and freeze panes. Tab 6 maps retailer codes to plain
English. Tab 7 documents every calculation. Color-coded: navy for
analysis tabs, teal for data, gray for reference.

**The SQL query library** (25 queries in 6 categories) is for the
analyst who wants to run their own cuts. Each `.sql` file answers
one diagnostic question — from "What is total revenue?" to "Which
promo-billback deductions have no matching promotion?" A 10-step
suggested execution order mirrors the diagnostic narrative, from
revenue through waste, promotions, retailer risk, and recovery.

All deliverables are built from the same SQLite database, maintained
as a git submodule. When the underlying data is updated, the workbook
is regenerated (`python build_workbook.py`) and the numbers stay
consistent because there is one source.

---

## 5. What a real engagement would add

The diagnostic demonstrates that the data exists, the methodology
works, and the findings are quantified. It is a point-in-time
snapshot built from exported files. A live engagement would differ
in five respects.

**Causal promotion modeling.** The pre/during/post methodology
measures volume change during a promotion without controlling for
confounders. A real engagement would build seasonality-adjusted
baselines using 18-24 months of history, controlling for trends,
holidays, distribution changes, and competitor activity. The
difference matters: simple comparison overstates lift for products
that sell well in the promotion's season and understates it for
counter-seasonal items.

**Automated deduction classification.** The diagnostic's crosswalk
covers retailer-specific codes across 6 retailers. A production
system would ingest retailer EDI feeds directly, apply ML-based
code classification for new or ambiguous codes, and maintain the
crosswalk continuously rather than as a static lookup table.

**System integration.** The diagnostic works from exported flat
files. A live engagement would connect to the ERP (invoice and
shipment data), the deduction management system (if one exists),
and retailer portals (deduction feeds, POS data, compliance
reports). Integration surfaces double-dips and ghost promos in near
real-time, not after a year of accumulation.

**Dispute workflow automation.** Cinderhaven already recovers 41.9%
of disputed dollars; the constraint is that only 32% of the waste
gets disputed, mostly in $73 increments. Automated workflows —
deadline tracking, evidence assembly, escalation rules, batch
filing for small-dollar categories — attack the coverage gap
rather than the win rate.

**Ongoing monitoring.** The diagnostic answers "where is the money
going?" once. The engagement answers it every month, with trend
reporting, exception alerts, and threshold triggers that flag new
patterns — a retailer whose deduction rate is climbing, a promotion
type whose ROI has turned negative, a compliance category that
spiked after a warehouse change. The value of the diagnostic is
proving $343K of recoverable, contestable waste exists where it
was invisible. The value of the engagement is preventing it from
reopening.
