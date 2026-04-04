#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
image_tar="${1:?usage: profiles-dashboard.sh <docker-image-tar> [image-tag]}"
release="$(tr -d '\n' < "$repo_root/packages/hermes-image/hermes-release.txt")"
image_tag="${2:-ghostship-hermes:$release}"
container_name="ghostship-hermes-dashboard-test"
tmp_root="$(mktemp -d)"
home_dir="$tmp_root/home"
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

mkdir -p "$home_dir" "$workspace_dir"
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
  -v "$home_dir:/home/hermes" \
  -v "$workspace_dir:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -v "$nix_volume_root:/nix" \
  "$image_tag" /init >/dev/null

wait_for_http "http://127.0.0.1:7681/"
wait_for_http "http://127.0.0.1:7681/api/status"

assert_http_contains "http://127.0.0.1:7681/" 'data-dashboard="ghostship-hermes-dashboard"'
assert_http_contains "http://127.0.0.1:7681/" "Open Terminal"
assert_http_contains "http://127.0.0.1:7681/" "Managed service state stays in"
assert_http_contains "http://127.0.0.1:7681/api/status" '"sessions": \[\]'
assert_http_contains "http://127.0.0.1:7681/api/status" '"name": "default"'
assert_http_contains "http://127.0.0.1:7681/api/status" '"name": "test"'
assert_http_contains "http://127.0.0.1:7681/api/status" '"name": "coder"'

curl -fsS -X POST http://127.0.0.1:7681/api/terminal/open >/tmp/ghostship-hermes-terminal-open-1.json
terminal_one="$(jq -r '.active_terminal_id' /tmp/ghostship-hermes-terminal-open-1.json)"
terminal_one_url="$(jq -r '.sessions[] | select(.id == "'"$terminal_one"'") | .terminal_url' /tmp/ghostship-hermes-terminal-open-1.json)"
grep -q '"active_terminal_id"' /tmp/ghostship-hermes-terminal-open-1.json
wait_for_http "http://127.0.0.1:7681$terminal_one_url"
assert_http_contains "http://127.0.0.1:7681$terminal_one_url" "ttyd"

curl -fsS -X POST http://127.0.0.1:7681/api/terminal/open >/tmp/ghostship-hermes-terminal-open-2.json
terminal_two="$(jq -r '.active_terminal_id' /tmp/ghostship-hermes-terminal-open-2.json)"
terminal_two_url="$(jq -r '.sessions[] | select(.id == "'"$terminal_two"'") | .terminal_url' /tmp/ghostship-hermes-terminal-open-2.json)"
wait_for_http "http://127.0.0.1:7681$terminal_two_url"
assert_http_contains "http://127.0.0.1:7681$terminal_two_url" "ttyd"
assert_http_contains "http://127.0.0.1:7681/api/status" "\"id\": \"$terminal_one\""
assert_http_contains "http://127.0.0.1:7681/api/status" "\"id\": \"$terminal_two\""

curl -fsS -X POST "http://127.0.0.1:7681/api/terminals/$terminal_two/close" >/tmp/ghostship-hermes-terminal-close-2.json
assert_http_contains "http://127.0.0.1:7681/api/status" "\"id\": \"$terminal_one\""

curl -fsS -X POST "http://127.0.0.1:7681/api/terminals/$terminal_one/close" >/tmp/ghostship-hermes-terminal-close-1.json
assert_http_contains "http://127.0.0.1:7681/api/status" '"sessions": \[\]'

run_in_container "$container_name" 'id hermes | grep -F "uid=3000" >/dev/null'
run_in_container "$container_name" 'systemctl is-active hermes-agent.service >/dev/null'
run_in_container "$container_name" 'test "$(systemctl show -P Result ghostship-hermes-bootstrap.service)" = "success"'
run_in_container "$container_name" 'su - hermes -c "hermes profile show test >/dev/null"'
run_in_container "$container_name" 'su - hermes -c "hermes profile show coder >/dev/null"'
run_in_container "$container_name" 'su - hermes -c "test -d /home/hermes/.hermes/profiles/test && test -d /home/hermes/.hermes/profiles/coder"'
run_in_container "$container_name" 'su - hermes -c "hermes config show 2>/dev/null | grep -F \"/home/hermes\" >/dev/null"'
run_in_container "$container_name" 'systemctl is-active ghostship-dashboard-controller.service >/dev/null'
run_in_container "$container_name" 'systemctl cat hermes-agent.service | grep -F "WorkingDirectory=/home/hermes" >/dev/null'
run_in_container "$container_name" 'systemctl cat ghostship-hermes-bootstrap.service | grep -F "WorkingDirectory=/home/hermes" >/dev/null'
