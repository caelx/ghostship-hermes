#!/usr/bin/env bash
set -Eeuo pipefail

image_ref="${1:?usage: single-agent-dashboard.sh <image-ref>}"
container_name="ghostship-hermes-dashboard-test"
dashboard_port="${GHOSTSHIP_TEST_DASHBOARD_PORT:-}"
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

dump_failure_state() {
  local exit_code="$1"
  if [ "$exit_code" -eq 0 ]; then
    return
  fi
  if ! "$container_engine" ps -a --format '{{.Names}}' | grep -Fx "$container_name" >/dev/null 2>&1; then
    return
  fi

  echo "===== container logs: $container_name =====" >&2
  "$container_engine" logs "$container_name" >&2 || true

  echo "===== browser profile tree =====" >&2
  "$container_engine" exec "$container_name" /bin/sh -lc "find /home/hermes/.local/state/cloakbrowser -maxdepth 2 -printf '%u:%g %y %p -> %l\\n' 2>/dev/null | sed -n '1,80p'" >&2 || true
  echo >&2

  echo "===== non-hermes owned paths =====" >&2
  "$container_engine" exec "$container_name" /bin/sh -lc "find /home/hermes \\! -user hermes -printf '%u:%g %y %p -> %l\\n' | sed -n '1,80p'" >&2 || true
  echo >&2
}
trap 'dump_failure_state "$?"' ERR

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

wait_for_hermes_shell() {
  local target_container="$1"
  local command="$2"
  local attempts="${3:-90}"
  local delay="${4:-2}"
  local try=1

  while [ "$try" -le "$attempts" ]; do
    if run_as_hermes "$target_container" "$command" >/dev/null 2>&1; then
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
  "$container_engine" exec --user 3000:3000 --env HOME=/home/hermes --env HERMES_HOME=/home/hermes/.hermes --env GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults --env PATH=/opt/ghostship-utils/venv/bin:/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin "$target_container" /bin/sh -lc "$*"
}

run_test_container() {
  local publish_arg=""
  if [ -n "${1:-}" ]; then
    publish_arg="${1:?missing host port}:7681"
    shift
  else
    shift || true
    publish_arg="127.0.0.1::7681"
  fi
  "$container_engine" run -d \
    --name "$container_name" \
    --publish "$publish_arg" \
    --volume "$home_dir:/home/hermes" \
    --volume "$workspace_dir:/workspace" \
    --volume "$nix_dir:/nix" \
    --env OPENROUTER_API_KEY=test-openrouter \
    --env OPENCODE_GO_API_KEY=test-opencode \
    --env GOOGLE_AI_STUDIO_API_KEY=test-google \
    --env DISCORD_BOT_TOKEN=test-discord-token \
    --env DISCORD_ALLOWED_USERS=1 \
    --env DISCORD_HOME_CHANNEL=2 \
    --env DISCORD_FREE_RESPONSE_CHANNELS=3 \
    --env GHOSTSHIP_ROUTER_CHANNEL=3 \
    --env WEBHOOK_SECRET=test-webhook-secret \
    "$image_ref" "$@"
}

container_host_port() {
  "$container_engine" port "$container_name" 7681/tcp | sed -n 's/.*:\([0-9][0-9]*\)$/\1/p' | head -n1
}

start_test_container_with_retry() {
  local target_port="${1-}"
  local create_output=""
  local attempts=1

  if [ -z "$target_port" ]; then
    attempts=5
  fi

  for _ in $(seq 1 "$attempts"); do
    if create_output="$(run_test_container "$target_port" 2>&1)"; then
      return 0
    fi
    "$container_engine" rm -f "$container_name" >/dev/null 2>&1 || true
    if ! grep -F "Address already in use" <<<"$create_output" >/dev/null 2>&1; then
      printf '%s\n' "$create_output" >&2
      return 1
    fi
    sleep 1
  done

  printf '%s\n' "$create_output" >&2
  return 1
}

smoke_note() {
  printf '== smoke: %s ==\n' "$1"
}

mkdir -p "$home_dir" "$workspace_dir" "$nix_dir"
mkdir -p "$home_dir/.hermes/skills/custom"
cat >"$home_dir/.hermes/skills/custom/SKILL.md" <<'EOF'
# Custom Skill

Custom downstream skill should survive image seeding.
EOF

"$container_engine" rm -f "$container_name" >/dev/null 2>&1 || true
start_test_container_with_retry "$dashboard_port"
[ -n "$dashboard_port" ] || dashboard_port="$(container_host_port)"

wait_for_http "http://127.0.0.1:${dashboard_port}/api/status"
wait_for_http "http://127.0.0.1:${dashboard_port}/terminal/"
wait_for_container_http "$container_name" "http://127.0.0.1:8788/readyz"

status_json="$(curl -fsS "http://127.0.0.1:${dashboard_port}/api/status")"
printf '%s' "$status_json" | python3 -c 'import json, sys; data = json.load(sys.stdin); assert data["hermes_home"] == "/home/hermes/.hermes"; assert data["gateway_state"] is not None'

run_in_container "$container_name" 'python3 -c '\''import json, urllib.request; data = json.load(urllib.request.urlopen("http://127.0.0.1:8788/readyz")); assert data["ok"] is True'\'''
curl -fsSI "http://127.0.0.1:${dashboard_port}/terminal/" >/dev/null
bundle="$(curl -fsS "http://127.0.0.1:${dashboard_port}/" | sed -n 's/.*src=\"\([^\"]*index-[^\"]*\.js\)\".*/\1/p' | head -n1)"
curl -fsS "http://127.0.0.1:${dashboard_port}${bundle}" | grep -q '/terminal/'
curl -fsS "http://127.0.0.1:${dashboard_port}${bundle}" | grep -q 'sandbox:"allow-same-origin allow-scripts allow-forms"'
! curl -fsS "http://127.0.0.1:${dashboard_port}${bundle}" | grep -q 'allow-modals'
! curl -fsS "http://127.0.0.1:${dashboard_port}${bundle}" | grep -q 'href:"/terminal/",target:"_blank"'

run_in_container "$container_name" '
for cmd in \
  nix git rg ttyd tmux tirith jq fd yq uv gh gws bws gcloud blogwatcher-cli \
  codex gemini agent-browser opencode \
  ghostship-bazarr ghostship-bookstack ghostship-changedetection ghostship-chaptarr \
  ghostship-flaresolverr ghostship-grimmory ghostship-n8n ghostship-nzbget ghostship-plex ghostship-pricebuddy \
  ghostship-prowlarr ghostship-pyload-ng ghostship-qbittorrent ghostship-radarr ghostship-romm ghostship-rss-bridge \
  ghostship-searxng ghostship-sonarr ghostship-synology ghostship-tautulli ghostship-hermes-router
do
  command -v "$cmd" >/dev/null || { echo "missing command: $cmd" >&2; exit 1; }
done
'
run_as_hermes "$container_name" 'for cmd in bws gws gh gcloud blogwatcher-cli; do command -v "$cmd" >/dev/null || exit 1; done'
run_as_hermes "$container_name" 'bws --help >/dev/null'
run_as_hermes "$container_name" 'gws --help >/dev/null'
run_as_hermes "$container_name" 'gh --help >/dev/null'
run_as_hermes "$container_name" 'gcloud --help >/dev/null'
run_as_hermes "$container_name" 'blogwatcher-cli --help >/dev/null'
smoke_note "native browser persistence"
run_as_hermes "$container_name" 'agent-browser close --all >/dev/null 2>&1 || true'
run_as_hermes "$container_name" 'agent-browser open http://127.0.0.1:7681/ >/dev/null'
run_as_hermes "$container_name" "agent-browser eval \"localStorage.setItem('ghostship-smoke','warm');\" >/dev/null"
run_as_hermes "$container_name" "agent-browser eval \"({localStorage: localStorage.getItem('ghostship-smoke')})\" | python3 -c 'import json, sys; data = json.load(sys.stdin); assert data[\"localStorage\"] == \"warm\"'"
run_as_hermes "$container_name" 'agent-browser close --all >/dev/null'
run_in_container "$container_name" 'test -d /home/hermes/.local/state/cloakbrowser'
run_in_container "$container_name" 'command -v google-chrome >/dev/null'
smoke_note "home ownership"
run_in_container "$container_name" 'test -z "$(find /home/hermes \! -user hermes -print -quit)"'
smoke_note "memory plugin import"
run_as_hermes "$container_name" '/opt/hermes/venv/bin/python -c "import plugins.memory.holographic"'
smoke_note "gateway status"
run_as_hermes "$container_name" '/opt/hermes/venv/bin/hermes gateway status >/tmp/gateway-status.txt && cat /tmp/gateway-status.txt'
smoke_note "config assertions"
run_as_hermes "$container_name" 'sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: openai-codex" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  default: gpt-5.4" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^fallback_model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: opencode-go" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^fallback_model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  model: minimax-m2.7" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^agent:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  reasoning_effort: medium" >/dev/null'
run_as_hermes "$container_name" '/opt/hermes/venv/bin/python - <<'\''PY'\''
import yaml
from pathlib import Path

config = yaml.safe_load(Path("/home/hermes/.hermes/config.yaml").read_text(encoding="utf-8"))
providers = config.get("custom_providers") or []
router = next((entry for entry in providers if entry.get("name") == "ghostship-router"), None)
assert router is not None
assert router.get("model") == "agentic"
assert router.get("base_url") == "http://127.0.0.1:8788/v1"
PY'
run_as_hermes "$container_name" '/opt/hermes/venv/bin/python - <<'\''PY'\''
import inspect
from pathlib import Path
import gateway.run

source_path = Path(inspect.getsourcefile(gateway.run))
text = source_path.read_text(encoding="utf-8")
assert "\"model\": \"agentic\"" in text
assert "ghostship-router (`agentic`)" in text
PY'
run_as_hermes "$container_name" 'sed -n "/^memory:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: holographic" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^plugins:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "    db_path: \$HERMES_HOME/memory_store.db" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^auxiliary:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "    model: gemini-2.5-flash-lite" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^auxiliary:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "    base_url: https://generativelanguage.googleapis.com/v1beta/openai/" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^auxiliary:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "    api_key: \${GOOGLE_AI_STUDIO_API_KEY}" >/dev/null'
run_as_hermes "$container_name" 'grep -F "group_sessions_per_user: true" /home/hermes/.hermes/config.yaml >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^terminal:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  timeout: 180" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^browser:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  cloud_provider: local" >/dev/null'
run_as_hermes "$container_name" '! sed -n "/^browser:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "camofox" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^discord:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  require_mention: false" >/dev/null'
run_as_hermes "$container_name" 'sed -n "/^discord:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  reactions: false" >/dev/null'
run_as_hermes "$container_name" 'grep -F "unauthorized_dm_behavior: ignore" /home/hermes/.hermes/config.yaml >/dev/null'
run_in_container "$container_name" 'test -f /home/hermes/.hermes/skills/custom/SKILL.md'
run_in_container "$container_name" 'test -f /home/hermes/.hermes/skills/autonomous-ai-agents/codex/SKILL.md'

smoke_note "doctor"
doctor_output="$(run_as_hermes "$container_name" '/opt/hermes/venv/bin/hermes doctor' || true)"
grep -q '✓ git' <<<"$doctor_output"
grep -q '✓ ripgrep' <<<"$doctor_output"
grep -q '✓ codex CLI' <<<"$doctor_output"
grep -q '✓ ~/.hermes/skills/ exists' <<<"$doctor_output"

smoke_note "tmux theme"
run_as_hermes "$container_name" 'tmux kill-session -t themecheck >/dev/null 2>&1 || true; tmux new-session -d -s themecheck sleep 600; tmux show -gv status-style | grep -Fx "bg=#041C1C,fg=#FFE6CB"; tmux show -gv pane-active-border-style | grep -Fx "fg=#67E8F9"'

smoke_note "persistence warmup"
run_in_container "$container_name" 'printf smoke-home > /home/hermes/persist-home.txt && printf smoke-workspace > /workspace/persist-workspace.txt && chown hermes:hermes /home/hermes/persist-home.txt /workspace/persist-workspace.txt'
run_as_hermes "$container_name" "nix --extra-experimental-features 'nix-command flakes' profile add nixpkgs#hello"
run_as_hermes "$container_name" 'hello | head -n1 | grep -Fx "Hello, world!"'

"$container_engine" restart "$container_name" >/dev/null
smoke_note "post-restart dashboard"
wait_for_container_http "$container_name" "http://127.0.0.1:7681/api/status"
smoke_note "post-restart persistence"
run_in_container "$container_name" 'grep -Fx "smoke-home" /home/hermes/persist-home.txt >/dev/null && grep -Fx "smoke-workspace" /workspace/persist-workspace.txt >/dev/null'
smoke_note "post-restart nix profile"
wait_for_hermes_shell "$container_name" 'hello | head -n1 | grep -Fx "Hello, world!"'
smoke_note "post-restart managed tools"
run_as_hermes "$container_name" 'for cmd in bws gws gh gcloud blogwatcher-cli; do command -v "$cmd" >/dev/null || exit 1; done'
run_as_hermes "$container_name" 'bws --help >/dev/null'
run_as_hermes "$container_name" 'gws --help >/dev/null'
run_as_hermes "$container_name" 'gh --help >/dev/null'
run_as_hermes "$container_name" 'gcloud --help >/dev/null'
run_as_hermes "$container_name" 'blogwatcher-cli --help >/dev/null'
smoke_note "post-restart browser profile"
run_as_hermes "$container_name" 'agent-browser open http://127.0.0.1:7681/ >/dev/null'
run_as_hermes "$container_name" "agent-browser eval \"({localStorage: localStorage.getItem('ghostship-smoke')})\" | python3 -c 'import json, sys; data = json.load(sys.stdin); assert data[\"localStorage\"] == \"warm\"'"
run_as_hermes "$container_name" 'agent-browser close --all >/dev/null'

"$container_engine" rm -f "$container_name" >/dev/null
start_test_container_with_retry ""
recreate_dashboard_port="$(container_host_port)"
[ -n "$recreate_dashboard_port" ] || exit 1

smoke_note "post-recreate dashboard"
wait_for_container_http "$container_name" "http://127.0.0.1:7681/api/status"
smoke_note "post-recreate persistence"
run_in_container "$container_name" 'grep -Fx "smoke-home" /home/hermes/persist-home.txt >/dev/null && grep -Fx "smoke-workspace" /workspace/persist-workspace.txt >/dev/null'
smoke_note "post-recreate nix profile"
wait_for_hermes_shell "$container_name" 'hello | head -n1 | grep -Fx "Hello, world!"'
smoke_note "post-recreate browser profile"
run_as_hermes "$container_name" 'agent-browser open http://127.0.0.1:7681/ >/dev/null'
run_as_hermes "$container_name" "agent-browser eval \"({localStorage: localStorage.getItem('ghostship-smoke')})\" | python3 -c 'import json, sys; data = json.load(sys.stdin); assert data[\"localStorage\"] == \"warm\"'"
run_as_hermes "$container_name" 'agent-browser close --all >/dev/null'
