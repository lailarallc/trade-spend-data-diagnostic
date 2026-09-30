"""Extract all 21 Cinderhaven tables from Postgres into local SQLite.

Usage:
    flyctl proxy 5432 -a cinderhaven-db  # in another terminal
    ALLOW_PROD_DB=1 python scripts/extract_from_postgres.py
"""
import os
import sqlite3
import sys
from decimal import Decimal
from pathlib import Path

import psycopg2

import prod_guard  # vendored in scripts/; refuses a fly tunnel to production

_pw = os.environ.get("POSTGRES_PASSWORD")
if not _pw:
    print("Error: POSTGRES_PASSWORD environment variable is required.", file=sys.stderr)
    sys.exit(1)
DB_URL = os.environ.get("DATABASE_URL", f"postgresql://postgres:REDACTED@localhost:5432/cinderhaven")

OUT = Path(__file__).resolve().parent.parent / "cinderhaven-data" / "data" / "cinderhaven_product_master.db"

TABLE_MAP = {
    "chargebacks": "retailer_chargebacks",
    "deduction_codes": "retailer_deduction_codes",
    "deductions": "retailer_deductions",
    "dispute_evidence": "retailer_dispute_evidence",
    "disputes": "retailer_disputes",
    "distribution_log": "distribution_log",
    "edi_requirements": "retailer_edi_requirements",
    "order_lines": "retailer_order_lines",
    "orders": "retailer_orders",
    "pack_records": "retailer_pack_records",
    "post_audit_claims": "retailer_post_audit_claims",
    "price_history": "price_history",
    "product_master": "product_master",
    "promotions": "promotions",
    "remittances": "retailer_remittances",
    "retailer_rules": "retailer_rules",
    "retailers": "retailers",
    "scan_data": "scan_data",
    "shipments": "retailer_shipments",
    "sku_costs": "sku_costs",
    "stores": "stores",
}


def extract():
    prod_guard.check(DB_URL)
    pg = psycopg2.connect(DB_URL)
    pg.set_session(readonly=True)
    pg_cur = pg.cursor()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        backup = OUT.with_suffix(".db.bak")
        if backup.exists():
            backup.unlink()
        print(f"Backing up existing DB to {backup.name}")
        OUT.rename(backup)

    sl = sqlite3.connect(str(OUT))
    sl.execute("PRAGMA journal_mode=WAL")
    sl.execute("PRAGMA synchronous=NORMAL")

    for sqlite_name, pg_name in TABLE_MAP.items():
        pg_cur.execute(
            f"SELECT column_name, data_type FROM information_schema.columns "
            f"WHERE table_schema='raw' AND table_name='{pg_name}' ORDER BY ordinal_position"
        )
        cols = pg_cur.fetchall()
        if not cols:
            print(f"  SKIP {sqlite_name} (no Postgres table raw.{pg_name})")
            continue

        col_defs = []
        col_names = []
        for cname, dtype in cols:
            col_names.append(cname)
            if dtype in ("integer", "bigint", "smallint"):
                stype = "INTEGER"
            elif dtype in ("numeric", "double precision", "real"):
                stype = "REAL"
            else:
                stype = "TEXT"
            col_defs.append(f'"{cname}" {stype}')

        sl.execute(f"DROP TABLE IF EXISTS [{sqlite_name}]")
        sl.execute(f"CREATE TABLE [{sqlite_name}] ({', '.join(col_defs)})")

        pg_cur.execute(f"SELECT {', '.join(col_names)} FROM raw.{pg_name}")
        batch_size = 10000
        total = 0
        while True:
            rows = pg_cur.fetchmany(batch_size)
            if not rows:
                break
            clean = [
                tuple(float(v) if isinstance(v, Decimal) else v for v in row)
                for row in rows
            ]
            placeholders = ", ".join(["?"] * len(col_names))
            sl.executemany(
                f"INSERT INTO [{sqlite_name}] VALUES ({placeholders})",
                clean,
            )
            total += len(rows)
            if total % 100000 == 0:
                print(f"    {sqlite_name}: {total:,} rows...", flush=True)

        sl.commit()
        print(f"  {sqlite_name}: {total:,} rows")

    sl.execute("ANALYZE")
    sl.close()
    pg.close()

    size_mb = OUT.stat().st_size / (1024 * 1024)
    print(f"\nDone. {OUT} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    extract()
