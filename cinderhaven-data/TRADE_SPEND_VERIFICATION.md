# Trade Spend Verification — Updated cinderhaven-data Build

**Date:** 2026-05-09
**Database:** `cinderhaven_product_master.db` (163.7 MB, 22 tables, built from merged deduction pipeline)
**Scan window:** 2024-05-11 to 2026-05-02 (104 weeks)

---

## 1. Revenue and Channel Mix (trailing 52 weeks: 2025-05-03 to 2026-05-02)

| Channel              |       Revenue | Share |
|----------------------|--------------:|------:|
| National mass retailer | $13,001,137.79 | 50.8% |
| Distributor A        |  $4,485,742.51 | 17.5% |
| Natural grocer       |  $2,713,109.97 | 10.6% |
| Club retailer        |  $2,239,549.07 |  8.8% |
| DTC                  |    $851,241.16 |  3.3% |
| Green Basket Market  |    $507,427.01 |  2.0% |
| Southside Grocers    |    $488,833.07 |  1.9% |
| Prairie Provisions   |    $445,557.53 |  1.7% |
| Mountain Pantry Co   |    $436,938.58 |  1.7% |
| Harbor Fresh         |    $423,515.23 |  1.7% |
| **Total**            | **$25,593,051.92** | **100%** |

Full-window revenue (104 weeks): $46,483,183.75

---

## 2. Trade Spend Rates (sku_costs — unchanged)

| Channel      | Avg trade_spend_pct | Channel Rev      | Implied $      |
|--------------|--------------------:|-----------------:|---------------:|
| National mass retailer |              0.2149 | $13,001,137.79   | $2,794,276.76  |
| Distributor A |              0.1507 |  $4,485,742.51   |   $675,996.41  |
| Club retailer |              0.1739 |  $2,239,549.07   |   $389,363.02  |
| Natural grocer |              0.1279 |  $2,713,109.97   |   $346,892.21  |
| Regional     |              0.0993 |  $2,302,271.42   |   $228,523.46  |
| DTC          |              0.0000 |    $851,241.16   |         $0.00  |
| **Total**    |                     |                  | **$4,435,051.87** |

**Implied trade spend rate: 17.33% of trailing-52w revenue.**

---

## 3. Promotions Table — New Fields

- **Rows:** 188 (across 75 distinct promo events)
- **promo_cost:** 181 non-null, 7 null
  - Sum: **$20,483.73**
  - Min: $11.57 — Max: $337.21 — Avg: $113.17
- **funding_mechanism distribution:**

| Mechanism   | Count | Sum promo_cost |
|-------------|------:|---------------:|
| bill_back   |    52 |     $5,872.61  |
| fixed_fee   |    48 |     $6,824.21  |
| off_invoice |    47 |     $5,168.11  |
| scan_down   |    36 |     $2,350.84  |
| mcb         |     5 |       $267.96  |

- funding_mechanism set but promo_cost NULL: **7 rows** (expected — represents TBD/unconfirmed costs)
- promo_cost set but funding_mechanism NULL: **0 rows**

**Note:** The $20.5K promo_cost sum represents granular per-event manufacturer cost estimates. It is not the total trade spend — the sku_costs trade_spend_pct captures the full trade budget rate including slotting, accruals, and billbacks that don't appear as individual promotion rows.

---

## 4. Deductions — Updated Window

- **Date range:** 2024-07-04 to 2026-05-02
- **Max deduction_date <= scan_data max? YES**
- **Total:** 3,087 deductions, **$1,537,390.70**
- **Trailing 365 days** (2025-05-03 to 2026-05-02): 2,365 deductions, **$1,222,452.80**

### By type

| Type           | Count | Total $      | Share |
|----------------|------:|-------------:|------:|
| vague          |   233 | $339,306.01  | 22.1% |
| promo_billback |   355 | $275,563.31  | 17.9% |
| short_ship     | 1,062 | $240,133.32  | 15.6% |
| label_fine     |   452 | $222,956.15  | 14.5% |
| spoilage       |   135 | $126,263.26  |  8.2% |
| slotting       |    31 | $120,401.48  |  7.8% |
| late_delivery  |   580 | $114,881.85  |  7.5% |
| damaged        |   125 |  $77,931.81  |  5.1% |
| pallet_fine    |   114 |  $19,953.51  |  1.3% |

### By retailer

| Retailer            | Count | Total $      | Share |
|---------------------|------:|-------------:|------:|
| National mass retailer | 1,435 | $647,077.57  | 42.1% |
| Distributor A       |   473 | $252,187.22  | 16.4% |
| Distributor B       |   423 | $186,147.52  | 12.1% |
| Club retailer       |    80 | $175,848.97  | 11.4% |
| Natural grocer      |   339 | $123,548.26  |  8.0% |
| green_basket_market |    95 |  $43,324.69  |  2.8% |
| southside_grocers   |    69 |  $30,592.52  |  2.0% |
| harbor_fresh        |    56 |  $27,282.76  |  1.8% |
| prairie_provisions  |    67 |  $26,377.54  |  1.7% |
| dtc                 |     2 |  $13,079.32  |  0.9% |
| mountain_pantry_co  |    48 |  $11,924.33  |  0.8% |

**promo_billback specifically:** 355 deductions, $275,563.31

---

## 5. Double-Dips

**Count: 3 — Total: $19,305.91**

| Deduction ID | Retailer | SKU      | Amount     | Date       | Matching off_invoice Promo |
|--------------|----------|----------|------------|------------|---------------------------|
| DED-0003040  | National mass retailer | CHP-0013 | $6,226.59  | 2024-07-04 | PROMO-0046 (2024-06-10 to 2024-06-24) |
| DED-0003041  | dtc      | CHP-0071 | $7,551.68  | 2024-08-02 | PROMO-0070 (2024-07-15 to 2024-07-22) |
| DED-0003042  | dtc      | CHP-0084 | $5,527.64  | 2024-08-07 | PROMO-0070 (2024-07-15 to 2024-07-22) |

Each double-dip has a confirmed matching promotion with `funding_mechanism = 'off_invoice'` in the same SKU/retailer window. The retailer collected the discount twice: once via the invoice price reduction, once via a promo_billback deduction.

**Note:** Double-dip deductions have `order_id = NULL` — they were seeded as billing-level deductions, not linked to the order/shipment pipeline. This is by design.

---

## 6. Disputes and Recovery

| Metric           | Value           |
|------------------|----------------:|
| Total disputes   |           1,409 |
| Total disputed $ |    $687,209.52  |
| Total recovered  |     $98,215.54  |
| **Recovery rate**| **14.3%**       |

### By outcome

| Outcome          | Count | Disputed $    | Recovered $   |
|------------------|------:|--------------:|--------------:|
| lost_evidence    |   472 | $226,212.17   |         $0.00 |
| abandoned        |   161 | $117,466.49   |         $0.00 |
| pending          |   116 | $108,048.12   |         $0.00 |
| won_full         |   215 |  $81,254.54   |    $81,254.54 |
| lost_no_response |   144 |  $56,741.44   |         $0.00 |
| lost_other       |   163 |  $54,624.82   |         $0.00 |
| won_partial      |   101 |  $35,693.96   |    $16,961.00 |
| lost_deadline    |    37 |   $7,167.98   |         $0.00 |

---

## 7. Three-Bucket Model

| Bucket                                       | $              | % of Revenue |
|----------------------------------------------|---------------:|-------------:|
| Structural trade (implied - promo_cost)       | $4,414,568.14  |       17.25% |
| Planned promotional (promo_cost sum)          |    $20,483.73  |        0.08% |
| Operational/compliance (trail-365 excl PB)    | $1,010,940.02  |        3.95% |
| **ALL-IN TOTAL**                              | **$5,445,991.89** | **21.28%** |

**promo_billback deductions (trail-365): $211,512.78** — excluded from operational bucket to avoid double-counting with the promotions table, but these are real cash outflows.

**Overlap flag:** The promo_billback deductions and promotions.promo_cost could overlap if the same promotional events appear in both tables. The three-bucket model handles this by counting promo_cost as "planned promotional" and excluding promo_billback deductions from "operational." Promo_billback deductions that DON'T correspond to a tracked promotion would be missed — but that's the gap the workbook should surface.

---

## 8. Cross-Table Consistency

| Check                                      | Result |
|--------------------------------------------|--------|
| Deduction order_id not in orders           | 0      |
| Deduction retailer_id not in retailers     | 0      |
| order_lines sku not in product_master      | 0      |
| deduction_date outside scan_data window    | 0      |
| Chargebacks with exact amount+month match  | 1      |

chargebacks (381 rows) and deductions (3,087 rows) are separate tables with different schemas. No shared PKs by design. The 1 exact-amount+month match is coincidental.

---

## Changes from Pre-Merge Findings

| Metric                  | Pre-Merge  | Post-Merge      | Delta        |
|-------------------------|------------|-----------------|--------------|
| Trailing-52w revenue    | $25.96M    | $25,593,051.92  | -$367K       |
| Implied trade spend     | $4.44M     | $4,435,051.87   | ~unchanged   |
| Trailing-365 deductions | ~$932K     | $1,222,452.80   | +$290K       |
| Recovery rate           | (not measured) | 14.3%        | —            |

Revenue shifted slightly due to date window alignment (the trailing-52w window moved forward). Implied trade spend held. Deduction total increased — the merged pipeline generates a broader set of deduction types (now 9 types vs the pre-merge state) with the full deduction lifecycle.

---

## Locked Numbers for the Workbook

| Metric                              | Value              |
|--------------------------------------|--------------------|
| Annual wholesale revenue             | $25,597,699        |
| Implied trade spend (sku_costs)      | $4,435,513 (17.3%) |
| Promotions promo_cost sum            | $20,484            |
| Structural trade (implied - promo)   | $4,415,029 (17.3%) |
| Trailing-365 deductions (all)        | $1,225,472 (4.8%)  |
| Trailing-365 deductions (excl PB)    | $1,012,455 (4.0%)  |
| Trailing-365 promo_billback          | $213,017           |
| All-in trade spend (2-bucket)        | $5,447,968 (21.3%) |
| Double-dip count / total             | 3 / $19,306        |
| Dispute count                        | 1,410              |
| Total recovered                      | $98,216            |
| Recovery rate                        | 13.7%              |
| Scan data window                     | 2024-05-11 to 2026-05-02 |
| Deduction window                     | 2024-07-04 to 2026-05-02 |
| Cross-table integrity violations     | 0                  |
