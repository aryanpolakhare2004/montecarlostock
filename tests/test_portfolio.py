import numpy as np
import pandas as pd
import pytest

from mcstock.portfolio import portfolio_gbm_paths, summarize_portfolio


def _synthetic_prices(seed=0, n=500):
    rng = np.random.default_rng(seed)
    returns_a = rng.normal(0.0004, 0.01, n)
    returns_b = rng.normal(0.0003, 0.015, n)
    prices_a = 100 * np.exp(np.cumsum(returns_a))
    prices_b = 50 * np.exp(np.cumsum(returns_b))
    return pd.DataFrame({"A": prices_a, "B": prices_b})


def test_portfolio_paths_shape_and_start_value():
    prices = _synthetic_prices()
    paths = portfolio_gbm_paths(prices, weights=[0.6, 0.4], days=20, n_sims=30, initial_value=1000.0, seed=1)
    assert paths.shape == (30, 21)
    assert np.allclose(paths[:, 0], 1000.0)


def test_weights_must_sum_to_one():
    prices = _synthetic_prices()
    with pytest.raises(ValueError):
        portfolio_gbm_paths(prices, weights=[0.5, 0.6], days=10, n_sims=5)


def test_summarize_portfolio_keys():
    prices = _synthetic_prices()
    paths = portfolio_gbm_paths(prices, weights=[0.5, 0.5], days=20, n_sims=200, initial_value=1000.0, seed=3)
    summary = summarize_portfolio(paths)
    assert set(summary) == {"mean", "median", "std", "p05", "p95", "prob_loss"}
