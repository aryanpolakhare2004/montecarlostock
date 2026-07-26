import numpy as np
import pandas as pd

from mcstock.ml.models import MODEL_REGISTRY, chronological_split, predict_proba_up, train_classifier


def _synthetic_dataset(n=300, seed=0):
    rng = np.random.default_rng(seed)
    signal = rng.normal(0, 1, n)
    noise = rng.normal(0, 0.1, n)
    X = pd.DataFrame({"signal": signal, "noise": noise})
    y = pd.Series((signal + noise > 0).astype(int))
    return X, y


def test_chronological_split_preserves_order_no_shuffle():
    X, y = _synthetic_dataset()
    X_train, X_test, y_train, y_test = chronological_split(X, y, test_size=0.2)
    assert len(X_test) == 60
    assert X_train.index.max() < X_test.index.min()


def test_train_classifier_all_model_types_learn_signal():
    X, y = _synthetic_dataset()
    for model_type in MODEL_REGISTRY:
        result = train_classifier(X, y, model_type=model_type, test_size=0.3)
        assert result["test_accuracy"] > 0.7
        prob = predict_proba_up(result["model"], X.iloc[[-1]])
        assert 0.0 <= prob <= 1.0


def test_unknown_model_type_raises():
    X, y = _synthetic_dataset()
    try:
        train_classifier(X, y, model_type="not-a-model")
        assert False, "expected ValueError"
    except ValueError:
        pass
