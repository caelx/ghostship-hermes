from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path

import yaml


HOME = Path(os.environ.get("HOME", "/home/hermes"))
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(HOME / ".hermes")))
WORKSPACE = Path(os.environ.get("GHOSTSHIP_WORKSPACE_ROOT", "/workspace"))
ROUTER_URL = os.environ.get("GHOSTSHIP_ROUTER_URL", "http://127.0.0.1:8788/v1")
ROUTER_API_KEY_ENV = "_GHOSTSHIP_ROUTER_API_KEY"
AUXILIARY_MODEL = "gemini-3.1-flash-lite-preview"
AUXILIARY_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
AUXILIARY_API_KEY = "${GOOGLE_AI_STUDIO_API_KEY}"


def _env_flag(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


DISCORD_REACTIONS = _env_flag("DISCORD_REACTIONS", "false")
DISCORD_REQUIRE_MENTION = _env_flag("DISCORD_REQUIRE_MENTION", "false")
DISCORD_AUTO_THREAD = _env_flag("DISCORD_AUTO_THREAD", "false")


def _direct_gemini() -> dict[str, str]:
    return {
        "model": AUXILIARY_MODEL,
        "base_url": AUXILIARY_BASE_URL,
        "api_key": AUXILIARY_API_KEY,
    }


DEFAULT_CONFIG = {
    "model": {
        "provider": "openai-codex",
        "default": "gpt-5.4",
    },
    "memory": {
        "provider": "holographic",
        "memory_enabled": True,
        "user_profile_enabled": True,
        "nudge_interval": 10,
        "flush_min_turns": 6,
    },
    "plugins": {
        "hermes-memory-store": {
            "db_path": "$HERMES_HOME/memory_store.db",
            "auto_extract": False,
            "default_trust": 0.5,
        }
    },
    "fallback_model": {
        "provider": "opencode-go",
        "model": "minimax-m2.7",
    },
    "custom_providers": [
        {
            "name": "ghostship-router",
            "base_url": ROUTER_URL,
            "api_key_env": ROUTER_API_KEY_ENV,
            "api_mode": "chat_completions",
            "model": "agentic",
        }
    ],
    "timezone": "Pacific/Honolulu",
    "agent": {
        "max_turns": 110,
        "reasoning_effort": "medium",
        "verbose": False,
    },
    "compression": {
        "enabled": True,
        "threshold": 0.50,
        "target_ratio": 0.25,
        "protect_last_n": 20,
    },
    "session_reset": {
        "mode": "both",
        "idle_minutes": 240,
        "at_hour": 4,
    },
    "browser": {
        "cloud_provider": "local",
        "inactivity_timeout": 120,
        "command_timeout": 30,
        "record_sessions": False,
    },
    "approvals": {
        "mode": "off",
    },
    "security": {
        "redact_secrets": True,
        "tirith_enabled": True,
        "tirith_path": "tirith",
        "tirith_timeout": 5,
        "tirith_fail_open": True,
        "website_blocklist": {
            "enabled": False,
            "domains": [],
            "shared_files": [],
        },
    },
    "checkpoints": {
        "enabled": True,
        "max_snapshots": 50,
    },
    "streaming": {
        "enabled": True,
        "transport": "edit",
        "edit_interval": 0.3,
        "buffer_threshold": 40,
    },
    "stt": {
        "enabled": False,
    },
    "human_delay": {
        "mode": "off",
    },
    "auxiliary": {
        "vision": _direct_gemini(),
        "web_extract": _direct_gemini(),
        "approval": _direct_gemini(),
        "compression": _direct_gemini(),
        "session_search": _direct_gemini(),
        "skills_hub": _direct_gemini(),
        "mcp": _direct_gemini(),
        "flush_memories": _direct_gemini(),
    },
    "terminal": {
        "backend": "local",
        "cwd": str(WORKSPACE),
        "timeout": 180,
    },
    "discord": {
        "require_mention": DISCORD_REQUIRE_MENTION,
        "auto_thread": DISCORD_AUTO_THREAD,
        "reactions": DISCORD_REACTIONS,
    },
    "unauthorized_dm_behavior": "ignore",
    "display": {
        "compact": True,
        "interim_assistant_messages": False,
        "streaming": True,
        "tool_progress": "all",
        "background_process_notifications": "result",
        "bell_on_complete": False,
        "show_reasoning": True,
        "skin": "default",
    },
    "group_sessions_per_user": True,
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _is_router_primary_stub(config: object) -> bool:
    if not isinstance(config, dict):
        return False

    model = config.get("model")
    if not isinstance(model, dict):
        return False

    return (
        model.get("provider") == "auto"
        and model.get("default") == "agentic"
        and model.get("base_url") == ROUTER_URL
        and "fallback_model" not in config
        and "memory" not in config
        and "auxiliary" not in config
    )


def _merge_provider_defaults(providers: object, defaults: object) -> bool:
    if not isinstance(providers, list) or not isinstance(defaults, list):
        return False

    changed = False
    existing_by_name = {
        item.get("name"): item
        for item in providers
        if isinstance(item, dict) and item.get("name")
    }
    for default in defaults:
        if not isinstance(default, dict):
            continue
        name = default.get("name")
        if not name:
            continue
        existing = existing_by_name.get(name)
        if existing is None:
            providers.append(deepcopy(default))
            changed = True
            continue
        changed = _merge_missing_defaults(existing, default) or changed
    return changed


def _merge_missing_defaults(config: object, defaults: object) -> bool:
    if not isinstance(config, dict) or not isinstance(defaults, dict):
        return False

    changed = False
    for key, value in defaults.items():
        if key not in config:
            config[key] = deepcopy(value)
            changed = True
            continue

        current = config.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            changed = _merge_missing_defaults(current, value) or changed
        elif key == "custom_providers":
            changed = _merge_provider_defaults(current, value) or changed

    return changed


def _normalize_group_sessions(config: object) -> bool:
    if not isinstance(config, dict):
        return False

    discord = config.get("discord")
    if not isinstance(discord, dict) or "group_sessions_per_user" not in discord:
        return False

    changed = False
    if "group_sessions_per_user" not in config:
        config["group_sessions_per_user"] = discord["group_sessions_per_user"]
        changed = True
    del discord["group_sessions_per_user"]
    changed = True
    return changed


def _normalize_router_auth(config: object) -> bool:
    if not isinstance(config, dict):
        return False

    changed = False

    for key in ("model", "fallback_model"):
        section = config.get(key)
        if isinstance(section, dict) and section.get("base_url") == ROUTER_URL:
            if section.get("api_key_env") != ROUTER_API_KEY_ENV:
                section["api_key_env"] = ROUTER_API_KEY_ENV
                changed = True

    custom_providers = config.get("custom_providers")
    if isinstance(custom_providers, list):
        for provider in custom_providers:
            if not isinstance(provider, dict):
                continue
            if provider.get("base_url") != ROUTER_URL:
                continue
            if provider.get("api_key_env") != ROUTER_API_KEY_ENV:
                provider["api_key_env"] = ROUTER_API_KEY_ENV
                changed = True

    return changed


def _normalize_managed_model_contract(config: object) -> bool:
    if not isinstance(config, dict):
        return False

    changed = False

    model = config.get("model")
    if (
        isinstance(model, dict)
        and model.get("provider") == "opencode-go"
        and model.get("default") == "minimax-m2.7"
    ):
        model["provider"] = "openai-codex"
        model["default"] = "gpt-5.4"
        changed = True

    fallback_model = config.get("fallback_model")
    if (
        isinstance(fallback_model, dict)
        and fallback_model.get("provider") == "openai-codex"
        and fallback_model.get("model") == "gpt-5.4-mini"
    ):
        fallback_model["provider"] = "opencode-go"
        fallback_model["model"] = "minimax-m2.7"
        changed = True

    agent = config.get("agent")
    if isinstance(agent, dict) and agent.get("reasoning_effort") == "high":
        agent["reasoning_effort"] = "medium"
        changed = True

    return changed


def main() -> None:
    for relative in (
        ".config",
        ".cache",
        ".local/bin",
        ".local/share",
        ".local/state",
        ".npm",
        ".cargo",
        ".rustup",
        ".ssh",
        ".hermes",
    ):
        ensure_dir(HOME / relative)

    ensure_dir(WORKSPACE)

    config_path = HERMES_HOME / "config.yaml"
    if not config_path.exists():
        config_path.write_text(
            yaml.safe_dump(DEFAULT_CONFIG, sort_keys=False),
            encoding="utf-8",
        )
    else:
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        changed = False
        if not isinstance(loaded, dict):
            loaded = deepcopy(DEFAULT_CONFIG)
            changed = True
        elif _is_router_primary_stub(loaded):
            loaded = deepcopy(DEFAULT_CONFIG)
            changed = True
        changed = _merge_missing_defaults(loaded, DEFAULT_CONFIG) or changed
        changed = _normalize_group_sessions(loaded) or changed
        changed = _normalize_router_auth(loaded) or changed
        changed = _normalize_managed_model_contract(loaded) or changed
        if changed:
            config_path.write_text(
                yaml.safe_dump(loaded, sort_keys=False),
                encoding="utf-8",
            )

    env_path = HERMES_HOME / ".env"
    if not env_path.exists():
        env_path.write_text(
            "# Optional downstream runtime env file.\n"
            "# Container environment variables remain the primary contract.\n",
            encoding="utf-8",
        )

if __name__ == "__main__":
    main()
