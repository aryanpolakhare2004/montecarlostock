"""Shared summary-statistics helpers for Monte Carlo distributions."""
from __future__ import annotations

import numpy as np


def percentile_summary(values: np.ndarray) -> dict:
    """Core mean/median/std/p05/p95 summary shared across terminal-value distributions."""
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "std": float(np.std(values, ddof=1)),
        "p05": float(np.percentile(values, 5)),
        "p95": float(np.percentile(values, 95)),
    }


def percentile_bands(paths: np.ndarray, percentiles: tuple[int, ...] = (5, 25, 50, 75, 95)) -> list[dict]:
    """Per-step percentile band for a 2D (n_sims, n_steps) path array, for a fan chart."""
    values = np.percentile(paths, percentiles, axis=0)
    return [
        {"step": step, **{f"p{p}": float(values[i, step]) for i, p in enumerate(percentiles)}}
        for step in range(paths.shape[1])
    ]


def histogram_bins(values: np.ndarray, bins: int = 30) -> list[dict]:
    """Bin a 1D distribution into (bin_start, bin_end, count) rows, for a histogram chart."""
    counts, edges = np.histogram(values, bins=bins)
    return [
        {"bin_start": float(edges[i]), "bin_end": float(edges[i + 1]), "count": int(counts[i])}
        for i in range(len(counts))
    ]


def returns_and_drawdown_summary(total_returns: np.ndarray, max_drawdowns: np.ndarray) -> dict:
    """Shared summary for a distribution of strategy total returns plus per-path max drawdowns."""
    return {
        "mean_return": float(np.mean(total_returns)),
        "median_return": float(np.median(total_returns)),
        "std_return": float(np.std(total_returns, ddof=1)),
        "p05_return": float(np.percentile(total_returns, 5)),
        "p95_return": float(np.percentile(total_returns, 95)),
        "prob_profit": float(np.mean(total_returns > 0)),
        "mean_max_drawdown": float(np.mean(max_drawdowns)),
        "worst_max_drawdown": float(np.min(max_drawdowns)),
    }
