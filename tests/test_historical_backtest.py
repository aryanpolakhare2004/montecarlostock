import numpy as np

from mcstock.historical_backtest import resample_return_series, summarize_equity


def test_resample_return_series_shape_and_start():
    daily_returns = np.random.default_rng(0).normal(0.0005, 0.01, 300)
    equity = resample_return_series(daily_returns, days=30, n_sims=25, block_size=5, seed=1)
    assert equity.shape == (25, 31)
    assert np.allclose(equity[:, 0], 1.0)


def test_summarize_equity_keys_and_drawdown_sign():
    daily_returns = np.random.default_rng(0).normal(0.0005, 0.01, 300)
    equity = resample_return_series(daily_returns, days=30, n_sims=200, block_size=5, seed=2)
    summary = summarize_equity(equity)
    assert set(summary) == {
        "mean_return", "median_return", "p05_return", "p95_return",
        "prob_profit", "mean_max_drawdown", "worst_max_drawdown",
    }
    assert summary["worst_max_drawdown"] <= summary["mean_max_drawdown"] <= 0.0
