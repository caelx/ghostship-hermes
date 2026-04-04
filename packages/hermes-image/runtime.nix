{
  bash,
  coreutils,
  findutils,
  gnugrep,
  gnused,
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
    export HERMES_HOME="''${HERMES_HOME:-/data/.hermes}"
    export GHOSTSHIP_DATA_ROOT="''${GHOSTSHIP_DATA_ROOT:-/data}"
    export GHOSTSHIP_HOME_ROOT="''${GHOSTSHIP_HOME_ROOT:-/data/home}"
    export GHOSTSHIP_WORKSPACE_ROOT="''${GHOSTSHIP_WORKSPACE_ROOT:-/workspace}"
    export GHOSTSHIP_DASHBOARD_STATE_DIR="''${GHOSTSHIP_DASHBOARD_STATE_DIR:-/data/.ghostship/dashboard}"
    export GHOSTSHIP_DASHBOARD_PORT="''${GHOSTSHIP_DASHBOARD_PORT:-7683}"
    export GHOSTSHIP_TTYD_PORT="''${GHOSTSHIP_TTYD_PORT:-7682}"
    export GHOSTSHIP_TTYD_BASE_PATH="''${GHOSTSHIP_TTYD_BASE_PATH:-/terminal}"
    export GHOSTSHIP_TTYD_TITLE="''${GHOSTSHIP_TTYD_TITLE:-ghostship-hermes}"
    export MESSAGING_CWD="''${MESSAGING_CWD:-/workspace}"
    export XDG_CONFIG_HOME="''${XDG_CONFIG_HOME:-$HOME/.config}"
    export XDG_DATA_HOME="''${XDG_DATA_HOME:-$HOME/.local/share}"
    export XDG_STATE_HOME="''${XDG_STATE_HOME:-$HOME/.local/state}"
    export XDG_CACHE_HOME="''${XDG_CACHE_HOME:-$HOME/.cache}"
    export PATH="$HOME/.local/bin:$HOME/.nix-profile/bin:/nix/var/nix/profiles/default/bin:$PATH"

    top_level_home_dirs=(
      .hermes
      .config
      .local
      .cache
      .agent-browser
      .agents
      .codex
      .gemini
      .copilot
      .npm
      .bun
      .ssh
      .gnupg
      .pki
    )

    secure_home_dirs=(
      .ssh
      .gnupg
      .pki
    )

    ensure_dir() {
      local path="$1"
      local mode="$2"
      install -d -m "$mode" "$path"
      chown "$HERMES_UID:$HERMES_GID" "$path"
    }

    migrate_path_to_symlink() {
      local live_path="$1"
      local persisted_path="$2"

      ensure_dir "$(dirname "$persisted_path")" 0750

      if [ -L "$live_path" ]; then
        if [ "$(readlink -f "$live_path")" = "$persisted_path" ]; then
          return 0
        fi
        rm -f "$live_path"
      elif [ -d "$live_path" ]; then
        if [ ! -d "$persisted_path" ]; then
          mv "$live_path" "$persisted_path"
        else
          cp -a "$live_path"/. "$persisted_path"/
          rm -rf "$live_path"
        fi
      elif [ -f "$live_path" ]; then
        if [ ! -e "$persisted_path" ]; then
          mv "$live_path" "$persisted_path"
        else
          rm -f "$live_path"
        fi
      fi

      ln -sfn "$persisted_path" "$live_path"
      return 0
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
      local live_path persisted_path dir

      install -d -m 1777 /tmp
      ensure_dir "$GHOSTSHIP_DATA_ROOT" 0750
      ensure_dir "$HERMES_HOME" 0750
      ensure_dir "$GHOSTSHIP_HOME_ROOT" 0750
      ensure_dir "$GHOSTSHIP_WORKSPACE_ROOT" 0750
      ensure_dir "$HOME" 0750
      ensure_dir "$GHOSTSHIP_DASHBOARD_STATE_DIR" 0750

      for dir in "''${top_level_home_dirs[@]}"; do
        ensure_dir "$GHOSTSHIP_HOME_ROOT/$dir" 0750
        live_path="$HOME/$dir"
        persisted_path="$GHOSTSHIP_HOME_ROOT/$dir"
        migrate_path_to_symlink "$live_path" "$persisted_path"
      done

      for dir in "''${secure_home_dirs[@]}"; do
        chmod 0700 "$GHOSTSHIP_HOME_ROOT/$dir"
      done

      prepare_nix_profile_state
      ensure_dir "$XDG_CONFIG_HOME" 0750
      ensure_dir "$XDG_DATA_HOME" 0750
      ensure_dir "$XDG_STATE_HOME" 0750
      ensure_dir "$XDG_CACHE_HOME" 0750
      ensure_dir "$HOME/.local/bin" 0750
      ensure_dir "$HOME/.config/systemd/user" 0750

      chown -R "$HERMES_UID:$HERMES_GID" "$GHOSTSHIP_DASHBOARD_STATE_DIR" "$GHOSTSHIP_WORKSPACE_ROOT" "$HERMES_HOME" "$GHOSTSHIP_HOME_ROOT" >/dev/null 2>&1 || true
      chmod 0750 "$GHOSTSHIP_WORKSPACE_ROOT" "$HERMES_HOME" "$GHOSTSHIP_HOME_ROOT"
    }

    run_dashboard_controller() {
      exec python ${./dashboard-controller.py}
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
