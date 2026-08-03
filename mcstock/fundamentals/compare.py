"""Side-by-side comparison across multiple tickers, e.g. Micron vs Western Digital vs Seagate."""
from __future__ import annotations

from . import analyst


def _composite(scores: dict) -> float | None:
    parts = [scores.get("business_quality"), scores.get("growth"), scores.get("financial_strength"),
             scores.get("valuation")]
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    base = sum(parts) / len(parts)
    risk = scores.get("risk_score")
    if risk is not None:
        base -= 0.15 * risk
    return round(base, 1)


def compare(tickers: list[str], llm_backend_name: str | None = None) -> dict:
    """Analyze each ticker and rank them by a simple composite score.

    Composite = average(quality, growth, financial strength, valuation) - 0.15 * risk.
    It's a convenience ranking for the comparison table, not a substitute for
    reading each ticker's own scorecard and evidence.
    """
    reports: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for ticker in tickers:
        try:
            reports[ticker.upper()] = analyst.analyze(ticker, llm_backend_name=llm_backend_name)
        except Exception as exc:
            errors[ticker.upper()] = str(exc)

    rows = []
    for ticker, report in reports.items():
        scores = report["scores"]
        rows.append({
            "ticker": ticker,
            "company_name": report["company_name"],
            "composite": _composite(scores),
            "business_quality": scores.get("business_quality"),
            "growth": scores.get("growth"),
            "financial_strength": scores.get("financial_strength"),
            "valuation": scores.get("valuation"),
            "risk_label": scores.get("risk_label"),
            "revenue_trend": report["trends"]["revenue_trend"],
            "fcf_status": report["trends"]["fcf_status"],
            "debt_position": report["trends"]["debt_position"],
            "confidence": report["confidence"],
        })
    rows.sort(key=lambda r: (r["composite"] is None, -(r["composite"] or 0)))

    return {"rows": rows, "reports": reports, "errors": errors}
