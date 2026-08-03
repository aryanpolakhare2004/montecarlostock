"""Derive financial ratios and growth features from a wide annual metrics table."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import data as price_data


def _safe_col(df: pd.DataFrame, name: str) -> pd.Series:
    if name in df.columns:
        return df[name]
    return pd.Series(index=df.index, dtype=float)


def build_metrics_table(annual: pd.DataFrame) -> pd.DataFrame:
    """Add derived ratios/margins to a wide (fiscal_year x raw metric) annual table."""
    if annual.empty:
        return pd.DataFrame()

    revenue = _safe_col(annual, "revenue")
    gross_profit = _safe_col(annual, "gross_profit")
    cost_of_revenue = _safe_col(annual, "cost_of_revenue")
    if gross_profit.isna().all() and not cost_of_revenue.isna().all():
        gross_profit = revenue - cost_of_revenue

    operating_income = _safe_col(annual, "operating_income")
    net_income = _safe_col(annual, "net_income")
    ocf = _safe_col(annual, "operating_cash_flow")
    capex = _safe_col(annual, "capital_expenditures").abs()
    fcf = ocf - capex
    long_term_debt = _safe_col(annual, "long_term_debt").fillna(0)
    current_debt = _safe_col(annual, "current_debt").fillna(0)
    total_debt = long_term_debt + current_debt
    cash = _safe_col(annual, "cash_and_equivalents")
    equity = _safe_col(annual, "stockholders_equity")
    diluted_shares = _safe_col(annual, "diluted_shares_outstanding")
    interest_expense = _safe_col(annual, "interest_expense")

    out = pd.DataFrame(index=annual.index)
    out["revenue"] = revenue
    out["gross_margin"] = gross_profit / revenue
    out["operating_margin"] = operating_income / revenue
    out["net_margin"] = net_income / revenue
    out["net_income"] = net_income
    out["operating_cash_flow"] = ocf
    out["free_cash_flow"] = fcf
    out["fcf_margin"] = fcf / revenue
    out["total_debt"] = total_debt
    out["cash_and_equivalents"] = cash
    out["net_debt"] = total_debt - cash
    out["stockholders_equity"] = equity
    out["debt_to_equity"] = total_debt / equity.replace(0, np.nan)
    out["interest_coverage"] = operating_income / interest_expense.replace(0, np.nan)
    out["diluted_shares_outstanding"] = diluted_shares

    out["revenue_growth_yoy"] = revenue.pct_change()
    out["net_income_growth_yoy"] = net_income.pct_change()
    out["fcf_growth_yoy"] = fcf.pct_change()
    out["share_dilution_yoy"] = diluted_shares.pct_change()

    return out


def cagr(series: pd.Series, years: int) -> float | None:
    """Compound annual growth rate over the trailing `years`, or None if not enough history."""
    clean = series.dropna()
    if len(clean) < years + 1:
        return None
    start, end = clean.iloc[-(years + 1)], clean.iloc[-1]
    if start is None or pd.isna(start) or start <= 0:
        return None
    return float((end / start) ** (1 / years) - 1)


def valuation_multiples(metrics: pd.DataFrame, price: float, shares_outstanding: float) -> dict:
    """Price multiples using the latest fiscal-year fundamentals and a current market price."""
    if metrics.empty or not price or not shares_outstanding:
        return {"market_cap": None, "price_to_earnings": None, "price_to_fcf": None,
                "price_to_sales": None, "price_to_book": None}

    latest = metrics.iloc[-1]
    market_cap = price * shares_outstanding

    def ratio(denominator):
        if denominator is None or pd.isna(denominator) or denominator <= 0:
            return None
        return market_cap / denominator

    return {
        "market_cap": market_cap,
        "price_to_earnings": ratio(latest.get("net_income")),
        "price_to_fcf": ratio(latest.get("free_cash_flow")),
        "price_to_sales": ratio(latest.get("revenue")),
        "price_to_book": ratio(latest.get("stockholders_equity")),
    }


def price_volatility(ticker: str, period: str = "3y") -> dict:
    """Annualized drift/volatility of the stock's own price history (risk input)."""
    try:
        prices = price_data.download_prices(ticker, period=period)
        returns = price_data.log_returns(prices)
        drift, vol = price_data.annualize_drift_vol(returns)
        last_price = float(prices.iloc[-1])
        return {"last_price": last_price, "annualized_drift": drift, "annualized_volatility": vol}
    except Exception:
        return {"last_price": None, "annualized_drift": None, "annualized_volatility": None}
