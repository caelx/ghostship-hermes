{ lib, stdenvNoCC, makeBinaryWrapper, hermesAgentPackage, agentBrowserPackage }:
stdenvNoCC.mkDerivation {
  pname = "hermes-agent-wrapped";
  version = "0.1.0";
  dontUnpack = true;
  nativeBuildInputs = [ makeBinaryWrapper ];
  installPhase = ''
    wrapper_bin="${hermesAgentPackage}/bin/hermes"
    hermes_env_bin=$(sed -n 's|^exec "\([^"]*/bin/hermes\)".*|\1|p' "$wrapper_bin")
    if [ -z "$hermes_env_bin" ]; then
      echo "failed to locate upstream hermes env bin from $wrapper_bin" >&2
      exit 1
    fi
    hermes_env_root=$(dirname "$(dirname "$hermes_env_bin")")
    skills_dir="${hermesAgentPackage}/share/hermes-agent/skills"

    mkdir -p "$out"
    cp -aL "$hermes_env_root"/. "$out"/
    chmod -R u+w "$out"
    rm -rf "$out/lib64"
    patchShebangs "$out/bin"

    site_packages="$out/lib/python3.11/site-packages"
    if [ ! -d "$site_packages" ]; then
      echo "failed to locate site-packages in wrapped Hermes env output" >&2
      exit 1
    fi

    mkdir -p "$site_packages/node_modules"
    ln -s ${agentBrowserPackage}/share/agent-browser/package "$site_packages/node_modules/agent-browser"

    SITE_PACKAGES="$site_packages" "$out/bin/python3.11" - <<'PATCH'
from pathlib import Path
import os

site = Path(os.environ["SITE_PACKAGES"])
tools = site / "hermes_cli" / "tools_config.py"
gateway_cli = site / "hermes_cli" / "gateway.py"
gateway_status = site / "gateway" / "status.py"
gateway_run = site / "gateway" / "run.py"
model_switch = site / "hermes_cli" / "model_switch.py"
providers = site / "hermes_cli" / "providers.py"

tools_text = tools.read_text()
tools_text = tools_text.replace(
    "        if not node_modules.exists() and shutil.which(\"npm\"):",
    "        if not (shutil.which(\"agent-browser\") or node_modules.exists()) and shutil.which(\"npm\"):",
    1,
)
tools_text = tools_text.replace(
    "        elif not node_modules.exists():",
    "        elif not (shutil.which(\"agent-browser\") or node_modules.exists()):",
    1,
)
tools.write_text(tools_text)

gateway_cli_text = gateway_cli.read_text()
gateway_cli_text = gateway_cli_text.replace(
    'def get_systemd_unit_path(system: bool = False) -> Path:\n    name = get_service_name()\n    if system:\n        return Path("/etc/systemd/system") / f"{name}.service"\n    return Path.home() / ".config" / "systemd" / "user" / f"{name}.service"\n',
    'def _managed_user_systemd_unit_path() -> Path:\n    return Path("/etc/systemd/user") / f"{get_service_name()}.service"\n\n\ndef get_systemd_unit_path(system: bool = False) -> Path:\n    name = get_service_name()\n    if system:\n        return Path("/etc/systemd/system") / f"{name}.service"\n    user_unit = Path.home() / ".config" / "systemd" / "user" / f"{name}.service"\n    managed_unit = _managed_user_systemd_unit_path()\n    if user_unit.exists():\n        return user_unit\n    if managed_unit.exists():\n        return managed_unit\n    return user_unit\n',
    1,
)
if "def _managed_user_systemd_unit_path() -> Path:" not in gateway_cli_text:
    raise RuntimeError("failed to teach Hermes gateway about managed /etc/systemd/user units")
gateway_cli_text = gateway_cli_text.replace(
    'def systemd_unit_is_current(system: bool = False) -> bool:\n    unit_path = get_systemd_unit_path(system=system)\n    if not unit_path.exists():\n        return False\n\n    installed = unit_path.read_text(encoding="utf-8")\n    expected_user = _read_systemd_user_from_unit(unit_path) if system else None\n    expected = generate_systemd_unit(system=system, run_as_user=expected_user)\n    return _normalize_service_definition(installed) == _normalize_service_definition(expected)\n',
    'def systemd_unit_is_current(system: bool = False) -> bool:\n    unit_path = get_systemd_unit_path(system=system)\n    if not unit_path.exists():\n        return False\n\n    if not system:\n        managed_unit = _managed_user_systemd_unit_path()\n        try:\n            if managed_unit.exists() and unit_path.resolve() == managed_unit.resolve():\n                return True\n        except OSError:\n            pass\n\n    installed = unit_path.read_text(encoding="utf-8")\n    expected_user = _read_systemd_user_from_unit(unit_path) if system else None\n    expected = generate_systemd_unit(system=system, run_as_user=expected_user)\n    return _normalize_service_definition(installed) == _normalize_service_definition(expected)\n',
    1,
)
if 'managed_unit.exists() and unit_path.resolve() == managed_unit.resolve()' not in gateway_cli_text:
    raise RuntimeError("failed to mark managed user-unit symlinks current for Hermes gateway status")
gateway_cli.write_text(gateway_cli_text)

status_text = gateway_status.read_text()
status_text = status_text.replace(
    '        "gateway/run.py",\n    )',
    '        "gateway/run.py",\n        ".hermes-wrapped gateway",\n        "gateway run --replace",\n        "gateway run",\n    )',
    2,
)
if status_text.count('".hermes-wrapped gateway"') != 2:
    raise RuntimeError("failed to expand gateway process signatures in gateway.status")
gateway_status.write_text(status_text)

gateway_run_text = gateway_run.read_text()
gateway_run_text = gateway_run_text.replace(
    '                user_provs = cfg.get("providers")\n',
    '                user_provs = cfg.get("providers") or custom_provs\n',
    1,
)
if 'cfg.get("providers") or custom_provs' not in gateway_run_text:
    gateway_run_text = gateway_run_text.replace(
    '                user_provs = cfg.get("providers")\n',
    '                user_provs = cfg.get("providers") or cfg.get("custom_providers")\n',
    1,
)
if 'cfg.get("providers") or custom_provs' not in gateway_run_text and 'cfg.get("providers") or cfg.get("custom_providers")' not in gateway_run_text:
    raise RuntimeError("failed to teach Discord model picker to use custom_providers")
gateway_run_text = gateway_run_text.replace(
    '                    _cur_api_key = current_api_key\n\n                    async def _on_model_selected(\n',
    '                    _cur_api_key = current_api_key\n                    _user_provs = user_provs\n\n                    async def _on_model_selected(\n',
    1,
)
gateway_run_text = gateway_run_text.replace(
    '                            explicit_provider=provider_slug,\n',
    '                            explicit_provider=provider_slug,\n                            user_providers=_user_provs,\n',
    1,
)
if 'user_providers=_user_provs' not in gateway_run_text:
    raise RuntimeError("failed to pass custom_providers into Discord model switches")

turn_route_marker = """    def _resolve_turn_agent_config(self, user_message: str, model: str, runtime_kwargs: dict) -> dict:
        from agent.smart_model_routing import resolve_turn_route
        from hermes_cli.models import resolve_fast_mode_overrides

        primary = {
            "model": model,
            "api_key": runtime_kwargs.get("api_key"),
            "base_url": runtime_kwargs.get("base_url"),
            "provider": runtime_kwargs.get("provider"),
            "api_mode": runtime_kwargs.get("api_mode"),
            "command": runtime_kwargs.get("command"),
            "args": list(runtime_kwargs.get("args") or []),
            "credential_pool": runtime_kwargs.get("credential_pool"),
        }
        route = resolve_turn_route(user_message, getattr(self, "_smart_model_routing", {}), primary)

        service_tier = getattr(self, "_service_tier", None)
        if not service_tier:
            route["request_overrides"] = None
            return route

        try:
            overrides = resolve_fast_mode_overrides(route.get("model"))
        except Exception:
            overrides = None
        route["request_overrides"] = overrides
        return route
"""
turn_route_replacement = """    @staticmethod
    def _ghostship_is_discord_router_channel(source) -> bool:
        if source is None:
            return False
        platform = getattr(source, "platform", None)
        platform_value = getattr(platform, "value", platform)
        if platform_value != "discord":
            return False
        if getattr(source, "chat_type", None) in {"dm", "thread"}:
            return False
        return getattr(source, "chat_id", None) == os.getenv("GHOSTSHIP_ROUTER_CHANNEL", "").strip()

    @staticmethod
    def _ghostship_force_discord_router_channel_route(runtime_kwargs: dict) -> dict:
        forced_runtime = dict(runtime_kwargs)
        forced_runtime["base_url"] = "http://127.0.0.1:8788/v1"
        forced_runtime["provider"] = "custom"
        forced_runtime["api_mode"] = "chat_completions"
        forced_runtime["command"] = None
        forced_runtime["args"] = []
        forced_runtime["credential_pool"] = None
        return forced_runtime

    def _resolve_turn_agent_config(self, user_message: str, model: str, runtime_kwargs: dict, source=None) -> dict:
        from agent.smart_model_routing import resolve_turn_route
        from hermes_cli.models import resolve_fast_mode_overrides

        if self._ghostship_is_discord_router_channel(source):
            primary = {
                "model": "agentic",
                "base_url": "http://127.0.0.1:8788/v1",
                "provider": "custom",
                "api_mode": "chat_completions",
                "command": None,
                "args": [],
                "credential_pool": None,
            }
            route = resolve_turn_route(user_message, getattr(self, "_smart_model_routing", {}), primary)
            route["model"] = "agentic"
            route["runtime"] = self._ghostship_force_discord_router_channel_route(route.get("runtime", {}))
            route["label"] = "ghostship discord router channel pin"
            route["signature"] = (
                route["model"],
                route["runtime"].get("provider"),
                route["runtime"].get("base_url"),
                route["runtime"].get("api_mode"),
                route["runtime"].get("command"),
                tuple(route["runtime"].get("args") or ()),
            )
        else:
            primary = {
                "model": model,
                "api_key": runtime_kwargs.get("api_key"),
                "base_url": runtime_kwargs.get("base_url"),
                "provider": runtime_kwargs.get("provider"),
                "api_mode": runtime_kwargs.get("api_mode"),
                "command": runtime_kwargs.get("command"),
                "args": list(runtime_kwargs.get("args") or []),
                "credential_pool": runtime_kwargs.get("credential_pool"),
            }
            route = resolve_turn_route(user_message, getattr(self, "_smart_model_routing", {}), primary)

        service_tier = getattr(self, "_service_tier", None)
        if not service_tier:
            route["request_overrides"] = None
            return route

        try:
            overrides = resolve_fast_mode_overrides(route.get("model"))
        except Exception:
            overrides = None
        route["request_overrides"] = overrides
        return route
"""
gateway_run_text = gateway_run_text.replace(turn_route_marker, turn_route_replacement, 1)
if turn_route_replacement not in gateway_run_text:
    raise RuntimeError("failed to inject ghostship discord router channel pin into gateway.run")

gateway_run_text = gateway_run_text.replace(
    '            turn_route = self._resolve_turn_agent_config(prompt, model, runtime_kwargs)\n',
    '            turn_route = self._resolve_turn_agent_config(prompt, model, runtime_kwargs, source)\n',
    1,
)
gateway_run_text = gateway_run_text.replace(
    '            turn_route = self._resolve_turn_agent_config(question, model, runtime_kwargs)\n',
    '            turn_route = self._resolve_turn_agent_config(question, model, runtime_kwargs, source)\n',
    1,
)
gateway_run_text = gateway_run_text.replace(
    '            turn_route = self._resolve_turn_agent_config(message, model, runtime_kwargs)\n',
    '            turn_route = self._resolve_turn_agent_config(message, model, runtime_kwargs, source)\n',
    1,
)

model_guard_marker = """        # No args: show interactive picker (Telegram/Discord) or text list
        if not model_input and not explicit_provider:
"""
model_guard_replacement = """        if self._ghostship_is_discord_router_channel(source):
            self._session_model_overrides.pop(session_key, None)
            return "This Discord router channel is pinned to ghostship-router (`agentic`)."

        # No args: show interactive picker (Telegram/Discord) or text list
        if not model_input and not explicit_provider:
"""
gateway_run_text = gateway_run_text.replace(model_guard_marker, model_guard_replacement, 1)
if model_guard_replacement not in gateway_run_text:
    raise RuntimeError("failed to block /model in pinned discord router channels")

gateway_run.write_text(gateway_run_text)

providers_text = providers.read_text()
if "def resolve_custom_provider(" not in providers_text:
    providers_start = providers_text.index("def resolve_user_provider(")
    providers_end = providers_text.index("\ndef resolve_provider_full(")
    provider_lines = [
        "def resolve_user_provider(name: str, user_config: Dict[str, Any]) -> Optional[ProviderDef]:",
        "    \"\"\"Resolve a provider from the user's config.yaml custom provider surfaces.",
        "",
        "    Accepts both the legacy ``providers:`` dict and the modern",
        "    ``custom_providers:`` list.",
        "    \"\"\"",
        "    if not user_config:",
        "        return None",
        "",
        "    if isinstance(user_config, dict):",
        "        entry = user_config.get(name)",
        "        if not isinstance(entry, dict):",
        "            return None",
        "",
        "        display_name = entry.get(\"name\", \"\") or name",
        "        api_url = entry.get(\"api\", \"\") or entry.get(\"url\", \"\") or entry.get(\"base_url\", \"\") or \"\"",
        "        key_env = entry.get(\"key_env\", \"\") or \"\"",
        "        transport = entry.get(\"transport\", \"openai_chat\") or \"openai_chat\"",
        "",
        "        env_vars: List[str] = []",
        "        if key_env:",
        "            env_vars.append(key_env)",
        "",
        "        return ProviderDef(",
        "            id=name,",
        "            name=display_name,",
        "            transport=transport,",
        "            api_key_env_vars=tuple(env_vars),",
        "            base_url=api_url,",
        "            is_aggregator=False,",
        "            auth_type=\"api_key\",",
        "            source=\"user-config\",",
        "        )",
        "",
        "    if not isinstance(user_config, list):",
        "        return None",
        "",
        "    requested = name.strip().lower()",
        "    requested_slug = requested.removeprefix(\"custom:\")",
        "    for entry in user_config:",
        "        if not isinstance(entry, dict):",
        "            continue",
        "        display_name = str(entry.get(\"name\", \"\") or \"\").strip()",
        "        api_url = str(entry.get(\"base_url\", \"\") or entry.get(\"api\", \"\") or entry.get(\"url\", \"\") or \"\").strip()",
        "        if not display_name or not api_url:",
        "            continue",
        "        slug = display_name.strip().lower().replace(\" \", \"-\")",
        "        if requested_slug != slug:",
        "            continue",
        "",
        "        transport = entry.get(\"transport\", \"openai_chat\") or \"openai_chat\"",
        "        key_env = str(entry.get(\"key_env\", \"\") or \"\").strip()",
        "        env_vars: List[str] = []",
        "        if key_env:",
        "            env_vars.append(key_env)",
        "",
        "        return ProviderDef(",
        "            id=f\"custom:{slug}\",",
        "            name=display_name,",
        "            transport=transport,",
        "            api_key_env_vars=tuple(env_vars),",
        "            base_url=api_url,",
        "            is_aggregator=False,",
        "            auth_type=\"api_key\",",
        "            source=\"custom-provider\",",
        "        )",
        "",
        "    return None",
    ]
    providers_text = providers_text[:providers_start] + "\n".join(provider_lines) + "\n" + providers_text[providers_end:]
    if 'source=\"custom-provider\"' not in providers_text:
        raise RuntimeError("failed to add custom_providers support to resolve_user_provider")
providers.write_text(providers_text)

model_switch_text = model_switch.read_text()
old_user_provider_block = """    # --- 3. User-defined endpoints from config ---\n    if user_providers and isinstance(user_providers, dict):\n        for ep_name, ep_cfg in user_providers.items():\n            if not isinstance(ep_cfg, dict):\n                continue\n            display_name = ep_cfg.get(\"name\", \"\") or ep_name\n            api_url = ep_cfg.get(\"api\", \"\") or ep_cfg.get(\"url\", \"\") or \"\"\n            default_model = ep_cfg.get(\"default_model\", \"\")\n\n            models_list = []\n            if default_model:\n                models_list.append(default_model)\n\n            # Try to probe /v1/models if URL is set (but don't block on it)\n            # For now just show what we know from config\n            results.append({\n                \"slug\": ep_name,\n                \"name\": display_name,\n                \"is_current\": ep_name == current_provider,\n                \"is_user_defined\": True,\n                \"models\": models_list,\n                \"total_models\": len(models_list) if models_list else 0,\n                \"source\": \"user-config\",\n                \"api_url\": api_url,\n            })\n"""
new_user_provider_block = """    # --- 3. User-defined endpoints from config ---\n    if user_providers and isinstance(user_providers, dict):\n        for ep_name, ep_cfg in user_providers.items():\n            if not isinstance(ep_cfg, dict):\n                continue\n            display_name = ep_cfg.get(\"name\", \"\") or ep_name\n            api_url = ep_cfg.get(\"api\", \"\") or ep_cfg.get(\"url\", \"\") or \"\"\n            default_model = ep_cfg.get(\"default_model\", \"\")\n\n            models_list = []\n            if default_model:\n                models_list.append(default_model)\n\n            # Try to probe /v1/models if URL is set (but don't block on it)\n            # For now just show what we know from config\n            results.append({\n                \"slug\": ep_name,\n                \"name\": display_name,\n                \"is_current\": ep_name == current_provider,\n                \"is_user_defined\": True,\n                \"models\": models_list,\n                \"total_models\": len(models_list) if models_list else 0,\n                \"source\": \"user-config\",\n                \"api_url\": api_url,\n            })\n    elif user_providers and isinstance(user_providers, list):\n        from hermes_cli.models import fetch_api_models\n\n        for entry in user_providers:\n            if not isinstance(entry, dict):\n                continue\n            display_name = (entry.get(\"name\", \"\") or \"\").strip()\n            api_url = (entry.get(\"base_url\", \"\") or entry.get(\"api\", \"\") or entry.get(\"url\", \"\") or \"\").strip()\n            if not display_name or not api_url:\n                continue\n\n            slug = \"custom:\" + display_name.lower().replace(\" \", \"-\")\n            saved_model = str(entry.get(\"model\", \"\") or \"\").strip()\n            api_key = str(entry.get(\"api_key\", \"\") or \"\").strip() or None\n\n            fetched_models = fetch_api_models(api_key, api_url, timeout=3.0) or []\n            if fetched_models:\n                models_list = fetched_models[:max_models]\n                total_models = len(fetched_models)\n            elif saved_model:\n                models_list = [saved_model]\n                total_models = 1\n            else:\n                models_list = []\n                total_models = 0\n\n            results.append({\n                \"slug\": slug,\n                \"name\": display_name,\n                \"is_current\": slug == current_provider or display_name == current_provider,\n                \"is_user_defined\": True,\n                \"models\": models_list,\n                \"total_models\": total_models,\n                \"source\": \"custom-provider\",\n                \"api_url\": api_url,\n            })\n"""
if '# --- 4. Saved custom providers from config ---' not in model_switch_text:
    if old_user_provider_block not in model_switch_text:
        raise RuntimeError("failed to locate model_switch custom provider block")
    model_switch_text = model_switch_text.replace(old_user_provider_block, new_user_provider_block, 1)
    if '"source": "custom-provider"' not in model_switch_text:
        raise RuntimeError("failed to add custom_providers support to list_authenticated_providers")
model_switch.write_text(model_switch_text)
PATCH

    for prog in hermes hermes-agent hermes-acp; do
      if [ -f "$out/bin/$prog" ]; then
        wrapProgram "$out/bin/$prog" \
          --prefix PATH : ${lib.makeBinPath [ agentBrowserPackage ]} \
          --prefix PYTHONPATH : "$site_packages" \
          --set HERMES_BUNDLED_SKILLS "$skills_dir"
      fi
    done
  '';
  meta = with lib; {
    description = "Wrapped Hermes package with agent-browser layout and runtime fixes";
    platforms = hermesAgentPackage.meta.platforms or platforms.linux;
    mainProgram = "hermes";
  };
}
