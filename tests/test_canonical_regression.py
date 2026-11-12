"""Canonical regression test for the Cinderhaven baked database.

Follows the TestCinderhavenValidatedRegression pattern: loads the baked
SQLite database and asserts that key figures match the validated workbook
output.  This pins the data contract so any re-export or schema change
is caught immediately.
"""

import sqlite3
from pathlib import Path

import pytest

DB = Path(__file__).resolve().parent.parent / "cinderhaven-data" / "data" / "cinderhaven_product_master.db"

# --- Helpers ----------------------------------------------------------------

CHANNEL_RATE_COLS = {
    "Walmart": "trade_spend_pct_walmart",
    "Costco": "trade_spend_pct_costco",
    "Whole Foods": "trade_spend_pct_whole_foods",
    "Sprouts": "trade_spend_pct_sprouts",
    "Kroger": "trade_spend_pct_kroger",
    "UNFI": "trade_spend_pct_unfi",
    "DTC": "trade_spend_pct_dtc",
    "KeHE": "trade_spend_pct_kehe",
}


def _trailing_bounds(conn: sqlite3.Connection) -> tuple[str, str]:
    """Return (oldest_week, max_scan) for trailing 52 weeks."""
    weeks = conn.execute(
        "SELECT DISTINCT week_ending FROM scan_data ORDER BY week_ending DESC LIMIT 52"
    ).fetchall()
    return weeks[-1][0], weeks[0][0]


def _compute_structural_trade(conn: sqlite3.Connection, oldest_week: str) -> float:
    """Replicate the Python-side structural trade calculation from the workbook."""
    channel_rev = conn.execute(
        "SELECT s.retailer, SUM(sd.dollars_sold) "
        "FROM scan_data sd "
        "JOIN stores s ON sd.store_id = s.store_id "
        "WHERE sd.week_ending >= ? "
        "GROUP BY s.retailer",
        (oldest_week,),
    ).fetchall()

    rates: dict[str, float] = {}
    for channel, col in CHANNEL_RATE_COLS.items():
        rates[channel] = conn.execute(
            f"SELECT AVG({col}) FROM sku_costs"
        ).fetchone()[0] or 0.0
    regional_rate = conn.execute(
        "SELECT AVG(trade_spend_pct_regional) FROM sku_costs"
    ).fetchone()[0] or 0.0

    total = 0.0
    for retailer, rev in channel_rev:
        total += rev * rates.get(retailer, regional_rate)
    return total


# --- Fixtures ---------------------------------------------------------------

@pytest.fixture(scope="module")
def conn():
    """Open a read-only connection to the baked database."""
    if not DB.exists():
        pytest.skip(f"Baked database not found at {DB}")
    connection = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    yield connection
    connection.close()


# --- Tests ------------------------------------------------------------------

class TestCinderhavenCanonicalRegression:
    """Pin the Cinderhaven data contract against the validated workbook output.

    These values were validated via validate_workbook.py against the
    baked database (cinderhaven_product_master.db, ~118 MB).  Any change
    to the baked data that shifts these numbers must be intentional.
    """

    # -- Dimension counts ----------------------------------------------------

    def test_sku_count(self, conn):
        """Exactly 50 SKUs in product_master."""
        count = conn.execute("SELECT COUNT(*) FROM product_master").fetchone()[0]
        assert count == 50, f"Expected 50 SKUs, got {count}"

    def test_product_line_count(self, conn):
        """5 product lines after the 2026-06-02 re-export from Postgres."""
        lines = conn.execute(
            "SELECT DISTINCT product_line FROM product_master ORDER BY product_line"
        ).fetchall()
        line_names = [row[0] for row in lines]
        assert len(line_names) == 5, f"Expected 5 product lines, got {len(line_names)}: {line_names}"
        assert line_names == [
            "Artisan Sauces",
            "Dried Goods",
            "Pantry Staples",
            "Snack Bites",
            "Specialty Condiments",
        ]

    def test_retailer_count(self, conn):
        """6 retailers after 5-line re-export."""
        retailers = conn.execute(
            "SELECT name FROM retailers ORDER BY name"
        ).fetchall()
        retailer_names = [row[0] for row in retailers]
        assert len(retailer_names) == 6, (
            f"Expected 6 retailers, got {len(retailer_names)}: {retailer_names}"
        )
        assert "Kroger" in retailer_names, "Kroger missing from retailers table"
        assert "Sprouts" in retailer_names, "Sprouts missing from retailers table"

    def test_store_retailers_match(self, conn):
        """All 6 retailers appear in the stores table."""
        store_retailers = conn.execute(
            "SELECT DISTINCT retailer FROM stores ORDER BY retailer"
        ).fetchall()
        names = [row[0] for row in store_retailers]
        assert len(names) == 6, f"Expected 6 store retailers, got {len(names)}: {names}"
        assert "Kroger" in names
        assert "Sprouts" in names

    # -- Revenue & trade figures (0.5% tolerance) ----------------------------

    TOLERANCE = 0.005  # 0.5%

    @staticmethod
    def _approx(actual, expected, tol):
        """True when actual is within tol fraction of expected."""
        if expected == 0:
            return actual == 0
        return abs(actual - expected) / abs(expected) < tol

    def test_revenue(self, conn):
        """Trailing-52w scan revenue vs canonical revenue.retail_scan.cy2025.

        SSOT: reference/canonical_values.json, vendored from
        MsShawnP/cinderhaven-data-platform@7533264 (VERIFIED-AGAINST-PRODUCTION
        2026-07-29). Trailing-52w == CY2025 in this dataset. Supersedes the
        dead $32,539,868 pin (5-line re-export 2026-06-02).
        """
        import json as _json
        canon = _json.loads(
            (Path(__file__).resolve().parent.parent / "reference" / "canonical_values.json").read_text()
        )
        target = canon["revenue"]["retail_scan"]["cy2025"]
        oldest, _ = _trailing_bounds(conn)
        revenue = conn.execute(
            "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
            (oldest,),
        ).fetchone()[0]
        assert self._approx(revenue, target, self.TOLERANCE), (
            f"Revenue {revenue:,.2f} outside 0.5% of canonical ${target:,.2f}"
        )

    def test_structural_trade(self, conn):
        """Structural trade ~ $3,177,051 (9.83%), equal to canonical §Trade Economics.

        Kroger and Sprouts use their dedicated rate columns (2026-11-11); before
        that, Kroger fell back to the regional rate and this pinned $2,914,207.
        """
        oldest, _ = _trailing_bounds(conn)
        structural = _compute_structural_trade(conn, oldest)
        assert self._approx(structural, 3_177_051, self.TOLERANCE), (
            f"Structural trade {structural:,.2f} outside 0.5% of $3,177,051"
        )

    def test_operational_waste(self, conn):
        """Operational waste ~ $343,281 (derived, retailer scope, trailing-365).

        Canonical deductions.operational_waste_ex_billback.cy2025 is $344,655
        (0.4% away — window-boundary difference). The portfolio-level
        "~$380K/yr" ($379,559 measured 2026-07-30) in CINDERHAVEN_CANONICAL.md
        §Trade Economics is a wider channel scope; this repo is the retailer
        diagnostic. The two are different scopes by design.
        """
        _, max_scan = _trailing_bounds(conn)
        waste = conn.execute(
            "SELECT SUM(amount) FROM deductions "
            "WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ? "
            "  AND deduction_type != 'promo_billback'",
            (max_scan, max_scan),
        ).fetchone()[0]
        assert self._approx(waste, 343_281, self.TOLERANCE), (
            f"Operational waste {waste:,.2f} outside 0.5% of $343,281"
        )

    def test_all_in_rate(self, conn):
        """All-in trade rate ~ 10.9% (Kroger mapped 2026-11-11)."""
        oldest, max_scan = _trailing_bounds(conn)
        revenue = conn.execute(
            "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
            (oldest,),
        ).fetchone()[0]
        structural = _compute_structural_trade(conn, oldest)
        waste = conn.execute(
            "SELECT SUM(amount) FROM deductions "
            "WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ? "
            "  AND deduction_type != 'promo_billback'",
            (max_scan, max_scan),
        ).fetchone()[0]
        all_in = (structural + waste) / revenue
        assert self._approx(all_in, 0.1089, 0.01), (
            f"All-in rate {all_in:.4f} ({all_in*100:.1f}%) outside tolerance of 10.9%"
        )

    def test_structural_rate(self, conn):
        """Structural trade rate ~ 9.83% (Kroger and Sprouts on their own rate columns, 2026-11-11)."""
        oldest, _ = _trailing_bounds(conn)
        revenue = conn.execute(
            "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
            (oldest,),
        ).fetchone()[0]
        structural = _compute_structural_trade(conn, oldest)
        rate = structural / revenue
        assert self._approx(rate, 0.0983, self.TOLERANCE), (
            f"Structural rate {rate:.4f} ({rate*100:.1f}%) outside 0.5% of 9.8%"
        )

    def test_waste_rate(self, conn):
        """Operational waste rate ~ 1.06% (regen 2026-06-30)."""
        oldest, max_scan = _trailing_bounds(conn)
        revenue = conn.execute(
            "SELECT SUM(dollars_sold) FROM scan_data WHERE week_ending >= ?",
            (oldest,),
        ).fetchone()[0]
        waste = conn.execute(
            "SELECT SUM(amount) FROM deductions "
            "WHERE deduction_date > date(?, '-365 days') AND deduction_date <= ? "
            "  AND deduction_type != 'promo_billback'",
            (max_scan, max_scan),
        ).fetchone()[0]
        rate = waste / revenue
        assert self._approx(rate, 0.01057, self.TOLERANCE), (
            f"Waste rate {rate:.4f} ({rate*100:.2f}%) outside 0.5% of 1.06%"
        )

    def test_disputes_total(self, conn):
        """More than 3,000 disputes."""
        count = conn.execute("SELECT COUNT(*) FROM disputes").fetchone()[0]
        assert count > 3000, f"Expected >3,000 disputes, got {count}"
