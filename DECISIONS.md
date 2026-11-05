# Trade Spend Data Diagnostic — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-05-09 — Adopt solo-dev workflow with /log, /wrap, /init slash commands
- **Why:** Project needs session continuity across multiple work sessions.
  The solo-dev workflow (from claude-solo-dev-workflow repo) provides
  structured handoff via five tracking files (CLAUDE.md, PLAN.md,
  HANDOFF.md, DECISIONS.md, FAILURES.md) and three slash commands
  (/log for mid-session entries, /wrap for end-of-session summaries,
  /init for new project scaffolding). Keeps context recoverable without
  relying on conversation history.
- **Scope:** Global — project process, all sessions
- **Do not:** Skip /wrap at end of session. The handoff log is what
  makes the next session productive immediately.

### 2026-05-09 — Use openpyxl for Excel workbook generation, not xlsxwriter
- **Why:** Brief specifies openpyxl. Both are viable — xlsxwriter is
  faster for write-only workbooks but openpyxl supports read/write,
  which matters if the workbook needs to be modified after generation.
  openpyxl also handles data validation and conditional formatting well.
  Decision may be revisited if openpyxl proves too slow for the 13-tab
  workbook.
- **Scope:** Excel workbook generation
- **Do not:** Use xlsxwriter unless openpyxl hits a blocking limitation.

### 2026-05-09 — Use SQLite as the project database, not PostgreSQL or DuckDB
- **Why:** Brief specifies SQLite. The dataset is small (~thousands of
  rows across all tables). SQLite is zero-config, ships with Python,
  and the .db file can live in the repo. No need for a server.
- **Scope:** Global
- **Do not:** Over-engineer the schema for a dataset this size.

### 2026-05-17 — Sync cinderhaven-data from cinderhaven-data-platform Postgres, not generate in place
- **Why:** The platform (Fly.io Postgres, dbt pipeline) is the authoritative
  data source. It grew to 50 SKUs (from 90), 13.5K deductions (from 3K),
  6K disputes, Shopify DTC data, KeHE as a full retail channel, and an
  extended scan window through 2027-01-02. Rather than rewriting 18
  generation scripts, we exported the platform's raw tables directly to
  SQLite. The generation scripts in cinderhaven-data are now stale — the
  exported .db is the source of truth until scripts are updated.
- **Scope:** cinderhaven-data submodule, data pipeline
- **Do not:** Switch the diagnostic project itself to Postgres. SQLite
  stays — it's portable, free, and works offline. The platform is the
  upstream; SQLite is the local format.

### 2026-05-17 — Reset master to SQLite after conflicting Postgres migration
- **Why:** A prior session migrated the diagnostic to Postgres (`stg_*` tables,
  psycopg2, `DATABASE_URL`). This contradicted the explicit decision to keep
  SQLite for portability. Master was reset to the SQLite-based worktree branch;
  writing artifacts recovered selectively. The Postgres code is preserved at
  `backup/master-before-reset` but is not the active architecture.
- **Scope:** Global — project architecture, all code paths
- **Do not:** Re-attempt a Postgres migration for this project. The platform is
  upstream; SQLite is the distribution format. If the data needs refreshing,
  re-export from platform to SQLite.

### 2026-05-17 — Remove Power BI from all projects
- **Why:** User decision. Power BI deliverables dropped across all
  Lailara projects. The powerbi/ directory and all references removed.
- **Scope:** Global — this project and all Lailara projects
- **Do not:** Reference Power BI work as a deliverable or next step.

### 2026-05-10 — Validate deliverables with a separate verification script, not inline assertions
- **Why:** `validate_workbook.py` reopens the generated .xlsx and checks it
  as a reader would — locked numbers, cross-tab consistency, tab structure,
  no formula errors. Separate from the build so validation runs against the
  actual output file, not in-memory state. Also serves as living documentation
  of acceptance criteria. Tolerances (±$2,000 on dollar amounts, ±2 on counts)
  handle DB rebuild nondeterminism.
- **Scope:** Workbook generation, future deliverables (dashboard, SQL queries)
- **Do not:** Embed validation in the build script. Keep build and verify as
  separate steps.

### 2026-05-10 — Use rapidfuzz, not fuzzywuzzy, for fuzzy matching
- **Why:** Faster, MIT-licensed (fuzzywuzzy is GPL), drop-in compatible API.
  No reason to use fuzzywuzzy unless rapidfuzz hits a blocking issue.
- **Scope:** requirements.txt, any fuzzy matching code
- **Do not:** Use fuzzywuzzy unless rapidfuzz has a specific incompatibility.

### 2026-05-09 — Consume cinderhaven-data via git submodule, do not duplicate data
- **Why:** cinderhaven-data is the single source of truth (21 tables,
  unified build pipeline). Three downstream repos consume it via
  submodule. Duplicating data creates drift. This project builds the
  database by running cinderhaven-data's build_db.py, then adds its
  own analysis/workbook layers on top.
- **Scope:** Global — project setup, CI, build scripts
- **Do not:** Copy data files or generation scripts into this repo.
  All data generation lives in cinderhaven-data.

### 2026-05-09 — Use two-bucket executive framing, not three-bucket
- **Why:** The 95% confidence investigation found that "off-invoice"
  is a funding mechanism, not a separate category — putting it in its
  own bucket double-counts. The promotions table's promo_cost sum
  ($20K) is too small to be a meaningful standalone bucket. The data
  supports two clean buckets:
  - Structural/planned trade: $3.0M (9.2%) — the negotiated rate-card
  - Operational waste: ~$977K (3.0%) — deductions beyond planned trade
  All-in: ~$3.98M (12.2%). CEO takeaway: "Your structural rate is
  competitive. ~$965K in operational waste is buried in the deductions."
- **Scope:** Executive summary tab, dashboard, walkthrough
- **Do not:** Use a three-bucket model unless the data is extended to
  support it. The detail tabs can break out deduction types and
  funding mechanisms — the executive summary stays two-bucket.

### 2026-05-09 — Audience is a hands-on CEO, not a controller
- **Why:** The immediate prospect's CEO likes Excel, vlookups, playing
  with data — but also wants quick answers. The workbook needs a
  dashboard/summary tab up front with the punchline, then detail tabs
  structured for self-service exploration. Both levels must work.
- **Scope:** Excel workbook tab ordering, README tab, summary tab design
- **Do not:** Bury the headline in tab 7. Lead with the answer.

### 2026-06-02 — Cinderhaven 5-line seed calibration targets
- **Why:** Original 3-line seed at VELOCITY_SCALE=1.21 produced $33M TTM — incompatible with "$25M brand" description. Trade rates were flat and unrealistically low (11.3% all-in). Designed from ground up for 5 lines at realistic CPG economics.
- **Scope:** All cinderhaven-data generation scripts, all downstream repos that consume the dataset, all website figures.
- **Key parameters:** VELOCITY_SCALE=0.66, AS=1.30/PS=1.10/SC=1.00/DG=0.90/SB=0.85, UNFI=40 doors, KeHE=25, trade rates per-channel (Walmart 18-25%, Costco 15-20%, Kroger 16-22%, WFM 10-15%, Sprouts 12-16%, Regional 8-12%, UNFI 12-18%, KeHE 10-16%, DTC 0%).
- **Do not:** Change VELOCITY_SCALE or line multipliers without re-running the full pipeline and reporting all headline metrics. Do not propagate figures until sign-off.

---

## Data & Schema

### ~~2026-05-09 — Simulated data must hit specific target numbers from the brief~~
~~Original targets: 19.2% true trade rate, 16.8% deduction-only, ~$340K
off-invoice, $4.5M total trade, 42/38/20 category split.~~
**Superseded by 2026-05-09 entry below — verified numbers replace brief targets.**

### ~~2026-05-09 — Use verified numbers from unified cinderhaven-data build, not original brief targets~~
~~Verified numbers from v1 build: Revenue $27.5M, Structural 18.9%, Operational 7.2%, All-in 26.1%.~~
**Superseded 2026-06-05: v2 canonical reconciliation locked new baseline (see remittance-stub-parsing DECISIONS.md), then distressed scenario adopted for this diagnostic.**

### 2026-06-05 — Diagnostic consumes the distressed scenario dataset (not v2 baseline)

*[SUPERSEDED 2026-07-31: current pins $32,472,742 / 10.3% / 1.06%; dataset now 0 double-dips / $343,281 / 41.9%. The distressed key figures below ($977K waste, 3 double-dips, 20.9% recovery) no longer describe the shipped dataset — the 2026-06-30 regen and 2026-07-24 prod re-export replaced them.]*

- **Why:** The v2 canonical data ($480K/yr waste, 44% recovery, 0 vague, 0 double-dips) makes the diagnostic's exposé narrative impossible — the baseline is too clean. Rather than re-baselining all 11+ portfolio pieces, a named distressed scenario generates an alternate deduction layer consumed only by this diagnostic. Baseline tables (revenue, structural trade, chargebacks) are unchanged.
- **Scope:** All deliverables in this repo — workbook, walkthrough, EXECUTIVE_MEMO, DEFENSIBILITY, SQL queries
- **Key figures (distressed):**
  - Trailing-52w scan revenue: $32.5M (unchanged)
  - Structural trade: $3.0M / 9.2% (unchanged)
  - Operational waste: ~$977K trailing-365 (~$965K/yr), 3.0% of scan revenue
  - Vague: 318 trailing-365 / $417K (43% of waste), 33% no-PO
  - Double-dips: 3 / $19,062
  - Ghost promos: 3,258 / $361K
  - Disputes: 5,395 filed, $232K recovered, 20.9% recovery
- **Narrative pivot:** Rate-gap framing is dead (v2 all-in ~12.2% is under any budget). Story is now waste-magnitude: "the money isn't in a bloated rate; it's in the noise no one has time to fight."
- **Do not:** Use $1.13M, 20.4%, 3.8-point gap, 18.6% recovery, 405 ghost promos, 3,581 disputes, or any rate-gap framing. All are dead.

### 2026-05-09 — Build realistic quirks into simulated data sources
- **Why:** The credibility of the diagnostic depends on the data looking
  like what a controller actually deals with — inconsistent naming
  ("WFM" vs. "Whole Foods"), missing reason codes, date format
  mismatches, deduction dates lagging promo dates by 30–90 days. Clean
  data would make the matching trivial and the diagnostic pointless.
- **Scope:** All data generation scripts
- **Do not:** Make the quirks so extreme that matching becomes impossible.
  Target: ~68% clean match, ~23% internal inconsistency rate.

---

## Visualization

### 2026-05-10 — Automate DAX measure injection via pbi-tools, keep visual layout manual
- **Why:** The dashboard has 49 measures — entering them by hand is
  tedious and error-prone. pbi-tools can extract a .pbix into a folder
  structure, inject measure JSON files, and recompile. This automates
  the data model layer. Visual layout (positioning, slicers, formatting)
  cannot be reliably automated via pbi-tools — the report page JSON
  is undocumented and brittle. Honest split: measures automated,
  visuals manual.
- **Scope:** Power BI dashboard build workflow
- **Do not:** Attempt to generate visual layout JSON via pbi-tools.
  If pbi-tools is unavailable, measures can be created manually using
  `DAX_MEASURES.md` formulas.

---

## Output Formats

### 2026-05-09 — Excel workbook uses color-coded tabs: blue for input, green for output, gray for reference
- **Why:** Brief specifies clear input/output/reference tab separation.
  Color-coding is the fastest visual signal for a controller opening
  the workbook cold. Standard convention in financial workbooks.
- **Scope:** Excel workbook
- **Do not:** Use decorative colors or brand colors. Function over
  aesthetics.

### 2026-05-09 — Promo ROI uses simple pre/during/post methodology, not baseline modeling
- **Why:** Brief explicitly scopes this. Baseline modeling (seasonality
  adjustment, causal inference) is engagement-level work. Simple
  comparison with a stated assumption is sufficient for the portfolio
  piece and honest about its limitations.
- **Scope:** Promo ROI calculator tab and any ROI-related analysis
- **Do not:** Build sophisticated baseline models. Acknowledge the
  limitation in the documentation.

### 2026-05-11 — Workbook is a data tool, not a dashboard. No openpyxl charts.
- **Why:** openpyxl charts are basic and send mixed signals next to
  controller-grade data. Power BI handles visualization. The workbook
  handles exploration — Excel Tables (pivot-ready), interactive input
  cells, named ranges. A CEO who right-clicks and gets "Summarize with
  PivotTable" trusts the tool.
- **Scope:** Excel workbook generation, all tabs
- **Do not:** Add openpyxl chart objects back. The one visual element
  is the in-cell data bar waterfall on Tab 1.

### 2026-11-05: Workbook cells show trade-partner labels, not real names
- **Decision:** Write every retailer/distributor name or ID into a cell
  through `workbook/labels.py`, which reads the vendored
  `reference/retailer_display_labels.json`.
- **Why:** Owner rule 2026-11-05 (lailara-website DECISIONS): a
  Cinderhaven dollar figure never shares a row with a real partner name.
  The workbook is served publicly at `/tools/trade-spend-diagnostic.xlsx`
  and failed the gate with 128 violations. The Code Crosswalk tab carries
  no dollar figures, but its synthetic codes join 1:1 to the Ledger rows,
  so a real name there would de-anonymize every ledger dollar; it is
  relabeled too and sorted by label so the real names' order does not
  leak. `RET-REGIONAL` displays as "Regional Group" (label equals name).
  Queries, IDs, data keys and computations keep the real names.
- **Scope:** Every cell that shows a partner: Retailer Risk (P&L,
  concentration, what-if tables), Promo Efficacy (promo table, ghost
  promos), Leak Diagnostic (double-dip alert), Deduction Ledger (Retailer
  and Remittance Desc columns), Deduction Code Crosswalk (Retailer column
  and sort), Methodology (GM example sentence).
- **Do not:** Write `retailer`, `retailer_id`, `r["name"]`, or a
  hardcoded partner name into a cell, comment, sheet title, or table
  without `display_name()` / `relabel_text()`. Gate the dumped workbook
  with `scripts/check_retailer_labels.py` before publishing.

---

## Writing & Voice

[No entries yet — will be populated when walkthrough arc begins]

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
