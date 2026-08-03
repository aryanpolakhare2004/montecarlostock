"""DuckDB-backed local cache for SEC EDGAR data.

Caching avoids re-hitting SEC on every dashboard refresh (politeness + speed):
the ticker->CIK map barely changes and companyfacts for an already-analyzed
ticker is reused until it goes stale.
"""
from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb

from . import edgar

DATA_DIR = Path(os.environ.get("MCSTOCK_DATA_DIR", "mcstock_data"))
DB_PATH = DATA_DIR / "fundamentals.duckdb"

SCHEMA = """
CREATE TABLE IF NOT EXISTS ticker_cik_map (
    ticker VARCHAR PRIMARY KEY,
    cik BIGINT NOT NULL,
    title VARCHAR,
    fetched_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS company_facts_cache (
    cik BIGINT PRIMARY KEY,
    ticker VARCHAR,
    entity_name VARCHAR,
    fetched_at TIMESTAMP NOT NULL,
    raw_json JSON NOT NULL
);
"""


@contextmanager
def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(DB_PATH))
    try:
        conn.execute(SCHEMA)
        yield conn
    finally:
        conn.close()


def _is_fresh(fetched_at, max_age: timedelta) -> bool:
    if fetched_at is None:
        return False
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - fetched_at < max_age


def get_cik_for_ticker(ticker: str, max_age: timedelta = timedelta(days=7)) -> tuple[int, str]:
    """Resolve a ticker to (cik, title), using the cached SEC map when it's fresh enough."""
    ticker = ticker.upper()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT cik, title, fetched_at FROM ticker_cik_map WHERE ticker = ?", [ticker]
        ).fetchone()
        if row and _is_fresh(row[2], max_age):
            return int(row[0]), row[1]

        mapping = edgar.fetch_ticker_cik_map()
        now = datetime.now(timezone.utc)
        conn.execute("DELETE FROM ticker_cik_map")
        conn.executemany(
            "INSERT INTO ticker_cik_map (ticker, cik, title, fetched_at) VALUES (?, ?, ?, ?)",
            [(t, info["cik"], info["title"], now) for t, info in mapping.items()],
        )

    if ticker not in mapping:
        raise LookupError(f"Ticker '{ticker}' not found in SEC's company_tickers.json")
    return mapping[ticker]["cik"], mapping[ticker]["title"]


def get_company_facts(ticker: str, max_age: timedelta = timedelta(hours=12), force_refresh: bool = False) -> dict:
    """Return raw companyfacts JSON for a ticker, fetching from SEC only if the cache is stale."""
    cik, title = get_cik_for_ticker(ticker)

    with get_connection() as conn:
        if not force_refresh:
            row = conn.execute(
                "SELECT raw_json, fetched_at FROM company_facts_cache WHERE cik = ?", [cik]
            ).fetchone()
            if row and _is_fresh(row[1], max_age):
                return json.loads(row[0])

        facts = edgar.fetch_company_facts(cik)
        entity_name = facts.get("entityName", title)
        conn.execute(
            "INSERT OR REPLACE INTO company_facts_cache (cik, ticker, entity_name, fetched_at, raw_json) "
            "VALUES (?, ?, ?, ?, ?)",
            [cik, ticker.upper(), entity_name, datetime.now(timezone.utc), json.dumps(facts)],
        )
        return facts
