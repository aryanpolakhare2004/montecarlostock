"""Simple moving-average crossover strategy."""
from __future__ import annotations

import numpy as np

from .base import Strategy


class MovingAverageCrossover(Strategy):
    """Long whenever the fast SMA is above the slow SMA, flat otherwise."""

    def __init__(self, fast: int = 20, slow: int = 50):
        if fast >= slow:
            raise ValueError("fast window must be smaller than slow window")
        self.fast = fast
        self.slow = slow

    def positions(self, prices: np.ndarray) -> np.ndarray:
        fast_sma = _rolling_mean(prices, self.fast)
        slow_sma = _rolling_mean(prices, self.slow)
        signal = np.where(fast_sma > slow_sma, 1.0, 0.0)
        return signal[:-1]


def _rolling_mean(x: np.ndarray, window: int) -> np.ndarray:
    n = len(x)
    if n < window:
        return np.zeros(n)
    out = np.zeros(n)
    cumsum = np.cumsum(np.insert(x, 0, 0.0))
    out[window - 1:] = (cumsum[window:] - cumsum[:-window]) / window
    return out
