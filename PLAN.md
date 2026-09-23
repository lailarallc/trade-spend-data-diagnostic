# Trade Spend Data Diagnostic — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Current arc

No active arc. All five planned arcs are complete. Project is shipped
and live on GitHub. See arc history below and HANDOFF.md for details.

---

## Arc history

### 2026-05-22 — Improvement pass
- **Trigger:** User-initiated `/improve` + `pip audit`
- **What was reviewed:** Code, documentation, architecture (SQLite vs Postgres alignment), data integrity, dependencies
- **What was fixed:**
  - Tab 7 (Methodology) made fully dynamic — all numbers now queried from DB at build time instead of hardcoded
  - Tab 1 summary sentence made dynamic (structural rate, all-in rate computed from data)
  - `scripts/build_db.py` — removed hardcoded absolute path, simplified to submodule-only
  - README.md, EXECUTIVE_MEMO.md, DEFENSIBILITY.md, walkthrough.md — all rewritten with correct numbers from current DB
  - sql/README.md — locked numbers table and suggested execution order updated to current DB values
  - CUSTOMIZATION.md — rewritten for SQLite architecture (was referencing stg_* Postgres tables and DATABASE_URL)
  - AUDIT.md — removed (entirely from Postgres era, all findings stale)
  - Stale output files removed (v2, v3, v4 workbooks)
  - requirements.txt — pinned version ranges for openpyxl, pandas, rapidfuzz
- **Deferred:** Security review and code quality review (deep automated passes) — not run this session
- **Validation:** 60/60 checks passing after all changes
- **Next review:** 2026-06-22

### Post-arc: Power BI bug fixes and presentation redesign (2026-05-11)
- Fixed 5 data bugs (AllInTradeCost double-count, waterfall sort,
  double-dip $0, ghost promo context, total row explosion)
- Redesigned dashboard as presentation layer (28→16 visuals,
  narrative takeaways, tables/slicers removed)
- DESIGN.md and BUILD_GUIDE.md rewritten

### Post-arc: Workbook restructuring (2026-05-11)
- Stripped openpyxl charts from tabs 2–4, replaced Tab 1 chart with
  in-cell data bar waterfall
- Converted all data ranges to Excel Tables (ListObject) — 9 named
  tables across 6 tabs
- Enhanced interactive input cells (FFF2CC fill, Protection(locked=False),
  data validation, cell comments)
- Fixed tab colors (00B050 green, A5A5A5 gray), added 6 KPI named ranges
- 10 files modified, 59/59 validation checks passing

### Arc 5: Written walkthrough (completed 2026-05-10)
- **Goal:** Write the narrative walkthrough and project README that
  tie the deliverables together as a portfolio piece
- **Outcome:** 2,276-word walkthrough covering problem, methodology,
  findings, deliverables, and real-engagement upsell — Economist
  voice, every paragraph data-forward with specific Cinderhaven
  numbers. Project README (76 lines) orients a cold visitor in
  under 60 seconds. All numbers verified against DB actuals.
- **Key decisions:** None — this arc was execution against the voice
  and structure decisions already in DECISIONS.md.

### Arc 4: Power BI dashboard preparation (completed 2026-05-10)
- **Goal:** Prepare everything needed to assemble the Power BI dashboard
  — data exports, DAX measures, build guide, automation tooling
- **Outcome:** 4-page dashboard fully specified. 7 CSV data exports
  (star schema: 3 dimensions, 4 facts, 601K scan rows). 49 DAX measures
  documented with formulas and cross-references. `generate_pbix_model.py`
  automates measure injection via pbi-tools (extract → inject JSON →
  compile). BUILD_GUIDE.md covers automated data model setup and manual
  visual assembly. 6 specific Power BI value-adds over Excel documented.
  All export numbers validated against locked actuals.
- **Key decisions:** pbi-tools for measure automation, visual layout
  stays manual (report page JSON is undocumented/brittle). Channel-average
  trade rate methodology (AVG across SKUs per channel, not per-SKU rates).

### Arc 3: SQL diagnostic query library (completed 2026-05-10)
- **Goal:** Extract and document standalone SQL queries from the
  workbook build scripts
- **Outcome:** 25 .sql files across 6 categories (trade_rate,
  deductions, promo_roi, retailer, crosswalk, reconciliation). 17
  extracted from workbook scripts, 6 new gap queries written, 2
  duplicates consolidated, 3 cleaned up. All execute without error.
  36/36 verification checks pass. sql/README.md provides query index,
  10-step analyst walkthrough, and locked numbers reference.
- **Key decisions:** None — this arc was execution, not architecture.

### Arc 2: Workbook build (completed 2026-05-10)
- **Goal:** Build the 7-tab diagnostic Excel workbook
- **Outcome:** All 7 tabs built (Executive Pulse, Leak Diagnostic,
  Promo Efficacy, Retailer Risk, Deduction Ledger, Deduction Code
  Crosswalk, Methodology & Logic). Shared styles module, 8 named
  ranges, print areas, data validation, conditional formatting.
  validate_workbook.py passes 43 checks. Findings surfaced during
  build: 137 ghost promo deductions ($95,826), 292 unmapped codes,
  11-retailer P&L. Minor DB rebuild nondeterminism: ±$1,500 on waste
  rate, ±1 on dispute count — handled by validation tolerances.
- **Key decisions:** rapidfuzz over fuzzywuzzy, separate validation
  script pattern.

### Arc 1: Data generation (completed 2026-05-09)
- **Goal:** Generate unified Cinderhaven trade spend dataset
- **Outcome:** cinderhaven-data repo updated with 21 tables, deduction
  lifecycle merged from retailer-deduction-recovery project, promo_cost
  and funding_mechanism fields added, double-dips seeded, date windows
  aligned. Three downstream repos updated via submodule. Verified
  numbers locked in TRADE_SPEND_VERIFICATION.md.
- **Key decisions:** Two-bucket framing (structural trade + operational
  waste), original brief numbers superseded by verified actuals,
  cinderhaven-data is single source of truth via submodule.

---

## Improvement History

### 2026-09-23 — Audit (health check only)
- **Findings:** 1 critical, 5 important, 5 nice-to-have
- **Top concerns:** Structural trade is understated ~$199K (~0.6pp): workbook/queries.py maps Kroger ($6.6M revenue) to the 7% regional rate even though sku_costs.trade_spend_pct_kroger (10%) exists, which fully explains the "methodology scope" gap vs canonical 9.83%, and the regression test pins the understated value. Branch client-mode-2026-08 carries 12 commits unmerged to main (warehouse adapter + CI) that HANDOFF/PLAN never recorded. scripts/extract_from_postgres.py never uses POSTGRES_PASSWORD (URL has a literal REDACTED placeholder), and warehouse_adapter.py sums 365 days of waste against a shorter revenue window when <52 weeks of scans exist.
- **Action taken:** Audit only — no fixes this session
- **Next review:** 2026-12-22
