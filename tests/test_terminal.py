import numpy as np
import pandas as pd
import pytest

from mcstock.web import db, terminal


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db, "MODELS_DIR", tmp_path / "models")
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "mcstock.db")
    db.init_db()
    return db


def _fake_prices(n=80, start=100.0, step=0.5):
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.Series([start + step * i for i in range(n)], index=idx)


# ---- ascii helpers ----

def test_ascii_sparkline_length_matches_input():
    values = [1.0, 2.0, 3.0, 2.0, 1.0]
    result = terminal.ascii_sparkline(values)
    assert len(result) == len(values)


def test_ascii_sparkline_constant_values():
    result = terminal.ascii_sparkline([5.0, 5.0, 5.0])
    assert result == terminal.SPARK_LEVELS[0] * 3


def test_ascii_sparkline_empty():
    assert terminal.ascii_sparkline([]) == ""


def test_ascii_table_includes_headers_and_rows():
    table = terminal.ascii_table(["A", "B"], [[1, "x"], [22, "yy"]])
    lines = table.splitlines()
    assert lines[0].startswith("A")
    assert "B" in lines[0]
    assert any("22" in line for line in lines)


# ---- execute() dispatch ----

def test_execute_empty_command_returns_empty_string():
    assert terminal.execute("   ") == ""


def test_execute_unknown_command():
    result = terminal.execute("bogus")
    assert "unknown command" in result


def test_execute_help():
    result = terminal.execute("help")
    assert "Available commands" in result
    assert "watchlist" in result


def test_execute_malformed_quoting_does_not_raise():
    result = terminal.execute('price "unterminated')
    assert "error" in result.lower()


# ---- price ----

def test_cmd_price_usage_without_ticker():
    assert terminal.execute("price").startswith("usage:")


def test_cmd_price_success(monkeypatch):
    monkeypatch.setattr(terminal.data, "download_prices", lambda ticker, period="5y": _fake_prices())
    result = terminal.execute("price AAPL --days 10 --sims 200")
    assert "AAPL" in result
    assert "Monte Carlo projection" in result
    assert "mean" in result


def test_cmd_price_handles_download_failure(monkeypatch):
    def boom(ticker, period="5y"):
        raise ValueError("no data")

    monkeypatch.setattr(terminal.data, "download_prices", boom)
    result = terminal.execute("price NOPE")
    assert result == "error: no data"


# ---- strategy ----

def test_cmd_strategy_usage_without_ticker():
    assert terminal.execute("strategy").startswith("usage:")


def test_cmd_strategy_unsupported_strategy_name(monkeypatch):
    monkeypatch.setattr(terminal.data, "download_prices", lambda ticker, period="5y": _fake_prices())
    result = terminal.execute("strategy AAPL --strategy ml-technical")
    assert "unsupported strategy" in result


def test_cmd_strategy_buy_and_hold(monkeypatch):
    monkeypatch.setattr(terminal.data, "download_prices", lambda ticker, period="5y": _fake_prices())
    result = terminal.execute("strategy AAPL --sims 100 --days 20")
    assert "AAPL" in result
    assert "mean_return" in result


# ---- analyst ----

def test_cmd_analyst_usage_without_ticker():
    assert terminal.execute("analyst") == "usage: analyst TICKER"


def test_cmd_analyst_success(monkeypatch):
    fake_report = {
        "ticker": "TEST", "company_name": "Test Corp",
        "scores": {"business_quality": 80.0, "financial_strength": 70.0, "growth": 60.0,
                   "valuation": 50.0, "risk_label": "Low"},
        "trends": {"revenue_trend": "Growing", "fcf_status": "Positive",
                   "debt_position": "Manageable", "share_dilution": "Low"},
        "bull_case": "Strong margins.", "bear_case": "Pricey.",
        "red_flags": ["None"],
        "fair_value": {"low": 90.0, "high": 120.0, "current_price": 100.0},
        "confidence": 88.0,
    }
    monkeypatch.setattr(terminal.fundamentals_analyst, "analyze", lambda ticker, llm_backend_name=None: fake_report)
    result = terminal.execute("analyst TEST")
    assert "Test Corp (TEST)" in result
    assert "Business quality:       80/100" in result
    assert "Bull case:              Strong margins." in result
    assert "Estimated fair-value range: $90.00 - $120.00" in result


def test_cmd_analyst_propagates_error(monkeypatch):
    def boom(ticker, llm_backend_name=None):
        raise LookupError("not found")

    monkeypatch.setattr(terminal.fundamentals_analyst, "analyze", boom)
    result = terminal.execute("analyst NOPE")
    assert result == "error: not found"


# ---- compare ----

def test_cmd_compare_usage_without_args():
    assert terminal.execute("compare").startswith("usage:")


def test_cmd_compare_success(monkeypatch):
    fake_result = {
        "rows": [
            {"ticker": "MU", "company_name": "Micron Technology", "composite": 49.0,
             "business_quality": 46.5, "growth": 86.2, "financial_strength": 79.3,
             "valuation": 0.0, "risk_label": "Low"},
        ],
        "errors": {"BAD": "not found"},
    }
    monkeypatch.setattr(terminal.fundamentals_compare, "compare", lambda tickers: fake_result)
    result = terminal.execute("compare MU,BAD")
    assert "MU" in result
    assert "Micron Technology" in result
    assert "errors:" in result
    assert "BAD: not found" in result


# ---- watchlist ----

def test_cmd_watchlist_add_list_remove(temp_db):
    assert terminal.execute("watchlist list") == "(empty)"
    assert "added AAPL" in terminal.execute("watchlist add AAPL")
    assert terminal.execute("watchlist list") == "AAPL"
    assert "removed AAPL" in terminal.execute("watchlist remove AAPL")
    assert terminal.execute("watchlist list") == "(empty)"


def test_cmd_watchlist_usage_without_args():
    assert terminal.execute("watchlist").startswith("usage:")
