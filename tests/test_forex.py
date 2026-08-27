import pandas as pd

from mcstock import forex


def _fake_prices(n=40, start=1.1, step=0.001):
    return pd.Series([start + i * step for i in range(n)])


def test_quick_quote_shape(monkeypatch):
    monkeypatch.setattr(forex.data, "download_prices", lambda symbol, period="3mo": _fake_prices())
    quote = forex.quick_quote("EURUSD=X")
    assert quote["symbol"] == "EURUSD=X"
    assert quote["last_price"] > 1.0
    assert quote["day_change_pct"] is not None
    assert len(quote["sparkline"]) == 30


def test_quick_quote_single_price_point_has_no_day_change(monkeypatch):
    monkeypatch.setattr(forex.data, "download_prices", lambda symbol, period="3mo": _fake_prices(n=1))
    quote = forex.quick_quote("EURUSD=X")
    assert quote["day_change_pct"] is None


def test_forex_pairs_list_has_symbol_and_name():
    assert len(forex.FOREX_PAIRS) > 0
    for entry in forex.FOREX_PAIRS:
        assert set(entry) == {"symbol", "name"}
