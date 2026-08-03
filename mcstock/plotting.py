"""Matplotlib helpers for rendering Monte Carlo simulation charts to PNG bytes."""
from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def _render_png(fig, ax, title: str, xlabel: str, ylabel: str, show_legend: bool = True) -> bytes:
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if show_legend:
        ax.legend()
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    return buf.getvalue()


def plot_paths(paths: np.ndarray, title: str, max_paths: int = 200) -> bytes:
    fig, ax = plt.subplots(figsize=(10, 6))
    n_show = min(max_paths, paths.shape[0])
    for i in range(n_show):
        ax.plot(paths[i], linewidth=0.5, alpha=0.4)
    ax.plot(np.mean(paths, axis=0), color="black", linewidth=2, label="mean path")
    return _render_png(fig, ax, title, "Trading day", "Value")


def plot_final_distribution(values: np.ndarray, title: str) -> bytes:
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(values, bins=50, color="steelblue", edgecolor="white")
    ax.axvline(np.median(values), color="black", linestyle="--", label="median")
    return _render_png(fig, ax, title, "Final value", "Frequency")


def plot_strategy_comparison(mean_returns: dict[str, float]) -> bytes:
    """Bar chart ranking strategies by mean Monte Carlo return, for /api/compare."""
    names = list(mean_returns.keys())
    values = [mean_returns[name] for name in names]
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ["#3ecf8e" if v >= 0 else "#ef6f6f" for v in values]
    ax.bar(names, values, color=colors)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.tick_params(axis="x", rotation=20)
    return _render_png(fig, ax, "Strategy comparison (mean return)", "Strategy", "Mean return", show_legend=False)


def plot_fundamentals_overview(metrics_history: list[dict], title: str) -> bytes:
    """Revenue, net income, and free cash flow by fiscal year, for the fundamentals dashboard."""
    years = [row["fiscal_year"] for row in metrics_history]
    fig, ax = plt.subplots(figsize=(10, 6))
    for key, label, color in (
        ("revenue", "Revenue", "#4f8cff"),
        ("net_income", "Net income", "#3ecf8e"),
        ("free_cash_flow", "Free cash flow", "#f2a93b"),
    ):
        values = [row.get(key) for row in metrics_history]
        ax.plot(years, values, marker="o", label=label, color=color)
    ax.axhline(0, color="gray", linewidth=0.8)
    return _render_png(fig, ax, title, "Fiscal year", "USD")


def save_png(png_bytes: bytes, out_path: str) -> None:
    with open(out_path, "wb") as f:
        f.write(png_bytes)
