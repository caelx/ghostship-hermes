{
  bash,
  coreutils,
  findutils,
  gnugrep,
  gnused,
  hermesDashboard,
  procps,
  python3,
  ttyd,
  util-linux,
  writeShellApplication,
}:
writeShellApplication {
  name = "ghostship-hermes-runtime";
  runtimeInputs = [
    bash
    coreutils
    findutils
    gnugrep
    gnused
    procps
    python3
    ttyd
    util-linux
  ];
  text = ''
    set -euo pipefail

    export HERMES_USER="''${HERMES_USER:-hermes}"
    export HERMES_UID="''${HERMES_UID:-3000}"
    export HERMES_GID="''${HERMES_GID:-3000}"
    export HOME="''${HOME:-/home/hermes}"
    export HERMES_HOME="''${HERMES_HOME:-/home/hermes/.hermes}"
    export GHOSTSHIP_WORKSPACE_ROOT="''${GHOSTSHIP_WORKSPACE_ROOT:-/workspace}"
    export GHOSTSHIP_DASHBOARD_STATE_DIR="''${GHOSTSHIP_DASHBOARD_STATE_DIR:-/home/hermes/.local/state/ghostship-hermes/dashboard}"
    export GHOSTSHIP_ROUTER_STATE_DIR="''${GHOSTSHIP_ROUTER_STATE_DIR:-/home/hermes/.local/state/ghostship-hermes/router}"
    export GHOSTSHIP_DASHBOARD_HOST="''${GHOSTSHIP_DASHBOARD_HOST:-0.0.0.0}"
    export GHOSTSHIP_DASHBOARD_PORT="''${GHOSTSHIP_DASHBOARD_PORT:-7681}"
    export GHOSTSHIP_TTYD_PORT_BASE="''${GHOSTSHIP_TTYD_PORT_BASE:-7682}"
    export GHOSTSHIP_TTYD_HOST="''${GHOSTSHIP_TTYD_HOST:-127.0.0.1}"
    export GHOSTSHIP_TTYD_TITLE="''${GHOSTSHIP_TTYD_TITLE:-ghostship-hermes}"
    export GHOSTSHIP_TERMINAL_CWD="''${GHOSTSHIP_TERMINAL_CWD:-/home/hermes}"
    export HERMES_HUD_PROJECTS_DIR="''${HERMES_HUD_PROJECTS_DIR:-$GHOSTSHIP_WORKSPACE_ROOT}"
    export GHOSTSHIP_HUD_DEFAULT_PROFILE_NAME="''${GHOSTSHIP_HUD_DEFAULT_PROFILE_NAME:-Managed Agent}"
    export GHOSTSHIP_AGENT_TOOLS_PREFIX="''${GHOSTSHIP_AGENT_TOOLS_PREFIX:-$HOME/.local/share/ghostship-agent-tools/npm}"
    export XDG_CONFIG_HOME="''${XDG_CONFIG_HOME:-$HOME/.config}"
    export XDG_DATA_HOME="''${XDG_DATA_HOME:-$HOME/.local/share}"
    export XDG_STATE_HOME="''${XDG_STATE_HOME:-$HOME/.local/state}"
    export XDG_CACHE_HOME="''${XDG_CACHE_HOME:-$HOME/.cache}"
    export BITWARDENCLI_APPDATA_DIR="''${BITWARDENCLI_APPDATA_DIR:-$HOME/.local/state/bitwarden-cli}"
    export PATH="$GHOSTSHIP_AGENT_TOOLS_PREFIX/bin:$HOME/.local/bin:$HOME/.nix-profile/bin:/nix/var/nix/profiles/default/bin:$PATH"

    ensure_dir() {
      local path="$1"
      local mode="$2"
      install -d -m "$mode" "$path"
      chown "$HERMES_UID:$HERMES_GID" "$path"
    }

    prepare_nix_profile_state() {
      local profile_root gc_root profile_link

      profile_root="/nix/var/nix/profiles/per-user/$HERMES_USER"
      gc_root="/nix/var/nix/gcroots/per-user/$HERMES_USER"
      profile_link="$HOME/.nix-profile"

      install -d -m 0755 /nix/var/nix/daemon-socket >/dev/null 2>&1 || true
      install -d -m 0755 /nix/var/nix/profiles/per-user >/dev/null 2>&1 || true
      install -d -m 0755 "$profile_root" "$gc_root" >/dev/null 2>&1 || true
      chown -R "$HERMES_UID:$HERMES_GID" "$profile_root" "$gc_root" >/dev/null 2>&1 || true

      ln -sfn "$profile_root/profile" "$profile_link"
      chown -h "$HERMES_UID:$HERMES_GID" "$profile_link" >/dev/null 2>&1 || true
    }

    prepare_storage() {
      install -d -m 1777 /tmp
      ensure_dir "$GHOSTSHIP_WORKSPACE_ROOT" 0750
      ensure_dir "$HOME" 0750
      ensure_dir "$HERMES_HOME" 0750
      ensure_dir "$GHOSTSHIP_DASHBOARD_STATE_DIR" 0750
      ensure_dir "$GHOSTSHIP_ROUTER_STATE_DIR" 0750
      ensure_dir "/run/user/$HERMES_UID" 0700

      prepare_nix_profile_state
      ensure_dir "$XDG_CONFIG_HOME" 0750
      ensure_dir "$XDG_DATA_HOME" 0750
      ensure_dir "$XDG_STATE_HOME" 0750
      ensure_dir "$BITWARDENCLI_APPDATA_DIR" 0700
      ensure_dir "$XDG_CACHE_HOME" 0750
      ensure_dir "$HOME/.local/bin" 0750
      ensure_dir "$GHOSTSHIP_AGENT_TOOLS_PREFIX" 0750
      ensure_dir "$XDG_CACHE_HOME/npm" 0750
      ensure_dir "$HOME/.config/systemd/user" 0750
      ensure_dir "$HOME/.ssh" 0700
      ensure_dir "$HOME/.gnupg" 0700
      ensure_dir "$HOME/.pki" 0700
      chown -R "$HERMES_UID:$HERMES_GID" "$HOME" "$GHOSTSHIP_WORKSPACE_ROOT" >/dev/null 2>&1 || true
      chmod 0750 "$HOME" "$GHOSTSHIP_WORKSPACE_ROOT" "$HERMES_HOME"
    }

    run_dashboard_controller() {
      exec ${hermesDashboard}/bin/hermes-dashboard
    }
    usage() {
      printf 'usage: ghostship-hermes-runtime <prepare-storage|dashboard-controller>\n' >&2
      exit 1
    }

    command="''${1:-}"
    case "$command" in
      prepare-storage)
        prepare_storage
        ;;
      dashboard-controller)
        run_dashboard_controller
        ;;
      *)
        usage
        ;;
    esac
  '';
}
