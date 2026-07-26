import numpy as np

from mcstock.backtest import backtest_strategy, resample_paths
from mcstock.strategies.buy_and_hold import BuyAndHold


def test_resample_paths_shape_and_start():
    log_returns = np.random.default_rng(0).normal(0.0003, 0.01, 500)
    paths = resample_paths(log_returns, s0=100.0, days=30, n_sims=20, block_size=5, seed=1)
    assert paths.shape == (20, 31)
    assert np.allclose(paths[:, 0], 100.0)


def test_backtest_buy_and_hold_matches_price_return():
    log_returns = np.random.default_rng(0).normal(0.0003, 0.01, 500)
    result = backtest_strategy(BuyAndHold(), log_returns, s0=100.0, days=30, n_sims=50, block_size=5, seed=2)
    paths = result["paths"]
    expected_returns = paths[:, -1] / paths[:, 0] - 1.0
    assert np.allclose(result["total_returns"], expected_returns, atol=1e-9)
