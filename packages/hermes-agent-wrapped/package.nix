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
doctor = site / "hermes_cli" / "doctor.py"
tools = site / "hermes_cli" / "tools_config.py"
gateway_cli = site / "hermes_cli" / "gateway.py"
gateway_status = site / "gateway" / "status.py"
gateway_run = site / "gateway" / "run.py"
model_switch = site / "hermes_cli" / "model_switch.py"

doctor_text = doctor.read_text()
doctor_text = doctor_text.replace(
    "        if agent_browser_path.exists():",
    "        if shutil.which(\"agent-browser\") or agent_browser_path.exists():",
    1,
)
doctor.write_text(doctor_text)

doctor_text = doctor.read_text()
doctor_text = doctor_text.replace(
    '        ("MiniMax (China)",  ("MINIMAX_CN_API_KEY",),                         None,                                  "MINIMAX_CN_BASE_URL", False),\n',
    '        ("MiniMax (China)",  ("MINIMAX_CN_API_KEY",),                         None,                                  "MINIMAX_CN_BASE_URL", False),\n        ("OpenCode Go",      ("OPENCODE_GO_API_KEY",),                        None,                                  "OPENCODE_GO_BASE_URL", False),\n',
    1,
)
if '("OpenCode Go",      ("OPENCODE_GO_API_KEY",),                        None,                                  "OPENCODE_GO_BASE_URL", False),' not in doctor_text:
    raise RuntimeError("failed to teach hermes doctor that OpenCode Go lacks /models health checks")
doctor.write_text(doctor_text)

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
    '                user_provs = cfg.get("providers") or cfg.get("custom_providers")\n',
    1,
)
if 'cfg.get("providers") or cfg.get("custom_providers")' not in gateway_run_text:
    raise RuntimeError("failed to teach Discord model picker to use custom_providers")
gateway_run.write_text(gateway_run_text)

model_switch_text = model_switch.read_text()
old_user_provider_block = """    # --- 3. User-defined endpoints from config ---\n    if user_providers and isinstance(user_providers, dict):\n        for ep_name, ep_cfg in user_providers.items():\n            if not isinstance(ep_cfg, dict):\n                continue\n            display_name = ep_cfg.get(\"name\", \"\") or ep_name\n            api_url = ep_cfg.get(\"api\", \"\") or ep_cfg.get(\"url\", \"\") or \"\"\n            default_model = ep_cfg.get(\"default_model\", \"\")\n\n            models_list = []\n            if default_model:\n                models_list.append(default_model)\n\n            # Try to probe /v1/models if URL is set (but don't block on it)\n            # For now just show what we know from config\n            results.append({\n                \"slug\": ep_name,\n                \"name\": display_name,\n                \"is_current\": ep_name == current_provider,\n                \"is_user_defined\": True,\n                \"models\": models_list,\n                \"total_models\": len(models_list) if models_list else 0,\n                \"source\": \"user-config\",\n                \"api_url\": api_url,\n            })\n"""
new_user_provider_block = """    # --- 3. User-defined endpoints from config ---\n    if user_providers and isinstance(user_providers, dict):\n        for ep_name, ep_cfg in user_providers.items():\n            if not isinstance(ep_cfg, dict):\n                continue\n            display_name = ep_cfg.get(\"name\", \"\") or ep_name\n            api_url = ep_cfg.get(\"api\", \"\") or ep_cfg.get(\"url\", \"\") or \"\"\n            default_model = ep_cfg.get(\"default_model\", \"\")\n\n            models_list = []\n            if default_model:\n                models_list.append(default_model)\n\n            # Try to probe /v1/models if URL is set (but don't block on it)\n            # For now just show what we know from config\n            results.append({\n                \"slug\": ep_name,\n                \"name\": display_name,\n                \"is_current\": ep_name == current_provider,\n                \"is_user_defined\": True,\n                \"models\": models_list,\n                \"total_models\": len(models_list) if models_list else 0,\n                \"source\": \"user-config\",\n                \"api_url\": api_url,\n            })\n    elif user_providers and isinstance(user_providers, list):\n        from hermes_cli.models import fetch_api_models\n\n        for entry in user_providers:\n            if not isinstance(entry, dict):\n                continue\n            display_name = (entry.get(\"name\", \"\") or \"\").strip()\n            api_url = (entry.get(\"base_url\", \"\") or entry.get(\"api\", \"\") or entry.get(\"url\", \"\") or \"\").strip()\n            if not display_name or not api_url:\n                continue\n\n            slug = \"custom:\" + display_name.lower().replace(\" \", \"-\")\n            saved_model = str(entry.get(\"model\", \"\") or \"\").strip()\n            api_key = str(entry.get(\"api_key\", \"\") or \"\").strip() or None\n\n            fetched_models = fetch_api_models(api_key, api_url, timeout=3.0) or []\n            if fetched_models:\n                models_list = fetched_models[:max_models]\n                total_models = len(fetched_models)\n            elif saved_model:\n                models_list = [saved_model]\n                total_models = 1\n            else:\n                models_list = []\n                total_models = 0\n\n            results.append({\n                \"slug\": slug,\n                \"name\": display_name,\n                \"is_current\": slug == current_provider or display_name == current_provider,\n                \"is_user_defined\": True,\n                \"models\": models_list,\n                \"total_models\": total_models,\n                \"source\": \"custom-provider\",\n                \"api_url\": api_url,\n            })\n"""
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
