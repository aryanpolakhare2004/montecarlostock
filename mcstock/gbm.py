"""Geometric Brownian Motion price-path simulation."""
from __future__ import annotations

import numpy as np

from .stats import percentile_summary


def simulate_gbm_paths(
    s0: float,
    mu: float,
    sigma: float,
    days: int,
    n_sims: int,
    trading_days: int = 252,
    seed: int | None = None,
) -> np.ndarray:
    """Simulate `n_sims` GBM price paths of length `days` trading days.

    `mu` and `sigma` are annualized drift and volatility. Returns an array of
    shape (n_sims, days + 1), where column 0 is the starting price `s0`.
    """
    rng = np.random.default_rng(seed)
    dt = 1.0 / trading_days
    z = rng.standard_normal((n_sims, days))
    increments = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
    log_paths = np.cumsum(increments, axis=1)
    return s0 * np.exp(np.hstack([np.zeros((n_sims, 1)), log_paths]))


def summarize_final_prices(paths: np.ndarray) -> dict:
    """Summary statistics for the terminal (final-day) price distribution."""
    finals = paths[:, -1]
    start = paths[0, 0]
    summary = percentile_summary(finals)
    summary["p25"] = float(np.percentile(finals, 25))
    summary["p75"] = float(np.percentile(finals, 75))
    summary["prob_above_start"] = float(np.mean(finals > start))
    return summary
