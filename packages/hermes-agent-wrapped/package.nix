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

    site_packages=$(find "$out/lib" -mindepth 2 -maxdepth 2 -type d -path '*/site-packages' | sort | head -n1)
    if [ -z "$site_packages" ] || [ ! -d "$site_packages" ]; then
      echo "failed to locate site-packages in wrapped Hermes env output" >&2
      find "$out" -maxdepth 4 -type d >&2 || true
      exit 1
    fi

    python_bin=$(find "$out/bin" -maxdepth 1 -type f \( -name 'python3.*' -o -name python3 -o -name python \) | sort | head -n1)
    if [ -z "$python_bin" ] || [ ! -x "$python_bin" ]; then
      echo "failed to locate python in wrapped Hermes env output" >&2
      find "$out/bin" -maxdepth 1 -type f >&2 || true
      exit 1
    fi

    mkdir -p "$site_packages/node_modules"
    ln -s ${agentBrowserPackage}/share/agent-browser/package "$site_packages/node_modules/agent-browser"

    SITE_PACKAGES="$site_packages" "$python_bin" - <<'PATCH'
from pathlib import Path
import os

site = Path(os.environ["SITE_PACKAGES"])
tools = site / "hermes_cli" / "tools_config.py"
gateway_cli = site / "hermes_cli" / "gateway.py"
gateway_status = site / "gateway" / "status.py"
gateway_run = site / "gateway" / "run.py"
discord_platform = site / "gateway" / "platforms" / "discord.py"
model_switch = site / "hermes_cli" / "model_switch.py"
providers = site / "hermes_cli" / "providers.py"
config_py = site / "hermes_cli" / "config.py"
runtime_provider = site / "hermes_cli" / "runtime_provider.py"
auxiliary_client = site / "agent" / "auxiliary_client.py"
webhook_cli = site / "hermes_cli" / "webhook.py"
run_agent = site / "run_agent.py"

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
turn_route_direct_marker = """    def _resolve_turn_agent_config(self, user_message: str, model: str, runtime_kwargs: dict) -> dict:
        \"\"\"Build the effective model/runtime config for a single turn.

        Always uses the session's primary model/provider.  If `/fast` is
        enabled and the model supports Priority Processing / Anthropic fast
        mode, attach `request_overrides` so the API call is marked
        accordingly.
        \"\"\"
        from hermes_cli.models import resolve_fast_mode_overrides

        runtime = {
            "api_key": runtime_kwargs.get("api_key"),
            "base_url": runtime_kwargs.get("base_url"),
            "provider": runtime_kwargs.get("provider"),
            "api_mode": runtime_kwargs.get("api_mode"),
            "command": runtime_kwargs.get("command"),
            "args": list(runtime_kwargs.get("args") or []),
            "credential_pool": runtime_kwargs.get("credential_pool"),
        }
        route = {
            "model": model,
            "runtime": runtime,
            "signature": (
                model,
                runtime["provider"],
                runtime["base_url"],
                runtime["api_mode"],
                runtime["command"],
                tuple(runtime["args"]),
            ),
        }

        service_tier = getattr(self, "_service_tier", None)
        if not service_tier:
            route["request_overrides"] = None
            return route

        try:
            overrides = resolve_fast_mode_overrides(route["model"])
        except Exception:
            overrides = None
        route["request_overrides"] = overrides
        return route
"""
turn_route_helpers = """    @staticmethod
    def _ghostship_is_discord_codex_channel(source) -> bool:
        if source is None:
            return False
        platform = getattr(source, "platform", None)
        platform_value = getattr(platform, "value", platform)
        if platform_value != "discord":
            return False
        if getattr(source, "chat_type", None) == "dm":
            return False
        codex_channel = os.getenv("GHOSTSHIP_CODEX_CHANNEL", "").strip()
        if not codex_channel:
            return False
        chat_id = getattr(source, "chat_id", None)
        parent_chat_id = getattr(source, "chat_id_alt", None)
        return chat_id == codex_channel or parent_chat_id == codex_channel

    @staticmethod
    def _ghostship_force_discord_codex_channel_route(runtime_kwargs: dict) -> dict:
        forced_runtime = dict(runtime_kwargs)
        forced_runtime["base_url"] = None
        forced_runtime["provider"] = "openai-codex"
        forced_runtime["api_mode"] = "codex_responses"
        forced_runtime["command"] = None
        forced_runtime["args"] = []
        forced_runtime["credential_pool"] = None
        return forced_runtime

"""
turn_route_smart_replacement = turn_route_helpers + """    def _resolve_turn_agent_config(self, user_message: str, model: str, runtime_kwargs: dict, source=None) -> dict:
        from agent.smart_model_routing import resolve_turn_route
        from hermes_cli.models import resolve_fast_mode_overrides

        if self._ghostship_is_discord_codex_channel(source):
            primary = {
                "model": "gpt-5.5",
                "base_url": None,
                "provider": "openai-codex",
                "api_mode": "codex_responses",
                "command": None,
                "args": [],
                "credential_pool": None,
            }
            route = resolve_turn_route(user_message, getattr(self, "_smart_model_routing", {}), primary)
            route["model"] = "gpt-5.5"
            route["runtime"] = self._ghostship_force_discord_codex_channel_route(route.get("runtime", {}))
            route["label"] = "ghostship discord codex channel pin"
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
turn_route_direct_replacement = turn_route_helpers + """    def _resolve_turn_agent_config(self, user_message: str, model: str, runtime_kwargs: dict, source=None) -> dict:
        from hermes_cli.models import resolve_fast_mode_overrides

        if self._ghostship_is_discord_codex_channel(source):
            runtime = self._ghostship_force_discord_codex_channel_route({})
            route = {
                "model": "gpt-5.5",
                "runtime": runtime,
                "label": "ghostship discord codex channel pin",
                "signature": (
                    "gpt-5.5",
                    runtime.get("provider"),
                    runtime.get("base_url"),
                    runtime.get("api_mode"),
                    runtime.get("command"),
                    tuple(runtime.get("args") or ()),
                ),
            }
        else:
            runtime = {
                "api_key": runtime_kwargs.get("api_key"),
                "base_url": runtime_kwargs.get("base_url"),
                "provider": runtime_kwargs.get("provider"),
                "api_mode": runtime_kwargs.get("api_mode"),
                "command": runtime_kwargs.get("command"),
                "args": list(runtime_kwargs.get("args") or []),
                "credential_pool": runtime_kwargs.get("credential_pool"),
            }
            route = {
                "model": model,
                "runtime": runtime,
                "signature": (
                    model,
                    runtime["provider"],
                    runtime["base_url"],
                    runtime["api_mode"],
                    runtime["command"],
                    tuple(runtime["args"]),
                ),
            }

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
gateway_run_text = gateway_run_text.replace(turn_route_marker, turn_route_smart_replacement, 1)
if "_ghostship_is_discord_codex_channel" not in gateway_run_text:
    gateway_run_text = gateway_run_text.replace(turn_route_direct_marker, turn_route_direct_replacement, 1)
if "_ghostship_is_discord_codex_channel" not in gateway_run_text:
    raise RuntimeError("failed to inject ghostship discord codex channel pin into gateway.run")

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
model_guard_replacement = """        if self._ghostship_is_discord_codex_channel(source):
            self._session_model_overrides.pop(session_key, None)
            return "This Discord Codex channel is pinned to openai-codex (`gpt-5.5`)."

        # No args: show interactive picker (Telegram/Discord) or text list
        if not model_input and not explicit_provider:
"""
gateway_run_text = gateway_run_text.replace(model_guard_marker, model_guard_replacement, 1)
if model_guard_replacement not in gateway_run_text:
    raise RuntimeError("failed to block /model in pinned discord codex channels")

gateway_run_text = gateway_run_text.replace(
    '    async def _session_expiry_watcher(self, interval: int = 300):\n',
    """    async def _ghostship_discord_thread_is_dead(self, adapter, thread_id: str) -> bool:
        client = getattr(adapter, "_client", None)
        if client is None:
            return False
        try:
            thread_int = int(thread_id)
        except (TypeError, ValueError):
            return False
        try:
            thread = client.get_channel(thread_int)
            if thread is None:
                thread = await client.fetch_channel(thread_int)
        except Exception:
            return True
        if thread is None:
            return True
        return bool(getattr(thread, "archived", False) or getattr(thread, "locked", False))

    @staticmethod
    def _ghostship_discord_thread_id_for_entry(session_key: str, entry) -> str | None:
        origin = getattr(entry, "origin", None)
        thread_id = getattr(origin, "thread_id", None)
        if thread_id:
            return str(thread_id)
        parsed = _parse_session_key(session_key)
        if parsed and parsed.get("platform") == "discord" and parsed.get("chat_type") == "thread":
            return parsed.get("thread_id") or parsed.get("chat_id")
        return None

    async def _ghostship_retire_closed_discord_threads(self) -> int:
        now = datetime.now()
        if now.hour < 5:
            return 0
        marker = now.date().isoformat()
        if getattr(self, "_ghostship_last_discord_thread_retire_date", None) == marker:
            return 0
        adapter = self.adapters.get(Platform.DISCORD)
        if adapter is None:
            return 0

        self.session_store._ensure_loaded()
        retired = 0
        for key, entry in list(self.session_store._entries.items()):
            platform = getattr(entry, "platform", None)
            platform_value = getattr(platform, "value", platform)
            if platform_value != "discord":
                continue
            if getattr(entry, "chat_type", None) != "thread":
                continue
            if key in self._running_agents:
                continue
            active_processes = getattr(self.session_store, "_has_active_processes_fn", None)
            if active_processes is not None:
                try:
                    if active_processes(key):
                        continue
                except Exception as exc:
                    logger.debug("Discord thread retirement process check failed for %s: %s", key, exc)
                    continue
            thread_id = self._ghostship_discord_thread_id_for_entry(key, entry)
            if not thread_id:
                continue
            if not await self._ghostship_discord_thread_is_dead(adapter, thread_id):
                continue
            if not getattr(entry, "memory_flushed", False):
                try:
                    await self._async_flush_memories(entry.session_id, key)
                except Exception as exc:
                    logger.debug("Discord thread retirement memory flush failed for %s: %s", key, exc)

            cached_agent = None
            cache_lock = getattr(self, "_agent_cache_lock", None)
            if cache_lock is not None:
                with cache_lock:
                    cached = self._agent_cache.get(key)
                    cached_agent = cached[0] if isinstance(cached, tuple) else cached if cached else None
            if cached_agent and cached_agent is not _AGENT_PENDING_SENTINEL:
                self._cleanup_agent_resources(cached_agent)
            self._evict_cached_agent(key)
            self._session_model_overrides.pop(key, None)

            with self.session_store._lock:
                if self.session_store._entries.get(key) is entry:
                    self.session_store._entries.pop(key, None)
                    self.session_store._save()
                    retired += 1

        self._ghostship_last_discord_thread_retire_date = marker
        if retired:
            logger.info("Retired %d closed Discord thread session(s)", retired)
        return retired

    async def _session_expiry_watcher(self, interval: int = 300):
""",
    1,
)
if "_ghostship_retire_closed_discord_threads" not in gateway_run_text:
    raise RuntimeError("failed to inject closed Discord thread retirement sweep")

gateway_run_text = gateway_run_text.replace(
    """                # Periodically prune stale SessionStore entries.  The
                # in-memory dict (and sessions.json) would otherwise grow
""",
    """                try:
                    await self._ghostship_retire_closed_discord_threads()
                except Exception as _e:
                    logger.debug("Discord closed-thread retirement failed: %s", _e)

                # Periodically prune stale SessionStore entries.  The
                # in-memory dict (and sessions.json) would otherwise grow
""",
    1,
)
if "Discord closed-thread retirement failed" not in gateway_run_text:
    raise RuntimeError("failed to schedule closed Discord thread retirement sweep")

gateway_run.write_text(gateway_run_text)

discord_text = discord_platform.read_text()
discord_text = discord_text.replace(
    '        thread_id = None\n\n        if is_dm:\n',
    '        thread_id = None\n        parent_channel_id = self._get_parent_channel_id(interaction.channel) if is_thread else None\n\n        if is_dm:\n',
    1,
)
discord_text = discord_text.replace(
    '            thread_id=thread_id,\n            chat_topic=chat_topic,\n',
    '            thread_id=thread_id,\n            chat_id_alt=parent_channel_id,\n            chat_topic=chat_topic,\n',
    1,
)
discord_text = discord_text.replace(
    '        source = self.build_source(\n            chat_id=thread_id,\n',
    '        _parent_channel = self._thread_parent_channel(getattr(interaction, "channel", None))\n        _parent_id = str(getattr(_parent_channel, "id", "") or "")\n\n        source = self.build_source(\n            chat_id=thread_id,\n',
    1,
)
discord_text = discord_text.replace(
    '            thread_id=thread_id,\n            chat_topic=chat_topic,\n        )\n\n        _parent_channel = self._thread_parent_channel(getattr(interaction, "channel", None))\n        _parent_id = str(getattr(_parent_channel, "id", "") or "")\n',
    '            thread_id=thread_id,\n            chat_id_alt=_parent_id or None,\n            chat_topic=chat_topic,\n        )\n\n',
    1,
)
discord_text = discord_text.replace(
    '            skip_thread = bool(channel_ids & no_thread_channels) or is_free_channel\n',
    '            skip_thread = bool(channel_ids & no_thread_channels)\n',
    1,
)
discord_text = discord_text.replace(
    '                    thread_id = str(thread.id)\n                    auto_threaded_channel = thread\n',
    '                    thread_id = str(thread.id)\n                    parent_channel_id = str(message.channel.id)\n                    auto_threaded_channel = thread\n',
    1,
)
discord_text = discord_text.replace(
    '            thread_id=thread_id,\n            chat_topic=chat_topic,\n            is_bot=getattr(message.author, "bot", False),\n',
    '            thread_id=thread_id,\n            chat_id_alt=parent_channel_id if is_thread else None,\n            chat_topic=chat_topic,\n            is_bot=getattr(message.author, "bot", False),\n',
    1,
)
if "skip_thread = bool(channel_ids & no_thread_channels) or is_free_channel" in discord_text:
    raise RuntimeError("failed to allow free-response channels to auto-thread")
if "chat_id_alt=parent_channel_id if is_thread else None" not in discord_text:
    raise RuntimeError("failed to preserve Discord thread parent channel ids")
discord_platform.write_text(discord_text)

webhook_cli_text = webhook_cli.read_text()
webhook_cli_text = webhook_cli_text.replace(
    '    if args.deliver_chat_id:\n        route["deliver_extra"] = {"chat_id": args.deliver_chat_id}\n',
    '    deliver_chat_id = args.deliver_chat_id\n    if not deliver_chat_id and route["deliver"] == "discord":\n        deliver_chat_id = os.getenv("DISCORD_WEBHOOK_CHANNEL", "").strip()\n    if deliver_chat_id:\n        route["deliver_extra"] = {"chat_id": deliver_chat_id}\n',
    1,
)
if 'DISCORD_WEBHOOK_CHANNEL' not in webhook_cli_text:
    raise RuntimeError("failed to default Discord webhook delivery channel")
webhook_cli.write_text(webhook_cli_text)

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
        "        key_env = entry.get(\"api_key_env\", \"\") or entry.get(\"key_env\", \"\") or \"\"",
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
        "        key_env = str(entry.get(\"api_key_env\", \"\") or entry.get(\"key_env\", \"\") or \"\").strip()",
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
else:
    custom_provider_api_key_marker = """        return ProviderDef(
            id=slug,
            name=display_name,
            transport="openai_chat",
            api_key_env_vars=(),
"""
    custom_provider_api_key_replacement = """        key_env = (
            entry.get("api_key_env", "")
            or entry.get("key_env", "")
            or ""
        )
        env_vars: List[str] = []
        if key_env:
            env_vars.append(str(key_env).strip())

        return ProviderDef(
            id=slug,
            name=display_name,
            transport="openai_chat",
            api_key_env_vars=tuple(env_vars),
"""
    if custom_provider_api_key_marker in providers_text:
        providers_text = providers_text.replace(custom_provider_api_key_marker, custom_provider_api_key_replacement, 1)
    if 'entry.get("api_key_env", "")' not in providers_text:
        raise RuntimeError("failed to teach custom_providers to honor api_key_env")
providers.write_text(providers_text)

config_text = config_py.read_text()
config_text = config_text.replace(
    '        "keyEnv": "key_env",\n        "defaultModel": "default_model",\n',
    '        "keyEnv": "key_env",\n        "apiKeyEnv": "api_key_env",\n        "defaultModel": "default_model",\n',
    1,
)
config_text = config_text.replace(
    '        "name", "api", "url", "base_url", "api_key", "key_env",\n        "api_mode", "transport", "model", "default_model", "models",\n',
    '        "name", "api", "url", "base_url", "api_key", "key_env", "api_key_env",\n        "api_mode", "transport", "model", "default_model", "models",\n',
    1,
)
config_text = config_text.replace(
    '    key_env = entry.get("key_env")\n    if isinstance(key_env, str) and key_env.strip():\n        normalized["key_env"] = key_env.strip()\n',
    '    key_env = entry.get("key_env") or entry.get("api_key_env")\n    if isinstance(key_env, str) and key_env.strip():\n        normalized["key_env"] = key_env.strip()\n        normalized["api_key_env"] = key_env.strip()\n',
    1,
)
if '"apiKeyEnv": "api_key_env"' not in config_text or '"api_key_env"' not in config_text:
    raise RuntimeError("failed to teach custom provider config normalization about api_key_env")
config_py.write_text(config_text)

runtime_provider_text = runtime_provider.read_text()
runtime_provider_text = runtime_provider_text.replace(
    '            key_env = str(entry.get("key_env", "") or "").strip()\n',
    '            key_env = str(entry.get("api_key_env", "") or entry.get("key_env", "") or "").strip()\n',
    1,
)
runtime_provider_text = runtime_provider_text.replace(
    '            "api_key": str(entry.get("api_key", "") or "").strip(),\n        }\n        key_env = str(entry.get("key_env", "") or "").strip()\n        if key_env:\n            result["key_env"] = key_env\n',
    '            "api_key": str(entry.get("api_key", "") or "").strip(),\n        }\n        key_env = str(entry.get("api_key_env", "") or entry.get("key_env", "") or "").strip()\n        if key_env:\n            result["key_env"] = key_env\n            result["api_key_env"] = key_env\n',
    1,
)
runtime_provider_text = runtime_provider_text.replace(
    '        os.getenv(str(custom_provider.get("key_env", "") or "").strip(), "").strip(),\n',
    '        os.getenv(str(custom_provider.get("api_key_env", "") or custom_provider.get("key_env", "") or "").strip(), "").strip(),\n',
    1,
)
if 'custom_provider.get("api_key_env", "")' not in runtime_provider_text:
    raise RuntimeError("failed to teach runtime named custom providers about api_key_env")
runtime_provider.write_text(runtime_provider_text)

auxiliary_client_text = auxiliary_client.read_text()
auxiliary_client_text = auxiliary_client_text.replace(
    '            custom_key_env = custom_entry.get("key_env", "").strip()\n',
    '            custom_key_env = (\n                custom_entry.get("api_key_env", "")\n                or custom_entry.get("key_env", "")\n                or ""\n            ).strip()\n',
    1,
)
if 'custom_entry.get("api_key_env", "")' not in auxiliary_client_text:
    raise RuntimeError("failed to teach agent named custom providers about api_key_env")
auxiliary_client.write_text(auxiliary_client_text)

run_agent_text = run_agent.read_text()
run_agent_text = run_agent_text.replace(
    "    def _try_activate_fallback(self) -> bool:\n",
    "    def _try_activate_fallback(self, trigger=None, error=None, status_code=None) -> bool:\n",
    1,
)
run_agent_text = run_agent_text.replace(
    "            return self._try_activate_fallback()  # skip invalid, try next\n",
    "            return self._try_activate_fallback(trigger=trigger, error=error, status_code=status_code)  # skip invalid, try next\n",
    1,
)
run_agent_text = run_agent_text.replace(
    "            old_model = self.model\n            self.model = fb_model\n",
    "            old_model = self.model\n            old_provider = self.provider\n            self.model = fb_model\n",
    1,
)
run_agent_text = run_agent_text.replace(
    """            logging.info(
                "Fallback activated: %s → %s (%s)",
                old_model, fb_model, fb_provider,
            )
""",
    """            logging.info(
                "Fallback activated: %s → %s (%s)",
                old_model, fb_model, fb_provider,
            )
            if trigger or error is not None:
                logging.warning(
                    "Primary model failure before fallback: trigger=%s primary=%s (%s) "
                    "fallback=%s (%s) status=%s error_type=%s error=%s",
                    trigger or "unspecified",
                    old_model,
                    old_provider,
                    fb_model,
                    fb_provider,
                    status_code or "",
                    type(error).__name__ if error is not None else "",
                    self._summarize_api_error(error) if error is not None else "",
                )
""",
    1,
)
for old, new in (
    (
        "                            if self._try_activate_fallback():\n",
        "                            if self._try_activate_fallback(trigger=\"nous_rate_guard\"):\n",
    ),
    (
        "                        if self._try_activate_fallback():\n",
        "                        if self._try_activate_fallback(trigger=\"invalid_response\", error=response):\n",
    ),
    (
        "                            if self._try_activate_fallback():\n",
        "                            if self._try_activate_fallback(trigger=\"invalid_response_max_retries\", error=response):\n",
    ),
    (
        "                            if self._try_activate_fallback():\n",
        "                            if self._try_activate_fallback(trigger=\"rate_limited\", error=api_error, status_code=status_code):\n",
    ),
    (
        "                        if self._try_activate_fallback():\n",
        "                        if self._try_activate_fallback(trigger=\"non_retryable_client_error\", error=api_error, status_code=status_code):\n",
    ),
    (
        "                        if self._try_activate_fallback():\n",
        "                        if self._try_activate_fallback(trigger=\"max_retries_exhausted\", error=api_error, status_code=status_code):\n",
    ),
    (
        "                            if self._try_activate_fallback():\n",
        "                            if self._try_activate_fallback(trigger=\"empty_response_exhausted\"):\n",
    ),
):
    if old in run_agent_text:
        run_agent_text = run_agent_text.replace(old, new, 1)
run_agent_text = run_agent_text.replace(
    """        kimi_requires_reasoning = (
            self.provider in {"kimi-coding", "kimi-coding-cn"}
            or base_url_host_matches(self.base_url, "api.kimi.com")
            or base_url_host_matches(self.base_url, "moonshot.ai")
            or base_url_host_matches(self.base_url, "moonshot.cn")
        )
""",
    """        ghostship_opencode_go_reasoning = (
            self.provider == "opencode-go"
            and isinstance(getattr(self, "reasoning_config", None), dict)
            and self.reasoning_config.get("enabled") is not False
        )
        kimi_requires_reasoning = (
            self.provider in {"kimi-coding", "kimi-coding-cn"}
            or ghostship_opencode_go_reasoning
            or base_url_host_matches(self.base_url, "api.kimi.com")
            or base_url_host_matches(self.base_url, "moonshot.ai")
            or base_url_host_matches(self.base_url, "moonshot.cn")
        )
""",
    1,
)
if 'self.provider == "opencode-go"' not in run_agent_text:
    raise RuntimeError("failed to replay opencode-go tool-call history with reasoning_content")
if 'api_msg["reasoning_content"] = ""' not in run_agent_text:
    raise RuntimeError("failed to verify opencode-go reasoning_content replay fallback")
if "Primary model failure before fallback" not in run_agent_text:
    raise RuntimeError("failed to add primary fallback failure logging")
run_agent.write_text(run_agent_text)

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
