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
