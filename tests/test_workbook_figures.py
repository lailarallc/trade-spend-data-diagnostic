"""Workbook-level figure locks for the Retailer Risk tab.

Retailer Risk once showed $0 Op Deductions and $0 Promo BB for every retailer:
deductions are keyed by retailer_id ('RET-WALMART') but the lookup used a
lowercased name ('walmart'), so nothing matched and all-in trade, net-net
margin, deduction share and the what-if table all silently understated.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
WORKBOOK = ROOT / "output" / "trade_spend_diagnostic.xlsx"
DB = ROOT / "cinderhaven-data" / "data" / "cinderhaven_product_master.db"
CANON = ROOT / "reference" / "canonical_values.json"

needs_workbook = pytest.mark.skipif(not WORKBOOK.exists(), reason="workbook artifact not present")

# Retailer Risk P&L table layout (tab_retailer_risk.py): header row 5, data from row 6.
COL_NAME, COL_REV, COL_OP, COL_PB = 2, 3, 7, 9


def _pnl_rows(ws) -> list[tuple]:
    rows = []
    for r in range(6, ws.max_row + 1):
        name = ws.cell(row=r, column=COL_NAME).value
        if not isinstance(name, str) or ws.cell(row=r, column=COL_REV).value is None:
            break
        rows.append((name, ws.cell(row=r, column=COL_REV).value,
                     ws.cell(row=r, column=COL_OP).value, ws.cell(row=r, column=COL_PB).value))
    return rows


@pytest.fixture(scope="module")
def wb():
    return load_workbook(WORKBOOK, data_only=False)


@needs_workbook
def test_every_selling_retailer_has_deductions(wb):
    rows = _pnl_rows(wb["Retailer Risk"])
    selling = [r for r in rows if r[1] > 0]
    assert len(selling) == 6, f"expected 6 retailers with revenue, got {selling}"
    for name, _rev, op, pb in selling:
        assert op > 0, f"{name}: Op Deductions is {op}"
        assert pb > 0, f"{name}: Promo BB is {pb}"


@needs_workbook
def test_op_deductions_sum_to_executive_pulse_waste(wb):
    op_total = sum(r[2] for r in _pnl_rows(wb["Retailer Risk"]))
    waste = wb["Executive Pulse"]["D13"].value
    assert op_total == pytest.approx(waste, abs=0.01)


@needs_workbook
def test_deductions_reconcile_to_canon_cy2025(wb):
    """Tab 4 uses a trailing-365-day window ending at the last scan week; canon
    publishes calendar 2025. Shifting the window edges must land exactly on canon."""
    rows = _pnl_rows(wb["Retailer Risk"])
    canon = json.loads(CANON.read_text(encoding="utf-8"))["deductions"]
    with sqlite3.connect(DB) as conn:
        max_scan = conn.execute("SELECT MAX(week_ending) FROM scan_data").fetchone()[0]
        start = (date.fromisoformat(max_scan) - timedelta(days=364)).isoformat()

        def edge(lo: str, hi: str, op: str) -> float:
            return conn.execute(
                f"SELECT COALESCE(SUM(amount), 0) FROM deductions "
                f"WHERE deduction_date BETWEEN ? AND ? AND deduction_type {op} 'promo_billback'",
                (lo, hi),
            ).fetchone()[0]

        for col, op, key in ((2, "!=", "operational_waste_ex_billback"), (3, "=", "promo_billback")):
            tab4 = sum(r[col] for r in rows)
            in_window_2024 = edge(start, "2024-12-31", op)
            after_window_2025 = edge((date.fromisoformat(max_scan) + timedelta(days=1)).isoformat(),
                                     "2025-12-31", op)
            cy2025 = tab4 - in_window_2024 + after_window_2025
            assert cy2025 == pytest.approx(canon[key]["cy2025"], abs=0.01), key


@needs_workbook
def test_methodology_gm_example_matches_retailer_risk(wb):
    """The Methodology GM example once hardcoded 39.0% / 62.5% while Retailer
    Risk computed 51.9% / 75.9%. Both now read fetch_gross_margins()."""
    import re

    text = next(v for row in wb["Methodology & Logic"].iter_rows(values_only=True)
                for v in row if isinstance(v, str) and "GM =" in v)
    quoted = {name.strip().lower(): float(pct) / 100
              for name, pct in re.findall(r"([A-Za-z ]+?) GM = ([\d.]+)%", text)}
    ws = wb["Retailer Risk"]
    sheet = {ws.cell(row=r, column=COL_NAME).value.lower(): ws.cell(row=r, column=12).value
             for r in range(6, 6 + len(_pnl_rows(ws)))}
    assert set(quoted) == {"national mass retailer", "dtc"}, quoted
    for name, pct in quoted.items():
        assert pct == pytest.approx(round(sheet[name], 3), abs=1e-9), (name, pct, sheet[name])


@needs_workbook
def test_all_in_total_matches_executive_pulse(wb):
    """Canon: all-in trade = structural + operational waste, excluding
    promo_billback. Retailer Risk once summed Promo BB into all-in."""
    ws = wb["Retailer Risk"]
    rows = range(6, 6 + len(_pnl_rows(ws)))
    all_in_total = sum(ws.cell(row=r, column=10).value for r in rows)
    pulse = wb["Executive Pulse"]
    assert all_in_total == pytest.approx(pulse["D12"].value + pulse["D13"].value, abs=0.01)
    for r in rows:
        structural, op, all_in = (ws.cell(row=r, column=c).value for c in (5, 7, 10))
        assert all_in == pytest.approx(structural + op, abs=0.01), ws.cell(row=r, column=2).value
