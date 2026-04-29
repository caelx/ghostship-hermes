import importlib.util
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


def test_upstream_patch_paths_keep_codex_pin_through_discord_thread_parent() -> None:
    for path in (
        "packages/hermes-agent-wrapped/package.nix",
        "packages/hermes-image/build/prepare_upstream_hermes.py",
    ):
        text = read(path)
        assert (
            'parent_chat_id = getattr(source, "chat_id_alt", None)' in text
            or 'parent_chat_id = getattr(source, \\"chat_id_alt\\", None)' in text
        )
        assert "chat_id == codex_channel or parent_chat_id == codex_channel" in text
        assert "chat_id_alt=parent_channel_id if is_thread else None" in text
        assert "chat_id_alt=_parent_id or None" in text
        assert "skip_thread = bool(channel_ids & no_thread_channels)" in text
        assert "openai-codex (`gpt-5.5`)" in text


def test_webhook_discord_delivery_defaults_to_webhook_channel() -> None:
    for path in (
        "packages/hermes-agent-wrapped/package.nix",
        "packages/hermes-image/build/prepare_upstream_hermes.py",
    ):
        text = read(path)
        assert 'route["deliver"] == "discord"' in text
        assert 'os.getenv("DISCORD_WEBHOOK_CHANNEL", "").strip()' in text
        assert 'route["deliver_extra"] = {"chat_id": deliver_chat_id}' in text


def test_custom_provider_api_key_env_is_patched_for_router_auth() -> None:
    for path in (
        "packages/hermes-agent-wrapped/package.nix",
        "packages/hermes-image/build/prepare_upstream_hermes.py",
    ):
        text = read(path)
        assert 'entry.get("api_key_env", "")' in text
        assert "api_key_env_vars=tuple(env_vars)" in text
        assert '"apiKeyEnv": "api_key_env"' in text
        assert 'entry.get("key_env") or entry.get("api_key_env")' in text
        assert 'custom_provider.get("api_key_env", "")' in text
        assert 'custom_entry.get("api_key_env", "")' in text


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


def test_chrome_wrapper_does_not_force_all_launches_into_one_profile() -> None:
    chrome = read("packages/hermes-image/rootfs/usr/local/bin/google-chrome")
    dockerfile = read("packages/hermes-image/Dockerfile")

    assert 'if [ "$has_user_data_dir" = false ]; then' in chrome
    assert 'args+=("--user-data-dir=${profile_root}")' in chrome
    assert 'if [ "$has_log_level" = false ]; then' in chrome
    assert 'args+=("--log-level=3")' in chrome
    assert 'args+=("--no-sandbox")' in chrome
    assert "--disable-extensions" not in chrome
    assert "GHOSTSHIP_CHROME_ALLOW_DISABLE_EXTENSIONS" not in chrome
    assert "AGENT_BROWSER_PROFILE=/home/hermes/.local/state/cloakbrowser" not in dockerfile
    assert 'map_user_data_dir' not in chrome
    assert 'args+=("--user-data-dir=$(map_user_data_dir "${1#--user-data-dir=}")")' not in chrome
    assert 'exec "$binary" "${stealth_args[@]}" "$@" "--user-data-dir=${profile_root}"' not in chrome


def test_ublock_origin_lite_is_loaded_by_agent_browser_extension_env() -> None:
    dockerfile = read("packages/hermes-image/Dockerfile")
    helper_path = ROOT / "packages/hermes-image/build/install_ubol.py"
    spec = importlib.util.spec_from_file_location("install_ubol", helper_path)
    assert spec is not None and spec.loader is not None
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)

    assert "ARG UBOL_REF=2026.426.1626" in dockerfile
    assert "AGENT_BROWSER_EXTENSIONS=/opt/ghostship/extensions/ublock-origin-lite" in dockerfile
    assert "AGENT_BROWSER_PROFILE=/home/hermes/.local/state/cloakbrowser" not in dockerfile
    assert "ExtensionSettings" not in dockerfile
    assert "ghostship-agent-browser.json" not in dockerfile
    assert "ghostship-ubol-settings.json" not in dockerfile

    assert helper.UBOL_EXTENSION_ID == "bfpkagngpehfhmefokecpdmakpacpfac"
    assert helper.UBOL_EXTENSION_ID == helper.extension_id_from_key(helper.UBOL_MANIFEST_KEY)
    assert helper.UBOL_DEFAULT_RULESETS == [
        "ublock-filters",
        "easylist",
        "easyprivacy",
        "pgl",
        "adguard-spyware-url",
        "block-lan",
        "ublock-badware",
        "urlhaus-full",
        "annoyances-ai",
        "annoyances-cookies",
        "annoyances-notifications",
        "annoyances-others",
        "annoyances-overlays",
        "annoyances-social",
        "annoyances-widgets",
    ]

    policy_files = list((ROOT / "packages/hermes-image/rootfs/etc").glob("**/policies/managed/*.json"))
    assert policy_files == []
    assert "ExtensionSettings" not in read("packages/hermes-image/rootfs/usr/local/bin/google-chrome")


def test_managed_router_defaults_use_flash_and_kimi() -> None:
    init_home = read("packages/hermes-image/build/init_home.py")
    module = read("packages/hermes-image/nixos-module.nix")
    router_config = read("packages/hermes-router/src/hermes_router/config.py")
    router_models = read("packages/hermes-router/src/hermes_router/models.py")

    for text in (init_home, module):
        assert "deepseek-v4-flash" in text
        assert "kimi-k2.6" in text
        assert '"deepseek-v4-pro": {},' not in text
        assert '"minimax-m2.7": {},' not in text

    assert 'primary_served_model=os.environ.get("GHOSTSHIP_ROUTER_PRIMARY_SERVED_MODEL", "deepseek-v4-flash")' in router_config
    assert 'fallback_served_model=os.environ.get("GHOSTSHIP_ROUTER_FALLBACK_SERVED_MODEL", "kimi-k2.6")' in router_config
    assert 'for alias in ("deepseek-v4-flash", "kimi-k2.6")' in router_config
    assert 'name="deepseek-v4-flash"' in router_config
    assert 'name="kimi-k2.6"' in router_config
    assert 'model: str = "deepseek-v4-flash"' in router_models


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
