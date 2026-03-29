{
  rsync,
  writeShellApplication,
  bash,
  coreutils,
  curl,
  ffmpeg,
  findutils,
  git,
  gnugrep,
  gnused,
  hermesRelease,
  nodejs_22,
  python311,
  tmux,
  ttyd,
  uv,
  util-linux,
}:
writeShellApplication {
  name = "ghostship-hermes-runtime";
  runtimeInputs = [
    bash
    coreutils
    curl
    ffmpeg
    findutils
    git
    gnugrep
    gnused
    nodejs_22
    rsync
    tmux
    ttyd
    uv
    util-linux
    python311
  ];
  text = ''
    set -euo pipefail

    ensure_runtime_prereqs() {
      export SSL_CERT_FILE="''${SSL_CERT_FILE:-/etc/ssl/certs/ca-bundle.crt}"
      export NIX_SSL_CERT_FILE="''${NIX_SSL_CERT_FILE:-$SSL_CERT_FILE}"

      tmp_dir="''${TMPDIR:-/tmp}"
      mkdir -p "$tmp_dir"
    }

    command_name="''${1:-}"
    shift || true

    case "$command_name" in
      bootstrap)
        ensure_runtime_prereqs
        export HOME="''${HOME:-/home/hermes}"
        export HERMES_HOME="''${HERMES_HOME:-$HOME/.hermes}"
        export GHOSTSHIP_HERMES_REF="''${GHOSTSHIP_HERMES_REF:-${hermesRelease}}"
        install_root="$HERMES_HOME/hermes-agent"
        release_marker="$HERMES_HOME/.ghostship-hermes-release"
        repo_url="''${GHOSTSHIP_HERMES_REPO:-https://github.com/NousResearch/hermes-agent.git}"
        tmp_root="$(TMPDIR="$tmp_dir" mktemp -d)"
        cleanup() {
          rm -rf "$tmp_root"
        }
        trap cleanup EXIT

        mkdir -p "$HOME" "$HERMES_HOME"
        mkdir -p "$HERMES_HOME/cron" "$HERMES_HOME/logs" "$HERMES_HOME/memories" "$HERMES_HOME/sessions" "$HERMES_HOME/skills"

        if [ -x "$install_root/venv/bin/hermes" ] && [ -f "$release_marker" ] && [ "$(tr -d '\n' < "$release_marker")" = "$GHOSTSHIP_HERMES_REF" ]; then
          exit 0
        fi

        rm -rf "$tmp_root/repo"
        git clone --depth 1 --branch "$GHOSTSHIP_HERMES_REF" --recurse-submodules "$repo_url" "$tmp_root/repo"
        cd "$tmp_root/repo"

        uv venv venv --python ${python311.interpreter}
        uv pip install --python "$tmp_root/repo/venv/bin/python" -e ".[all]"
        npm install

        if [ -f "$tmp_root/repo/cli-config.yaml.example" ] && [ ! -f "$HERMES_HOME/config.yaml" ]; then
          cp "$tmp_root/repo/cli-config.yaml.example" "$HERMES_HOME/config.yaml"
        fi

        if [ ! -f "$HERMES_HOME/.env" ]; then
          touch "$HERMES_HOME/.env"
        fi

        rm -rf "$install_root.new"
        mkdir -p "$install_root.new"
        rsync -a --delete "$tmp_root/repo/" "$install_root.new/"
        rm -rf "$install_root"
        mv "$install_root.new" "$install_root"
        printf '%s' "$GHOSTSHIP_HERMES_REF" > "$release_marker"
        ;;
      seed-skills)
        export HOME="''${HOME:-/home/hermes}"
        export HERMES_HOME="''${HERMES_HOME:-$HOME/.hermes}"
        source_dir="''${GHOSTSHIP_DEFAULT_SKILLS:-/share/ghostship-hermes/skills}"
        target_dir="$HERMES_HOME/skills"

        mkdir -p "$target_dir"
        if [ ! -d "$source_dir" ]; then
          exit 0
        fi

        while IFS= read -r skill_dir; do
          skill_name="$(basename "$skill_dir")"
          if [ ! -e "$target_dir/$skill_name" ]; then
            cp -R "$skill_dir" "$target_dir/$skill_name"
          fi
        done < <(find "$source_dir" -mindepth 1 -maxdepth 1 -type d | sort)
        ;;
      entrypoint)
        if [ "$(id -u)" -eq 0 ]; then
          install -d -m 1777 /tmp
          install -d -m 0755 -o 1000 -g 1000 /home/hermes
          install -d -m 0755 -o 1000 -g 1000 /home/hermes/.hermes
          install -d -m 0755 -o 1000 -g 1000 /nix
          exec setpriv --reuid=1000 --regid=1000 --clear-groups "$0" entrypoint-user "$@"
        fi
        exec "$0" entrypoint-user "$@"
        ;;
      entrypoint-user)
        ensure_runtime_prereqs
        export HOME="''${HOME:-/home/hermes}"
        export HERMES_HOME="''${HERMES_HOME:-$HOME/.hermes}"
        export TERMINAL_CWD="''${TERMINAL_CWD:-$HOME}"
        export PATH="$HERMES_HOME/hermes-agent/venv/bin:$HERMES_HOME/hermes-agent/node_modules/.bin:$PATH"

        "$0" bootstrap
        "$0" seed-skills

        session_name="''${TTYD_SESSION_NAME:-hermes}"
        title="''${TTYD_TITLE:-Hermes}"
        port="''${TTYD_PORT:-7681}"
        startup_command="cd \"$TERMINAL_CWD\" && exec env HOME=\"$HOME\" HERMES_HOME=\"$HERMES_HOME\" PATH=\"$PATH\" hermes"

        if ! tmux has-session -t "$session_name" 2>/dev/null; then
          tmux new-session -d -s "$session_name" "$startup_command"
        fi

        exec ttyd --writable -p "$port" -t "titleFixed=$title" tmux attach-session -t "$session_name"
        ;;
      *)
        printf 'usage: ghostship-hermes-runtime <bootstrap|seed-skills|entrypoint|entrypoint-user>\n' >&2
        exit 64
        ;;
    esac
  '';
}
