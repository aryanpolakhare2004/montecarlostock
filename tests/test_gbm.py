import numpy as np

from mcstock.gbm import simulate_gbm_paths, summarize_final_prices


def test_simulate_gbm_paths_shape():
    paths = simulate_gbm_paths(s0=100.0, mu=0.05, sigma=0.2, days=10, n_sims=50, seed=1)
    assert paths.shape == (50, 11)
    assert np.allclose(paths[:, 0], 100.0)


def test_zero_vol_matches_deterministic_drift():
    days = 5
    paths = simulate_gbm_paths(s0=100.0, mu=0.1, sigma=0.0, days=days, n_sims=3, seed=0)
    dt = 1 / 252
    expected = 100.0 * np.exp(0.1 * dt * np.arange(days + 1))
    for i in range(3):
        assert np.allclose(paths[i], expected)


def test_summarize_final_prices_keys():
    paths = simulate_gbm_paths(s0=50.0, mu=0.0, sigma=0.3, days=20, n_sims=200, seed=42)
    summary = summarize_final_prices(paths)
    assert set(summary) == {"mean", "median", "std", "p05", "p25", "p75", "p95", "prob_above_start"}
    assert summary["p05"] <= summary["median"] <= summary["p95"]
