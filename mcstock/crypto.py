"""A curated list of common cryptocurrencies (yfinance symbols) and a fast
per-symbol quote -- no fundamentals/SEC data involved, since crypto assets
aren't companies.
"""
from __future__ import annotations

from . import data

CRYPTOCURRENCIES = [
    {"symbol": "BTC-USD", "name": "Bitcoin"},
    {"symbol": "ETH-USD", "name": "Ethereum"},
    {"symbol": "SOL-USD", "name": "Solana"},
    {"symbol": "BNB-USD", "name": "BNB"},
    {"symbol": "XRP-USD", "name": "XRP"},
    {"symbol": "ADA-USD", "name": "Cardano"},
    {"symbol": "DOGE-USD", "name": "Dogecoin"},
    {"symbol": "AVAX-USD", "name": "Avalanche"},
    {"symbol": "DOT-USD", "name": "Polkadot"},
    {"symbol": "LINK-USD", "name": "Chainlink"},
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
