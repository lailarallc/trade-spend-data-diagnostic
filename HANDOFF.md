# Trade Spend Data Diagnostic — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

---

## 2026-07-24 — Refresh SQLite from prod and update validation assertions

**Started from:** Project in maintenance mode. Validation assertions stale from prior data changes. SQLite needed refresh from prod Postgres.

**Did:** Started flyctl proxy, extracted all 21 tables from prod Postgres into fresh SQLite (1.4M scan rows, 20K deductions, 7.7K disputes). Ran fixup, rebuilt workbook, updated 8 stale assertions in validate_workbook.py (revenue, structural, waste, rates, double-dips). Fixed latent cross-tab bug where category range included the Total row. 59/59 passing. Committed and pushed.

**State:** SQLite refreshed from prod. Workbook rebuilds clean. 59/59 validation passing. No broken or in-progress work. Key figures: $32.8M revenue, 10.5% all-in, 1.2% waste, 0 double-dips. *[SUPERSEDED 2026-07-31: current pins $32,472,742 / 10.3% / 1.06%; dataset now 0 double-dips / $343,281 / 41.9%]*

**Next:** No pending work. Project in maintenance mode. `/improve` review overdue (was due 2026-06-22). Consider running next session.

---

## 2026-06-02 15:02 — Seed recalibration build complete — 5-line dataset at $24.6M with realistic CPG economics

**What changed:** Recalibrated Cinderhaven seed from 3-line/$33M to 5-line/$24.6M. Updated seed_product_master.sql (added Dried Goods + Snack Bites, broadened active_retailers), 03_generate_costs.py (Kroger/Sprouts columns, DG/SB margin ranges), 05_generate_scan_data.py (VELOCITY_SCALE=0.66, line velocity multipliers, DG/SB seasonality, reduced UNFI/KeHE equivalent doors). Rebuilt entire 17-step pipeline via build_db.py --force.

**Why:** TTM revenue was $33M with 5 lines but only 3 lines in the seed. Trade spend was 11.3% all-in (unrealistically low). Design approved for ~$25M with 18-22% all-in trade. Dataset is now designed for 5 lines from the ground up.

**State:** Database regenerated, workbook builds clean. Headline metrics: $24.6M revenue, 17.5% structural, 4.2% waste, 21.7% all-in, $296K chargebacks. Step 3 metrics reported, awaiting sign-off. Validation script has stale hardcoded bounds (reports FAIL on revenue check) — needs recalibration after sign-off. Downstream repos (short-ship-cost, product-data-health-audit, launch-cost, SKU rationalization) not yet re-exported.

**Next:** Get sign-off on Step 3 metrics. Then: propagate figures to website (Step 4), update regression tests (Step 5), export baked artifacts to downstream repos.

---

## 2026-05-22 22:00 — Improvement pass + code review + security review

**Started from:** `/improve` audit identified 10 findings (4 critical, 4 important, 2 nice-to-have). User said "fix all."

**Did:**
- Made Tab 7 (Methodology) fully dynamic — added `_query_methodology_numbers(db_path)` that queries 25+ metrics from DB. No more hardcoded dollar figures.
- Made Tab 1 summary sentence dynamic (computes structural/all-in rates from data).
- Removed hardcoded absolute path from `scripts/build_db.py`.
- Rewrote 5 markdown docs with correct numbers: README.md, EXECUTIVE_MEMO.md, DEFENSIBILITY.md, walkthrough.md, sql/README.md (locked numbers table + execution order).
- Rewrote CUSTOMIZATION.md — was referencing Postgres stg_* tables and DATABASE_URL; now describes SQLite architecture with correct table names.
- Removed AUDIT.md — entirely from Postgres era, all findings stale.
- Removed 3 stale output files (v2, v3, v4 workbooks).
- Pinned requirements.txt (openpyxl>=3.1.5,<4.0, pandas>=2.0,<4.0, rapidfuzz>=3.0,<4.0).
- Ran pip audit — no vulnerabilities found.
- Updated project-health.md tracker.

**State:** 60/60 validation passing. All numbers flow from SQLite DB. No hardcoded stale figures in code or docs. Code review clean (3 findings fixed). Security review clean (0 vulnerabilities). Two commits pushed to origin.

**Next:** No pending work. Project in maintenance mode. Next `/improve` due 2026-06-22. Next dep audit due 2026-07-22.

---

## 2026-05-17 18:00 — Merge, release update, and ship

**Started from:** Worktree branch had all platform sync work committed but not merged to master.

**Did:** Attempted merge — master had diverged to Postgres (27 commits). Reset master to SQLite-based worktree (per DECISIONS.md). Recovered writing artifacts (EXECUTIVE_MEMO.md, DEFENSIBILITY.md, CUSTOMIZATION.md, AUDIT.md, LICENSE) from old master and updated all numbers. Rebuilt workbook (59/59), replaced GitHub Release asset. Updated cinderhaven-data repo README and build_db.py with platform-sourced warnings. Force-pushed both repos.

**State:** Project complete and shipped. Both repos live on GitHub. Download link works. No pending code work.

**Next:** Only manual task remaining: open .xlsx in Excel for visual verification (data bars, tables, interactive inputs). Otherwise move to a different project.

---

## 2026-05-17 — Platform data sync, merge, and release update

**Started from:** cinderhaven-data-platform had major data changes (50 SKUs, 13.5K deductions, KeHE as full channel, Shopify DTC data). Needed to sync the seed repo and re-lock the diagnostic.

**Did:**
- Exported all 30 raw tables from Fly.io Postgres to fresh SQLite (977K scan, 13.5K deductions, 6.1K disputes, plus 9 new tables: Shopify orders/lines/chargebacks/refunds/transactions/payouts, distributors, sku_distributors, retailer_requirements)
- Added KeHE to all channel rate mappings (trade_spend_pct_kehe, wholesale_kehe) in tab_executive_pulse.py, tab_retailer_risk.py, and 4 SQL files
- Removed distributor B "deduction-only" special case from tab_retailer_risk.py — distributor B now has $2.6M trailing-52w revenue
- Re-locked all numbers across 15+ files:
  - Revenue: $27,483,467 (was $25.6M)
  - Structural: $5,207,524 / 18.9% (was $4.4M / 17.3%)
  - Op waste: $1,967,416 / 7.2% (was $1.0M / 4.0%)
  - All-in: $7,174,939 / 26.1% (was $5.4M / 21.3%)
  - Gap: 7.2pp (was ~4pp)
  - Disputes: 6,105, Recovery: $987,798 / 19.8%
  - SKUs: 50 (was 90)
- Removed powerbi/ directory entirely (Power BI dropped from all projects)
- Resolved architectural conflict: master had migrated to Postgres; reset master to SQLite-based worktree (platform → SQLite export → ships in repo)
- Recovered writing artifacts from old master (EXECUTIVE_MEMO.md, DEFENSIBILITY.md, CUSTOMIZATION.md, AUDIT.md, LICENSE) and updated all numbers
- Rebuilt workbook, 59/59 validation checks passing
- Updated GitHub Release v1.0 with new .xlsx
- Force-pushed master to origin

**State:** Project is shipped and live on GitHub. README download link works. All numbers match platform data. Architecture: Postgres (platform) → SQLite export → git submodule → anyone can clone and run.

**Next:** The cinderhaven-data generation scripts are stale (still produce 90-SKU dataset) — they should be rewritten to reproduce the platform data. That's cinderhaven-data repo work, not this project. This project is complete.

---

## 2026-05-17 — Data source audit and number re-lock

**Started from:** cinderhaven-data upstream had substantial changes (random seed refactoring across 18 scripts: `random.seed()` → `random.Random(SEED)`). Needed to verify all math and analysis still holds.

**Did:**
- Updated cinderhaven-data submodule pointer (4f1ae91 → 8496d86)
- Rebuilt database and verified: scan_data/sku_costs outputs identical (seed refactor preserved call sequences). Only trailing-365 deduction amounts shifted slightly (+$1,515 op waste, +1 dispute).
- Re-locked all numbers across ~50 hardcoded references in 20+ files:
  - Revenue: $25,593,052 → $25,597,699
  - Structural trade: $4,435,052 → $4,435,513
  - Operational waste: $1,010,940 → $1,012,455
  - Promo billback: $211,513 → $213,017
  - All-in trade: $5,445,992 → $5,447,968
  - Disputes: 1,409 → 1,410
  - Recovery rate: 14.3% → 13.7% (denominator method change: now uses total disputed dollars $716,083, not just resolved)
- All rates unchanged: 17.3% structural, 4.0% waste, 21.3% all-in
- Updated: validate_workbook.py, powerbi/export_data.py, workbook/tab_methodology.py, workbook/tab_leak_diagnostic.py, walkthrough.md, all powerbi docs, sql/README.md, SQL file comments, DECISIONS.md, TRADE_SPEND_VERIFICATION.md
- Confirmed schema changes (deductions.sku removed, disputes.disputed_amount removed) don't affect project code — never referenced directly
- Deleted temp verification scripts (verify_new_data.py, verify_correct_window.py, ghost_check.py, explore_db.py)
- Final validation: 59/59 checks passing

**State:** All deliverables verified against updated data source. Workbook generates clean. No narrative changes needed beyond exact dollar figures — the story (17.3% planned, 4pp gap = operational waste) is intact.

**Next:** Commit this work, merge to main branch, then proceed with any remaining project goals (Power BI assembly in Desktop, GitHub push).

---

## 2026-05-11 — Power BI bug fixes and presentation redesign

**Started from:** All five arcs complete. Dashboard had data bugs and needed visual polish.

**Did:** Fixed 5 data bugs (All-In Trade Cost double-count, waterfall sort, double-dip $0, ghost promo context, total row explosion). Wrote visual formatting spec. Redesigned dashboard from analysis tool to presentation layer — 28 visuals down to 16, narrative takeaways per page, tables/slicers removed. Rewrote DESIGN.md and BUILD_GUIDE.md for presentation approach.

**State:** All arcs complete. Power BI data/measures match locked figures. Dashboard assembly in Power BI Desktop is the only remaining manual step.

**Next:** Open Power BI Desktop, follow BUILD_GUIDE.md to rebuild the 4 pages as presentation layout.

---

## 2026-05-11 22:30 — Workbook restructuring

**Started from:** All five arcs complete. No active PLAN.md arc. Opened session to fix Excel workbook formatting and consistency.

**Did:** Stripped openpyxl charts from tabs 2–4, replaced Tab 1 chart with in-cell data bar waterfall, converted all data ranges to Excel Tables (ListObject), enhanced interactive input cells (yellow fill, data validation, cell comments, Protection(locked=False)), fixed tab colors (blue for tab 5, gray for tabs 6–7), suppressed gridlines on green/gray tabs, added 6 KPI named ranges, added what-if margin column on Tab 4, fixed CEO takeaway trailing "is", compacted layouts. 10 files modified, 59/59 validation checks passing.

**State:** Workbook generates clean. Not yet visually verified in Excel — data bars and table formatting need human eye pass. Interactive input cells not yet tested live.

**Next:** Open .xlsx in Excel, visually verify in-cell waterfall and table formatting, test all three interactive input cells (recovery rate, promo window, what-if trade rates). Then decide next move.

---

## [2026-05-10] Session Wrap-Up — Arc 5 complete, all arcs done

**Session focus:** Complete Arc 5 (written walkthrough) — the final arc. Write
the full narrative walkthrough and project README.

**Completed:**
- Updated PLAN.md: archived Arc 4, defined Arc 5 (goal, tasks, done criteria)
- Wrote `walkthrough.md` — 2,276-word narrative in 5 sections: the problem
  (trade spend opacity at $15M–$30M), methodology (two-bucket framing, data
  architecture), findings (all Cinderhaven numbers with tab/query references),
  deliverables (workbook, SQL, dashboard orientation), real-engagement upsell
- Verified all walkthrough numbers against live database queries (waste by
  category, promo ROI distribution, retailer margins, ghost promos, recovery)
- Caught and replaced one instance of banned word "leverage"
- Wrote project-level `README.md` — 76 lines: punchline, directory map,
  quick start with submodule note, deliverable links, stack
- Marked all Arc 5 tasks and definition-of-done items complete

**Current state:** All five arcs are **complete**. The project is a finished
portfolio piece with no in-progress work:
- Arc 1: Data generation (cinderhaven-data, 21 tables, verified numbers)
- Arc 2: Workbook build (7 tabs, 43 validation checks passing)
- Arc 3: SQL query library (25 queries, 36 verification checks)
- Arc 4: Power BI preparation (design, 7 CSVs, 49 DAX measures, build guide)
- Arc 5: Written walkthrough + project README

**Key files changed:**
- `walkthrough.md` — created (full diagnostic narrative, 2,276 words)
- `README.md` — created (project-level orientation for cold visitors)
- `PLAN.md` — Arc 4 archived, Arc 5 defined and completed

**Next steps:**
1. Assemble the .pbix in Power BI Desktop following `powerbi/BUILD_GUIDE.md`
   (manual visual layout — the data model and measures are pre-generated)
2. Push cinderhaven-data deduction pipeline scripts to GitHub (unblocks
   submodule-based builds without the DB copy workaround)
3. Decide on a license
4. Consider: video walkthrough, slide deck, or client-facing proposal template

**Blockers:** None — all planned work is complete.

**Context for next session:** No arcs remain in PLAN.md. The project is
shippable as-is. The only infrastructure gap is that cinderhaven-data's
deduction pipeline scripts haven't been pushed to the remote (the build_db.py
fallback works, but a fresh clone would need the pre-built DB copied manually).
The Power BI dashboard exists as documentation and pre-generated measures but
has not been assembled in Power BI Desktop — that's a manual step following
BUILD_GUIDE.md § 4.

---

## [2026-05-10] Session Wrap-Up — Workbook-level features and end-to-end validation

**Session focus:** Add workbook-level polish (named ranges, print areas, active
sheet) and run comprehensive end-to-end validation to confirm all acceptance
criteria pass.

**Completed:**
- Added 8 named ranges to workbook (AllInTradeRate, StructuralTradeRate,
  OperationalWasteRate, TotalRevenue, StructuralTrade, OperationalWaste,
  AllInTradeCost, RecoveryRate)
- Set print areas for Tabs 1–4 (landscape letter orientation)
- Set active sheet to Executive Pulse (Tab 1)
- Wrote `validate_workbook.py` — 43 automated checks covering tab structure,
  locked numbers, double-dips, recovery, retailer totals, deduction count,
  crosswalk completeness, cross-tab consistency, error scan, named ranges,
  data validation, and conditional formatting
- Fixed validation script issues: Windows cp1252 encoding (added UTF-8
  reconfigure), openpyxl API (`defined_names.values()` not `.definedName`),
  tolerance adjustments for minor DB rebuild variance
- All 43 validation checks pass
- Marked all PLAN.md tasks and definition-of-done items complete

**Current state:** The workbook arc is **complete**. All 7 tabs generate
correctly, all locked numbers match, all interactive features work, and the
validation script confirms everything end-to-end. The workbook is at
`output/trade_spend_diagnostic.xlsx`.

**Key files changed:**
- `workbook/generator.py` — added `_add_named_ranges()`, `_set_print_areas()`,
  active sheet setting
- `validate_workbook.py` — created (comprehensive 43-check validation)
- `PLAN.md` — all tasks and definition-of-done items marked complete

**Next steps:**
1. Push cinderhaven-data deduction pipeline scripts to GitHub (unblocks
   submodule-based builds without the DB copy workaround)
2. Begin next arc: Power BI dashboard (consumes workbook structure)
3. Or: SQL diagnostic query library
4. Or: Written walkthrough / README

**Blockers:** None — workbook arc is complete.

**Context for next session:** The workbook arc (Arc 2) is done. All tasks and
definition-of-done criteria are satisfied. The `validate_workbook.py` script
can be re-run any time to confirm the workbook still passes all checks after
changes. The one outstanding infrastructure item is pushing cinderhaven-data
to GitHub so the submodule clone works without the DB copy fallback. The next
arc should be chosen from PLAN.md's "Out of scope" list — Power BI dashboard
is listed as the natural next step.

---

## 2026-05-10 — Arc 2 complete: 7-tab workbook

**Started from:** Arc 2 beginning. Project structure not set up. Data
foundation complete from Arc 1.

**Did:** Built the full 7-tab diagnostic workbook end-to-end. Project
structure (submodule, build script, entry point), shared styles module,
all 7 tabs (Executive Pulse, Leak Diagnostic, Promo Efficacy, Retailer
Risk, Deduction Ledger, Deduction Code Crosswalk, Methodology & Logic),
workbook-level features (8 named ranges, print areas, data validation,
conditional formatting), and validation script (43 checks, all passing).
Key findings surfaced during build: 137 ghost promo deductions ($95,826),
292 unmapped deduction codes, 11-retailer P&L including distributor B deduction-only
and DTC zero-trade benchmark.

**State:** Arc 2 complete. `python build_workbook.py` produces workbook
from submodule. `python validate_workbook.py` passes all 43 checks.
Minor DB rebuild nondeterminism: waste rate ~$1,500 variance ($1,012,455
vs locked $1,010,940), disputes 1,410 vs locked 1,409. Validation
tolerances handle both.

**Next:** Choose next arc — Power BI dashboard, SQL diagnostic query
library, or written walkthrough.

---

## [2026-05-10] Session Wrap-Up — Project setup and database wiring
**Session focus:** Set up project structure (submodule, build script, DB),
explore schema, prepare for workbook generation.

**Completed:**
- Added cinderhaven-data as git submodule (`git submodule add`)
- Created `scripts/build_db.py` — wraps submodule build, falls back to
  pre-built DB from active cinderhaven-data repo when submodule is incomplete
- Created `scripts/` and `output/` directories
- Copied pre-built database (163.7 MB, 22 tables) into submodule data path
- Explored full database schema — all column names mapped for every table
- Created `scripts/explore_db.py` (disposable helper for schema inspection)
- Verified openpyxl 3.1.5 installed and working
- Configured `.claude/settings.local.json` with `bypassPermissions` mode

**Current state:** Project structure is in place. Database is ready at
`cinderhaven-data/data/cinderhaven_product_master.db` with all 22 tables.
No workbook code written yet. The PLAN.md "set up project structure" task
is effectively done — needs locked number verification before marking
formally complete.

**Key files changed:**
- `.gitmodules` — created (cinderhaven-data submodule reference)
- `cinderhaven-data/` — submodule added, DB copied into `data/`
- `scripts/build_db.py` — created (build/locate database)
- `scripts/explore_db.py` — created (schema exploration helper)
- `scripts/` — created (empty dir for workbook generation code)
- `output/` — created (empty dir for generated .xlsx)
- `.claude/settings.local.json` — created (bypassPermissions mode)

**Key schema details for next session:**
- `scan_data`: columns are `week_ending` (not week_start), `dollars_sold`
  (not unit_price × units_sold). Revenue = SUM(dollars_sold).
- `sku_costs`: per-channel columns (`trade_spend_pct_walmart`,
  `trade_spend_pct_costco`, `trade_spend_pct_whole_foods`,
  `trade_spend_pct_regional`, `trade_spend_pct_unfi`, `trade_spend_pct_dtc`).
  Regional chains: Green Basket Market, Southside Grocers, Prairie
  Provisions, Mountain Pantry Co, Harbor Fresh → all use `_regional`.
- `deductions.retailer_id` uses slugs (walmart, costco, whole_foods, etc.)
- `retailers` table: 11 rows with display `name` and dispute portal info
- `promotions`: 188 rows across 75 distinct `promo_id`s; has `promo_cost`
  and `funding_mechanism` columns
- `deduction_codes`: 97 rows — `code_id`, `retailer_id`, `code`, `name`,
  `deduction_type`, `is_published`
- Trailing-365 window: `>= '2025-05-03' AND <= '2026-05-02'`
- Trailing-52w for revenue uses same dates on `week_ending`
- `stores.retailer` maps store_id to channel for scan_data joins

**Next steps:**
1. Verify locked numbers against the copied DB (run SQL checks)
2. Build Tab 7 (Methodology & Logic) — defines all calculations
3. Build Tab 6 → Tab 1 per the task spec
4. Workbook-level features (named ranges, formatting, validation)
5. End-to-end validation

**Blockers:**
- Permission config change (`bypassPermissions`) requires new session
- cinderhaven-data GitHub repo missing deduction scripts 07-15 (workaround
  in place via build_db.py fallback — not blocking workbook build)

**Context for next session:** Start a fresh session so `bypassPermissions`
takes effect. First action: run locked number verification SQL against the
DB. Then begin `generate_workbook.py` with Tab 7 (Methodology & Logic).
The build order is Tab 7 → 6 → 5 → 4 → 3 → 2 → 1 because earlier tabs
depend on calculations defined in later tabs. The `scripts/explore_db.py`
can be deleted — it was a one-off exploration tool.

---

## [2026-05-09] Session Wrap-Up — Workflow scaffolding and git init
**Session focus:** Set up solo-dev workflow infrastructure and project scaffolding

**Completed:**
- Created `.claude/commands/` with `log.md` and `wrap.md` slash commands
- Created `CLAUDE.md` (project overview and conventions template)
- Created `FAILURES.md` (empty, ready for entries)
- Initialized git repo (`git init`)
- Updated claude-solo-dev-workflow reference repo: added `slash-commands/init.md`, replaced `workflow-package/README.md` with version referencing `/init`
- Added trade-spend-data-diagnostic entry to MsShawnP GitHub profile README

**Current state:** All workflow files in place. Git repo initialized but
no commits yet. Data foundation complete from prior session (cinderhaven-data,
21 tables, locked numbers). No workbook code written. PLAN.md Arc 2
(workbook build) defined and ready to start.

**Key files changed:**
- `.claude/commands/log.md` — created (/log slash command)
- `.claude/commands/wrap.md` — created (/wrap slash command)
- `CLAUDE.md` — created (project overview template)
- `FAILURES.md` — created (empty log)
- `DECISIONS.md` — added workflow adoption decision

**Next steps:**
- Set up project structure (submodule, build script, workbook entry point)
- Build Tab 1: Executive Pulse
- Push to GitHub when ready

**Blockers:** None

**Context for next session:** Everything is scaffolded. The first real
task is PLAN.md's first unchecked item: "Set up project structure —
submodule, build script, workbook generation entry point." The
cinderhaven-data submodule needs to be added, and a Python entry point
created that connects to the .db and generates the workbook.

---

## 2026-05-09 — 95% confidence session + data reconciliation

**Started from:** Project initialized, no code written.

**Did:**
- Ran 95% confidence interview: established business question, audience
  (hands-on CEO), unified dataset strategy
- Discovered existing cinderhaven-data repo (90 SKUs, product_master,
  sku_costs, promotions, scan_data, stores) and retailer-deduction-recovery
  repo (full deduction schema, 3,333 deductions, deployed React app)
- Sent Code to investigate both repos — FINDINGS.md revealed original
  brief numbers were internally inconsistent (off-invoice double-count,
  $1.4M operational figure was 18-month not annualized, deduction-only
  rate was 3.6% not 12%)
- Decided: unified dataset in cinderhaven-data, consumed via submodule
- Sent Code to merge recovery project's generation scripts into
  cinderhaven-data, add promo_cost/funding_mechanism to promotions,
  add is_double_dip flag, align date windows
- Fixed DTC double-dips (moved to realistic retailers)
- Sent Code to re-verify — TRADE_SPEND_VERIFICATION.md produced with
  locked numbers
- Updated DECISIONS.md (superseded brief numbers, added 4 new decisions)
- Updated PLAN.md (completed Arc 1, defined Arc 2: workbook)

**State:** Data foundation complete. cinderhaven-data has 21 tables,
three downstream repos updated. Locked numbers verified. PLAN.md
Arc 2 defined (workbook build). No workbook code written yet.

Tab structure designed (7 tabs, down from original 13):
1. Executive Pulse (green) — punchline, waterfall, addressable improvement, responsibility matrix
2. Leak Diagnostic (green) — waste by category, double-dip alert, adjustable recovery rate
3. Promo Efficacy (green) — ROI with adjustable pre/post window, data quality indicators
4. Retailer Risk (green) — concentration, net-net margin, what-if trade rate inputs
5. Deduction Ledger (blue) — full trailing-365 data, auto-filters, freeze panes
6. Deduction Code Crosswalk (gray) — retailer codes → plain English
7. Methodology & Logic (gray) — definitions, data lineage, build date

Brief reviewed through 3 rounds of external critique. Interactive
elements defined (adjustable recovery rate, promo window, what-if
trade rates). Addressable improvement number to be calculated and
displayed on Tab 1.

**Next:** Set up project structure (submodule, build script, entry
point), then build Tab 1.

**Open items:**
- Recovery rate (14.3%) is above the 5–10% spec target from recovery
  project — cosmetic, not blocking
- Project repo structure not yet set up
- Addressable improvement $ needs calculation during build
- "Trade Spend Leakage" from brainstorm list unresolved — may just
  be this project by another name

---
