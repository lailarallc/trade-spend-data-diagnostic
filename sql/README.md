# SQL Diagnostic Query Library

Standalone SQL queries for investigating Cinderhaven Provisions' trade
spend, deduction patterns, and promotional performance. Each `.sql` file
answers one diagnostic question and runs against the `cinderhaven_product_master.db`
SQLite database (located at `cinderhaven-data/data/` via git submodule).
Intended for controllers, analysts, or anyone who wants to explore the
data without opening the Excel workbook.

---

## How to run

**Database path** (relative to project root):

```
cinderhaven-data/data/cinderhaven_product_master.db
```

**sqlite3 CLI:**

```bash
sqlite3 cinderhaven-data/data/cinderhaven_product_master.db < sql/trade_rate/total_revenue.sql
```

For queries with parameters, open the file, replace the `:param_name`
placeholders with literal values, then run.

**Python:**

```python
import sqlite3
from pathlib import Path

db = Path("cinderhaven-data/data/cinderhaven_product_master.db")
conn = sqlite3.connect(db)

# Example: total revenue
sql = Path("sql/trade_rate/total_revenue.sql").read_text()
# Replace parameter placeholder before executing
sql = sql.replace(":oldest_week", "'2026-01-10'")
for row in conn.execute(sql):
    print(row)
```

---

## Query index

### trade_rate/

| File | Question it answers |
|------|---------------------|
| trailing_52_weeks.sql | What are the 52 most recent weekly scan periods? |
| total_revenue.sql | What is total wholesale revenue for the trailing 52 weeks? |
| revenue_by_retailer.sql | How is revenue distributed across retailers/channels? |
| channel_trade_rates.sql | What is the average structural trade rate for each channel? |
| structural_trade_amount.sql | What is the structural trade spend in dollars, by retailer? |
| all_in_trade_rate.sql | What is the all-in trade rate (structural + waste) as % of revenue? |

### deductions/

| File | Question it answers |
|------|---------------------|
| waste_by_type_summary.sql | What is operational waste by deduction type (count and dollars)? |
| waste_by_category.sql | Same as above, plus avg dispute resolution days and % of waste |
| double_dip_events.sql | Which deductions are double-payments on the same promotion? |
| operational_deductions_by_retailer.sql | How much operational waste does each retailer generate? |
| promo_billback_by_retailer.sql | How much does each retailer bill back for promotional activity? |

### promo_roi/

| File | Question it answers |
|------|---------------------|
| all_promotions.sql | What promotions are in the calendar? |
| asp_by_sku_retailer.sql | What is the average selling price for each SKU at each retailer? |
| weekly_volume_by_sku_retailer.sql | What is weekly unit volume by SKU and retailer? |
| matched_promo_deductions.sql | Which promo_billback deductions match a planned promotion? |
| ghost_promos.sql | Which promo_billback deductions have no matching promotion? |
| ghost_promo_summary.sql | How many ghost promo deductions exist and what's the total? |
| promo_performance.sql | What is the ROI of each promotion (pre/during volume comparison)? |

### retailer/

| File | Question it answers |
|------|---------------------|
| gross_margin_by_channel.sql | What is the average gross margin for each sales channel? |
| net_net_margin.sql | What is each retailer's net-net effective margin after all trade costs? |

### crosswalk/

| File | Question it answers |
|------|---------------------|
| deduction_codes.sql | What do retailer-specific deduction codes mean (verified vs. inferred)? |

### reconciliation/

| File | Question it answers |
|------|---------------------|
| dispute_summary.sql | How many disputes have been filed and how much recovered? |
| recovery_rate.sql | What percentage of disputed dollars has been recovered? |
| addressable_improvement.sql | How much more could be recovered at a target recovery rate? |
| full_deduction_ledger.sql | Full deduction detail with code translations and dispute status |

---

## Suggested execution order

For a new analyst walking through the diagnostic narrative:

1. **trailing_52_weeks.sql** — establish the analysis window; note
   the oldest and newest dates for use as parameters in later queries
2. **total_revenue.sql** — the revenue headline ($32.32M trailing-52w, CY2025)
3. **all_in_trade_rate.sql** — the punchline: 9.8% structural +
   1.1% waste = 10.9% all-in (the rate card is known and budgeted;
   the waste magnitude is the story)
4. **waste_by_category.sql** — where the 1.1% comes from (8 deduction
   types; six of them within $4,800 of each other, none above 16%
   of the total)
5. **double_dip_events.sql** — the double-payment check (0 events in
   the current data)
6. **promo_performance.sql** — which promotions created value vs.
   destroyed it
7. **ghost_promo_summary.sql** — $50K in deductions referencing
   promotions not in the calendar
8. **net_net_margin.sql** — true margin by retailer after all trade costs
9. **recovery_rate.sql** — current dispute recovery performance (41.9%)
10. **addressable_improvement.sql** — how much more could be recovered
    at a 30% target rate

This order mirrors the workbook's tab flow: Executive Pulse (1–3),
Leak Diagnostic (4–5), Promo Efficacy (6–7), Retailer Risk (8),
Reconciliation (9–10).

---

## Parameters

Queries that require date ranges or other inputs use named placeholder
comments (`:param_name`). Before running, replace each placeholder with
a literal value.

Common parameters:

| Parameter | Meaning | How to get the value |
|-----------|---------|----------------------|
| `:oldest_week` | Start of the trailing-52-week window | Last row from `trailing_52_weeks.sql` |
| `:max_scan` | End of the analysis window (most recent scan week) | First row from `trailing_52_weeks.sql` |
| `:target_rate` | Target recovery rate as a decimal (e.g., 0.30) | Your assumption |
| `:window` | Pre-period weeks for promo ROI baseline (1–8) | Default: 4 |

---

## Locked numbers reference

Key verified figures for sanity-checking query output (regenerated
dataset; pins mirror `validate_workbook.py`). Minor variance (±$2,000
on dollar amounts, ±2 on counts) is expected from trailing-window
boundary effects.

| Metric | Locked value | Query to check |
|--------|-------------|----------------|
| Trailing-52w scan revenue | $32,323,140 | total_revenue.sql |
| Structural trade | ~$3,177,051 (9.8%) | structural_trade_amount.sql |
| Operational waste | ~$343,281 (1.1%) | waste_by_category.sql |
| All-in trade cost | ~$3,520,331 (10.9%) | all_in_trade_rate.sql |
| Largest waste category | spoilage, $53,664 (15.6% of waste) | waste_by_category.sql |
| Double-dip events | 0 | double_dip_events.sql |
| Disputes filed | 5,247 | dispute_summary.sql |
| Total recovered | $160,161 (41.9% of $382,579 disputed) | recovery_rate.sql |
| Ghost promos | 521 / $50,055 | ghost_promo_summary.sql |
| Trailing-365 deductions | 5,309 | full_deduction_ledger.sql |
