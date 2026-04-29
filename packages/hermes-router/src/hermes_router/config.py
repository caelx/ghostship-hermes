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


def _first_env(*names: str, default: str | None = None) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value is not None:
            return value
    return default


def _env_token(value: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in value.upper())


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


def _parse_int_csv_env(name: str, *, default: tuple[int, ...]) -> tuple[int, ...]:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    values: list[int] = []
    for item in raw.split(","):
        entry = item.strip()
        if not entry:
            continue
        values.append(int(entry))
    return tuple(values) or default


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
class ProviderSeedPolicy:
    provider_name: str
    seeded_models: tuple[str, ...] = ()
    unused_models: tuple[str, ...] = ()
    daily_reset_hours: int = 24


@dataclass(frozen=True)
class RouterConfig:
    host: str
    port: int
    log_level: str
    api_key: str | None
    cors_origins: tuple[str, ...]
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
    provider_cooldown_seconds: int
    provider_failure_threshold: float
    provider_rate_limit_threshold: float
    provider_timeout_threshold: float
    provider_slow_first_text_threshold_ms: float
    provider_slow_total_threshold_ms: float
    provider_exhaustion_threshold: float
    exhaustion_cooldown_ladder_seconds: tuple[int, ...]
    provider_suspect_window_seconds: int
    provider_disable_seconds: int
    provider_probe_escalation_factor: float
    provider_max_disable_seconds: int
    provider_lane_limit: int
    provider_throttle_ladder_seconds: tuple[int, ...]
    free_attempt_timeout_seconds: float
    free_stream_first_byte_timeout_seconds: float
    free_total_budget_seconds: float
    fallback_timeout_seconds: float
    primary_served_model: str
    fallback_served_model: str
    opencode_go_large_tool_history_primary_timeout_seconds: float
    opencode_go_large_tool_history_fallback_timeout_seconds: float
    trace_routing: bool
    openrouter_min_request_spacing_seconds: float
    opencode_min_request_spacing_seconds: float
    nvidia_build_min_request_spacing_seconds: float
    openrouter_api_key: str | None
    openrouter_base_url: str
    openrouter_http_referer: str | None
    openrouter_title: str | None
    opencode_api_key: str | None
    opencode_base_url: str
    opencode_go_api_key: str | None
    opencode_go_base_url: str
    zenmux_api_key: str | None
    zenmux_base_url: str
    electron_hub_api_key: str | None
    electron_hub_base_url: str
    nvidia_build_api_key: str | None
    nvidia_build_base_url: str
    disabled_providers: tuple[str, ...]
    disabled_models: tuple[str, ...]
    provider_weight_overrides: dict[str, float]
    model_weight_overrides: dict[str, float]
    alias_pin_overrides: dict[str, tuple[str, ...]]
    provider_priority: tuple[str, ...]
    provider_rpm_limits: dict[str, int]
    provider_seed_policies: tuple[ProviderSeedPolicy, ...]
    aliases: tuple[AliasConfig, ...]

    @classmethod
    def from_env(cls) -> RouterConfig:
        state_dir = Path(os.environ.get("GHOSTSHIP_ROUTER_STATE_DIR", str(_default_state_dir())))
        db_path = Path(os.environ.get("GHOSTSHIP_ROUTER_DB_PATH", str(state_dir / "router.db")))
        return cls(
            host=_first_env("GHOSTSHIP_ROUTER_HOST", "API_SERVER_HOST", default="127.0.0.1") or "127.0.0.1",
            port=int(_first_env("GHOSTSHIP_ROUTER_PORT", "API_SERVER_PORT", default="8788") or "8788"),
            log_level=os.environ.get("GHOSTSHIP_ROUTER_LOG_LEVEL", "info"),
            api_key=os.environ.get("_GHOSTSHIP_ROUTER_API_KEY"),
            cors_origins=_parse_csv_env("GHOSTSHIP_ROUTER_CORS_ORIGINS") or _parse_csv_env("API_SERVER_CORS_ORIGINS"),
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
            provider_cooldown_seconds=int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_COOLDOWN_SECONDS", "300")),
            provider_failure_threshold=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_FAILURE_THRESHOLD", default=3.0),
            provider_rate_limit_threshold=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_RATE_LIMIT_THRESHOLD", default=2.5),
            provider_timeout_threshold=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_TIMEOUT_THRESHOLD", default=2.5),
            provider_slow_first_text_threshold_ms=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_SLOW_FIRST_TEXT_THRESHOLD_MS", default=15000.0),
            provider_slow_total_threshold_ms=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_SLOW_TOTAL_THRESHOLD_MS", default=30000.0),
            provider_exhaustion_threshold=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_EXHAUSTION_THRESHOLD", default=3.0),
            exhaustion_cooldown_ladder_seconds=_parse_int_csv_env(
                "GHOSTSHIP_ROUTER_EXHAUSTION_COOLDOWN_LADDER_SECONDS",
                default=(30, 60, 300, 600, 1200, 2400),
            ),
            provider_suspect_window_seconds=int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_SUSPECT_WINDOW_SECONDS", "120")),
            provider_disable_seconds=int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_DISABLE_SECONDS", "21600")),
            provider_probe_escalation_factor=_parse_float_env("GHOSTSHIP_ROUTER_PROVIDER_PROBE_ESCALATION_FACTOR", default=2.0),
            provider_max_disable_seconds=int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_MAX_DISABLE_SECONDS", "86400")),
            provider_lane_limit=int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_LANE_LIMIT", "3")),
            provider_throttle_ladder_seconds=_parse_int_csv_env(
                "GHOSTSHIP_ROUTER_PROVIDER_THROTTLE_LADDER_SECONDS",
                default=(15, 30, 60, 300, 900),
            ),
            free_attempt_timeout_seconds=_parse_float_env("GHOSTSHIP_ROUTER_FREE_ATTEMPT_TIMEOUT_SECONDS", default=10.0),
            free_stream_first_byte_timeout_seconds=_parse_float_env("GHOSTSHIP_ROUTER_FREE_STREAM_FIRST_BYTE_TIMEOUT_SECONDS", default=8.0),
            free_total_budget_seconds=_parse_float_env("GHOSTSHIP_ROUTER_FREE_TOTAL_BUDGET_SECONDS", default=24.0),
            fallback_timeout_seconds=_parse_float_env("GHOSTSHIP_ROUTER_FALLBACK_TIMEOUT_SECONDS", default=45.0),
            primary_served_model=os.environ.get("GHOSTSHIP_ROUTER_PRIMARY_SERVED_MODEL", "deepseek-v4-flash"),
            fallback_served_model=os.environ.get("GHOSTSHIP_ROUTER_FALLBACK_SERVED_MODEL", "kimi-k2.6"),
            opencode_go_large_tool_history_primary_timeout_seconds=_parse_float_env(
                "GHOSTSHIP_ROUTER_OPENCODE_GO_LARGE_TOOL_HISTORY_PRIMARY_TIMEOUT_SECONDS",
                default=25.0,
            ),
            opencode_go_large_tool_history_fallback_timeout_seconds=_parse_float_env(
                "GHOSTSHIP_ROUTER_OPENCODE_GO_LARGE_TOOL_HISTORY_FALLBACK_TIMEOUT_SECONDS",
                default=75.0,
            ),
            trace_routing=_parse_bool_env("GHOSTSHIP_ROUTER_TRACE_ROUTING", default=False),
            openrouter_min_request_spacing_seconds=_parse_float_env(
                "GHOSTSHIP_ROUTER_OPENROUTER_MIN_REQUEST_SPACING_SECONDS",
                default=3.0,
            ),
            opencode_min_request_spacing_seconds=_parse_float_env(
                "GHOSTSHIP_ROUTER_OPENCODE_MIN_REQUEST_SPACING_SECONDS",
                default=2.0,
            ),
            nvidia_build_min_request_spacing_seconds=_parse_float_env(
                "GHOSTSHIP_ROUTER_NVIDIA_BUILD_MIN_REQUEST_SPACING_SECONDS",
                default=1.0,
            ),
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY"),
            openrouter_base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            openrouter_http_referer=os.environ.get("OPENROUTER_HTTP_REFERER"),
            openrouter_title=os.environ.get("OPENROUTER_TITLE"),
            opencode_api_key=_first_env("OPENCODE_ZEN_API_KEY", "OPENCODE_API_KEY"),
            opencode_base_url=_first_env("OPENCODE_ZEN_BASE_URL", "OPENCODE_BASE_URL", default="https://opencode.ai/zen/v1") or "https://opencode.ai/zen/v1",
            opencode_go_api_key=os.environ.get("OPENCODE_GO_API_KEY"),
            opencode_go_base_url=os.environ.get("OPENCODE_GO_BASE_URL", "https://opencode.ai/zen/go/v1"),
            zenmux_api_key=os.environ.get("ZENMUX_API_KEY"),
            zenmux_base_url=os.environ.get("ZENMUX_BASE_URL", "https://zenmux.ai/api/v1"),
            electron_hub_api_key=os.environ.get("ELECTRON_HUB_API_KEY"),
            electron_hub_base_url=os.environ.get("ELECTRON_HUB_BASE_URL", "https://api.electronhub.ai/v1"),
            nvidia_build_api_key=_first_env("NVIDIA_BUILD_API_KEY", "NVIDIA_API_KEY"),
            nvidia_build_base_url=os.environ.get("NVIDIA_BUILD_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            disabled_providers=_parse_csv_env("GHOSTSHIP_ROUTER_DISABLED_PROVIDERS"),
            disabled_models=_parse_csv_env("GHOSTSHIP_ROUTER_DISABLED_MODELS"),
            provider_weight_overrides=_parse_assignment_env("GHOSTSHIP_ROUTER_PROVIDER_WEIGHT_OVERRIDES", cast=float),
            model_weight_overrides=_parse_assignment_env("GHOSTSHIP_ROUTER_MODEL_WEIGHT_OVERRIDES", cast=float),
            alias_pin_overrides={
                alias: _parse_csv_env(f"GHOSTSHIP_ROUTER_ALIAS_PIN_{_env_token(alias)}")
                for alias in ("deepseek-v4-flash", "kimi-k2.6")
            },
            provider_priority=(
                "nvidia-build",
                "opencode-zen",
                "zenmux",
                "electron-hub",
                "openrouter",
                "opencode-go",
            ),
            provider_rpm_limits={
                "nvidia-build": int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_RPM_NVIDIA_BUILD", "30")),
                "opencode-zen": int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_RPM_OPENCODE_ZEN", "30")),
                "zenmux": int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_RPM_ZENMUX", "10")),
                "electron-hub": int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_RPM_ELECTRON_HUB", "5")),
                "openrouter": int(os.environ.get("GHOSTSHIP_ROUTER_PROVIDER_RPM_OPENROUTER", "20")),
            },
            provider_seed_policies=(
                ProviderSeedPolicy(
                    provider_name="nvidia-build",
                    unused_models=_parse_csv_env("GHOSTSHIP_ROUTER_NVIDIA_BUILD_UNUSED_MODELS"),
                ),
                ProviderSeedPolicy(
                    provider_name="opencode-zen",
                    unused_models=_parse_csv_env("GHOSTSHIP_ROUTER_OPENCODE_ZEN_UNUSED_MODELS"),
                ),
                ProviderSeedPolicy(
                    provider_name="openrouter",
                    unused_models=_parse_csv_env("GHOSTSHIP_ROUTER_OPENROUTER_UNUSED_MODELS"),
                ),
                ProviderSeedPolicy(
                    provider_name="zenmux",
                    unused_models=_parse_csv_env("GHOSTSHIP_ROUTER_ZENMUX_UNUSED_MODELS"),
                ),
                ProviderSeedPolicy(
                    provider_name="electron-hub",
                    unused_models=_parse_csv_env("GHOSTSHIP_ROUTER_ELECTRON_HUB_UNUSED_MODELS"),
                ),
                ProviderSeedPolicy(
                    provider_name="opencode-go",
                    unused_models=_parse_csv_env("GHOSTSHIP_ROUTER_OPENCODE_GO_UNUSED_MODELS"),
                ),
            ),
            aliases=(
                AliasConfig(
                    name="deepseek-v4-flash",
                    description="DeepSeek V4 Flash through discovered free equivalents first, then OpenCode Go.",
                    preferred_models=_parse_csv_env("GHOSTSHIP_ROUTER_DEEPSEEK_V4_FLASH_MODELS"),
                ),
                AliasConfig(
                    name="kimi-k2.6",
                    description="Kimi K2.6 through discovered free equivalents first, then OpenCode Go.",
                    preferred_models=_parse_csv_env("GHOSTSHIP_ROUTER_KIMI_K2_6_MODELS"),
                ),
            ),
        )

    def alias_map(self) -> dict[str, AliasConfig]:
        return {alias.name: alias for alias in self.aliases}

    def provider_seed_map(self) -> dict[str, ProviderSeedPolicy]:
        return {policy.provider_name: policy for policy in self.provider_seed_policies}
