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
bind_nix="${GHOSTSHIP_TEST_BIND_NIX:-0}"
nix_volume_root="${GHOSTSHIP_NIX_VOLUME_ROOT:-}"
dashboard_port="${GHOSTSHIP_TEST_DASHBOARD_PORT:-7681}"
dashboard_base_url="http://127.0.0.1:${dashboard_port}"
router_base_url="http://127.0.0.1:8788"

if [ "$bind_nix" = "1" ]; then
  if [ -z "$nix_volume_root" ]; then
    if [ -n "${GHOSTSHIP_NIX_STORE:-}" ]; then
      nix_volume_root="${GHOSTSHIP_NIX_STORE}/nix"
    else
      nix_volume_root="/nix"
    fi
  fi

  if [ ! -d "$nix_volume_root/store" ]; then
    echo "$nix_volume_root/store is required when GHOSTSHIP_TEST_BIND_NIX=1" >&2
    exit 1
  fi
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

run_as_hermes() {
  local container_name="$1"
  shift
  docker exec \
    -u 3000:3000 \
    -e HOME=/home/hermes \
    -e HERMES_HOME=/home/hermes/.hermes \
    -e TERMINAL_CWD=/home/hermes \
    -e PATH=/home/hermes/.local/bin:/home/hermes/.local/state/nix/profiles/ghostship-managed/bin:/home/hermes/.nix-profile/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/bin \
    "$container_name" \
    "$container_shell" -lc "$*"
}

run_as_hermes_default_path() {
  local container_name="$1"
  shift
  docker exec \
    -u 3000:3000 \
    -e HOME=/home/hermes \
    -e HERMES_HOME=/home/hermes/.hermes \
    -e TERMINAL_CWD=/home/hermes \
    "$container_name" \
    "$container_shell" -lc "$*"
}

wait_for_router_ready() {
  local container_name="$1"
  local attempts="${2:-60}"
  local delay="${3:-2}"
  local try=1

  while [ "$try" -le "$attempts" ]; do
    if run_in_container "$container_name" 'systemctl is-active ghostship-hermes-router.service >/dev/null 2>&1 && curl -fsS http://127.0.0.1:8788/readyz >/dev/null 2>&1'; then
      return 0
    fi
    sleep "$delay"
    try=$((try + 1))
  done

  return 1
}

assert_router_inventory() {
  local container_name="$1"
  run_in_container "$container_name" "curl -fsS ${router_base_url}/v1/models | jq -e '[.data[].id] | index(\"auxiliary\") and index(\"coding\") and index(\"agentic\") and index(\"vision\") and index(\"tts\")' >/dev/null"
}

assert_free_router_buckets() {
  local container_name="$1"
  run_in_container "$container_name" "curl -fsS ${router_base_url}/v1/models | jq -e '
    [.data[] | select(.id == \"auxiliary\" or .id == \"coding\" or .id == \"agentic\" or .id == \"vision\" or .id == \"tts\")]
    | length == 5
    and all(.[]; all(.metadata.candidates[]; .is_free == true))
    and all(.[]; if .id == \"tts\" then true else .metadata.candidate_count > 0 end)
  ' >/dev/null"
}

assert_model_config() {
  local container_name="$1"
  local scope="$2"
  local expected_model="$3"
  local command

  if [ "$scope" = "root" ]; then
    command='hermes config show'
  else
    command="hermes -p $scope config show"
  fi

  run_as_hermes "$container_name" "$command | grep -F 'provider: auto' >/dev/null"
  run_as_hermes "$container_name" "$command | grep -F 'base_url: http://127.0.0.1:8788/v1' >/dev/null"
  run_as_hermes "$container_name" "$command | grep -F 'default: $expected_model' >/dev/null"
}

assert_gateway_pid_contract() {
  local container_name="$1"
  local profile="$2"

  run_as_hermes "$container_name" "pid=\$(jq -r '.pid' /home/hermes/.hermes/profiles/$profile/gateway.pid); kind=\$(jq -r '.kind' /home/hermes/.hermes/profiles/$profile/gateway.pid); argv=\$(jq -r '.argv | join(\" \")' /home/hermes/.hermes/profiles/$profile/gateway.pid); test -n \"\$pid\"; test \"\$kind\" = \"hermes-gateway\"; printf '%s' \"\$argv\" | grep -F 'hermes gateway run --replace --profile $profile' >/dev/null; kill -0 \"\$pid\""
  run_as_hermes "$container_name" "pid=\$(jq -r '.pid' /home/hermes/.hermes/profiles/$profile/gateway.pid); ps -p \"\$pid\" -o args= | grep -F \" -p $profile gateway run --replace\" >/dev/null"
  run_as_hermes "$container_name" "hermes -p $profile gateway status | grep -F 'Managed gateway for profile '\''$profile'\'' is running' >/dev/null"
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

mkdir -p "$home_dir/.nix-profile/bin" "$workspace_dir"
cat > "$home_dir/.nix-profile/bin/hermes" <<'EOF'
#!/bin/sh
echo legacy-default-hermes
EOF
chmod +x "$home_dir/.nix-profile/bin/hermes"
docker rm -f "$container_name" >/dev/null 2>&1 || true

nix_mount_args=()
if [ "$bind_nix" = "1" ]; then
  nix_mount_args=(-v "$nix_volume_root:/nix")
fi

docker run -d \
  --name "$container_name" \
  --privileged \
  --cgroupns=host \
  --tmpfs /run \
  --tmpfs /run/lock \
  --tmpfs /tmp \
  -e container=docker \
  -e BWS_ACCESS_TOKEN \
  -e GOOGLE_AI_STUDIO_API_KEY \
  -e OPENCODE_GO_API_KEY \
  -e DISCORD_GENERAL_CHANNEL_ID \
  -e DISCORD_ASSISTANT_BOT_TOKEN \
  -e DISCORD_ASSISTANT_ALLOWED_USERS \
  -e DISCORD_ASSISTANT_CHANNEL_ID \
  -e DISCORD_OPERATIONS_BOT_TOKEN \
  -e DISCORD_OPERATIONS_ALLOWED_USERS \
  -e DISCORD_OPERATIONS_CHANNEL_ID \
  -e DISCORD_SUPERVISOR_BOT_TOKEN \
  -e DISCORD_SUPERVISOR_ALLOWED_USERS \
  -e DISCORD_SUPERVISOR_CHANNEL_ID \
  -e BROWSER_CDP_URL \
  -p "${dashboard_port}:7681" \
  -v "$home_dir:/home/hermes" \
  -v "$workspace_dir:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  "${nix_mount_args[@]}" \
  "$image_tag" /init >/dev/null

wait_for_http "${dashboard_base_url}/"
wait_for_http "${dashboard_base_url}/api/status"
wait_for_router_ready "$container_name"

assert_http_contains "${dashboard_base_url}/" 'data-dashboard="ghostship-hermes-dashboard"'
assert_http_contains "${dashboard_base_url}/" 'data-dashboard-style="hermes-studio"'
assert_http_contains "${dashboard_base_url}/" 'data-home-view="environment"'
assert_http_contains "${dashboard_base_url}/" "Runtime"
assert_http_contains "${dashboard_base_url}/" "Providers"
assert_http_contains "${dashboard_base_url}/" "Profiles"
wait_for_json_value "${dashboard_base_url}/api/status" '.sessions | length' "0"
wait_for_json_value "${dashboard_base_url}/api/status" '.profiles[] | select(.name == "assistant") | .name' "assistant"
wait_for_json_value "${dashboard_base_url}/api/status" '.profiles[] | select(.name == "operations") | .name' "operations"
wait_for_json_value "${dashboard_base_url}/api/status" '.profiles[] | select(.name == "supervisor") | .name' "supervisor"
wait_for_json_value "${dashboard_base_url}/api/status" '.default_profile' "assistant"

open_started_ms="$(date +%s%3N)"
curl -fsS -X POST "${dashboard_base_url}/api/terminal/open" >/tmp/ghostship-hermes-terminal-open-1.json
open_finished_ms="$(date +%s%3N)"
test $((open_finished_ms - open_started_ms)) -lt 2000
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
wait_for_json_value "${dashboard_base_url}/api/status" ".sessions[] | select(.id == \"$terminal_one\") | .id" "$terminal_one"
wait_for_json_value "${dashboard_base_url}/api/status" ".sessions[] | select(.id == \"$terminal_two\") | .id" "$terminal_two"
assert_websocket_proxy "$terminal_two_url"

curl -fsS -X POST "${dashboard_base_url}/api/terminals/$terminal_two/close" >/tmp/ghostship-hermes-terminal-close-2.json
wait_for_json_value "${dashboard_base_url}/api/status" ".sessions[] | select(.id == \"$terminal_one\") | .id" "$terminal_one"

curl -fsS -X POST "${dashboard_base_url}/api/terminals/$terminal_one/close" >/tmp/ghostship-hermes-terminal-close-1.json
wait_for_json_value "${dashboard_base_url}/api/status" '.sessions | length' "0"

run_in_container "$container_name" 'id hermes | grep -F "uid=3000" >/dev/null'
run_in_container "$container_name" '! systemctl is-active hermes-agent.service >/dev/null'
run_in_container "$container_name" 'test "$(systemctl show -P Result ghostship-hermes-bootstrap.service)" = "success"'
run_in_container "$container_name" 'test "$(systemctl show -P Result ghostship-hermes-user-tooling.service)" = "success"'
run_in_container "$container_name" 'systemctl cat ghostship-hermes-startup.service | grep -F "ghostship-hermes-bootstrap.service" >/dev/null'
run_in_container "$container_name" '! systemctl cat ghostship-hermes-startup.service | grep -F "ghostship-hermes-user-tooling.service" >/dev/null'
run_in_container "$container_name" '! systemctl cat ghostship-hermes-bootstrap.service | grep -F "ghostship-hermes-user-tooling.service" >/dev/null'
run_in_container "$container_name" 'systemctl is-active ghostship-hermes-router.service >/dev/null'
run_in_container "$container_name" 'systemctl is-active ghostship-hermes-profile-assistant.service >/dev/null'
run_in_container "$container_name" 'systemctl is-active ghostship-hermes-profile-operations.service >/dev/null'
run_in_container "$container_name" 'systemctl is-active ghostship-hermes-profile-supervisor.service >/dev/null'
run_in_container "$container_name" 'test "$(cat /etc/ghostship-hermes-release)" = "$(cat /home/hermes/.ghostship-hermes-release)"'
run_as_hermes "$container_name" 'hermes profile show assistant >/dev/null'
run_as_hermes "$container_name" 'hermes profile show operations >/dev/null'
run_as_hermes "$container_name" 'hermes profile show supervisor >/dev/null'
run_as_hermes "$container_name" 'test -d /home/hermes/.hermes/profiles/assistant && test -d /home/hermes/.hermes/profiles/operations && test -d /home/hermes/.hermes/profiles/supervisor'
run_as_hermes "$container_name" 'test -f /home/hermes/.hermes/.managed && test -f /home/hermes/.hermes/profiles/assistant/.managed && test -f /home/hermes/.hermes/profiles/operations/.managed && test -f /home/hermes/.hermes/profiles/supervisor/.managed'
run_as_hermes "$container_name" '! test -d /home/hermes/.hermes/profiles/coder'
run_as_hermes "$container_name" '! test -f /home/hermes/.hermes/active_profile'
run_as_hermes_default_path "$container_name" 'test "$(command -v codex)" = "/home/hermes/.local/bin/codex"'
run_as_hermes_default_path "$container_name" 'test "$(command -v opencode)" = "/home/hermes/.local/bin/opencode"'
run_as_hermes_default_path "$container_name" 'agent_browser_path="$(command -v agent-browser)"; test -n "$agent_browser_path"; test "$agent_browser_path" != "/home/hermes/.local/bin/agent-browser"; test "${agent_browser_path#"/nix/store/"}" != "$agent_browser_path"'
run_as_hermes_default_path "$container_name" '! command -v gemini >/dev/null'
run_as_hermes_default_path "$container_name" 'agent-browser --help >/tmp/ghostship-agent-browser-help.txt 2>/tmp/ghostship-agent-browser-help.err && grep -F "agent-browser - fast browser automation CLI for AI agents" /tmp/ghostship-agent-browser-help.txt >/dev/null'
run_as_hermes "$container_name" 'hermes config show 2>/dev/null | grep -F "/home/hermes" >/dev/null'
run_as_hermes "$container_name" 'test "$(command -v hermes)" = "/home/hermes/.local/state/nix/profiles/ghostship-managed/bin/hermes"'
run_as_hermes "$container_name" 'current_wrapper="$(systemctl cat ghostship-hermes-user-tooling.service | sed -n "s#.*\(/nix/store/[^: ]*-hermes-agent-wrapped-0\.1\.0\)/bin.*#\1#p" | tail -n1)"; test -n "$current_wrapper"; test "$(readlink -f "$(command -v hermes)")" = "$current_wrapper/bin/hermes"'
run_as_hermes "$container_name" 'nix profile list --profile /home/hermes/.local/state/nix/profiles/ghostship-managed --json | jq -e "[.elements | keys[] | select(. == \"hermes-agent-wrapped\" or startswith(\"hermes-agent-wrapped-\"))] | length == 1" >/dev/null'
run_as_hermes "$container_name" "node -p 'const pkg=require(\"/home/hermes/.hermes/hermes-agent/package.json\"); JSON.stringify(Object.keys(pkg.devDependencies).sort())' | grep -Fx '[\"@openai/codex\",\"opencode-ai\"]' >/dev/null"
run_as_hermes "$container_name" '! hermes --version 2>/dev/null | grep -F "legacy-default-hermes" >/dev/null'
run_as_hermes "$container_name" 'hermes -p assistant config show | grep -F "Model:" | grep -F "gpt-5.4" >/dev/null'
run_as_hermes "$container_name" 'hermes -p assistant config show | grep -F "Model:" | grep -F "openai-codex" >/dev/null'
run_as_hermes "$container_name" 'hermes -p assistant config show | grep -F "Working dir:" | grep -F "/workspace" >/dev/null'
run_as_hermes "$container_name" 'hermes -p assistant config show | grep -F "Vision" | grep -F "gemini-3.1-flash-lite-preview" >/dev/null'
run_as_hermes "$container_name" 'grep -F "provider: holographic" /home/hermes/.hermes/profiles/assistant/config.yaml >/dev/null'
run_as_hermes "$container_name" 'grep -F "cloud_provider: local" /home/hermes/.hermes/profiles/assistant/config.yaml >/dev/null'
run_as_hermes "$container_name" 'grep -F "auto_thread: false" /home/hermes/.hermes/profiles/assistant/config.yaml >/dev/null'
run_as_hermes "$container_name" 'grep -F "auto_thread: false" /home/hermes/.hermes/profiles/operations/config.yaml >/dev/null'
run_as_hermes "$container_name" 'grep -F "auto_thread: false" /home/hermes/.hermes/profiles/supervisor/config.yaml >/dev/null'
run_as_hermes "$container_name" "grep -F \"DISCORD_HOME_CHANNEL=${DISCORD_GENERAL_CHANNEL_ID}\" /home/hermes/.hermes/profiles/assistant/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_BOT_TOKEN=${DISCORD_ASSISTANT_BOT_TOKEN}\" /home/hermes/.hermes/profiles/assistant/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_ALLOWED_USERS=${DISCORD_ASSISTANT_ALLOWED_USERS}\" /home/hermes/.hermes/profiles/assistant/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_FREE_RESPONSE_CHANNELS=${DISCORD_ASSISTANT_CHANNEL_ID}\" /home/hermes/.hermes/profiles/assistant/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_HOME_CHANNEL=${DISCORD_GENERAL_CHANNEL_ID}\" /home/hermes/.hermes/profiles/operations/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_BOT_TOKEN=${DISCORD_OPERATIONS_BOT_TOKEN}\" /home/hermes/.hermes/profiles/operations/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_ALLOWED_USERS=${DISCORD_OPERATIONS_ALLOWED_USERS}\" /home/hermes/.hermes/profiles/operations/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_FREE_RESPONSE_CHANNELS=${DISCORD_OPERATIONS_CHANNEL_ID}\" /home/hermes/.hermes/profiles/operations/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_HOME_CHANNEL=${DISCORD_GENERAL_CHANNEL_ID}\" /home/hermes/.hermes/profiles/supervisor/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_BOT_TOKEN=${DISCORD_SUPERVISOR_BOT_TOKEN}\" /home/hermes/.hermes/profiles/supervisor/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_ALLOWED_USERS=${DISCORD_SUPERVISOR_ALLOWED_USERS}\" /home/hermes/.hermes/profiles/supervisor/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_FREE_RESPONSE_CHANNELS=${DISCORD_SUPERVISOR_CHANNEL_ID}\" /home/hermes/.hermes/profiles/supervisor/.env >/dev/null"
assert_gateway_pid_contract "$container_name" assistant
assert_gateway_pid_contract "$container_name" operations
assert_gateway_pid_contract "$container_name" supervisor
run_as_hermes "$container_name" 'test "$(sha256sum /home/hermes/seeds/profiles/assistant/SOUL.md | cut -d" " -f1)" = "$(sha256sum /home/hermes/.hermes/profiles/assistant/SOUL.md | cut -d" " -f1)"'
run_as_hermes "$container_name" 'test "$(sha256sum /home/hermes/seeds/profiles/operations/SOUL.md | cut -d" " -f1)" = "$(sha256sum /home/hermes/.hermes/profiles/operations/SOUL.md | cut -d" " -f1)"'
run_as_hermes "$container_name" 'test "$(sha256sum /home/hermes/seeds/profiles/supervisor/SOUL.md | cut -d" " -f1)" = "$(sha256sum /home/hermes/.hermes/profiles/supervisor/SOUL.md | cut -d" " -f1)"'
run_as_hermes "$container_name" 'test -f /home/hermes/.hermes/profiles/assistant/SOUL.md.ghostship-seeded-sha256'
run_as_hermes "$container_name" 'printf "agent-edited soul\n" >/home/hermes/.hermes/profiles/assistant/SOUL.md'
run_in_container "$container_name" 'systemctl start ghostship-hermes-bootstrap.service'
run_as_hermes "$container_name" 'grep -Fx "agent-edited soul" /home/hermes/.hermes/profiles/assistant/SOUL.md >/dev/null'
run_as_hermes "$container_name" 'hermes gateway status | grep -F "Managed gateway runtime is enabled" >/dev/null'
run_as_hermes "$container_name" 'hermes gateway status | grep -F "assistant: active (ghostship-hermes-profile-assistant.service)" >/dev/null'
run_as_hermes "$container_name" 'hermes -p assistant gateway status | grep -F "Managed gateway for profile '\''assistant'\'' is running" >/dev/null'
run_as_hermes "$container_name" 'hermes -p assistant gateway status | grep -F "Service: ghostship-hermes-profile-assistant.service" >/dev/null'
run_as_hermes "$container_name" 'hermes doctor | grep -F "operations: gateway running" >/dev/null'
run_as_hermes "$container_name" '! hermes doctor 2>&1 | grep -F "agent-browser not found" >/dev/null'
run_as_hermes "$container_name" 'hermes -p assistant gateway restart | grep -F "systemctl restart ghostship-hermes-profile-assistant.service" >/dev/null'
run_in_container "$container_name" 'systemctl is-active ghostship-dashboard-controller.service >/dev/null'
run_in_container "$container_name" 'systemctl cat ghostship-hermes-profile-assistant.service | grep -F "WorkingDirectory=/workspace" >/dev/null'
run_in_container "$container_name" 'systemctl cat ghostship-hermes-profile-operations.service | grep -F "WorkingDirectory=/workspace" >/dev/null'
run_in_container "$container_name" 'systemctl cat ghostship-hermes-profile-supervisor.service | grep -F "WorkingDirectory=/workspace" >/dev/null'
run_as_hermes "$container_name" 'printf "DISCORD_FREE_RESPONSE_CHANNELS=stale\n" >> /home/hermes/.hermes/profiles/assistant/.env'
run_as_hermes "$container_name" 'bootstrap_script="$(systemctl cat ghostship-hermes-bootstrap.service | sed -n '\''s/^ExecStart=//p'\'' | head -n1)"; test -n "$bootstrap_script"; env -u DISCORD_ASSISTANT_CHANNEL_ID "$bootstrap_script"'
run_as_hermes "$container_name" '! grep -F "DISCORD_FREE_RESPONSE_CHANNELS=stale" /home/hermes/.hermes/profiles/assistant/.env >/dev/null'
run_as_hermes "$container_name" '! grep -F "DISCORD_FREE_RESPONSE_CHANNELS=${DISCORD_ASSISTANT_CHANNEL_ID}" /home/hermes/.hermes/profiles/assistant/.env >/dev/null'
run_as_hermes "$container_name" 'bootstrap_script="$(systemctl cat ghostship-hermes-bootstrap.service | sed -n '\''s/^ExecStart=//p'\'' | head -n1)"; test -n "$bootstrap_script"; "$bootstrap_script"'
run_as_hermes "$container_name" "grep -F \"DISCORD_FREE_RESPONSE_CHANNELS=${DISCORD_ASSISTANT_CHANNEL_ID}\" /home/hermes/.hermes/profiles/assistant/.env >/dev/null"
assert_gateway_pid_contract "$container_name" assistant
