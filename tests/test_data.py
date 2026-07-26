import numpy as np
import pandas as pd

from mcstock.data import annualize_drift_vol, log_returns


def test_log_returns():
    prices = pd.Series([100.0, 110.0, 121.0])
    returns = log_returns(prices)
    assert len(returns) == 2
    assert np.isclose(returns.iloc[0], np.log(1.1))


def test_annualize_drift_vol():
    rng = np.random.default_rng(0)
    daily = pd.Series(rng.normal(0.0005, 0.01, 1000))
    mu, sigma = annualize_drift_vol(daily)
    assert np.isclose(mu, daily.mean() * 252)
    assert np.isclose(sigma, daily.std(ddof=1) * np.sqrt(252))
