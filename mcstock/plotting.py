"""Matplotlib helpers for saving Monte Carlo simulation charts."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def _finish_and_save(fig, ax, title: str, xlabel: str, ylabel: str, out_path: str) -> None:
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_paths(paths: np.ndarray, out_path: str, title: str, max_paths: int = 200) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    n_show = min(max_paths, paths.shape[0])
    for i in range(n_show):
        ax.plot(paths[i], linewidth=0.5, alpha=0.4)
    ax.plot(np.mean(paths, axis=0), color="black", linewidth=2, label="mean path")
    _finish_and_save(fig, ax, title, "Trading day", "Value", out_path)


def plot_final_distribution(values: np.ndarray, out_path: str, title: str) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(values, bins=50, color="steelblue", edgecolor="white")
    ax.axvline(np.median(values), color="black", linestyle="--", label="median")
    _finish_and_save(fig, ax, title, "Final value", "Frequency", out_path)
