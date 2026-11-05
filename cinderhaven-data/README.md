> **Superseded 2026-07-29.** This directory documents an older, locally generated dataset. The live source of record is `cinderhaven-data-platform` (`reference/canonical_values.yml`, verified against production). Kept as provenance; figures below are historical.

# cinderhaven-data

> **Snapshot, not source of truth.** The SQLite database in `data/`
> is an export of **[cinderhaven-data-platform](https://github.com/MsShawnP/cinderhaven-data-platform)**
> (Fly.io Postgres + dbt), which is the single source of truth for
> Cinderhaven data. This repo pins the snapshot that the
> trade-spend diagnostic was built and validated against. The
> generation scripts in `scripts/` predate the platform — the 01-15
> generators produce an older 90-SKU dataset, and `build_db.py`
> re-seeds a retired 50-SKU / 3-product-line product master — and
> must not be run to rebuild the current database.

Cinderhaven Provisions is a **synthetic demonstration dataset**: a
fictional specialty food brand invented for the
[Lailara portfolio](https://github.com/MsShawnP). It is not a real
company, not a client, and not any real company's data — every row
is generated. The scenario: a brand doing $32.3M in trailing-52-week
scan revenue across 50 SKUs in five product lines (Artisan Sauces,
Pantry Staples, Specialty Condiments, Dried Goods, Snack Bites),
selling through six retailers — a national mass retailer, a club retailer, a natural grocer,
a regional natural grocer, a conventional grocer, and a regional group — across 640 doors. The cost
table also carries rate-card columns for UNFI, KeHE, and DTC, but
the scan and deduction history covers the six retailers.

## The dataset

**`data/cinderhaven_product_master.db`** — a 102 MB SQLite database,
21 tables, committed directly. No build step.

The deduction and dispute layers pose the scenario the
[trade-spend diagnostic](https://github.com/MsShawnP/trade-spend-data-diagnostic)
is built to detect: roughly $343K/year of operational waste spread
almost evenly across eight deduction categories, a dispute function
that wins 41.9 cents per disputed dollar but touches less than a
third of the waste, and a promotion calendar that stops in November
2024 while promo billbacks keep arriving through the end of 2025.

### Commercial tables

| Table | Rows | What it contains |
|---|---:|---|
| `product_master` | 50 | SKU attributes: GTINs, UPCs, case dimensions, MSRP, brand owner |
| `stores` | 640 | Doors by retailer (Walmart 180, Kroger 150, Whole Foods 120, Sprouts 90, Costco 60, Regional Group 40) with region, state, volume tier |
| `distribution_log` | 9,943 | SKU x store authorization history |
| `sku_costs` | 50 | COGS, landed cost, per-channel wholesale prices, per-channel trade rate columns (incl. UNFI, KeHE, DTC) |
| `price_history` | 407 | Time-based wholesale price and MSRP changes |
| `promotions` | 123 | Promo calendar, 2023-01-02 to 2024-11-03; five types (ad circular 31, BOGO 24, digital coupon 24, endcap 23, TPR 21) |
| `chargebacks` | 2,873 | Defect-driven chargebacks by month, 2023-01 to 2026-01 |
| `scan_data` | 1,325,794 | Weekly units and dollars by SKU x store; 156 weeks, 2023-01-07 to 2025-12-27 |

### Deduction and dispute tables

| Table | Rows | What it contains |
|---|---:|---|
| `retailers` | 6 | Retailer reference: dispute portal, dispute method |
| `retailer_rules` | 54 | Per-retailer x deduction-type dispute rules |
| `deduction_codes` | 102 | Retailer-specific deduction codes |
| `edi_requirements` | 49 | Per-retailer compliance specs |
| `orders` | 46,760 | Purchase orders, 2023-01-01 to 2026-01-02 |
| `order_lines` | 189,039 | Line items per order |
| `shipments` | 46,760 | Carrier, BOL, delivery, ASN per order |
| `pack_records` | 46,760 | Pack/label compliance evidence |
| `deductions` | 14,947 | Deduction records, 2023-01-23 to 2026-01-02 (~36 months); nine types — eight operational categories plus `promo_billback`; `is_vague` and `is_double_dip` are 0 on every row |
| `remittances` | 222 | Payment events bundling deductions |
| `disputes` | 5,247 | Dispute filings with evidence quality, outcome, recovered amount |
| `dispute_evidence` | 22,912 | Evidence items per dispute |
| `post_audit_claims` | 222 | Retroactive audit clawbacks |

## Headline figures (verified against this snapshot)

- Trailing-52-week scan revenue (2025-01-04 to 2025-12-27):
  **$32,323,139.62**
- Structural trade: **$2,992,224 (9.2%)** by the workbook's
  channel-average method; a pure-SQL channel-mapping variant gives
  $2,914,207 (9.0%) — both derivations are documented in the
  diagnostic's `DEFENSIBILITY.md`
- Operational waste (trailing 365 days, excluding promo billbacks):
  **$343,281 across 4,772 events (1.1%)**; all-in trade **10.3%**
- Waste categories: 8, six of them clustered between $48,861 and
  $53,664; the largest is 15.6% of the total
- Promo billbacks with no matching calendar promotion: **521 /
  $50,055** over three years; 513 of 540 trailing-year billbacks
  ($49,315) are unmatched
- Double-dip deductions: **0**; vague deductions: **0**
- Disputes: **5,247** (won 1,411, partial 1,478, lost 1,509,
  pending 849); **$160,161 recovered on $382,579 disputed = 41.9%**
  (49.7% on closed disputes)

## How this snapshot was produced

The database was exported from the cinderhaven-data-platform
Postgres instance and patched for local use by two scripts in the
trade-spend-data-diagnostic repo: `scripts/extract_from_postgres.py`
(pulls all 21 tables over a `flyctl proxy`) and
`scripts/fixup_extracted_db.py` (adds the compatibility columns the
workbook expects, e.g. plain retailer names alongside `RET-*` ids).

The generators in this repo's `scripts/01-15` are the pre-platform
pipeline. They produce a different, older dataset (90 SKUs, 2024
windows) and remain only as reference; `data_generation_log.md`
documents that pipeline, not the current database.

## Downstream

- **[trade-spend-data-diagnostic](https://github.com/MsShawnP/trade-spend-data-diagnostic)** — Excel workbook diagnostic (consumes this repo as a git submodule)
- **[cinderhaven-data-platform](https://github.com/MsShawnP/cinderhaven-data-platform)** — dbt pipeline on Fly.io Postgres (upstream source)
- **[retailer-deduction-recovery](https://github.com/MsShawnP/retailer-deduction-recovery)** — Interactive React demo
- **[retail-velocity-decision-tool](https://github.com/MsShawnP/retail-velocity-decision-tool)** — Velocity decision tool

## Setup

1. Clone this repo
2. The database is already at `data/cinderhaven_product_master.db`

No build step required — the DB is committed directly.

## Tools

Python 3.10+ (stdlib only), SQLite

## License

MIT — see [LICENSE](LICENSE).
