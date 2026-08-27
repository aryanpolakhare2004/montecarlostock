import pandas as pd

from mcstock import crypto


def _fake_prices(n=40, start=100.0, step=0.5):
    return pd.Series([start + i * step for i in range(n)])


def test_quick_quote_shape(monkeypatch):
    monkeypatch.setattr(crypto.data, "download_prices", lambda symbol, period="3mo": _fake_prices())
    quote = crypto.quick_quote("BTC-USD")
    assert quote["symbol"] == "BTC-USD"
    assert quote["last_price"] > 100
    assert quote["day_change_pct"] is not None
    assert len(quote["sparkline"]) == 30


def test_quick_quote_single_price_point_has_no_day_change(monkeypatch):
    monkeypatch.setattr(crypto.data, "download_prices", lambda symbol, period="3mo": _fake_prices(n=1))
    quote = crypto.quick_quote("BTC-USD")
    assert quote["day_change_pct"] is None


def test_cryptocurrencies_list_has_symbol_and_name():
    assert len(crypto.CRYPTOCURRENCIES) > 0
    for entry in crypto.CRYPTOCURRENCIES:
        assert set(entry) == {"symbol", "name"}
