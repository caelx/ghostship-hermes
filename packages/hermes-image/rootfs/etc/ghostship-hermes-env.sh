#!/usr/bin/env bash

ghostship_is_hermes_passthrough_key() {
  local key="${1:-}"

  case "$key" in
    DISCORD_WEBHOOK_CHANNEL|GHOSTSHIP_ROUTER_CHANNEL|_GHOSTSHIP_ROUTER_API_KEY)
      return 0
      ;;
  esac

  case "$key" in
    ""|_[A-Z0-9_]*|AGENT_BROWSER_PROFILE|API_SERVER_HOST|API_SERVER_PORT|BASH_FUNC_*|CARGO_HOME|DBUS_SESSION_BUS_ADDRESS|GHOSTSHIP_DASHBOARD_HOST|GHOSTSHIP_DASHBOARD_PORT|GHOSTSHIP_HERMES_GATEWAY_SERVICE|GHOSTSHIP_HERMES_MANAGED_PROFILE|GHOSTSHIP_HERMES_PROJECT_ROOT|GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF|GHOSTSHIP_NIX_DEFAULT_PROFILE|GHOSTSHIP_ROUTER_HOST|GHOSTSHIP_ROUTER_PORT|GHOSTSHIP_ROUTER_URL|GHOSTSHIP_TERMINAL_CWD|GHOSTSHIP_TOOLING_MODE|GHOSTSHIP_TTYD_BASE_PATH|GHOSTSHIP_TTYD_SOCKET|GHOSTSHIP_WEB_PORT|GHOSTSHIP_WORKSPACE_ROOT|HERMES_HOME|HOME|HOSTNAME|LOGNAME|NIX_SSL_CERT_FILE|NPM_CONFIG_PREFIX|OPENAI_API_KEY|PATH|PWD|RUSTUP_HOME|SHELL|SHLVL|SSL_CERT_FILE|TERM|TERMINAL_CWD|USER|XDG_CACHE_HOME|XDG_CONFIG_HOME|XDG_DATA_HOME|XDG_RUNTIME_DIR|XDG_STATE_HOME)
      return 1
      ;;
    API_SERVER_*|GHOSTSHIP_DASHBOARD_*|GHOSTSHIP_HERMES_*|GHOSTSHIP_HUD_*|GHOSTSHIP_ROUTER_*|GHOSTSHIP_TOOLING_*|GHOSTSHIP_TTYD_*|HERMES_HUD_*|INVOCATION_*|JOURNAL_*|LC_*|LISTEN_*|S6_*|SYSTEMD_*)
      return 1
      ;;
  esac

  [[ "$key" =~ ^[A-Z][A-Z0-9_]*$ ]]
}

ghostship_quote_env_value() {
  printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"
}

ghostship_collect_hermes_env() {
  local map_name="$1"
  local terminal_cwd="$2"
  local -n env_values="$map_name"

  env_values=()
  env_values["TERMINAL_CWD"]="$terminal_cwd"

  while IFS= read -r -d '' entry; do
    local key value
    key="${entry%%=*}"
    value="${entry#*=}"
    ghostship_is_hermes_passthrough_key "$key" || continue
    [ -n "$value" ] || continue
    case "$value" in
      *$'\n'*)
        continue
        ;;
    esac
    env_values["$key"]="$value"
  done < <(env -0)

  if [ -z "${env_values[OPENCODE_API_KEY]+x}" ] && [ -n "${OPENCODE_GO_API_KEY:-}" ]; then
    env_values["OPENCODE_API_KEY"]="${OPENCODE_GO_API_KEY}"
  fi
}

ghostship_write_hermes_env_file() {
  local target="$1"
  local map_name="$2"
  local tmp_target
  local -n env_values="$map_name"

  mkdir -p "$(dirname "$target")"
  tmp_target="$(mktemp "$(dirname "$target")/.hermes.env.tmp.XXXXXX")"

  {
    for key in $(printf '%s\n' "${!env_values[@]}" | sort); do
      printf '%s=%s\n' "$key" "$(ghostship_quote_env_value "${env_values[$key]}")"
    done
  } >"$tmp_target"
  chmod 0600 "$tmp_target"
  mv -f "$tmp_target" "$target"
}

ghostship_write_hermes_env_keys_file() {
  local target="$1"
  local map_name="$2"
  local tmp_target
  local -n env_values="$map_name"

  mkdir -p "$(dirname "$target")"
  tmp_target="$(mktemp "$(dirname "$target")/.hermes.env.keys.tmp.XXXXXX")"
  printf '%s\n' "${!env_values[@]}" | sort >"$tmp_target"
  chmod 0600 "$tmp_target"
  mv -f "$tmp_target" "$target"
}

ghostship_merge_hermes_env_file() {
  local target="$1"
  local managed_source="$2"
  local previous_keys_file="$3"
  local tmp_target
  local line key
  declare -A strip_keys=()

  while IFS='=' read -r key _; do
    [ -n "$key" ] || continue
    strip_keys["$key"]=1
  done <"$managed_source"

  if [ -r "$previous_keys_file" ]; then
    while IFS= read -r key; do
      [ -n "$key" ] || continue
      strip_keys["$key"]=1
    done <"$previous_keys_file"
  fi

  mkdir -p "$(dirname "$target")"
  tmp_target="$(mktemp "$(dirname "$target")/.hermes.env.tmp.XXXXXX")"

  if [ -r "$target" ]; then
    while IFS= read -r line || [ -n "$line" ]; do
      if [[ "$line" =~ ^[[:space:]]*(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)= ]]; then
        key="${BASH_REMATCH[2]}"
        if [ -n "${strip_keys[$key]+x}" ]; then
          continue
        fi
      fi
      printf '%s\n' "$line" >>"$tmp_target"
    done <"$target"
  fi

  cat "$managed_source" >>"$tmp_target"
  chmod 0600 "$tmp_target"
  mv -f "$tmp_target" "$target"
}

ghostship_unset_hermes_excluded_env() {
  local key keep_key

  while IFS='=' read -r key _; do
    for keep_key in "$@"; do
      if [ "$key" = "$keep_key" ]; then
        continue 2
      fi
    done
    ghostship_is_hermes_passthrough_key "$key" && continue
    unset "$key"
  done < <(env)
}
