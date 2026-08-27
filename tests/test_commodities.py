import pandas as pd

from mcstock import commodities


def _fake_prices(n=40, start=100.0, step=0.5):
    return pd.Series([start + i * step for i in range(n)])


def test_quick_quote_shape(monkeypatch):
    monkeypatch.setattr(commodities.data, "download_prices", lambda symbol, period="3mo": _fake_prices())
    quote = commodities.quick_quote("GC=F")
    assert quote["symbol"] == "GC=F"
    assert quote["last_price"] > quote["day_change_pct"] * 0 + 100  # sanity: last_price is a real number > 100
    assert quote["day_change_pct"] is not None
    assert len(quote["sparkline"]) == 30


def test_quick_quote_single_price_point_has_no_day_change(monkeypatch):
    monkeypatch.setattr(commodities.data, "download_prices", lambda symbol, period="3mo": _fake_prices(n=1))
    quote = commodities.quick_quote("GC=F")
    assert quote["day_change_pct"] is None


def test_commodities_list_has_symbol_and_name():
    assert len(commodities.COMMODITIES) > 0
    for entry in commodities.COMMODITIES:
        assert set(entry) == {"symbol", "name"}
