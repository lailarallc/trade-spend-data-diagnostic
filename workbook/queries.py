"""Shared database query helpers."""

import sqlite3
from pathlib import Path

CHANNEL_RATE_COLS = {
    "Walmart": "trade_spend_pct_walmart",
    "Costco": "trade_spend_pct_costco",
    "Whole Foods": "trade_spend_pct_whole_foods",
    "Sprouts": "trade_spend_pct_sprouts",
    "UNFI": "trade_spend_pct_unfi",
    "DTC": "trade_spend_pct_dtc",
    "KeHE": "trade_spend_pct_kehe",
}
# Kroger has no dedicated trade_spend_pct column; falls back to regional rate

_VALID_RATE_COLS = frozenset(CHANNEL_RATE_COLS.values()) | {"trade_spend_pct_regional"}


def get_trailing_bounds(conn: sqlite3.Connection) -> tuple[str, str]:
    """Return (oldest_week, max_scan) for trailing 52 weeks of scan data."""
    weeks = conn.execute(
        "SELECT DISTINCT week_ending FROM scan_data ORDER BY week_ending DESC LIMIT 52"
    ).fetchall()
    if not weeks:
        raise ValueError("scan_data contains no rows — cannot generate workbook")
    return weeks[-1][0], weeks[0][0]


def fetch_channel_rates(conn: sqlite3.Connection) -> tuple[dict[str, float], float]:
    """Return (rates_by_channel, regional_rate) from sku_costs."""
    rates: dict[str, float] = {}
    for channel, col in CHANNEL_RATE_COLS.items():
        assert col in _VALID_RATE_COLS
        rates[channel] = conn.execute(
            f"SELECT AVG({col}) FROM sku_costs"
        ).fetchone()[0] or 0.0
    regional_rate = conn.execute(
        "SELECT AVG(trade_spend_pct_regional) FROM sku_costs"
    ).fetchone()[0] or 0.0
    return rates, regional_rate


def fetch_gross_margins(conn: sqlite3.Connection) -> dict[str, float]:
    """Return gross margin by channel: (AVG(wholesale) - AVG(COGS)) / AVG(wholesale).

    Single source for Retailer Risk and the Methodology example.
    """
    gm_map: dict[str, float] = {}
    for channel, wcol in [("Walmart", "wholesale_walmart"), ("Costco", "wholesale_costco"),
                          ("Whole Foods", "wholesale_whole_foods"),
                          ("Sprouts", "wholesale_sprouts"), ("UNFI", "wholesale_unfi"),
                          ("DTC", "wholesale_dtc"), ("KeHE", "wholesale_kehe"),
                          ("Regional", "wholesale_regional")]:
        # Kroger has no dedicated wholesale column; uses regional rate
        r = conn.execute(f"SELECT AVG(cogs_per_unit), AVG({wcol}) FROM sku_costs").fetchone()
        if r[0] is not None and r[1]:
            gm_map[channel] = (r[1] - r[0]) / r[1]
        else:
            gm_map[channel] = 0
    return gm_map
