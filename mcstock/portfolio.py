"""Multi-asset portfolio Monte Carlo simulation with correlated GBM paths."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import percentile_summary


def portfolio_gbm_paths(
    prices: pd.DataFrame,
    weights: list[float] | np.ndarray,
    days: int,
    n_sims: int,
    initial_value: float = 1.0,
    trading_days: int = 252,
    seed: int | None = None,
) -> np.ndarray:
    """Simulate correlated GBM paths per asset and combine into portfolio value.

    `prices` holds historical close prices, one column per asset. `weights`
    must align with `prices.columns` and sum to 1. Buy-and-hold is assumed
    (share counts are fixed at t=0; the portfolio is not rebalanced). Returns
    an array of shape (n_sims, days + 1) of total portfolio value.
    """
    weights = np.asarray(weights, dtype=float)
    if not np.isclose(weights.sum(), 1.0):
        raise ValueError("weights must sum to 1")
    if len(weights) != prices.shape[1]:
        raise ValueError("weights length must match number of assets")

    log_rets = np.log(prices / prices.shift(1)).dropna()
    mu = log_rets.mean().to_numpy() * trading_days
    cov = log_rets.cov().to_numpy() * trading_days
    sigma = np.sqrt(np.diag(cov))
    chol = np.linalg.cholesky(cov)

    rng = np.random.default_rng(seed)
    dt = 1.0 / trading_days
    n_assets = len(weights)

    s0 = prices.iloc[-1].to_numpy()
    asset_shares = (weights * initial_value) / s0

    # Fully vectorized across simulations: draw all shocks at once, correlate,
    # cumulate, and combine assets into portfolio value with batched matmuls.
    z = rng.standard_normal((n_sims, days, n_assets))
    correlated_shocks = z @ chol.T
    drift = (mu - 0.5 * sigma**2) * dt
    log_increments = drift + correlated_shocks * np.sqrt(dt)
    asset_paths = s0 * np.exp(np.cumsum(log_increments, axis=1))

    portfolio_values = np.empty((n_sims, days + 1))
    portfolio_values[:, 0] = initial_value
    portfolio_values[:, 1:] = asset_paths @ asset_shares
    return portfolio_values


def summarize_portfolio(paths: np.ndarray) -> dict:
    finals = paths[:, -1]
    start = paths[0, 0]
    summary = percentile_summary(finals)
    summary["prob_loss"] = float(np.mean(finals < start))
    return summary
