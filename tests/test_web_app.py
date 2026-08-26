from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from mcstock.web import app as app_module
from mcstock.web import db


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "mcstock.db")
    db.init_db()
    return TestClient(app_module.app)


def test_index_serves_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "mcstock" in resp.text.lower()


def test_empty_history_endpoints(client):
    assert client.get("/api/runs").json() == []
    assert client.get("/api/models").json() == []


def test_missing_run_chart_is_404(client):
    resp = client.get("/api/runs/999/chart")
    assert resp.status_code == 404


def test_predict_unknown_model_is_404(client):
    resp = client.post("/api/predict", json={"model_id": 999})
    assert resp.status_code == 404


def test_backtest_ml_unknown_model_is_404(client):
    resp = client.post("/api/backtest_ml", json={"model_id": 999})
    assert resp.status_code == 404


def test_compare_unknown_model_is_404_before_any_network_call(client):
    # model_ids are validated before the ticker is downloaded, so this must
    # 404 without needing network access.
    resp = client.post("/api/compare", json={"ticker": "AAPL", "model_ids": [999]})
    assert resp.status_code == 404


def test_strategy_ml_technical_without_model_id_is_400(client):
    resp = client.post("/api/strategy", json={"ticker": "AAPL", "strategy": "ml-technical"})
    assert resp.status_code == 400


def test_strategy_unknown_strategy_is_400(client):
    resp = client.post("/api/strategy", json={"ticker": "AAPL", "strategy": "not-a-strategy"})
    assert resp.status_code == 400


def test_portfolio_weights_mismatch_is_400(client):
    resp = client.post(
        "/api/portfolio", json={"tickers": ["AAPL", "MSFT"], "weights": [1.0]}
    )
    assert resp.status_code == 400


# ---- sentiment ----

def test_sentiment_unknown_source_group_is_400(client):
    resp = client.post("/api/sentiment", json={"ticker": "AAPL", "source_group": "none"})
    assert resp.status_code == 400


def test_sentiment_endpoint_returns_scored_items(client, monkeypatch):
    fixed_items = [
        {"title": "Stocks surge to record highs", "published": datetime(2026, 1, 2, tzinfo=timezone.utc), "source": "yfinance"},
        {"title": "Shares plunge amid investigation", "published": datetime(2026, 1, 1, tzinfo=timezone.utc), "source": "yfinance"},
    ]
    monkeypatch.setattr(app_module.sentiment_news, "fetch_all_news", lambda ticker, sources: fixed_items)

    resp = client.post("/api/sentiment", json={"ticker": "aapl", "source_group": "yfinance"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["ticker"] == "AAPL"
    assert body["item_count"] == 2
    assert len(body["daily"]) == 2
    # newest first
    assert body["items"][0]["title"] == "Stocks surge to record highs"


# ---- alerts ----

def test_alert_add_unknown_metric_is_400(client):
    resp = client.post("/api/alerts", json={"ticker": "AAPL", "metric": "bogus", "operator": "above", "threshold": 100})
    assert resp.status_code == 400


def test_alert_add_unknown_operator_is_400(client):
    resp = client.post("/api/alerts", json={"ticker": "AAPL", "metric": "price", "operator": "bogus", "threshold": 100})
    assert resp.status_code == 400


def test_alert_lifecycle(client):
    resp = client.post("/api/alerts", json={"ticker": "AAPL", "metric": "price", "operator": "above", "threshold": 100})
    assert resp.status_code == 200
    alert = resp.json()
    assert alert["ticker"] == "AAPL"
    assert alert["triggered_at"] is None

    listed = client.get("/api/alerts").json()
    assert [a["id"] for a in listed] == [alert["id"]]

    resp = client.delete(f"/api/alerts/{alert['id']}")
    assert resp.status_code == 200
    assert client.get("/api/alerts").json() == []


# ---- portfolio optimize ----

def test_portfolio_optimize_empty_tickers_is_400(client):
    resp = client.post("/api/portfolio/optimize", json={"tickers": [], "objective": "max_sharpe"})
    assert resp.status_code == 400


def test_portfolio_optimize_returns_weights(client, monkeypatch):
    rng = np.random.default_rng(0)
    n = 300
    prices = pd.DataFrame({
        "AAPL": 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.01, n))),
        "MSFT": 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, n))),
    })
    monkeypatch.setattr(app_module.data, "download_close_prices", lambda tickers, period="5y": prices)

    resp = client.post("/api/portfolio/optimize", json={"tickers": ["AAPL", "MSFT"], "objective": "min_variance"})
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["weights"]) == {"AAPL", "MSFT"}
    assert abs(sum(body["weights"].values()) - 1.0) < 1e-6
    assert all(w >= -1e-9 for w in body["weights"].values())


# ---- watchlist bulk import ----

def test_watchlist_bulk_add_partial_success(client, monkeypatch):
    def fake_quick_summary(ticker):
        if ticker.upper() == "BADTICKER":
            raise ValueError(f"Ticker '{ticker}' not found")
        return {"ticker": ticker.upper(), "company_name": ticker.upper(), "last_price": 1.0,
                "day_change_pct": None, "sparkline": [], "scores": {}, "composite": None}

    monkeypatch.setattr(app_module.fundamentals_watchlist, "quick_summary", fake_quick_summary)

    resp = client.post("/api/watchlist/bulk", json={"tickers": ["AAPL", "MSFT", "BADTICKER", "aapl"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["added"] == ["AAPL", "MSFT"]
    assert list(body["errors"]) == ["BADTICKER"]
