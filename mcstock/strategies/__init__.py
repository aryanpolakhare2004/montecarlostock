"""Trading strategies for Monte Carlo backtests."""

from .base import Strategy
from .buy_and_hold import BuyAndHold
from .ml_classifier import MLClassifierStrategy
from .moving_average import MovingAverageCrossover

__all__ = ["Strategy", "BuyAndHold", "MovingAverageCrossover", "MLClassifierStrategy"]
