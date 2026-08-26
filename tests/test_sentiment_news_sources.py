from datetime import datetime, timezone

from mcstock.sentiment import news_sources


def test_fetch_all_news_skips_failing_source(monkeypatch):
    fixed_items = [{"title": "Headline", "published": datetime(2026, 1, 1, tzinfo=timezone.utc), "source": "yfinance"}]

    def fake_yfinance(ticker):
        return fixed_items

    def boom_reddit(ticker):
        raise RuntimeError("missing Reddit credentials")

    monkeypatch.setitem(news_sources._SOURCE_FETCHERS, "yfinance", fake_yfinance)
    monkeypatch.setitem(news_sources._SOURCE_FETCHERS, "reddit", boom_reddit)

    items = news_sources.fetch_all_news("AAPL", sources=["yfinance", "reddit"])
    assert items == fixed_items


def test_fetch_all_news_unknown_source_is_ignored():
    items = news_sources.fetch_all_news("AAPL", sources=["not-a-real-source"])
    assert items == []
