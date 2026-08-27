"""A curated list of common forex pairs (yfinance symbols) and a fast
per-symbol quote -- no fundamentals/SEC data involved, since currency
pairs aren't companies.
"""
from __future__ import annotations

from . import data

FOREX_PAIRS = [
    {"symbol": "EURUSD=X", "name": "EUR/USD"},
    {"symbol": "GBPUSD=X", "name": "GBP/USD"},
    {"symbol": "USDJPY=X", "name": "USD/JPY"},
    {"symbol": "USDCHF=X", "name": "USD/CHF"},
    {"symbol": "AUDUSD=X", "name": "AUD/USD"},
    {"symbol": "USDCAD=X", "name": "USD/CAD"},
    {"symbol": "NZDUSD=X", "name": "NZD/USD"},
    {"symbol": "EURGBP=X", "name": "EUR/GBP"},
    {"symbol": "EURJPY=X", "name": "EUR/JPY"},
    {"symbol": "GBPJPY=X", "name": "GBP/JPY"},
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
