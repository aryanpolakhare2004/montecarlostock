"""Wraps a fitted technical-only classifier as a Strategy for Monte Carlo bootstrap backtests."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..features import TECHNICAL_FEATURE_COLUMNS, build_technical_features
from .base import Strategy


class MLClassifierStrategy(Strategy):
    """Applies a fitted sklearn pipeline to whatever price path it's given --
    real history or a Monte Carlo bootstrapped path.

    Only supports models trained purely on price-derived technical features
    (see mcstock.features.TECHNICAL_FEATURE_COLUMNS): sentiment and volume
    can't be recomputed for a synthetic bootstrapped path. Models trained
    with those extra features should instead be evaluated via
    mcstock.historical_backtest, which resamples the model's own realized
    historical returns rather than re-deriving positions from synthetic prices.
    """

    def __init__(self, model, feature_names: list[str]):
        extra = set(feature_names) - set(TECHNICAL_FEATURE_COLUMNS)
        if extra:
            raise ValueError(
                f"MLClassifierStrategy only supports price-derived technical features; "
                f"got extra columns {sorted(extra)} (sentiment/volume). Train with "
                "--sentiment none --no-volume, or use mcstock.historical_backtest instead."
            )
        self.model = model
        self.feature_names = list(feature_names)

    def positions(self, prices: np.ndarray) -> np.ndarray:
        close = pd.Series(prices)
        features = build_technical_features(close)[self.feature_names]
        warmup = features.isna().any(axis=1).to_numpy()
        preds = self.model.predict(features.fillna(0.0)).astype(float)
        preds[warmup] = 0.0
        return preds[:-1]
