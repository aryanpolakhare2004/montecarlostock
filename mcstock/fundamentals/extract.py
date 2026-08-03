"""Turn a raw SEC companyfacts JSON blob into tidy annual financial-statement data.

A single companyfacts response already contains several years of comparative
figures for each concept (each 10-K reports the current year plus priors), so
one API call per ticker is enough to build a multi-year history.
"""
from __future__ import annotations

import pandas as pd

from .concepts import CONCEPTS

UNIT_OVERRIDES = {
    "diluted_shares_outstanding": "shares",
}


def _candidate_entries(facts_json: dict, metric: str) -> tuple[list[dict], str] | tuple[None, None]:
    """Return (unit entries, tag_used) for the first candidate tag present in the filer's facts."""
    facts = facts_json.get("facts", {})
    unit_key = UNIT_OVERRIDES.get(metric, "USD")
    for taxonomy, tag in CONCEPTS[metric]:
        node = facts.get(taxonomy, {}).get(tag)
        if not node:
            continue
        units = node.get("units", {})
        entries = units.get(unit_key)
        if entries:
            return entries, tag
    return None, None


def extract_annual_series(facts_json: dict, metric: str) -> pd.DataFrame:
    """Return a DataFrame with one row per fiscal year for `metric`.

    Columns: fiscal_year, end_date, value, form, filed, tag.
    Restatements are resolved by keeping the most recently filed value per fiscal year.
    """
    entries, tag = _candidate_entries(facts_json, metric)
    if not entries:
        return pd.DataFrame(columns=["fiscal_year", "end_date", "value", "form", "filed", "tag"])

    annual = [
        e for e in entries
        if e.get("form", "").startswith("10-K") and e.get("fp") == "FY" and e.get("fy") is not None
    ]
    if not annual:
        return pd.DataFrame(columns=["fiscal_year", "end_date", "value", "form", "filed", "tag"])

    df = pd.DataFrame(annual)
    df = df.sort_values("filed").drop_duplicates(subset=["fy"], keep="last")
    df = df.rename(columns={"fy": "fiscal_year", "end": "end_date", "val": "value"})
    df["tag"] = tag
    df = df[["fiscal_year", "end_date", "value", "form", "filed", "tag"]]
    return df.sort_values("fiscal_year").reset_index(drop=True)


def extract_all(facts_json: dict) -> dict[str, pd.DataFrame]:
    """Extract annual series for every tracked metric."""
    return {metric: extract_annual_series(facts_json, metric) for metric in CONCEPTS}


def to_annual_table(facts_json: dict) -> pd.DataFrame:
    """Wide table: rows = fiscal year, columns = metric, values = reported figure."""
    series = extract_all(facts_json)
    columns = {}
    for metric, df in series.items():
        if df.empty:
            continue
        columns[metric] = df.set_index("fiscal_year")["value"]
    if not columns:
        return pd.DataFrame()
    table = pd.DataFrame(columns).sort_index()
    return table


def entity_name(facts_json: dict) -> str:
    return facts_json.get("entityName", "")
