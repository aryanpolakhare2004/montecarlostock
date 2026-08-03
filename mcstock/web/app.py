"""FastAPI web frontend for mcstock: full CLI parity plus SQLite-backed run/model history."""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .. import data, gbm, plotting
from ..backtest import backtest_strategy, evaluate_strategy_on_paths, resample_paths
from ..fundamentals import analyst as fundamentals_analyst
from ..fundamentals import compare as fundamentals_compare
from ..historical_backtest import realized_daily_returns, resample_return_series, summarize_equity
from ..ml.dataset import build_dataset, build_latest_features
from ..ml.models import load_bundle, predict_proba_up, save_bundle, train_classifier
from ..portfolio import portfolio_gbm_paths, summarize_portfolio
from ..strategies.buy_and_hold import BuyAndHold
from ..strategies.ml_classifier import MLClassifierStrategy
from ..strategies.moving_average import MovingAverageCrossover
from . import db

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
    model_ids: list[int] = []


class FundamentalsRequest(BaseModel):
    ticker: str
    force_refresh: bool = False
    llm_backend: Optional[str] = None


class FundamentalsCompareRequest(BaseModel):
    tickers: list[str]
    llm_backend: Optional[str] = None


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
    }


def _build_strategy(req: StrategyRequest):
    if req.strategy == "buy-and-hold":
        return BuyAndHold()
    if req.strategy == "sma-crossover":
        return MovingAverageCrossover(fast=req.fast, slow=req.slow)
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
    return {"run_id": run_id, "summary": summary, "chart_png_base64": _png_b64(png)}


@app.post("/api/compare")
def api_compare(req: CompareRequest) -> dict:
    """Run every candidate strategy on the *same* resampled price paths, so the
    comparison isolates strategy skill from which synthetic scenarios each got.
    """
    candidates: dict[str, object] = {
        "buy-and-hold": BuyAndHold(),
        "sma-crossover": MovingAverageCrossover(fast=req.fast, slow=req.slow),
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
    return {"run_id": run_id, "summary": summary, "chart_png_base64": _png_b64(png)}


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


@app.get("/api/models")
def api_list_models() -> list[dict]:
    return db.list_models()
