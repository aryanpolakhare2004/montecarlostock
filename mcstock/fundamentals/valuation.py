"""Heuristic fair-value range: blends a multiples-based estimate with a simple
5-year discounted-cash-flow model. This is deliberately simple — a transparent
sanity-check range, not a substitute for a real valuation model.
"""
from __future__ import annotations

import pandas as pd

from .ratios import cagr

DISCOUNT_RATE = 0.09
TERMINAL_GROWTH = 0.025
PROJECTION_YEARS = 5


def _dcf_lite(fcf_per_share: float | None, growth_rate: float | None) -> float | None:
    if fcf_per_share is None or fcf_per_share <= 0 or growth_rate is None:
        return None
    growth_rate = max(min(growth_rate, 0.20), -0.05)
    fcf = fcf_per_share
    pv = 0.0
    for t in range(1, PROJECTION_YEARS + 1):
        fcf *= (1 + growth_rate)
        pv += fcf / (1 + DISCOUNT_RATE) ** t
    terminal_value = (fcf * (1 + TERMINAL_GROWTH)) / (DISCOUNT_RATE - TERMINAL_GROWTH)
    pv += terminal_value / (1 + DISCOUNT_RATE) ** PROJECTION_YEARS
    return pv


def estimate_fair_value(metrics: pd.DataFrame, price_stats: dict, shares_outstanding: float | None) -> dict:
    empty = {"low": None, "high": None, "current_price": price_stats.get("last_price"),
              "methods": {}, "upside_low_pct": None, "upside_high_pct": None}
    if metrics.empty or not shares_outstanding:
        return empty

    latest = metrics.iloc[-1]
    net_income = latest.get("net_income")
    fcf = latest.get("free_cash_flow")
    eps = (net_income / shares_outstanding) if pd.notna(net_income) else None
    fcf_ps = (fcf / shares_outstanding) if pd.notna(fcf) else None
    growth = cagr(metrics["revenue"], 3) if "revenue" in metrics else None

    methods: dict[str, dict] = {}
    if eps is not None and eps > 0:
        methods["earnings_multiple"] = {"low": round(eps * 15, 2), "high": round(eps * 30, 2)}
    if fcf_ps is not None and fcf_ps > 0:
        methods["fcf_multiple"] = {"low": round(fcf_ps * 15, 2), "high": round(fcf_ps * 25, 2)}
    dcf = _dcf_lite(fcf_ps, growth)
    if dcf is not None:
        methods["dcf_lite"] = {"low": round(dcf * 0.85, 2), "high": round(dcf * 1.15, 2)}

    if not methods:
        return empty

    low = sum(m["low"] for m in methods.values()) / len(methods)
    high = sum(m["high"] for m in methods.values()) / len(methods)
    if low > high:
        low, high = high, low

    price = price_stats.get("last_price")
    upside_low = (low / price - 1) if price else None
    upside_high = (high / price - 1) if price else None

    return {
        "low": round(low, 2), "high": round(high, 2), "current_price": price,
        "methods": methods, "upside_low_pct": upside_low, "upside_high_pct": upside_high,
    }
