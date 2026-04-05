from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .providers.base import ProviderModel


@dataclass(frozen=True)
class RouteEvent:
    alias: str
    provider_name: str
    backend_model: str
    success: bool
    retryable: bool
    is_fallback: bool
    category: str | None
    latency_ms: float | None
    details: Any
    created_at: float


class StateStore:
    def load_inventory(self, provider_name: str) -> list[ProviderModel]:
        raise NotImplementedError

    def save_inventory(self, provider_name: str, models: list[ProviderModel], *, reason: str) -> None:
        raise NotImplementedError

    def save_classifications(self, classifications: dict[str, tuple[str, ...]], *, source: str) -> None:
        raise NotImplementedError

    def record_attempt(self, event: RouteEvent) -> None:
        raise NotImplementedError

    def apply_success(self, provider_name: str, backend_model: str, *, latency_ms: float | None) -> None:
        raise NotImplementedError

    def apply_failure(self, provider_name: str, backend_model: str, *, category: str, retryable: bool) -> None:
        raise NotImplementedError

    def get_model_state(self) -> dict[str, dict[str, Any]]:
        raise NotImplementedError

    def get_recent_events(self, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    def snapshot(self) -> dict[str, Any]:
        raise NotImplementedError


class SqliteStateStore(StateStore):
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS inventory (
                    provider_name TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    is_free INTEGER NOT NULL,
                    tags_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (provider_name, model_id)
                );

                CREATE TABLE IF NOT EXISTS classifications (
                    model_id TEXT PRIMARY KEY,
                    tags_json TEXT NOT NULL,
                    source TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS model_state (
                    provider_name TEXT NOT NULL,
                    backend_model TEXT NOT NULL,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    retryable_failure_count INTEGER NOT NULL DEFAULT 0,
                    last_error_category TEXT,
                    last_error_at REAL,
                    cooldown_until REAL NOT NULL DEFAULT 0,
                    last_latency_ms REAL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (provider_name, backend_model)
                );

                CREATE TABLE IF NOT EXISTS route_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias TEXT NOT NULL,
                    provider_name TEXT NOT NULL,
                    backend_model TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    retryable INTEGER NOT NULL,
                    is_fallback INTEGER NOT NULL,
                    category TEXT,
                    latency_ms REAL,
                    details_json TEXT,
                    created_at REAL NOT NULL
                );
                """
            )

    def load_inventory(self, provider_name: str) -> list[ProviderModel]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT inventory.model_id, inventory.is_free, inventory.tags_json, inventory.metadata_json, classifications.tags_json AS classified_tags
                FROM inventory
                LEFT JOIN classifications ON classifications.model_id = inventory.model_id
                WHERE inventory.provider_name = ?
                ORDER BY inventory.model_id
                """,
                (provider_name,),
            ).fetchall()
        models: list[ProviderModel] = []
        for row in rows:
            base_tags = tuple(json.loads(row["tags_json"]))
            classified_tags = tuple(json.loads(row["classified_tags"])) if row["classified_tags"] else ()
            tags = tuple(dict.fromkeys([*base_tags, *classified_tags]))
            models.append(
                ProviderModel(
                    id=str(row["model_id"]),
                    provider=provider_name,
                    is_free=bool(row["is_free"]),
                    tags=tags,
                    metadata=json.loads(row["metadata_json"]),
                )
            )
        return models

    def save_inventory(self, provider_name: str, models: list[ProviderModel], *, reason: str) -> None:
        now = time.time()
        with self._connect() as connection:
            connection.execute("DELETE FROM inventory WHERE provider_name = ?", (provider_name,))
            connection.executemany(
                """
                INSERT INTO inventory (provider_name, model_id, is_free, tags_json, metadata_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        provider_name,
                        model.id,
                        1 if model.is_free else 0,
                        json.dumps(list(model.tags)),
                        json.dumps({**model.metadata, "refresh_reason": reason}, sort_keys=True),
                        now,
                    )
                    for model in models
                ],
            )

    def save_classifications(self, classifications: dict[str, tuple[str, ...]], *, source: str) -> None:
        now = time.time()
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO classifications (model_id, tags_json, source, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(model_id) DO UPDATE SET
                  tags_json = excluded.tags_json,
                  source = excluded.source,
                  updated_at = excluded.updated_at
                """,
                [
                    (model_id, json.dumps(list(tags)), source, now)
                    for model_id, tags in classifications.items()
                ],
            )

    def record_attempt(self, event: RouteEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO route_events (
                    alias, provider_name, backend_model, success, retryable, is_fallback,
                    category, latency_ms, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.alias,
                    event.provider_name,
                    event.backend_model,
                    1 if event.success else 0,
                    1 if event.retryable else 0,
                    1 if event.is_fallback else 0,
                    event.category,
                    event.latency_ms,
                    json.dumps(event.details, sort_keys=True) if event.details is not None else None,
                    event.created_at,
                ),
            )

    def apply_success(self, provider_name: str, backend_model: str, *, latency_ms: float | None) -> None:
        now = time.time()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO model_state (
                    provider_name, backend_model, success_count, failure_count, retryable_failure_count,
                    last_error_category, last_error_at, cooldown_until, last_latency_ms, updated_at
                ) VALUES (?, ?, 1, 0, 0, NULL, NULL, 0, ?, ?)
                ON CONFLICT(provider_name, backend_model) DO UPDATE SET
                  success_count = model_state.success_count + 1,
                  cooldown_until = 0,
                  last_latency_ms = excluded.last_latency_ms,
                  updated_at = excluded.updated_at
                """,
                (provider_name, backend_model, latency_ms, now),
            )

    def apply_failure(self, provider_name: str, backend_model: str, *, category: str, retryable: bool) -> None:
        now = time.time()
        cooldown_until = now + self._cooldown_seconds(category)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO model_state (
                    provider_name, backend_model, success_count, failure_count, retryable_failure_count,
                    last_error_category, last_error_at, cooldown_until, last_latency_ms, updated_at
                ) VALUES (?, ?, 0, 1, ?, ?, ?, ?, NULL, ?)
                ON CONFLICT(provider_name, backend_model) DO UPDATE SET
                  failure_count = model_state.failure_count + 1,
                  retryable_failure_count = model_state.retryable_failure_count + excluded.retryable_failure_count,
                  last_error_category = excluded.last_error_category,
                  last_error_at = excluded.last_error_at,
                  cooldown_until = CASE
                    WHEN excluded.cooldown_until > model_state.cooldown_until THEN excluded.cooldown_until
                    ELSE model_state.cooldown_until
                  END,
                  updated_at = excluded.updated_at
                """,
                (provider_name, backend_model, 1 if retryable else 0, category, now, cooldown_until, now),
            )

    def get_model_state(self) -> dict[str, dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT provider_name, backend_model, success_count, failure_count, retryable_failure_count,
                       last_error_category, last_error_at, cooldown_until, last_latency_ms, updated_at
                FROM model_state
                """
            ).fetchall()
        return {
            f"{row['provider_name']}::{row['backend_model']}": {
                "provider_name": row["provider_name"],
                "backend_model": row["backend_model"],
                "success_count": row["success_count"],
                "failure_count": row["failure_count"],
                "retryable_failure_count": row["retryable_failure_count"],
                "last_error_category": row["last_error_category"],
                "last_error_at": row["last_error_at"],
                "cooldown_until": row["cooldown_until"],
                "last_latency_ms": row["last_latency_ms"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        }

    def get_recent_events(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT alias, provider_name, backend_model, success, retryable, is_fallback,
                       category, latency_ms, details_json, created_at
                FROM route_events
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "alias": row["alias"],
                "provider_name": row["provider_name"],
                "backend_model": row["backend_model"],
                "success": bool(row["success"]),
                "retryable": bool(row["retryable"]),
                "is_fallback": bool(row["is_fallback"]),
                "category": row["category"],
                "latency_ms": row["latency_ms"],
                "details": json.loads(row["details_json"]) if row["details_json"] else None,
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def snapshot(self) -> dict[str, Any]:
        with self._connect() as connection:
            inventory_count = connection.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
            classification_count = connection.execute("SELECT COUNT(*) FROM classifications").fetchone()[0]
            event_count = connection.execute("SELECT COUNT(*) FROM route_events").fetchone()[0]
        return {
            "db_path": str(self.db_path),
            "inventory_count": inventory_count,
            "classification_count": classification_count,
            "event_count": event_count,
            "model_state": list(self.get_model_state().values()),
        }

    @staticmethod
    def _cooldown_seconds(category: str) -> float:
        return {
            "rate_limited": 300.0,
            "timeout": 60.0,
            "server_error": 60.0,
            "transport_error": 30.0,
            "model_missing": 15.0,
            "unauthorized": 3600.0,
            "bad_request": 600.0,
        }.get(category, 30.0)
