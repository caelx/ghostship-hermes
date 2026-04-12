from __future__ import annotations

import json
import math
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .providers.base import ProviderModel

_LATENCY_ALPHA = 0.3


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
    first_text_latency_ms: float | None
    details: Any
    created_at: float


def _json_loads(value: str | None, *, default: Any) -> Any:
    if not value:
        return default
    return json.loads(value)


class StateStore:
    def load_inventory(self, provider_name: str) -> list[ProviderModel]:
        raise NotImplementedError

    def save_inventory(self, provider_name: str, models: list[ProviderModel], *, reason: str) -> None:
        raise NotImplementedError

    def save_classifications(self, classifications: dict[str, tuple[str, ...]], *, source: str) -> None:
        raise NotImplementedError

    def save_rankings(
        self,
        rankings: dict[str, dict[str, Any]],
        *,
        source: str,
        worker_provider_name: str | None,
        worker_backend_model: str | None,
    ) -> None:
        raise NotImplementedError

    def record_attempt(self, event: RouteEvent) -> None:
        raise NotImplementedError

    def apply_success(self, provider_name: str, backend_model: str, *, latency_ms: float | None, first_text_latency_ms: float | None) -> None:
        raise NotImplementedError

    def apply_failure(self, provider_name: str, backend_model: str, *, category: str, retryable: bool) -> None:
        raise NotImplementedError

    def record_provider_exhaustion(
        self,
        provider_name: str,
        *,
        backend_model: str,
        category: str,
        zero_output: bool,
        suspect_window_seconds: float,
        disable_seconds: float,
        probe_escalation_factor: float,
        max_disable_seconds: float,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def clear_provider_exhaustion(self, provider_name: str) -> None:
        raise NotImplementedError

    def activate_provider_probe(self, provider_name: str) -> None:
        raise NotImplementedError

    def record_refresh(
        self,
        provider_name: str,
        *,
        reason: str,
        success: bool,
        model_count: int = 0,
        category: str | None = None,
        details: Any = None,
    ) -> None:
        raise NotImplementedError

    def get_model_state(self) -> dict[str, dict[str, Any]]:
        raise NotImplementedError

    def get_provider_state(self) -> dict[str, dict[str, Any]]:
        raise NotImplementedError

    def get_rankings(self) -> dict[str, dict[str, Any]]:
        raise NotImplementedError

    def get_overrides(self) -> dict[str, Any]:
        raise NotImplementedError

    def upsert_model_override(self, provider_name: str, backend_model: str, *, enabled: bool | None = None, weight: float | None = None) -> None:
        raise NotImplementedError

    def upsert_provider_override(self, provider_name: str, *, enabled: bool | None = None, weight: float | None = None) -> None:
        raise NotImplementedError

    def upsert_alias_pin(self, alias: str, model_ids: tuple[str, ...]) -> None:
        raise NotImplementedError

    def set_provider_cooldown(self, provider_name: str, *, cooldown_until: float, category: str, details: Any = None) -> None:
        raise NotImplementedError

    def put_response(self, response_id: str, payload: dict[str, Any], *, conversation_history: list[dict[str, Any]], instructions: str | None) -> None:
        raise NotImplementedError

    def get_response(self, response_id: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def delete_response(self, response_id: str) -> bool:
        raise NotImplementedError

    def get_conversation_response(self, conversation: str) -> str | None:
        raise NotImplementedError

    def set_conversation_response(self, conversation: str, response_id: str) -> None:
        raise NotImplementedError

    def load_chat_session(self, session_id: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def save_chat_session(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        raise NotImplementedError

    def get_recent_events(self, limit: int) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_route_metric_rows(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_refresh_metric_rows(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    def snapshot(self) -> dict[str, Any]:
        raise NotImplementedError


class SqliteStateStore(StateStore):
    def __init__(
        self,
        db_path: Path,
        *,
        rolling_window_seconds: float = 3600.0,
        exhaustion_cooldown_ladder_seconds: tuple[int, ...] = (30, 60, 300, 600, 1200, 2400),
    ):
        self.db_path = db_path
        self.rolling_window_seconds = max(rolling_window_seconds, 1.0)
        self.exhaustion_cooldown_ladder_seconds = tuple(float(value) for value in exhaustion_cooldown_ladder_seconds) or (30.0,)
        self._model_state_cache: dict[str, dict[str, Any]] | None = None
        self._provider_state_cache: dict[str, dict[str, Any]] | None = None
        self._rankings_cache: dict[str, dict[str, Any]] | None = None
        self._overrides_cache: dict[str, Any] | None = None
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.db_path.touch(exist_ok=True)
        except OSError:
            pass
        connection = sqlite3.connect(str(self.db_path), timeout=30.0)
        connection.row_factory = sqlite3.Row
        return connection

    def _invalidate_read_caches(self, *cache_names: str) -> None:
        names = cache_names or (
            "_model_state_cache",
            "_provider_state_cache",
            "_rankings_cache",
            "_overrides_cache",
        )
        for name in names:
            setattr(self, name, None)

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
                    recent_success REAL NOT NULL DEFAULT 0,
                    recent_failure REAL NOT NULL DEFAULT 0,
                    recent_rate_limit REAL NOT NULL DEFAULT 0,
                    recent_timeout REAL NOT NULL DEFAULT 0,
                    recent_auth_failure REAL NOT NULL DEFAULT 0,
                    recent_transport_failure REAL NOT NULL DEFAULT 0,
                    recent_server_error REAL NOT NULL DEFAULT 0,
                    recent_exhaustion REAL NOT NULL DEFAULT 0,
                    last_error_category TEXT,
                    last_error_at REAL,
                    cooldown_until REAL NOT NULL DEFAULT 0,
                    cooldown_reason TEXT,
                    exhaustion_streak INTEGER NOT NULL DEFAULT 0,
                    last_exhaustion_at REAL,
                    last_latency_ms REAL,
                    last_first_text_latency_ms REAL,
                    latency_avg_ms REAL,
                    first_text_latency_avg_ms REAL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (provider_name, backend_model)
                );

                CREATE TABLE IF NOT EXISTS provider_state (
                    provider_name TEXT PRIMARY KEY,
                    success_count INTEGER NOT NULL DEFAULT 0,
                    failure_count INTEGER NOT NULL DEFAULT 0,
                    request_success_count INTEGER NOT NULL DEFAULT 0,
                    request_failure_count INTEGER NOT NULL DEFAULT 0,
                    refresh_success_count INTEGER NOT NULL DEFAULT 0,
                    refresh_failure_count INTEGER NOT NULL DEFAULT 0,
                    recent_success REAL NOT NULL DEFAULT 0,
                    recent_failure REAL NOT NULL DEFAULT 0,
                    recent_rate_limit REAL NOT NULL DEFAULT 0,
                    recent_timeout REAL NOT NULL DEFAULT 0,
                    recent_auth_failure REAL NOT NULL DEFAULT 0,
                    recent_transport_failure REAL NOT NULL DEFAULT 0,
                    recent_server_error REAL NOT NULL DEFAULT 0,
                    recent_refresh_failure REAL NOT NULL DEFAULT 0,
                    recent_exhaustion REAL NOT NULL DEFAULT 0,
                    last_error_category TEXT,
                    last_error_at REAL,
                    cooldown_until REAL NOT NULL DEFAULT 0,
                    disable_reason TEXT,
                    breaker_level INTEGER NOT NULL DEFAULT 0,
                    suspect_backend_model TEXT,
                    suspect_category TEXT,
                    suspect_at REAL,
                    suspect_zero_output INTEGER NOT NULL DEFAULT 0,
                    probe_mode INTEGER NOT NULL DEFAULT 0,
                    last_probe_at REAL,
                    last_latency_ms REAL,
                    last_first_text_latency_ms REAL,
                    latency_avg_ms REAL,
                    first_text_latency_avg_ms REAL,
                    last_refresh_at REAL,
                    last_refresh_reason TEXT,
                    last_refresh_ok INTEGER,
                    last_refresh_error_json TEXT,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS model_rankings (
                    provider_name TEXT NOT NULL,
                    backend_model TEXT NOT NULL,
                    alias_scores_json TEXT NOT NULL,
                    rerank_scores_json TEXT NOT NULL,
                    reason TEXT,
                    confidence REAL,
                    source TEXT NOT NULL,
                    worker_provider_name TEXT,
                    worker_backend_model TEXT,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (provider_name, backend_model)
                );

                CREATE TABLE IF NOT EXISTS model_overrides (
                    provider_name TEXT NOT NULL,
                    backend_model TEXT NOT NULL,
                    enabled INTEGER,
                    weight REAL NOT NULL DEFAULT 0,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (provider_name, backend_model)
                );

                CREATE TABLE IF NOT EXISTS provider_overrides (
                    provider_name TEXT PRIMARY KEY,
                    enabled INTEGER,
                    weight REAL NOT NULL DEFAULT 0,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS alias_pins (
                    alias TEXT PRIMARY KEY,
                    models_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
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
                    first_text_latency_ms REAL,
                    details_json TEXT,
                    created_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS refresh_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider_name TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    model_count INTEGER NOT NULL DEFAULT 0,
                    category TEXT,
                    details_json TEXT,
                    created_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS stored_responses (
                    response_id TEXT PRIMARY KEY,
                    response_json TEXT NOT NULL,
                    conversation_history_json TEXT NOT NULL,
                    instructions TEXT,
                    accessed_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS response_conversations (
                    conversation TEXT PRIMARY KEY,
                    response_id TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    messages_json TEXT NOT NULL,
                    updated_at REAL NOT NULL
                );
                """
            )
            self._ensure_column(connection, "model_state", "recent_success", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(connection, "model_state", "recent_failure", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(connection, "model_state", "recent_rate_limit", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(connection, "model_state", "recent_timeout", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(connection, "model_state", "recent_auth_failure", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(connection, "model_state", "recent_transport_failure", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(connection, "model_state", "recent_server_error", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(connection, "model_state", "recent_exhaustion", "REAL NOT NULL DEFAULT 0")
            self._ensure_column(connection, "model_state", "cooldown_reason", "TEXT")
            self._ensure_column(connection, "model_state", "exhaustion_streak", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(connection, "model_state", "last_exhaustion_at", "REAL")
            self._ensure_column(connection, "model_state", "last_first_text_latency_ms", "REAL")
            self._ensure_column(connection, "model_state", "latency_avg_ms", "REAL")
            self._ensure_column(connection, "model_state", "first_text_latency_avg_ms", "REAL")
            self._ensure_column(connection, "route_events", "first_text_latency_ms", "REAL")
            self._ensure_column(connection, "provider_state", "disable_reason", "TEXT")
            self._ensure_column(connection, "provider_state", "breaker_level", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(connection, "provider_state", "suspect_backend_model", "TEXT")
            self._ensure_column(connection, "provider_state", "suspect_category", "TEXT")
            self._ensure_column(connection, "provider_state", "suspect_at", "REAL")
            self._ensure_column(connection, "provider_state", "suspect_zero_output", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(connection, "provider_state", "probe_mode", "INTEGER NOT NULL DEFAULT 0")
            self._ensure_column(connection, "provider_state", "last_probe_at", "REAL")

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        existing = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

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
            base_tags = tuple(_json_loads(row["tags_json"], default=[]))
            classified_tags = tuple(_json_loads(row["classified_tags"], default=[]))
            tags = tuple(dict.fromkeys([*base_tags, *classified_tags]))
            models.append(
                ProviderModel(
                    id=str(row["model_id"]),
                    provider=provider_name,
                    is_free=bool(row["is_free"]),
                    tags=tags,
                    metadata=_json_loads(row["metadata_json"], default={}),
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
        self._invalidate_read_caches()

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
        self._invalidate_read_caches("_rankings_cache")

    def save_rankings(
        self,
        rankings: dict[str, dict[str, Any]],
        *,
        source: str,
        worker_provider_name: str | None,
        worker_backend_model: str | None,
    ) -> None:
        now = time.time()
        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO model_rankings (
                    provider_name, backend_model, alias_scores_json, rerank_scores_json,
                    reason, confidence, source, worker_provider_name, worker_backend_model, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_name, backend_model) DO UPDATE SET
                  alias_scores_json = excluded.alias_scores_json,
                  rerank_scores_json = excluded.rerank_scores_json,
                  reason = excluded.reason,
                  confidence = excluded.confidence,
                  source = excluded.source,
                  worker_provider_name = excluded.worker_provider_name,
                  worker_backend_model = excluded.worker_backend_model,
                  updated_at = excluded.updated_at
                """,
                [
                    (
                        ranking["provider_name"],
                        ranking["backend_model"],
                        json.dumps(ranking.get("alias_scores", {}), sort_keys=True),
                        json.dumps(ranking.get("rerank_scores", {}), sort_keys=True),
                        ranking.get("reason"),
                        ranking.get("confidence"),
                        source,
                        worker_provider_name,
                        worker_backend_model,
                        now,
                    )
                    for ranking in rankings.values()
                ],
            )
        self._invalidate_read_caches("_rankings_cache")

    def record_attempt(self, event: RouteEvent) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO route_events (
                    alias, provider_name, backend_model, success, retryable, is_fallback,
                    category, latency_ms, first_text_latency_ms, details_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    event.first_text_latency_ms,
                    json.dumps(event.details, sort_keys=True) if event.details is not None else None,
                    event.created_at,
                ),
            )
        self._invalidate_read_caches("_model_state_cache", "_provider_state_cache")

    def apply_success(self, provider_name: str, backend_model: str, *, latency_ms: float | None, first_text_latency_ms: float | None) -> None:
        now = time.time()
        with self._connect() as connection:
            model_row = self._fetch_model_row(connection, provider_name, backend_model)
            provider_row = self._fetch_provider_row(connection, provider_name)
            model_payload = self._success_payload(model_row, now, latency_ms=latency_ms, first_text_latency_ms=first_text_latency_ms)
            provider_payload = self._success_payload(provider_row, now, latency_ms=latency_ms, first_text_latency_ms=first_text_latency_ms)
            connection.execute(
                """
                INSERT INTO model_state (
                    provider_name, backend_model, success_count, failure_count, retryable_failure_count,
                    recent_success, recent_failure, recent_rate_limit, recent_timeout, recent_auth_failure,
                    recent_transport_failure, recent_server_error, recent_exhaustion,
                    last_error_category, last_error_at, cooldown_until,
                    last_latency_ms, last_first_text_latency_ms, latency_avg_ms, first_text_latency_avg_ms, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_name, backend_model) DO UPDATE SET
                  success_count = excluded.success_count,
                  failure_count = excluded.failure_count,
                  retryable_failure_count = excluded.retryable_failure_count,
                  recent_success = excluded.recent_success,
                  recent_failure = excluded.recent_failure,
                  recent_rate_limit = excluded.recent_rate_limit,
                  recent_timeout = excluded.recent_timeout,
                  recent_auth_failure = excluded.recent_auth_failure,
                  recent_transport_failure = excluded.recent_transport_failure,
                  recent_server_error = excluded.recent_server_error,
                  recent_exhaustion = excluded.recent_exhaustion,
                  last_error_category = excluded.last_error_category,
                  last_error_at = excluded.last_error_at,
                  cooldown_until = excluded.cooldown_until,
                  last_latency_ms = excluded.last_latency_ms,
                  last_first_text_latency_ms = excluded.last_first_text_latency_ms,
                  latency_avg_ms = excluded.latency_avg_ms,
                  first_text_latency_avg_ms = excluded.first_text_latency_avg_ms,
                  updated_at = excluded.updated_at
                """,
                (
                    provider_name,
                    backend_model,
                    model_payload["success_count"],
                    model_payload["failure_count"],
                    model_payload["retryable_failure_count"],
                    model_payload["recent_success"],
                    model_payload["recent_failure"],
                    model_payload["recent_rate_limit"],
                    model_payload["recent_timeout"],
                    model_payload["recent_auth_failure"],
                    model_payload["recent_transport_failure"],
                    model_payload["recent_server_error"],
                    model_payload["recent_exhaustion"],
                    None,
                    None,
                    0,
                    latency_ms,
                    first_text_latency_ms,
                    model_payload["latency_avg_ms"],
                    model_payload["first_text_latency_avg_ms"],
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO provider_state (
                    provider_name, success_count, failure_count, request_success_count, request_failure_count,
                    refresh_success_count, refresh_failure_count,
                    recent_success, recent_failure, recent_rate_limit, recent_timeout, recent_auth_failure,
                    recent_transport_failure, recent_server_error, recent_refresh_failure, recent_exhaustion,
                    last_error_category, last_error_at, cooldown_until, last_latency_ms, last_first_text_latency_ms,
                    latency_avg_ms, first_text_latency_avg_ms, last_refresh_at, last_refresh_reason,
                    last_refresh_ok, last_refresh_error_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_name) DO UPDATE SET
                  success_count = excluded.success_count,
                  failure_count = excluded.failure_count,
                  request_success_count = excluded.request_success_count,
                  request_failure_count = excluded.request_failure_count,
                  refresh_success_count = excluded.refresh_success_count,
                  refresh_failure_count = excluded.refresh_failure_count,
                  recent_success = excluded.recent_success,
                  recent_failure = excluded.recent_failure,
                  recent_rate_limit = excluded.recent_rate_limit,
                  recent_timeout = excluded.recent_timeout,
                  recent_auth_failure = excluded.recent_auth_failure,
                  recent_transport_failure = excluded.recent_transport_failure,
                  recent_server_error = excluded.recent_server_error,
                  recent_refresh_failure = excluded.recent_refresh_failure,
                  recent_exhaustion = excluded.recent_exhaustion,
                  last_error_category = excluded.last_error_category,
                  last_error_at = excluded.last_error_at,
                  cooldown_until = excluded.cooldown_until,
                  last_latency_ms = excluded.last_latency_ms,
                  last_first_text_latency_ms = excluded.last_first_text_latency_ms,
                  latency_avg_ms = excluded.latency_avg_ms,
                  first_text_latency_avg_ms = excluded.first_text_latency_avg_ms,
                  updated_at = excluded.updated_at
                """,
                (
                    provider_name,
                    provider_payload["success_count"],
                    provider_payload["failure_count"],
                    provider_payload["request_success_count"],
                    provider_payload["request_failure_count"],
                    provider_payload["refresh_success_count"],
                    provider_payload["refresh_failure_count"],
                    provider_payload["recent_success"],
                    provider_payload["recent_failure"],
                    provider_payload["recent_rate_limit"],
                    provider_payload["recent_timeout"],
                    provider_payload["recent_auth_failure"],
                    provider_payload["recent_transport_failure"],
                    provider_payload["recent_server_error"],
                    provider_payload["recent_refresh_failure"],
                    provider_payload["recent_exhaustion"],
                    provider_row["last_error_category"] if provider_row else None,
                    provider_row["last_error_at"] if provider_row else None,
                    0,
                    latency_ms,
                    first_text_latency_ms,
                    provider_payload["latency_avg_ms"],
                    provider_payload["first_text_latency_avg_ms"],
                    provider_row["last_refresh_at"] if provider_row else None,
                    provider_row["last_refresh_reason"] if provider_row else None,
                    provider_row["last_refresh_ok"] if provider_row else None,
                    provider_row["last_refresh_error_json"] if provider_row else None,
                    now,
                ),
            )
            connection.execute(
                """
                UPDATE model_state
                SET exhaustion_streak = 0,
                    last_exhaustion_at = NULL,
                    cooldown_reason = NULL
                WHERE provider_name = ? AND backend_model = ?
                """,
                (provider_name, backend_model),
            )
            connection.execute(
                """
                UPDATE provider_state
                SET disable_reason = NULL,
                    breaker_level = 0,
                    suspect_backend_model = NULL,
                    suspect_category = NULL,
                    suspect_at = NULL,
                    suspect_zero_output = 0,
                    probe_mode = 0,
                    last_probe_at = NULL
                WHERE provider_name = ?
                """,
                (provider_name,),
            )
        self._invalidate_read_caches("_model_state_cache", "_provider_state_cache")

    def apply_failure(self, provider_name: str, backend_model: str, *, category: str, retryable: bool) -> None:
        now = time.time()
        cooldown_until = now + self._model_cooldown_seconds(category, row=None)
        with self._connect() as connection:
            model_row = self._fetch_model_row(connection, provider_name, backend_model)
            provider_row = self._fetch_provider_row(connection, provider_name)
            model_payload = self._failure_payload(model_row, now, category=category, retryable=retryable)
            provider_payload = self._failure_payload(provider_row, now, category=category, retryable=retryable, provider_level=True)
            cooldown_until = now + self._model_cooldown_seconds(category, row=model_row)
            connection.execute(
                """
                INSERT INTO model_state (
                    provider_name, backend_model, success_count, failure_count, retryable_failure_count,
                    recent_success, recent_failure, recent_rate_limit, recent_timeout, recent_auth_failure,
                    recent_transport_failure, recent_server_error, recent_exhaustion,
                    last_error_category, last_error_at, cooldown_until,
                    last_latency_ms, last_first_text_latency_ms, latency_avg_ms, first_text_latency_avg_ms, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_name, backend_model) DO UPDATE SET
                  success_count = excluded.success_count,
                  failure_count = excluded.failure_count,
                  retryable_failure_count = excluded.retryable_failure_count,
                  recent_success = excluded.recent_success,
                  recent_failure = excluded.recent_failure,
                  recent_rate_limit = excluded.recent_rate_limit,
                  recent_timeout = excluded.recent_timeout,
                  recent_auth_failure = excluded.recent_auth_failure,
                  recent_transport_failure = excluded.recent_transport_failure,
                  recent_server_error = excluded.recent_server_error,
                    recent_exhaustion = excluded.recent_exhaustion,
                    last_error_category = excluded.last_error_category,
                    last_error_at = excluded.last_error_at,
                    cooldown_until = CASE
                    WHEN excluded.cooldown_until > model_state.cooldown_until THEN excluded.cooldown_until
                    ELSE model_state.cooldown_until
                  END,
                  updated_at = excluded.updated_at
                """,
                (
                    provider_name,
                    backend_model,
                    model_payload["success_count"],
                    model_payload["failure_count"],
                    model_payload["retryable_failure_count"],
                    model_payload["recent_success"],
                    model_payload["recent_failure"],
                    model_payload["recent_rate_limit"],
                    model_payload["recent_timeout"],
                    model_payload["recent_auth_failure"],
                    model_payload["recent_transport_failure"],
                    model_payload["recent_server_error"],
                    model_payload["recent_exhaustion"],
                    category,
                    now,
                    cooldown_until,
                    model_row["last_latency_ms"] if model_row else None,
                    model_row["last_first_text_latency_ms"] if model_row else None,
                    model_row["latency_avg_ms"] if model_row else None,
                    model_row["first_text_latency_avg_ms"] if model_row else None,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO provider_state (
                    provider_name, success_count, failure_count, request_success_count, request_failure_count,
                    refresh_success_count, refresh_failure_count,
                    recent_success, recent_failure, recent_rate_limit, recent_timeout, recent_auth_failure,
                    recent_transport_failure, recent_server_error, recent_refresh_failure, recent_exhaustion,
                    last_error_category, last_error_at, cooldown_until, last_latency_ms, last_first_text_latency_ms,
                    latency_avg_ms, first_text_latency_avg_ms, last_refresh_at, last_refresh_reason,
                    last_refresh_ok, last_refresh_error_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_name) DO UPDATE SET
                  success_count = excluded.success_count,
                  failure_count = excluded.failure_count,
                  request_success_count = excluded.request_success_count,
                  request_failure_count = excluded.request_failure_count,
                  refresh_success_count = excluded.refresh_success_count,
                  refresh_failure_count = excluded.refresh_failure_count,
                  recent_success = excluded.recent_success,
                  recent_failure = excluded.recent_failure,
                  recent_rate_limit = excluded.recent_rate_limit,
                  recent_timeout = excluded.recent_timeout,
                  recent_auth_failure = excluded.recent_auth_failure,
                  recent_transport_failure = excluded.recent_transport_failure,
                  recent_server_error = excluded.recent_server_error,
                  recent_refresh_failure = excluded.recent_refresh_failure,
                    recent_exhaustion = excluded.recent_exhaustion,
                    last_error_category = excluded.last_error_category,
                    last_error_at = excluded.last_error_at,
                    updated_at = excluded.updated_at
                """,
                (
                    provider_name,
                    provider_payload["success_count"],
                    provider_payload["failure_count"],
                    provider_payload["request_success_count"],
                    provider_payload["request_failure_count"],
                    provider_payload["refresh_success_count"],
                    provider_payload["refresh_failure_count"],
                    provider_payload["recent_success"],
                    provider_payload["recent_failure"],
                    provider_payload["recent_rate_limit"],
                    provider_payload["recent_timeout"],
                    provider_payload["recent_auth_failure"],
                    provider_payload["recent_transport_failure"],
                    provider_payload["recent_server_error"],
                    provider_payload["recent_refresh_failure"],
                    provider_payload["recent_exhaustion"],
                    category,
                    now,
                    provider_row["cooldown_until"] if provider_row else 0,
                    provider_row["last_latency_ms"] if provider_row else None,
                    provider_row["last_first_text_latency_ms"] if provider_row else None,
                    provider_row["latency_avg_ms"] if provider_row else None,
                    provider_row["first_text_latency_avg_ms"] if provider_row else None,
                    provider_row["last_refresh_at"] if provider_row else None,
                    provider_row["last_refresh_reason"] if provider_row else None,
                    provider_row["last_refresh_ok"] if provider_row else None,
                    provider_row["last_refresh_error_json"] if provider_row else None,
                    now,
                ),
            )
            connection.execute(
                """
                UPDATE model_state
                SET exhaustion_streak = ?,
                    last_exhaustion_at = ?,
                    cooldown_reason = ?
                WHERE provider_name = ? AND backend_model = ?
                """,
                (
                    self._next_exhaustion_streak(model_row, now, category=category),
                    (now if self._is_exhaustion_category(category) else None),
                    (category if self._is_exhaustion_category(category) else None),
                    provider_name,
                    backend_model,
                ),
            )
        self._invalidate_read_caches("_model_state_cache", "_provider_state_cache")

    def record_provider_exhaustion(
        self,
        provider_name: str,
        *,
        backend_model: str,
        category: str,
        zero_output: bool,
        suspect_window_seconds: float,
        disable_seconds: float,
        probe_escalation_factor: float,
        max_disable_seconds: float,
    ) -> dict[str, Any]:
        now = time.time()
        if not zero_output or not self._is_exhaustion_category(category):
            return {"disabled": False, "probe_failed": False}
        with self._connect() as connection:
            row = self._fetch_provider_row(connection, provider_name)
            if row is None:
                connection.execute(
                    "INSERT INTO provider_state (provider_name, updated_at) VALUES (?, ?)",
                    (provider_name, now),
                )
                row = self._fetch_provider_row(connection, provider_name)
            assert row is not None
            breaker_level = int(row["breaker_level"] or 0)
            probe_mode = bool(row["probe_mode"] or 0)
            suspect_model = row["suspect_backend_model"]
            suspect_at = float(row["suspect_at"] or 0)
            disable_reason = row["disable_reason"]
            disable = False
            probe_failed = False

            if category == "insufficient_balance":
                disable = True
            elif probe_mode:
                disable = True
                probe_failed = True
            elif suspect_model and suspect_model != backend_model and (now - suspect_at) <= suspect_window_seconds:
                disable = True

            if disable:
                next_level = max(1, breaker_level + 1)
                duration = min(
                    max_disable_seconds,
                    disable_seconds * (probe_escalation_factor ** max(0, next_level - 1)),
                )
                connection.execute(
                    """
                    UPDATE provider_state
                    SET cooldown_until = CASE
                            WHEN ? > cooldown_until THEN ?
                            ELSE cooldown_until
                        END,
                        disable_reason = ?,
                        breaker_level = ?,
                        suspect_backend_model = NULL,
                        suspect_category = NULL,
                        suspect_at = NULL,
                        suspect_zero_output = 0,
                        probe_mode = 0,
                        last_probe_at = ?
                    WHERE provider_name = ?
                    """,
                    (
                        now + duration,
                        now + duration,
                        category if category == "insufficient_balance" else (disable_reason or category),
                        next_level,
                        (now if probe_failed else row["last_probe_at"]),
                        provider_name,
                    ),
                )
            else:
                connection.execute(
                    """
                    UPDATE provider_state
                    SET suspect_backend_model = ?,
                        suspect_category = ?,
                        suspect_at = ?,
                        suspect_zero_output = 1
                    WHERE provider_name = ?
                    """,
                    (backend_model, category, now, provider_name),
                )
        self._invalidate_read_caches("_provider_state_cache")
        return {"disabled": disable, "probe_failed": probe_failed}

    def clear_provider_exhaustion(self, provider_name: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE provider_state
                SET disable_reason = NULL,
                    breaker_level = 0,
                    suspect_backend_model = NULL,
                    suspect_category = NULL,
                    suspect_at = NULL,
                    suspect_zero_output = 0,
                    probe_mode = 0,
                    last_probe_at = NULL
                WHERE provider_name = ?
                """,
                (provider_name,),
            )
        self._invalidate_read_caches("_provider_state_cache")

    def activate_provider_probe(self, provider_name: str) -> None:
        now = time.time()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE provider_state
                SET probe_mode = 1,
                    last_probe_at = ?
                WHERE provider_name = ?
                """,
                (now, provider_name),
            )
        self._invalidate_read_caches("_provider_state_cache")

    def record_refresh(
        self,
        provider_name: str,
        *,
        reason: str,
        success: bool,
        model_count: int = 0,
        category: str | None = None,
        details: Any = None,
    ) -> None:
        now = time.time()
        with self._connect() as connection:
            provider_row = self._fetch_provider_row(connection, provider_name)
            payload = self._refresh_payload(provider_row, now, success=success, category=category)
            cooldown_until = 0 if success else (provider_row["cooldown_until"] if provider_row else 0)
            if not success and category == "unauthorized":
                cooldown_until = max(cooldown_until or 0, now + self._cooldown_seconds(category))
            connection.execute(
                """
                INSERT INTO provider_state (
                    provider_name, success_count, failure_count, request_success_count, request_failure_count,
                    refresh_success_count, refresh_failure_count,
                    recent_success, recent_failure, recent_rate_limit, recent_timeout, recent_auth_failure,
                    recent_transport_failure, recent_server_error, recent_refresh_failure, recent_exhaustion,
                    last_error_category, last_error_at, cooldown_until, last_latency_ms, last_first_text_latency_ms,
                    latency_avg_ms, first_text_latency_avg_ms, last_refresh_at, last_refresh_reason,
                    last_refresh_ok, last_refresh_error_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_name) DO UPDATE SET
                  success_count = excluded.success_count,
                  failure_count = excluded.failure_count,
                  request_success_count = excluded.request_success_count,
                  request_failure_count = excluded.request_failure_count,
                  refresh_success_count = excluded.refresh_success_count,
                  refresh_failure_count = excluded.refresh_failure_count,
                  recent_success = excluded.recent_success,
                  recent_failure = excluded.recent_failure,
                  recent_rate_limit = excluded.recent_rate_limit,
                  recent_timeout = excluded.recent_timeout,
                  recent_auth_failure = excluded.recent_auth_failure,
                  recent_transport_failure = excluded.recent_transport_failure,
                  recent_server_error = excluded.recent_server_error,
                  recent_refresh_failure = excluded.recent_refresh_failure,
                  recent_exhaustion = excluded.recent_exhaustion,
                  last_error_category = excluded.last_error_category,
                  last_error_at = excluded.last_error_at,
                  cooldown_until = excluded.cooldown_until,
                  last_refresh_at = excluded.last_refresh_at,
                  last_refresh_reason = excluded.last_refresh_reason,
                  last_refresh_ok = excluded.last_refresh_ok,
                  last_refresh_error_json = excluded.last_refresh_error_json,
                  updated_at = excluded.updated_at
                """,
                (
                    provider_name,
                    payload["success_count"],
                    payload["failure_count"],
                    payload["request_success_count"],
                    payload["request_failure_count"],
                    payload["refresh_success_count"],
                    payload["refresh_failure_count"],
                    payload["recent_success"],
                    payload["recent_failure"],
                    payload["recent_rate_limit"],
                    payload["recent_timeout"],
                    payload["recent_auth_failure"],
                    payload["recent_transport_failure"],
                    payload["recent_server_error"],
                    payload["recent_refresh_failure"],
                    payload["recent_exhaustion"],
                    category if not success else (provider_row["last_error_category"] if provider_row else None),
                    now if not success else (provider_row["last_error_at"] if provider_row else None),
                    cooldown_until,
                    provider_row["last_latency_ms"] if provider_row else None,
                    provider_row["last_first_text_latency_ms"] if provider_row else None,
                    provider_row["latency_avg_ms"] if provider_row else None,
                    provider_row["first_text_latency_avg_ms"] if provider_row else None,
                    now,
                    reason,
                    1 if success else 0,
                    json.dumps(details, sort_keys=True) if details is not None else None,
                    now,
                ),
            )
            connection.execute(
                """
                INSERT INTO refresh_events (provider_name, reason, success, model_count, category, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    provider_name,
                    reason,
                    1 if success else 0,
                    model_count,
                    category,
                    json.dumps(details, sort_keys=True) if details is not None else None,
                    now,
                ),
            )
            if success:
                connection.execute(
                    """
                    UPDATE provider_state
                    SET cooldown_until = 0,
                        disable_reason = NULL,
                        breaker_level = 0,
                        suspect_backend_model = NULL,
                        suspect_category = NULL,
                        suspect_at = NULL,
                        suspect_zero_output = 0,
                        probe_mode = 0,
                        last_probe_at = NULL
                    WHERE provider_name = ?
                    """,
                    (provider_name,),
                )
        self._invalidate_read_caches("_provider_state_cache")

    def get_model_state(self) -> dict[str, dict[str, Any]]:
        if self._model_state_cache is None:
            with self._connect() as connection:
                rows = connection.execute("SELECT * FROM model_state").fetchall()
            self._model_state_cache = {
                f"{row['provider_name']}::{row['backend_model']}": dict(row)
                for row in rows
            }
        return self._model_state_cache

    def get_provider_state(self) -> dict[str, dict[str, Any]]:
        if self._provider_state_cache is None:
            with self._connect() as connection:
                rows = connection.execute("SELECT * FROM provider_state").fetchall()
            self._provider_state_cache = {
                str(row["provider_name"]): dict(row)
                for row in rows
            }
        return self._provider_state_cache

    def get_rankings(self) -> dict[str, dict[str, Any]]:
        if self._rankings_cache is None:
            with self._connect() as connection:
                rows = connection.execute("SELECT * FROM model_rankings").fetchall()
            rankings: dict[str, dict[str, Any]] = {}
            for row in rows:
                key = f"{row['provider_name']}::{row['backend_model']}"
                rankings[key] = {
                    "provider_name": row["provider_name"],
                    "backend_model": row["backend_model"],
                    "alias_scores": _json_loads(row["alias_scores_json"], default={}),
                    "rerank_scores": _json_loads(row["rerank_scores_json"], default={}),
                    "reason": row["reason"],
                    "confidence": row["confidence"],
                    "source": row["source"],
                    "worker_provider_name": row["worker_provider_name"],
                    "worker_backend_model": row["worker_backend_model"],
                    "updated_at": row["updated_at"],
                }
            self._rankings_cache = rankings
        return self._rankings_cache

    def get_overrides(self) -> dict[str, Any]:
        if self._overrides_cache is None:
            with self._connect() as connection:
                model_rows = connection.execute("SELECT * FROM model_overrides ORDER BY provider_name, backend_model").fetchall()
                provider_rows = connection.execute("SELECT * FROM provider_overrides ORDER BY provider_name").fetchall()
                alias_rows = connection.execute("SELECT * FROM alias_pins ORDER BY alias").fetchall()
            self._overrides_cache = {
                "models": [
                    {
                        "provider_name": row["provider_name"],
                        "backend_model": row["backend_model"],
                        "enabled": None if row["enabled"] is None else bool(row["enabled"]),
                        "weight": row["weight"],
                        "updated_at": row["updated_at"],
                    }
                    for row in model_rows
                ],
                "providers": [
                    {
                        "provider_name": row["provider_name"],
                        "enabled": None if row["enabled"] is None else bool(row["enabled"]),
                        "weight": row["weight"],
                        "updated_at": row["updated_at"],
                    }
                    for row in provider_rows
                ],
                "alias_pins": [
                    {
                        "alias": row["alias"],
                        "models": tuple(_json_loads(row["models_json"], default=[])),
                        "updated_at": row["updated_at"],
                    }
                    for row in alias_rows
                ],
            }
        return self._overrides_cache

    def upsert_model_override(self, provider_name: str, backend_model: str, *, enabled: bool | None = None, weight: float | None = None) -> None:
        now = time.time()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT enabled, weight FROM model_overrides WHERE provider_name = ? AND backend_model = ?",
                (provider_name, backend_model),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO model_overrides (provider_name, backend_model, enabled, weight, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(provider_name, backend_model) DO UPDATE SET
                  enabled = excluded.enabled,
                  weight = excluded.weight,
                  updated_at = excluded.updated_at
                """,
                (
                    provider_name,
                    backend_model,
                    (
                        existing["enabled"]
                        if enabled is None and existing is not None
                        else (None if enabled is None else (1 if enabled else 0))
                    ),
                    weight if weight is not None else (existing["weight"] if existing else 0.0),
                    now,
                ),
            )
        self._invalidate_read_caches("_overrides_cache")

    def upsert_provider_override(self, provider_name: str, *, enabled: bool | None = None, weight: float | None = None) -> None:
        now = time.time()
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT enabled, weight FROM provider_overrides WHERE provider_name = ?",
                (provider_name,),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO provider_overrides (provider_name, enabled, weight, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(provider_name) DO UPDATE SET
                  enabled = excluded.enabled,
                  weight = excluded.weight,
                  updated_at = excluded.updated_at
                """,
                (
                    provider_name,
                    (
                        existing["enabled"]
                        if enabled is None and existing is not None
                        else (None if enabled is None else (1 if enabled else 0))
                    ),
                    weight if weight is not None else (existing["weight"] if existing else 0.0),
                    now,
                ),
            )
        self._invalidate_read_caches("_overrides_cache")

    def upsert_alias_pin(self, alias: str, model_ids: tuple[str, ...]) -> None:
        now = time.time()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO alias_pins (alias, models_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(alias) DO UPDATE SET
                  models_json = excluded.models_json,
                  updated_at = excluded.updated_at
                """,
                (alias, json.dumps(list(model_ids)), now),
            )
        self._invalidate_read_caches("_overrides_cache")

    def set_provider_cooldown(self, provider_name: str, *, cooldown_until: float, category: str, details: Any = None) -> None:
        now = time.time()
        with self._connect() as connection:
            row = self._fetch_provider_row(connection, provider_name)
            payload = self._refresh_payload(row, now, success=False, category=category)
            connection.execute(
                """
                INSERT INTO provider_state (
                    provider_name, success_count, failure_count, request_success_count, request_failure_count,
                    refresh_success_count, refresh_failure_count,
                    recent_success, recent_failure, recent_rate_limit, recent_timeout, recent_auth_failure,
                    recent_transport_failure, recent_server_error, recent_refresh_failure, recent_exhaustion,
                    last_error_category, last_error_at, cooldown_until, last_latency_ms, last_first_text_latency_ms,
                    latency_avg_ms, first_text_latency_avg_ms, last_refresh_at, last_refresh_reason,
                    last_refresh_ok, last_refresh_error_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_name) DO UPDATE SET
                  cooldown_until = CASE
                    WHEN excluded.cooldown_until > provider_state.cooldown_until THEN excluded.cooldown_until
                    ELSE provider_state.cooldown_until
                  END,
                  last_error_category = excluded.last_error_category,
                  last_error_at = excluded.last_error_at,
                  recent_failure = excluded.recent_failure,
                  recent_rate_limit = excluded.recent_rate_limit,
                  recent_timeout = excluded.recent_timeout,
                  recent_auth_failure = excluded.recent_auth_failure,
                  recent_transport_failure = excluded.recent_transport_failure,
                  recent_server_error = excluded.recent_server_error,
                  recent_refresh_failure = excluded.recent_refresh_failure,
                  recent_exhaustion = excluded.recent_exhaustion,
                  updated_at = excluded.updated_at
                """,
                (
                    provider_name,
                    payload["success_count"],
                    payload["failure_count"],
                    payload["request_success_count"],
                    payload["request_failure_count"],
                    payload["refresh_success_count"],
                    payload["refresh_failure_count"],
                    payload["recent_success"],
                    payload["recent_failure"],
                    payload["recent_rate_limit"],
                    payload["recent_timeout"],
                    payload["recent_auth_failure"],
                    payload["recent_transport_failure"],
                    payload["recent_server_error"],
                    payload["recent_refresh_failure"],
                    payload["recent_exhaustion"],
                    category,
                    now,
                    cooldown_until,
                    row["last_latency_ms"] if row else None,
                    row["last_first_text_latency_ms"] if row else None,
                    row["latency_avg_ms"] if row else None,
                    row["first_text_latency_avg_ms"] if row else None,
                    row["last_refresh_at"] if row else None,
                    row["last_refresh_reason"] if row else None,
                    row["last_refresh_ok"] if row else None,
                    json.dumps(details, sort_keys=True) if details is not None else (row["last_refresh_error_json"] if row else None),
                    now,
                ),
            )
        self._invalidate_read_caches("_provider_state_cache")

    def put_response(self, response_id: str, payload: dict[str, Any], *, conversation_history: list[dict[str, Any]], instructions: str | None) -> None:
        now = time.time()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO stored_responses (
                    response_id, response_json, conversation_history_json, instructions, accessed_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(response_id) DO UPDATE SET
                  response_json = excluded.response_json,
                  conversation_history_json = excluded.conversation_history_json,
                  instructions = excluded.instructions,
                  accessed_at = excluded.accessed_at
                """,
                (
                    response_id,
                    json.dumps(payload, sort_keys=True),
                    json.dumps(conversation_history, sort_keys=True),
                    instructions,
                    now,
                ),
            )

    def get_response(self, response_id: str) -> dict[str, Any] | None:
        now = time.time()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT response_json, conversation_history_json, instructions
                FROM stored_responses
                WHERE response_id = ?
                """,
                (response_id,),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                "UPDATE stored_responses SET accessed_at = ? WHERE response_id = ?",
                (now, response_id),
            )
        return {
            "response": _json_loads(row["response_json"], default={}),
            "conversation_history": _json_loads(row["conversation_history_json"], default=[]),
            "instructions": row["instructions"],
        }

    def delete_response(self, response_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM stored_responses WHERE response_id = ?",
                (response_id,),
            )
        return cursor.rowcount > 0

    def get_conversation_response(self, conversation: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT response_id FROM response_conversations WHERE conversation = ?",
                (conversation,),
            ).fetchone()
        return str(row["response_id"]) if row else None

    def set_conversation_response(self, conversation: str, response_id: str) -> None:
        now = time.time()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO response_conversations (conversation, response_id, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(conversation) DO UPDATE SET
                  response_id = excluded.response_id,
                  updated_at = excluded.updated_at
                """,
                (conversation, response_id, now),
            )

    def load_chat_session(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT messages_json FROM chat_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return []
        return _json_loads(row["messages_json"], default=[])

    def save_chat_session(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        now = time.time()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO chat_sessions (session_id, messages_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                  messages_json = excluded.messages_json,
                  updated_at = excluded.updated_at
                """,
                (session_id, json.dumps(messages, sort_keys=True), now),
            )

    def get_recent_events(self, limit: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT alias, provider_name, backend_model, success, retryable, is_fallback,
                       category, latency_ms, first_text_latency_ms, details_json, created_at
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
                "first_text_latency_ms": row["first_text_latency_ms"],
                "details": _json_loads(row["details_json"], default=None),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_route_metric_rows(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT alias, provider_name, backend_model, success, retryable, is_fallback, category, COUNT(*) AS count
                FROM route_events
                GROUP BY alias, provider_name, backend_model, success, retryable, is_fallback, category
                ORDER BY alias, provider_name, backend_model
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def get_refresh_metric_rows(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT provider_name, reason, success, category, COUNT(*) AS count
                FROM refresh_events
                GROUP BY provider_name, reason, success, category
                ORDER BY provider_name, reason
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def snapshot(self) -> dict[str, Any]:
        with self._connect() as connection:
            inventory_count = connection.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
            classification_count = connection.execute("SELECT COUNT(*) FROM classifications").fetchone()[0]
            ranking_count = connection.execute("SELECT COUNT(*) FROM model_rankings").fetchone()[0]
            event_count = connection.execute("SELECT COUNT(*) FROM route_events").fetchone()[0]
            refresh_event_count = connection.execute("SELECT COUNT(*) FROM refresh_events").fetchone()[0]
            stored_response_count = connection.execute("SELECT COUNT(*) FROM stored_responses").fetchone()[0]
            chat_session_count = connection.execute("SELECT COUNT(*) FROM chat_sessions").fetchone()[0]
        return {
            "db_path": str(self.db_path),
            "inventory_count": inventory_count,
            "classification_count": classification_count,
            "ranking_count": ranking_count,
            "event_count": event_count,
            "refresh_event_count": refresh_event_count,
            "stored_response_count": stored_response_count,
            "chat_session_count": chat_session_count,
            "model_state": list(self.get_model_state().values()),
            "provider_state": list(self.get_provider_state().values()),
            "rankings": list(self.get_rankings().values()),
            "overrides": self.get_overrides(),
        }

    def _fetch_model_row(self, connection: sqlite3.Connection, provider_name: str, backend_model: str) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT * FROM model_state WHERE provider_name = ? AND backend_model = ?",
            (provider_name, backend_model),
        ).fetchone()

    def _fetch_provider_row(self, connection: sqlite3.Connection, provider_name: str) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT * FROM provider_state WHERE provider_name = ?",
            (provider_name,),
        ).fetchone()

    def _success_payload(self, row: sqlite3.Row | None, now: float, *, latency_ms: float | None, first_text_latency_ms: float | None) -> dict[str, Any]:
        updated_at = float(row["updated_at"]) if row and row["updated_at"] is not None else now
        return {
            "success_count": int(row["success_count"]) + 1 if row else 1,
            "failure_count": int(row["failure_count"]) if row else 0,
            "retryable_failure_count": int(row["retryable_failure_count"]) if row and "retryable_failure_count" in row.keys() else 0,
            "request_success_count": int(row["request_success_count"]) + 1 if row and "request_success_count" in row.keys() else 1,
            "request_failure_count": int(row["request_failure_count"]) if row and "request_failure_count" in row.keys() else 0,
            "refresh_success_count": int(row["refresh_success_count"]) if row and "refresh_success_count" in row.keys() else 0,
            "refresh_failure_count": int(row["refresh_failure_count"]) if row and "refresh_failure_count" in row.keys() else 0,
            "recent_success": self._decayed_increment(row["recent_success"] if row and "recent_success" in row.keys() else 0, updated_at, now),
            "recent_failure": self._decay(row["recent_failure"] if row and "recent_failure" in row.keys() else 0, updated_at, now),
            "recent_rate_limit": self._decay(row["recent_rate_limit"] if row and "recent_rate_limit" in row.keys() else 0, updated_at, now),
            "recent_timeout": self._decay(row["recent_timeout"] if row and "recent_timeout" in row.keys() else 0, updated_at, now),
            "recent_auth_failure": self._decay(row["recent_auth_failure"] if row and "recent_auth_failure" in row.keys() else 0, updated_at, now),
            "recent_transport_failure": self._decay(row["recent_transport_failure"] if row and "recent_transport_failure" in row.keys() else 0, updated_at, now),
            "recent_server_error": self._decay(row["recent_server_error"] if row and "recent_server_error" in row.keys() else 0, updated_at, now),
            "recent_refresh_failure": self._decay(row["recent_refresh_failure"] if row and "recent_refresh_failure" in row.keys() else 0, updated_at, now),
            "recent_exhaustion": self._decay(row["recent_exhaustion"] if row and "recent_exhaustion" in row.keys() else 0, updated_at, now),
            "latency_avg_ms": self._ema(row["latency_avg_ms"] if row and "latency_avg_ms" in row.keys() else None, latency_ms),
            "first_text_latency_avg_ms": self._ema(row["first_text_latency_avg_ms"] if row and "first_text_latency_avg_ms" in row.keys() else None, first_text_latency_ms),
        }

    def _failure_payload(self, row: sqlite3.Row | None, now: float, *, category: str, retryable: bool, provider_level: bool = False) -> dict[str, Any]:
        updated_at = float(row["updated_at"]) if row and row["updated_at"] is not None else now
        payload = {
            "success_count": int(row["success_count"]) if row and "success_count" in row.keys() else 0,
            "failure_count": int(row["failure_count"]) + 1 if row else 1,
            "retryable_failure_count": (
                int(row["retryable_failure_count"]) + (1 if retryable else 0)
                if row and "retryable_failure_count" in row.keys()
                else (1 if retryable else 0)
            ),
            "request_success_count": int(row["request_success_count"]) if row and "request_success_count" in row.keys() else 0,
            "request_failure_count": int(row["request_failure_count"]) + 1 if row and "request_failure_count" in row.keys() else 1,
            "refresh_success_count": int(row["refresh_success_count"]) if row and "refresh_success_count" in row.keys() else 0,
            "refresh_failure_count": int(row["refresh_failure_count"]) if row and "refresh_failure_count" in row.keys() else 0,
            "recent_success": self._decay(row["recent_success"] if row and "recent_success" in row.keys() else 0, updated_at, now),
            "recent_failure": self._decayed_increment(row["recent_failure"] if row and "recent_failure" in row.keys() else 0, updated_at, now),
            "recent_rate_limit": self._decay_category(row, "recent_rate_limit", updated_at, now, category == "rate_limited"),
            "recent_timeout": self._decay_category(row, "recent_timeout", updated_at, now, category == "timeout"),
            "recent_auth_failure": self._decay_category(row, "recent_auth_failure", updated_at, now, category == "unauthorized"),
            "recent_transport_failure": self._decay_category(row, "recent_transport_failure", updated_at, now, category == "transport_error"),
            "recent_server_error": self._decay_category(row, "recent_server_error", updated_at, now, category == "server_error"),
            "recent_refresh_failure": self._decay(row["recent_refresh_failure"] if row and "recent_refresh_failure" in row.keys() else 0, updated_at, now),
            "recent_exhaustion": self._decay_category(
                row,
                "recent_exhaustion",
                updated_at,
                now,
                category in {"rate_limited", "insufficient_balance", "quota_exhausted"},
            ),
        }
        if provider_level and category == "unauthorized":
            payload["recent_auth_failure"] += 1.0
        return payload

    def _refresh_payload(self, row: sqlite3.Row | None, now: float, *, success: bool, category: str | None) -> dict[str, Any]:
        updated_at = float(row["updated_at"]) if row and row["updated_at"] is not None else now
        payload = {
            "success_count": int(row["success_count"]) if row else 0,
            "failure_count": int(row["failure_count"]) if row else 0,
            "request_success_count": int(row["request_success_count"]) if row and "request_success_count" in row.keys() else 0,
            "request_failure_count": int(row["request_failure_count"]) if row and "request_failure_count" in row.keys() else 0,
            "refresh_success_count": int(row["refresh_success_count"]) + (1 if success else 0) if row else (1 if success else 0),
            "refresh_failure_count": int(row["refresh_failure_count"]) + (0 if success else 1) if row else (0 if success else 1),
            "recent_success": self._decay(row["recent_success"] if row and "recent_success" in row.keys() else 0, updated_at, now),
            "recent_failure": self._decay(row["recent_failure"] if row and "recent_failure" in row.keys() else 0, updated_at, now),
            "recent_rate_limit": self._decay_category(row, "recent_rate_limit", updated_at, now, (not success and category == "rate_limited")),
            "recent_timeout": self._decay_category(row, "recent_timeout", updated_at, now, (not success and category == "timeout")),
            "recent_auth_failure": self._decay_category(row, "recent_auth_failure", updated_at, now, (not success and category == "unauthorized")),
            "recent_transport_failure": self._decay_category(row, "recent_transport_failure", updated_at, now, (not success and category == "transport_error")),
            "recent_server_error": self._decay_category(row, "recent_server_error", updated_at, now, (not success and category == "server_error")),
            "recent_refresh_failure": self._decayed_increment(
                row["recent_refresh_failure"] if row and "recent_refresh_failure" in row.keys() else 0,
                updated_at,
                now,
                amount=(0.0 if success else 1.0),
            ),
            "recent_exhaustion": self._decay_category(
                row,
                "recent_exhaustion",
                updated_at,
                now,
                (not success and category in {"rate_limited", "insufficient_balance", "quota_exhausted"}),
            ),
        }
        if success:
            payload["recent_refresh_failure"] = self._decay(row["recent_refresh_failure"] if row and "recent_refresh_failure" in row.keys() else 0, updated_at, now)
        return payload

    def _decay_category(self, row: sqlite3.Row | None, key: str, updated_at: float, now: float, triggered: bool) -> float:
        baseline = self._decay(row[key] if row and key in row.keys() else 0, updated_at, now)
        return baseline + 1.0 if triggered else baseline

    def _decayed_increment(self, value: float | None, updated_at: float, now: float, *, amount: float = 1.0) -> float:
        baseline = self._decay(value, updated_at, now)
        return baseline + amount

    def _decay(self, value: float | None, updated_at: float, now: float) -> float:
        baseline = float(value or 0.0)
        elapsed = max(0.0, now - updated_at)
        if baseline == 0.0 or elapsed == 0.0:
            return baseline
        return round(baseline * math.exp(-elapsed / self.rolling_window_seconds), 6)

    @staticmethod
    def _is_exhaustion_category(category: str) -> bool:
        return category in {"rate_limited", "insufficient_balance", "quota_exhausted"}

    def _next_exhaustion_streak(self, row: sqlite3.Row | None, now: float, *, category: str) -> int:
        if not self._is_exhaustion_category(category):
            return 0
        if row is None:
            return 1
        last_exhaustion_at = float(row["last_exhaustion_at"] or 0)
        previous_streak = int(row["exhaustion_streak"] or 0)
        if last_exhaustion_at and (now - last_exhaustion_at) <= max(self.rolling_window_seconds, 900.0):
            return previous_streak + 1
        return 1

    def _model_cooldown_seconds(self, category: str, *, row: sqlite3.Row | None) -> float:
        if self._is_exhaustion_category(category):
            ladder = self.exhaustion_cooldown_ladder_seconds
            streak = self._next_exhaustion_streak(row, time.time(), category=category)
            index = min(max(streak, 1), len(ladder)) - 1
            return ladder[index]
        return self._cooldown_seconds(category)

    @staticmethod
    def _ema(previous: float | None, current: float | None) -> float | None:
        if current is None:
            return previous
        if previous is None:
            return round(current, 2)
        return round((float(previous) * (1.0 - _LATENCY_ALPHA)) + (current * _LATENCY_ALPHA), 2)

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
            "quota_exhausted": 600.0,
            "insufficient_balance": 900.0,
        }.get(category, 30.0)
