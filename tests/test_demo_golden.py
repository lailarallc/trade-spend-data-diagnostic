"""Demo golden + P1 regression lock — trade-spend-data-diagnostic.

The RE-AUDIT 2026-08-01 item-1 P1: the validator once pinned a retired revenue
figure, SQL headers called it "Locked", and walkthrough/README carried a stale
pre-reseed revenue figure. The workbook is now re-derived from post-resync
platform data ($32,323,139.62). This locks that fix at the artifact + SQL-header
level; retired-token *absence* across live surfaces is enforced separately by the
canonical drift gate (scripts/check_canonical_drift.py), and the DB-side figures
are pinned in test_canonical_regression.py from reference/canonical_values.json.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
WORKBOOK = ROOT / "output" / "trade_spend_diagnostic.xlsx"

CURRENT_REVENUE = 32_323_139.62


@pytest.mark.skipif(not WORKBOOK.exists(), reason="workbook artifact not present")
def test_workbook_revenue_cell_is_current_figure():
    """Executive Pulse D11 equals the current canonical figure — a stale
    (pre-reseed) rebuild is caught here."""
    wb = load_workbook(WORKBOOK, data_only=False)
    d11 = wb["Executive Pulse"]["D11"].value
    assert d11 is not None
    assert abs(d11 - CURRENT_REVENUE) / CURRENT_REVENUE < 0.005, (
        f"workbook D11 revenue {d11:,.2f} != current ${CURRENT_REVENUE:,.2f} — "
        "a stale (pre-reseed) workbook. STOP and re-export before re-pinning."
    )


def test_sql_locked_header_names_current_figure():
    """The trade-rate 'Locked number' header names the current figure."""
    sql = (ROOT / "sql" / "trade_rate" / "total_revenue.sql").read_text(encoding="utf-8")
    m = re.search(r"Locked number:\s*\$([\d,]+)", sql)
    assert m, "no 'Locked number' header found in total_revenue.sql"
    # $32,323,140 (rounded current figure) — not the retired pre-reseed value.
    assert m.group(1).replace(",", "") == "32323140"
    # And it rounds to the current canonical revenue.
    assert round(int(m.group(1).replace(",", "")), -1) == round(CURRENT_REVENUE, -1)
