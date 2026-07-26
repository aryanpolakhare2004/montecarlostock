"""Free news sourcing and sentiment scoring for mcstock ML strategies."""

from .news_sources import fetch_all_news, fetch_rss_headlines, fetch_yfinance_news
from .scorer import daily_sentiment_features, score_text

__all__ = [
    "fetch_all_news",
    "fetch_rss_headlines",
    "fetch_yfinance_news",
    "daily_sentiment_features",
    "score_text",
]
