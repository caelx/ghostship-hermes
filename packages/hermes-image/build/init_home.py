from __future__ import annotations

import os
from pathlib import Path

import yaml


HOME = Path(os.environ.get("HOME", "/home/hermes"))
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(HOME / ".hermes")))
WORKSPACE = Path(os.environ.get("GHOSTSHIP_WORKSPACE_ROOT", "/workspace"))
ROUTER_URL = os.environ.get("GHOSTSHIP_ROUTER_URL", "http://127.0.0.1:8788/v1")


DEFAULT_CONFIG = {
    "model": {
        "provider": "auto",
        "default": "agentic",
        "base_url": ROUTER_URL,
        "api_key_env": "OPENAI_API_KEY",
    },
    "custom_providers": [
        {
            "name": "ghostship-router",
            "base_url": ROUTER_URL,
            "api_key_env": "OPENAI_API_KEY",
            "api_mode": "chat_completions",
            "model": "agentic",
        }
    ],
    "terminal": {
        "backend": "local",
        "cwd": str(WORKSPACE),
    },
    "browser": {
        "cloud_provider": "local",
    },
    "discord": {
        "require_mention": True,
        "auto_thread": False,
        "reactions": True,
        "group_sessions_per_user": True,
    },
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


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

    env_path = HERMES_HOME / ".env"
    if not env_path.exists():
        env_path.write_text(
            "# Optional downstream runtime env file.\n"
            "# Container environment variables remain the primary contract.\n",
            encoding="utf-8",
        )

if __name__ == "__main__":
    main()
