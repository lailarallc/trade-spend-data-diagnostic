# Trade Spend Diagnostic — finding the $343K of operational waste hiding in Cinderhaven's deductions

A trade spend diagnostic for a mid-market natural/specialty CPG company.
Cinderhaven's structural trade rate (9.8% of retailer scan revenue, ~$3.2M on
$32,323,139.62 trailing-52-week — canonical `revenue.retail_scan.cy2025`,
verified against production 2026-07-29) is the negotiated, budgeted cost of doing business. The
problem is operational: ~$343K per year in avoidable deductions, spread
almost evenly across eight categories — six of them between $49K and $54K
each, so no single fix exists — that nobody classifies or verifies before
the filing window closes. All-in trade cost including waste is 10.9% of
revenue; the 1.1-point delta above the structural rate is where the
recoverable money lives.

> **Scope note (2026-07-30).** This diagnostic derives its figures live from the
> retailer dataset: 9.8% structural / 10.9% all-in / ~$343K waste on
> $32,323,139.62 trailing-52-week scan revenue. The portfolio-level canonical
> (`CINDERHAVEN_CANONICAL.md` § Trade Economics) publishes 9.83% structural /
> 11.00% all-in / ~$380K waste on the same $32,323,139.62 denominator.
> Structural trade matches canonical to the dollar ($3,177,051). The remaining
> ~0.1pp all-in gap is waste scope, not data drift: the workbook sums the
> retailer deduction ledger, while canonical measures waste across all
> channels. Canonical is the governing figure for cross-repo claims;
> reconciling the waste scopes is an explicitly deferred owner decision.

## What it does

The diagnostic quantifies the waste, classifies every deduction into a
defensible taxonomy, identifies which waste is addressable, and provides a
retailer-by-retailer P&L showing where the margin erosion concentrates.
It ships as four deliverables:

- **Excel workbook** — a 7-tab diagnostic built from a trailing-365-day
  dataset. Tab 1 leads with the finding and a recovery model. Tabs 2-4
  break down waste by category, promo ROI, and retailer risk (with channel
  rollup). Tab 5 is the full deduction ledger; tabs 6-7 are reference.
  Interactive inputs: adjustable recovery rate, promo comparison window,
  per-retailer what-if trade rates.
- **Executive memo** ([`EXECUTIVE_MEMO.md`](EXECUTIVE_MEMO.md)) — one-page
  condensation: the finding, where the money goes, what to do Monday morning.
- **Defensibility log** ([`DEFENSIBILITY.md`](DEFENSIBILITY.md)) —
  classification rules and rebuttal text for every deduction bucket.
  Pre-empts the "your consultant doesn't understand our business" pushback.
- **SQL query library** — 25 standalone queries answering specific diagnostic
  questions, from total revenue to ghost promo identification, for anyone who
  wants the data without opening Excel. See [`sql/README.md`](sql/README.md).

For the full methodology, findings narrative, and a tour of each deliverable,
read the [walkthrough](walkthrough.md).

## Why it matters

CPG companies in the $15M-$30M band are big enough to sell through four or
five retail channels — each with its own deduction mechanics and code
taxonomies — but too small to justify $50K+/year trade promotion management
software. So the controller reconciles trade spend in Excel, and the
unplanned cost (compliance fines, short-ship charges, pricing errors,
spoilage claims) arrives as remittance line items no one has time to classify or
dispute before the filing window closes. The result: companies know what they
*planned* to spend on trade, not what they actually lost. This diagnostic
makes the loss measurable — here, 1.1% of scan revenue that appeared in no
report until the infrastructure to calculate it was built.

## Quick start

```bash
git clone --recurse-submodules <repo-url>
cd trade-spend-data-diagnostic
pip install -r requirements.txt
python build_workbook.py        # writes output/trade_spend_diagnostic.xlsx
python validate_workbook.py     # acceptance suite (59 checks)
```

The `--recurse-submodules` flag is required — the `cinderhaven-data`
submodule contains the SQLite database. If you cloned without it:

```bash
git submodule update --init
```

`build_workbook.py` accepts `-o/--output` to change the destination path.
Individual SQL queries run directly against the submodule database:

```bash
sqlite3 cinderhaven-data/data/cinderhaven_product_master.db < sql/trade_rate/total_revenue.sql
```

## Tech stack

Python 3.10+, openpyxl, pandas, rapidfuzz, SQLite. No services, no cloud
dependencies — everything runs locally against the bundled database.

## Data contract

Cinderhaven canonical platform data: 50 SKUs across 5 product lines (Artisan
Sauces, Pantry Staples, Specialty Condiments, Dried Goods, Snack Bites),
6 contracted retailers (Walmart, Costco, Whole Foods, Sprouts, Kroger,
Regional Group), 3 distributors (UNFI, KeHE, DPI Northwest) + 1 DTC channel
(Shopify). Source: `CINDERHAVEN_CANONICAL.md` in `cinderhaven-data-platform`.

This diagnostic consumes the bundled SQLite snapshot — baseline revenue,
structural trade, and chargebacks unchanged from canonical, with regenerated
deduction and dispute layers (8 deduction categories, 5,247 disputes, no
vague-deduction or double-dip layer). The submodule's README documents the
snapshot table by table. The validated figure pins live in
`validate_workbook.py`.

## Project structure

```
EXECUTIVE_MEMO.md           One-page CEO summary
DEFENSIBILITY.md            Deduction classification rules + rebuttals
walkthrough.md              Full methodology and findings narrative
build_workbook.py           Generates the 7-tab diagnostic workbook
validate_workbook.py        Acceptance test suite (59 checks)
workbook/                   Workbook generation modules (one per tab)
sql/                        25 standalone diagnostic queries
scripts/                    Database build/extract helpers
cinderhaven-data/           Synthetic dataset (git submodule, 21 tables)
output/                     Generated workbook
requirements.txt            Python dependencies
```

## License

MIT. See [LICENSE](LICENSE).

## Contact

Shawn P — msshawnp@gmail.com

---
Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.
