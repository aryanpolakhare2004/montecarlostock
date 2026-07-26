"""Build labeled (technical + optional sentiment) feature datasets for ML strategies."""
from __future__ import annotations

import pandas as pd

from .. import data as data_module
from .._dates import to_naive_utc
from ..features import build_technical_features
from ..sentiment.news_sources import fetch_all_news
from ..sentiment.scorer import SENTIMENT_FEATURE_COLUMNS, daily_sentiment_features


def _sentiment_features(ticker: str, sentiment_sources: list[str] | None) -> pd.DataFrame | None:
    if not sentiment_sources:
        return None
    news_items = fetch_all_news(ticker, sources=sentiment_sources)
    return daily_sentiment_features(news_items)


def _build_features(ticker: str, period: str, sentiment_sources, use_volume: bool) -> tuple[pd.DataFrame, pd.Series]:
    history = data_module.download_history(ticker, period=period)
    close = history["Close"]
    volume = history["Volume"] if use_volume else None

    features = build_technical_features(close, volume)
    features.index = to_naive_utc(features.index)

    sentiment = _sentiment_features(ticker, sentiment_sources)
    if sentiment is not None:
        features = features.join(sentiment, how="left")
        features[SENTIMENT_FEATURE_COLUMNS] = features[SENTIMENT_FEATURE_COLUMNS].fillna(0.0)

    close_naive = close.copy()
    close_naive.index = to_naive_utc(close_naive.index)
    return features, close_naive


def build_dataset(
    ticker: str,
    period: str = "5y",
    horizon: int = 1,
    sentiment_sources: list[str] | None = None,
    use_volume: bool = True,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Build (X, y, forward_return) for next-`horizon`-day up/down prediction.

    `sentiment_sources` may include "yfinance", "rss", "reddit" (or be
    None/empty for a technical-only dataset). `forward_return` is the actual
    forward percentage return backing the binary label -- useful for turning
    model predictions into realized strategy returns.
    """
    features, close = _build_features(ticker, period, sentiment_sources, use_volume)

    forward_return = close.pct_change(horizon, fill_method=None).shift(-horizon).rename("forward_return")
    label = (forward_return > 0).astype(int).rename("label")

    combined = features.join(forward_return, how="inner").join(label, how="inner").dropna()
    X = combined.drop(columns=["label", "forward_return"])
    y = combined["label"]
    forward = combined["forward_return"]
    return X, y, forward


def build_latest_features(
    ticker: str,
    period: str = "6mo",
    sentiment_sources: list[str] | None = None,
    use_volume: bool = True,
) -> pd.Series:
    """Feature row for the most recent trading day, for live prediction (no label)."""
    features, _ = _build_features(ticker, period, sentiment_sources, use_volume)
    return features.iloc[-1]
