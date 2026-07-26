"""Shared block-bootstrap resampling for Monte Carlo return simulations."""
from __future__ import annotations

import numpy as np


def block_bootstrap_samples(
    returns: np.ndarray,
    days: int,
    n_sims: int,
    block_size: int = 5,
    seed: int | None = None,
) -> np.ndarray:
    """Block-bootstrap `returns` into an (n_sims, days) matrix of resampled values.

    Each simulated row concatenates randomly chosen contiguous blocks of
    length `block_size` from `returns`, preserving local autocorrelation
    better than an iid resample. Fully vectorized across simulations.
    """
    rng = np.random.default_rng(seed)
    n_returns = len(returns)
    if n_returns < block_size:
        raise ValueError("Not enough historical returns for the requested block size")

    n_blocks = int(np.ceil(days / block_size))
    starts = rng.integers(0, n_returns - block_size + 1, size=(n_sims, n_blocks))
    idx = starts[:, :, None] + np.arange(block_size)
    return returns[idx].reshape(n_sims, n_blocks * block_size)[:, :days]
