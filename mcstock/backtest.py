"""Monte Carlo strategy backtesting via block-bootstrapped historical returns."""
from __future__ import annotations

import numpy as np

from .bootstrap import block_bootstrap_samples
from .stats import returns_and_drawdown_summary
from .strategies.base import Strategy


def resample_paths(
    log_returns: np.ndarray,
    s0: float,
    days: int,
    n_sims: int,
    block_size: int = 5,
    seed: int | None = None,
) -> np.ndarray:
    """Build synthetic price paths by block-bootstrapping historical log returns."""
    sampled = block_bootstrap_samples(log_returns, days, n_sims, block_size, seed)
    paths = np.empty((n_sims, days + 1))
    paths[:, 0] = s0
    paths[:, 1:] = s0 * np.exp(np.cumsum(sampled, axis=1))
    return paths


def backtest_strategy(
    strategy: Strategy,
    log_returns: np.ndarray,
    s0: float,
    days: int,
    n_sims: int,
    block_size: int = 5,
    seed: int | None = None,
) -> dict:
    """Run a Monte Carlo backtest of `strategy` over resampled price paths."""
    paths = resample_paths(log_returns, s0, days, n_sims, block_size, seed)
    daily_returns = np.diff(paths, axis=1) / paths[:, :-1]

    total_returns = np.empty(n_sims)
    max_drawdowns = np.empty(n_sims)

    for sim in range(n_sims):
        positions = strategy.positions(paths[sim])
        equity = np.cumprod(1.0 + positions * daily_returns[sim])
        total_returns[sim] = equity[-1] - 1.0
        running_max = np.maximum.accumulate(equity)
        max_drawdowns[sim] = np.min((equity - running_max) / running_max)

    summary = returns_and_drawdown_summary(total_returns, max_drawdowns)
    summary["total_returns"] = total_returns
    summary["paths"] = paths
    return summary
