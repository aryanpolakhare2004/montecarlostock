"""Technical-indicator feature engineering, using only pandas/numpy (no extra deps)."""
from __future__ import annotations

import numpy as np
import pandas as pd

TECHNICAL_FEATURE_COLUMNS = [
    "return_1d",
    "return_5d",
    "return_10d",
    "sma_5_ratio",
    "sma_10_ratio",
    "sma_20_ratio",
    "sma_50_ratio",
    "volatility_10d",
    "volatility_20d",
    "rsi_14",
    "macd",
    "macd_signal",
    "bollinger_pct_b",
]

VOLUME_FEATURE_COLUMNS = ["volume_change", "volume_ratio_20d"]


def build_technical_features(close: pd.Series, volume: pd.Series | None = None) -> pd.DataFrame:
    """Engineer technical-indicator features from close prices (and optional volume).

    All windows are strictly causal (use only current and past data), so this
    is safe to apply to any price array -- real history or a Monte Carlo
    simulated path.
    """
    df = pd.DataFrame(index=close.index)
    returns = close.pct_change(fill_method=None)

    df["return_1d"] = returns
    df["return_5d"] = close.pct_change(5, fill_method=None)
    df["return_10d"] = close.pct_change(10, fill_method=None)

    for window in (5, 10, 20, 50):
        sma = close.rolling(window).mean()
        df[f"sma_{window}_ratio"] = close / sma - 1.0

    df["volatility_10d"] = returns.rolling(10).std()
    df["volatility_20d"] = returns.rolling(20).std()

    df["rsi_14"] = _rsi(close, 14)

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    signal = macd.ewm(span=9, adjust=False).mean()
    df["macd"] = macd
    df["macd_signal"] = macd - signal

    sma_20 = close.rolling(20).mean()
    std_20 = close.rolling(20).std()
    upper = sma_20 + 2 * std_20
    lower = sma_20 - 2 * std_20
    df["bollinger_pct_b"] = (close - lower) / (upper - lower)

    if volume is not None:
        df["volume_change"] = volume.pct_change(fill_method=None)
        df["volume_ratio_20d"] = volume / volume.rolling(20).mean() - 1.0

    return df


def _rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1 / window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


rsi = _rsi
