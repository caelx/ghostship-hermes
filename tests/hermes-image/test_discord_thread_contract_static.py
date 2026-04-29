import json
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
    assert "AGENT_BROWSER_PROFILE=/home/hermes/.local/state/cloakbrowser" not in dockerfile
    assert 'map_user_data_dir' not in chrome
    assert 'args+=("--user-data-dir=$(map_user_data_dir "${1#--user-data-dir=}")")' not in chrome
    assert 'exec "$binary" "${stealth_args[@]}" "$@" "--user-data-dir=${profile_root}"' not in chrome


def test_cloakbrowser_managed_policy_installs_ublock_origin_lite() -> None:
    extension_id = "ddkjiahejlhfcafbddmgiahcphecmpfh"
    policy_paths = (
        "packages/hermes-image/rootfs/etc/opt/chrome/policies/managed/ghostship-agent-browser.json",
        "packages/hermes-image/rootfs/etc/chromium/policies/managed/ghostship-agent-browser.json",
    )
    integer_policies = {
        "DefaultNotificationsSetting": 2,
        "DefaultGeolocationSetting": 2,
        "DefaultPopupsSetting": 2,
        "DefaultClipboardSetting": 2,
        "DefaultSensorsSetting": 2,
        "DefaultAutomaticDownloadsSetting": 2,
        "DefaultSerialGuardSetting": 2,
        "DefaultWebUsbGuardSetting": 2,
        "DefaultWebBluetoothGuardSetting": 2,
        "DefaultWebHidGuardSetting": 2,
    }
    boolean_policies = {
        "AudioCaptureAllowed": False,
        "VideoCaptureAllowed": False,
        "ScreenCaptureAllowed": False,
        "AutoplayAllowed": False,
        "FullscreenAllowed": False,
        "EnableMediaRouter": False,
        "BackgroundModeEnabled": False,
        "PromotionalTabsEnabled": False,
        "PaymentMethodQueryEnabled": False,
    }

    policies = [json.loads(read(path)) for path in policy_paths]
    assert policies[0] == policies[1]

    policy = policies[0]
    extension = policy["ExtensionSettings"][extension_id]
    assert extension == {
        "installation_mode": "force_installed",
        "update_url": "https://clients2.google.com/service/update2/crx",
        "toolbar_pin": "force_pinned",
    }
    for key, value in integer_policies.items():
        assert policy[key] == value
    for key, value in boolean_policies.items():
        assert policy[key] is value

    ubol_policy = policy["3rdparty"]["extensions"][extension_id]
    assert ubol_policy["disableFirstRunPage"] is True
    assert ubol_policy["defaultFiltering"] == "complete"
    assert ubol_policy["showBlockedCount"] is True
    assert ubol_policy["strictBlockMode"] is True
    assert ubol_policy["disabledFeatures"] == ["develop"]
    assert ubol_policy["rulesets"] == [
        "-*",
        "+default",
        "+ublock-badware",
        "+urlhaus-full",
        "+adguard-spyware-url",
        "-block-lan",
        "-adguard-mobile",
        "+annoyances-ai",
        "+annoyances-cookies",
        "+annoyances-notifications",
        "+annoyances-others",
        "+annoyances-overlays",
        "+annoyances-social",
        "+annoyances-widgets",
    ]


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
