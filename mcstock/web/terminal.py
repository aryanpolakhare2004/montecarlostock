"""Text-only command dispatcher backing the web dashboard's Terminal tab.

Every command returns a plain string (never raises to the caller) so the
frontend can render it straight into a scrolling console, the way a real
terminal would print output or an error and keep going.
"""
from __future__ import annotations

import shlex

from .. import data, gbm
from ..backtest import backtest_strategy
from ..fundamentals import analyst as fundamentals_analyst
from ..fundamentals import compare as fundamentals_compare
from ..strategies.buy_and_hold import BuyAndHold
from ..strategies.moving_average import MovingAverageCrossover
from . import db

SPARK_LEVELS = "▁▂▃▄▅▆▇█"


def ascii_sparkline(values: list[float]) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    if hi == lo:
        return SPARK_LEVELS[0] * len(values)
    span = hi - lo
    scale = len(SPARK_LEVELS) - 1
    return "".join(SPARK_LEVELS[min(int((v - lo) / span * scale), scale)] for v in values)


def ascii_table(headers: list[str], rows: list[list]) -> str:
    str_rows = [[str(cell) for cell in row] for row in rows]
    widths = [len(str(h)) for h in headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(cells: list[str]) -> str:
        return "  ".join(cell.ljust(w) for cell, w in zip(cells, widths))

    lines = [fmt_row([str(h) for h in headers]), fmt_row(["-" * w for w in widths])]
    lines += [fmt_row(row) for row in str_rows]
    return "\n".join(lines)


def _fmt_score(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.1f}"


def _parse_flags(args: list[str]) -> tuple[list[str], dict[str, str]]:
    positional: list[str] = []
    flags: dict[str, str] = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            key = arg[2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                flags[key] = args[i + 1]
                i += 2
            else:
                flags[key] = "true"
                i += 1
        else:
            positional.append(arg)
            i += 1
    return positional, flags


def cmd_help(_args: list[str]) -> str:
    return (
        "Available commands:\n"
        "  help                                      show this message\n"
        "  price TICKER [--days N] [--sims N] [--period P]\n"
        "                                             Monte Carlo GBM price simulation\n"
        "  strategy TICKER [--strategy buy-and-hold|sma-crossover] [--days N] [--sims N]\n"
        "                                             Monte Carlo strategy backtest\n"
        "  analyst TICKER                             AI fundamentals scorecard\n"
        "  compare TICKER,TICKER,...                  rank companies by fundamentals\n"
        "  watchlist list|add TICKER|remove TICKER    manage the saved watchlist\n"
        "  clear                                      clear the screen"
    )


def cmd_price(args: list[str]) -> str:
    positional, flags = _parse_flags(args)
    if not positional:
        return "usage: price TICKER [--days N] [--sims N] [--period P]"
    ticker = positional[0].upper()
    days = int(flags.get("days", 252))
    sims = int(flags.get("sims", 5000))
    period = flags.get("period", "5y")

    try:
        prices = data.download_prices(ticker, period=period)
        returns = data.log_returns(prices)
        mu, sigma = data.annualize_drift_vol(returns)
        s0 = float(prices.iloc[-1])
        paths = gbm.simulate_gbm_paths(s0, mu, sigma, days, sims)
        summary = gbm.summarize_final_prices(paths)
    except Exception as exc:
        return f"error: {exc}"

    lines = [
        f"{ticker}  s0={s0:.2f}  mu={mu * 100:.2f}%/yr  sigma={sigma * 100:.2f}%/yr",
        f"recent price action  {ascii_sparkline([float(p) for p in prices.tail(60)])}",
        "",
        f"Monte Carlo projection ({sims} sims, {days} days):",
    ]
    for key, value in summary.items():
        lines.append(f"  {key:<20} {value:.4f}" if isinstance(value, float) else f"  {key:<20} {value}")
    return "\n".join(lines)


def cmd_strategy(args: list[str]) -> str:
    positional, flags = _parse_flags(args)
    if not positional:
        return "usage: strategy TICKER [--strategy buy-and-hold|sma-crossover] [--days N] [--sims N] [--fast N] [--slow N]"
    ticker = positional[0].upper()
    strategy_name = flags.get("strategy", "buy-and-hold")
    days = int(flags.get("days", 252))
    sims = int(flags.get("sims", 2000))
    block_size = int(flags.get("block-size", 5))
    period = flags.get("period", "5y")

    if strategy_name == "buy-and-hold":
        strategy = BuyAndHold()
    elif strategy_name == "sma-crossover":
        strategy = MovingAverageCrossover(fast=int(flags.get("fast", 20)), slow=int(flags.get("slow", 50)))
    else:
        return f"unsupported strategy for the terminal: '{strategy_name}' (use buy-and-hold or sma-crossover)"

    try:
        prices = data.download_prices(ticker, period=period)
        returns = data.log_returns(prices).to_numpy()
        s0 = float(prices.iloc[-1])
        result = backtest_strategy(strategy, returns, s0, days, sims, block_size=block_size)
    except Exception as exc:
        return f"error: {exc}"

    lines = [f"{ticker}  strategy={strategy_name}  ({sims} sims, {days} days)", ""]
    for key in (
        "mean_return", "median_return", "std_return", "p05_return", "p95_return",
        "prob_profit", "mean_max_drawdown", "worst_max_drawdown",
    ):
        lines.append(f"  {key:<20} {result[key]:.4f}")
    return "\n".join(lines)


def cmd_analyst(args: list[str]) -> str:
    positional, _flags = _parse_flags(args)
    if not positional:
        return "usage: analyst TICKER"
    ticker = positional[0].upper()

    try:
        report = fundamentals_analyst.analyze(ticker, llm_backend_name="stub")
    except Exception as exc:
        return f"error: {exc}"

    s, t, fv = report["scores"], report["trends"], report["fair_value"]

    def score_line(label: str, value: float | None) -> str:
        return f"{label:<24}{'n/a' if value is None else f'{value:.0f}/100'}"

    lines = [
        f"{report['company_name']} ({report['ticker']})",
        "",
        score_line("Business quality:", s["business_quality"]),
        score_line("Financial strength:", s["financial_strength"]),
        score_line("Growth:", s["growth"]),
        score_line("Valuation:", s["valuation"]),
        f"{'Risk:':<24}{s['risk_label']}",
        "",
        f"{'Revenue trend:':<24}{t['revenue_trend']}",
        f"{'Free cash flow:':<24}{t['fcf_status']}",
        f"{'Debt position:':<24}{t['debt_position']}",
        f"{'Share dilution:':<24}{t['share_dilution']}",
        "",
        f"Bull case:              {report['bull_case']}",
        f"Bear case:              {report['bear_case']}",
        "Major red flags:",
    ]
    lines += [f"  - {flag}" for flag in report["red_flags"]]
    if fv.get("low") is not None:
        lines.append(
            f"Estimated fair-value range: ${fv['low']:.2f} - ${fv['high']:.2f} "
            f"(current ${fv['current_price']:.2f})"
        )
    else:
        lines.append("Estimated fair-value range: n/a")
    lines.append(f"Confidence:             {report['confidence']:.0f}%")
    return "\n".join(lines)


def cmd_compare(args: list[str]) -> str:
    if not args:
        return "usage: compare TICKER1,TICKER2,... (comma or space separated)"
    tickers = [t.strip().upper() for chunk in args for t in chunk.split(",") if t.strip()]

    try:
        result = fundamentals_compare.compare(tickers)
    except Exception as exc:
        return f"error: {exc}"

    headers = ["#", "Ticker", "Company", "Composite", "Quality", "Growth", "Fin.Str", "Valuation", "Risk"]
    rows = [
        [
            i, r["ticker"], r["company_name"][:24], _fmt_score(r["composite"]),
            _fmt_score(r["business_quality"]), _fmt_score(r["growth"]),
            _fmt_score(r["financial_strength"]), _fmt_score(r["valuation"]), r["risk_label"],
        ]
        for i, r in enumerate(result["rows"], start=1)
    ]
    lines = [ascii_table(headers, rows)]
    if result["errors"]:
        lines.append("")
        lines.append("errors:")
        lines += [f"  {t}: {e}" for t, e in result["errors"].items()]
    return "\n".join(lines)


def cmd_watchlist(args: list[str]) -> str:
    if not args:
        return "usage: watchlist list|add TICKER|remove TICKER"
    sub = args[0].lower()
    if sub == "list":
        tickers = db.list_watchlist_tickers()
        return "\n".join(tickers) if tickers else "(empty)"
    if sub == "add" and len(args) > 1:
        db.add_watchlist_ticker(args[1])
        return f"added {args[1].upper()} to watchlist"
    if sub == "remove" and len(args) > 1:
        db.remove_watchlist_ticker(args[1])
        return f"removed {args[1].upper()} from watchlist"
    return "usage: watchlist list|add TICKER|remove TICKER"


COMMANDS = {
    "help": cmd_help,
    "price": cmd_price,
    "strategy": cmd_strategy,
    "analyst": cmd_analyst,
    "compare": cmd_compare,
    "watchlist": cmd_watchlist,
}


def execute(command: str) -> str:
    command = command.strip()
    if not command:
        return ""
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        return f"error: {exc}"
    if not parts:
        return ""

    name, args = parts[0].lower(), parts[1:]
    handler = COMMANDS.get(name)
    if handler is None:
        return f"unknown command: '{name}' (type 'help' for a list)"
    try:
        return handler(args)
    except Exception as exc:
        return f"error: {exc}"
