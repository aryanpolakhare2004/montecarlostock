"""Classical ML classifiers for binary up/down prediction."""
from __future__ import annotations

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODEL_REGISTRY = {
    "logreg": lambda: LogisticRegression(max_iter=1000),
    "random_forest": lambda: RandomForestClassifier(n_estimators=300, max_depth=5, random_state=0),
    "gradient_boosting": lambda: GradientBoostingClassifier(random_state=0),
}


def chronological_split(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2):
    """Split time-ordered data without shuffling, to avoid lookahead bias."""
    n_test = max(1, int(len(X) * test_size))
    split = len(X) - n_test
    return X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]


def train_classifier(X: pd.DataFrame, y: pd.Series, model_type: str = "logreg", test_size: float = 0.2) -> dict:
    """Fit a scaled classifier on a chronological (no-shuffle) train/test split."""
    if model_type not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model_type '{model_type}', choose from {list(MODEL_REGISTRY)}")

    X_train, X_test, y_train, y_test = chronological_split(X, y, test_size)

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", MODEL_REGISTRY[model_type]()),
    ])
    pipeline.fit(X_train, y_train)

    return {
        "model": pipeline,
        "model_type": model_type,
        "feature_names": list(X.columns),
        "train_accuracy": float(accuracy_score(y_train, pipeline.predict(X_train))),
        "test_accuracy": float(accuracy_score(y_test, pipeline.predict(X_test))),
        "test_report": classification_report(y_test, pipeline.predict(X_test), zero_division=0),
        "X_test": X_test,
        "y_test": y_test,
    }


def predict_proba_up(model: Pipeline, X_row: pd.DataFrame) -> float:
    """Probability of the 'up' (class 1) label for the last row of `X_row`."""
    proba = model.predict_proba(X_row)
    classes = list(model.named_steps["classifier"].classes_)
    return float(proba[-1, classes.index(1)])
