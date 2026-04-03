{
  rsync,
  writeShellApplication,
  bash,
  caddy,
  coreutils,
  curl,
  dbus,
  diffutils,
  ffmpeg,
  findutils,
  git,
  gawk,
  gnugrep,
  gnused,
  hermesRelease,
  jq,
  nodejs_22,
  python311,
  systemd,
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
    dbus
    diffutils
    ffmpeg
    findutils
    git
    gawk
    gnugrep
    gnused
    jq
    nodejs_22
    python311
    rsync
    systemd
    tmux
    ttyd
    uv
    util-linux
  ];
  text = ''
    set -euo pipefail

    log_info() {
      printf 'info: %s\n' "$1" >&2
    }

    log_warn() {
      printf 'warn: %s\n' "$1" >&2
    }

    ensure_runtime_prereqs() {
      export HERMES_USER="''${HERMES_USER:-hermes}"
      export HERMES_UID="''${HERMES_UID:-3000}"
      export HERMES_GID="''${HERMES_GID:-3000}"
      export HOME="''${HOME:-/home/hermes}"
      export GHOSTSHIP_DATA_ROOT="''${GHOSTSHIP_DATA_ROOT:-/opt/data}"
      export GHOSTSHIP_HOME_ROOT="''${GHOSTSHIP_HOME_ROOT:-$GHOSTSHIP_DATA_ROOT/home}"
      export GHOSTSHIP_WORKSPACE_ROOT="''${GHOSTSHIP_WORKSPACE_ROOT:-/workspace}"
      export HERMES_HOME="''${HERMES_HOME:-$GHOSTSHIP_DATA_ROOT}"
      export XDG_CONFIG_HOME="''${XDG_CONFIG_HOME:-$HOME/.config}"
      export XDG_DATA_HOME="''${XDG_DATA_HOME:-$HOME/.local/share}"
      export XDG_STATE_HOME="''${XDG_STATE_HOME:-$HOME/.local/state}"
      export XDG_CACHE_HOME="''${XDG_CACHE_HOME:-$HOME/.cache}"
      export XDG_RUNTIME_DIR="''${XDG_RUNTIME_DIR:-/run/user/$HERMES_UID}"
      export FEED_DB_PATH="''${FEED_DB_PATH:-$HERMES_HOME/feed/feed.db}"
      export TERMINAL_CWD="''${TERMINAL_CWD:-$GHOSTSHIP_WORKSPACE_ROOT}"
      export SSL_CERT_FILE="''${SSL_CERT_FILE:-/etc/ssl/certs/ca-bundle.crt}"
      export NIX_SSL_CERT_FILE="''${NIX_SSL_CERT_FILE:-$SSL_CERT_FILE}"
      export GHOSTSHIP_HERMES_REF="''${GHOSTSHIP_HERMES_REF:-${hermesRelease}}"
      export GHOSTSHIP_DEFAULT_SKILLS="''${GHOSTSHIP_DEFAULT_SKILLS:-/usr/local/share/ghostship-hermes/skills}"
      export GHOSTSHIP_WORKSTATION_SEED="''${GHOSTSHIP_WORKSTATION_SEED:-/usr/local/share/ghostship-hermes/workstation-seed}"
      export GHOSTSHIP_DASHBOARD_DIR="''${GHOSTSHIP_DASHBOARD_DIR:-/usr/local/share/ghostship-hermes/dashboard}"
      export GHOSTSHIP_WORKSTATION_DIR="''${GHOSTSHIP_WORKSTATION_DIR:-$XDG_DATA_HOME/ghostship-hermes}"
      export GHOSTSHIP_APPS_DIR="$GHOSTSHIP_WORKSTATION_DIR/apps"
      export GHOSTSHIP_CURRENT_DIR="$GHOSTSHIP_WORKSTATION_DIR/current"
      export GHOSTSHIP_SEED_CACHE_DIR="$GHOSTSHIP_WORKSTATION_DIR/seed-cache"
      export GHOSTSHIP_SYSTEMD_MANAGED_DIR="$GHOSTSHIP_WORKSTATION_DIR/systemd/user"
      export GHOSTSHIP_RUNTIME_STATE_DIR="''${GHOSTSHIP_RUNTIME_STATE_DIR:-$XDG_STATE_HOME/ghostship-hermes/runtime}"
      export GHOSTSHIP_WWW_DIR="$GHOSTSHIP_RUNTIME_STATE_DIR/www"
      export GHOSTSHIP_API_DIR="$GHOSTSHIP_WWW_DIR/api"
      export GHOSTSHIP_CADDY_DIR="$GHOSTSHIP_RUNTIME_STATE_DIR/caddy"
      export GHOSTSHIP_CADDY_CONFIG="$GHOSTSHIP_CADDY_DIR/Caddyfile"
      export GHOSTSHIP_PROFILE_PORTS="$GHOSTSHIP_RUNTIME_STATE_DIR/profile-ports.tsv"
      export GHOSTSHIP_GENERATED_UNITS_DIR="$GHOSTSHIP_SYSTEMD_MANAGED_DIR/generated"
      export GHOSTSHIP_APP_STATE_DIR="$XDG_STATE_HOME/ghostship-hermes/apps"
      export GHOSTSHIP_OPENCODE_STATE_DIR="$XDG_STATE_HOME/opencode"
      export GHOSTSHIP_HONCHO_SHARED_DIR="''${GHOSTSHIP_HONCHO_SHARED_DIR:-$HERMES_HOME/shared/honcho}"
      export GHOSTSHIP_HOME_HERMES_DIR="$GHOSTSHIP_HOME_ROOT/.hermes"
      export GHOSTSHIP_HOME_CONFIG_DIR="$GHOSTSHIP_HOME_ROOT/.config"
      export GHOSTSHIP_HOME_LOCAL_DIR="$GHOSTSHIP_HOME_ROOT/.local"
      export GHOSTSHIP_HOME_CACHE_DIR="$GHOSTSHIP_HOME_ROOT/.cache"
      export GHOSTSHIP_HOME_AGENTS_DIR="$GHOSTSHIP_HOME_ROOT/.agents"
      export GHOSTSHIP_HOME_CODEX_DIR="$GHOSTSHIP_HOME_ROOT/.codex"
      export GHOSTSHIP_HOME_GEMINI_DIR="$GHOSTSHIP_HOME_ROOT/.gemini"
      export GHOSTSHIP_HOME_OPENCODE_DIR="$GHOSTSHIP_HOME_ROOT/.opencode"
      export GHOSTSHIP_SYSTEMCTL_BIN="${systemd}/bin/systemctl"
      export GHOSTSHIP_SYSTEMD_USER_BIN="${systemd}/lib/systemd/systemd"
      export PATH="$HOME/.local/bin:$HOME/.nix-profile/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:$HERMES_HOME/hermes-agent/venv/bin:$HERMES_HOME/hermes-agent/node_modules/.bin:$PATH"

      tmp_dir="''${TMPDIR:-/tmp}"
      mkdir -p "$tmp_dir"
    }

    configure_runtime_identity() {
      local passwd_line group_line
      passwd_line="''${HERMES_USER}:x:''${HERMES_UID}:''${HERMES_GID}:Hermes:$HOME:/bin/bash"
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

    persist_missing_dir_contents() {
      local source_dir="$1"
      local dest_dir="$2"
      [ -d "$source_dir" ] || return 0
      mkdir -p "$dest_dir"
      rsync -a --ignore-existing "$source_dir"/ "$dest_dir"/
      chmod -R u+rwX "$dest_dir"
      return 0
    }

    persist_missing_file() {
      local source_file="$1"
      local dest_file="$2"
      [ -f "$source_file" ] || return 0
      mkdir -p "$(dirname "$dest_file")"
      if [ ! -e "$dest_file" ]; then
        cp "$source_file" "$dest_file"
        chmod u+rw "$dest_file"
      else
        log_warn "preserving existing persisted file at $dest_file"
      fi
      return 0
    }

    migrate_home_path_to_symlink() {
      local live_path="$1"
      local persisted_path="$2"

      mkdir -p "$(dirname "$persisted_path")"

      if [ -L "$live_path" ]; then
        if [ "$(readlink -f "$live_path")" = "$persisted_path" ]; then
          return 0
        fi
        rm -f "$live_path"
      elif [ -d "$live_path" ]; then
        persist_missing_dir_contents "$live_path" "$persisted_path"
        rm -rf "$live_path"
      elif [ -f "$live_path" ]; then
        persist_missing_file "$live_path" "$persisted_path"
        rm -f "$live_path"
      fi

      ln -sfn "$persisted_path" "$live_path"
      return 0
    }

    prepare_persisted_layout() {
      install -d -m 1777 /tmp
      install -d -m 0755 \
        "$HOME" \
        "$GHOSTSHIP_DATA_ROOT" \
        "$GHOSTSHIP_HOME_ROOT" \
        "$GHOSTSHIP_WORKSPACE_ROOT" \
        "$HERMES_HOME" \
        "$HERMES_HOME/feed" \
        "$HERMES_HOME/cron" \
        "$HERMES_HOME/logs" \
        "$HERMES_HOME/memories" \
        "$HERMES_HOME/sessions" \
        "$HERMES_HOME/skills" \
        "$GHOSTSHIP_HOME_HERMES_DIR" \
        "$GHOSTSHIP_HOME_CONFIG_DIR" \
        "$GHOSTSHIP_HOME_LOCAL_DIR" \
        "$GHOSTSHIP_HOME_CACHE_DIR" \
        "$GHOSTSHIP_HOME_AGENTS_DIR" \
        "$GHOSTSHIP_HOME_CODEX_DIR" \
        "$GHOSTSHIP_HOME_GEMINI_DIR" \
        "$GHOSTSHIP_HOME_OPENCODE_DIR"
      
      migrate_home_path_to_symlink "$HOME/.hermes" "$GHOSTSHIP_HOME_HERMES_DIR"
      migrate_home_path_to_symlink "$HOME/.config" "$GHOSTSHIP_HOME_CONFIG_DIR"
      migrate_home_path_to_symlink "$HOME/.local" "$GHOSTSHIP_HOME_LOCAL_DIR"
      migrate_home_path_to_symlink "$HOME/.cache" "$GHOSTSHIP_HOME_CACHE_DIR"
      migrate_home_path_to_symlink "$HOME/.agents" "$GHOSTSHIP_HOME_AGENTS_DIR"
      migrate_home_path_to_symlink "$HOME/.codex" "$GHOSTSHIP_HOME_CODEX_DIR"
      migrate_home_path_to_symlink "$HOME/.gemini" "$GHOSTSHIP_HOME_GEMINI_DIR"
      migrate_home_path_to_symlink "$HOME/.opencode" "$GHOSTSHIP_HOME_OPENCODE_DIR"
      migrate_home_path_to_symlink "$HOME/workspace" "$GHOSTSHIP_WORKSPACE_ROOT"
      return 0
    }

    prepare_nix_profile_state() {
      local profile_root gc_root per_user_root
      profile_root="/nix/var/nix/profiles/per-user/$HERMES_USER"
      gc_root="/nix/var/nix/gcroots/per-user/$HERMES_USER"
      per_user_root="/nix/var/nix/profiles/per-user"

      install -d -m 0755 "$per_user_root" >/dev/null 2>&1 || true
      install -d -m 0755 "$profile_root" "$gc_root" >/dev/null 2>&1 || true
      chown -R "$HERMES_UID:$HERMES_GID" "$profile_root" "$gc_root" >/dev/null 2>&1 || true
      return 0
    }

    ensure_runtime_directories() {
      prepare_persisted_layout
      install -d -m 0755 \
        "$XDG_CONFIG_HOME" \
        "$XDG_DATA_HOME" \
        "$XDG_STATE_HOME" \
        "$XDG_CACHE_HOME" \
        "$HOME/.local/bin" \
        "$HOME/.config/systemd/user/default.target.wants" \
        "$HOME/.config/systemd/user/timers.target.wants" \
        "$GHOSTSHIP_WORKSTATION_DIR" \
        "$GHOSTSHIP_APPS_DIR" \
        "$GHOSTSHIP_CURRENT_DIR" \
        "$GHOSTSHIP_SEED_CACHE_DIR" \
        "$GHOSTSHIP_SYSTEMD_MANAGED_DIR" \
        "$GHOSTSHIP_GENERATED_UNITS_DIR" \
        "$GHOSTSHIP_APP_STATE_DIR" \
        "$GHOSTSHIP_OPENCODE_STATE_DIR" \
        "$GHOSTSHIP_RUNTIME_STATE_DIR" \
        "$GHOSTSHIP_WWW_DIR" \
        "$GHOSTSHIP_API_DIR" \
        "$GHOSTSHIP_CADDY_DIR" \
        "$XDG_RUNTIME_DIR"
      chmod 0700 "$XDG_RUNTIME_DIR"
      prepare_nix_profile_state
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

    enumerate_profiles() {
      local index=0
      local profile_dir profile_name slug
      local -a profile_dirs=()
      printf 'default\t%s\tdefault\t%s\ttrue\n' "$HERMES_HOME" "9000"
      if [ -d "$HOME/.hermes/profiles" ]; then
        mapfile -t profile_dirs < <(find "$HOME/.hermes/profiles" -mindepth 1 -maxdepth 1 -type d | sort)
        for profile_dir in "''${profile_dirs[@]}"; do
          index=$((index + 1))
          profile_name="$(basename "$profile_dir")"
          slug="$(slugify_profile_name "$profile_name")"
          printf '%s\t%s\t%s\t%s\tfalse\n' "$profile_name" "$profile_dir" "$slug" "$((9000 + index))"
        done
      fi
      return 0
    }

    copy_missing_children() {
      local source_dir="$1"
      local target_dir="$2"
      local entry_name

      [ -d "$source_dir" ] || return 0
      mkdir -p "$target_dir"
      while IFS= read -r entry_name; do
        [ -n "$entry_name" ] || continue
        if [ ! -e "$target_dir/$entry_name" ]; then
          cp -R "$source_dir/$entry_name" "$target_dir/$entry_name"
          chmod -R u+rwX "$target_dir/$entry_name"
        fi
      done < <(find "$source_dir" -mindepth 1 -maxdepth 1 -printf '%f\n' | sort)
      return 0
    }

    copy_file_if_missing() {
      local source_file="$1"
      local target_file="$2"
      mkdir -p "$(dirname "$target_file")"
      if [ ! -e "$target_file" ]; then
        cp "$source_file" "$target_file"
        chmod u+rw "$target_file"
      fi
      return 0
    }

    strip_marked_block() {
      local file="$1"
      local begin="$2"
      local end="$3"
      local tmp_file

      [ -f "$file" ] || return 0
      tmp_file="$(mktemp)"
      awk -v begin="$begin" -v end="$end" '
        $0 == begin { skipping = 1; next }
        $0 == end { skipping = 0; next }
        !skipping { print }
      ' "$file" > "$tmp_file"
      mv "$tmp_file" "$file"
      return 0
    }

    append_markdown_override() {
      local source_file="$1"
      local target_file="$2"
      local block_id="$3"
      local begin end tmp_file

      [ -f "$source_file" ] || return 0
      [ -f "$target_file" ] || return 0

      begin="<!-- ghostship:$block_id:begin -->"
      end="<!-- ghostship:$block_id:end -->"
      strip_marked_block "$target_file" "$begin" "$end"

      tmp_file="$(mktemp)"
      {
        cat "$target_file"
        printf '\n%s\n' "$begin"
        cat "$source_file"
        printf '%s\n' "$end"
      } > "$tmp_file"
      mv "$tmp_file" "$target_file"
      return 0
    }

    insert_toml_prompt_override() {
      local source_file="$1"
      local target_file="$2"
      local block_id="$3"
      local begin end tmp_file

      [ -f "$source_file" ] || return 0
      [ -f "$target_file" ] || return 0

      begin="<!-- ghostship:$block_id:begin -->"
      end="<!-- ghostship:$block_id:end -->"
      strip_marked_block "$target_file" "$begin" "$end"

      tmp_file="$(mktemp)"
      awk -v begin="$begin" -v end="$end" -v src="$source_file" '
        { lines[++count] = $0 }
        END {
          if (count == 0) {
            exit 0
          }

          inserted = 0
          for (index = 1; index <= count; index++) {
            if (!inserted && index == count && lines[index] == "\"\"\"") {
              print ""
              print begin
              while ((getline line < src) > 0) print line
              close(src)
              print end
              print lines[index]
              inserted = 1
            } else {
              print lines[index]
            }
          }

          if (!inserted) {
            print ""
            print begin
            while ((getline line < src) > 0) print line
            close(src)
            print end
          }
        }
      ' "$target_file" > "$tmp_file"
      mv "$tmp_file" "$target_file"
      return 0
    }

    create_openspec_override_file() {
      local key="$1"
      local tmp_file

      tmp_file="$(mktemp)"
      case "$key" in
        propose)
          cat > "$tmp_file" <<'EOF'
## Ghostship Override

- Before `openspec new change`, use `using-git-worktrees` if it is available.
- Create or reuse `.worktree/<name>/`.
- Run the change creation and artifact generation flow from that worktree, not from `main`.
EOF
          ;;
        apply)
          cat > "$tmp_file" <<'EOF'
## Ghostship Override

- If implementation gets stuck on a bug, failing test, or unexpected behavior, use `systematic-debugging` if it is available.
- Do root-cause-first debugging before proposing or applying fixes.
EOF
          ;;
        archive)
          cat > "$tmp_file" <<'EOF'
## Ghostship Override

- Before archive, commit the change branch and fast-forward merge it back into `main`.
- Run the archive flow from the main worktree after that merge.
- After archive succeeds, delete the change worktree with `git worktree remove <worktree-path>`.
EOF
          ;;
        *)
          rm -f "$tmp_file"
          return 1
          ;;
      esac

      printf '%s\n' "$tmp_file"
      return 0
    }

    apply_ghostship_openspec_overrides() {
      local project_root="$1"
      local propose_override apply_override archive_override tool_dir

      [ -d "$project_root/openspec" ] || return 0

      propose_override="$(create_openspec_override_file propose)"
      apply_override="$(create_openspec_override_file apply)"
      archive_override="$(create_openspec_override_file archive)"

      for tool_dir in .codex .gemini .opencode; do
        append_markdown_override \
          "$propose_override" \
          "$project_root/$tool_dir/skills/openspec-propose/SKILL.md" \
          "$tool_dir-openspec-propose"
        append_markdown_override \
          "$apply_override" \
          "$project_root/$tool_dir/skills/openspec-apply-change/SKILL.md" \
          "$tool_dir-openspec-apply-change"
        append_markdown_override \
          "$archive_override" \
          "$project_root/$tool_dir/skills/openspec-archive-change/SKILL.md" \
          "$tool_dir-openspec-archive-change"
      done

      if [ -d "$project_root/.gemini/commands/opsx" ]; then
        insert_toml_prompt_override \
          "$propose_override" \
          "$project_root/.gemini/commands/opsx/propose.toml" \
          "gemini-opsx-propose"
        insert_toml_prompt_override \
          "$apply_override" \
          "$project_root/.gemini/commands/opsx/apply.toml" \
          "gemini-opsx-apply"
        insert_toml_prompt_override \
          "$archive_override" \
          "$project_root/.gemini/commands/opsx/archive.toml" \
          "gemini-opsx-archive"
      fi

      if [ -d "$project_root/.opencode/command" ]; then
        append_markdown_override \
          "$propose_override" \
          "$project_root/.opencode/command/opsx-propose.md" \
          "opencode-opsx-propose"
        append_markdown_override \
          "$apply_override" \
          "$project_root/.opencode/command/opsx-apply.md" \
          "opencode-opsx-apply"
        append_markdown_override \
          "$archive_override" \
          "$project_root/.opencode/command/opsx-archive.md" \
          "opencode-opsx-archive"
      fi

      rm -f "$propose_override" "$apply_override" "$archive_override"
      return 0
    }

    managed_target_is_live() {
      local target="$1"
      [ -L "$target" ] || return 1
      case "$(readlink -f "$target")" in
        "$GHOSTSHIP_SYSTEMD_MANAGED_DIR"/*) return 0 ;;
      esac
      return 1
    }

    generated_target_is_live() {
      local target="$1"
      [ -L "$target" ] || return 1
      case "$(readlink -f "$target")" in
        "$GHOSTSHIP_GENERATED_UNITS_DIR"/*) return 0 ;;
      esac
      return 1
    }

    install_managed_user_unit() {
      local unit_name="$1"
      local source_file="$GHOSTSHIP_WORKSTATION_SEED/.config/systemd/user/$unit_name"
      local managed_file="$GHOSTSHIP_SYSTEMD_MANAGED_DIR/$unit_name"
      local live_file="$HOME/.config/systemd/user/$unit_name"

      [ -f "$source_file" ] || return 0
      mkdir -p "$GHOSTSHIP_SYSTEMD_MANAGED_DIR" "$HOME/.config/systemd/user"
      cp "$source_file" "$managed_file"
      chmod u+rw "$managed_file"

      if [ ! -e "$live_file" ] || managed_target_is_live "$live_file"; then
        ln -sfn "$managed_file" "$live_file"
      fi
      return 0
    }

    enable_user_unit() {
      local unit_name="$1"
      local wants_dir="$2"
      local live_file="$HOME/.config/systemd/user/$unit_name"

      mkdir -p "$wants_dir"
      if [ -e "$live_file" ]; then
        ln -sfn "$live_file" "$wants_dir/$unit_name"
      fi
      return 0
    }

    install_managed_user_units() {
      local unit_name

      while IFS= read -r unit_name; do
        [ -n "$unit_name" ] || continue
        install_managed_user_unit "$unit_name"
      done < <(find "$GHOSTSHIP_WORKSTATION_SEED/.config/systemd/user" -mindepth 1 -maxdepth 1 -type f -printf '%f\n' | sort)

      enable_user_unit "ghostship-workstation-bootstrap.service" "$HOME/.config/systemd/user/default.target.wants"
      enable_user_unit "ghostship-caddy.service" "$HOME/.config/systemd/user/default.target.wants"
      enable_user_unit "ghostship-profile-reconciler.service" "$HOME/.config/systemd/user/default.target.wants"
      enable_user_unit "ghostship-app-update.timer" "$HOME/.config/systemd/user/timers.target.wants"
      enable_user_unit "ghostship-asset-refresh.timer" "$HOME/.config/systemd/user/timers.target.wants"
      enable_user_unit "ghostship-opencode-model-refresh.timer" "$HOME/.config/systemd/user/timers.target.wants"
      return 0
    }

    seed_workstation() {
      ensure_runtime_prereqs
      ensure_runtime_directories
      ensure_honcho_layout

      if [ ! -d "$GHOSTSHIP_WORKSTATION_SEED" ]; then
        return 0
      fi

      copy_missing_children "$GHOSTSHIP_WORKSTATION_SEED/.agents/skills" "$HOME/.agents/skills"
      copy_missing_children "$GHOSTSHIP_WORKSTATION_SEED/.codex/skills" "$HOME/.codex/skills"
      copy_missing_children "$GHOSTSHIP_WORKSTATION_SEED/.gemini/commands" "$HOME/.gemini/commands"
      copy_missing_children "$GHOSTSHIP_WORKSTATION_SEED/.gemini/skills" "$HOME/.gemini/skills"
      copy_missing_children "$GHOSTSHIP_WORKSTATION_SEED/.opencode/command" "$HOME/.opencode/command"
      copy_missing_children "$GHOSTSHIP_WORKSTATION_SEED/.opencode/skills" "$HOME/.opencode/skills"

      copy_file_if_missing "$GHOSTSHIP_WORKSTATION_SEED/.agents/AGENTS.md" "$HOME/.agents/AGENTS.md"
      copy_file_if_missing "$GHOSTSHIP_WORKSTATION_SEED/.config/codex/config.toml" "$XDG_CONFIG_HOME/codex/config.toml"
      copy_file_if_missing "$GHOSTSHIP_WORKSTATION_SEED/.config/gemini-cli/settings.json" "$XDG_CONFIG_HOME/gemini-cli/settings.json"
      copy_file_if_missing "$GHOSTSHIP_WORKSTATION_SEED/.config/opencode/opencode.json" "$XDG_CONFIG_HOME/opencode/opencode.json"

      mkdir -p "$HOME/.codex"
      if [ ! -e "$HOME/.codex/AGENTS.md" ] || [ -L "$HOME/.codex/AGENTS.md" ]; then
        ln -sfn "$HOME/.agents/AGENTS.md" "$HOME/.codex/AGENTS.md"
      fi

      mkdir -p "$GHOSTSHIP_SEED_CACHE_DIR/current"
      rsync -a --delete "$GHOSTSHIP_WORKSTATION_SEED/" "$GHOSTSHIP_SEED_CACHE_DIR/current/"
      chmod -R u+rwX "$GHOSTSHIP_SEED_CACHE_DIR/current"
      install_managed_user_units
      return 0
    }

    seed_hermes_skills() {
      ensure_runtime_prereqs
      local skill_dir skill_name
      mkdir -p "$HERMES_HOME/skills"
      [ -d "$GHOSTSHIP_DEFAULT_SKILLS" ] || return 0
      while IFS= read -r skill_dir; do
        skill_name="$(basename "$skill_dir")"
        if [ ! -e "$HERMES_HOME/skills/$skill_name" ]; then
          cp -R "$skill_dir" "$HERMES_HOME/skills/$skill_name"
          chmod -R u+rwX "$HERMES_HOME/skills/$skill_name"
        fi
      done < <(find "$GHOSTSHIP_DEFAULT_SKILLS" -mindepth 1 -maxdepth 1 -type d | sort)
      return 0
    }

    bootstrap_hermes() {
      ensure_runtime_prereqs
      local install_root release_marker repo_url tmp_root needs_reinstall
      install_root="$HERMES_HOME/hermes-agent"
      release_marker="$HERMES_HOME/.ghostship-hermes-release"
      repo_url="''${GHOSTSHIP_HERMES_REPO:-https://github.com/NousResearch/hermes-agent.git}"
      tmp_root="$(TMPDIR="$tmp_dir" mktemp -d)"

      cleanup_bootstrap() {
        rm -rf "$tmp_root"
      }
      trap cleanup_bootstrap EXIT

      mkdir -p "$HOME" "$HERMES_HOME" "$HERMES_HOME/cron" "$HERMES_HOME/logs" "$HERMES_HOME/memories" "$HERMES_HOME/sessions" "$HERMES_HOME/skills"
      mkdir -p "$HOME/.local/bin"

      needs_reinstall=1
      if [ -x "$install_root/venv/bin/hermes" ] && [ -f "$release_marker" ] && [ "$(tr -d '\n' < "$release_marker")" = "$GHOSTSHIP_HERMES_REF" ]; then
        if grep -Fx "#!$install_root/venv/bin/python" "$install_root/venv/bin/hermes" >/dev/null 2>&1; then
          needs_reinstall=0
        fi
      fi

      if [ "$needs_reinstall" -eq 0 ]; then
        ln -sfn "$install_root/venv/bin/hermes" "$HOME/.local/bin/hermes"
        trap - EXIT
        cleanup_bootstrap
        return 0
      fi

      log_info "bootstrapping Hermes $GHOSTSHIP_HERMES_REF"
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

      if [ -f "$install_root/docker/SOUL.md" ] && [ ! -f "$HERMES_HOME/SOUL.md" ]; then
        cp "$install_root/docker/SOUL.md" "$HERMES_HOME/SOUL.md"
      fi

      rm -rf "$install_root/venv"
      uv venv venv --python ${python311.interpreter}
      uv build --wheel --out-dir "$tmp_root/dist" .
      uv pip install --python "$install_root/venv/bin/python" "$tmp_root/dist"/*.whl
      npm install

      printf '%s' "$GHOSTSHIP_HERMES_REF" > "$release_marker"
      ln -sfn "$install_root/venv/bin/hermes" "$HOME/.local/bin/hermes"
      trap - EXIT
      cleanup_bootstrap
      return 0
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
      return 0
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
      return 0
    }

    render_ttyd_unit() {
      local profile_name="$1"
      local profile_home="$2"
      local slug="$3"
      local port="$4"
      local base_path="/profiles/$slug/"
      local unit_file="$GHOSTSHIP_GENERATED_UNITS_DIR/ghostship-profile-ttyd-$slug.service"

      write_if_changed "$unit_file" <<EOF
[Unit]
Description=ghostship-hermes terminal for profile $profile_name
After=ghostship-caddy.service

[Service]
Type=simple
ExecStart=/usr/local/bin/ghostship-hermes-runtime ttyd-profile-service ''${profile_name@Q} ''${profile_home@Q} ''${port@Q} ''${base_path@Q}
Restart=always
RestartSec=2s
EOF
      return 0
    }

    install_generated_user_unit() {
      local unit_name="$1"
      local generated_file="$GHOSTSHIP_GENERATED_UNITS_DIR/$unit_name"
      local live_file="$HOME/.config/systemd/user/$unit_name"

      [ -f "$generated_file" ] || return 0
      mkdir -p "$HOME/.config/systemd/user"

      if [ ! -e "$live_file" ] || generated_target_is_live "$live_file"; then
        ln -sfn "$generated_file" "$live_file"
      fi
      return 0
    }

    remove_generated_user_unit() {
      local unit_name="$1"
      local live_file="$HOME/.config/systemd/user/$unit_name"

      if generated_target_is_live "$live_file"; then
        rm -f "$live_file"
      fi
      return 0
    }

    profile_gateway_unit_candidates() {
      local profile_name="$1"
      local slug="$2"
      local is_default="$3"

      if [ "$is_default" = "true" ]; then
        printf 'hermes-gateway.service\n'
        printf 'hermes-gateway-default.service\n'
      else
        printf 'hermes-gateway-%s.service\n' "$profile_name"
        if [ "$slug" != "$profile_name" ]; then
          printf 'hermes-gateway-%s.service\n' "$slug"
        fi
      fi
      return 0
    }

    user_unit_exists() {
      local unit_name="$1"
      local candidate

      for candidate in \
        "$HOME/.config/systemd/user/$unit_name" \
        "$GHOSTSHIP_SYSTEMD_MANAGED_DIR/$unit_name" \
        "/etc/systemd/user/$unit_name" \
        "/usr/lib/systemd/user/$unit_name"
      do
        if [ -e "$candidate" ]; then
          return 0
        fi
      done
      return 1
    }

    collect_gateway_state() {
      local profile_name="$1"
      local slug="$2"
      local is_default="$3"
      local unit_name

      GATEWAY_EXPECTED=false
      GATEWAY_RUNNING=false

      while IFS= read -r unit_name; do
        [ -n "$unit_name" ] || continue
        if user_unit_exists "$unit_name"; then
          GATEWAY_EXPECTED=true
        fi
        if "$GHOSTSHIP_SYSTEMCTL_BIN" --user --quiet is-active "$unit_name" 2>/dev/null; then
          GATEWAY_RUNNING=true
        fi
      done < <(profile_gateway_unit_candidates "$profile_name" "$slug" "$is_default")

      return 0
    }

    generate_profile_state() {
      local start_units="$1"
      local entries_file desired_units_file reload_required=0
      local profile_name profile_home slug port is_default
      local unit_file unit_name

      ensure_runtime_prereqs
      ensure_runtime_directories
      ensure_honcho_layout

      entries_file="$(mktemp)"
      desired_units_file="$(mktemp)"
      : > "$GHOSTSHIP_PROFILE_PORTS"

      while IFS=$'\t' read -r profile_name profile_home slug port is_default; do
        render_ttyd_unit "$profile_name" "$profile_home" "$slug" "$port"
        unit_name="ghostship-profile-ttyd-$slug.service"
        install_generated_user_unit "$unit_name"
        printf '%s\n' "$unit_name" >> "$desired_units_file"
        printf '%s\t%s\t%s\n' "$profile_name" "$slug" "$port" >> "$GHOSTSHIP_PROFILE_PORTS"
        collect_gateway_state "$profile_name" "$slug" "$is_default"
        printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$profile_name" "$slug" "$is_default" "/profiles/$slug/" "$GATEWAY_EXPECTED" "$GATEWAY_RUNNING" >> "$entries_file"
      done < <(enumerate_profiles)

      while IFS= read -r unit_file; do
        unit_name="$(basename "$unit_file")"
        if ! grep -Fxq "$unit_name" "$desired_units_file"; then
          if [ "$start_units" = "true" ]; then
            "$GHOSTSHIP_SYSTEMCTL_BIN" --user stop "$unit_name" >/dev/null 2>&1 || true
          fi
          rm -f "$unit_file"
          remove_generated_user_unit "$unit_name"
          reload_required=1
        fi
      done < <(find "$GHOSTSHIP_GENERATED_UNITS_DIR" -mindepth 1 -maxdepth 1 -type f -name 'ghostship-profile-ttyd-*.service' | sort)

      if [ "$start_units" = "true" ]; then
        "$GHOSTSHIP_SYSTEMCTL_BIN" --user daemon-reload >/dev/null 2>&1 || true
        while IFS= read -r unit_name; do
          [ -n "$unit_name" ] || continue
          "$GHOSTSHIP_SYSTEMCTL_BIN" --user start "$unit_name" >/dev/null 2>&1 || true
        done < "$desired_units_file"
      elif [ "$reload_required" -eq 1 ]; then
        :
      fi

      generate_manifest "$entries_file"
      generate_caddy_config "$GHOSTSHIP_PROFILE_PORTS"
      rm -f "$entries_file" "$desired_units_file"
      return 0
    }

    validate_binary() {
      local command_path="$1"
      "$command_path" --version >/dev/null 2>&1 || "$command_path" --help >/dev/null 2>&1
    }

    switch_symlink_atomically() {
      local target="$1"
      local link_path="$2"
      local tmp_link
      tmp_link="$link_path.tmp"
      ln -sfn "$target" "$tmp_link"
      mv -Tf "$tmp_link" "$link_path"
      return 0
    }

    install_npm_app() {
      local app_key="$1"
      local package_name="$2"
      local command_name="$3"
      local version version_dir tmp_dir command_path

      version="$(npm view "$package_name" version --json | tr -d '"')"
      if [ -z "$version" ]; then
        log_warn "no version returned for $package_name"
        return 0
      fi

      version_dir="$GHOSTSHIP_APPS_DIR/$app_key/$version"
      command_path="$version_dir/bin/$command_name"
      if [ ! -x "$command_path" ]; then
        tmp_dir="$version_dir.tmp.$$"
        rm -rf "$tmp_dir"
        mkdir -p "$tmp_dir"
        log_info "installing $package_name@$version"
        if ! npm install --global --prefix "$tmp_dir" "$package_name@$version" >/tmp/ghostship-"$app_key"-install.log 2>&1; then
          log_warn "install failed for $package_name@$version"
          rm -rf "$tmp_dir"
          return 0
        fi
        command_path="$tmp_dir/bin/$command_name"
        if [ ! -x "$command_path" ] || ! validate_binary "$command_path"; then
          log_warn "validation failed for $package_name@$version"
          rm -rf "$tmp_dir"
          return 0
        fi
        mkdir -p "$(dirname "$version_dir")"
        mv "$tmp_dir" "$version_dir"
      fi

      mkdir -p "$GHOSTSHIP_CURRENT_DIR" "$HOME/.local/bin"
      switch_symlink_atomically "$version_dir" "$GHOSTSHIP_CURRENT_DIR/$app_key"
      switch_symlink_atomically "$version_dir/bin/$command_name" "$HOME/.local/bin/$command_name"
      return 0
    }

    update_apps_once() {
      ensure_runtime_prereqs
      ensure_runtime_directories
      install_npm_app "codex" "@openai/codex" "codex"
      install_npm_app "gemini-cli" "@google/gemini-cli" "gemini"
      install_npm_app "opencode" "opencode-ai" "opencode"
      install_npm_app "openspec" "@fission-ai/openspec" "openspec"
      install_npm_app "skills" "skills" "skills"
      return 0
    }

    refresh_global_skills() {
      local skills_output
      if ! command -v skills >/dev/null 2>&1; then
        return 0
      fi
      if ! skills_output="$(skills update -g 2>&1)"; then
        log_warn "skills update -g failed"
        if [ -n "$skills_output" ]; then
          printf '%s\n' "$skills_output" >&2
        fi
        return 0
      fi
      if [ -n "$skills_output" ]; then
        printf '%s\n' "$skills_output" >&2
      fi
      return 0
    }

    refresh_gemini_extension() {
      local name="$1"
      local repo="$2"
      local extension_output

      if ! command -v gemini >/dev/null 2>&1; then
        return 0
      fi

      if [ -d "$HOME/.gemini/extensions/$name/.git" ]; then
        log_info "refreshing $name"
        if ! extension_output="$(gemini extensions update "$name" 2>&1)"; then
          log_warn "$name refresh failed"
          [ -n "$extension_output" ] && printf '%s\n' "$extension_output" >&2
          return 0
        fi
      elif [ ! -d "$HOME/.gemini/extensions/$name" ]; then
        log_info "installing $name"
        if ! extension_output="$(gemini extensions install "$repo" --auto-update --consent 2>&1)"; then
          log_warn "$name install failed"
          [ -n "$extension_output" ] && printf '%s\n' "$extension_output" >&2
          return 0
        fi
      else
        return 0
      fi

      [ -n "$extension_output" ] && printf '%s\n' "$extension_output" >&2
      return 0
    }

    refresh_openspec_roots() {
      local config_file repo_root openspec_output search_root
      if ! command -v openspec >/dev/null 2>&1; then
        return 0
      fi

      for search_root in "$HOME" "$GHOSTSHIP_WORKSPACE_ROOT"; do
        [ -d "$search_root" ] || continue
        while IFS= read -r config_file; do
          [ -n "$config_file" ] || continue
          repo_root="$(dirname "$(dirname "$config_file")")"
          log_info "refreshing openspec instructions in $repo_root"
          if ! openspec_output="$(cd "$repo_root" && openspec update . 2>&1)"; then
            log_warn "openspec refresh failed for $repo_root"
            [ -n "$openspec_output" ] && printf '%s\n' "$openspec_output" >&2
            continue
          fi
          apply_ghostship_openspec_overrides "$repo_root"
          [ -n "$openspec_output" ] && printf '%s\n' "$openspec_output" >&2
        done < <(find "$search_root" -path '*/openspec/config.yaml' -type f -not -path "$GHOSTSHIP_WORKSTATION_DIR/*" 2>/dev/null | sort)
      done
      return 0
    }

    refresh_assets_once() {
      ensure_runtime_prereqs
      ensure_runtime_directories
      refresh_global_skills
      refresh_gemini_extension "gemini-cli-security" "https://github.com/gemini-cli-extensions/security"
      refresh_openspec_roots
      return 0
    }

    refresh_opencode_models_once() {
      ensure_runtime_prereqs
      ensure_runtime_directories

      local models_url generated_config refresh_stamp today response_file config_file stamp_file
      models_url='https://openrouter.ai/api/frontend/models/find?categories=programming&fmt=cards&max_price=0&order=top-weekly'
      generated_config="$GHOSTSHIP_OPENCODE_STATE_DIR/programming-free-models.json"
      refresh_stamp="$GHOSTSHIP_OPENCODE_STATE_DIR/programming-free-models.date"
      today="$(date -u +%F)"

      if [ -f "$generated_config" ] && [ -f "$refresh_stamp" ] && [ "$(cat "$refresh_stamp")" = "$today" ]; then
        return 0
      fi

      response_file="$(mktemp "$GHOSTSHIP_OPENCODE_STATE_DIR/openrouter-models.XXXXXX.json")"
      config_file="$(mktemp "$GHOSTSHIP_OPENCODE_STATE_DIR/opencode-config.XXXXXX.json")"
      stamp_file="$(mktemp "$GHOSTSHIP_OPENCODE_STATE_DIR/opencode-refresh.XXXXXX")"

      if ! curl --fail --silent --show-error --location "$models_url" > "$response_file"; then
        log_warn "opencode model refresh fetch failed"
        rm -f "$response_file" "$config_file" "$stamp_file"
        return 0
      fi

      if ! jq -ce '
        def ghostship_name:
          if (. // "") | length == 0 then .
          elif test("\\(free\\)$") then sub("\\(free\\)$"; "(ghostship-free)")
          else . + " (ghostship-free)"
          end;

        .data.models
        | map(
            select((.endpoint.pricing.prompt // "") == "0")
            | select((.endpoint.pricing.completion // "") == "0")
            | {
                id: (.endpoint.model_variant_slug // ""),
                name: ((.name // "") | ghostship_name)
              }
          )
        | map(select(.id | length > 0))
        | if length == 0 then error("no free programming models returned") else . end
        | {
            "$schema": "https://opencode.ai/config.json",
            permission: "allow",
            provider: {
              openrouter: {
                models: (
                  reduce .[] as $model (
                    {};
                    .[$model.id] = (
                      if ($model.name | length) > 0
                      then { name: $model.name }
                      else {}
                      end
                    )
                  )
                )
              }
            }
          }
      ' "$response_file" > "$config_file"; then
        log_warn "opencode model refresh parse failed"
        rm -f "$response_file" "$config_file" "$stamp_file"
        return 0
      fi

      printf '%s\n' "$today" > "$stamp_file"
      mv "$config_file" "$generated_config"
      mv "$stamp_file" "$refresh_stamp"
      rm -f "$response_file"
      return 0
    }

    workstation_bootstrap() {
      ensure_runtime_prereqs
      ensure_runtime_directories
      ensure_honcho_layout
      bootstrap_hermes
      seed_hermes_skills
      seed_workstation
      generate_profile_state "false"
      return 0
    }

    prepare_runtime_storage() {
      ensure_runtime_prereqs
      prepare_runtime_storage_for_user
      return 0
    }

    prepare_runtime_storage_for_user() {
      ensure_runtime_prereqs
      install -d -m 1777 /tmp
      install -d -m 0755 "$HOME" "$GHOSTSHIP_DATA_ROOT" "$GHOSTSHIP_HOME_ROOT" "$GHOSTSHIP_WORKSPACE_ROOT" "$XDG_RUNTIME_DIR"
      chown -R "$HERMES_UID:$HERMES_GID" "$HOME" "$GHOSTSHIP_DATA_ROOT" "$GHOSTSHIP_HOME_ROOT" "$GHOSTSHIP_WORKSPACE_ROOT" "$XDG_RUNTIME_DIR" >/dev/null 2>&1 || true
      prepare_nix_profile_state
      return 0
    }

    run_profile_chat() {
      local profile_name="$1"
      local profile_home="$2"
      export HERMES_HOME="$profile_home"
      export FEED_DB_PATH="$HERMES_HOME/feed/feed.db"
      mkdir -p "$HERMES_HOME/feed"
      cd "$TERMINAL_CWD"

      if profile_has_chat_credentials "$profile_name" "$profile_home"; then
        exec hermes chat
      fi

      printf 'Hermes profile %s is not configured yet; starting shell.\n' "$profile_name" >&2
      exec bash -l
    }

    command_name="''${1:-}"
    shift || true

    case "$command_name" in
      bootstrap)
        bootstrap_hermes
        ;;
      prepare-runtime-storage)
        prepare_runtime_storage
        ;;
      seed-skills)
        seed_hermes_skills
        ;;
      seed-workstation)
        seed_workstation
        ;;
      update-apps-once)
        update_apps_once
        ;;
      refresh-assets-once)
        refresh_assets_once
        ;;
      refresh-opencode-models-once)
        refresh_opencode_models_once
        ;;
      workstation-bootstrap)
        workstation_bootstrap
        ;;
      generate-profile-state)
        generate_profile_state "false"
        ;;
      entrypoint)
        ensure_runtime_prereqs
        configure_runtime_identity
        if [ "$(id -u)" -eq 0 ]; then
          prepare_runtime_storage_for_user
          setpriv --reuid "$HERMES_UID" --regid "$HERMES_GID" --clear-groups --inh-caps -all "$0" seed-skills
          setpriv --reuid "$HERMES_UID" --regid "$HERMES_GID" --clear-groups --inh-caps -all "$0" seed-workstation
          exec setpriv --reuid "$HERMES_UID" --regid "$HERMES_GID" --clear-groups --inh-caps -all "$0" user-manager
        fi
        "$0" seed-skills
        "$0" seed-workstation
        exec "$0" user-manager
        ;;
      user-manager)
        ensure_runtime_prereqs
        ensure_runtime_directories
        ensure_honcho_layout
        dbus_config=""
        mkdir -p "$XDG_RUNTIME_DIR"
        chmod 0700 "$XDG_RUNTIME_DIR"
        export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
        dbus_config="$(mktemp "$XDG_RUNTIME_DIR/dbus-session.XXXXXX.conf")"
        cat > "$dbus_config" <<EOF
<!DOCTYPE busconfig PUBLIC "-//freedesktop//DTD D-Bus Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">
<busconfig>
  <type>session</type>
  <listen>''${DBUS_SESSION_BUS_ADDRESS}</listen>
  <auth>EXTERNAL</auth>
  <standard_session_servicedirs />
  <policy context="default">
    <allow send_destination="*" eavesdrop="true"/>
    <allow eavesdrop="true"/>
    <allow own="*"/>
  </policy>
  <policy context="mandatory">
    <deny send_interface="org.freedesktop.DBus.Local" />
  </policy>
</busconfig>
EOF
        dbus-daemon \
          --config-file="$dbus_config" \
          --fork \
          --nopidfile
        exec "$GHOSTSHIP_SYSTEMD_USER_BIN" --user
        ;;
      caddy-service)
        ensure_runtime_prereqs
        ensure_runtime_directories
        if [ ! -f "$GHOSTSHIP_CADDY_CONFIG" ]; then
          generate_profile_state "false"
        fi
        exec caddy run --config "$GHOSTSHIP_CADDY_CONFIG" --adapter caddyfile
        ;;
      profile-reconciler-loop)
        ensure_runtime_prereqs
        ensure_runtime_directories
        while true; do
          generate_profile_state "true"
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
      *)
        printf 'usage: ghostship-hermes-runtime <bootstrap|seed-skills|seed-workstation|update-apps-once|refresh-assets-once|refresh-opencode-models-once|workstation-bootstrap|generate-profile-state|entrypoint|user-manager|caddy-service|profile-reconciler-loop|ttyd-profile-service|terminal-profile-session>\n' >&2
        exit 64
        ;;
    esac
  '';
}
