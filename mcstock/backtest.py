"""Monte Carlo strategy backtesting via block-bootstrapped historical returns."""
from __future__ import annotations

import numpy as np

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
    rng = np.random.default_rng(seed)
    n_returns = len(log_returns)
    if n_returns < block_size:
        raise ValueError("Not enough historical returns for the requested block size")

    n_blocks = int(np.ceil(days / block_size))
    paths = np.empty((n_sims, days + 1))
    paths[:, 0] = s0

    for sim in range(n_sims):
        starts = rng.integers(0, n_returns - block_size + 1, size=n_blocks)
        sampled = np.concatenate([log_returns[s:s + block_size] for s in starts])[:days]
        paths[sim, 1:] = s0 * np.exp(np.cumsum(sampled))

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

    return {
        "mean_return": float(np.mean(total_returns)),
        "median_return": float(np.median(total_returns)),
        "std_return": float(np.std(total_returns, ddof=1)),
        "p05_return": float(np.percentile(total_returns, 5)),
        "p95_return": float(np.percentile(total_returns, 95)),
        "prob_profit": float(np.mean(total_returns > 0)),
        "mean_max_drawdown": float(np.mean(max_drawdowns)),
        "worst_max_drawdown": float(np.min(max_drawdowns)),
        "total_returns": total_returns,
        "paths": paths,
    }
