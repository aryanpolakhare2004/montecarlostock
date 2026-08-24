import pandas as pd
import pytest

from mcstock.fundamentals import (
    analyst,
    compare as compare_mod,
    edgar,
    extract,
    llm_analyst,
    ratios,
    scorecard,
    store,
    valuation,
    watchlist as watchlist_mod,
)

YEARS = [2021, 2022, 2023, 2024]


def _entry(fy: int, val: float) -> dict:
    return {
        "start": f"{fy - 1}-07-01",
        "end": f"{fy}-06-30",
        "val": val,
        "accn": f"0000000000-{fy}-000001",
        "fy": fy,
        "fp": "FY",
        "form": "10-K",
        "filed": f"{fy}-08-15",
    }


def make_companyfacts(entity_name: str = "Test Corp", restated: bool = False) -> dict:
    revenue = {2021: 100e9, 2022: 110e9, 2023: 125e9, 2024: 140e9}
    gross_profit = {y: revenue[y] * 0.65 for y in YEARS}
    operating_income = {y: revenue[y] * 0.30 for y in YEARS}
    net_income = {y: revenue[y] * 0.25 for y in YEARS}
    ocf = {y: revenue[y] * 0.32 for y in YEARS}
    capex = {y: revenue[y] * 0.08 for y in YEARS}
    cash = {2021: 20e9, 2022: 25e9, 2023: 30e9, 2024: 35e9}
    lt_debt = {2021: 10e9, 2022: 10e9, 2023: 9e9, 2024: 8e9}
    cur_debt = {y: 1e9 for y in YEARS}
    assets = {2021: 150e9, 2022: 160e9, 2023: 175e9, 2024: 190e9}
    liabilities = {2021: 50e9, 2022: 52e9, 2023: 53e9, 2024: 54e9}
    equity = {y: assets[y] - liabilities[y] for y in YEARS}
    shares = {2021: 7.5e9, 2022: 7.4e9, 2023: 7.35e9, 2024: 7.3e9}
    interest = {y: 0.5e9 for y in YEARS}

    def series(values: dict) -> dict:
        entries = [_entry(y, values[y]) for y in YEARS]
        if restated:
            # a late restated duplicate for the latest year with a different value
            restated_entry = dict(_entry(YEARS[-1], values[YEARS[-1]] * 1.1))
            restated_entry["filed"] = f"{YEARS[-1] + 2}-01-01"
            entries.append(restated_entry)
        return entries

    facts = {
        "us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {"units": {"USD": series(revenue)}},
            "GrossProfit": {"units": {"USD": series(gross_profit)}},
            "OperatingIncomeLoss": {"units": {"USD": series(operating_income)}},
            "NetIncomeLoss": {"units": {"USD": series(net_income)}},
            "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": series(ocf)}},
            "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": series(capex)}},
            "CashAndCashEquivalentsAtCarryingValue": {"units": {"USD": series(cash)}},
            "LongTermDebtNoncurrent": {"units": {"USD": series(lt_debt)}},
            "LongTermDebtCurrent": {"units": {"USD": series(cur_debt)}},
            "Assets": {"units": {"USD": series(assets)}},
            "Liabilities": {"units": {"USD": series(liabilities)}},
            "StockholdersEquity": {"units": {"USD": series(equity)}},
            "WeightedAverageNumberOfDilutedSharesOutstanding": {"units": {"shares": series(shares)}},
            "InterestExpense": {"units": {"USD": series(interest)}},
        }
    }
    return {"entityName": entity_name, "cik": 123456, "facts": facts}


# ---- extract ----

def test_extract_annual_series_basic():
    facts = make_companyfacts()
    df = extract.extract_annual_series(facts, "revenue")
    assert list(df["fiscal_year"]) == YEARS
    assert df["value"].iloc[-1] == pytest.approx(140e9)
    assert (df["tag"] == "RevenueFromContractWithCustomerExcludingAssessedTax").all()


def test_extract_annual_series_missing_metric_returns_empty():
    facts = {"entityName": "Empty Co", "facts": {}}
    df = extract.extract_annual_series(facts, "revenue")
    assert df.empty


def test_extract_annual_series_dedupes_restatements_keeping_latest_filed():
    facts = make_companyfacts(restated=True)
    df = extract.extract_annual_series(facts, "revenue")
    assert len(df) == len(YEARS)  # no duplicate fiscal years
    assert df["value"].iloc[-1] == pytest.approx(140e9 * 1.1)


def test_to_annual_table_wide_format():
    facts = make_companyfacts()
    table = extract.to_annual_table(facts)
    assert list(table.index) == YEARS
    assert "revenue" in table.columns
    assert "diluted_shares_outstanding" in table.columns


def test_entity_name():
    assert extract.entity_name(make_companyfacts("Acme Inc")) == "Acme Inc"


# ---- ratios ----

@pytest.fixture
def metrics_table():
    facts = make_companyfacts()
    annual = extract.to_annual_table(facts)
    return ratios.build_metrics_table(annual)


def test_build_metrics_table_margins(metrics_table):
    latest = metrics_table.iloc[-1]
    assert latest["gross_margin"] == pytest.approx(0.65, abs=1e-6)
    assert latest["operating_margin"] == pytest.approx(0.30, abs=1e-6)
    assert latest["net_margin"] == pytest.approx(0.25, abs=1e-6)
    assert latest["free_cash_flow"] == pytest.approx(140e9 * 0.32 - 140e9 * 0.08)


def test_build_metrics_table_growth_and_dilution(metrics_table):
    revenue_growth = metrics_table["revenue_growth_yoy"].iloc[-1]
    assert revenue_growth == pytest.approx((140e9 - 125e9) / 125e9)
    dilution = metrics_table["share_dilution_yoy"].iloc[-1]
    assert dilution < 0  # share count shrank (buybacks) in the fixture


def test_build_metrics_table_empty_input():
    import pandas as pd

    assert ratios.build_metrics_table(pd.DataFrame()).empty


def test_cagr_basic(metrics_table):
    value = ratios.cagr(metrics_table["revenue"], 3)
    expected = (140e9 / 100e9) ** (1 / 3) - 1
    assert value == pytest.approx(expected)


def test_cagr_insufficient_history(metrics_table):
    assert ratios.cagr(metrics_table["revenue"].tail(2), 3) is None


def test_valuation_multiples(metrics_table):
    result = ratios.valuation_multiples(metrics_table, price=100.0, shares_outstanding=7.3e9)
    assert result["market_cap"] == pytest.approx(730e9)
    assert result["price_to_earnings"] == pytest.approx(730e9 / (140e9 * 0.25))


def test_valuation_multiples_missing_inputs(metrics_table):
    result = ratios.valuation_multiples(metrics_table, price=None, shares_outstanding=None)
    assert result["market_cap"] is None
    assert result["price_to_earnings"] is None


def test_price_volatility_handles_failure(monkeypatch):
    def boom(*args, **kwargs):
        raise ValueError("no data")

    monkeypatch.setattr(ratios.price_data, "download_prices", boom)
    result = ratios.price_volatility("NOPE")
    assert result == {"last_price": None, "annualized_drift": None, "annualized_volatility": None}


# ---- scorecard ----

def test_score_business_quality_within_range(metrics_table):
    score, evidence = scorecard.score_business_quality(metrics_table)
    assert 0 <= score <= 100
    assert len(evidence) > 0


def test_score_growth_within_range(metrics_table):
    score, evidence = scorecard.score_growth(metrics_table)
    assert 0 <= score <= 100
    assert evidence


def test_score_financial_strength_within_range(metrics_table):
    score, evidence = scorecard.score_financial_strength(metrics_table)
    assert 0 <= score <= 100


def test_score_valuation_expensive_vs_cheap():
    cheap, _ = scorecard.score_valuation({"price_to_earnings": 10, "price_to_fcf": 12, "price_to_sales": 2})
    expensive, _ = scorecard.score_valuation({"price_to_earnings": 60, "price_to_fcf": 70, "price_to_sales": 20})
    assert cheap > expensive


def test_score_risk_label_thresholds(metrics_table):
    score, label, evidence = scorecard.score_risk(metrics_table, {"annualized_volatility": 0.20})
    assert label in ("Low", "Medium", "High")
    assert 0 <= score <= 100


def test_score_functions_handle_empty_metrics():
    import pandas as pd

    empty = pd.DataFrame()
    assert scorecard.score_business_quality(empty) == (None, ["No financial data available."])
    assert scorecard.score_growth(empty)[0] is None
    assert scorecard.score_financial_strength(empty)[0] is None
    score, label, _ = scorecard.score_risk(empty, {})
    assert score is None and label == "Unknown"


def test_trend_labels(metrics_table):
    trends = scorecard.trend_labels(metrics_table)
    assert trends["revenue_trend"] == "Growing"
    assert trends["fcf_status"] == "Positive"
    assert trends["debt_position"] == "Manageable"
    assert trends["share_dilution"] == "Low"


def test_data_confidence_range(metrics_table):
    valuation_mult = ratios.valuation_multiples(metrics_table, price=100.0, shares_outstanding=7.3e9)
    confidence = scorecard.data_confidence(metrics_table, valuation_mult, {"annualized_volatility": 0.2})
    assert 0 <= confidence <= 100


# ---- valuation ----

def test_estimate_fair_value_basic(metrics_table):
    result = valuation.estimate_fair_value(metrics_table, {"last_price": 100.0}, shares_outstanding=7.3e9)
    assert result["low"] is not None and result["high"] is not None
    assert result["low"] <= result["high"]
    assert "earnings_multiple" in result["methods"]


def test_estimate_fair_value_missing_shares(metrics_table):
    result = valuation.estimate_fair_value(metrics_table, {"last_price": 100.0}, shares_outstanding=None)
    assert result["low"] is None and result["methods"] == {}


# ---- llm_analyst ----

def _sample_context():
    return {
        "ticker": "TEST",
        "company_name": "Test Corp",
        "scores": {
            "business_quality": 80.0, "growth": 70.0, "financial_strength": 30.0,
            "valuation": 40.0, "risk_score": 70.0, "risk_label": "High",
        },
        "trends": {
            "revenue_trend": "Growing", "fcf_status": "Negative",
            "debt_position": "High", "share_dilution": "High",
        },
        "evidence": {
            "business_quality": ["Gross margin 65.0% (latest FY)."],
            "growth": ["3-year revenue CAGR of 12.0%."],
            "financial_strength": ["Debt-to-equity of 2.50."],
            "valuation": ["P/E of 55.0x."],
            "risk": ["Debt-to-equity of 2.50."],
        },
        "valuation_range": {"low": 90, "high": 120},
    }


def test_stub_backend_generates_bull_bear_and_flags():
    result = llm_analyst.StubBackend().generate_analysis(_sample_context())
    assert "business quality" in result["bull_case"]
    assert "financial strength" in result["bear_case"]
    assert "Debt load is high relative to equity." in result["red_flags"]
    assert "Free cash flow was negative in the latest fiscal year." in result["red_flags"]
    assert result["source"] == "template (no LLM)"


def test_stub_backend_no_flags_when_healthy():
    ctx = _sample_context()
    ctx["trends"] = {"revenue_trend": "Growing", "fcf_status": "Positive",
                      "debt_position": "Manageable", "share_dilution": "Low"}
    ctx["scores"]["risk_label"] = "Low"
    ctx["scores"]["valuation"] = 60.0
    result = llm_analyst.StubBackend().generate_analysis(ctx)
    assert result["red_flags"] == ["No major red flags detected from the metrics tracked here."]


def test_ollama_backend_parse_extracts_sections():
    text = (
        "Bull case: Strong growth and margins.\n"
        "Bear case: Elevated leverage.\n"
        "Red flags:\n- High debt\n- Negative FCF"
    )
    parsed = llm_analyst.OllamaBackend._parse(text)
    assert parsed["bull_case"] == "Strong growth and margins."
    assert parsed["bear_case"] == "Elevated leverage."
    assert parsed["red_flags"] == ["High debt", "Negative FCF"]


def test_ollama_backend_parse_falls_back_to_raw_text():
    parsed = llm_analyst.OllamaBackend._parse("just some unstructured text")
    assert parsed["bull_case"] == "just some unstructured text"
    assert parsed["bear_case"] == ""


def test_get_backend_defaults_to_stub(monkeypatch):
    monkeypatch.delenv("MCSTOCK_LLM_BACKEND", raising=False)
    assert isinstance(llm_analyst.get_backend(), llm_analyst.StubBackend)


def test_get_backend_selects_ollama():
    backend = llm_analyst.get_backend("ollama")
    assert isinstance(backend, llm_analyst.OllamaBackend)


def test_get_backend_selects_together():
    backend = llm_analyst.get_backend("together")
    assert isinstance(backend, llm_analyst.TogetherBackend)


# ---- edgar ----

def test_fetch_ticker_cik_map(monkeypatch):
    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return {"0": {"cik_str": 789019, "ticker": "msft", "title": "MICROSOFT CORP"}}

    monkeypatch.setattr(edgar.requests, "get", lambda *a, **k: FakeResponse())
    monkeypatch.setattr(edgar, "_throttle", lambda: None)
    mapping = edgar.fetch_ticker_cik_map()
    assert mapping["MSFT"] == {"cik": 789019, "title": "MICROSOFT CORP"}


def test_fetch_json_raises_lookuperror_on_404(monkeypatch):
    class FakeResponse:
        status_code = 404

        def raise_for_status(self):
            raise AssertionError("should not be called")

        def json(self):
            return {}

    monkeypatch.setattr(edgar.requests, "get", lambda *a, **k: FakeResponse())
    monkeypatch.setattr(edgar, "_throttle", lambda: None)
    with pytest.raises(LookupError):
        edgar.fetch_json("https://example.com/missing")


# ---- store ----

@pytest.fixture
def temp_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "fundamentals.duckdb")
    return store


def test_get_cik_for_ticker_uses_cache_on_second_call(temp_store, monkeypatch):
    calls = {"n": 0}

    def fake_map():
        calls["n"] += 1
        return {"MSFT": {"cik": 789019, "title": "MICROSOFT CORP"}}

    monkeypatch.setattr(edgar, "fetch_ticker_cik_map", fake_map)
    cik1, title1 = temp_store.get_cik_for_ticker("msft")
    cik2, title2 = temp_store.get_cik_for_ticker("msft")
    assert (cik1, title1) == (789019, "MICROSOFT CORP")
    assert (cik2, title2) == (cik1, title1)
    assert calls["n"] == 1  # second call hit the cache, not SEC


def test_get_cik_for_ticker_unknown_raises(temp_store, monkeypatch):
    monkeypatch.setattr(edgar, "fetch_ticker_cik_map", lambda: {"MSFT": {"cik": 1, "title": "x"}})
    with pytest.raises(LookupError):
        temp_store.get_cik_for_ticker("NOPE")


def test_get_company_facts_caches(temp_store, monkeypatch):
    monkeypatch.setattr(edgar, "fetch_ticker_cik_map", lambda: {"MSFT": {"cik": 789019, "title": "MICROSOFT CORP"}})
    calls = {"n": 0}

    def fake_facts(cik):
        calls["n"] += 1
        return make_companyfacts("Microsoft Corp")

    monkeypatch.setattr(edgar, "fetch_company_facts", fake_facts)
    facts1 = temp_store.get_company_facts("msft")
    facts2 = temp_store.get_company_facts("msft")
    assert facts1["entityName"] == "Microsoft Corp"
    assert facts2 == facts1
    assert calls["n"] == 1


def test_get_company_facts_force_refresh(temp_store, monkeypatch):
    monkeypatch.setattr(edgar, "fetch_ticker_cik_map", lambda: {"MSFT": {"cik": 789019, "title": "MICROSOFT CORP"}})
    calls = {"n": 0}

    def fake_facts(cik):
        calls["n"] += 1
        return make_companyfacts("Microsoft Corp")

    monkeypatch.setattr(edgar, "fetch_company_facts", fake_facts)
    temp_store.get_company_facts("msft")
    temp_store.get_company_facts("msft", force_refresh=True)
    assert calls["n"] == 2


# ---- analyst orchestration ----

def test_analyze_end_to_end(monkeypatch):
    monkeypatch.setattr(analyst.store, "get_company_facts", lambda ticker, force_refresh=False: make_companyfacts("Test Corp"))
    monkeypatch.setattr(
        analyst.ratios, "price_volatility",
        lambda ticker, period="3y": {"last_price": 100.0, "annualized_drift": 0.1, "annualized_volatility": 0.25},
    )

    report = analyst.analyze("TEST")

    assert report["ticker"] == "TEST"
    assert report["company_name"] == "Test Corp"
    assert set(report["scores"]) == {
        "business_quality", "growth", "financial_strength", "valuation", "risk_score", "risk_label",
    }
    assert report["trends"]["revenue_trend"] == "Growing"
    assert report["bull_case"] and report["bear_case"]
    assert isinstance(report["red_flags"], list)
    assert report["narrative_source"] == "template (no LLM)"
    assert 0 <= report["confidence"] <= 100
    assert len(report["annual_history"]) == len(YEARS)


def test_analyze_falls_back_to_stub_when_llm_backend_fails(monkeypatch):
    monkeypatch.setattr(analyst.store, "get_company_facts", lambda ticker, force_refresh=False: make_companyfacts())
    monkeypatch.setattr(
        analyst.ratios, "price_volatility",
        lambda ticker, period="3y": {"last_price": 100.0, "annualized_drift": 0.1, "annualized_volatility": 0.25},
    )

    class BoomBackend:
        def generate_analysis(self, context):
            raise RuntimeError("ollama not running")

    monkeypatch.setattr(analyst.llm_analyst, "get_backend", lambda name=None: BoomBackend())

    report = analyst.analyze("TEST")
    assert "template" in report["narrative_source"]
    assert "ollama not running" in report["narrative_source"]


# ---- compare ----

def test_compare_ranks_and_collects_errors(monkeypatch):
    def fake_analyze(ticker, llm_backend_name=None):
        if ticker.upper() == "BAD":
            raise LookupError("not found")
        base_score = 80.0 if ticker.upper() == "GOOD" else 40.0
        return {
            "ticker": ticker.upper(), "company_name": f"{ticker.upper()} Inc",
            "scores": {
                "business_quality": base_score, "growth": base_score,
                "financial_strength": base_score, "valuation": base_score,
                "risk_score": 20.0, "risk_label": "Low",
            },
            "trends": {"revenue_trend": "Growing", "fcf_status": "Positive", "debt_position": "Manageable"},
            "confidence": 90.0,
        }

    monkeypatch.setattr(compare_mod.analyst, "analyze", fake_analyze)
    result = compare_mod.compare(["GOOD", "BAD", "OK"])

    assert result["rows"][0]["ticker"] == "GOOD"
    assert "BAD" in result["errors"]
    assert len(result["rows"]) == 2


# ---- watchlist quick_summary ----

def _fake_price_series(n=40, start=100.0, step=1.0):
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.Series([start + step * i for i in range(n)], index=idx)


def test_quick_summary_end_to_end(monkeypatch):
    monkeypatch.setattr(watchlist_mod.store, "get_company_facts", lambda ticker: make_companyfacts("Test Corp"))
    monkeypatch.setattr(watchlist_mod.price_data, "download_prices", lambda ticker, period="3mo": _fake_price_series())

    summary = watchlist_mod.quick_summary("TEST")

    assert summary["ticker"] == "TEST"
    assert summary["company_name"] == "Test Corp"
    assert summary["last_price"] == pytest.approx(139.0)
    assert summary["day_change_pct"] == pytest.approx(1.0 / 138.0)
    assert len(summary["sparkline"]) == 30
    assert summary["scores"]["business_quality"] is not None
    assert summary["composite"] is not None


def test_quick_summary_single_price_point_has_no_day_change(monkeypatch):
    monkeypatch.setattr(watchlist_mod.store, "get_company_facts", lambda ticker: make_companyfacts("Test Corp"))
    monkeypatch.setattr(
        watchlist_mod.price_data, "download_prices", lambda ticker, period="3mo": _fake_price_series(n=1)
    )

    summary = watchlist_mod.quick_summary("TEST")
    assert summary["day_change_pct"] is None
