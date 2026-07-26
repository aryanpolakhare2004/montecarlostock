"""Command-line interface for mcstock Monte Carlo simulations."""
from __future__ import annotations

import argparse
import sys

import joblib
import numpy as np

from . import data, gbm, plotting
from .backtest import backtest_strategy
from .historical_backtest import realized_daily_returns, resample_return_series, summarize_equity
from .ml.dataset import build_dataset, build_latest_features
from .ml.models import predict_proba_up, train_classifier
from .portfolio import portfolio_gbm_paths, summarize_portfolio
from .strategies.buy_and_hold import BuyAndHold
from .strategies.ml_classifier import MLClassifierStrategy
from .strategies.moving_average import MovingAverageCrossover

SENTIMENT_SOURCE_GROUPS = {
    "none": None,
    "yfinance": ["yfinance"],
    "rss": ["rss"],
    "reddit": ["reddit"],
    "all": ["yfinance", "rss", "reddit"],
}


def _load_ml_technical_strategy(args: argparse.Namespace) -> MLClassifierStrategy:
    if not args.model_in:
        raise SystemExit("--model-in is required for --strategy ml-technical")
    bundle = joblib.load(args.model_in)
    if bundle.get("sentiment_sources"):
        raise SystemExit(
            "ml-technical requires a model trained with --sentiment none --no-volume; "
            "use 'mcstock backtest-ml' for models trained with sentiment/volume features"
        )
    return MLClassifierStrategy(bundle["model"], bundle["feature_names"])


STRATEGIES = {
    "buy-and-hold": lambda args: BuyAndHold(),
    "sma-crossover": lambda args: MovingAverageCrossover(fast=args.fast, slow=args.slow),
    "ml-technical": _load_ml_technical_strategy,
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


def cmd_train(args: argparse.Namespace) -> None:
    sentiment_sources = SENTIMENT_SOURCE_GROUPS[args.sentiment]
    X, y, forward = build_dataset(
        args.ticker, period=args.period, horizon=args.horizon,
        sentiment_sources=sentiment_sources, use_volume=args.use_volume,
    )
    result = train_classifier(X, y, model_type=args.model, test_size=args.test_size)
    test_returns = realized_daily_returns(result["model"], result["X_test"], forward)

    print(f"{args.ticker} model={args.model} sentiment={args.sentiment} use_volume={args.use_volume}")
    print(f"Trained on {len(X)} days, {len(result['X_test'])} held out chronologically")
    print(f"  train_accuracy: {result['train_accuracy']:.4f}")
    print(f"  test_accuracy: {result['test_accuracy']:.4f}")
    print(result["test_report"])

    joblib.dump({
        "model": result["model"],
        "model_type": args.model,
        "feature_names": result["feature_names"],
        "sentiment_sources": sentiment_sources,
        "use_volume": args.use_volume,
        "horizon": args.horizon,
        "train_accuracy": result["train_accuracy"],
        "test_accuracy": result["test_accuracy"],
        "test_returns": test_returns.to_numpy(),
    }, args.model_out)
    print(f"Saved model to {args.model_out}")


def cmd_predict(args: argparse.Namespace) -> None:
    bundle = joblib.load(args.model_in)
    latest = build_latest_features(
        args.ticker, sentiment_sources=bundle["sentiment_sources"], use_volume=bundle["use_volume"]
    )
    X_row = latest[bundle["feature_names"]].to_frame().T.fillna(0.0)
    prob_up = predict_proba_up(bundle["model"], X_row)
    direction = "UP" if prob_up >= 0.5 else "DOWN"

    print(f"{args.ticker} model={bundle['model_type']} sentiment={bundle['sentiment_sources']}")
    print(f"Predicted next {bundle['horizon']}-day direction: {direction} (P(up)={prob_up:.3f})")


def cmd_backtest_ml(args: argparse.Namespace) -> None:
    bundle = joblib.load(args.model_in)
    test_returns = bundle["test_returns"]

    equity = resample_return_series(
        test_returns, days=args.days, n_sims=args.sims, block_size=args.block_size, seed=args.seed
    )
    summary = summarize_equity(equity)

    print(f"model={bundle['model_type']} sentiment={bundle['sentiment_sources']}")
    print(f"Held-out train/test accuracy: {bundle['train_accuracy']:.4f} / {bundle['test_accuracy']:.4f}")
    print(f"Monte Carlo resampled {args.sims} equity curves over {args.days} days "
          f"from {len(test_returns)} realized daily returns")
    _print_summary(summary)

    if args.out:
        plotting.plot_paths(equity, args.out, "ML strategy Monte Carlo projection")
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
    p_strategy.add_argument(
        "--model-in", default=None,
        help="Path to a joblib model saved by 'mcstock train' (required for --strategy ml-technical)"
    )
    p_strategy.set_defaults(func=cmd_strategy)

    p_train = sub.add_parser(
        "train", help="Train a classical ML classifier (technical indicators + optional sentiment) for binary up/down prediction"
    )
    p_train.add_argument("ticker")
    p_train.add_argument("--model", choices=["logreg", "random_forest", "gradient_boosting"], default="logreg")
    p_train.add_argument("--sentiment", choices=list(SENTIMENT_SOURCE_GROUPS), default="none",
                          help="News sources to score with VADER and add as features (reddit needs "
                               "REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET env vars)")
    p_train.add_argument("--no-volume", dest="use_volume", action="store_false",
                          help="Exclude volume features (required to later use --strategy ml-technical)")
    p_train.add_argument("--period", default="5y")
    p_train.add_argument("--horizon", type=int, default=1, help="Predict direction over this many trading days ahead")
    p_train.add_argument("--test-size", type=float, default=0.2, help="Fraction of most-recent days held out for testing")
    p_train.add_argument("--model-out", default="mcstock_model.joblib")
    p_train.set_defaults(func=cmd_train)

    p_predict = sub.add_parser("predict", help="Binary up/down prediction for the next period using a trained model")
    p_predict.add_argument("ticker")
    p_predict.add_argument("--model-in", required=True, help="Path to a joblib model saved by 'mcstock train'")
    p_predict.set_defaults(func=cmd_predict)

    p_backtest_ml = sub.add_parser(
        "backtest-ml", help="Monte Carlo resample a trained model's realized held-out returns to project robustness"
    )
    p_backtest_ml.add_argument("--model-in", required=True, help="Path to a joblib model saved by 'mcstock train'")
    p_backtest_ml.add_argument("--days", type=int, default=60)
    p_backtest_ml.add_argument("--sims", type=int, default=10000)
    p_backtest_ml.add_argument("--block-size", type=int, default=5)
    p_backtest_ml.add_argument("--seed", type=int, default=None)
    p_backtest_ml.add_argument("--out", default=None)
    p_backtest_ml.set_defaults(func=cmd_backtest_ml)

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
