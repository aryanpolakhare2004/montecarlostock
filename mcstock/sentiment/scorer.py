"""VADER-based sentiment scoring and daily aggregation."""
from __future__ import annotations

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

SENTIMENT_FEATURE_COLUMNS = [
    "sentiment_mean",
    "sentiment_std",
    "sentiment_count",
    "pct_positive",
    "pct_negative",
]

_analyzer = SentimentIntensityAnalyzer()


def score_text(text: str) -> float:
    """Compound VADER sentiment score in [-1, 1]."""
    return _analyzer.polarity_scores(text)["compound"]


def daily_sentiment_features(items: list[dict]) -> pd.DataFrame:
    """Aggregate scored headlines into one row per calendar date.

    `items` are dicts with 'title' and 'published' (datetime) keys, as
    produced by mcstock.sentiment.news_sources. Returns a tz-naive,
    date-indexed DataFrame with columns: sentiment_mean, sentiment_std,
    sentiment_count, pct_positive, pct_negative.
    """
    if not items:
        return pd.DataFrame(columns=SENTIMENT_FEATURE_COLUMNS)

    rows = []
    for item in items:
        ts = pd.Timestamp(item["published"])
        if ts.tzinfo is not None:
            ts = ts.tz_convert("UTC").tz_localize(None)
        rows.append({"date": ts.normalize(), "score": score_text(item["title"])})

    grouped = pd.DataFrame(rows).groupby("date")["score"]
    out = pd.DataFrame({
        "sentiment_mean": grouped.mean(),
        "sentiment_std": grouped.std(ddof=0).fillna(0.0),
        "sentiment_count": grouped.count(),
        "pct_positive": grouped.apply(lambda s: (s > 0.05).mean()),
        "pct_negative": grouped.apply(lambda s: (s < -0.05).mean()),
    })
    return out.sort_index()
