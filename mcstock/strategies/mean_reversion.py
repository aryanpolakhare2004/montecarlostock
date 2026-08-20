"""RSI-based mean reversion strategy."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import features
from .base import Strategy


class MeanReversion(Strategy):
    """Long once RSI drops into oversold territory, flat once it climbs back
    into overbought territory, holding the prior position in between.
    """

    def __init__(self, rsi_period: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        if rsi_period <= 0:
            raise ValueError("rsi_period must be positive")
        if oversold >= overbought:
            raise ValueError("oversold threshold must be smaller than overbought threshold")
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def positions(self, prices: np.ndarray) -> np.ndarray:
        rsi = features.rsi(pd.Series(prices), self.rsi_period)
        raw = pd.Series(np.nan, index=rsi.index)
        raw[rsi <= self.oversold] = 1.0
        raw[rsi >= self.overbought] = 0.0
        signal = raw.ffill().fillna(0.0)
        return signal.to_numpy()[:-1]
