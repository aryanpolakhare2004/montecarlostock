"""FastAPI web frontend for mcstock: full CLI parity plus SQLite-backed run/model history."""
from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .. import commodities, data, gbm, plotting, stats
from ..backtest import backtest_strategy, evaluate_strategy_on_paths, resample_paths
from ..fundamentals import analyst as fundamentals_analyst
from ..fundamentals import compare as fundamentals_compare
from ..fundamentals import watchlist as fundamentals_watchlist
from ..historical_backtest import realized_daily_returns, resample_return_series, summarize_equity
from ..ml.dataset import build_dataset, build_latest_features
from ..ml.models import load_bundle, predict_proba_up, save_bundle, train_classifier
from ..portfolio import optimize_weights, portfolio_gbm_paths, summarize_portfolio
from ..sentiment import news_sources as sentiment_news
from ..sentiment import scorer as sentiment_scorer
from ..strategies.buy_and_hold import BuyAndHold
from ..strategies.mean_reversion import MeanReversion
from ..strategies.ml_classifier import MLClassifierStrategy
from ..strategies.moving_average import MovingAverageCrossover
from . import db, pdf_report, terminal

STATIC_DIR = Path(__file__).parent / "static"

SENTIMENT_SOURCE_GROUPS = {
    "none": None,
    "yfinance": ["yfinance"],
    "rss": ["rss"],
    "reddit": ["reddit"],
    "all": ["yfinance", "rss", "reddit"],
}

app = FastAPI(title="mcstock")
db.init_db()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(LookupError)
async def lookup_error_handler(request: Request, exc: LookupError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


def _png_b64(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode("ascii")


# ---- request schemas ----

class PriceRequest(BaseModel):
    ticker: str
    period: str = "5y"
    days: int = 252
    sims: int = 10000
    seed: Optional[int] = None


class StrategyRequest(BaseModel):
    ticker: str
    strategy: str = "buy-and-hold"
    fast: int = 20
    slow: int = 50
    rsi_period: int = 14
    oversold: float = 30.0
    overbought: float = 70.0
    period: str = "5y"
    days: int = 252
    sims: int = 5000
    block_size: int = 5
    seed: Optional[int] = None
    model_id: Optional[int] = None


class PortfolioRequest(BaseModel):
    tickers: list[str]
    weights: Optional[list[float]] = None
    value: float = 10000.0
    period: str = "5y"
    days: int = 252
    sims: int = 5000
    seed: Optional[int] = None


class PortfolioOptimizeRequest(BaseModel):
    tickers: list[str]
    period: str = "5y"
    objective: str = "max_sharpe"
    risk_free_rate: float = 0.0


class TrainRequest(BaseModel):
    ticker: str
    model: str = "logreg"
    sentiment: str = "none"
    use_volume: bool = True
    period: str = "5y"
    horizon: int = 1
    test_size: float = 0.2


class PredictRequest(BaseModel):
    model_id: int


class BacktestMLRequest(BaseModel):
    model_id: int
    days: int = 60
    sims: int = 10000
    block_size: int = 5
    seed: Optional[int] = None


class CompareRequest(BaseModel):
    ticker: str
    period: str = "5y"
    days: int = 252
    sims: int = 5000
    block_size: int = 5
    seed: Optional[int] = None
    fast: int = 20
    slow: int = 50
    rsi_period: int = 14
    oversold: float = 30.0
    overbought: float = 70.0
    model_ids: list[int] = []


class FundamentalsRequest(BaseModel):
    ticker: str
    force_refresh: bool = False
    llm_backend: Optional[str] = None


class FundamentalsCompareRequest(BaseModel):
    tickers: list[str]
    llm_backend: Optional[str] = None


class WatchlistAddRequest(BaseModel):
    ticker: str


class WatchlistBulkAddRequest(BaseModel):
    tickers: list[str]


class AlertCreateRequest(BaseModel):
    ticker: str
    metric: str
    operator: str
    threshold: float


class SentimentRequest(BaseModel):
    ticker: str
    source_group: str = "all"


class TerminalRequest(BaseModel):
    command: str


# ---- simulation endpoints ----

@app.post("/api/price")
def api_price(req: PriceRequest) -> dict:
    prices = data.download_prices(req.ticker, period=req.period)
    returns = data.log_returns(prices)
    mu, sigma = data.annualize_drift_vol(returns)
    s0 = float(prices.iloc[-1])

    paths = gbm.simulate_gbm_paths(s0, mu, sigma, req.days, req.sims, seed=req.seed)
    summary = gbm.summarize_final_prices(paths)
    png = plotting.plot_paths(paths, f"{req.ticker} GBM simulation")

    run_id = db.record_run("price", req.ticker, req.model_dump(), summary, png)
    return {
        "run_id": run_id, "s0": s0, "mu": mu, "sigma": sigma,
        "summary": summary, "chart_png_base64": _png_b64(png),
        "bands": stats.percentile_bands(paths),
        "distribution": stats.histogram_bins(paths[:, -1]),
    }


def _build_strategy(req: StrategyRequest):
    if req.strategy == "buy-and-hold":
        return BuyAndHold()
    if req.strategy == "sma-crossover":
        return MovingAverageCrossover(fast=req.fast, slow=req.slow)
    if req.strategy == "mean-reversion":
        return MeanReversion(rsi_period=req.rsi_period, oversold=req.oversold, overbought=req.overbought)
    if req.strategy == "ml-technical":
        if req.model_id is None:
            raise HTTPException(400, "model_id is required for strategy=ml-technical")
        record = db.get_model(req.model_id)
        if record is None:
            raise HTTPException(404, f"model {req.model_id} not found")
        bundle = load_bundle(record["model_path"])
        try:
            return MLClassifierStrategy(bundle["model"], bundle["feature_names"])
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
    raise HTTPException(400, f"unknown strategy '{req.strategy}'")


@app.post("/api/strategy")
def api_strategy(req: StrategyRequest) -> dict:
    prices = data.download_prices(req.ticker, period=req.period)
    returns = data.log_returns(prices).to_numpy()
    s0 = float(prices.iloc[-1])
    strategy = _build_strategy(req)

    result = backtest_strategy(strategy, returns, s0, req.days, req.sims, block_size=req.block_size, seed=req.seed)
    summary = {k: result[k] for k in (
        "mean_return", "median_return", "std_return", "p05_return", "p95_return",
        "prob_profit", "mean_max_drawdown", "worst_max_drawdown",
    )}
    png = plotting.plot_final_distribution(
        result["total_returns"], f"{req.ticker} {req.strategy} return distribution"
    )

    run_id = db.record_run("strategy", req.ticker, req.model_dump(), summary, png)
    return {
        "run_id": run_id, "summary": summary, "chart_png_base64": _png_b64(png),
        "distribution": stats.histogram_bins(result["total_returns"]),
    }


@app.post("/api/compare")
def api_compare(req: CompareRequest) -> dict:
    """Run every candidate strategy on the *same* resampled price paths, so the
    comparison isolates strategy skill from which synthetic scenarios each got.
    """
    candidates: dict[str, object] = {
        "buy-and-hold": BuyAndHold(),
        "sma-crossover": MovingAverageCrossover(fast=req.fast, slow=req.slow),
        "mean-reversion": MeanReversion(rsi_period=req.rsi_period, oversold=req.oversold, overbought=req.overbought),
    }
    for model_id in req.model_ids:
        record = db.get_model(model_id)
        if record is None:
            raise HTTPException(404, f"model {model_id} not found")
        bundle = load_bundle(record["model_path"])
        try:
            candidates[f"ml-technical#{model_id} ({record['ticker']})"] = MLClassifierStrategy(
                bundle["model"], bundle["feature_names"]
            )
        except ValueError as exc:
            raise HTTPException(400, f"model {model_id}: {exc}") from exc

    prices = data.download_prices(req.ticker, period=req.period)
    returns = data.log_returns(prices).to_numpy()
    s0 = float(prices.iloc[-1])
    paths = resample_paths(returns, s0, req.days, req.sims, block_size=req.block_size, seed=req.seed)

    results = {}
    for name, strategy in candidates.items():
        summary = evaluate_strategy_on_paths(strategy, paths)
        summary.pop("total_returns")
        results[name] = summary

    ranking = sorted(results, key=lambda name: results[name]["mean_return"], reverse=True)
    png = plotting.plot_strategy_comparison({name: results[name]["mean_return"] for name in results})

    run_id = db.record_run("compare", req.ticker, req.model_dump(), results, png)
    return {"run_id": run_id, "ranking": ranking, "results": results, "chart_png_base64": _png_b64(png)}


@app.post("/api/portfolio")
def api_portfolio(req: PortfolioRequest) -> dict:
    tickers = req.tickers
    if req.weights:
        if len(req.weights) != len(tickers):
            raise HTTPException(400, "weights must have one value per ticker")
        weights = req.weights
    else:
        weights = [1.0 / len(tickers)] * len(tickers)

    prices = data.download_close_prices(tickers, period=req.period)
    paths = portfolio_gbm_paths(prices, weights, req.days, req.sims, initial_value=req.value, seed=req.seed)
    summary = summarize_portfolio(paths)
    png = plotting.plot_paths(paths, "Portfolio simulation")

    run_id = db.record_run("portfolio", ",".join(tickers), req.model_dump(), summary, png)
    return {
        "run_id": run_id, "weights": dict(zip(tickers, weights)),
        "summary": summary, "chart_png_base64": _png_b64(png),
        "bands": stats.percentile_bands(paths),
    }


@app.post("/api/portfolio/optimize")
def api_portfolio_optimize(req: PortfolioOptimizeRequest) -> dict:
    if not req.tickers:
        raise HTTPException(400, "at least one ticker is required")
    prices = data.download_close_prices(req.tickers, period=req.period)
    result = optimize_weights(prices, objective=req.objective, risk_free_rate=req.risk_free_rate)
    return {
        "weights": dict(zip(req.tickers, result["weights"].tolist())),
        "expected_return": result["expected_return"],
        "expected_volatility": result["expected_volatility"],
        "sharpe_ratio": result["sharpe_ratio"],
    }


# ---- fundamentals (investment analyst) endpoints ----

@app.post("/api/fundamentals")
def api_fundamentals(req: FundamentalsRequest) -> dict:
    report = fundamentals_analyst.analyze(
        req.ticker, llm_backend_name=req.llm_backend, force_refresh=req.force_refresh
    )
    png = None
    if report["metrics_history"]:
        png = plotting.plot_fundamentals_overview(
            report["metrics_history"], f"{report['ticker']} revenue / net income / FCF"
        )

    db.record_run(
        "fundamentals", report["ticker"], req.model_dump(),
        {"scores": report["scores"], "confidence": report["confidence"]}, png,
    )
    response = dict(report)
    response["chart_png_base64"] = _png_b64(png) if png else None
    return response


@app.post("/api/fundamentals/compare")
def api_fundamentals_compare(req: FundamentalsCompareRequest) -> dict:
    if not req.tickers:
        raise HTTPException(400, "at least one ticker is required")
    result = fundamentals_compare.compare(req.tickers, llm_backend_name=req.llm_backend)
    return {"rows": result["rows"], "reports": result["reports"], "errors": result["errors"]}


# ---- sentiment endpoint ----

@app.post("/api/sentiment")
def api_sentiment(req: SentimentRequest) -> dict:
    sources = SENTIMENT_SOURCE_GROUPS.get(req.source_group)
    if not sources:
        raise HTTPException(400, f"unknown source group '{req.source_group}'")

    items = sentiment_news.fetch_all_news(req.ticker, sources=sources)
    scored = sorted(
        (
            {
                "title": item["title"],
                "source": item["source"],
                "published": item["published"].isoformat(),
                "score": sentiment_scorer.score_text(item["title"]),
            }
            for item in items
        ),
        key=lambda row: row["published"],
        reverse=True,
    )
    overall_sentiment = sum(row["score"] for row in scored) / len(scored) if scored else None
    daily = sentiment_scorer.daily_sentiment_features(items)

    return {
        "ticker": req.ticker.upper(),
        "source_group": req.source_group,
        "item_count": len(scored),
        "overall_sentiment": overall_sentiment,
        "items": scored[:50],
        "daily": [{"date": str(idx.date()), **row} for idx, row in daily.iterrows()],
    }


# ---- commodities endpoints ----

@app.get("/api/commodities")
def api_commodities_list() -> dict:
    return {"commodities": commodities.COMMODITIES}


@app.get("/api/commodities/quotes")
def api_commodities_quotes() -> dict:
    quotes = []
    errors = {}
    for entry in commodities.COMMODITIES:
        try:
            quotes.append({**commodities.quick_quote(entry["symbol"]), "name": entry["name"]})
        except Exception as exc:
            errors[entry["symbol"]] = str(exc)
    return {"quotes": quotes, "errors": errors}


# ---- watchlist endpoints ----

@app.get("/api/watchlist")
def api_watchlist_list() -> dict:
    tickers = db.list_watchlist_tickers()
    summaries = []
    errors = {}
    for ticker in tickers:
        try:
            summaries.append(fundamentals_watchlist.quick_summary(ticker))
        except Exception as exc:
            errors[ticker] = str(exc)
    return {"tickers": summaries, "errors": errors}


@app.post("/api/watchlist")
def api_watchlist_add(req: WatchlistAddRequest) -> dict:
    summary = fundamentals_watchlist.quick_summary(req.ticker)
    db.add_watchlist_ticker(req.ticker)
    return summary


@app.post("/api/watchlist/bulk")
def api_watchlist_bulk_add(req: WatchlistBulkAddRequest) -> dict:
    added = []
    errors = {}
    seen = set()
    for raw in req.tickers:
        ticker = raw.strip().upper()
        if not ticker or ticker in seen:
            continue
        seen.add(ticker)
        try:
            fundamentals_watchlist.quick_summary(ticker)
            db.add_watchlist_ticker(ticker)
            added.append(ticker)
        except Exception as exc:
            errors[ticker] = str(exc)
    return {"added": added, "errors": errors}


@app.delete("/api/watchlist/{ticker}")
def api_watchlist_remove(ticker: str) -> dict:
    db.remove_watchlist_ticker(ticker)
    return {"removed": ticker.upper()}


# ---- watchlist alert endpoints ----

@app.post("/api/alerts")
def api_alerts_add(req: AlertCreateRequest) -> dict:
    if req.metric not in ("price", "volatility"):
        raise HTTPException(400, f"unknown metric '{req.metric}'")
    if req.operator not in ("above", "below"):
        raise HTTPException(400, f"unknown operator '{req.operator}'")
    alert_id = db.add_alert(req.ticker, req.metric, req.operator, req.threshold)
    return next(a for a in db.list_alerts() if a["id"] == alert_id)


@app.get("/api/alerts")
def api_alerts_list() -> list[dict]:
    return db.list_alerts()


@app.delete("/api/alerts/{alert_id}")
def api_alerts_remove(alert_id: int) -> dict:
    db.remove_alert(alert_id)
    return {"removed": alert_id}


# ---- terminal endpoint ----

@app.post("/api/terminal")
def api_terminal(req: TerminalRequest) -> dict:
    return {"output": terminal.execute(req.command)}


# ---- ML endpoints ----

@app.post("/api/train")
def api_train(req: TrainRequest) -> dict:
    if req.sentiment not in SENTIMENT_SOURCE_GROUPS:
        raise HTTPException(400, f"unknown sentiment source group '{req.sentiment}'")
    sentiment_sources = SENTIMENT_SOURCE_GROUPS[req.sentiment]

    X, y, forward = build_dataset(
        req.ticker, period=req.period, horizon=req.horizon,
        sentiment_sources=sentiment_sources, use_volume=req.use_volume,
    )
    result = train_classifier(X, y, model_type=req.model, test_size=req.test_size)
    test_returns = realized_daily_returns(result["model"], result["X_test"], forward)

    model_path = str(db.MODELS_DIR / f"{req.ticker}_{req.model}_{db.timestamp_slug()}.joblib")
    save_bundle(
        model_path,
        model=result["model"], model_type=req.model, feature_names=result["feature_names"],
        sentiment_sources=sentiment_sources, use_volume=req.use_volume, horizon=req.horizon,
        train_accuracy=result["train_accuracy"], test_accuracy=result["test_accuracy"],
        test_returns=test_returns.to_numpy(),
    )
    model_id = db.register_model(
        req.ticker, req.model, sentiment_sources, req.use_volume, req.horizon,
        result["train_accuracy"], result["test_accuracy"], model_path,
    )
    return {
        "model_id": model_id,
        "train_accuracy": result["train_accuracy"],
        "test_accuracy": result["test_accuracy"],
        "test_report": result["test_report"],
    }


@app.post("/api/predict")
def api_predict(req: PredictRequest) -> dict:
    record = db.get_model(req.model_id)
    if record is None:
        raise HTTPException(404, f"model {req.model_id} not found")
    bundle = load_bundle(record["model_path"])

    latest = build_latest_features(
        record["ticker"], sentiment_sources=bundle["sentiment_sources"], use_volume=bundle["use_volume"]
    )
    X_row = latest[bundle["feature_names"]].to_frame().T.fillna(0.0)
    prob_up = predict_proba_up(bundle["model"], X_row)
    direction = "UP" if prob_up >= 0.5 else "DOWN"

    return {"ticker": record["ticker"], "direction": direction, "prob_up": prob_up, "horizon": bundle["horizon"]}


@app.post("/api/backtest_ml")
def api_backtest_ml(req: BacktestMLRequest) -> dict:
    record = db.get_model(req.model_id)
    if record is None:
        raise HTTPException(404, f"model {req.model_id} not found")
    bundle = load_bundle(record["model_path"])
    test_returns = bundle["test_returns"]

    equity = resample_return_series(
        test_returns, days=req.days, n_sims=req.sims, block_size=req.block_size, seed=req.seed
    )
    summary = summarize_equity(equity)
    png = plotting.plot_paths(equity, "ML strategy Monte Carlo projection")

    run_id = db.record_run("backtest_ml", record["ticker"], req.model_dump(), summary, png)
    return {
        "run_id": run_id, "summary": summary, "chart_png_base64": _png_b64(png),
        "bands": stats.percentile_bands(equity),
    }


# ---- history endpoints ----

@app.get("/api/runs")
def api_list_runs(limit: int = 50) -> list[dict]:
    return db.list_runs(limit)


@app.get("/api/runs/{run_id}/chart")
def api_run_chart(run_id: int) -> Response:
    record = db.get_run(run_id)
    if record is None or not record.get("chart_png"):
        raise HTTPException(404, "no chart for this run")
    return Response(content=record["chart_png"], media_type="image/png")


@app.get("/api/runs/{run_id}/pdf")
def api_run_pdf(run_id: int) -> Response:
    record = db.get_run(run_id)
    if record is None:
        raise HTTPException(404, "run not found")
    return Response(content=pdf_report.build_run_pdf(record), media_type="application/pdf")


@app.get("/api/models")
def api_list_models() -> list[dict]:
    return db.list_models()


# ---- background alert checker ----

ALERT_CHECK_INTERVAL_SECONDS = int(os.environ.get("MCSTOCK_ALERT_INTERVAL_SECONDS", "300"))


def _alert_condition_met(alert: dict) -> bool:
    prices = data.download_prices(alert["ticker"], period="3mo")
    if alert["metric"] == "price":
        value = float(prices.iloc[-1])
    else:
        returns = data.log_returns(prices)
        _, value = data.annualize_drift_vol(returns)
    if alert["operator"] == "above":
        return value >= alert["threshold"]
    return value <= alert["threshold"]


def _check_alerts() -> None:
    for alert in db.list_pending_alerts():
        try:
            if _alert_condition_met(alert):
                db.mark_alert_triggered(alert["id"])
        except Exception:
            continue


scheduler = AsyncIOScheduler()


@app.on_event("startup")
async def _launch_alert_checker() -> None:
    scheduler.add_job(
        _check_alerts, "interval", seconds=ALERT_CHECK_INTERVAL_SECONDS,
        id="alert_checker", replace_existing=True,
    )
    scheduler.start()


@app.on_event("shutdown")
async def _stop_alert_checker() -> None:
    scheduler.shutdown(wait=False)
