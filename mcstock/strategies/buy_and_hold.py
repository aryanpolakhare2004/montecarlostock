"""Baseline always-long strategy."""
from __future__ import annotations

import numpy as np

from .base import Strategy


class BuyAndHold(Strategy):
    def positions(self, prices: np.ndarray) -> np.ndarray:
        return np.ones(len(prices) - 1)
