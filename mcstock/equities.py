"""A curated list of major, liquid equities across sectors, plus a fast
per-symbol quote -- mirrors commodities/crypto/forex, but these are real
companies so fundamentals data is available for them elsewhere (Analyst,
Price, Watchlist, etc.).
"""
from __future__ import annotations

from . import data

EQUITIES = [
    {"symbol": "AAPL", "name": "Apple"},
    {"symbol": "MSFT", "name": "Microsoft"},
    {"symbol": "GOOGL", "name": "Alphabet"},
    {"symbol": "AMZN", "name": "Amazon"},
    {"symbol": "NVDA", "name": "NVIDIA"},
    {"symbol": "META", "name": "Meta Platforms"},
    {"symbol": "TSLA", "name": "Tesla"},
    {"symbol": "AVGO", "name": "Broadcom"},
    {"symbol": "AMD", "name": "Advanced Micro Devices"},
    {"symbol": "NFLX", "name": "Netflix"},
    {"symbol": "JPM", "name": "JPMorgan Chase"},
    {"symbol": "BAC", "name": "Bank of America"},
    {"symbol": "V", "name": "Visa"},
    {"symbol": "MA", "name": "Mastercard"},
    {"symbol": "JNJ", "name": "Johnson & Johnson"},
    {"symbol": "UNH", "name": "UnitedHealth Group"},
    {"symbol": "PFE", "name": "Pfizer"},
    {"symbol": "WMT", "name": "Walmart"},
    {"symbol": "PG", "name": "Procter & Gamble"},
    {"symbol": "KO", "name": "Coca-Cola"},
    {"symbol": "HD", "name": "Home Depot"},
    {"symbol": "MCD", "name": "McDonald's"},
    {"symbol": "NKE", "name": "Nike"},
    {"symbol": "DIS", "name": "Walt Disney"},
    {"symbol": "XOM", "name": "Exxon Mobil"},
    {"symbol": "CVX", "name": "Chevron"},
    {"symbol": "CAT", "name": "Caterpillar"},
    {"symbol": "BA", "name": "Boeing"},
    {"symbol": "NEE", "name": "NextEra Energy"},
    {"symbol": "LIN", "name": "Linde"},
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
