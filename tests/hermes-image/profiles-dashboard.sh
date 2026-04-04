#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
image_tar="${1:?usage: profiles-dashboard.sh <docker-image-tar> [image-tag]}"
release="$(tr -d '\n' < "$repo_root/packages/hermes-image/hermes-release.txt")"
image_tag="${2:-ghostship-hermes:$release}"
container_name="ghostship-hermes-dashboard-test"
tmp_root="$(mktemp -d)"
data_dir="$tmp_root/data"
workspace_dir="$tmp_root/workspace"
container_shell="/bin/sh"
container_path="/run/current-system/sw/bin:/nix/var/nix/profiles/system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/bin"
nix_volume_root="${GHOSTSHIP_NIX_VOLUME_ROOT:-}"

if [ -z "$nix_volume_root" ]; then
  if [ -n "${GHOSTSHIP_NIX_STORE:-}" ]; then
    nix_volume_root="${GHOSTSHIP_NIX_STORE}/nix"
  else
    nix_volume_root="/nix"
  fi
fi

if [ ! -d "$nix_volume_root/store" ]; then
  echo "$nix_volume_root/store is required for dashboard validation" >&2
  exit 1
fi

cleanup() {
  docker rm -f "$container_name" >/dev/null 2>&1 || true
  docker image rm -f "$image_tag" >/dev/null 2>&1 || true
  rm -rf "$tmp_root" >/dev/null 2>&1 || true
}
trap cleanup EXIT

wait_for_http() {
  local url="$1"
  local attempts="${2:-60}"
  local delay="${3:-2}"
  local try=1

  while [ "$try" -le "$attempts" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
    try=$((try + 1))
  done

  return 1
}

assert_http_contains() {
  local url="$1"
  local pattern="$2"
  local body

  body="$(curl -fsS "$url")"
  grep -q "$pattern" <<<"$body"
}

run_in_container() {
  local container_name="$1"
  shift
  docker exec \
    -e PATH="$container_path" \
    "$container_name" \
    "$container_shell" -lc "$*"
}

if [ "${SKIP_DOCKER_LOAD:-0}" != "1" ]; then
  xz -dc "$image_tar" | docker import - "$image_tag" >/dev/null
fi

mkdir -p "$data_dir" "$workspace_dir"
docker rm -f "$container_name" >/dev/null 2>&1 || true

docker run -d \
  --name "$container_name" \
  --privileged \
  --cgroupns=host \
  --tmpfs /run \
  --tmpfs /run/lock \
  --tmpfs /tmp \
  -e container=docker \
  -p 7681:7681 \
  -v "$data_dir:/data" \
  -v "$workspace_dir:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -v "$nix_volume_root:/nix" \
  "$image_tag" /init >/dev/null

wait_for_http "http://127.0.0.1:7681/"
wait_for_http "http://127.0.0.1:7681/api/status"

assert_http_contains "http://127.0.0.1:7681/" 'data-dashboard="ghostship-hermes-dashboard"'
assert_http_contains "http://127.0.0.1:7681/" "Open Terminal"
assert_http_contains "http://127.0.0.1:7681/api/status" '"running": false'

curl -fsS -X POST http://127.0.0.1:7681/api/terminal/open >/tmp/ghostship-hermes-terminal-open.json
grep -q '"running": true' /tmp/ghostship-hermes-terminal-open.json

wait_for_http "http://127.0.0.1:7681/terminal/"
assert_http_contains "http://127.0.0.1:7681/terminal/" "ttyd"
assert_http_contains "http://127.0.0.1:7681/api/status" '"running": true'

curl -fsS -X POST http://127.0.0.1:7681/api/terminal/close >/tmp/ghostship-hermes-terminal-close.json
grep -q '"running": false' /tmp/ghostship-hermes-terminal-close.json
assert_http_contains "http://127.0.0.1:7681/api/status" '"running": false'

run_in_container "$container_name" 'id hermes | grep -F "uid=3000" >/dev/null'
run_in_container "$container_name" 'systemctl is-active hermes-agent.service >/dev/null'
run_in_container "$container_name" 'systemctl is-active ghostship-dashboard-controller.service >/dev/null'
run_in_container "$container_name" 'systemctl is-active ghostship-caddy.service >/dev/null'
