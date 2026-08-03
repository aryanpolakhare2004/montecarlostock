"""Transparent, rule-based scoring: every 0-100 score is a weighted blend of a
few named indicators, and every indicator that had data produces one evidence
string. No black box — you can trace each score back to the numbers behind it.
"""
from __future__ import annotations

import math

import pandas as pd

Evidence = list[str]


def _scale(value: float | None, low: float, high: float) -> float | None:
    """Map value linearly onto 0-100 with `low` -> 0 and `high` -> 100 (direction-agnostic)."""
    if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
        return None
    if low == high:
        return 100.0 if value >= high else 0.0
    frac = (value - low) / (high - low)
    return float(min(max(frac, 0.0), 1.0) * 100)


def _latest(series: pd.Series | None) -> float | None:
    if series is None or len(series.dropna()) == 0:
        return None
    val = series.dropna().iloc[-1]
    return float(val)


def _weighted_score(components: list[tuple[float | None, float, str]]) -> tuple[float | None, Evidence]:
    """components: list of (score_0_100_or_None, weight, evidence_text_if_available).

    Weights are renormalized over components that actually had data.
    """
    available = [(s, w, e) for s, w, e in components if s is not None]
    if not available:
        return None, ["Not enough reported data to compute this score."]
    total_weight = sum(w for _, w, _ in available)
    score = sum(s * w for s, w, _ in available) / total_weight
    evidence = [e for _, _, e in available]
    missing = len(components) - len(available)
    if missing:
        evidence.append(f"({missing} of {len(components)} usual inputs were unavailable and were excluded.)")
    return round(score, 1), evidence


def _pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x * 100:.1f}%"


def score_business_quality(metrics: pd.DataFrame) -> tuple[float | None, Evidence]:
    if metrics.empty:
        return None, ["No financial data available."]
    gross_margin = _latest(metrics.get("gross_margin"))
    operating_margin = _latest(metrics.get("operating_margin"))
    fcf_margin = _latest(metrics.get("fcf_margin"))
    growth = metrics.get("revenue_growth_yoy")
    consistency = None
    if growth is not None:
        recent = growth.dropna().tail(5)
        if len(recent) > 0:
            consistency = float((recent > 0).mean())

    components = [
        (_scale(gross_margin, 0.15, 0.75), 0.35, f"Gross margin {_pct(gross_margin)} (latest FY)."),
        (_scale(operating_margin, 0.0, 0.35), 0.25, f"Operating margin {_pct(operating_margin)} (latest FY)."),
        (_scale(fcf_margin, -0.05, 0.30), 0.20, f"Free-cash-flow margin {_pct(fcf_margin)} (latest FY)."),
        (_scale(consistency, 0.0, 1.0), 0.20,
         f"Revenue grew in {consistency * 100:.0f}% of the last {min(len(growth.dropna()), 5) if growth is not None else 0} years."
         if consistency is not None else None),
    ]
    return _weighted_score(components)


def score_growth(metrics: pd.DataFrame) -> tuple[float | None, Evidence]:
    if metrics.empty:
        return None, ["No financial data available."]
    from .ratios import cagr

    revenue_cagr_3y = cagr(metrics["revenue"], 3) if "revenue" in metrics else None
    latest_rev_growth = _latest(metrics.get("revenue_growth_yoy"))
    latest_ni_growth = _latest(metrics.get("net_income_growth_yoy"))

    components = [
        (_scale(revenue_cagr_3y, -0.05, 0.30), 0.5,
         f"3-year revenue CAGR of {_pct(revenue_cagr_3y)}." if revenue_cagr_3y is not None else None),
        (_scale(latest_rev_growth, -0.05, 0.30), 0.25,
         f"Latest-year revenue growth of {_pct(latest_rev_growth)}." if latest_rev_growth is not None else None),
        (_scale(latest_ni_growth, -0.20, 0.50), 0.25,
         f"Latest-year net income growth of {_pct(latest_ni_growth)}." if latest_ni_growth is not None else None),
    ]
    return _weighted_score(components)


def score_financial_strength(metrics: pd.DataFrame) -> tuple[float | None, Evidence]:
    if metrics.empty:
        return None, ["No financial data available."]
    debt_to_equity = _latest(metrics.get("debt_to_equity"))
    interest_coverage = _latest(metrics.get("interest_coverage"))
    fcf_margin = _latest(metrics.get("fcf_margin"))
    net_debt = _latest(metrics.get("net_debt"))
    revenue = _latest(metrics.get("revenue"))
    net_debt_to_revenue = (net_debt / revenue) if (net_debt is not None and revenue) else None

    components = [
        (_scale(debt_to_equity, 3.0, 0.0), 0.30,
         f"Debt-to-equity of {debt_to_equity:.2f}." if debt_to_equity is not None else None),
        (_scale(interest_coverage, 1.0, 15.0), 0.20,
         f"Operating income covers interest expense {interest_coverage:.1f}x." if interest_coverage is not None else None),
        (_scale(fcf_margin, -0.10, 0.25), 0.25,
         f"Free-cash-flow margin {_pct(fcf_margin)}." if fcf_margin is not None else None),
        (_scale(net_debt_to_revenue, 0.5, -0.5), 0.25,
         f"Net debt is {net_debt_to_revenue * 100:.0f}% of revenue." if net_debt_to_revenue is not None else None),
    ]
    return _weighted_score(components)


def score_valuation(valuation: dict) -> tuple[float | None, Evidence]:
    pe = valuation.get("price_to_earnings")
    pfcf = valuation.get("price_to_fcf")
    ps = valuation.get("price_to_sales")

    components = [
        (_scale(pe, 45.0, 10.0), 0.40, f"P/E of {pe:.1f}x." if pe else None),
        (_scale(pfcf, 50.0, 10.0), 0.35, f"Price-to-FCF of {pfcf:.1f}x." if pfcf else None),
        (_scale(ps, 15.0, 1.0), 0.25, f"Price-to-sales of {ps:.1f}x." if ps else None),
    ]
    return _weighted_score(components)


def score_risk(metrics: pd.DataFrame, price_stats: dict) -> tuple[float | None, str, Evidence]:
    """Returns (risk_score_0_100_higher_is_riskier, label, evidence)."""
    if metrics.empty:
        return None, "Unknown", ["No financial data available."]

    debt_to_equity = _latest(metrics.get("debt_to_equity"))
    volatility = price_stats.get("annualized_volatility")
    dilution = metrics.get("share_dilution_yoy")
    avg_dilution = float(dilution.dropna().tail(3).mean()) if dilution is not None and len(dilution.dropna()) else None
    latest_fcf = _latest(metrics.get("free_cash_flow"))

    components = [
        (_scale(debt_to_equity, 0.0, 3.0), 0.30,
         f"Debt-to-equity of {debt_to_equity:.2f}." if debt_to_equity is not None else None),
        (_scale(volatility, 0.15, 0.70), 0.30,
         f"Annualized price volatility of {volatility * 100:.0f}%." if volatility is not None else None),
        (_scale(avg_dilution, 0.0, 0.15), 0.25,
         f"Diluted share count grew {avg_dilution * 100:.1f}%/yr on average (last 3 yrs)." if avg_dilution is not None else None),
        (100.0 if (latest_fcf is not None and latest_fcf < 0) else (0.0 if latest_fcf is not None else None), 0.15,
         "Latest-year free cash flow is negative." if latest_fcf is not None and latest_fcf < 0
         else ("Latest-year free cash flow is positive." if latest_fcf is not None else None)),
    ]
    score, evidence = _weighted_score(components)
    if score is None:
        return None, "Unknown", evidence
    label = "Low" if score < 33 else "Medium" if score < 66 else "High"
    return score, label, evidence


def trend_labels(metrics: pd.DataFrame) -> dict:
    """Human-readable trend labels for the at-a-glance summary row."""
    if metrics.empty:
        return {"revenue_trend": "Unknown", "fcf_status": "Unknown",
                "debt_position": "Unknown", "share_dilution": "Unknown"}
    from .ratios import cagr

    rev_cagr = cagr(metrics["revenue"], 3) if "revenue" in metrics else None
    if rev_cagr is None:
        revenue_trend = "Unknown"
    elif rev_cagr > 0.05:
        revenue_trend = "Growing"
    elif rev_cagr > -0.02:
        revenue_trend = "Flat"
    else:
        revenue_trend = "Declining"

    latest_fcf = _latest(metrics.get("free_cash_flow"))
    fcf_status = "Unknown" if latest_fcf is None else ("Positive" if latest_fcf >= 0 else "Negative")

    dte = _latest(metrics.get("debt_to_equity"))
    if dte is None:
        debt_position = "Unknown"
    elif dte < 0.5:
        debt_position = "Manageable"
    elif dte < 1.5:
        debt_position = "Elevated"
    else:
        debt_position = "High"

    dilution_series = metrics.get("share_dilution_yoy")
    avg_dilution = float(dilution_series.dropna().tail(3).mean()) if dilution_series is not None and len(dilution_series.dropna()) else None
    if avg_dilution is None:
        share_dilution = "Unknown"
    elif avg_dilution < 0.01:
        share_dilution = "Low"
    elif avg_dilution < 0.03:
        share_dilution = "Moderate"
    else:
        share_dilution = "High"

    return {
        "revenue_trend": revenue_trend,
        "fcf_status": fcf_status,
        "debt_position": debt_position,
        "share_dilution": share_dilution,
    }


REQUIRED_FIELDS_FOR_CONFIDENCE = [
    "revenue", "gross_margin", "operating_margin", "net_margin", "free_cash_flow",
    "debt_to_equity", "net_debt", "diluted_shares_outstanding",
]


def data_confidence(metrics: pd.DataFrame, valuation: dict, price_stats: dict) -> float:
    """Rough % of expected inputs that were actually available, latest fiscal year."""
    if metrics.empty:
        return 0.0
    latest = metrics.iloc[-1]
    have = sum(1 for f in REQUIRED_FIELDS_FOR_CONFIDENCE if f in latest and pd.notna(latest[f]))
    total = len(REQUIRED_FIELDS_FOR_CONFIDENCE)
    have += 1 if valuation.get("price_to_earnings") or valuation.get("price_to_fcf") else 0
    total += 1
    have += 1 if price_stats.get("annualized_volatility") is not None else 0
    total += 1
    return round(100 * have / total, 1)
