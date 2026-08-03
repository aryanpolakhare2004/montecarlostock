"""Fast per-ticker summary for the watchlist: price, day change, a sparkline,
and the numeric scorecard -- but no LLM narrative, since a watchlist needs to
render many rows quickly rather than produce one deep report.
"""
from __future__ import annotations

from .. import data as price_data
from . import extract, ratios, scorecard, store
from .analyst import _latest_shares
from .compare import _composite


def quick_summary(ticker: str) -> dict:
    facts = store.get_company_facts(ticker)
    company_name = extract.entity_name(facts) or ticker.upper()

    annual = extract.to_annual_table(facts)
    metrics = ratios.build_metrics_table(annual)
    shares_outstanding = _latest_shares(metrics)

    prices = price_data.download_prices(ticker, period="3mo")
    last_price = float(prices.iloc[-1])
    prev_price = float(prices.iloc[-2]) if len(prices) > 1 else None
    day_change_pct = (last_price / prev_price - 1) if prev_price else None
    sparkline = [round(float(p), 2) for p in prices.tail(30)]

    returns = price_data.log_returns(prices)
    _, volatility = price_data.annualize_drift_vol(returns) if len(returns) > 5 else (None, None)

    valuation_multiples = ratios.valuation_multiples(metrics, last_price, shares_outstanding)

    bq_score, _ = scorecard.score_business_quality(metrics)
    growth_score, _ = scorecard.score_growth(metrics)
    fs_score, _ = scorecard.score_financial_strength(metrics)
    val_score, _ = scorecard.score_valuation(valuation_multiples)
    risk_score, risk_label, _ = scorecard.score_risk(metrics, {"annualized_volatility": volatility})

    scores = {
        "business_quality": bq_score,
        "growth": growth_score,
        "financial_strength": fs_score,
        "valuation": val_score,
        "risk_score": risk_score,
        "risk_label": risk_label,
    }

    return {
        "ticker": ticker.upper(),
        "company_name": company_name,
        "last_price": last_price,
        "day_change_pct": day_change_pct,
        "sparkline": sparkline,
        "scores": scores,
        "composite": _composite(scores),
    }
