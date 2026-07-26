"""Free news/text sources for sentiment analysis. No paid API keys required,
except Reddit (which needs a free app registered at
https://www.reddit.com/prefs/apps).
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import feedparser
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_yfinance_news(ticker: str) -> list[dict]:
    """Headlines yfinance already has cached for a ticker. No API key required."""
    items = []
    for entry in yf.Ticker(ticker).news:
        content = entry.get("content", {})
        title = content.get("title")
        pub_date = content.get("pubDate") or content.get("displayTime")
        if not title or not pub_date:
            continue
        items.append({"title": title, "published": _parse_iso(pub_date), "source": "yfinance"})
    return items


def fetch_rss_headlines(ticker: str, extra_feed_urls: list[str] | None = None) -> list[dict]:
    """Headlines from free RSS feeds (Google News search RSS by default)."""
    feed_urls = list(extra_feed_urls or [])
    feed_urls.append(f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en")

    items = []
    for url in feed_urls:
        parsed = feedparser.parse(url)
        for entry in parsed.entries:
            title = entry.get("title")
            published = entry.get("published_parsed")
            if not title or not published:
                continue
            items.append({
                "title": title,
                "published": datetime(*published[:6], tzinfo=timezone.utc),
                "source": "rss",
            })
    return items


def fetch_reddit_posts(
    ticker: str,
    subreddits: tuple[str, ...] = ("stocks", "investing", "wallstreetbets"),
    limit: int = 50,
    client_id: str | None = None,
    client_secret: str | None = None,
    user_agent: str = "mcstock-sentiment/0.1",
) -> list[dict]:
    """Posts mentioning `ticker` via the free-tier Reddit API.

    Create a free "script" app at https://www.reddit.com/prefs/apps, then pass
    the client_id/client_secret here or set the REDDIT_CLIENT_ID /
    REDDIT_CLIENT_SECRET environment variables.
    """
    import praw

    client_id = client_id or os.environ.get("REDDIT_CLIENT_ID")
    client_secret = client_secret or os.environ.get("REDDIT_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "Reddit sentiment requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET "
            "(create a free app at https://www.reddit.com/prefs/apps)"
        )

    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

    items = []
    for sub in subreddits:
        for submission in reddit.subreddit(sub).search(ticker, limit=limit, sort="new"):
            items.append({
                "title": submission.title,
                "published": datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
                "source": f"reddit/{sub}",
            })
    return items


_SOURCE_FETCHERS = {
    "yfinance": fetch_yfinance_news,
    "rss": fetch_rss_headlines,
    "reddit": fetch_reddit_posts,
}


def fetch_all_news(ticker: str, sources: list[str] = ("yfinance", "rss", "reddit")) -> list[dict]:
    """Combine news items across sources, skipping any that fail (e.g. missing
    Reddit credentials) with a logged warning rather than raising.
    """
    items: list[dict] = []
    for name in sources:
        fetch_fn = _SOURCE_FETCHERS.get(name)
        if fetch_fn is None:
            continue
        try:
            items.extend(fetch_fn(ticker))
        except Exception as exc:
            logger.warning("skipping %s news source: %s", name, exc)
    return items


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
