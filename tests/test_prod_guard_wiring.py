"""The prod guard sits in front of the Postgres read in scripts/extract_from_postgres.py.

The script reads DATABASE_URL, else localhost:5432 -- a `fly proxy` tunnel to
production when one is open. These tests fake a flyctl listener and assert
nothing connects.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import prod_guard  # noqa: E402

psycopg2 = pytest.importorskip("psycopg2")


def _load_extract(monkeypatch, database_url):
    for var in ("ALLOW_PROD_DB", "DATABASE_URL", "PGHOST", "PGPORT"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("POSTGRES_PASSWORD", "not-a-real-password")
    if database_url:
        monkeypatch.setenv("DATABASE_URL", database_url)
    spec = importlib.util.spec_from_file_location("extract_from_postgres", SCRIPTS / "extract_from_postgres.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def fly_tunnel(monkeypatch):
    monkeypatch.setattr(prod_guard, "_listener", lambda port: "flyctl")
    monkeypatch.setattr(psycopg2, "connect", lambda *a, **kw: pytest.fail("connected"))


def test_database_url_refuses_fly_tunnel(fly_tunnel, monkeypatch):
    mod = _load_extract(monkeypatch, "postgresql://localhost:5432/db")
    with pytest.raises(prod_guard.ProdDatabaseError):
        mod.extract()


def test_localhost_default_refuses_fly_tunnel(fly_tunnel, monkeypatch):
    mod = _load_extract(monkeypatch, None)
    with pytest.raises(prod_guard.ProdDatabaseError):
        mod.extract()
