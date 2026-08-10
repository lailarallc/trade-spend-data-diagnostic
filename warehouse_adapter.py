"""Client-warehouse adapter — the reference pattern for connecting a paid
diagnostic to a client's own data warehouse.

This is deliberately the reference implementation the rest of Wave 2 copies. Two
principles:

1. **No hardcoded schema.** Every table and column name is read from the
   ``warehouse:`` block of ``engagement.yml`` — there is not one Cinderhaven
   table name in this file. Point it at a different warehouse by editing config.

2. **One vocabulary.** The pulled rows go through the SAME
   ``lailara_engagement`` POS specs and the SAME required declarations
   (``week_convention``, ``scan_basis``) as the CSV client mode — via
   ``read_records`` (a DB cursor's ``fetchall()`` becomes a ReadResult) — instead
   of inventing a parallel warehouse vocabulary. A mislabeled week grid or an
   unlabeled dollar basis is caught here exactly as it is for a file.

It connects (SQLite for the demo; any DB-API 2.0 connection works the same way),
pulls the scans and deductions tables by their config-mapped names, validates
them, and produces a branded, provenance-footed **Warehouse Trade-Spend
Readiness** summary — trailing-52-week scan revenue (basis-labeled) and
operational-waste rate — or a Data Readiness Report if the schema map is wrong.

Usage:
    python warehouse_adapter.py --config engagement.warehouse.yml [--out client-output] [--final]
"""

from __future__ import annotations

import argparse
import contextlib
import html
import sqlite3
from pathlib import Path

import pandas as pd

from lailara_engagement import (
    ColumnSpec,
    PreflightSpec,
    build_provenance,
    load_config,
    pos,
    read_records,
    run_preflight,
    validation_status_label,
    write_report,
)
from lailara_engagement import palette as P
from lailara_engagement.provenance import Provenance

TOOL = "trade-spend-data-diagnostic"
TOOL_VERSION = "1.0"


def _deductions_spec() -> PreflightSpec:
    return PreflightSpec(tool=TOOL, version=TOOL_VERSION, columns=[
        ColumnSpec(name="deduction_id", dtype="identifier", required=True, unique=True,
                   spec_ref="INPUT-SPEC §Deductions"),
        ColumnSpec(name="deduction_type", dtype="string", required=True, spec_ref="INPUT-SPEC §Deductions"),
        ColumnSpec(name="amount", dtype="number", required=True, not_negative=True,
                   spec_ref="INPUT-SPEC §Deductions"),
        ColumnSpec(name="deduction_date", dtype="date", required=True, spec_ref="INPUT-SPEC §Deductions"),
    ])


def _connect(warehouse: dict):
    kind = (warehouse.get("kind") or "sqlite").lower()
    if kind != "sqlite":
        # A different warehouse just needs a DB-API 2.0 connection here; the rest
        # of the adapter is driver-agnostic. Kept to sqlite for the demo.
        raise SystemExit(f"warehouse.kind {kind!r} not wired in this demo; pass a sqlite path.")
    path = warehouse.get("path")
    if not path or not Path(path).exists():
        raise SystemExit(f"warehouse.path not found: {path!r}")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def _pull(conn, table: str, colmap: dict[str, str]):
    """Config-driven SELECT: fetch client columns aliased to canonical names."""
    canon = list(colmap.keys())
    select = ", ".join(f'"{colmap[c]}" AS "{c}"' for c in canon)
    rows = conn.execute(f'SELECT {select} FROM "{table}"').fetchall()  # noqa: S608 (names from trusted config)
    return read_records(rows, canon, name=f"{table} (warehouse)")


def _fmt_dollars(v):
    return "—" if v is None else f"${v:,.0f}"


def run(config_path: str, out_dir: str, *, final: bool = False) -> dict:
    config = load_config(config_path)
    warehouse = config.raw.get("warehouse") or {}
    tables = warehouse.get("tables") or {}
    columns = warehouse.get("columns") or {}
    if "scans" not in tables or "deductions" not in tables:
        raise SystemExit("engagement.yml `warehouse.tables` must map `scans` and `deductions`.")

    week_conv_name, _wd = pos.resolve_week_convention(config)
    scan_basis = pos.resolve_scan_basis(config)
    basis_word = pos.scan_basis_label(scan_basis)

    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)

    with contextlib.closing(_connect(warehouse)) as conn:
        scan_read = _pull(conn, tables["scans"], columns.get("scans") or {
            c: c for c in ("store_id", "sku", "week_ending", "units_sold", "dollars_sold")})
        ded_read = _pull(conn, tables["deductions"], columns.get("deductions") or {
            c: c for c in ("deduction_id", "deduction_type", "amount", "deduction_date")})

    scan_report, scan_frame = pos.intake(
        scan_read, pos.scan_spec(tool=TOOL, version=TOOL_VERSION, week_convention=week_conv_name), config)
    ded_report = run_preflight(ded_read, _deductions_spec(), config)
    scan_report.disclosures.extend(pos.declared_disclosures(week_conv_name, scan_basis))

    reports = {"scans": scan_report, "deductions": ded_report}
    blocked = {k: r for k, r in reports.items() if not r.passed}
    provenance = build_provenance(
        tool=TOOL, tool_version=TOOL_VERSION, inputs=[scan_read, ded_read], config=config,
        validation_status=validation_status_label("failed" if blocked else "clean",
                                                   sum(r.n_warnings for r in reports.values())),
        extra={"Source": f"warehouse ({warehouse.get('kind', 'sqlite')})",
               "Week convention": week_conv_name, "Scan basis": f"{basis_word} dollars"})
    if blocked:
        written = {}
        for key, report in blocked.items():
            p = write_report(report, config, str(out), provenance=provenance, draft=not final,
                             basename=f"data-readiness-{key}",
                             title=f"Warehouse Data Readiness Report — {key}")
            written[key] = p["html"]
        return {"status": "blocked", "blocked_files": list(blocked), "readiness_reports": written}

    # Trailing-52-week scan revenue (basis = scan_basis), from the validated frame.
    # When fewer than 52 weeks are present the window clamps to what exists — and
    # every window LABEL below reports the ACTUAL coverage, never a hardcoded
    # "52 weeks" / "365d" over a shorter span (that would misstate the window a
    # money figure is quoted against).
    weeks = sorted(scan_frame["week_ending"].dropna().unique())
    n_weeks = min(52, len(weeks))
    oldest = weeks[-n_weeks]
    max_week = weeks[-1]
    max_ts = pd.Timestamp(max_week)
    in_window = scan_frame[scan_frame["week_ending"] >= oldest]
    revenue = round(float(in_window["dollars_sold"].sum()), 2)

    # Operational waste: trailing-365d deductions, excluding promo billback. The
    # cutoff is unchanged (every deduction inside the trailing year is counted);
    # only the LABEL clamps to the actual span when < 1 year of data exists.
    ded = pos.to_frame(ded_read, ded_report, _deductions_spec())
    cutoff = max_ts - pd.Timedelta(days=365)
    dwin = ded[(ded["deduction_date"] > cutoff) & (ded["deduction_date"] <= max_ts)
               & (ded["deduction_type"].str.lower() != "promo_billback")]
    waste = round(float(dwin["amount"].sum()), 2)
    waste_rate = round(waste / revenue, 4) if revenue else 0.0
    waste_days = 365 if len(weeks) >= 52 else min(365, (max_ts - pd.Timestamp(oldest)).days)

    # Truthful, clamped window label. An explicit basis.window_label declared in
    # the engagement config is honored verbatim when present; otherwise the label
    # is computed from the actual weeks in the window.
    computed_window = (f"trailing {n_weeks} weeks {pd.Timestamp(oldest).strftime('%b %d, %Y')} – "
                       f"{max_ts.strftime('%b %d, %Y')}")
    declared_window = ((config.raw.get("basis") or {}).get("window_label") or "").strip()
    window_label = declared_window or computed_window

    summary = {"revenue": revenue, "waste": waste, "waste_rate": waste_rate,
               "basis": basis_word, "window": window_label,
               "n_weeks": n_weeks, "waste_days": waste_days}
    html_path = out / "warehouse-trade-spend-readiness.html"
    html_path.write_text(_render(config, summary, provenance, draft=not final), encoding="utf-8")
    return {"status": "ok", **summary, "report": str(html_path),
            "n_warnings": sum(r.n_warnings for r in reports.values())}


def _render(config, s, provenance: Provenance, *, draft: bool) -> str:
    esc = html.escape
    draft_class = " ll-draft" if draft else ""
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Warehouse Trade-Spend Readiness — {esc(config.client_name)}</title>
<style>{_css(draft)}</style></head>
<body class="{draft_class.strip()}"><main class=ll-page>
<header class=ll-header>
  <div class=ll-eyebrow>Lailara LLC · Trade-Spend Diagnostic</div>
  <h1 class=ll-title>Warehouse Trade-Spend Readiness</h1>
  <div class=ll-client>
    <div><span class=ll-k>Client</span> {esc(config.client_name)}</div>
    <div><span class=ll-k>Engagement</span> {esc(config.engagement_id)}</div>
    <div><span class=ll-k>As of</span> {esc(config.as_of_date.isoformat())}</div>
    <div><span class=ll-k>Prepared by</span> {esc(config.prepared_by)}</div>
  </div>
</header>
<section class=ll-banner>
  <div class=ll-score>{_fmt_dollars(s['revenue'])} {esc(s['basis'])} revenue</div>
  <div>operational waste {_fmt_dollars(s['waste'])} · {s['waste_rate']*100:.2f}% of revenue</div>
  <div class=ll-basis>Basis: {esc(s['basis'])} dollars · Window: {esc(s['window'])}<br>
       Pulled live from the client warehouse via config-mapped schema — no table names hardcoded.</div>
</section>
<section class=ll-section>
  <h2 class=ll-h2>Headline</h2>
  <table class=ll-table>
    <tr><td>Trailing-{s['n_weeks']}-week revenue ({esc(s['basis'])})</td><td class=num>{_fmt_dollars(s['revenue'])}</td></tr>
    <tr><td>Operational waste (ex promo billback, trailing {s['waste_days']}d)</td><td class=num>{_fmt_dollars(s['waste'])}</td></tr>
    <tr><td>Waste rate</td><td class=num>{s['waste_rate']*100:.2f}%</td></tr>
  </table>
  <p class=ll-note>Structural trade and promo efficacy run on the same warehouse
  connector with their rate-table maps added to <code>warehouse.columns</code>.</p>
</section>
{provenance.to_html()}
</main></body></html>"""


def _css(draft: bool) -> str:
    draft_css = (
        ".ll-draft::before{content:'DRAFT';position:fixed;top:50%;left:50%;"
        "transform:translate(-50%,-50%) rotate(-32deg);font-family:var(--s);"
        "font-size:22vw;font-weight:700;color:rgba(204,16,10,.06);z-index:0;"
        "pointer-events:none;white-space:nowrap}" if draft else ""
    )
    return f"""
:root{{--s:{P.LL_SERIF};--f:{P.LL_SANS}}}
*{{box-sizing:border-box}}
body{{margin:0;background:{P.LL_CANVAS};color:{P.LL_TEXT};font-family:var(--f);line-height:1.6}}
.ll-page{{position:relative;z-index:1;max-width:{P.LL_MAX_WIDTH};margin:0 auto;padding:48px 24px}}
.ll-header{{border-bottom:1px solid {P.LL_GRIDLINE};padding-bottom:24px;margin-bottom:24px}}
.ll-eyebrow{{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:{P.LL_RED};font-weight:600}}
.ll-title{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:32px;margin:8px 0 16px}}
.ll-client{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 24px;font-size:14px}}
.ll-k{{display:block;color:{P.LL_TEXT_SEC};font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
.ll-banner{{border-radius:2px;padding:16px 20px;margin-bottom:32px;background:{P.LL_CHICAGO_SURFACE};color:{P.LL_CHICAGO}}}
.ll-score{{font-family:var(--s);font-weight:700;font-size:22px}}
.ll-basis{{font-size:12px;color:{P.LL_TEXT_SEC};margin-top:8px}}
.ll-section{{margin:0 0 32px}}
.ll-h2{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:22px;
margin:0 0 12px;padding-bottom:6px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.ll-note{{font-size:13px;color:{P.LL_TEXT_SEC};margin-top:8px}}
.ll-table{{width:100%;border-collapse:collapse;font-size:14px}}
.ll-table td{{padding:8px 12px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.ll-provenance{{margin-top:40px;background:{P.LL_CARD_BG};color:{P.LL_CARD_TEXT};
padding:20px 24px;border-radius:2px;font-size:13px}}
.ll-prov-title{{font-family:var(--s);font-weight:700;font-size:16px;margin-bottom:8px}}
.ll-provenance div{{margin-bottom:4px;color:{P.LL_CARD_SUBTITLE}}}
.ll-provenance strong{{color:{P.LL_CARD_TEXT}}}
.ll-prov-inputs{{width:100%;border-collapse:collapse;margin-top:8px}}
.ll-prov-inputs th{{text-align:left;border-bottom:1px solid rgba(255,255,255,.12);padding:4px 8px;color:{P.LL_CARD_MUTED}}}
.ll-prov-inputs td{{padding:4px 8px;border-bottom:1px solid rgba(255,255,255,.08);color:{P.LL_CARD_SUBTITLE}}}
.ll-prov-brand{{margin-top:12px;font-family:var(--s);color:{P.LL_CARD_MUTED}}}
{draft_css}
@media print{{body{{background:#fff}}}}
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="trade-spend warehouse adapter")
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="client-output"); ap.add_argument("--final", action="store_true")
    args = ap.parse_args(argv)
    result = run(args.config, args.out, final=args.final)
    if result["status"] == "blocked":
        print("BLOCKED — data not ready. Readiness report(s):")
        for key, path in result["readiness_reports"].items():
            print(f"  {key}: {path}")
        return 3
    print(f"{_fmt_dollars(result['revenue'])} {result['basis']} revenue · "
          f"waste {_fmt_dollars(result['waste'])} ({result['waste_rate']*100:.2f}%)")
    print(f"report -> {result['report']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
