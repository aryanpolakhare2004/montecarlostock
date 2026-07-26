"""Base class for trading strategies used in Monte Carlo backtests."""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class Strategy(ABC):
    """Turns a price path into a series of position sizes.

    `positions(prices)` returns an array of length `len(prices) - 1`: index i
    is the fraction of capital held long (0.0-1.0) while earning the return
    from day i to day i+1.
    """

    @abstractmethod
    def positions(self, prices: np.ndarray) -> np.ndarray:
        raise NotImplementedError
