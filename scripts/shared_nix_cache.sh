#!/usr/bin/env bash
set -euo pipefail

readonly NIXCACHE_OCI_REPO="cmspam/nixcache-oci"
readonly NIXCACHE_OCI_COMMIT="c7268f982c24f4385af0838fee5af54927cf1498"
readonly DEFAULT_CACHE_REPO="caelx/ghostship-cache"
readonly DEFAULT_CACHE_PORT="37515"
readonly DEFAULT_CACHE_UPSTREAM="https://cache.nixos.org"

log() {
  printf 'shared-nix-cache: %s\n' "$*" >&2
}

die() {
  log "$*"
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

cache_repo() {
  printf '%s\n' "${GHOSTSHIP_CACHE_REPO:-$DEFAULT_CACHE_REPO}"
}

cache_state_dir() {
  printf '%s\n' "${GHOSTSHIP_CACHE_STATE_DIR:-${RUNNER_TEMP:-/tmp}/ghostship-nixcache}"
}

fetch_upstream_file() {
  local relpath="$1"
  local dest="$2"
  local url="https://raw.githubusercontent.com/${NIXCACHE_OCI_REPO}/${NIXCACHE_OCI_COMMIT}/${relpath}"
  curl -fsSL "$url" -o "$dest"
}

append_nix_conf_line() {
  local line="$1"
  local nix_conf="${HOME}/.config/nix/nix.conf"
  mkdir -p "$(dirname "$nix_conf")"
  touch "$nix_conf"
  grep -qxF "$line" "$nix_conf" || printf '%s\n' "$line" >> "$nix_conf"
}

cache_token() {
  if [[ -n "${GHOSTSHIP_CACHE_GHCR_TOKEN:-}" ]]; then
    printf '%s\n' "$GHOSTSHIP_CACHE_GHCR_TOKEN"
  elif [[ -n "${GITHUB_CACHE_FALLBACK_TOKEN:-}" ]]; then
    printf '%s\n' "$GITHUB_CACHE_FALLBACK_TOKEN"
  elif [[ -n "${GITHUB_TOKEN:-}" ]]; then
    printf '%s\n' "$GITHUB_TOKEN"
  elif [[ -n "${GH_TOKEN:-}" ]]; then
    printf '%s\n' "$GH_TOKEN"
  fi
}


cache_publish_user() {
  if [[ -n "${GHOSTSHIP_CACHE_GHCR_USER:-}" ]]; then
    printf '%s\n' "$GHOSTSHIP_CACHE_GHCR_USER"
  elif [[ -n "${GITHUB_REPOSITORY_OWNER:-}" ]]; then
    printf '%s\n' "$GITHUB_REPOSITORY_OWNER"
  elif [[ -n "${GITHUB_ACTOR:-}" ]]; then
    printf '%s\n' "$GITHUB_ACTOR"
  fi
}

cache_can_publish() {
  require_cmd curl

  local token user repo registry http_code
  token="$(cache_token || true)"
  user="$(cache_publish_user || true)"
  repo="$(cache_repo)"
  registry="${GHOSTSHIP_CACHE_REGISTRY:-ghcr.io}"

  [[ -n "$token" ]] || return 1
  [[ -n "$user" ]] || return 1

  http_code=$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 20 \
    -u "${user}:${token}" \
    -X POST \
    "https://${registry}/v2/${repo}/nix-cache/blobs/uploads/" 2>/dev/null || true)

  [[ "$http_code" == "202" ]]
}

cache_has_index() {
  require_cmd curl

  local repo
  repo="$(cache_repo)"
  local registry="${GHOSTSHIP_CACHE_REGISTRY:-ghcr.io}"
  local scope="repository:${repo}/nix-cache:pull"
  local token_json token header http_code

  token_json=$(curl -fsS --connect-timeout 5 --max-time 15 \
    "https://${registry}/token?scope=${scope}&service=${registry}" 2>/dev/null || true)
  token=$(python3 - <<'PYTOKEN' "$token_json"
import json, sys
try:
    print(json.loads(sys.argv[1]).get('token', ''))
except Exception:
    print('')
PYTOKEN
)

  header=( -H 'Accept: application/vnd.oci.image.manifest.v1+json' )
  if [[ -n "$token" ]]; then
    header+=( -H "Authorization: Bearer ${token}" )
  fi

  http_code=$(curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 \
    "${header[@]}" \
    "https://${registry}/v2/${repo}/nix-cache/manifests/cache-index" 2>/dev/null || true)

  [[ "$http_code" == "200" ]]
}

bootstrap_cache() {
  require_cmd curl
  require_cmd python3

  local public_key="${GHOSTSHIP_CACHE_PUBLIC_KEY:-}"
  [[ -n "$public_key" ]] || die "GHOSTSHIP_CACHE_PUBLIC_KEY is not set; shared cache bootstrap is disabled"

  local state_dir
  state_dir="$(cache_state_dir)"
  mkdir -p "$state_dir"

  local proxy_script="$state_dir/nixcache-proxy.py"
  local proxy_log="$state_dir/proxy.log"
  local proxy_pid_file="$state_dir/proxy.pid"
  local port="${GHOSTSHIP_CACHE_PORT:-$DEFAULT_CACHE_PORT}"
  local listen="${GHOSTSHIP_CACHE_LISTEN:-127.0.0.1}"
  local upstream="${GHOSTSHIP_CACHE_UPSTREAM:-$DEFAULT_CACHE_UPSTREAM}"
  if ! cache_has_index; then
    log "cache index not present yet; skipping shared cache consumption for this run"
    return 1
  fi

  fetch_upstream_file proxy/main.py "$proxy_script"
  chmod +x "$proxy_script"

  if [[ -f "$proxy_pid_file" ]] && kill -0 "$(cat "$proxy_pid_file")" 2>/dev/null; then
    kill "$(cat "$proxy_pid_file")" 2>/dev/null || true
  fi

  env \
    NIXCACHE_REPO="$(cache_repo)" \
    NIXCACHE_REGISTRY="${GHOSTSHIP_CACHE_REGISTRY:-ghcr.io}" \
    NIXCACHE_PORT="$port" \
    NIXCACHE_LISTEN="$listen" \
    NIXCACHE_UPSTREAM="$upstream" \
    python3 "$proxy_script" >"$proxy_log" 2>&1 &
  local proxy_pid=$!
  printf '%s\n' "$proxy_pid" > "$proxy_pid_file"

  local ready=false
  for _ in $(seq 1 20); do
    if curl -fsS "http://${listen}:${port}/nix-cache-info" >/dev/null 2>&1; then
      ready=true
      break
    fi
    sleep 1
  done

  if [[ "$ready" != true ]]; then
    log "proxy failed to start"
    [[ -f "$proxy_log" ]] && cat "$proxy_log" >&2
    kill "$proxy_pid" 2>/dev/null || true
    return 1
  fi

  append_nix_conf_line "extra-substituters = http://${listen}:${port}"
  append_nix_conf_line "extra-trusted-substituters = http://${listen}:${port}"
  append_nix_conf_line "extra-trusted-public-keys = ${public_key}"

  if [[ -n "${GITHUB_ENV:-}" ]]; then
    {
      printf 'GHOSTSHIP_CACHE_PROXY_URL=http://%s:%s\n' "$listen" "$port"
      printf 'GHOSTSHIP_CACHE_PROXY_PID_FILE=%s\n' "$proxy_pid_file"
      printf 'GHOSTSHIP_CACHE_ENABLED=true\n'
    } >> "$GITHUB_ENV"
  fi

  log "proxy ready at http://${listen}:${port} for $(cache_repo)"
}

load_builder_lib() {
  local work_dir
  work_dir="$(mktemp -d)"
  fetch_upstream_file lib/cache-builder.sh "$work_dir/cache-builder.sh"
  export NIXCACHE_REPO="$(cache_repo)"
  export NIXCACHE_REGISTRY="${GHOSTSHIP_CACHE_REGISTRY:-ghcr.io}"
  export NIXCACHE_UPSTREAM_CACHES="${GHOSTSHIP_CACHE_UPSTREAM:-$DEFAULT_CACHE_UPSTREAM}"
  local token
  token="$(cache_token || true)"
  export GITHUB_TOKEN="$token"
  export GH_TOKEN="$token"
  # shellcheck disable=SC1090
  source "$work_dir/cache-builder.sh"
}

plan_paths() {
  require_cmd curl
  require_cmd nix
  local flake_ref="$1"
  local output_file="$2"
  mkdir -p "$(dirname "$output_file")"
  : > "$output_file"
  load_builder_lib
  mapfile -t paths < <(find_paths_to_cache "$flake_ref")
  if (( ${#paths[@]} > 0 )); then
    printf '%s\n' "${paths[@]}" > "$output_file"
  fi
  log "planned $(grep -c . "$output_file" 2>/dev/null || true) cache upload path(s) for $flake_ref"
}

write_signing_key() {
  local key_dir="$1"
  local signing_key="${GHOSTSHIP_CACHE_SIGNING_KEY:-}"
  [[ -n "$signing_key" ]] || die "GHOSTSHIP_CACHE_SIGNING_KEY is required to publish cache entries"
  local key_file="$key_dir/ghostship-cache.key"
  printf '%s\n' "$signing_key" > "$key_file"
  chmod 600 "$key_file"
  if [[ -n "${GHOSTSHIP_CACHE_PUBLIC_KEY:-}" ]]; then
    printf '%s\n' "$GHOSTSHIP_CACHE_PUBLIC_KEY" > "${key_file}.pub"
  fi
  printf '%s\n' "$key_file"
}

publish_paths() {
  require_cmd curl
  require_cmd jq
  require_cmd nix
  require_cmd xz

  local paths_file="$1"
  shift
  (( $# >= 1 )) || die "publish requires at least one GC root path"
  [[ -f "$paths_file" ]] || die "cache plan file not found: $paths_file"

  mapfile -t paths < "$paths_file"
  if (( ${#paths[@]} == 0 )); then
    log "no new local paths to publish"
    return 0
  fi

  local work_dir
  work_dir="$(mktemp -d)"
  local key_file
  key_file="$(write_signing_key "$work_dir")"
  export NIXCACHE_SIGNING_KEY_FILE="$key_file"
  load_builder_lib

  export_paths_directly "${paths[@]}"
  upload_to_oci "$@"

  if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
    {
      printf '## Shared Nix Cache Publish\n\n'
      printf -- '- Cache repo: `%s`\n' "$(cache_repo)"
      printf -- '- New store paths uploaded: `%s`\n' "${#paths[@]}"
    } >> "$GITHUB_STEP_SUMMARY"
  fi
}

usage() {
  cat >&2 <<'EOF'
usage:
  shared_nix_cache.sh bootstrap
  shared_nix_cache.sh has-index
  shared_nix_cache.sh can-publish
  shared_nix_cache.sh plan <flake-ref> <output-file>
  shared_nix_cache.sh publish <paths-file> <gc-root> [gc-root...]
EOF
}

main() {
  local cmd="${1:-}"
  case "$cmd" in
    bootstrap)
      shift
      bootstrap_cache "$@"
      ;;
    has-index)
      shift
      (( $# == 0 )) || { usage; exit 1; }
      cache_has_index
      ;;
    can-publish)
      shift
      (( $# == 0 )) || { usage; exit 1; }
      cache_can_publish
      ;;
    plan)
      shift
      (( $# == 2 )) || { usage; exit 1; }
      plan_paths "$1" "$2"
      ;;
    publish)
      shift
      (( $# >= 2 )) || { usage; exit 1; }
      publish_paths "$@"
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
