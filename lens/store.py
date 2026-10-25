"""SQLite storage for dated check results and imported traffic numbers."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB = "data/lens.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY,
    client_id TEXT NOT NULL,
    period TEXT NOT NULL,              -- YYYY-MM
    started_at TEXT NOT NULL,
    providers TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES runs(id),
    client_id TEXT NOT NULL,
    period TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT,
    prompt_id TEXT NOT NULL,
    prompt TEXT NOT NULL,
    language TEXT,
    service TEXT,
    answer TEXT,
    citations TEXT,
    mentioned INTEGER,
    matched_alias TEXT,
    match_score REAL,
    snippet TEXT,
    error TEXT,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS results_client_period ON results(client_id, period);
CREATE TABLE IF NOT EXISTS competitors (
    result_id INTEGER NOT NULL REFERENCES results(id),
    name TEXT NOT NULL,
    kind TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS competitors_result ON competitors(result_id);
CREATE TABLE IF NOT EXISTS traffic (
    client_id TEXT NOT NULL,
    period TEXT NOT NULL,
    source TEXT NOT NULL,              -- ga4 | gsc
    metric TEXT NOT NULL,
    value REAL NOT NULL,
    PRIMARY KEY (client_id, period, source, metric)
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


class Store:
    def __init__(self, path: str | Path | None = None):
        path = str(path or os.environ.get("LENS_DB", DEFAULT_DB))
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def start_run(self, client_id: str, period: str, providers: list[str]) -> int:
        cur = self.conn.execute(
            "INSERT INTO runs (client_id, period, started_at, providers) VALUES (?, ?, ?, ?)",
            (client_id, period, now(), ",".join(providers)),
        )
        self.conn.commit()
        return cur.lastrowid

    def add_result(self, *, run_id: int, client_id: str, period: str, provider: str, model: str | None,
                   prompt_id: str, prompt: str, language: str | None, service: str | None,
                   answer: str | None = None, citations: list[str] | None = None,
                   mentioned: bool | None = None, matched_alias: str | None = None,
                   match_score: float | None = None, snippet: str | None = None,
                   error: str | None = None, competitors: list | None = None) -> int:
        cur = self.conn.execute(
            """INSERT INTO results (run_id, client_id, period, provider, model, prompt_id, prompt,
                   language, service, answer, citations, mentioned, matched_alias, match_score,
                   snippet, error, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, client_id, period, provider, model, prompt_id, prompt, language, service, answer,
             json.dumps(citations or []), None if mentioned is None else int(mentioned),
             matched_alias, match_score, snippet, error, now()),
        )
        result_id = cur.lastrowid
        self.conn.executemany(
            "INSERT INTO competitors (result_id, name, kind) VALUES (?, ?, ?)",
            [(result_id, c.name, c.kind) for c in competitors or []],
        )
        self.conn.commit()
        return result_id

    def set_traffic(self, client_id: str, period: str, source: str, metric: str, value: float):
        self.conn.execute(
            "INSERT OR REPLACE INTO traffic (client_id, period, source, metric, value) VALUES (?, ?, ?, ?, ?)",
            (client_id, period, source, metric, value),
        )
        self.conn.commit()

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.conn.execute(sql, params).fetchall()
