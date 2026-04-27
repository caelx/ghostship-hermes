import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_managed_discord_defaults_are_threaded_and_daily() -> None:
    assert "DISCORD_AUTO_THREAD=true" in read("packages/hermes-image/Dockerfile")

    init_home = read("packages/hermes-image/build/init_home.py")
    assert '_env_flag("DISCORD_AUTO_THREAD", "true")' in init_home
    assert '"session_reset": {\n        "mode": "daily",\n        "idle_minutes": 240,\n        "at_hour": 4,' in init_home

    module = read("packages/hermes-image/nixos-module.nix")
    assert 'mode = "daily";' in module
    assert "at_hour = 4;" in module
    assert "auto_thread = true;" in module
    assert "DISCORD_WEBHOOK_CHANNEL" in module


def test_managed_model_contract_uses_opencode_deepseek_primary() -> None:
    init_home = read("packages/hermes-image/build/init_home.py")
    assert '"provider": "opencode-go"' in init_home
    assert '"default": "deepseek-v4-pro"' in init_home
    assert '"model": "minimax-m2.7"' in init_home

    module = read("packages/hermes-image/nixos-module.nix")
    assert 'provider = "opencode-go";' in module
    assert 'default = "deepseek-v4-pro";' in module
    assert 'model = "minimax-m2.7";' in module


def test_managed_agent_max_iterations_defaults_to_500() -> None:
    assert '"max_turns": 500' in read("packages/hermes-image/build/init_home.py")
    assert "max_turns = 500;" in read("packages/hermes-image/nixos-module.nix")


def test_upstream_patch_paths_keep_router_pin_through_discord_thread_parent() -> None:
    for path in (
        "packages/hermes-agent-wrapped/package.nix",
        "packages/hermes-image/build/prepare_upstream_hermes.py",
    ):
        text = read(path)
        assert (
            'parent_chat_id = getattr(source, "chat_id_alt", None)' in text
            or 'parent_chat_id = getattr(source, \\"chat_id_alt\\", None)' in text
        )
        assert "chat_id == router_channel or parent_chat_id == router_channel" in text
        assert "chat_id_alt=parent_channel_id if is_thread else None" in text
        assert "chat_id_alt=_parent_id or None" in text
        assert "skip_thread = bool(channel_ids & no_thread_channels)" in text
        assert "ghostship-router (`agentic`)" in text


def test_webhook_discord_delivery_defaults_to_webhook_channel() -> None:
    for path in (
        "packages/hermes-agent-wrapped/package.nix",
        "packages/hermes-image/build/prepare_upstream_hermes.py",
    ):
        text = read(path)
        assert 'route["deliver"] == "discord"' in text
        assert 'os.getenv("DISCORD_WEBHOOK_CHANNEL", "").strip()' in text
        assert 'route["deliver_extra"] = {"chat_id": deliver_chat_id}' in text


def test_closed_discord_thread_retirement_is_patched_into_gateway() -> None:
    for path in (
        "packages/hermes-agent-wrapped/package.nix",
        "packages/hermes-image/build/prepare_upstream_hermes.py",
    ):
        text = read(path)
        assert "_ghostship_retire_closed_discord_threads" in text
        assert 'now.hour < 5' in text
        assert 'getattr(thread, "archived", False)' in text
        assert 'getattr(thread, "locked", False)' in text
        assert "self._session_model_overrides.pop(key, None)" in text
        assert "self.session_store._entries.pop(key, None)" in text


def test_downstream_discord_snowflake_ids_are_not_committed() -> None:
    tracked_paths = [
        "README.md",
        "docs/runtime-env.md",
        "docs/workstation-image.md",
        "AGENTS.md",
        "CHANGELOG.md",
        "packages/hermes-image/Dockerfile",
        "packages/hermes-image/build/init_home.py",
        "packages/hermes-image/nixos-module.nix",
        "packages/hermes-image/rootfs/etc/ghostship-hermes-env.sh",
        "packages/hermes-agent-wrapped/package.nix",
        "packages/hermes-image/build/prepare_upstream_hermes.py",
        "tests/hermes-image/single-agent-dashboard.sh",
    ]
    combined = "\n".join(read(path) for path in tracked_paths)
    assert re.search(r"\b[1-9][0-9]{16,20}\b", combined) is None
