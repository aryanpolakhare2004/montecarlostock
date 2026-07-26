import numpy as np
import pytest

from mcstock.strategies.buy_and_hold import BuyAndHold
from mcstock.strategies.moving_average import MovingAverageCrossover


def test_buy_and_hold_always_long():
    prices = np.array([100.0, 101.0, 102.0, 103.0])
    positions = BuyAndHold().positions(prices)
    assert np.array_equal(positions, np.ones(3))


def test_moving_average_crossover_signals():
    prices = np.concatenate([np.linspace(100, 90, 30), np.linspace(90, 130, 40)])
    strat = MovingAverageCrossover(fast=3, slow=10)
    positions = strat.positions(prices)
    assert len(positions) == len(prices) - 1
    assert set(np.unique(positions)) <= {0.0, 1.0}
    assert positions[-1] == 1.0


def test_fast_must_be_smaller_than_slow():
    with pytest.raises(ValueError):
        MovingAverageCrossover(fast=10, slow=5)
