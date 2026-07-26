"""Historical (non-bootstrapped) evaluation for ML strategies, plus Monte Carlo
resampling of a strategy's realized daily returns to project robustness.

Sentiment can't be recomputed for a synthetic bootstrapped price path (unlike
pure technical indicators), so sentiment-aware models are evaluated here on
their *actual* held-out historical performance, and that realized return
series is what gets Monte Carlo resampled -- rather than resampling prices
and re-deriving positions from scratch.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def realized_daily_returns(model, X_test: pd.DataFrame, forward_returns: pd.Series) -> pd.Series:
    """Daily strategy returns from a fitted model's predictions on held-out data.

    `forward_returns` must be the actual forward asset return aligned to each
    row of X_test (the same series `label` was derived from).
    """
    positions = model.predict(X_test).astype(float)
    strat_returns = positions * forward_returns.loc[X_test.index].to_numpy()
    return pd.Series(strat_returns, index=X_test.index)


def resample_return_series(
    daily_returns: np.ndarray,
    days: int,
    n_sims: int,
    block_size: int = 5,
    seed: int | None = None,
) -> np.ndarray:
    """Block-bootstrap a realized daily-return series into many synthetic equity curves.

    Returns an array of shape (n_sims, days + 1) of cumulative equity, starting at 1.0.
    """
    rng = np.random.default_rng(seed)
    n_returns = len(daily_returns)
    if n_returns < block_size:
        raise ValueError("Not enough realized returns for the requested block size")

    n_blocks = int(np.ceil(days / block_size))
    equity = np.empty((n_sims, days + 1))
    equity[:, 0] = 1.0

    for sim in range(n_sims):
        starts = rng.integers(0, n_returns - block_size + 1, size=n_blocks)
        sampled = np.concatenate([daily_returns[s:s + block_size] for s in starts])[:days]
        equity[sim, 1:] = np.cumprod(1.0 + sampled)

    return equity


def summarize_equity(equity: np.ndarray) -> dict:
    finals = equity[:, -1]
    running_max = np.maximum.accumulate(equity, axis=1)
    drawdowns = ((equity - running_max) / running_max).min(axis=1)
    return {
        "mean_return": float(np.mean(finals) - 1.0),
        "median_return": float(np.median(finals) - 1.0),
        "p05_return": float(np.percentile(finals, 5) - 1.0),
        "p95_return": float(np.percentile(finals, 95) - 1.0),
        "prob_profit": float(np.mean(finals > 1.0)),
        "mean_max_drawdown": float(np.mean(drawdowns)),
        "worst_max_drawdown": float(np.min(drawdowns)),
    }
