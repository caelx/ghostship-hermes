#!/usr/bin/env bash
set -euo pipefail

image_ref="${1:?usage: single-agent-dashboard.sh <image-ref>}"
container_name="ghostship-hermes-dashboard-test"
dashboard_port="${GHOSTSHIP_TEST_DASHBOARD_PORT:-17681}"
tmp_root="$(mktemp -d)"
home_dir="$tmp_root/home"
workspace_dir="$tmp_root/workspace"
nix_dir="$tmp_root/nix"
host_uid="$(id -u)"
host_gid="$(id -g)"

container_engine="${CONTAINER_ENGINE:-}"
if [ -z "$container_engine" ]; then
  if command -v docker >/dev/null 2>&1; then
    container_engine="docker"
  elif command -v podman >/dev/null 2>&1; then
    container_engine="podman"
  else
    echo "docker or podman is required for image testing" >&2
    exit 1
  fi
fi

cleanup() {
  "$container_engine" rm -f "$container_name" >/dev/null 2>&1 || true
  if "$container_engine" image inspect "$image_ref" >/dev/null 2>&1; then
    "$container_engine" run --rm --entrypoint /bin/sh -u 0:0 -v "$tmp_root:/cleanup" "$image_ref" -lc '
      chown -R '"$host_uid:$host_gid"' /cleanup >/dev/null 2>&1 || true
      chmod -R u+w /cleanup >/dev/null 2>&1 || true
    ' >/dev/null 2>&1 || true
  fi
  rm -rf "$tmp_root" >/dev/null 2>&1 || true
}
trap cleanup EXIT

wait_for_http() {
  local url="$1"
  local attempts="${2:-90}"
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

wait_for_container_http() {
  local target_container="$1"
  local url="$2"
  local attempts="${3:-90}"
  local delay="${4:-2}"
  local try=1

  while [ "$try" -le "$attempts" ]; do
    if "$container_engine" exec "$target_container" /bin/sh -lc "curl -fsS \"$url\" >/dev/null" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
    try=$((try + 1))
  done

  return 1
}

run_in_container() {
  local target_container="$1"
  shift
  "$container_engine" exec "$target_container" /bin/sh -lc "$*"
}

run_as_hermes() {
  local target_container="$1"
  shift
  "$container_engine" exec --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env PATH=/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin "$target_container" /bin/sh -lc "$*"
}

mkdir -p "$home_dir" "$workspace_dir" "$nix_dir"

"$container_engine" rm -f "$container_name" >/dev/null 2>&1 || true
"$container_engine" run -d \
  --name "$container_name" \
  --publish "${dashboard_port}:7681" \
  --volume "$home_dir:/home/hermes" \
  --volume "$workspace_dir:/workspace" \
  --volume "$nix_dir:/nix" \
  --env OPENAI_API_KEY=test-openai \
  --env OPENROUTER_API_KEY=test-openrouter \
  --env OPENCODE_GO_API_KEY=test-opencode \
  --env GOOGLE_AI_STUDIO_API_KEY=test-google \
  --env DISCORD_BOT_TOKEN=test-discord-token \
  --env DISCORD_ALLOWED_USERS=1 \
  --env DISCORD_HOME_CHANNEL=2 \
  --env GHOSTSHIP_ROUTER_CHANNEL=3 \
  --env GHOSTSHIP_DEEPTHINK_CHANNEL=4 \
  --env WEBHOOK_SECRET=test-webhook-secret \
  "$image_ref" >/dev/null

wait_for_http "http://127.0.0.1:${dashboard_port}/api/status"
wait_for_http "http://127.0.0.1:${dashboard_port}/terminal/"
wait_for_container_http "$container_name" "http://127.0.0.1:8788/readyz"

status_json="$(curl -fsS "http://127.0.0.1:${dashboard_port}/api/status")"
printf '%s' "$status_json" | python3 -c 'import json, sys; data = json.load(sys.stdin); assert data["hermes_home"] == "/home/hermes/.hermes"; assert data["gateway_state"] is not None'

run_in_container "$container_name" 'python3 -c '\''import json, urllib.request; data = json.load(urllib.request.urlopen("http://127.0.0.1:8788/readyz")); assert data["ok"] is True'\'''
curl -fsSI "http://127.0.0.1:${dashboard_port}/terminal/" >/dev/null
bundle="$(curl -fsS "http://127.0.0.1:${dashboard_port}/" | sed -n 's/.*src=\"\([^\"]*index-[^\"]*\.js\)\".*/\1/p' | head -n1)"
curl -fsS "http://127.0.0.1:${dashboard_port}${bundle}" | grep -q '/terminal/'

run_in_container "$container_name" 'command -v nix >/dev/null && command -v git >/dev/null && command -v rg >/dev/null && command -v ttyd >/dev/null && command -v tmux >/dev/null && command -v agent-browser >/dev/null'
run_as_hermes "$container_name" '/opt/hermes/venv/bin/hermes gateway status >/tmp/gateway-status.txt && cat /tmp/gateway-status.txt'

doctor_output="$(run_as_hermes "$container_name" '/opt/hermes/venv/bin/hermes doctor' || true)"
grep -q '✓ git' <<<"$doctor_output"
grep -q '✓ ripgrep' <<<"$doctor_output"
grep -q '✓ codex CLI' <<<"$doctor_output"
grep -q '✓ ~/.hermes/skills/ exists' <<<"$doctor_output"

run_as_hermes "$container_name" 'tmux kill-session -t themecheck >/dev/null 2>&1 || true; tmux new-session -d -s themecheck sleep 600; tmux show -gv status-style | grep -Fx "bg=#041C1C,fg=#FFE6CB"; tmux show -gv pane-active-border-style | grep -Fx "fg=#67E8F9"'

run_in_container "$container_name" 'printf smoke-home > /home/hermes/persist-home.txt && printf smoke-workspace > /workspace/persist-workspace.txt && chown hermes:hermes /home/hermes/persist-home.txt /workspace/persist-workspace.txt'
run_as_hermes "$container_name" "nix --extra-experimental-features 'nix-command flakes' profile add nixpkgs#hello"
run_as_hermes "$container_name" 'hello | head -n1 | grep -Fx "Hello, world!"'

"$container_engine" restart "$container_name" >/dev/null
wait_for_http "http://127.0.0.1:${dashboard_port}/api/status"
run_in_container "$container_name" 'grep -Fx "smoke-home" /home/hermes/persist-home.txt >/dev/null && grep -Fx "smoke-workspace" /workspace/persist-workspace.txt >/dev/null'
run_as_hermes "$container_name" 'hello | head -n1 | grep -Fx "Hello, world!"'

"$container_engine" rm -f "$container_name" >/dev/null
"$container_engine" run -d \
  --name "$container_name" \
  --publish "${dashboard_port}:7681" \
  --volume "$home_dir:/home/hermes" \
  --volume "$workspace_dir:/workspace" \
  --volume "$nix_dir:/nix" \
  --env OPENAI_API_KEY=test-openai \
  --env OPENROUTER_API_KEY=test-openrouter \
  --env OPENCODE_GO_API_KEY=test-opencode \
  --env GOOGLE_AI_STUDIO_API_KEY=test-google \
  --env DISCORD_BOT_TOKEN=test-discord-token \
  --env DISCORD_ALLOWED_USERS=1 \
  --env DISCORD_HOME_CHANNEL=2 \
  --env GHOSTSHIP_ROUTER_CHANNEL=3 \
  --env GHOSTSHIP_DEEPTHINK_CHANNEL=4 \
  --env WEBHOOK_SECRET=test-webhook-secret \
  "$image_ref" >/dev/null

wait_for_http "http://127.0.0.1:${dashboard_port}/api/status"
run_in_container "$container_name" 'grep -Fx "smoke-home" /home/hermes/persist-home.txt >/dev/null && grep -Fx "smoke-workspace" /workspace/persist-workspace.txt >/dev/null'
run_as_hermes "$container_name" 'hello | head -n1 | grep -Fx "Hello, world!"'
