#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for workstation validation" >&2
  exit 1
fi

if ! docker version >/dev/null 2>&1; then
  echo "docker is installed but not reachable from this shell" >&2
  exit 1
fi

nix_cmd() {
  if [ -n "${GHOSTSHIP_NIX_STORE:-}" ]; then
    nix --store "${GHOSTSHIP_NIX_STORE}" "$@"
  else
    nix "$@"
  fi
}

resolve_store_path() {
  local path="$1"

  if [ -n "${GHOSTSHIP_NIX_STORE:-}" ] && [[ "$path" == /nix/store/* ]]; then
    printf '%s\n' "${GHOSTSHIP_NIX_STORE}/nix/store/${path#/nix/store/}"
    return 0
  fi

  printf '%s\n' "$path"
}

rootfs_output="${GHOSTSHIP_ROOTFS_OUTPUT:-${GHOSTSHIP_IMAGE_OUTPUT:-}}"
rootfs_tar="${GHOSTSHIP_ROOTFS_TAR:-${GHOSTSHIP_IMAGE_TAR:-}}"
nix_volume_root="${GHOSTSHIP_NIX_VOLUME_ROOT:-}"
dashboard_port="${GHOSTSHIP_TEST_DASHBOARD_PORT:-7681}"
dashboard_base_url="http://127.0.0.1:${dashboard_port}"
router_base_url="http://127.0.0.1:8788"

if [ -z "$nix_volume_root" ]; then
  if [ -n "${GHOSTSHIP_NIX_STORE:-}" ]; then
    nix_volume_root="${GHOSTSHIP_NIX_STORE}/nix"
  else
    nix_volume_root="/nix"
  fi
fi

if [ ! -d "$nix_volume_root/store" ]; then
  echo "$nix_volume_root/store is required for the persisted /nix validation path" >&2
  exit 1
fi

if [ -z "$rootfs_output" ] && [ -z "$rootfs_tar" ]; then
  rootfs_output="$(nix_cmd build --no-link --print-out-paths .#packages.x86_64-linux.ghostship-hermes-rootfs)"
  rootfs_output="$(resolve_store_path "$rootfs_output")"
fi

if [ -z "$rootfs_tar" ] && [ -n "$rootfs_output" ]; then
  if [ -d "$rootfs_output" ]; then
    rootfs_tar="$(find "$rootfs_output" -type f -name '*.tar.xz' | head -n 1)"
  else
    rootfs_tar="$rootfs_output"
  fi
fi

if [ -n "$rootfs_tar" ]; then
  rootfs_tar="$(resolve_store_path "$rootfs_tar")"
fi

if [ -z "$rootfs_tar" ]; then
  echo "failed to locate compressed NixOS rootfs tarball under $rootfs_output" >&2
  exit 1
fi

image_ref="ghostship-hermes-validate:$(date +%s)"
tmp_root="$(mktemp -d)"
home_dir="$tmp_root/home"
workspace_dir="$tmp_root/workspace"
container_one="ghostship-validate-$$-1"
container_two="ghostship-validate-$$-2"
host_uid="$(id -u)"
host_gid="$(id -g)"
container_shell="/bin/sh"
container_path="/run/current-system/sw/bin:/nix/var/nix/profiles/system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/bin"

cleanup() {
  docker rm -f "$container_one" "$container_two" >/dev/null 2>&1 || true
  docker run --rm -v "$tmp_root:/cleanup" alpine sh -lc "
    chown -R $host_uid:$host_gid /cleanup >/dev/null 2>&1 || true
    chmod -R u+w /cleanup >/dev/null 2>&1 || true
  " >/dev/null 2>&1 || true
  docker image rm -f "$image_ref" >/dev/null 2>&1 || true
  rm -rf "$tmp_root"
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

assert_file_contains() {
  local file="$1"
  local pattern="$2"
  grep -q "$pattern" "$file"
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
    -e BITWARDENCLI_APPDATA_DIR=/home/hermes/.local/state/bitwarden-cli \
    -e TERMINAL_CWD=/home/hermes \
    -e XDG_RUNTIME_DIR=/run/user/3000 \
    -e DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/3000/bus \
    -e PATH=/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/bin \
    "$target_container" \
    "$container_shell" -lc "$*"
}

wait_for_container_ready() {
  local target_container="$1"
  local tries=0

  until run_in_container "$target_container" '
    systemctl is-active ghostship-storage.service >/dev/null 2>&1 &&
    test "$(systemctl show -P Result ghostship-hermes-bootstrap.service 2>/dev/null)" = "success" &&
    systemctl is-active ghostship-hermes-router.service >/dev/null 2>&1 &&
    systemctl is-active ghostship-hermes-hudui.service >/dev/null 2>&1 &&
    runuser -u hermes -- env XDG_RUNTIME_DIR=/run/user/3000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/3000/bus systemctl --user is-active hermes-gateway.service >/dev/null 2>&1 &&
    curl -fsS http://127.0.0.1:8788/readyz >/dev/null 2>&1 &&
    curl -fsS http://127.0.0.1:7681/api/health >/dev/null 2>&1
  '; do
    tries=$((tries + 1))
    if [ "$tries" -ge 90 ]; then
      echo "container $target_container did not become ready" >&2
      docker logs "$target_container" >&2 || true
      run_in_container "$target_container" '
        systemctl --no-pager --full status ghostship-storage.service ghostship-hermes-bootstrap.service ghostship-hermes-router.service ghostship-hermes-hudui.service || true
        runuser -u hermes -- env XDG_RUNTIME_DIR=/run/user/3000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/3000/bus systemctl --user --no-pager --full status hermes-gateway.service ghostship-hermes-gateway-restart.path || true
      ' >&2 || true
      exit 1
    fi
    sleep 2
  done
}

wait_for_hermes_condition() {
  local target_container="$1"
  local command="$2"
  local tries=0

  until run_as_hermes "$target_container" "$command"; do
    tries=$((tries + 1))
    if [ "$tries" -ge 60 ]; then
      echo "timed out waiting for hermes condition: $command" >&2
      return 1
    fi
    sleep 2
  done
}

assert_router_inventory() {
  local target_container="$1"
  run_in_container "$target_container" "curl -fsS ${router_base_url}/v1/models | jq -e '[.data[].id] | index(\"auxiliary\") and index(\"coding\") and index(\"agentic\") and index(\"vision\") and index(\"tts\")' >/dev/null"
}

assert_model_config() {
  local target_container="$1"
  run_as_hermes "$target_container" 'hermes config show | grep -F "provider: openai-codex" >/dev/null'
  run_as_hermes "$target_container" 'hermes config show | grep -F "default: gpt-5.5" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^web:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  backend: firecrawl" >/dev/null'
  run_as_hermes "$target_container" '! sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  base_url: http://127.0.0.1:8788/v1" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^fallback_model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: opencode-go" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^fallback_model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  model: minimax-m2.7" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^agent:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  reasoning_effort: medium" >/dev/null'
  run_as_hermes "$target_container" '! sed -n "/^custom_providers:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "api_key:" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^discord:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  require_mention: false" >/dev/null'
}

assert_config_migration() {
  local target_container="$1"
  run_as_hermes "$target_container" 'sed -i "/^model:/,/^[^ ]/s/^  provider: openai-codex$/  provider: opencode-go/" /home/hermes/.hermes/config.yaml'
  run_as_hermes "$target_container" 'sed -i "/^model:/,/^[^ ]/s/^  default: gpt-5.5$/  default: minimax-m2.7/" /home/hermes/.hermes/config.yaml'
  run_as_hermes "$target_container" 'sed -i "/^model:$/a\  base_url: http://127.0.0.1:8788/v1" /home/hermes/.hermes/config.yaml'
  run_as_hermes "$target_container" 'sed -i "/^fallback_model:/,/^[^ ]/s/^  provider: opencode-go$/  provider: openai-codex/" /home/hermes/.hermes/config.yaml'
  run_as_hermes "$target_container" 'sed -i "/^fallback_model:/,/^[^ ]/s/^  model: minimax-m2.7$/  model: gpt-5.4-mini/" /home/hermes/.hermes/config.yaml'
  run_as_hermes "$target_container" 'sed -i "/^agent:/,/^[^ ]/s/^  reasoning_effort: medium$/  reasoning_effort: high/" /home/hermes/.hermes/config.yaml'
  run_as_hermes "$target_container" 'sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: opencode-go" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  default: minimax-m2.7" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  base_url: http://127.0.0.1:8788/v1" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^fallback_model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: openai-codex" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^fallback_model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  model: gpt-5.4-mini" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^agent:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  reasoning_effort: high" >/dev/null'
  run_in_container "$target_container" 'systemctl start ghostship-hermes-bootstrap.service >/dev/null'
  run_as_hermes "$target_container" '! sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  base_url: http://127.0.0.1:8788/v1" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: openai-codex" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  default: gpt-5.5" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^web:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  backend: firecrawl" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^fallback_model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  provider: opencode-go" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^fallback_model:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  model: minimax-m2.7" >/dev/null'
  run_as_hermes "$target_container" 'sed -n "/^agent:/,/^[^ ]/p" /home/hermes/.hermes/config.yaml | grep -F "  reasoning_effort: medium" >/dev/null'
}

assert_primary_execution() {
  local target_container="$1"
  run_as_hermes "$target_container" 'hermes chat -q "Reply with exactly OK." >/tmp/hermes-primary.out 2>&1'
  run_as_hermes "$target_container" '! grep -Fi "switching to fallback" /tmp/hermes-primary.out >/dev/null'
  run_as_hermes "$target_container" 'grep -Fx "OK" /tmp/hermes-primary.out >/dev/null'
}

mkdir -p "$home_dir/.hermes/profiles/assistant" "$home_dir/seeds/skills/workflow-single" "$workspace_dir"
printf 'legacy-profile\n' > "$home_dir/.hermes/profiles/assistant/.managed"
printf 'assistant\n' > "$home_dir/.hermes/active_profile"
printf 'seed-skill-v1\n' > "$home_dir/seeds/skills/workflow-single/SKILL.md"
printf 'seed-soul-v1\n' > "$home_dir/seeds/SOUL.md"
chmod 0555 "$home_dir/seeds/skills/workflow-single"
chmod 0444 "$home_dir/seeds/skills/workflow-single/SKILL.md"
xz -dc "$rootfs_tar" | docker import - "$image_ref" >/dev/null

docker run -d \
  --name "$container_one" \
  --privileged \
  --cgroupns=host \
  --tmpfs /run \
  --tmpfs /run/lock \
  --tmpfs /tmp \
  -e container=docker \
  -e OPENCODE_GO_API_KEY=single-agent-opencode-key \
  -e OPENROUTER_API_KEY \
  -e OPENROUTER_BASE_URL \
  -e OPENROUTER_HTTP_REFERER \
  -e OPENROUTER_TITLE \
  -e DISCORD_BOT_TOKEN=single-agent-bot-token \
  -e DISCORD_ALLOWED_USERS=single-agent-user \
  -e GHOSTSHIP_ROUTER_CHANNEL=single-agent-channel \
  -e DISCORD_HOME_CHANNEL=single-agent-home \
  -e WEBHOOK_SECRET=single-agent-webhook-secret \
  -e CHAPTARR_URL=http://chaptarr.example:8789 \
  -e CHAPTARR_API_KEY=chaptarr-token \
  -v "$home_dir:/home/hermes" \
  -v "$workspace_dir:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -v "$nix_volume_root:/nix" \
  -p "${dashboard_port}:7681" \
  "$image_ref" /init >/dev/null

wait_for_container_ready "$container_one"
wait_for_http "${dashboard_base_url}/"
wait_for_http "${dashboard_base_url}/api/health"
wait_for_http "${dashboard_base_url}/api/profiles"
wait_for_http "${dashboard_base_url}/api/projects"
curl -fsS "${dashboard_base_url}/api/health" | jq -e ' .config_model == "gpt-5.5" and .config_provider == "openai-codex" ' >/dev/null
curl -fsS "${dashboard_base_url}/api/profiles" | jq -e ' .profiles[0].name == "Managed Agent" ' >/dev/null
curl -fsS "${dashboard_base_url}/api/projects" | jq -e ' .projects_dir == "/workspace" ' >/dev/null

run_in_container "$container_one" 'id hermes | grep -F "uid=3000(hermes) gid=3000(hermes)" >/dev/null'
run_in_container "$container_one" 'test "$(systemctl show -P Result ghostship-hermes-bootstrap.service)" = "success"'
run_in_container "$container_one" '! systemctl is-active hermes-agent.service >/dev/null'
run_in_container "$container_one" 'systemctl is-active ghostship-hermes-router.service >/dev/null'
run_as_hermes "$container_one" 'systemctl --user is-active hermes-gateway.service >/dev/null'
run_as_hermes "$container_one" 'test -L /home/hermes/.config/systemd/user/hermes-gateway.service'
run_as_hermes "$container_one" 'readlink /home/hermes/.config/systemd/user/hermes-gateway.service | grep -Fx "/etc/systemd/user/hermes-gateway.service" >/dev/null'
run_as_hermes "$container_one" 'hermes gateway status >/tmp/gateway-status.out 2>&1; grep -F "User gateway service is running" /tmp/gateway-status.out >/dev/null; ! grep -F "Installed gateway service definition is outdated" /tmp/gateway-status.out >/dev/null'
run_as_hermes "$container_one" 'test "$HOME" = "/home/hermes"'
run_as_hermes "$container_one" 'test "$HERMES_HOME" = "/home/hermes/.hermes"'
run_as_hermes "$container_one" '! test -d /home/hermes/.hermes/profiles'
run_as_hermes "$container_one" '! test -f /home/hermes/.hermes/active_profile'
run_as_hermes "$container_one" 'grep -Fx "seed-skill-v1" /home/hermes/.hermes/skills/workflow-single/SKILL.md >/dev/null'
run_as_hermes "$container_one" 'test -w /home/hermes/.hermes/skills/workflow-single'
run_as_hermes "$container_one" 'test -w /home/hermes/.hermes/skills/workflow-single/SKILL.md'
run_as_hermes "$container_one" '! test -e /home/hermes/.hermes/profiles/assistant/skills/workflow-single/SKILL.md'
run_as_hermes "$container_one" 'grep -Fx "seed-soul-v1" /home/hermes/.hermes/SOUL.md >/dev/null'
run_as_hermes "$container_one" 'printf "{\"provider\":\"codex\"}\n" > /home/hermes/.hermes/auth.json'
run_as_hermes "$container_one" 'for cmd in bw bw-unlock bw-lock; do command -v "$cmd" >/dev/null || exit 1; done'
run_as_hermes "$container_one" 'bw --help >/dev/null'
run_as_hermes "$container_one" 'bw-unlock --help >/dev/null'
run_as_hermes "$container_one" 'bw-lock --help >/dev/null'
run_as_hermes "$container_one" 'test -d /home/hermes/.local/state/bitwarden-cli'
run_as_hermes "$container_one" '! test -e "/home/hermes/.config/Bitwarden CLI"'
run_in_container "$container_one" "stat -c '%U:%G %a' /run/user/3000/ghostship-bitwarden | grep -Fx 'hermes:hermes 700' >/dev/null"
run_as_hermes "$container_one" 'grep -E "^BITWARDENCLI_APPDATA_DIR='\''?/home/hermes/.local/state/bitwarden-cli'\''?$" /home/hermes/.hermes/.env >/dev/null'
run_as_hermes "$container_one" '! grep -Eq "^(BW_CLIENTSECRET|BW_PASSWORD|BW_SESSION)=" /home/hermes/.hermes/.env'
assert_router_inventory "$container_one"
assert_model_config "$container_one"
assert_config_migration "$container_one"
assert_primary_execution "$container_one"

run_as_hermes "$container_one" '
  mkdir -p \
    ~/.config/ghostship-test \
    ~/.local/share/ghostship-test \
    ~/.cache/ghostship-test \
    ~/.agent-browser \
    ~/.agents \
    ~/.codex \
    ~/.copilot \
    ~/.npm \
    ~/.bun \
    ~/.ssh \
    ~/.gnupg \
    ~/.pki
  printf "config\n" > ~/.config/ghostship-test/persist.txt
  printf "local\n" > ~/.local/share/ghostship-test/persist.txt
  printf "cache\n" > ~/.cache/ghostship-test/persist.txt
  printf "agent-browser\n" > ~/.agent-browser/persist.txt
  printf "agents\n" > ~/.agents/persist.txt
  printf "codex\n" > ~/.codex/persist.txt
  printf "copilot\n" > ~/.copilot/persist.txt
  printf "npm\n" > ~/.npm/persist.txt
  printf "bun\n" > ~/.bun/persist.txt
  printf "ssh\n" > ~/.ssh/persist.txt
  printf "gnupg\n" > ~/.gnupg/persist.txt
  printf "pki\n" > ~/.pki/persist.txt
  printf "workspace\n" > /workspace/work-item.txt
'

run_as_hermes "$container_one" 'nix profile install nixpkgs#hello >/tmp/nix-hello-install.log'
wait_for_hermes_condition "$container_one" 'command -v hello >/dev/null'
run_as_hermes "$container_one" 'hello >/tmp/hello.out && grep -F "Hello, world!" /tmp/hello.out >/dev/null'

run_as_hermes "$container_one" 'nix profile install nixpkgs#nodejs_22 >/tmp/nix-node-install.log'
wait_for_hermes_condition "$container_one" 'command -v npm >/dev/null'
run_as_hermes "$container_one" '
  npm install --prefix "$HOME/.local" cowsay@1.5.0 >/tmp/cowsay-install.log
  node -p "require(process.env.HOME + \"/.local/node_modules/cowsay/package.json\").version" | grep -Fx "1.5.0" >/dev/null
  npm install --prefix "$HOME/.local" cowsay@1.6.0 >/tmp/cowsay-upgrade.log
  node -p "require(process.env.HOME + \"/.local/node_modules/cowsay/package.json\").version" | grep -Fx "1.6.0" >/dev/null
'

run_as_hermes "$container_one" 'nix profile install nixpkgs#opencode >/tmp/nix-opencode-install.log'
wait_for_hermes_condition "$container_one" 'command -v opencode >/dev/null'
run_as_hermes "$container_one" '
  opencode --version >/tmp/opencode-version.log 2>&1 || true
  mkdir -p \
    ~/.config/opencode \
    ~/.local/share/opencode \
    ~/.local/state/opencode \
    ~/.cache/opencode
  printf "config\n" > ~/.config/opencode/persist.txt
  printf "share\n" > ~/.local/share/opencode/persist.txt
  printf "state\n" > ~/.local/state/opencode/persist.txt
  printf "cache\n" > ~/.cache/opencode/persist.txt
'

run_as_hermes "$container_one" '
  printf "user-skill-v2\n" > /home/hermes/.hermes/skills/workflow-single/SKILL.md
  printf "user-soul-v2\n" > /home/hermes/.hermes/SOUL.md
'
chmod u+w "$home_dir/seeds/skills/workflow-single" "$home_dir/seeds/skills/workflow-single/SKILL.md"
printf 'seed-skill-v2\n' > "$home_dir/seeds/skills/workflow-single/SKILL.md"
printf 'seed-soul-v2\n' > "$home_dir/seeds/SOUL.md"

docker rm -f "$container_one" >/dev/null

docker run -d \
  --name "$container_two" \
  --privileged \
  --cgroupns=host \
  --tmpfs /run \
  --tmpfs /run/lock \
  --tmpfs /tmp \
  -e container=docker \
  -e OPENCODE_GO_API_KEY=single-agent-opencode-key \
  -e OPENROUTER_API_KEY \
  -e OPENROUTER_BASE_URL \
  -e OPENROUTER_HTTP_REFERER \
  -e OPENROUTER_TITLE \
  -e DISCORD_BOT_TOKEN=single-agent-bot-token \
  -e DISCORD_ALLOWED_USERS=single-agent-user \
  -e GHOSTSHIP_ROUTER_CHANNEL=single-agent-channel \
  -e DISCORD_HOME_CHANNEL=single-agent-home \
  -e WEBHOOK_SECRET=single-agent-webhook-secret \
  -e CHAPTARR_URL=http://chaptarr.example:8789 \
  -e CHAPTARR_API_KEY=chaptarr-token \
  -v "$home_dir:/home/hermes" \
  -v "$workspace_dir:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -v "$nix_volume_root:/nix" \
  -p "${dashboard_port}:7681" \
  "$image_ref" /init >/dev/null

wait_for_container_ready "$container_two"
wait_for_http "${dashboard_base_url}/"
wait_for_http "${dashboard_base_url}/api/health"
wait_for_http "${dashboard_base_url}/api/profiles"
wait_for_http "${dashboard_base_url}/api/projects"
curl -fsS "${dashboard_base_url}/api/health" | jq -e ' .config_model == "gpt-5.5" and .config_provider == "openai-codex" ' >/dev/null
curl -fsS "${dashboard_base_url}/api/profiles" | jq -e ' .profiles[0].name == "Managed Agent" ' >/dev/null
curl -fsS "${dashboard_base_url}/api/projects" | jq -e ' .projects_dir == "/workspace" ' >/dev/null

run_as_hermes "$container_two" 'grep -Fx "config" ~/.config/ghostship-test/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "local" ~/.local/share/ghostship-test/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "cache" ~/.cache/ghostship-test/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "agent-browser" ~/.agent-browser/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "agents" ~/.agents/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "codex" ~/.codex/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "copilot" ~/.copilot/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "npm" ~/.npm/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "bun" ~/.bun/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "ssh" ~/.ssh/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "gnupg" ~/.gnupg/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "pki" ~/.pki/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "workspace" /workspace/work-item.txt >/dev/null'
run_as_hermes "$container_two" '! test -d /home/hermes/.hermes/profiles'
run_as_hermes "$container_two" '! test -f /home/hermes/.hermes/active_profile'
run_as_hermes "$container_two" 'hello >/tmp/hello.out && grep -F "Hello, world!" /tmp/hello.out >/dev/null'
run_as_hermes "$container_two" 'command -v opencode >/dev/null'
run_as_hermes "$container_two" 'grep -F "\"provider\":\"codex\"" /home/hermes/.hermes/auth.json >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "user-skill-v2" /home/hermes/.hermes/skills/workflow-single/SKILL.md >/dev/null'
run_as_hermes "$container_two" '! test -e /home/hermes/.hermes/profiles/assistant/skills/workflow-single/SKILL.md'
run_as_hermes "$container_two" '! grep -Fx "seed-skill-v2" /home/hermes/.hermes/skills/workflow-single/SKILL.md >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "user-soul-v2" /home/hermes/.hermes/SOUL.md >/dev/null'
run_as_hermes "$container_two" '! grep -Fx "seed-soul-v2" /home/hermes/.hermes/SOUL.md >/dev/null'
run_as_hermes "$container_two" 'for cmd in bw bw-unlock bw-lock; do command -v "$cmd" >/dev/null || exit 1; done'
run_as_hermes "$container_two" 'bw-unlock --help >/dev/null'
run_as_hermes "$container_two" 'bw-lock --help >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "config" ~/.config/opencode/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "share" ~/.local/share/opencode/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "state" ~/.local/state/opencode/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "cache" ~/.cache/opencode/persist.txt >/dev/null'
run_as_hermes "$container_two" '
  node -p "require(process.env.HOME + \"/.local/node_modules/cowsay/package.json\").version" | grep -Fx "1.6.0" >/dev/null
'
assert_router_inventory "$container_two"
assert_model_config "$container_two"

curl -fsS -X POST "${dashboard_base_url}/api/console/open" >/tmp/ghostship-terminal-open-3.json
terminal_three="$(jq -r ' .session.id' /tmp/ghostship-terminal-open-3.json)"
terminal_three_url="$(jq -r ' .session.terminal_url' /tmp/ghostship-terminal-open-3.json)"
wait_for_http "${dashboard_base_url}${terminal_three_url}"
curl -fsS -X POST "${dashboard_base_url}/api/console/sessions/$terminal_three/close" >/tmp/ghostship-terminal-close-3.json
assert_file_contains /tmp/ghostship-terminal-close-3.json '"session": null'

printf 'validated ghostship-hermes image persistence with %s\n' "$image_ref"
