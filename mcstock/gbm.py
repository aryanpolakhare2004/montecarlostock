"""Geometric Brownian Motion price-path simulation."""
from __future__ import annotations

import numpy as np


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
    return {
        "mean": float(np.mean(finals)),
        "median": float(np.median(finals)),
        "std": float(np.std(finals, ddof=1)),
        "p05": float(np.percentile(finals, 5)),
        "p25": float(np.percentile(finals, 25)),
        "p75": float(np.percentile(finals, 75)),
        "p95": float(np.percentile(finals, 95)),
        "prob_above_start": float(np.mean(finals > start)),
    }
