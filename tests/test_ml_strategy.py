import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from mcstock.features import TECHNICAL_FEATURE_COLUMNS
from mcstock.strategies.ml_classifier import MLClassifierStrategy


def _dummy_model(feature_names):
    pipeline = Pipeline([("scaler", StandardScaler()), ("classifier", LogisticRegression())])
    rng = np.random.default_rng(0)
    X = pd.DataFrame(rng.normal(size=(50, len(feature_names))), columns=feature_names)
    y = (X.iloc[:, 0] > 0).astype(int)
    pipeline.fit(X, y)
    return pipeline


def test_positions_shape_matches_prices():
    feature_names = TECHNICAL_FEATURE_COLUMNS[:3]
    model = _dummy_model(feature_names)
    strategy = MLClassifierStrategy(model, feature_names)

    prices = 100 * np.exp(np.cumsum(np.random.default_rng(1).normal(0, 0.01, 80)))
    positions = strategy.positions(prices)
    assert len(positions) == len(prices) - 1
    assert set(np.unique(positions)) <= {0.0, 1.0}


def test_rejects_non_technical_features():
    with pytest.raises(ValueError):
        MLClassifierStrategy(model=None, feature_names=["sma_5_ratio", "sentiment_mean"])
