"""Orchestrates one ticker end-to-end: EDGAR data -> ratios -> scorecard ->
fair value -> narrative. This is the single entry point the web app and CLI
should call.
"""
from __future__ import annotations

import pandas as pd

from . import extract, llm_analyst, ratios, scorecard, store, valuation


def _latest_shares(metrics: pd.DataFrame) -> float | None:
    if metrics.empty or "diluted_shares_outstanding" not in metrics:
        return None
    series = metrics["diluted_shares_outstanding"].dropna()
    return float(series.iloc[-1]) if len(series) else None


def analyze(ticker: str, llm_backend_name: str | None = None, force_refresh: bool = False) -> dict:
    """Return a full investment-analyst report dict for a single ticker."""
    facts = store.get_company_facts(ticker, force_refresh=force_refresh)
    company_name = extract.entity_name(facts) or ticker.upper()

    annual = extract.to_annual_table(facts)
    metrics = ratios.build_metrics_table(annual)
    price_stats = ratios.price_volatility(ticker)
    shares_outstanding = _latest_shares(metrics)
    valuation_multiples = ratios.valuation_multiples(metrics, price_stats.get("last_price"), shares_outstanding)

    bq_score, bq_evidence = scorecard.score_business_quality(metrics)
    growth_score, growth_evidence = scorecard.score_growth(metrics)
    fs_score, fs_evidence = scorecard.score_financial_strength(metrics)
    val_score, val_evidence = scorecard.score_valuation(valuation_multiples)
    risk_score, risk_label, risk_evidence = scorecard.score_risk(metrics, price_stats)

    trends = scorecard.trend_labels(metrics)
    confidence = scorecard.data_confidence(metrics, valuation_multiples, price_stats)
    fair_value = valuation.estimate_fair_value(metrics, price_stats, shares_outstanding)

    scores = {
        "business_quality": bq_score,
        "growth": growth_score,
        "financial_strength": fs_score,
        "valuation": val_score,
        "risk_score": risk_score,
        "risk_label": risk_label,
    }
    evidence = {
        "business_quality": bq_evidence,
        "growth": growth_evidence,
        "financial_strength": fs_evidence,
        "valuation": val_evidence,
        "risk": risk_evidence,
    }

    context = {
        "ticker": ticker.upper(), "company_name": company_name,
        "scores": scores, "trends": trends, "evidence": evidence, "valuation_range": fair_value,
    }
    backend = llm_analyst.get_backend(llm_backend_name)
    try:
        narrative = backend.generate_analysis(context)
    except Exception as exc:
        narrative = llm_analyst.StubBackend().generate_analysis(context)
        narrative["source"] = f"template (LLM backend failed: {exc})"

    return {
        "ticker": ticker.upper(),
        "company_name": company_name,
        "scores": scores,
        "trends": trends,
        "evidence": evidence,
        "valuation_multiples": valuation_multiples,
        "fair_value": fair_value,
        "price_stats": price_stats,
        "confidence": confidence,
        "bull_case": narrative["bull_case"],
        "bear_case": narrative["bear_case"],
        "red_flags": narrative["red_flags"],
        "narrative_source": narrative.get("source"),
        "annual_history": [] if annual.empty else annual.reset_index().to_dict(orient="records"),
        "metrics_history": [] if metrics.empty else metrics.reset_index().to_dict(orient="records"),
    }
