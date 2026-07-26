import numpy as np
import pandas as pd

from mcstock.features import TECHNICAL_FEATURE_COLUMNS, VOLUME_FEATURE_COLUMNS, build_technical_features


def _synthetic_close(n=200, seed=0):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0005, 0.01, n)
    return pd.Series(100 * np.exp(np.cumsum(returns)))


def test_build_technical_features_columns_and_shape():
    close = _synthetic_close()
    features = build_technical_features(close)
    assert list(features.columns) == TECHNICAL_FEATURE_COLUMNS
    assert len(features) == len(close)


def test_build_technical_features_are_causal():
    close = _synthetic_close()
    full = build_technical_features(close)
    truncated = build_technical_features(close.iloc[:100])
    # dropping future rows must not change already-computed past values
    pd.testing.assert_series_equal(full["rsi_14"].iloc[:100], truncated["rsi_14"], check_names=False)
    pd.testing.assert_series_equal(full["macd"].iloc[:100], truncated["macd"], check_names=False)


def test_build_technical_features_with_volume():
    close = _synthetic_close()
    volume = pd.Series(np.random.default_rng(1).integers(1000, 5000, len(close)).astype(float))
    features = build_technical_features(close, volume)
    for col in VOLUME_FEATURE_COLUMNS:
        assert col in features.columns
