#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
image_bundle="${1:?usage: single-agent-dashboard.sh <image-bundle> [image-tag]}"
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

: "${DISCORD_BOT_TOKEN:=single-agent-bot-token}"
: "${DISCORD_ALLOWED_USERS:=single-agent-user}"
: "${DISCORD_FREE_RESPONSE_CHANNELS:=single-agent-channel}"
: "${DISCORD_HOME_CHANNEL:=single-agent-home}"
: "${WEBHOOK_SECRET:=single-agent-webhook-secret}"
: "${BROWSER_CDP_URL:=ws://single-agent-browser.example/ws}"
: "${PLEX_URL:=http://plex.example:32400}"
: "${PLEX_TOKEN:=plex-token}"
: "${CHAPTARR_URL:=http://chaptarr.example:8789}"
: "${CHAPTARR_API_KEY:=chaptarr-token}"
: "${CHAPTARR_API_PATH:=api}"
: "${CHAPTARR_API_VERSION:=v1}"
: "${N8N_URL:=http://n8n.example:5678}"
: "${N8N_API_KEY:=n8n-token}"
: "${N8N_PUBLIC_API_ENDPOINT:=api/v1}"
: "${N8N_PUBLIC_API_VERSION:=v1}"
: "${GHOSTSHIP_ROUTER_API_KEY:=router-secret}"

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

assert_http_not_contains() {
  local url="$1"
  local pattern="$2"
  local body

  body="$(curl -fsS "$url")"
  ! grep -q "$pattern" <<<"$body"
}

run_in_container() {
  local target_container="$1"
  shift
  docker exec \
    -e PATH="$container_path" \
    "$target_container" \
    "$container_shell" -lc "$*"
}

run_as_hermes() {
  local target_container="$1"
  shift
  docker exec \
    -u 3000:3000 \
    -e HOME=/home/hermes \
    -e HERMES_HOME=/home/hermes/.hermes \
    -e TERMINAL_CWD=/home/hermes \
    -e PATH=/home/hermes/.local/bin:/home/hermes/.local/state/nix/profiles/ghostship-managed/bin:/home/hermes/.nix-profile/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/bin \
    "$target_container" \
    "$container_shell" -lc "$*"
}

run_as_hermes_default_path() {
  local target_container="$1"
  shift
  docker exec \
    -u 3000:3000 \
    -e HOME=/home/hermes \
    -e HERMES_HOME=/home/hermes/.hermes \
    -e TERMINAL_CWD=/home/hermes \
    "$target_container" \
    "$container_shell" -lc "$*"
}

wait_for_router_ready() {
  local target_container="$1"
  local attempts="${2:-60}"
  local delay="${3:-2}"
  local try=1

  while [ "$try" -le "$attempts" ]; do
    if run_in_container "$target_container" 'systemctl is-active ghostship-hermes-router.service >/dev/null 2>&1 && curl -fsS http://127.0.0.1:8788/readyz >/dev/null 2>&1'; then
      return 0
    fi
    sleep "$delay"
    try=$((try + 1))
  done

  return 1
}

assert_router_inventory() {
  local target_container="$1"
  run_in_container "$target_container" "curl -fsS ${router_base_url}/v1/models | jq -e '[.data[].id] | index(\"auxiliary\") and index(\"coding\") and index(\"agentic\") and index(\"vision\") and index(\"tts\")' >/dev/null"
}

assert_model_config() {
  local target_container="$1"
  run_as_hermes "$target_container" 'hermes config show | grep -F "provider: opencode-go" >/dev/null'
  run_as_hermes "$target_container" 'hermes config show | grep -F "default: minimax-m2.7" >/dev/null'
  run_as_hermes "$target_container" 'hermes config show | grep -F "fallback_model:" >/dev/null'
  run_as_hermes "$target_container" 'hermes config show | grep -F "provider: custom" >/dev/null'
  run_as_hermes "$target_container" 'hermes config show | grep -F "model: agentic" >/dev/null'
  run_as_hermes "$target_container" 'hermes config show | grep -F "base_url: http://127.0.0.1:8788/v1" >/dev/null'
  run_as_hermes "$target_container" 'hermes config show | grep -F "api_key_env: OPENAI_API_KEY" >/dev/null'
  run_in_container "$target_container" 'printenv GHOSTSHIP_ROUTER_DISABLED_MODELS | grep -Fx "openrouter/free" >/dev/null'
  run_in_container "$target_container" "curl -fsS http://127.0.0.1:7681/api/status | jq -e ' .environment.model == \"minimax-m2.7\" and .environment.model_provider == \"opencode-go\" and .environment.fallback_model == \"agentic\" and .environment.fallback_provider == \"custom\" and .environment.router_disabled_models == \"openrouter/free\" ' >/dev/null"
}

assert_gateway_pid_contract() {
  local target_container="$1"
  run_as_hermes "$target_container" 'pid=$(jq -r ".pid" /home/hermes/.hermes/gateway.pid); kind=$(jq -r ".kind" /home/hermes/.hermes/gateway.pid); argv=$(jq -r ".argv | join(\" \")" /home/hermes/.hermes/gateway.pid); test -n "$pid"; test "$kind" = "hermes-gateway"; printf "%s" "$argv" | grep -F "hermes gateway run --replace" >/dev/null; kill -0 "$pid"'
  run_as_hermes "$target_container" 'pid=$(jq -r ".pid" /home/hermes/.hermes/gateway.pid); ps -p "$pid" -o args= | grep -F "gateway run --replace" >/dev/null'
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

find_browser_executable() {
  if [ -n "${GHOSTSHIP_TEST_BROWSER_EXECUTABLE:-}" ]; then
    printf '%s\n' "$GHOSTSHIP_TEST_BROWSER_EXECUTABLE"
    return 0
  fi

  local candidate
  for candidate in chromium chromium-browser google-chrome google-chrome-stable chrome; do
    if command -v "$candidate" >/dev/null 2>&1; then
      command -v "$candidate"
      return 0
    fi
  done

  return 1
}

assert_dashboard_browser_open() {
  local browser_executable
  if ! browser_executable="$(find_browser_executable)"; then
    echo "Skipping browser-driven dashboard validation: no browser executable found" >&2
    return 0
  fi

  local browser_session="ghostship-dashboard-e2e-$$"
  local browser_args=(
    --session "$browser_session"
    --executable-path "$browser_executable"
    --allowed-domains 127.0.0.1,localhost
    --json
  )

  agent-browser "${browser_args[@]}" open "${dashboard_base_url}/" >/tmp/ghostship-agent-browser-open.json
  agent-browser "${browser_args[@]}" click "#open-terminal" >/tmp/ghostship-agent-browser-click.json
  agent-browser "${browser_args[@]}" wait "iframe.terminal-frame" >/tmp/ghostship-agent-browser-wait-frame.json
  agent-browser "${browser_args[@]}" wait 1500 >/tmp/ghostship-agent-browser-wait-time.json
  agent-browser "${browser_args[@]}" is visible "iframe.terminal-frame" >/tmp/ghostship-agent-browser-visible.json
  agent-browser "${browser_args[@]}" eval '(() => document.querySelector("iframe.terminal-frame")?.getAttribute("src") || "")()' >/tmp/ghostship-agent-browser-frame-src.json
  jq -r '.data.result // empty' /tmp/ghostship-agent-browser-frame-src.json | grep -E '^/terminals/.+/$' >/dev/null
  agent-browser --session "$browser_session" close --all >/dev/null 2>&1 || true
}

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for dashboard image testing" >&2
  exit 1
fi

if ! docker version >/dev/null 2>&1; then
  echo "docker is installed but not reachable from this shell" >&2
  exit 1
fi

if [ "${SKIP_IMAGE_IMPORT:-0}" != "1" ]; then
  "$repo_root/scripts/export_publishable_image.sh" "$image_bundle" "$image_tag" >/dev/null
fi

mkdir -p "$home_dir/.nix-profile/bin" "$home_dir/seeds/skills/workflow-single" "$workspace_dir" "$home_dir/.hermes/profiles/assistant"
cat > "$home_dir/.nix-profile/bin/hermes" <<'EOF'
#!/bin/sh
echo legacy-default-hermes
EOF
chmod +x "$home_dir/.nix-profile/bin/hermes"
printf 'seed-skill-v1\n' > "$home_dir/seeds/skills/workflow-single/SKILL.md"
printf 'seed-soul-v1\n' > "$home_dir/seeds/SOUL.md"
chmod 0555 "$home_dir/seeds/skills/workflow-single"
chmod 0444 "$home_dir/seeds/skills/workflow-single/SKILL.md"
printf 'legacy-profile\n' > "$home_dir/.hermes/profiles/assistant/.managed"
printf 'assistant\n' > "$home_dir/.hermes/active_profile"
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
  -e DISCORD_BOT_TOKEN \
  -e DISCORD_ALLOWED_USERS \
  -e DISCORD_FREE_RESPONSE_CHANNELS \
  -e DISCORD_HOME_CHANNEL \
  -e WEBHOOK_SECRET \
  -e BROWSER_CDP_URL \
  -e PLEX_URL \
  -e PLEX_TOKEN \
  -e CHAPTARR_URL \
  -e CHAPTARR_API_KEY \
  -e CHAPTARR_API_PATH \
  -e CHAPTARR_API_VERSION \
  -e N8N_URL \
  -e N8N_API_KEY \
  -e N8N_PUBLIC_API_ENDPOINT \
  -e N8N_PUBLIC_API_VERSION \
  -e GHOSTSHIP_ROUTER_API_KEY \
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
assert_http_contains "${dashboard_base_url}/" "Agent"
assert_http_not_contains "${dashboard_base_url}/" "Profiles"
wait_for_json_value "${dashboard_base_url}/api/status" '.sessions | length' "0"
wait_for_json_value "${dashboard_base_url}/api/status" '.environment.agent.service' "ghostship-hermes-gateway.service"
curl -fsS "${dashboard_base_url}/api/status" | jq -e 'has("profiles") | not' >/dev/null

open_started_ms="$(date +%s%3N)"
curl -fsS -X POST "${dashboard_base_url}/api/terminal/open" >/tmp/ghostship-hermes-terminal-open-1.json
open_finished_ms="$(date +%s%3N)"
test $((open_finished_ms - open_started_ms)) -lt 2000
terminal_one="$(jq -r '.active_terminal_id' /tmp/ghostship-hermes-terminal-open-1.json)"
terminal_one_url="$(jq -r '.sessions[] | select(.id == "'"$terminal_one"'") | .terminal_url' /tmp/ghostship-hermes-terminal-open-1.json)"
wait_for_http "${dashboard_base_url}${terminal_one_url}"
wait_for_json_value "${dashboard_base_url}/api/status" ".sessions[] | select(.id == \"$terminal_one\") | .ready" "true"
assert_http_contains "${dashboard_base_url}${terminal_one_url}" "ttyd"
assert_websocket_proxy "$terminal_one_url"
assert_dashboard_browser_open

curl -fsS -X POST "${dashboard_base_url}/api/terminals/$terminal_one/close" >/tmp/ghostship-hermes-terminal-close-1.json
wait_for_json_value "${dashboard_base_url}/api/status" '.sessions | length' "0"

run_in_container "$container_name" 'id hermes | grep -F "uid=3000" >/dev/null'
run_in_container "$container_name" '! systemctl is-active hermes-agent.service >/dev/null'
run_in_container "$container_name" 'systemctl is-active ghostship-hermes-router.service >/dev/null'
run_in_container "$container_name" 'systemctl is-active ghostship-hermes-gateway.service >/dev/null'
run_in_container "$container_name" 'test "$(cat /etc/ghostship-hermes-release)" = "$(cat /home/hermes/.ghostship-hermes-release)"'
run_in_container "$container_name" 'systemctl cat ghostship-hermes-gateway.service | grep -F "WorkingDirectory=/workspace" >/dev/null'
run_as_hermes "$container_name" 'test -f /home/hermes/.hermes/.managed'
run_as_hermes "$container_name" '! test -d /home/hermes/.hermes/profiles'
run_as_hermes "$container_name" '! test -f /home/hermes/.hermes/active_profile'
run_as_hermes_default_path "$container_name" 'test "$(command -v codex)" = "/home/hermes/.local/bin/codex"'
run_as_hermes_default_path "$container_name" 'test "$(command -v opencode)" = "/home/hermes/.local/bin/opencode"'
run_as_hermes_default_path "$container_name" 'agent_browser_path="$(command -v agent-browser)"; test -n "$agent_browser_path"; test "$agent_browser_path" != "/home/hermes/.local/bin/agent-browser"; test "${agent_browser_path#"/nix/store/"}" != "$agent_browser_path"'
run_as_hermes_default_path "$container_name" 'command -v gh >/dev/null'
run_as_hermes_default_path "$container_name" 'command -v ssh >/dev/null'
run_as_hermes_default_path "$container_name" 'command -v scp >/dev/null'
run_as_hermes_default_path "$container_name" 'command -v ssh-keygen >/dev/null'
run_as_hermes_default_path "$container_name" 'test "$(command -v fd)" = "/home/hermes/.local/state/nix/profiles/ghostship-managed/bin/fd"'
run_as_hermes_default_path "$container_name" 'test "$(command -v uv)" = "/home/hermes/.local/state/nix/profiles/ghostship-managed/bin/uv"'
run_as_hermes_default_path "$container_name" 'test "$(command -v yq)" = "/home/hermes/.local/state/nix/profiles/ghostship-managed/bin/yq"'
run_as_hermes_default_path "$container_name" 'test "$(command -v tmux)" = "/home/hermes/.local/state/nix/profiles/ghostship-managed/bin/tmux"'
run_as_hermes_default_path "$container_name" 'test "$(command -v python3)" = "/home/hermes/.local/state/nix/profiles/ghostship-managed/bin/python3"'
run_as_hermes_default_path "$container_name" 'test "$(command -v pip)" = "/home/hermes/.local/state/nix/profiles/ghostship-managed/bin/pip"'
run_as_hermes_default_path "$container_name" '! command -v gemini >/dev/null'
run_as_hermes_default_path "$container_name" 'agent-browser --help >/tmp/ghostship-agent-browser-help.txt 2>/tmp/ghostship-agent-browser-help.err && grep -F "agent-browser - fast browser automation CLI for AI agents" /tmp/ghostship-agent-browser-help.txt >/dev/null'
run_as_hermes_default_path "$container_name" 'fd --version >/dev/null'
run_as_hermes_default_path "$container_name" 'uv --version >/dev/null'
run_as_hermes_default_path "$container_name" 'yq --version >/dev/null'
run_as_hermes_default_path "$container_name" 'tmux -V >/dev/null'
run_as_hermes_default_path "$container_name" 'python3 --version >/tmp/ghostship-python-version.txt && grep -F "Python 3." /tmp/ghostship-python-version.txt >/dev/null'
run_as_hermes_default_path "$container_name" 'pip --version >/tmp/ghostship-pip-version.txt && grep -F "pip " /tmp/ghostship-pip-version.txt >/dev/null'
run_as_hermes_default_path "$container_name" 'python3 -m pip --version >/tmp/ghostship-python-module-pip-version.txt && grep -F "pip " /tmp/ghostship-python-module-pip-version.txt >/dev/null'
run_as_hermes "$container_name" 'hermes config show 2>/dev/null | grep -F "/home/hermes" >/dev/null'
run_as_hermes "$container_name" 'test "$(command -v hermes)" = "/home/hermes/.local/state/nix/profiles/ghostship-managed/bin/hermes"'
run_as_hermes "$container_name" '! hermes --version 2>/dev/null | grep -F "legacy-default-hermes" >/dev/null'
assert_router_inventory "$container_name"
assert_model_config "$container_name"
run_as_hermes "$container_name" "grep -F \"DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}\" /home/hermes/.hermes/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_ALLOWED_USERS=${DISCORD_ALLOWED_USERS}\" /home/hermes/.hermes/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_FREE_RESPONSE_CHANNELS=${DISCORD_FREE_RESPONSE_CHANNELS}\" /home/hermes/.hermes/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"DISCORD_HOME_CHANNEL=${DISCORD_HOME_CHANNEL}\" /home/hermes/.hermes/.env >/dev/null"
run_as_hermes "$container_name" 'grep -F "WEBHOOK_ENABLED=true" /home/hermes/.hermes/.env >/dev/null'
run_as_hermes "$container_name" 'grep -F "WEBHOOK_PORT=8644" /home/hermes/.hermes/.env >/dev/null'
run_as_hermes "$container_name" "grep -F \"WEBHOOK_SECRET=${WEBHOOK_SECRET}\" /home/hermes/.hermes/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"BROWSER_CDP_URL=${BROWSER_CDP_URL}\" /home/hermes/.hermes/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"PLEX_URL=${PLEX_URL}\" /home/hermes/.hermes/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"CHAPTARR_URL=${CHAPTARR_URL}\" /home/hermes/.hermes/.env >/dev/null"
run_as_hermes "$container_name" "grep -F \"CHAPTARR_API_KEY=${CHAPTARR_API_KEY}\" /home/hermes/.hermes/.env >/dev/null"
run_as_hermes "$container_name" '! grep -F "CHAPTARR_API_PATH=" /home/hermes/.hermes/.env >/dev/null'
run_as_hermes "$container_name" '! grep -F "CHAPTARR_API_VERSION=" /home/hermes/.hermes/.env >/dev/null'
run_as_hermes "$container_name" '! grep -F "N8N_PUBLIC_API_ENDPOINT=" /home/hermes/.hermes/.env >/dev/null'
run_as_hermes "$container_name" '! grep -F "N8N_PUBLIC_API_VERSION=" /home/hermes/.hermes/.env >/dev/null'
run_as_hermes "$container_name" '! grep -F "GHOSTSHIP_ROUTER_API_KEY=" /home/hermes/.hermes/.env >/dev/null'
run_as_hermes "$container_name" 'grep -Fx "seed-skill-v1" /home/hermes/.hermes/skills/workflow-single/SKILL.md >/dev/null'
run_as_hermes "$container_name" 'test -w /home/hermes/.hermes/skills/workflow-single'
run_as_hermes "$container_name" 'test -w /home/hermes/.hermes/skills/workflow-single/SKILL.md'
run_as_hermes "$container_name" '! test -e /home/hermes/.hermes/profiles/assistant/skills/workflow-single/SKILL.md'
run_as_hermes "$container_name" 'mkdir -p /home/hermes/.hermes/skills/autonomous-ai-agents/codex && printf "built-in skill\n" >/home/hermes/.hermes/skills/autonomous-ai-agents/codex/SKILL.md && chmod 0555 /home/hermes/.hermes/skills/autonomous-ai-agents /home/hermes/.hermes/skills/autonomous-ai-agents/codex && chmod 0444 /home/hermes/.hermes/skills/autonomous-ai-agents/codex/SKILL.md'
run_in_container "$container_name" 'systemctl start ghostship-hermes-bootstrap.service'
run_as_hermes "$container_name" 'grep -Fx "built-in skill" /home/hermes/.hermes/skills/autonomous-ai-agents/codex/SKILL.md >/dev/null'
run_as_hermes "$container_name" 'test -w /home/hermes/.hermes/skills/autonomous-ai-agents/codex'
run_as_hermes "$container_name" 'test -w /home/hermes/.hermes/skills/autonomous-ai-agents/codex/SKILL.md'
run_as_hermes "$container_name" 'grep -Fx "seed-soul-v1" /home/hermes/.hermes/SOUL.md >/dev/null'
run_as_hermes "$container_name" 'test -f /home/hermes/.hermes/SOUL.md.ghostship-seeded-sha256'
run_as_hermes "$container_name" 'printf "%s" "You are Hermes Agent, an intelligent AI assistant created by Nous Research. You are helpful, knowledgeable, and direct. You assist users with a wide range of tasks including answering questions, writing and editing code, analyzing information, creative work, and executing actions via your tools. You communicate clearly, admit uncertainty when appropriate, and prioritize being genuinely useful over being verbose unless otherwise directed below. Be targeted and efficient in your exploration and investigations." >/home/hermes/.hermes/SOUL.md && rm -f /home/hermes/.hermes/SOUL.md.ghostship-seeded-sha256'
run_in_container "$container_name" 'systemctl start ghostship-hermes-bootstrap.service'
run_as_hermes "$container_name" 'grep -Fx "seed-soul-v1" /home/hermes/.hermes/SOUL.md >/dev/null'
run_as_hermes "$container_name" 'test -f /home/hermes/.hermes/SOUL.md.ghostship-seeded-sha256'
run_as_hermes "$container_name" 'printf "agent-edited soul\n" >/home/hermes/.hermes/SOUL.md'
run_in_container "$container_name" 'systemctl start ghostship-hermes-bootstrap.service'
run_as_hermes "$container_name" 'grep -Fx "agent-edited soul" /home/hermes/.hermes/SOUL.md >/dev/null'
run_as_hermes "$container_name" 'hermes doctor >/dev/null'
assert_gateway_pid_contract "$container_name"
run_as_hermes "$container_name" 'hermes gateway status | grep -F "Managed gateway service is running" >/dev/null'
run_as_hermes "$container_name" 'hermes gateway status | grep -F "ghostship-hermes-gateway.service" >/dev/null'
run_as_hermes "$container_name" 'hermes gateway restart | grep -F "systemctl restart ghostship-hermes-gateway.service" >/dev/null'

printf 'validated ghostship-hermes dashboard smoke test with %s\n' "$image_tag"
