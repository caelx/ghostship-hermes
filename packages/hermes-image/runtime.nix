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

    hermes_has_credentials() {
      local key
      for key in \
        OPENROUTER_API_KEY \
        NOUS_API_KEY \
        GLM_API_KEY \
        KIMI_API_KEY \
        MINIMAX_API_KEY \
        MINIMAX_CN_API_KEY \
        COPILOT_GITHUB_TOKEN \
        GH_TOKEN \
        GITHUB_TOKEN \
        OPENAI_API_KEY \
        OPENAI_BASE_URL \
        HERMES_INFERENCE_PROVIDER \
        HERMES_MODEL
      do
        if [ -n "''${!key:-}" ]; then
          return 0
        fi
      done

      if [ -f "$HERMES_HOME/.env" ] && grep -Eq '^(OPENROUTER_API_KEY|NOUS_API_KEY|GLM_API_KEY|KIMI_API_KEY|MINIMAX_API_KEY|MINIMAX_CN_API_KEY|COPILOT_GITHUB_TOKEN|GH_TOKEN|GITHUB_TOKEN|OPENAI_API_KEY|OPENAI_BASE_URL|HERMES_INFERENCE_PROVIDER|HERMES_MODEL)=' "$HERMES_HOME/.env"; then
        return 0
      fi

      if [ -f "$HERMES_HOME/auth.json" ] && grep -Eq '"active_provider"[[:space:]]*:[[:space:]]*"[A-Za-z0-9-]+"' "$HERMES_HOME/auth.json"; then
        return 0
      fi

      return 1
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

        needs_reinstall=1
        if [ -x "$install_root/venv/bin/hermes" ] && [ -f "$release_marker" ] && [ "$(tr -d '\n' < "$release_marker")" = "$GHOSTSHIP_HERMES_REF" ]; then
          if grep -Fx "#!$install_root/venv/bin/python" "$install_root/venv/bin/hermes" >/dev/null 2>&1; then
            needs_reinstall=0
          fi
        fi

        if [ "$needs_reinstall" -eq 0 ]; then
          exit 0
        fi

        rm -rf "$tmp_root/repo"
        git clone --depth 1 --branch "$GHOSTSHIP_HERMES_REF" --recurse-submodules "$repo_url" "$tmp_root/repo"
        cd "$tmp_root/repo"

        rm -rf "$install_root.new"
        mkdir -p "$install_root.new"
        rsync -a --delete "$tmp_root/repo/" "$install_root.new/"
        rm -rf "$install_root"
        mv "$install_root.new" "$install_root"
        cd "$install_root"

        if [ -f "$install_root/cli-config.yaml.example" ] && [ ! -f "$HERMES_HOME/config.yaml" ]; then
          cp "$install_root/cli-config.yaml.example" "$HERMES_HOME/config.yaml"
        fi

        if [ ! -f "$HERMES_HOME/.env" ]; then
          touch "$HERMES_HOME/.env"
        fi

        rm -rf "$install_root/venv"
        uv venv venv --python ${python311.interpreter}
        uv build --wheel --out-dir "$tmp_root/dist" .
        uv pip install --python "$install_root/venv/bin/python" "$tmp_root/dist"/*.whl
        npm install

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
        startup_command="exec \"$0\" terminal-session"

        if ! tmux has-session -t "$session_name" 2>/dev/null; then
          tmux new-session -d -s "$session_name" "$startup_command"
        fi

        exec ttyd --writable -p "$port" -t "titleFixed=$title" tmux attach-session -t "$session_name"
        ;;
      terminal-session)
        ensure_runtime_prereqs
        export HOME="''${HOME:-/home/hermes}"
        export HERMES_HOME="''${HERMES_HOME:-$HOME/.hermes}"
        export TERMINAL_CWD="''${TERMINAL_CWD:-$HOME}"
        export PATH="$HERMES_HOME/hermes-agent/venv/bin:$HERMES_HOME/hermes-agent/node_modules/.bin:$PATH"

        if hermes_has_credentials; then
          cd "$TERMINAL_CWD"
          exec hermes chat
        fi

        printf 'Hermes is not configured yet; starting shell.\n' >&2
        cd "$TERMINAL_CWD"
        exec bash -l
        ;;
      *)
        printf 'usage: ghostship-hermes-runtime <bootstrap|seed-skills|entrypoint|entrypoint-user|terminal-session>\n' >&2
        exit 64
        ;;
    esac
  '';
}
