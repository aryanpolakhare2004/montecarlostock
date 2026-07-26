"""Command-line interface for mcstock Monte Carlo simulations."""
from __future__ import annotations

import argparse
import sys

import numpy as np

from . import data, gbm, plotting
from .backtest import backtest_strategy
from .portfolio import portfolio_gbm_paths, summarize_portfolio
from .strategies.buy_and_hold import BuyAndHold
from .strategies.moving_average import MovingAverageCrossover

STRATEGIES = {
    "buy-and-hold": lambda args: BuyAndHold(),
    "sma-crossover": lambda args: MovingAverageCrossover(fast=args.fast, slow=args.slow),
}


def _print_summary(summary: dict) -> None:
    for key, value in summary.items():
        print(f"  {key}: {value:.4f}" if isinstance(value, float) else f"  {key}: {value}")


def cmd_price(args: argparse.Namespace) -> None:
    prices = data.download_prices(args.ticker, period=args.period)
    returns = data.log_returns(prices)
    mu, sigma = data.annualize_drift_vol(returns)
    s0 = float(prices.iloc[-1])

    paths = gbm.simulate_gbm_paths(s0, mu, sigma, args.days, args.sims, seed=args.seed)
    summary = gbm.summarize_final_prices(paths)

    print(f"{args.ticker}: s0={s0:.2f} mu={mu:.2%}/yr sigma={sigma:.2%}/yr")
    print(f"Simulated {args.sims} paths over {args.days} trading days")
    _print_summary(summary)

    if args.out:
        plotting.plot_paths(paths, args.out, f"{args.ticker} GBM simulation")
        print(f"Saved chart to {args.out}")


def cmd_strategy(args: argparse.Namespace) -> None:
    prices = data.download_prices(args.ticker, period=args.period)
    returns = data.log_returns(prices).to_numpy()
    s0 = float(prices.iloc[-1])
    strategy = STRATEGIES[args.strategy](args)

    result = backtest_strategy(
        strategy, returns, s0, args.days, args.sims, block_size=args.block_size, seed=args.seed
    )

    print(f"{args.ticker} strategy={args.strategy}")
    print(f"Simulated {args.sims} resampled paths over {args.days} trading days")
    _print_summary({k: result[k] for k in (
        "mean_return", "median_return", "std_return", "p05_return", "p95_return",
        "prob_profit", "mean_max_drawdown", "worst_max_drawdown",
    )})

    if args.out:
        plotting.plot_final_distribution(
            result["total_returns"], args.out, f"{args.ticker} {args.strategy} return distribution"
        )
        print(f"Saved chart to {args.out}")


def cmd_portfolio(args: argparse.Namespace) -> None:
    tickers = args.tickers
    if args.weights:
        if len(args.weights) != len(tickers):
            raise SystemExit("--weights must have one value per ticker")
        weights = np.array(args.weights, dtype=float)
    else:
        weights = np.full(len(tickers), 1.0 / len(tickers))

    prices = data.download_close_prices(tickers, period=args.period)
    paths = portfolio_gbm_paths(prices, weights, args.days, args.sims, initial_value=args.value, seed=args.seed)
    summary = summarize_portfolio(paths)

    print(f"Portfolio: {dict(zip(tickers, weights))}")
    print(f"Simulated {args.sims} paths over {args.days} trading days, starting value {args.value}")
    _print_summary(summary)

    if args.out:
        plotting.plot_paths(paths, args.out, "Portfolio simulation")
        print(f"Saved chart to {args.out}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mcstock", description="Monte Carlo stock simulations")
    sub = parser.add_subparsers(dest="command", required=True)

    p_price = sub.add_parser("price", help="Simulate future price paths for a single ticker (GBM)")
    p_price.add_argument("ticker")
    p_price.add_argument("--period", default="5y", help="Historical lookback window for calibration")
    p_price.add_argument("--days", type=int, default=252, help="Number of trading days to simulate")
    p_price.add_argument("--sims", type=int, default=10000, help="Number of simulated paths")
    p_price.add_argument("--seed", type=int, default=None)
    p_price.add_argument("--out", default=None, help="Path to save a PNG chart of the simulated paths")
    p_price.set_defaults(func=cmd_price)

    p_strategy = sub.add_parser(
        "strategy", help="Monte Carlo backtest a trading strategy via block-bootstrapped returns"
    )
    p_strategy.add_argument("ticker")
    p_strategy.add_argument("--strategy", choices=list(STRATEGIES), default="buy-and-hold")
    p_strategy.add_argument("--fast", type=int, default=20, help="Fast SMA window (sma-crossover only)")
    p_strategy.add_argument("--slow", type=int, default=50, help="Slow SMA window (sma-crossover only)")
    p_strategy.add_argument("--period", default="5y")
    p_strategy.add_argument("--days", type=int, default=252)
    p_strategy.add_argument("--sims", type=int, default=5000)
    p_strategy.add_argument("--block-size", type=int, default=5, help="Block bootstrap block length in days")
    p_strategy.add_argument("--seed", type=int, default=None)
    p_strategy.add_argument("--out", default=None, help="Path to save a PNG chart of the return distribution")
    p_strategy.set_defaults(func=cmd_strategy)

    p_portfolio = sub.add_parser(
        "portfolio", help="Simulate a multi-asset portfolio's future value (correlated GBM)"
    )
    p_portfolio.add_argument("tickers", nargs="+")
    p_portfolio.add_argument(
        "--weights", type=float, nargs="+", default=None,
        help="Portfolio weights, one per ticker, must sum to 1 (default: equal-weighted)"
    )
    p_portfolio.add_argument("--value", type=float, default=10000.0, help="Starting portfolio value")
    p_portfolio.add_argument("--period", default="5y")
    p_portfolio.add_argument("--days", type=int, default=252)
    p_portfolio.add_argument("--sims", type=int, default=5000)
    p_portfolio.add_argument("--seed", type=int, default=None)
    p_portfolio.add_argument("--out", default=None)
    p_portfolio.set_defaults(func=cmd_portfolio)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
