"""SQLite persistence for run history and the trained-model registry."""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("MCSTOCK_DATA_DIR", "mcstock_data"))
MODELS_DIR = DATA_DIR / "models"
DB_PATH = DATA_DIR / "mcstock.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_type TEXT NOT NULL,
    ticker TEXT NOT NULL,
    params_json TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    chart_png BLOB,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    model_type TEXT NOT NULL,
    sentiment_sources TEXT,
    use_volume INTEGER NOT NULL,
    horizon INTEGER NOT NULL,
    train_accuracy REAL NOT NULL,
    test_accuracy REAL NOT NULL,
    model_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def record_run(run_type: str, ticker: str, params: dict, summary: dict, chart_png: bytes | None) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO runs (run_type, ticker, params_json, summary_json, chart_png, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (run_type, ticker, json.dumps(params), json.dumps(summary), chart_png,
             datetime.now(timezone.utc).isoformat()),
        )
        return cursor.lastrowid


def list_runs(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, run_type, ticker, params_json, summary_json, created_at, "
            "(chart_png IS NOT NULL) AS has_chart FROM runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_run_row_to_dict(row) for row in rows]


def get_run(run_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT *, (chart_png IS NOT NULL) AS has_chart FROM runs WHERE id = ?", (run_id,)
        ).fetchone()
    return _run_row_to_dict(row, include_chart=True) if row else None


def _run_row_to_dict(row: sqlite3.Row, include_chart: bool = False) -> dict:
    result = {
        "id": row["id"],
        "run_type": row["run_type"],
        "ticker": row["ticker"],
        "params": json.loads(row["params_json"]),
        "summary": json.loads(row["summary_json"]),
        "created_at": row["created_at"],
        "has_chart": bool(row["has_chart"]),
    }
    if include_chart:
        result["chart_png"] = row["chart_png"]
    return result


def register_model(
    ticker: str,
    model_type: str,
    sentiment_sources: list[str] | None,
    use_volume: bool,
    horizon: int,
    train_accuracy: float,
    test_accuracy: float,
    model_path: str,
) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO models (ticker, model_type, sentiment_sources, use_volume, horizon, "
            "train_accuracy, test_accuracy, model_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ticker, model_type, json.dumps(sentiment_sources) if sentiment_sources else None,
                int(use_volume), horizon, train_accuracy, test_accuracy, model_path,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return cursor.lastrowid


def list_models() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM models ORDER BY id DESC").fetchall()
    return [_model_row_to_dict(row) for row in rows]


def get_model(model_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone()
    return _model_row_to_dict(row) if row else None


def _model_row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "ticker": row["ticker"],
        "model_type": row["model_type"],
        "sentiment_sources": json.loads(row["sentiment_sources"]) if row["sentiment_sources"] else None,
        "use_volume": bool(row["use_volume"]),
        "horizon": row["horizon"],
        "train_accuracy": row["train_accuracy"],
        "test_accuracy": row["test_accuracy"],
        "model_path": row["model_path"],
        "created_at": row["created_at"],
    }
