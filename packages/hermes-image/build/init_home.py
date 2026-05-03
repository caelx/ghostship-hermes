from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path

import yaml


HOME = Path(os.environ.get("HOME", "/home/hermes"))
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(HOME / ".hermes")))
WORKSPACE = Path(os.environ.get("GHOSTSHIP_WORKSPACE_ROOT", "/workspace"))
LEGACY_ROUTER_NAME = "ghostship-" + "router"
LEGACY_ROUTER_PROVIDER = "custom:" + LEGACY_ROUTER_NAME
LEGACY_ROUTER_URL = "http://127.0.0.1:" + "8788" + "/v1"
OLLAMA_PROVIDER_NAME = "ollama-pro"
MANAGED_MODEL_PROVIDER = "custom:" + OLLAMA_PROVIDER_NAME
PRIMARY_MODEL = "deepseek-v4-pro:cloud"
FALLBACK_MODEL_PROVIDER = "opencode-go"
FALLBACK_MODEL = "deepseek-v4-pro"
AUXILIARY_MODEL = "gemini-2.5-flash-lite"
CURATOR_AUXILIARY_MODEL = "gemini-3.1-flash-lite-preview"
AUXILIARY_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
AUXILIARY_API_KEY = "${GOOGLE_AI_STUDIO_API_KEY}"
OLLAMA_BASE_URL = "https://ollama.com/v1"
OLLAMA_API_KEY_ENV = "OLLAMA_API_KEY"


def _env_flag(name: str, default: str) -> bool:
    return os.environ.get(name, default).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


DISCORD_REACTIONS = _env_flag("DISCORD_REACTIONS", "false")
DISCORD_REQUIRE_MENTION = _env_flag("DISCORD_REQUIRE_MENTION", "false")
DISCORD_AUTO_THREAD = _env_flag("DISCORD_AUTO_THREAD", "true")


def _direct_gemini() -> dict[str, str]:
    return {
        "model": AUXILIARY_MODEL,
        "base_url": AUXILIARY_BASE_URL,
        "api_key": AUXILIARY_API_KEY,
    }


def _curator_gemini() -> dict[str, str]:
    return {
        "model": CURATOR_AUXILIARY_MODEL,
        "base_url": AUXILIARY_BASE_URL,
        "api_key": AUXILIARY_API_KEY,
    }


DEFAULT_CONFIG = {
    "model": {
        "provider": MANAGED_MODEL_PROVIDER,
        "default": PRIMARY_MODEL,
    },
    "custom_providers": [
        {
            "name": OLLAMA_PROVIDER_NAME,
            "base_url": OLLAMA_BASE_URL,
            "api_key_env": OLLAMA_API_KEY_ENV,
            "model": PRIMARY_MODEL,
        },
    ],
    "web": {
        "backend": "firecrawl",
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
        "provider": FALLBACK_MODEL_PROVIDER,
        "model": FALLBACK_MODEL,
    },
    "timezone": "Pacific/Honolulu",
    "agent": {
        "max_turns": 500,
        "reasoning_effort": "xhigh",
        "verbose": False,
    },
    "compression": {
        "enabled": True,
        "threshold": 0.50,
        "target_ratio": 0.25,
        "protect_last_n": 20,
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
        "vision": _curator_gemini(),
        "web_extract": _direct_gemini(),
        "approval": _curator_gemini(),
        "compression": _direct_gemini(),
        "session_search": _direct_gemini(),
        "skills_hub": _direct_gemini(),
        "mcp": _direct_gemini(),
        "flush_memories": _direct_gemini(),
        "curator": _curator_gemini(),
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
        and model.get("base_url") == LEGACY_ROUTER_URL
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


def _remove_legacy_router_provider(config: object) -> bool:
    if not isinstance(config, dict):
        return False

    changed = False

    for key in ("model", "fallback_model"):
        section = config.get(key)
        if isinstance(section, dict) and section.get("base_url") == LEGACY_ROUTER_URL:
            for obsolete_key in ("base_url", "api_key_env"):
                if obsolete_key in section:
                    del section[obsolete_key]
                    changed = True

    custom_providers = config.get("custom_providers")
    if isinstance(custom_providers, list):
        filtered = [
            provider
            for provider in custom_providers
            if not (
                isinstance(provider, dict)
                and (provider.get("name") == LEGACY_ROUTER_NAME or provider.get("base_url") == LEGACY_ROUTER_URL)
            )
        ]
        if filtered != custom_providers:
            if filtered:
                config["custom_providers"] = filtered
                changed = True
            else:
                del config["custom_providers"]
                changed = True

    return changed


def _normalize_ollama_provider(config: object) -> bool:
    if not isinstance(config, dict):
        return False

    defaults = DEFAULT_CONFIG["custom_providers"][0]
    providers = config.get("custom_providers")
    if not isinstance(providers, list):
        config["custom_providers"] = [deepcopy(defaults)]
        return True

    changed = False
    for provider in providers:
        if isinstance(provider, dict) and provider.get("name") == OLLAMA_PROVIDER_NAME:
            for key, value in defaults.items():
                if provider.get(key) != value:
                    provider[key] = value
                    changed = True
            return changed

    providers.append(deepcopy(defaults))
    return True


def _normalize_auxiliary_model_contract(config: object) -> bool:
    if not isinstance(config, dict):
        return False

    auxiliary = config.get("auxiliary")
    if not isinstance(auxiliary, dict):
        config["auxiliary"] = deepcopy(DEFAULT_CONFIG["auxiliary"])
        return True

    changed = False
    for key in ("vision", "approval", "curator"):
        wanted = _curator_gemini()
        current = auxiliary.get(key)
        if current != wanted:
            auxiliary[key] = wanted
            changed = True
    return changed


def _normalize_managed_model_contract(config: object) -> bool:
    if not isinstance(config, dict):
        return False

    changed = False

    model = config.get("model")
    if (
        isinstance(model, dict)
        and model.get("provider") in {"opencode-go", "openai-codex", LEGACY_ROUTER_PROVIDER, MANAGED_MODEL_PROVIDER}
        and model.get("default") in {
            PRIMARY_MODEL,
            "deepseek-v4-pro",
            "deepseek-v4-flash",
            "minimax-m2.7",
            "gpt-5.4",
            "gpt-5.5",
        }
    ):
        model["provider"] = MANAGED_MODEL_PROVIDER
        model["default"] = PRIMARY_MODEL
        changed = True
    elif isinstance(model, dict) and model.get("provider") == "custom" and model.get("default") in {"agentic", "coding"}:
        model["provider"] = MANAGED_MODEL_PROVIDER
        model["default"] = PRIMARY_MODEL
        changed = True

    fallback_model = config.get("fallback_model")
    if (
        isinstance(fallback_model, dict)
        and fallback_model.get("provider") in {"openai-codex", "opencode-go", "custom", LEGACY_ROUTER_PROVIDER}
        and fallback_model.get("model") in {
            FALLBACK_MODEL,
            "gpt-5.4-mini",
            "minimax-m2.7",
            "kimi-k2.6",
            "agentic",
            "coding",
        }
    ):
        fallback_model["provider"] = FALLBACK_MODEL_PROVIDER
        fallback_model["model"] = FALLBACK_MODEL
        changed = True

    agent = config.get("agent")
    if isinstance(agent, dict) and agent.get("reasoning_effort") != "xhigh":
        agent["reasoning_effort"] = "xhigh"
        changed = True
    if isinstance(agent, dict) and agent.get("max_turns") != 500:
        agent["max_turns"] = 500
        changed = True

    web = config.get("web")
    if not isinstance(web, dict):
        config["web"] = {"backend": "firecrawl"}
        changed = True
    elif web.get("backend") != "firecrawl":
        web["backend"] = "firecrawl"
        changed = True

    return changed


def _remove_auto_session_reset(config: object) -> bool:
    if not isinstance(config, dict) or "session_reset" not in config:
        return False

    del config["session_reset"]
    return True


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
        changed = _remove_legacy_router_provider(loaded) or changed
        changed = _normalize_ollama_provider(loaded) or changed
        changed = _normalize_auxiliary_model_contract(loaded) or changed
        changed = _normalize_managed_model_contract(loaded) or changed
        changed = _remove_auto_session_reset(loaded) or changed
        if changed:
            config_path.write_text(
                yaml.safe_dump(loaded, sort_keys=False),
                encoding="utf-8",
            )

if __name__ == "__main__":
    main()
