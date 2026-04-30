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
    assert "has_extension_arg=true" in chrome
    assert 'if [ "$has_extension_arg" = true ]; then' in chrome
    assert "extension_binaries=(/opt/ghostship/cloakbrowser-cache/chromium-*/chrome)" in chrome
    assert 'exec "${extension_binaries[0]}" "${args[@]}"' in chrome
    assert "--disable-extensions)" not in chrome
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
    assert "chown -R 3000:3000 /opt/ghostship/extensions/ublock-origin-lite" in dockerfile
    assert "AGENT_BROWSER_ARGS=--no-sandbox" in dockerfile
    assert "DISPLAY=:99" in dockerfile
    assert "xvfb \\" in dockerfile
    assert "exec Xvfb \"$display\"" in read("packages/hermes-image/rootfs/etc/services.d/xvfb/run")
    assert "AGENT_BROWSER_PROFILE=/home/hermes/.local/state/cloakbrowser" not in dockerfile
    assert "ExtensionSettings" not in dockerfile
    assert "ghostship-agent-browser.json" not in dockerfile
    assert "ghostship-ubol-settings.json" not in dockerfile

    assert "manifest[\"key\"]" not in helper_path.read_text(encoding="utf-8")
    assert "UBOL_MANIFEST_KEY" not in helper_path.read_text(encoding="utf-8")
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


def test_managed_defaults_use_ollama_pro_and_opencode_go_fallback() -> None:
    init_home = read("packages/hermes-image/build/init_home.py")
    module = read("packages/hermes-image/nixos-module.nix")

    assert 'MANAGED_MODEL_PROVIDER = "custom:" + OLLAMA_PROVIDER_NAME' in init_home
    assert 'OLLAMA_PROVIDER_NAME = "ollama-pro"' in init_home
    assert "https://ollama.com/v1" in init_home
    assert "OLLAMA_API_KEY" in init_home
    assert "deepseek-v4-pro:cloud" in init_home
    assert "gemini-3.1-flash-lite-preview" in init_home

    for text in (module,):
        assert "custom:ollama-pro" in text
        assert "https://ollama.com/v1" in text
        assert "OLLAMA_API_KEY" in text
        assert "opencode-go" in text
        assert "deepseek-v4-pro:cloud" in text
        assert "deepseek-v4-pro" in text
        assert "gemini-3.1-flash-lite-preview" in text
        assert '"minimax-m2.7": {},' not in text

    assert 'provider = "opencode-go";' in module
    assert 'provider = ollamaProviderSlug;' in module
    assert 'name = "ghostship-" "router"' not in module
    assert '/opt/ghostship-' 'router' not in module
    assert '_GHOSTSHIP_' 'ROUTER_API_KEY' not in init_home


def test_opencode_go_replays_assistant_history_with_reasoning_content_placeholder() -> None:
    for path in (
        "packages/hermes-agent-wrapped/package.nix",
        "packages/hermes-image/build/prepare_upstream_hermes.py",
    ):
        text = read(path)
        assert 'self.provider == "opencode-go"' in text
        assert "ghostship_opencode_go_reasoning" in text
        assert "if ghostship_opencode_go_reasoning:" in text
        assert 'api_msg["reasoning_content"] = ""' in text


def test_fallback_logs_primary_failure_reason_when_switching_models() -> None:
    for path in (
        "packages/hermes-agent-wrapped/package.nix",
        "packages/hermes-image/build/prepare_upstream_hermes.py",
    ):
        text = read(path)
        assert "Primary model failure before fallback" in text
        assert "non_retryable_client_error" in text
        assert "max_retries_exhausted" in text
        assert "rate_limited" in text
        assert "self._summarize_api_error(error)" in text


def test_restored_api_docs_and_ghostship_wiki_are_baked() -> None:
    assert (ROOT / "docs/api/pyload-ng.md").exists()
    assert (ROOT / "docs/api/pyload-openapi.json").exists()
    assert (ROOT / "docs/api/prowlarr-openapi.json").exists()
    assert (ROOT / "docs/api/n8n-openapi.json").exists()

    dockerfile = read("packages/hermes-image/Dockerfile")
    prepare = read("packages/hermes-image/rootfs/etc/cont-init.d/10-ghostship-prepare")
    sync = read("packages/hermes-image/build/sync_ghostship_wiki.py")

    assert "COPY docs /src/docs" in dockerfile
    assert "cp -R /src/docs/ghostship-wiki/. /opt/ghostship/ghostship-wiki/" in dockerfile
    assert "cp -R /src/docs/api /opt/ghostship/ghostship-wiki/api/reference" in dockerfile
    assert "sync_ghostship_wiki.py" in dockerfile
    assert "GHOSTSHIP_WIKI_DEST=\"$HOME/ghostship-wiki\"" in prepare
    assert "MANIFEST_NAME = \".ghostship-managed-files\"" in sync
    assert "Agent-created files outside this list are preserved" in sync

    assert "FIRECRAWL_API_URL" in read("docs/ghostship-wiki/api/firecrawl.md")
    assert "PYLOAD_API_KEY" in read("docs/ghostship-wiki/api/service-env.md")
    assert "gws" in read("docs/ghostship-wiki/utilities.md")
    assert "reasoning_content" in read("docs/ghostship-wiki/models-and-reasoning.md")


def test_agent_browser_is_pinned_and_humanized_in_image() -> None:
    dockerfile = read("packages/hermes-image/Dockerfile")
    patcher = read("packages/hermes-image/build/prepare_agent_browser.py")
    prepare = read("packages/hermes-image/rootfs/etc/cont-init.d/10-ghostship-prepare")

    assert "ARG AGENT_BROWSER_REF=v0.26.0" in dockerfile
    assert "agent-browser@0.26.0" in dockerfile
    assert "prepare_agent_browser.py" in dockerfile
    assert ".#agent-browser-build-tools" in dockerfile
    assert "cargo build --release --manifest-path /tmp/agent-browser/cli/Cargo.toml" in dockerfile
    assert "install -m0755 /tmp/agent-browser/cli/target/release/agent-browser" in dockerfile
    assert "rm -rf \"$HOME/.local/lib/node_modules/agent-browser\"" in prepare
    assert "ln -sfn \"$HOME/.local/lib/node_modules/agent-browser/bin/$agent_browser_binary\" \"$HOME/.local/bin/agent-browser\"" in prepare

    for marker in (
        "GHOSTSHIP_HUMANIZED_AGENT_BROWSER",
        "ghostship_human_mouse_move",
        "ghostship_human_wheel",
        "ghostship_type_shift_symbol",
        "ghostship_human_type_text",
    ):
        assert marker in patcher


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
