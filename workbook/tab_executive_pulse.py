"""Tab 1: Executive Pulse — the CEO punchline."""

import contextlib
import sqlite3
from datetime import date
from pathlib import Path

from openpyxl.formatting.rule import DataBarRule
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table
from openpyxl.worksheet.worksheet import Worksheet

from workbook.queries import fetch_channel_rates, get_trailing_bounds
from workbook.styles import (
    ALIGN_CENTER,
    ALIGN_LEFT,
    ALIGN_RIGHT,
    BORDER_SECTION,
    CHICAGO_20,
    FONT_BODY,
    FONT_HEADER,
    FONT_KPI_LABEL,
    FONT_KPI_VALUE,
    FONT_NAV,
    FONT_SECTION,
    FONT_SMALL,
    HK_35,
    NUM_FMT_DOLLAR,
    NUM_FMT_PCT,
    SANS,
    SINGAPORE_55,
    TAB_NAMES,
    TABLE_STYLE,
    TOKYO_40,
)

CATEGORY_TO_DEPT = {
    "slotting": ("Sales", "Negotiated trade terms"),
    "short_ship": ("Operations", "Fulfillment accuracy"),
    "late_delivery": ("Operations", "Logistics/carrier management"),
    "damaged": ("Operations", "Packaging/handling"),
    "pallet_fine": ("Operations", "Compliance with retailer specs"),
    "label_fine": ("Operations", "Labeling/packaging compliance"),
    "spoilage": ("Operations", "Shelf-life/inventory management"),
    "vague": ("Finance", "Unclear codes — investigate"),
    "pricing_error": ("Finance", "Invoice/price discrepancies"),
    "double_dip": ("Finance", "Duplicate promo payment"),
}


def _query_metrics(db_path: Path) -> dict:
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        oldest_week, max_scan = get_trailing_bounds(conn)

        revenue = conn.execute(
            "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
            (oldest_week,),
        ).fetchone()[0]
        if not revenue:
            raise ValueError("scan_data.dollars_sold is NULL or zero — revenue base is required")

        channel_rev = conn.execute("""
            SELECT s.retailer, SUM(sd.dollars_sold)
            FROM scan_data sd
            JOIN stores s ON sd.store_id = s.store_id
            WHERE sd.week_ending >= ?
            GROUP BY s.retailer
        """, (oldest_week,)).fetchall()

        rates, regional_rate = fetch_channel_rates(conn)

        channel_trade = 0.0
        for retailer, rev in channel_rev:
            channel_trade += rev * rates.get(retailer, regional_rate)

        deductions_by_type = conn.execute("""
            SELECT deduction_type, COUNT(*), SUM(amount)
            FROM deductions
            WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ?
              AND deduction_type != 'promo_billback'
            GROUP BY deduction_type
            ORDER BY SUM(amount) DESC
        """, (max_scan, max_scan)).fetchall()

        operational_waste = sum(r[2] for r in deductions_by_type)

        dispute_stats = conn.execute("""
            SELECT COUNT(*), SUM(recovered_amount)
            FROM disputes
        """).fetchone()

        total_disputed = conn.execute("""
            SELECT SUM(d.amount)
            FROM deductions d
            JOIN disputes dis ON dis.deduction_id = d.deduction_id
        """).fetchone()[0] or 0.0

    return {
        "revenue": revenue,
        "structural_trade": channel_trade,
        "operational_waste": operational_waste,
        "deductions_by_type": deductions_by_type,
        "dispute_count": dispute_stats[0],
        "total_recovered": dispute_stats[1] or 0.0,
        "total_disputed": total_disputed,
        "oldest_week": oldest_week,
        "max_scan": max_scan,
    }


def build_executive_pulse(ws: Worksheet, db_path: Path) -> None:
    metrics = _query_metrics(db_path)

    revenue = metrics["revenue"]
    structural = metrics["structural_trade"]
    waste = metrics["operational_waste"]
    all_in = structural + waste
    net_after = revenue - all_in

    structural_rate = structural / revenue
    waste_rate = waste / revenue
    all_in_rate = all_in / revenue

    total_recovered = metrics["total_recovered"]
    total_disputed = metrics["total_disputed"]
    recovery_rate = total_recovered / total_disputed if total_disputed else 0.0

    ws.sheet_view.showGridLines = False

    col_widths = [3, 22, 18, 18, 18, 18, 14]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # --- Header block (rows 1-3) ---
    ws.merge_cells("B1:F1")
    ws["B1"] = "Cinderhaven Provisions"
    ws["B1"].font = FONT_HEADER

    ws.merge_cells("B2:F2")
    ws["B2"] = "Executive Pulse — Trade Spend Diagnostic"
    ws["B2"].font = FONT_SECTION

    ws.merge_cells("B3:F3")
    ws["B3"] = f"Trailing 52 weeks ({metrics['oldest_week']} to {metrics['max_scan']})  |  Built {date.today().isoformat()}"
    ws["B3"].font = FONT_SMALL

    # --- KPI trio (rows 5-7) ---
    kpis = [
        ("All-in trade — retailers, last 12 months", all_in_rate),
        ("Planned Trade Rate", structural_rate),
        ("Operational waste — retailers, last 12 months", waste_rate),
    ]
    for col_idx, (label, value) in enumerate(kpis, 2):
        cell_val = ws.cell(row=5, column=col_idx, value=value)
        cell_val.font = FONT_KPI_VALUE
        cell_val.number_format = NUM_FMT_PCT
        cell_val.alignment = ALIGN_CENTER

        cell_lbl = ws.cell(row=6, column=col_idx, value=label)
        cell_lbl.font = FONT_KPI_LABEL
        cell_lbl.alignment = ALIGN_CENTER

    ws.merge_cells("B7:F7")
    amounts = [amt for _dtype, _cnt, amt in metrics["deductions_by_type"] if amt]
    top_share = (max(amounts) / waste) if (amounts and waste) else 0
    ws["B7"] = (
        f"Structural trade rate ({structural_rate:.1%}) is the rate card working as designed. "
        f"~${waste:,.0f} in retailer operational waste over the last 12 months is buried in the deductions"
        f" — spread across categories, the largest just {top_share:.0%} of the total. "
        f"A process problem, not a single leak."
    )
    ws["B7"].font = FONT_SMALL
    ws["B7"].alignment = ALIGN_LEFT

    for col in range(2, 7):
        ws.cell(row=8, column=col).border = BORDER_SECTION

    # --- Hidden source data (rows 10-14) for named ranges ---
    ws.cell(row=9, column=2, value="Waterfall: Revenue to Net-After-Trade").font = FONT_SECTION

    chart_start = 10
    headers = ["Category", "Base", "Value"]
    for c, h in enumerate(headers, 2):
        ws.cell(row=chart_start, column=c, value=h).font = FONT_BODY

    waterfall_data = [
        ("Revenue", 0, revenue),
        ("Structural Trade", net_after + waste, structural),
        ("Operational waste — retailers, last 12 months", net_after, waste),
        ("Net After Trade", 0, net_after),
    ]
    for i, (cat, base, val) in enumerate(waterfall_data):
        r = chart_start + 1 + i
        ws.cell(row=r, column=2, value=cat)
        ws.cell(row=r, column=3, value=base).number_format = NUM_FMT_DOLLAR
        ws.cell(row=r, column=4, value=val).number_format = NUM_FMT_DOLLAR

    for r in range(chart_start, chart_start + 5):
        ws.row_dimensions[r].hidden = True

    # --- In-cell waterfall (rows 16-19) ---
    waterfall_visible = [
        ("Revenue", f"=D{chart_start + 1}", CHICAGO_20),
        ("Structural Trade", f"=D{chart_start + 2}", SINGAPORE_55),
        ("Operational waste — retailers, last 12 months", f"=D{chart_start + 3}", TOKYO_40),
        ("Net After Trade", f"=D{chart_start + 4}", HK_35),
    ]
    for i, (label, formula, color) in enumerate(waterfall_visible):
        r = 16 + i
        ws.cell(row=r, column=2, value=label).font = FONT_BODY
        val_cell = ws.cell(row=r, column=4, value=formula)
        val_cell.number_format = NUM_FMT_DOLLAR
        val_cell.alignment = ALIGN_RIGHT

        ws.conditional_formatting.add(
            f"D{r}",
            DataBarRule(
                start_type="num", start_value=0,
                end_type="num", end_value=revenue,
                color=color,
            ),
        )

    for col in range(2, 7):
        ws.cell(row=21, column=col).border = BORDER_SECTION

    # --- Addressable Improvement (rows 22-30) ---
    ws.cell(row=22, column=2, value="Addressable Improvement").font = FONT_SECTION

    imp_header_row = 23
    imp_headers = ["Metric", "Value"]
    for c, h in enumerate(imp_headers, 2):
        cell = ws.cell(row=imp_header_row, column=c, value=h)
        cell.font = FONT_BODY
        cell.alignment = ALIGN_CENTER

    improvement_rows = [
        ("Operational waste — retailers, last 12 months", waste, NUM_FMT_DOLLAR),
        ("Current recovery rate", recovery_rate, NUM_FMT_PCT),
        ("Currently recovered", total_recovered, NUM_FMT_DOLLAR),
        ("At 30% recovery", waste * 0.30, NUM_FMT_DOLLAR),
        ("At 50% recovery", waste * 0.50, NUM_FMT_DOLLAR),
        ("Incremental at 30% vs. current", waste * 0.30 - total_recovered, NUM_FMT_DOLLAR),
        ("Incremental at 50% vs. current", waste * 0.50 - total_recovered, NUM_FMT_DOLLAR),
    ]
    for i, (label, val, fmt) in enumerate(improvement_rows):
        r = imp_header_row + 1 + i
        ws.cell(row=r, column=2, value=label).font = FONT_BODY
        c_val = ws.cell(row=r, column=3, value=val)
        c_val.font = FONT_BODY
        c_val.number_format = fmt
        c_val.alignment = ALIGN_RIGHT

    imp_end_row = imp_header_row + len(improvement_rows)

    imp_table = Table(displayName="tbl_AddressableImprovement", ref=f"B{imp_header_row}:C{imp_end_row}")
    imp_table.tableStyleInfo = TABLE_STYLE
    ws.add_table(imp_table)

    for col in range(2, 7):
        ws.cell(row=imp_end_row + 1, column=col).border = BORDER_SECTION

    # --- Responsibility Matrix (rows 32+) ---
    resp_title_row = imp_end_row + 2
    ws.cell(row=resp_title_row, column=2, value="Responsibility Matrix — Who Owns the Waste").font = FONT_SECTION

    resp_header_row = resp_title_row + 1
    resp_headers = ["Deduction Type", "Amount", "Owner", "Root Cause"]
    for c, h in enumerate(resp_headers, 2):
        cell = ws.cell(row=resp_header_row, column=c, value=h)
        cell.font = FONT_BODY
        cell.alignment = ALIGN_CENTER

    for i, (dtype, count, amount) in enumerate(metrics["deductions_by_type"]):
        r = resp_header_row + 1 + i
        dept, cause = CATEGORY_TO_DEPT.get(dtype, ("Unclassified", ""))
        ws.cell(row=r, column=2, value=dtype.replace("_", " ").title())
        c_amt = ws.cell(row=r, column=3, value=amount)
        c_amt.number_format = NUM_FMT_DOLLAR
        c_amt.alignment = ALIGN_RIGHT
        ws.cell(row=r, column=4, value=dept)
        ws.cell(row=r, column=5, value=cause)

    resp_end_row = resp_header_row + len(metrics["deductions_by_type"])

    resp_table = Table(displayName="tbl_ResponsibilityMatrix", ref=f"B{resp_header_row}:E{resp_end_row}")
    resp_table.tableStyleInfo = TABLE_STYLE
    ws.add_table(resp_table)

    # --- Navigation hyperlinks ---
    nav_row = resp_end_row + 2
    ws.cell(row=nav_row, column=2, value="Navigate to:").font = FONT_SECTION

    nav_row += 1
    for i, tab_name in enumerate(TAB_NAMES):
        cell = ws.cell(row=nav_row, column=2 + i, value=tab_name)
        cell.font = FONT_NAV
        cell.hyperlink = f"#'{tab_name}'!A1"

    # --- Instructional callout ---
    callout_row = nav_row + 2
    ws.merge_cells(f"B{callout_row}:F{callout_row}")
    callout = ws.cell(
        row=callout_row, column=2,
        value=(
            "This workbook summarizes trailing-12-month trade spend for Cinderhaven Provisions. "
            "Green tabs are analysis. Blue tab is the full deduction ledger. "
            "Gray tabs are reference. Yellow cells are adjustable inputs."
        ),
    )
    callout.font = FONT_SMALL
    callout.alignment = ALIGN_LEFT
