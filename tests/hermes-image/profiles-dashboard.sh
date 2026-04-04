#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
image_bundle="${1:?usage: profiles-dashboard.sh <image-bundle> [image-tag]}"
release="$(tr -d '\n' < "$repo_root/packages/hermes-image/hermes-release.txt")"
image_tag="${2:-ghostship-hermes:$release}"
container_name="ghostship-hermes-dashboard-test"
tmp_root="$(mktemp -d)"
home_dir="$tmp_root/home"
workspace_dir="$tmp_root/workspace"
host_uid="$(id -u)"
host_gid="$(id -g)"
container_shell="/bin/sh"
container_path="/run/current-system/sw/bin:/nix/var/nix/profiles/system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/bin"
nix_volume_root="${GHOSTSHIP_NIX_VOLUME_ROOT:-}"
dashboard_port="${GHOSTSHIP_TEST_DASHBOARD_PORT:-7681}"
dashboard_base_url="http://127.0.0.1:${dashboard_port}"

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
  if docker image inspect "$image_tag" >/dev/null 2>&1; then
    docker run --rm --entrypoint /bin/sh -u 0:0 -v "$tmp_root:/cleanup" "$image_tag" -lc '
      chown -R '"$host_uid:$host_gid"' /cleanup >/dev/null 2>&1 || true
      chmod -R u+w /cleanup >/dev/null 2>&1 || true
    ' >/dev/null 2>&1 || true
  fi
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

wait_for_json_value() {
  local url="$1"
  local jq_filter="$2"
  local expected="$3"
  local attempts="${4:-60}"
  local delay="${5:-1}"
  local try=1
  local value

  while [ "$try" -le "$attempts" ]; do
    value="$(curl -fsS "$url" | jq -r "$jq_filter")"
    if [ "$value" = "$expected" ]; then
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

assert_websocket_proxy() {
  local terminal_url="$1"
  python3 - "$terminal_url" "$dashboard_port" <<'PY'
import base64
import hashlib
import os
import socket
import sys

terminal_url = sys.argv[1].rstrip("/")
dashboard_port = int(sys.argv[2])
path = f"{terminal_url}/ws"
key = base64.b64encode(os.urandom(16)).decode("ascii")
request = (
    f"GET {path} HTTP/1.1\r\n"
    f"Host: 127.0.0.1:{dashboard_port}\r\n"
    "Upgrade: websocket\r\n"
    "Connection: Upgrade\r\n"
    f"Sec-WebSocket-Key: {key}\r\n"
    "Sec-WebSocket-Version: 13\r\n"
    f"Origin: http://127.0.0.1:{dashboard_port}\r\n"
    "\r\n"
).encode("ascii")

sock = socket.create_connection(("127.0.0.1", dashboard_port), timeout=5)
sock.settimeout(5)
sock.sendall(request)

response = bytearray()
while b"\r\n\r\n" not in response:
    chunk = sock.recv(65536)
    if not chunk:
        raise SystemExit("websocket handshake closed early")
    response.extend(chunk)

head, _ = response.split(b"\r\n\r\n", 1)
lines = head.decode("latin1").split("\r\n")
if "101" not in lines[0]:
    raise SystemExit(f"unexpected websocket status: {lines[0]}")

headers = {}
for line in lines[1:]:
    name, value = line.split(":", 1)
    headers[name.strip().lower()] = value.strip()

expected_accept = base64.b64encode(
    hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
).decode("ascii")
if headers.get("sec-websocket-accept") != expected_accept:
    raise SystemExit("invalid websocket accept header")

payload = b"x"
mask = os.urandom(4)
masked = bytes(payload[i] ^ mask[i % 4] for i in range(len(payload)))
sock.sendall(bytes([0x89, 0x80 | len(payload)]) + mask + masked)

pong = sock.recv(32)
if not pong:
    raise SystemExit("websocket closed before pong")
if pong[0] & 0x0F != 0x0A:
    raise SystemExit(f"expected pong frame, got opcode {pong[0] & 0x0F}")

sock.close()
PY
}

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for dashboard image testing" >&2
  exit 1
fi

if ! docker version >/dev/null 2>&1; then
  echo "docker is installed but not reachable from this shell; start a local Docker daemon or enable WSL integration before running dashboard image tests" >&2
  exit 1
fi

if [ "${SKIP_IMAGE_IMPORT:-0}" != "1" ]; then
  "$repo_root/scripts/export_publishable_image.sh" "$image_bundle" "$image_tag" >/dev/null
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
  -e OPENROUTER_API_KEY \
  -e OPENROUTER_BASE_URL \
  -e OPENROUTER_HTTP_REFERER \
  -e OPENROUTER_TITLE \
  -e OPENROUTER_TEST_MODEL \
  -p "${dashboard_port}:7681" \
  -v "$home_dir:/home/hermes" \
  -v "$workspace_dir:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -v "$nix_volume_root:/nix" \
  "$image_tag" /init >/dev/null

wait_for_http "${dashboard_base_url}/"
wait_for_http "${dashboard_base_url}/api/status"

assert_http_contains "${dashboard_base_url}/" 'data-dashboard="ghostship-hermes-dashboard"'
assert_http_contains "${dashboard_base_url}/" "Open Terminal"
assert_http_contains "${dashboard_base_url}/" "Two declared Hermes profiles"
assert_http_contains "${dashboard_base_url}/api/status" '"sessions": \[\]'
assert_http_contains "${dashboard_base_url}/api/status" '"name": "operations"'
assert_http_contains "${dashboard_base_url}/api/status" '"name": "coder"'
assert_http_contains "${dashboard_base_url}/api/status" '"default_profile": "operations"'

open_started_ms="$(date +%s%3N)"
curl -fsS -X POST "${dashboard_base_url}/api/terminal/open" >/tmp/ghostship-hermes-terminal-open-1.json
open_finished_ms="$(date +%s%3N)"
test $((open_finished_ms - open_started_ms)) -lt 1500
terminal_one="$(jq -r '.active_terminal_id' /tmp/ghostship-hermes-terminal-open-1.json)"
terminal_one_url="$(jq -r '.sessions[] | select(.id == "'"$terminal_one"'") | .terminal_url' /tmp/ghostship-hermes-terminal-open-1.json)"
terminal_one_label="$(jq -r '.sessions[] | select(.id == "'"$terminal_one"'") | .label' /tmp/ghostship-hermes-terminal-open-1.json)"
grep -q '"active_terminal_id"' /tmp/ghostship-hermes-terminal-open-1.json
test "$terminal_one_label" = "/home/hermes"
wait_for_http "${dashboard_base_url}${terminal_one_url}"
wait_for_json_value "${dashboard_base_url}/api/status" ".sessions[] | select(.id == \"$terminal_one\") | .ready" "true"
assert_http_contains "${dashboard_base_url}${terminal_one_url}" "ttyd"
assert_websocket_proxy "$terminal_one_url"

curl -fsS -X POST "${dashboard_base_url}/api/terminal/open" >/tmp/ghostship-hermes-terminal-open-2.json
terminal_two="$(jq -r '.active_terminal_id' /tmp/ghostship-hermes-terminal-open-2.json)"
terminal_two_url="$(jq -r '.sessions[] | select(.id == "'"$terminal_two"'") | .terminal_url' /tmp/ghostship-hermes-terminal-open-2.json)"
wait_for_http "${dashboard_base_url}${terminal_two_url}"
wait_for_json_value "${dashboard_base_url}/api/status" ".sessions[] | select(.id == \"$terminal_two\") | .ready" "true"
assert_http_contains "${dashboard_base_url}${terminal_two_url}" "ttyd"
assert_http_contains "${dashboard_base_url}/api/status" "\"id\": \"$terminal_one\""
assert_http_contains "${dashboard_base_url}/api/status" "\"id\": \"$terminal_two\""
assert_websocket_proxy "$terminal_two_url"

curl -fsS -X POST "${dashboard_base_url}/api/terminals/$terminal_two/close" >/tmp/ghostship-hermes-terminal-close-2.json
assert_http_contains "${dashboard_base_url}/api/status" "\"id\": \"$terminal_one\""

curl -fsS -X POST "${dashboard_base_url}/api/terminals/$terminal_one/close" >/tmp/ghostship-hermes-terminal-close-1.json
assert_http_contains "${dashboard_base_url}/api/status" '"sessions": \[\]'

run_in_container "$container_name" 'id hermes | grep -F "uid=3000" >/dev/null'
run_in_container "$container_name" '! systemctl is-active hermes-agent.service >/dev/null'
run_in_container "$container_name" 'test "$(systemctl show -P Result ghostship-hermes-bootstrap.service)" = "success"'
run_in_container "$container_name" 'systemctl is-active ghostship-hermes-profile-operations.service >/dev/null'
run_in_container "$container_name" 'systemctl is-active ghostship-hermes-profile-coder.service >/dev/null'
run_in_container "$container_name" 'su - hermes -c "hermes profile show operations >/dev/null"'
run_in_container "$container_name" 'su - hermes -c "hermes profile show coder >/dev/null"'
run_in_container "$container_name" 'su - hermes -c "test -d /home/hermes/.hermes/profiles/operations && test -d /home/hermes/.hermes/profiles/coder"'
run_in_container "$container_name" 'su - hermes -c "! test -d /home/hermes/.hermes/profiles/test"'
run_in_container "$container_name" 'su - hermes -c "test \"$(cat /home/hermes/.hermes/active_profile)\" = \"operations\""'
run_in_container "$container_name" 'su - hermes -c "grep -F \"OPENROUTER_API_KEY=\" /home/hermes/.hermes/profiles/operations/.env >/dev/null"'
run_in_container "$container_name" 'su - hermes -c "grep -F \"OPENROUTER_API_KEY=\" /home/hermes/.hermes/profiles/coder/.env >/dev/null"'
run_in_container "$container_name" 'su - hermes -c "hermes config show 2>/dev/null | grep -F \"/home/hermes\" >/dev/null"'
run_in_container "$container_name" 'systemctl is-active ghostship-dashboard-controller.service >/dev/null'
run_in_container "$container_name" 'systemctl cat ghostship-hermes-profile-operations.service | grep -F "WorkingDirectory=/home/hermes" >/dev/null'
run_in_container "$container_name" 'systemctl cat ghostship-hermes-profile-coder.service | grep -F "WorkingDirectory=/home/hermes" >/dev/null'
