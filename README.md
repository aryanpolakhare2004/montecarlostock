# montecarlostock

Monte Carlo simulations for stock prices, trading strategies, and portfolios,
calibrated from live historical data via `yfinance`. Also includes trainable
ML trading models (technical indicators + free news sentiment) for binary
up/down prediction, with Monte Carlo robustness projection of their realized
returns.

## Install

```
pip install -e ".[dev]"
```

Reddit sentiment is an optional extra (needs a free Reddit API app):

```
pip install -e ".[dev,reddit]"
```

## Usage

### Simulate future price paths (GBM)

Calibrates drift and volatility from historical returns, then simulates
many Geometric Brownian Motion price paths.

```
mcstock price AAPL --days 252 --sims 10000 --out aapl_paths.png
```

### Backtest a rule-based trading strategy

Block-bootstraps historical daily returns into many synthetic price paths
and evaluates a strategy's return/drawdown distribution across them.

```
mcstock strategy AAPL --strategy sma-crossover --fast 20 --slow 50 --sims 5000 --out aapl_strategy.png
```

Strategies available: `buy-and-hold`, `sma-crossover`, `ml-technical` (a
trained, technical-indicator-only ML classifier -- see below).

### Train an ML classifier for binary up/down prediction

Engineers technical-indicator features (returns, moving averages, RSI, MACD,
Bollinger %B, volatility, volume) purely with pandas/numpy, optionally joins
in daily news sentiment, and trains a classifier on a **chronological**
train/test split (no shuffling, so the test period is always strictly later
in time than training -- avoids lookahead bias).

```
mcstock train AAPL --model random_forest --sentiment yfinance --period 5y --model-out aapl_model.joblib
```

- `--model`: `logreg`, `random_forest`, or `gradient_boosting`
- `--sentiment`: `none`, `yfinance`, `rss`, `reddit`, or `all` -- headlines are
  scored with VADER (lexicon-based, no downloads) and aggregated per day into
  mean/std sentiment, headline volume, and percent positive/negative.
  - `yfinance`/`rss` need no setup.
  - `reddit` needs a free "script" app from https://www.reddit.com/prefs/apps,
    passed via `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` env vars.
- `--no-volume`: drop volume features. Required if you want to later plug the
  saved model into `mcstock strategy --strategy ml-technical` (that pathway
  reruns the model on Monte Carlo bootstrapped *price-only* paths, so any
  feature that isn't derivable from price alone -- sentiment, volume -- isn't
  available there).

**Caveat:** daily stock direction is very noisy. Expect test accuracy close
to 50/50 for most tickers/periods -- a large gap between train and test
accuracy (as with `random_forest` here) means the model is overfitting noise,
not finding real signal. Treat this as a demonstration pipeline, not a
production trading system.

### Predict the next move

```
mcstock predict AAPL --model-in aapl_model.joblib
```

Prints a binary UP/DOWN call plus the model's predicted probability.

### Monte Carlo project a trained model's robustness

Sentiment can't be recomputed for a hypothetical bootstrapped price path, so
sentiment-aware models are instead evaluated on their *actual* realized daily
returns over the held-out test period, and that realized-return series is
what gets block-bootstrap resampled into thousands of alternate equity
curves:

```
mcstock backtest-ml --model-in aapl_model.joblib --sims 10000 --days 60 --out aapl_ml_mc.png
```

### Simulate a portfolio

Simulates correlated GBM paths for multiple tickers (correlation estimated
from historical returns) and combines them into total portfolio value.

```
mcstock portfolio AAPL MSFT GOOG --weights 0.5 0.3 0.2 --value 10000 --out portfolio.png
```

## Web dashboard

A FastAPI + vanilla HTML/JS dashboard gives browser access to everything the
CLI does, backed by a local SQLite database (`mcstock_data/mcstock.db`) that
logs every simulation run and every trained model:

```
mcstock serve
```

Then open http://127.0.0.1:8000. Sections: **Price**, **Strategy**,
**Compare**, **Portfolio**, **Train**, **Predict**, **Backtest ML**, and
**History** (browses past runs and trained models from SQLite; chart PNGs are
stored as BLOBs and served from the DB, not the filesystem).

**Compare** answers "which algorithm works best for this stock": it runs
buy-and-hold, sma-crossover, and any technical-only trained models on the
*same* Monte Carlo bootstrapped price paths (not independently reseeded
scenarios), so the ranking reflects actual strategy skill rather than which
strategy happened to get luckier synthetic paths.

Trained models and the SQLite DB live under `mcstock_data/` (override with
the `MCSTOCK_DATA_DIR` env var); this directory is gitignored.

## Tests

```
pytest
```
