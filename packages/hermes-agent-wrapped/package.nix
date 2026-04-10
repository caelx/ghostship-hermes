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
gateway = site / "hermes_cli" / "gateway.py"

doctor_text = doctor.read_text()
doctor_text = doctor_text.replace(
    "        if agent_browser_path.exists():",
    "        if shutil.which(\"agent-browser\") or agent_browser_path.exists():",
    1,
)
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

gateway_text = gateway.read_text()
main_command_marker = """
# =============================================================================
# Main Command Handler
# =============================================================================
"""
gateway_text = gateway_text.replace(
    main_command_marker,
    """

def _ghostship_managed_profiles_root() -> Path:
    return (Path.home() / ".hermes" / "profiles").resolve()


def _ghostship_managed_profile_name() -> str | None:
    home = get_hermes_home().resolve()
    try:
        relative = home.relative_to(_ghostship_managed_profiles_root())
    except ValueError:
        return None
    parts = relative.parts
    if len(parts) != 1:
        return None
    return parts[0]


def _ghostship_managed_profile_names() -> list[str]:
    root = _ghostship_managed_profiles_root()
    if not root.is_dir():
        return []
    return sorted(entry.name for entry in root.iterdir() if entry.is_dir())


def _ghostship_managed_service_name(profile: str) -> str:
    return f"ghostship-hermes-profile-{profile}"


def _ghostship_systemd_state(service_name: str) -> str:
    result = subprocess.run(
        ["systemctl", "is-active", service_name],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return result.stdout.strip() or "unknown"


def _ghostship_print_root_managed_status() -> None:
    profiles = _ghostship_managed_profile_names()
    if not profiles:
        print("✗ No managed profile gateways found")
        return

    print("✓ Managed gateway runtime is enabled")
    print("  This image runs one repo-managed gateway service per profile.")
    print()
    for profile in profiles:
        service_name = _ghostship_managed_service_name(profile)
        state = _ghostship_systemd_state(service_name)
        icon = "✓" if state == "active" else "✗"
        print(f"  {icon} {profile}: {state} ({service_name}.service)")
    print()
    print("Use profile-scoped status for full details:")
    for profile in profiles:
        print(f"  hermes -p {profile} gateway status")


def _ghostship_print_profile_managed_status(profile: str, deep: bool = False) -> None:
    service_name = _ghostship_managed_service_name(profile)
    state = _ghostship_systemd_state(service_name)

    if state == "active":
        print(f"✓ Managed gateway for profile '{profile}' is running")
    else:
        print(f"✗ Managed gateway for profile '{profile}' is {state}")
    print(f"  Service: {service_name}.service")

    if deep:
        print()
        subprocess.run(
            ["systemctl", "status", service_name, "--no-pager"],
            check=False,
            timeout=10,
        )
        print()
        print("Recent logs:")
        subprocess.run(
            ["journalctl", "-u", service_name, "-n", "20", "--no-pager"],
            check=False,
            timeout=10,
        )
    else:
        print("  Use --deep for systemd status and recent logs.")


def _ghostship_managed_mutation_guidance(subcmd: str, profile: str | None) -> None:
    print("This image manages Hermes gateway services through repo-owned systemd units.")
    if profile:
        service_name = _ghostship_managed_service_name(profile)
        print(f"Use: systemctl {subcmd} {service_name}.service")
        print(f"Or inspect first: hermes -p {profile} gateway status --deep")
    else:
        print("Choose a profile-specific gateway service:")
        for name in _ghostship_managed_profile_names():
            service_name = _ghostship_managed_service_name(name)
            print(f"  systemctl {subcmd} {service_name}.service")
        print("Or inspect the managed summary with: hermes gateway status")


def _ghostship_handle_managed_gateway_command(args) -> bool:
    if not is_managed():
        return False

    subcmd = getattr(args, "gateway_command", None)
    if subcmd not in {"status", "start", "stop", "restart"}:
        return False

    profile = _ghostship_managed_profile_name()
    if subcmd == "status":
        if profile:
            _ghostship_print_profile_managed_status(profile, deep=getattr(args, "deep", False))
        else:
            _ghostship_print_root_managed_status()
        return True

    _ghostship_managed_mutation_guidance(subcmd, profile)
    return True


# =============================================================================
# Main Command Handler
# =============================================================================
""",
    1,
)
if "_ghostship_handle_managed_gateway_command" not in gateway_text:
    raise RuntimeError("failed to inject ghostship managed gateway helpers into hermes_cli.gateway")

setup_block = """    if subcmd == "setup":
        gateway_setup()
        return

    # Service management commands
"""
setup_replacement = """    if subcmd == "setup":
        gateway_setup()
        return

    if _ghostship_handle_managed_gateway_command(args):
        return

    # Service management commands
"""
gateway_text = gateway_text.replace(setup_block, setup_replacement, 1)
if setup_replacement not in gateway_text:
    raise RuntimeError("failed to route managed gateway commands through ghostship shim")
gateway.write_text(gateway_text)
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
    description = "Wrapped Hermes package with agent-browser layout for doctor/runtime";
    platforms = hermesAgentPackage.meta.platforms or platforms.linux;
    mainProgram = "hermes";
  };
}
