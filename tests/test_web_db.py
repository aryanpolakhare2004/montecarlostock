import pytest

from mcstock.web import db


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "mcstock.db")
    db.init_db()
    return db


def test_record_and_list_runs(temp_db):
    run_id = temp_db.record_run("price", "AAPL", {"days": 10}, {"mean": 1.0}, b"pngbytes")
    runs = temp_db.list_runs()
    assert len(runs) == 1
    assert runs[0]["id"] == run_id
    assert runs[0]["ticker"] == "AAPL"
    assert runs[0]["has_chart"] is True

    full = temp_db.get_run(run_id)
    assert full["chart_png"] == b"pngbytes"
    assert full["summary"] == {"mean": 1.0}


def test_record_run_without_chart(temp_db):
    run_id = temp_db.record_run("train", "AAPL", {}, {"test_accuracy": 0.5}, None)
    runs = temp_db.list_runs()
    assert runs[0]["id"] == run_id
    assert runs[0]["has_chart"] is False


def test_get_run_missing_returns_none(temp_db):
    assert temp_db.get_run(999) is None


def test_list_runs_respects_limit_and_order(temp_db):
    for i in range(5):
        temp_db.record_run("price", f"T{i}", {}, {}, None)
    runs = temp_db.list_runs(limit=2)
    assert len(runs) == 2
    assert runs[0]["ticker"] == "T4"  # most recent first


def test_register_and_list_models(temp_db):
    model_id = temp_db.register_model(
        "AAPL", "logreg", ["yfinance"], False, 1, 0.9, 0.5, "/tmp/model.joblib"
    )
    models = temp_db.list_models()
    assert len(models) == 1
    assert models[0]["id"] == model_id
    assert models[0]["sentiment_sources"] == ["yfinance"]
    assert models[0]["use_volume"] is False

    fetched = temp_db.get_model(model_id)
    assert fetched["model_path"] == "/tmp/model.joblib"


def test_register_model_without_sentiment(temp_db):
    model_id = temp_db.register_model("AAPL", "logreg", None, True, 1, 0.9, 0.5, "/tmp/m2.joblib")
    fetched = temp_db.get_model(model_id)
    assert fetched["sentiment_sources"] is None
    assert fetched["use_volume"] is True


def test_get_model_missing_returns_none(temp_db):
    assert temp_db.get_model(999) is None


def test_watchlist_add_list_remove(temp_db):
    temp_db.add_watchlist_ticker("msft")
    temp_db.add_watchlist_ticker("aapl")
    assert temp_db.list_watchlist_tickers() == ["MSFT", "AAPL"]

    temp_db.remove_watchlist_ticker("msft")
    assert temp_db.list_watchlist_tickers() == ["AAPL"]


def test_watchlist_add_is_idempotent(temp_db):
    temp_db.add_watchlist_ticker("AAPL")
    temp_db.add_watchlist_ticker("AAPL")
    assert temp_db.list_watchlist_tickers() == ["AAPL"]


def test_watchlist_remove_missing_is_noop(temp_db):
    temp_db.remove_watchlist_ticker("NOPE")
    assert temp_db.list_watchlist_tickers() == []
