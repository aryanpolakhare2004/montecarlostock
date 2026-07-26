from datetime import datetime, timezone

from mcstock.sentiment.scorer import SENTIMENT_FEATURE_COLUMNS, daily_sentiment_features, score_text


def test_score_text_polarity():
    assert score_text("Stocks surge to record highs on strong earnings") > 0.2
    assert score_text("Company shares plunge amid fraud investigation") < -0.2


def test_daily_sentiment_features_aggregates_by_date():
    items = [
        {"title": "Great quarter, profits soar", "published": datetime(2026, 1, 1, 9, tzinfo=timezone.utc)},
        {"title": "Terrible results, investors flee", "published": datetime(2026, 1, 1, 15, tzinfo=timezone.utc)},
        {"title": "Steady performance reported", "published": datetime(2026, 1, 2, 9, tzinfo=timezone.utc)},
    ]
    features = daily_sentiment_features(items)
    assert list(features.columns) == SENTIMENT_FEATURE_COLUMNS
    assert len(features) == 2
    assert features.loc["2026-01-01", "sentiment_count"] == 2


def test_daily_sentiment_features_empty():
    features = daily_sentiment_features([])
    assert features.empty
    assert list(features.columns) == SENTIMENT_FEATURE_COLUMNS
