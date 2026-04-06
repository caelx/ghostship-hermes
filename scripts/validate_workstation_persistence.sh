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

ghostship_cmds=(
  ghostship-bazarr
  ghostship-changedetection
  ghostship-cloakbrowser
  ghostship-flaresolverr
  ghostship-grimmory
  ghostship-nzbget
  ghostship-plex
  ghostship-pricebuddy
  ghostship-prowlarr
  ghostship-pyload-ng
  ghostship-qbittorrent
  ghostship-radarr
  ghostship-romm
  ghostship-rss-bridge
  ghostship-searxng
  ghostship-sonarr
  ghostship-synology
  ghostship-tautulli
)

ghostship_cmds_joined="$(printf '%q ' "${ghostship_cmds[@]}")"

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

assert_http_contains() {
  local url="$1"
  local pattern="$2"
  local body

  body="$(curl -fsS "$url")"
  grep -q "$pattern" <<<"$body"
}

assert_file_contains() {
  local file="$1"
  local pattern="$2"
  grep -q "$pattern" "$file"
}

run_in_container() {
  local container_name="$1"
  shift
  docker exec \
    -e PATH="$container_path" \
    "$container_name" \
    "$container_shell" -lc "$*"
}

wait_for_container_ready() {
  local container_name="$1"
  local tries=0

  until run_in_container "$container_name" '
    systemctl is-active ghostship-storage.service >/dev/null 2>&1 &&
    test "$(systemctl show -P Result ghostship-hermes-bootstrap.service 2>/dev/null)" = "success" &&
    systemctl is-active ghostship-hermes-router.service >/dev/null 2>&1 &&
    systemctl is-active ghostship-hermes-profile-operations.service >/dev/null 2>&1 &&
    systemctl is-active ghostship-hermes-profile-coder.service >/dev/null 2>&1 &&
    systemctl is-active ghostship-dashboard-controller.service >/dev/null 2>&1 &&
    curl -fsS http://127.0.0.1:8788/readyz >/dev/null 2>&1 &&
    curl -fsS http://127.0.0.1:7681/api/status >/dev/null 2>&1
  '; do
    tries=$((tries + 1))
    if [ "$tries" -ge 90 ]; then
      echo "container $container_name did not become ready" >&2
      docker logs "$container_name" >&2 || true
      run_in_container "$container_name" '
        systemctl --no-pager --full status ghostship-storage.service ghostship-hermes-bootstrap.service ghostship-hermes-router.service ghostship-hermes-profile-operations.service ghostship-hermes-profile-coder.service ghostship-dashboard-controller.service || true
      ' >&2 || true
      exit 1
    fi
    sleep 2
  done
}

run_as_hermes() {
  local container_name="$1"
  shift
  docker exec \
    -u 3000:3000 \
    -e HOME=/home/hermes \
    -e HERMES_HOME=/home/hermes/.hermes \
    -e TERMINAL_CWD=/home/hermes \
    -e PATH=/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/run/current-system/sw/bin:/nix/var/nix/profiles/system/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/bin \
    "$container_name" \
    "$container_shell" -lc "$*"
}

wait_for_hermes_condition() {
  local container_name="$1"
  local command="$2"
  local tries=0

  until run_as_hermes "$container_name" "$command"; do
    tries=$((tries + 1))
    if [ "$tries" -ge 60 ]; then
      echo "timed out waiting for hermes condition: $command" >&2
      return 1
    fi
    sleep 2
  done
}

assert_router_inventory() {
  local container_name="$1"
  run_in_container "$container_name" "curl -fsS ${router_base_url}/v1/models | jq -e '[.data[].id] | index(\"lightweight\") and index(\"coding\") and index(\"heavyweight\")' >/dev/null"
}

assert_free_router_buckets() {
  local container_name="$1"
  run_in_container "$container_name" "curl -fsS ${router_base_url}/v1/models | jq -e '
    [.data[] | select(.id == "lightweight" or .id == "coding" or .id == "heavyweight")]
    | length == 3
    and all(.[]; .metadata.candidate_count > 0)
    and all(.[]; all(.metadata.candidates[]; .is_free == true))
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

mkdir -p "$home_dir" "$workspace_dir"
xz -dc "$rootfs_tar" | docker import - "$image_ref" >/dev/null

docker run -d \
  --name "$container_one" \
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
  -v "$home_dir:/home/hermes" \
  -v "$workspace_dir:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -v "$nix_volume_root:/nix" \
  -p "${dashboard_port}:7681" \
  "$image_ref" /init >/dev/null

wait_for_container_ready "$container_one"
wait_for_http "${dashboard_base_url}/"
wait_for_http "${dashboard_base_url}/api/status"
test "$(curl -fsS "${dashboard_base_url}/api/status" | jq -r '.profiles[] | select(.name == "operations") | .name')" = "operations"
test "$(curl -fsS "${dashboard_base_url}/api/status" | jq -r '.profiles[] | select(.name == "coder") | .name')" = "coder"
test "$(curl -fsS "${dashboard_base_url}/api/status" | jq -r '.default_profile')" = "operations"
test "$(curl -fsS "${dashboard_base_url}/api/status" | jq -r '.environment.providers[] | select(.name == "ghostship-router") | .router.ready')" = "true"

run_in_container "$container_one" 'id hermes | grep -F "uid=3000(hermes) gid=3000(hermes)" >/dev/null'
run_in_container "$container_one" 'test "$(systemctl show -P Result ghostship-hermes-bootstrap.service)" = "success"'
run_in_container "$container_one" '! systemctl is-active hermes-agent.service >/dev/null'
run_in_container "$container_one" 'systemctl is-active ghostship-hermes-router.service >/dev/null'
run_in_container "$container_one" 'systemctl cat ghostship-hermes-bootstrap.service | grep -F "WorkingDirectory=/home/hermes" >/dev/null'
run_in_container "$container_one" 'systemctl cat ghostship-hermes-profile-operations.service | grep -F "WorkingDirectory=/home/hermes" >/dev/null'
run_in_container "$container_one" 'systemctl cat ghostship-hermes-profile-coder.service | grep -F "WorkingDirectory=/home/hermes" >/dev/null'
run_as_hermes "$container_one" 'test "$HOME" = "/home/hermes"'
run_as_hermes "$container_one" 'test "$HERMES_HOME" = "/home/hermes/.hermes"'
run_as_hermes "$container_one" 'test "$(id -u)" = "3000" && test "$(id -g)" = "3000"'
run_in_container "$container_one" 'test -d /home/hermes/.hermes && test -d /workspace'

run_in_container "$container_one" '
  for cmd in codex gemini opencode openspec skills gws bws feed; do
    if command -v "$cmd" >/dev/null 2>&1; then
      echo "unexpected preinstalled command: $cmd" >&2
      exit 1
    fi
  done
'

run_in_container "$container_one" "for cmd in $ghostship_cmds_joined; do command -v \"\$cmd\" >/dev/null; done"
run_in_container "$container_one" 'command -v tirith >/dev/null'

run_in_container "$container_one" '
  for skill in bitwarden changedetection current-environment feed hermes-nix; do
    if [ -d "/home/hermes/.hermes/skills/$skill" ]; then
      echo "unexpected custom skill seeded: $skill" >&2
      exit 1
    fi
  done
'

run_as_hermes "$container_one" 'hermes profile show operations >/dev/null'
run_as_hermes "$container_one" 'hermes profile show coder >/dev/null'
run_as_hermes "$container_one" 'test "$(cat /home/hermes/.hermes/active_profile)" = "operations"'
run_as_hermes "$container_one" 'test -d /home/hermes/.hermes/profiles/operations'
run_as_hermes "$container_one" 'test -d /home/hermes/.hermes/profiles/coder'
run_as_hermes "$container_one" '! test -d /home/hermes/.hermes/profiles/test'
run_as_hermes "$container_one" 'hermes config show | grep -F "/home/hermes" >/dev/null'
run_as_hermes "$container_one" 'hermes profile list | grep -F "operations" >/dev/null'
run_as_hermes "$container_one" 'hermes profile list | grep -F "coder" >/dev/null'
assert_router_inventory "$container_one"
assert_free_router_buckets "$container_one"
assert_model_config "$container_one" root lightweight
assert_model_config "$container_one" operations heavyweight
assert_model_config "$container_one" coder coding
run_as_hermes "$container_one" 'grep -F "OPENROUTER_API_KEY=" /home/hermes/.hermes/profiles/operations/.env >/dev/null'
run_as_hermes "$container_one" 'grep -F "OPENROUTER_API_KEY=" /home/hermes/.hermes/profiles/coder/.env >/dev/null'

run_as_hermes "$container_one" '
  mkdir -p \
    ~/.hermes \
    ~/.config/ghostship-test \
    ~/.local/share/ghostship-test \
    ~/.cache/ghostship-test \
    ~/.agent-browser \
    ~/.agents \
    ~/.codex \
    ~/.gemini \
    ~/.copilot \
    ~/.npm \
    ~/.bun \
    ~/.ssh \
    ~/.gnupg \
    ~/.pki
  printf "hermes-home\n" > ~/.hermes/persist.txt
  printf "config\n" > ~/.config/ghostship-test/persist.txt
  printf "local\n" > ~/.local/share/ghostship-test/persist.txt
  printf "cache\n" > ~/.cache/ghostship-test/persist.txt
  printf "agent-browser\n" > ~/.agent-browser/persist.txt
  printf "agents\n" > ~/.agents/persist.txt
  printf "codex\n" > ~/.codex/persist.txt
  printf "gemini\n" > ~/.gemini/persist.txt
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

curl -fsS -X POST "${dashboard_base_url}/api/terminal/open" >/tmp/ghostship-terminal-open.json
terminal_one="$(jq -r '.active_terminal_id' /tmp/ghostship-terminal-open.json)"
terminal_one_url="$(jq -r '.sessions[] | select(.id == "'"$terminal_one"'") | .terminal_url' /tmp/ghostship-terminal-open.json)"
wait_for_http "${dashboard_base_url}${terminal_one_url}"

curl -fsS -X POST "${dashboard_base_url}/api/terminal/open" >/tmp/ghostship-terminal-open-2.json
terminal_two="$(jq -r '.active_terminal_id' /tmp/ghostship-terminal-open-2.json)"
terminal_two_url="$(jq -r '.sessions[] | select(.id == "'"$terminal_two"'") | .terminal_url' /tmp/ghostship-terminal-open-2.json)"
wait_for_http "${dashboard_base_url}${terminal_two_url}"

curl -fsS -X POST "${dashboard_base_url}/api/terminals/$terminal_two/close" >/tmp/ghostship-terminal-close-2.json
assert_file_contains /tmp/ghostship-terminal-close-2.json '"id": "'"$terminal_one"'"'
curl -fsS -X POST "${dashboard_base_url}/api/terminals/$terminal_one/close" >/tmp/ghostship-terminal-close.json
assert_file_contains /tmp/ghostship-terminal-close.json '"sessions": \[\]'

docker rm -f "$container_one" >/dev/null

docker run -d \
  --name "$container_two" \
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
  -v "$home_dir:/home/hermes" \
  -v "$workspace_dir:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -v "$nix_volume_root:/nix" \
  -p "${dashboard_port}:7681" \
  "$image_ref" /init >/dev/null

wait_for_container_ready "$container_two"
wait_for_http "${dashboard_base_url}/"
wait_for_http "${dashboard_base_url}/api/status"
test "$(curl -fsS "${dashboard_base_url}/api/status" | jq -r '.profiles[] | select(.name == "operations") | .name')" = "operations"
test "$(curl -fsS "${dashboard_base_url}/api/status" | jq -r '.profiles[] | select(.name == "coder") | .name')" = "coder"
test "$(curl -fsS "${dashboard_base_url}/api/status" | jq -r '.default_profile')" = "operations"
test "$(curl -fsS "${dashboard_base_url}/api/status" | jq -r '.environment.providers[] | select(.name == "ghostship-router") | .router.ready')" = "true"

run_as_hermes "$container_two" 'grep -Fx "hermes-home" ~/.hermes/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "config" ~/.config/ghostship-test/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "local" ~/.local/share/ghostship-test/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "cache" ~/.cache/ghostship-test/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "agent-browser" ~/.agent-browser/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "agents" ~/.agents/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "codex" ~/.codex/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "gemini" ~/.gemini/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "copilot" ~/.copilot/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "npm" ~/.npm/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "bun" ~/.bun/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "ssh" ~/.ssh/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "gnupg" ~/.gnupg/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "pki" ~/.pki/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "workspace" /workspace/work-item.txt >/dev/null'
run_as_hermes "$container_two" 'hermes profile show operations >/dev/null'
run_as_hermes "$container_two" 'test "$(cat /home/hermes/.hermes/active_profile)" = "operations"'
run_as_hermes "$container_two" 'test -d /home/hermes/.hermes/profiles/operations'
run_as_hermes "$container_two" 'test -d /home/hermes/.hermes/profiles/coder'
run_as_hermes "$container_two" '! test -d /home/hermes/.hermes/profiles/test'
run_as_hermes "$container_two" 'hermes profile list | grep -F "operations" >/dev/null'
run_as_hermes "$container_two" 'hermes profile list | grep -F "coder" >/dev/null'
run_in_container "$container_two" 'systemctl is-active ghostship-hermes-router.service >/dev/null'
assert_router_inventory "$container_two"
assert_free_router_buckets "$container_two"
assert_model_config "$container_two" root lightweight
assert_model_config "$container_two" operations heavyweight
assert_model_config "$container_two" coder coding
run_as_hermes "$container_two" 'hello >/tmp/hello.out && grep -F "Hello, world!" /tmp/hello.out >/dev/null'
run_as_hermes "$container_two" 'command -v tirith >/dev/null'
run_as_hermes "$container_two" 'command -v opencode >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "config" ~/.config/opencode/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "share" ~/.local/share/opencode/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "state" ~/.local/state/opencode/persist.txt >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "cache" ~/.cache/opencode/persist.txt >/dev/null'
run_as_hermes "$container_two" '
  node -p "require(process.env.HOME + \"/.local/node_modules/cowsay/package.json\").version" | grep -Fx "1.6.0" >/dev/null
'

curl -fsS -X POST "${dashboard_base_url}/api/terminal/open" >/tmp/ghostship-terminal-open-3.json
terminal_three="$(jq -r '.active_terminal_id' /tmp/ghostship-terminal-open-3.json)"
terminal_three_url="$(jq -r '.sessions[] | select(.id == "'"$terminal_three"'") | .terminal_url' /tmp/ghostship-terminal-open-3.json)"
wait_for_http "${dashboard_base_url}${terminal_three_url}"
curl -fsS -X POST "${dashboard_base_url}/api/terminals/$terminal_three/close" >/tmp/ghostship-terminal-close-3.json
assert_file_contains /tmp/ghostship-terminal-close-3.json '"sessions": \[\]'

printf 'validated ghostship-hermes image persistence with %s\n' "$image_ref"
