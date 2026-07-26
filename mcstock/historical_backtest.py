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

from .bootstrap import block_bootstrap_samples
from .stats import returns_and_drawdown_summary


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
    sampled = block_bootstrap_samples(daily_returns, days, n_sims, block_size, seed)
    equity = np.empty((n_sims, days + 1))
    equity[:, 0] = 1.0
    equity[:, 1:] = np.cumprod(1.0 + sampled, axis=1)
    return equity


def summarize_equity(equity: np.ndarray) -> dict:
    finals = equity[:, -1]
    running_max = np.maximum.accumulate(equity, axis=1)
    drawdowns = ((equity - running_max) / running_max).min(axis=1)
    return returns_and_drawdown_summary(finals - 1.0, drawdowns)
