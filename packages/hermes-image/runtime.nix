{
  rsync,
  writeShellApplication,
  bash,
  caddy,
  coreutils,
  curl,
  diffutils,
  ffmpeg,
  findutils,
  git,
  gnugrep,
  gnused,
  hermesRelease,
  nodejs_22,
  python311,
  s6,
  tmux,
  ttyd,
  uv,
  util-linux,
}:
writeShellApplication {
  name = "ghostship-hermes-runtime";
  runtimeInputs = [
    bash
    caddy
    coreutils
    curl
    diffutils
    ffmpeg
    findutils
    git
    gnugrep
    gnused
    nodejs_22
    python311
    rsync
    s6
    tmux
    ttyd
    uv
    util-linux
  ];
  text = ''
    set -euo pipefail

    ensure_runtime_prereqs() {
      export HERMES_USER="''${HERMES_USER:-hermes}"
      export HERMES_UID="''${HERMES_UID:-3000}"
      export HERMES_GID="''${HERMES_GID:-3000}"
      export HOME="''${HOME:-/home/hermes}"
      export HERMES_HOME="''${HERMES_HOME:-$HOME/.hermes}"
      export TERMINAL_CWD="''${TERMINAL_CWD:-$HOME}"
      export SSL_CERT_FILE="''${SSL_CERT_FILE:-/etc/ssl/certs/ca-bundle.crt}"
      export NIX_SSL_CERT_FILE="''${NIX_SSL_CERT_FILE:-$SSL_CERT_FILE}"
      export GHOSTSHIP_HERMES_REF="''${GHOSTSHIP_HERMES_REF:-${hermesRelease}}"
      export GHOSTSHIP_DASHBOARD_DIR="''${GHOSTSHIP_DASHBOARD_DIR:-/usr/local/share/ghostship-hermes/dashboard}"
      export GHOSTSHIP_STATE_DIR="''${GHOSTSHIP_STATE_DIR:-/run/ghostship-hermes}"
      export GHOSTSHIP_SERVICES_DIR="$GHOSTSHIP_STATE_DIR/services"
      export GHOSTSHIP_WWW_DIR="$GHOSTSHIP_STATE_DIR/www"
      export GHOSTSHIP_API_DIR="$GHOSTSHIP_WWW_DIR/api"
      export GHOSTSHIP_CADDY_DIR="$GHOSTSHIP_STATE_DIR/caddy"
      export GHOSTSHIP_CADDY_CONFIG="$GHOSTSHIP_CADDY_DIR/Caddyfile"
      export GHOSTSHIP_PROFILE_PORTS="$GHOSTSHIP_STATE_DIR/profile-ports.tsv"
      export GHOSTSHIP_HONCHO_SHARED_DIR="''${GHOSTSHIP_HONCHO_SHARED_DIR:-$HERMES_HOME/shared/honcho}"
      export PATH="/usr/local/bin:$HERMES_HOME/hermes-agent/venv/bin:$HERMES_HOME/hermes-agent/node_modules/.bin:$PATH"

      tmp_dir="''${TMPDIR:-/tmp}"
      mkdir -p "$tmp_dir"
    }

    configure_runtime_identity() {
      local passwd_line group_line
      passwd_line="''${HERMES_USER}:x:''${HERMES_UID}:''${HERMES_GID}:Hermes:/home/''${HERMES_USER}:/bin/bash"
      group_line="''${HERMES_USER}:x:''${HERMES_GID}:"

      if [ -w /etc/passwd ]; then
        if grep -Eq "^''${HERMES_USER}:" /etc/passwd; then
          sed -i "s#^''${HERMES_USER}:x:[0-9][0-9]*:[0-9][0-9]*:.*#''${passwd_line}#" /etc/passwd
        else
          printf '%s\n' "$passwd_line" >> /etc/passwd
        fi
      fi

      if [ -w /etc/group ]; then
        if grep -Eq "^''${HERMES_USER}:" /etc/group; then
          sed -i "s#^''${HERMES_USER}:x:[0-9][0-9]*:#''${group_line}#" /etc/group
        else
          printf '%s\n' "$group_line" >> /etc/group
        fi
      fi
    }

    ensure_runtime_directories() {
      install -d -m 1777 /tmp
      install -d -m 0755 "$HOME" "$HERMES_HOME" "$HERMES_HOME/profiles" "$GHOSTSHIP_STATE_DIR" "$GHOSTSHIP_SERVICES_DIR" "$GHOSTSHIP_WWW_DIR" "$GHOSTSHIP_API_DIR" "$GHOSTSHIP_CADDY_DIR"
      touch "$GHOSTSHIP_API_DIR/profiles.json"
    }

    honcho_shared_has_content() {
      [ -d "$GHOSTSHIP_HONCHO_SHARED_DIR" ] || return 1
      if find "$GHOSTSHIP_HONCHO_SHARED_DIR" -mindepth 1 -print -quit | grep -q .; then
        return 0
      fi
      return 1
    }

    ensure_honcho_layout() {
      local compat_link="$HOME/.honcho"

      if [ -d "$compat_link" ] && [ ! -L "$compat_link" ]; then
        install -d -m 0755 "$GHOSTSHIP_HONCHO_SHARED_DIR"
        rsync -a "$compat_link/" "$GHOSTSHIP_HONCHO_SHARED_DIR/"
        rm -rf "$compat_link"
        ln -s "$GHOSTSHIP_HONCHO_SHARED_DIR" "$compat_link"
        return 0
      fi

      if [ -L "$compat_link" ]; then
        if [ "$(readlink -f "$compat_link")" = "$GHOSTSHIP_HONCHO_SHARED_DIR" ]; then
          return 0
        fi
        rm -f "$compat_link"
      fi

      if honcho_shared_has_content; then
        ln -s "$GHOSTSHIP_HONCHO_SHARED_DIR" "$compat_link"
      fi

      return 0
    }

    write_if_changed() {
      local target="$1"
      local tmp_file
      tmp_file="$(mktemp)"
      cat > "$tmp_file"
      if [ ! -f "$target" ] || ! cmp -s "$tmp_file" "$target"; then
        mv "$tmp_file" "$target"
        chmod 0644 "$target"
        return 0
      fi
      rm -f "$tmp_file"
      return 0
    }

    slugify_profile_name() {
      printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//'
    }

    profile_has_chat_credentials() {
      local profile_name="$1"
      local profile_home="$2"
      local key

      if [ "$profile_name" = "default" ]; then
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
      fi

      if [ -f "$profile_home/.env" ] && grep -Eq '^(OPENROUTER_API_KEY|NOUS_API_KEY|GLM_API_KEY|KIMI_API_KEY|MINIMAX_API_KEY|MINIMAX_CN_API_KEY|COPILOT_GITHUB_TOKEN|GH_TOKEN|GITHUB_TOKEN|OPENAI_API_KEY|OPENAI_BASE_URL|HERMES_INFERENCE_PROVIDER|HERMES_MODEL)=' "$profile_home/.env"; then
        return 0
      fi

      if [ -f "$profile_home/auth.json" ] && grep -Eq '"active_provider"[[:space:]]*:[[:space:]]*"[A-Za-z0-9-]+"' "$profile_home/auth.json"; then
        return 0
      fi

      return 1
    }

    profile_has_gateway_credentials() {
      local profile_name="$1"
      local profile_home="$2"
      local key

      if [ "$profile_name" = "default" ]; then
        for key in \
          TELEGRAM_BOT_TOKEN \
          DISCORD_BOT_TOKEN \
          SLACK_BOT_TOKEN \
          SLACK_APP_TOKEN \
          MATTERMOST_TOKEN \
          MATRIX_ACCESS_TOKEN \
          MATRIX_PASSWORD \
          WHATSAPP_ENABLED \
          WEBHOOK_ENABLED \
          API_SERVER_ENABLED \
          SIGNAL_ACCOUNT \
          EMAIL_PASSWORD \
          EMAIL_IMAP_HOST \
          EMAIL_SMTP_HOST \
          DINGTALK_CLIENT_ID \
          DINGTALK_CLIENT_SECRET
        do
          if [ -n "''${!key:-}" ]; then
            return 0
          fi
        done
      fi

      if [ -f "$profile_home/.env" ] && grep -Eq '^(TELEGRAM_BOT_TOKEN|DISCORD_BOT_TOKEN|SLACK_BOT_TOKEN|SLACK_APP_TOKEN|MATTERMOST_TOKEN|MATRIX_ACCESS_TOKEN|MATRIX_PASSWORD|WHATSAPP_ENABLED|WEBHOOK_ENABLED|API_SERVER_ENABLED|SIGNAL_ACCOUNT|EMAIL_PASSWORD|EMAIL_IMAP_HOST|EMAIL_SMTP_HOST|DINGTALK_CLIENT_ID|DINGTALK_CLIENT_SECRET)=' "$profile_home/.env"; then
        return 0
      fi

      return 1
    }

    enumerate_profiles() {
      local index=0
      local profile_dir
      local -a profile_dirs=()
      printf 'default\t%s\tdefault\t%s\ttrue\n' "$HERMES_HOME" "9000"
      if [ -d "$HERMES_HOME/profiles" ]; then
        mapfile -t profile_dirs < <(find "$HERMES_HOME/profiles" -mindepth 1 -maxdepth 1 -type d | sort)
        for profile_dir in "''${profile_dirs[@]}"; do
          index=$((index + 1))
          profile_name="$(basename "$profile_dir")"
          slug="$(slugify_profile_name "$profile_name")"
          printf '%s\t%s\t%s\t%s\tfalse\n' "$profile_name" "$profile_dir" "$slug" "$((9000 + index))"
        done
      fi
      return 0
    }

    render_ttyd_service() {
      local profile_name="$1"
      local profile_home="$2"
      local slug="$3"
      local port="$4"
      local service_dir="$GHOSTSHIP_SERVICES_DIR/profile-ttyd-$slug"
      local base_path="/profiles/$slug/"
      local run_file="$service_dir/run"

      install -d -m 0755 "$service_dir"
      write_if_changed "$run_file" <<EOF
#!/bin/bash
set -euo pipefail
exec setpriv --reuid $HERMES_UID --regid $HERMES_GID --clear-groups --inh-caps -all /usr/local/bin/ghostship-hermes-runtime ttyd-profile-service ''${profile_name@Q} ''${profile_home@Q} ''${port@Q} ''${base_path@Q}
EOF
      chmod 0755 "$run_file"
    }

    render_static_service() {
      local service_name="$1"
      local subcommand="$2"
      local service_dir="$GHOSTSHIP_SERVICES_DIR/$service_name"
      local run_file="$service_dir/run"

      install -d -m 0755 "$service_dir"
      write_if_changed "$run_file" <<EOF
#!/bin/bash
set -euo pipefail
exec /usr/local/bin/ghostship-hermes-runtime $subcommand
EOF
      chmod 0755 "$run_file"
    }

    render_static_services() {
      render_static_service "caddy" "caddy-service"
      render_static_service "reconciler" "profile-reconciler-loop"
    }

    render_gateway_service() {
      local profile_name="$1"
      local profile_home="$2"
      local slug="$3"
      local service_dir="$GHOSTSHIP_SERVICES_DIR/profile-gateway-$slug"
      local run_file="$service_dir/run"

      install -d -m 0755 "$service_dir"
      write_if_changed "$run_file" <<EOF
#!/bin/bash
set -euo pipefail
exec setpriv --reuid $HERMES_UID --regid $HERMES_GID --clear-groups --inh-caps -all /usr/local/bin/ghostship-hermes-runtime gateway-profile-loop ''${profile_name@Q} ''${profile_home@Q}
EOF
      chmod 0755 "$run_file"
    }

    remove_service_dir() {
      local service_dir="$1"
      if [ -d "$service_dir" ]; then
        s6-svc -d "$service_dir" >/dev/null 2>&1 || true
        rm -rf "$service_dir"
      fi
    }

    generate_manifest() {
      local entries_file="$1"
      python3 - "$entries_file" "$GHOSTSHIP_API_DIR/profiles.json" <<'PY'
import json
import pathlib
import sys

entries_path = pathlib.Path(sys.argv[1])
output_path = pathlib.Path(sys.argv[2])
profiles = []
for raw_line in entries_path.read_text(encoding="utf-8").splitlines():
    if not raw_line.strip():
        continue
    name, slug, is_default, terminal_path, gateway_expected, gateway_running = raw_line.split("\t")
    profiles.append(
        {
            "name": name,
            "slug": slug,
            "is_default": is_default == "true",
            "terminal_path": terminal_path,
            "gateway_expected": gateway_expected == "true",
            "gateway_running": gateway_running == "true",
        }
    )

output_path.write_text(
    json.dumps({"profiles": profiles}, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
    }

    generate_caddy_config() {
      local ports_file="$1"
      local tmp_file
      tmp_file="$(mktemp)"
      {
        printf '{\n'
        printf '  admin 127.0.0.1:2019\n'
        printf '  auto_https off\n'
        printf '}\n\n'
        printf ':7681 {\n'
        printf '  encode gzip zstd\n'
        printf '  header {\n'
        printf '    -X-Frame-Options\n'
        printf '  }\n\n'
        printf '  handle /api/* {\n'
        printf '    root * %s\n' "$GHOSTSHIP_WWW_DIR"
        printf '    file_server\n'
        printf '  }\n\n'

        while IFS=$'\t' read -r _profile_name slug port; do
          printf '  handle /profiles/%s/* {\n' "$slug"
          printf '    reverse_proxy 127.0.0.1:%s {\n' "$port"
          printf '      header_down -X-Frame-Options\n'
          printf '    }\n'
          printf '  }\n\n'
        done < "$ports_file"

        printf '  handle {\n'
        printf '    root * %s\n' "$GHOSTSHIP_DASHBOARD_DIR"
        printf '    try_files {path} /index.html\n'
        printf '    file_server\n'
        printf '  }\n'
        printf '}\n'
      } > "$tmp_file"

      if [ ! -f "$GHOSTSHIP_CADDY_CONFIG" ] || ! cmp -s "$tmp_file" "$GHOSTSHIP_CADDY_CONFIG"; then
        mv "$tmp_file" "$GHOSTSHIP_CADDY_CONFIG"
        chmod 0644 "$GHOSTSHIP_CADDY_CONFIG"
        caddy reload --address 127.0.0.1:2019 --config "$GHOSTSHIP_CADDY_CONFIG" --adapter caddyfile >/dev/null 2>&1 || true
      else
        rm -f "$tmp_file"
      fi
    }

    reconcile_profiles() {
      ensure_runtime_prereqs
      ensure_runtime_directories
      ensure_honcho_layout

      local entries_file desired_services_file
      entries_file="$(mktemp)"
      desired_services_file="$(mktemp)"
      : > "$GHOSTSHIP_PROFILE_PORTS"

      while IFS=$'\t' read -r profile_name profile_home slug port is_default; do
        local gateway_expected gateway_running
        render_ttyd_service "$profile_name" "$profile_home" "$slug" "$port"
        printf 'profile-ttyd-%s\n' "$slug" >> "$desired_services_file"
        printf '%s\t%s\t%s\n' "$profile_name" "$slug" "$port" >> "$GHOSTSHIP_PROFILE_PORTS"

        gateway_expected=false
        gateway_running=false
        if profile_has_gateway_credentials "$profile_name" "$profile_home"; then
          render_gateway_service "$profile_name" "$profile_home" "$slug"
          printf 'profile-gateway-%s\n' "$slug" >> "$desired_services_file"
          gateway_expected=true
          gateway_running=true
        else
          remove_service_dir "$GHOSTSHIP_SERVICES_DIR/profile-gateway-$slug"
        fi

        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$profile_name" "$slug" "$is_default" "/profiles/$slug/" "$gateway_expected" "$gateway_running" >> "$entries_file"
      done < <(enumerate_profiles)

      if [ -d "$GHOSTSHIP_SERVICES_DIR" ]; then
        while IFS= read -r service_dir; do
          service_name="$(basename "$service_dir")"
          if ! grep -Fxq "$service_name" "$desired_services_file"; then
            remove_service_dir "$service_dir"
          fi
        done < <(find "$GHOSTSHIP_SERVICES_DIR" -mindepth 1 -maxdepth 1 -type d -name 'profile-*' | sort)
      fi

      generate_manifest "$entries_file"
      generate_caddy_config "$GHOSTSHIP_PROFILE_PORTS"
      s6-svscanctl -a "$GHOSTSHIP_SERVICES_DIR" >/dev/null 2>&1 || true

      rm -f "$entries_file" "$desired_services_file"
    }

    run_profile_chat() {
      local profile_name="$1"
      local profile_home="$2"
      export HERMES_HOME="$profile_home"
      cd "$TERMINAL_CWD"

      if profile_has_chat_credentials "$profile_name" "$profile_home"; then
        exec hermes chat
      fi

      printf 'Hermes profile %s is not configured yet; starting shell.\n' "$profile_name" >&2
      exec bash -l
    }

    run_profile_gateway_loop() {
      local profile_name="$1"
      local profile_home="$2"
      export HERMES_HOME="$profile_home"

      while true; do
        if profile_has_gateway_credentials "$profile_name" "$profile_home"; then
          cd "$profile_home"
          hermes gateway run --replace
          rc="$?"
          printf 'Hermes gateway for %s exited with %s; retrying in 5s.\n' "$profile_name" "$rc" >&2
          sleep 5
        else
          sleep 15
        fi
      done
    }

    command_name="''${1:-}"
    shift || true

    case "$command_name" in
      bootstrap)
        ensure_runtime_prereqs
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
        ensure_runtime_prereqs
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
      prepare-runtime)
      ensure_runtime_prereqs
      configure_runtime_identity
      ensure_runtime_directories
      ensure_honcho_layout
      render_static_services
      reconcile_profiles
      ;;
      entrypoint)
        ensure_runtime_prereqs
        configure_runtime_identity
        if [ "$(id -u)" -eq 0 ]; then
          install -d -m 1777 /tmp
          install -d -m 0755 -o "$HERMES_UID" -g "$HERMES_GID" "$HOME" "$HERMES_HOME" /nix
          "$0" bootstrap
          "$0" seed-skills
          ensure_honcho_layout
          chown -R "$HERMES_UID:$HERMES_GID" "$HOME"
          "$0" prepare-runtime
          exec s6-svscan "$GHOSTSHIP_SERVICES_DIR"
        fi
        "$0" prepare-runtime
        exec s6-svscan "$GHOSTSHIP_SERVICES_DIR"
        ;;
      caddy-service)
        ensure_runtime_prereqs
        ensure_runtime_directories
        if [ ! -f "$GHOSTSHIP_CADDY_CONFIG" ]; then
          reconcile_profiles
        fi
        if [ "$(id -u)" -eq 0 ]; then
          exec setpriv --reuid "$HERMES_UID" --regid "$HERMES_GID" --clear-groups --inh-caps -all caddy run --config "$GHOSTSHIP_CADDY_CONFIG" --adapter caddyfile
        fi
        exec caddy run --config "$GHOSTSHIP_CADDY_CONFIG" --adapter caddyfile
        ;;
      profile-reconciler-loop)
        ensure_runtime_prereqs
        ensure_runtime_directories
        while true; do
          reconcile_profiles
          sleep 5
        done
        ;;
      ttyd-profile-service)
        ensure_runtime_prereqs
        profile_name="''${1:?missing profile name}"
        profile_home="''${2:?missing profile home}"
        port="''${3:?missing port}"
        base_path="''${4:?missing base path}"
        export HERMES_HOME="$profile_home"
        title="Hermes: $profile_name"
        exec ttyd --writable -i 127.0.0.1 -p "$port" --base-path "$base_path" -t "titleFixed=$title" /usr/local/bin/ghostship-hermes-runtime terminal-profile-session "$profile_name" "$profile_home"
        ;;
      terminal-profile-session)
        ensure_runtime_prereqs
        profile_name="''${1:?missing profile name}"
        profile_home="''${2:?missing profile home}"
        run_profile_chat "$profile_name" "$profile_home"
        ;;
      gateway-profile-loop)
        ensure_runtime_prereqs
        profile_name="''${1:?missing profile name}"
        profile_home="''${2:?missing profile home}"
        run_profile_gateway_loop "$profile_name" "$profile_home"
        ;;
      *)
        printf 'usage: ghostship-hermes-runtime <bootstrap|seed-skills|prepare-runtime|entrypoint|caddy-service|profile-reconciler-loop|ttyd-profile-service|terminal-profile-session|gateway-profile-loop>\n' >&2
        exit 64
        ;;
    esac
  '';
}
