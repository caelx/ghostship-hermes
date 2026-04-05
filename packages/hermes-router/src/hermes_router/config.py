from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar


def _default_state_dir() -> Path:
    xdg_state_home = os.environ.get("XDG_STATE_HOME")
    if xdg_state_home:
        return Path(xdg_state_home) / "ghostship-hermes" / "router"
    return Path.home() / ".local" / "state" / "ghostship-hermes" / "router"


def _parse_csv_env(name: str) -> tuple[str, ...]:
    raw = os.environ.get(name, "")
    values = [item.strip() for item in raw.split(",") if item.strip()]
    return tuple(values)


def _parse_bool_env(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_float_env(name: str, *, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return float(raw)


_NumericT = TypeVar("_NumericT", int, float)


def _parse_assignment_env(name: str, *, cast: type[_NumericT]) -> dict[str, _NumericT]:
    raw = os.environ.get(name, "")
    values: dict[str, _NumericT] = {}
    for item in raw.split(","):
        entry = item.strip()
        if not entry or "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue
        values[key] = cast(value)
    return values


@dataclass(frozen=True)
class AliasConfig:
    name: str
    description: str
    preferred_models: tuple[str, ...] = ()


@dataclass(frozen=True)
class RouterConfig:
    host: str
    port: int
    log_level: str
    default_timeout: float
    inventory_ttl_seconds: int
    refresh_interval_seconds: int
    alias_model_limit: int
    allow_direct_models: bool
    allow_models: tuple[str, ...]
    block_models: tuple[str, ...]
    state_dir: Path
    db_path: Path
    debug_event_limit: int
    rolling_window_seconds: float
    ranking_enabled: bool
    ranking_interval_seconds: int
    ranking_worker_model: str | None
    ranking_shortlist_size: int
    provider_cooldown_seconds: int
    provider_failure_threshold: float
    provider_rate_limit_threshold: float
    provider_timeout_threshold: float
    provider_exhaustion_threshold: float
    openrouter_api_key: str | None
    openrouter_base_url: str
    openrouter_http_referer: str | None
    openrouter_title: str | None
    opencode_api_key: str | None
    opencode_base_url: str
    assisted_bucket_model: str | None
    assisted_bucket_batch_size: int
    disabled_providers: tuple[str, ...]
    disabled_models: tuple[str, ...]
    provider_weight_overrides: dict[str, float]
    model_weight_overrides: dict[str, float]
    alias_pin_overrides: dict[str, tuple[str, ...]]
    aliases: tuple[AliasConfig, ...]

    @classmethod
    def from_env(cls) -> RouterConfig:
        state_dir = Path(os.environ.get("GHOSTSHIP_ROUTER_STATE_DIR", str(_default_state_dir())))
        db_path = Path(os.environ.get("GHOSTSHIP_ROUTER_DB_PATH", str(state_dir / "router.db")))
        return cls(
            host=os.environ.get("GHOSTSHIP_ROUTER_HOST", "127.0.0.1"),
            port=int(os.environ.get("GHOSTSHIP_ROUTER_PORT", "8788")),
            log_level=os.environ.get("GHOSTSHIP_ROUTER_LOG_LEVEL", "info"),
            default_timeout=float(os.environ.get("GHOSTSHIP_ROUTER_TIMEOUT", "30")),
            inventory_ttl_seconds=int(os.environ.get("GHOSTSHIP_ROUTER_INVENTORY_TTL", "300")),
            refresh_interval_seconds=int(os.environ.get("GHOSTSHIP_ROUTER_REFRESH_INTERVAL", "300")),
            alias_model_limit=int(os.environ.get("GHOSTSHIP_ROUTER_ALIAS_MODEL_LIMIT", "5")),
            allow_direct_models=_parse_bool_env("GHOSTSHIP_ROUTER_ALLOW_DIRECT_MODELS", default=False),
            allow_models=_parse_csv_env("GHOSTSHIP_ROUTER_ALLOW_MODELS"),
            block_models=_parse_csv_env("GHOSTSHIP_ROUTER_BLOCK_MODELS"),
            state_dir=state_dir,
            db_path=db_path,
            debug_event_limit=int(os.environ.get("GHOSTSHIP_ROUTER_DEBUG_EVENT_LIMIT", "50")),
            rolling_window_seconds=_parse_float_env("GHOSTSHIP_ROUTER_ROLLING_WINDOW_SECONDS", default=3600.0),
            ranking_enabled=_parse_bool_env("GHOSTSHIP_ROUTER_RANKING_ENABLED", default=True),
            ranking_interval_seconds=int(os.environ.get("GHOSTSHIP_ROUTER_RANKING_INTERVAL", "900")),
            ranking_worker_model=os.environ.get("GHOSTSHIP_ROUTER_RANKING_WORKER_MODEL"),
            ranking_shortlist_size=int(os.environ.get("GHOSTSHIP_ROUTER_RANKING_SHORTLIST_SIZE", "5")),
            provider_cooldown_seconds=int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_COOLDOWN_SECONDS", "300")),
            provider_failure_threshold=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_FAILURE_THRESHOLD", default=3.0),
            provider_rate_limit_threshold=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_RATE_LIMIT_THRESHOLD", default=2.5),
            provider_timeout_threshold=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_TIMEOUT_THRESHOLD", default=2.5),
            provider_exhaustion_threshold=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_EXHAUSTION_THRESHOLD", default=3.0),
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
            openrouter_base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_http_referer=os.environ.get("OPENROUTER_HTTP_REFERER"),
            openrouter_title=os.environ.get("OPENROUTER_TITLE"),
            opencode_api_key=os.environ.get("OPENCODE_API_KEY"),
            opencode_base_url=os.environ.get("OPENCODE_BASE_URL", "https://opencode.ai/zen/v1"),
            assisted_bucket_model=os.environ.get("GHOSTSHIP_ROUTER_ASSISTED_BUCKET_MODEL"),
            assisted_bucket_batch_size=int(os.environ.get("GHOSTSHIP_ROUTER_ASSISTED_BUCKET_BATCH_SIZE", "20")),
            disabled_providers=_parse_csv_env("GHOSTSHIP_ROUTER_DISABLED_PROVIDERS"),
            disabled_models=_parse_csv_env("GHOSTSHIP_ROUTER_DISABLED_MODELS"),
            provider_weight_overrides=_parse_assignment_env("GHOSTSHIP_ROUTER_PROVIDER_WEIGHT_OVERRIDES", cast=float),
            model_weight_overrides=_parse_assignment_env("GHOSTSHIP_ROUTER_MODEL_WEIGHT_OVERRIDES", cast=float),
            alias_pin_overrides={
                alias: _parse_csv_env(f"GHOSTSHIP_ROUTER_ALIAS_PIN_{alias.upper()}")
                for alias in ("lightweight", "coding", "heavyweight")
            },
            aliases=(
                AliasConfig(
                    name="lightweight",
                    description="Cheap, fast work such as summaries, extraction, and routing.",
                    preferred_models=_parse_csv_env("GHOSTSHIP_ROUTER_LIGHTWEIGHT_MODELS"),
                ),
                AliasConfig(
                    name="coding",
                    description="Code generation, editing, debugging, and technical reasoning.",
                    preferred_models=_parse_csv_env("GHOSTSHIP_ROUTER_CODING_MODELS"),
                ),
                AliasConfig(
                    name="heavyweight",
                    description="Harder reasoning workloads when lighter free models are not enough.",
                    preferred_models=_parse_csv_env("GHOSTSHIP_ROUTER_HEAVYWEIGHT_MODELS"),
                ),
            ),
        )

    def alias_map(self) -> dict[str, AliasConfig]:
        return {alias.name: alias for alias in self.aliases}
