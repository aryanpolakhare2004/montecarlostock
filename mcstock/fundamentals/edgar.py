"""Thin client for SEC EDGAR's free structured-data APIs.

Endpoints used:
  https://www.sec.gov/files/company_tickers.json           (ticker -> CIK map)
  https://data.sec.gov/api/xbrl/companyfacts/CIK{10d}.json (all structured XBRL facts for a filer)

SEC's fair-access policy requires a descriptive User-Agent identifying the
requester (name + contact), and asks automated tools to stay well under 10
requests/second. We default the contact to the account owner's address but
it can be overridden via MCSTOCK_SEC_USER_AGENT.
"""
from __future__ import annotations

import os
import time

import requests

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

DEFAULT_USER_AGENT = "mcstock-fundamentals-analyst aspolakhare@gmail.com"
_MIN_REQUEST_INTERVAL = 0.15  # ~6-7 req/s, comfortably under SEC's 10 req/s guidance

_last_request_at = 0.0


def _user_agent() -> str:
    return os.environ.get("MCSTOCK_SEC_USER_AGENT", DEFAULT_USER_AGENT)


def _throttle() -> None:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_at = time.monotonic()


def fetch_json(url: str, timeout: float = 15.0) -> dict:
    """GET a JSON document from SEC EDGAR with the required headers and rate limiting."""
    _throttle()
    headers = {"User-Agent": _user_agent(), "Accept-Encoding": "gzip, deflate"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    if resp.status_code == 404:
        raise LookupError(f"SEC EDGAR returned 404 for {url}")
    resp.raise_for_status()
    return resp.json()


def fetch_ticker_cik_map() -> dict[str, dict]:
    """Return {ticker_upper: {"cik": int, "title": str}} for every SEC-registered ticker."""
    raw = fetch_json(TICKERS_URL)
    result: dict[str, dict] = {}
    for entry in raw.values():
        ticker = str(entry["ticker"]).upper()
        result[ticker] = {"cik": int(entry["cik_str"]), "title": entry["title"]}
    return result


def fetch_company_facts(cik: int) -> dict:
    """Return the raw companyfacts JSON (all XBRL concepts/units/values) for a CIK."""
    return fetch_json(COMPANY_FACTS_URL.format(cik=cik))
