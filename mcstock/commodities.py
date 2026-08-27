"""A curated list of common commodity futures (yfinance symbols) and a fast
per-symbol quote -- no fundamentals/SEC data involved, since futures have
none of that.
"""
from __future__ import annotations

from . import data

COMMODITIES = [
    {"symbol": "GC=F", "name": "Gold"},
    {"symbol": "SI=F", "name": "Silver"},
    {"symbol": "CL=F", "name": "Crude Oil (WTI)"},
    {"symbol": "BZ=F", "name": "Brent Crude"},
    {"symbol": "NG=F", "name": "Natural Gas"},
    {"symbol": "HG=F", "name": "Copper"},
    {"symbol": "PL=F", "name": "Platinum"},
    {"symbol": "ZC=F", "name": "Corn"},
    {"symbol": "ZS=F", "name": "Soybeans"},
    {"symbol": "ZW=F", "name": "Wheat"},
]


def quick_quote(symbol: str) -> dict:
    prices = data.download_prices(symbol, period="3mo")
    last_price = float(prices.iloc[-1])
    prev_price = float(prices.iloc[-2]) if len(prices) > 1 else None
    day_change_pct = (last_price / prev_price - 1) if prev_price else None
    return {
        "symbol": symbol,
        "last_price": last_price,
        "day_change_pct": day_change_pct,
        "sparkline": [round(float(p), 2) for p in prices.tail(30)],
    }
