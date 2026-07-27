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
