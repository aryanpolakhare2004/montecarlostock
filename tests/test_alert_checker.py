import numpy as np
import pandas as pd
import pytest

from mcstock.web import app as app_module


@pytest.fixture
def fixed_prices(monkeypatch):
    # Deterministic upward-drifting series so both price and volatility are known.
    prices = pd.Series(100 + np.arange(80, dtype=float) * 0.5)
    monkeypatch.setattr(app_module.data, "download_prices", lambda ticker, period="3mo": prices)
    return prices


def test_price_above_threshold_met(fixed_prices):
    last_price = float(fixed_prices.iloc[-1])
    alert = {"ticker": "AAPL", "metric": "price", "operator": "above", "threshold": last_price - 1}
    assert app_module._alert_condition_met(alert) is True


def test_price_above_threshold_not_met(fixed_prices):
    last_price = float(fixed_prices.iloc[-1])
    alert = {"ticker": "AAPL", "metric": "price", "operator": "above", "threshold": last_price + 1}
    assert app_module._alert_condition_met(alert) is False


def test_price_below_threshold(fixed_prices):
    last_price = float(fixed_prices.iloc[-1])
    alert = {"ticker": "AAPL", "metric": "price", "operator": "below", "threshold": last_price + 1}
    assert app_module._alert_condition_met(alert) is True


def test_volatility_metric_uses_annualized_vol(fixed_prices):
    returns = app_module.data.log_returns(fixed_prices)
    _, vol = app_module.data.annualize_drift_vol(returns)
    assert app_module._alert_condition_met(
        {"ticker": "AAPL", "metric": "volatility", "operator": "above", "threshold": vol - 0.001}
    ) is True
    assert app_module._alert_condition_met(
        {"ticker": "AAPL", "metric": "volatility", "operator": "below", "threshold": vol - 0.001}
    ) is False
