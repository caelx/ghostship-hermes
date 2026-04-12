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

patch_proxy_for_parallel_requests() {
  local proxy_script="$1"
  python3 - "$proxy_script" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

old = '    server = http.server.HTTPServer((LISTEN_ADDR, PORT), CacheHandler)\n'
new = (
    '    server = http.server.ThreadingHTTPServer((LISTEN_ADDR, PORT), CacheHandler)\n'
    '    server.daemon_threads = True\n'
)

if old not in text:
    raise SystemExit("proxy server bootstrap pattern not found")

path.write_text(text.replace(old, new, 1), encoding="utf-8")
PY
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

ghcr_manifest_http_code() {
  require_cmd curl

  local manifest_ref="$1"
  local manifest_url
  manifest_url="$(ghcr_manifest_url "$manifest_ref")"

  curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 \
    -H 'Accept: application/vnd.oci.image.manifest.v1+json' \
    "$manifest_url" 2>/dev/null || true
}

ghcr_manifest_url() {
  local manifest_ref="$1"
  local registry="${GHOSTSHIP_CACHE_REGISTRY:-ghcr.io}"
  local repo
  repo="$(cache_repo)"
  printf 'https://%s/v2/%s/nix-cache/manifests/%s\n' "$registry" "$repo" "$manifest_ref"
}

ghcr_scope() {
  local permissions="${1:-pull}"
  local repo
  repo="$(cache_repo)"
  printf 'repository:%s/nix-cache:%s\n' "$repo" "$permissions"
}

ghcr_bearer_token() {
  require_cmd curl

  local registry="${GHOSTSHIP_CACHE_REGISTRY:-ghcr.io}"
  local permissions="${1:-pull}"
  local use_auth="${2:-false}"
  local token user token_response registry_token
  token="$(cache_token || true)"
  user="$(cache_publish_user || true)"

  if [[ "$use_auth" == "true" ]]; then
    [[ -n "$token" ]] || return 1
    [[ -n "$user" ]] || return 1
    token_response=$(curl -sS --connect-timeout 5 --max-time 15 \
      -u "token:${token}" \
      "https://${registry}/token?scope=$(ghcr_scope "$permissions")&service=${registry}" 2>/dev/null || true)
  else
    token_response=$(curl -sS --connect-timeout 5 --max-time 15 \
      "https://${registry}/token?scope=$(ghcr_scope "$permissions")&service=${registry}" 2>/dev/null || true)
  fi

  registry_token="$(printf '%s' "$token_response" | jq -r '.token // empty' 2>/dev/null || true)"
  [[ -n "$registry_token" ]] || return 1
  printf '%s\n' "$registry_token"
}

ghcr_manifest_http_code_auth() {
  require_cmd curl

  local manifest_ref="$1"
  local manifest_url bearer_token
  manifest_url="$(ghcr_manifest_url "$manifest_ref")"
  bearer_token="$(ghcr_bearer_token pull true || true)"
  [[ -n "$bearer_token" ]] || return 1

  curl -sS -o /dev/null -w '%{http_code}' --connect-timeout 5 --max-time 15 \
    -H 'Accept: application/vnd.oci.image.manifest.v1+json' \
    -H "Authorization: Bearer ${bearer_token}" \
    "$manifest_url" 2>/dev/null || true
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
  local http_code
  http_code="$(ghcr_manifest_http_code cache-index)"
  if [[ "$http_code" == "200" ]]; then
    return 0
  fi

  http_code="$(ghcr_manifest_http_code_auth cache-index || true)"
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
  patch_proxy_for_parallel_requests "$proxy_script"
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
    GITHUB_TOKEN="$(cache_token || true)" \
    GH_TOKEN="$(cache_token || true)" \
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
  patch_cache_builder_for_large_indices
}

patch_cache_builder_for_large_indices() {
  update_cache_index() {
    local existing_index_file="$1"
    local new_entries_file="$2"
    shift 2
    local gc_root_paths=("$@")

    local gc_roots_file="$NIXCACHE_WORK_DIR/cache-index-gc-roots.json"
    jq -n '[]' > "$gc_roots_file"
    local p h
    for p in "${gc_root_paths[@]}"; do
      h=$(basename "$p" | cut -c1-32)
      jq --arg h "$h" '. + [$h]' "$gc_roots_file" > "${gc_roots_file}.tmp"
      mv "${gc_roots_file}.tmp" "$gc_roots_file"
    done

    local public_key=""
    if [[ -n "$NIXCACHE_SIGNING_KEY_FILE" ]] && [[ -f "${NIXCACHE_SIGNING_KEY_FILE}.pub" ]]; then
      public_key=$(cat "${NIXCACHE_SIGNING_KEY_FILE}.pub")
    fi

    local index_file="$NIXCACHE_WORK_DIR/cache-index.json"
    python3 - <<'PYUPDATE' "$existing_index_file" "$new_entries_file" "$gc_roots_file" "$public_key" "$NIXCACHE_REPO" "$NIXCACHE_REGISTRY" "$NIXCACHE_IMAGE" "$index_file"
import json
import sys
from datetime import datetime, timezone

existing_index_path, new_entries_path, gc_roots_path, public_key, repo, registry, image, index_path = sys.argv[1:9]

def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default

existing = load_json(existing_index_path, {})
new_entries = load_json(new_entries_path, {})
gc_roots = load_json(gc_roots_path, [])

index = {
    "version": 1,
    "repo": repo,
    "registry": registry,
    "image": image,
    "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "public_key": public_key,
    "entries": {},
    "gc_roots": [],
}

if isinstance(existing.get("entries"), dict):
    index["entries"].update(existing["entries"])
if isinstance(existing.get("gc_roots"), list):
    index["gc_roots"] = existing["gc_roots"]

index["entries"].update(new_entries)
index["gc_roots"] = sorted(set(index["gc_roots"] + gc_roots))

if not public_key and existing.get("public_key"):
    index["public_key"] = existing["public_key"]

with open(index_path, "w", encoding="utf-8") as handle:
    json.dump(index, handle, indent=2, sort_keys=True)
PYUPDATE

    local index_digest
    index_digest=$(oci_push_blob "$index_file")
    local index_size
    index_size=$(stat -c%s "$index_file")

    local config_file="$NIXCACHE_WORK_DIR/config.json"
    echo '{}' > "$config_file"
    local config_digest
    config_digest=$(oci_push_blob "$config_file")
    local config_size
    config_size=$(stat -c%s "$config_file")

    local manifest
    manifest=$(jq -n \
      --arg config_digest "$config_digest" \
      --argjson config_size "$config_size" \
      --arg index_digest "$index_digest" \
      --argjson index_size "$index_size" \
      '{
          schemaVersion: 2,
          mediaType: "application/vnd.oci.image.manifest.v1+json",
          config: {
              mediaType: "application/vnd.oci.image.config.v1+json",
              digest: $config_digest,
              size: $config_size
          },
          layers: [{
              mediaType: "application/vnd.nixcache.index.v1+json",
              digest: $index_digest,
              size: $index_size
          }]
      }')

    oci_push_manifest "cache-index" "$manifest"
  }

  upload_to_oci() {
    info "Uploading to GHCR: ${NIXCACHE_IMAGE}"

    local existing_index_file="$NIXCACHE_WORK_DIR/cache-existing-index.json"
    jq -n '{}' > "$existing_index_file"
    local existing_manifest
    existing_manifest=$(oci_get_manifest "cache-index")
    if [[ -n "$existing_manifest" ]]; then
      local index_digest
      index_digest=$(echo "$existing_manifest" | jq -r '.layers[0].digest // empty' 2>/dev/null)
      if [[ -n "$index_digest" ]]; then
        if ! oci_get_blob "$index_digest" > "$existing_index_file" 2>/dev/null; then
          jq -n '{}' > "$existing_index_file"
        fi
      fi
    fi

    local new_entries_file="$NIXCACHE_WORK_DIR/cache-new-entries.json"
    jq -n '{}' > "$new_entries_file"
    local uploaded=0
    local upload_failures=0
    local narinfo hash nar_url nar_file nar_size nar_digest store_path name
    local added_at

    for narinfo in "$CACHE_DIR"/*.narinfo; do
      [[ -f "$narinfo" ]] || continue
      hash=$(basename "$narinfo" .narinfo)

      nar_url=$(grep '^URL: ' "$narinfo" | head -1 | cut -d' ' -f2)
      nar_file="$CACHE_DIR/$nar_url"

      if [[ ! -f "$nar_file" ]]; then
        err "NAR file not found for $hash: $nar_url"
        continue
      fi

      nar_size=$(stat -c%s "$nar_file")
      info "  Uploading NAR for $hash ($(numfmt --to=iec "$nar_size" 2>/dev/null || echo "${nar_size}B"))"
      nar_digest=$(oci_push_blob "$nar_file") || {
        err "Failed to upload NAR for $hash"
        upload_failures=$((upload_failures + 1))
        continue
      }

      store_path=$(grep '^StorePath: ' "$narinfo" | head -1 | cut -d' ' -f2)
      name=$(basename "$store_path" | sed 's/^[a-z0-9]*-//')
      added_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

      jq \
        --arg hash "$hash" \
        --arg name "$name" \
        --rawfile narinfo "$narinfo" \
        --arg nar_digest "$nar_digest" \
        --argjson nar_size "$nar_size" \
        --arg added "$added_at" \
        '.[$hash] = {
          name: $name,
          narinfo: $narinfo,
          nar_digest: $nar_digest,
          nar_size: $nar_size,
          added: $added
        }' \
        "$new_entries_file" > "${new_entries_file}.tmp"
      mv "${new_entries_file}.tmp" "$new_entries_file"

      uploaded=$((uploaded + 1))
    done

    if [[ "$uploaded" -eq 0 ]]; then
      info "No new paths to upload"
      return 0
    fi

    if [[ "$upload_failures" -gt 0 ]]; then
      err "$upload_failures upload(s) failed. Updating index with $uploaded successful upload(s) only."
    fi

    info "Uploaded $uploaded NAR(s), updating index"
    update_cache_index "$existing_index_file" "$new_entries_file" "$@"
  }
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
