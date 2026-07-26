"""Historical price data access via yfinance."""
from __future__ import annotations

import numpy as np
import pandas as pd
import yfinance as yf


def download_history(ticker: str, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
    """Download full OHLCV history for a single ticker (needed for volume features)."""
    hist = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
    if hist.empty:
        raise ValueError(f"No price data returned for ticker '{ticker}'")
    return hist


def download_close_prices(tickers: list[str], period: str = "5y", interval: str = "1d") -> pd.DataFrame:
    """Download aligned historical close prices for one or more tickers."""
    frames = {ticker: download_history(ticker, period, interval)["Close"] for ticker in tickers}
    return pd.DataFrame(frames).dropna()


def download_prices(ticker: str, period: str = "5y", interval: str = "1d") -> pd.Series:
    """Download historical close prices for a single ticker."""
    return download_close_prices([ticker], period=period, interval=interval)[ticker]


def log_returns(prices: pd.Series) -> pd.Series:
    return np.log(prices / prices.shift(1)).dropna()


def annualize_drift_vol(returns: pd.Series, trading_days: int = 252) -> tuple[float, float]:
    """Convert a series of daily log returns into annualized drift and volatility."""
    mu = returns.mean() * trading_days
    sigma = returns.std(ddof=1) * np.sqrt(trading_days)
    return float(mu), float(sigma)
