#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
image_tar="${1:?usage: profiles-dashboard.sh <docker-image-tar> [image-tag]}"
release="$(tr -d '\n' < "$repo_root/packages/hermes-image/hermes-release.txt")"
image_tag="${2:-ghostship-hermes:$release}"
container_name="ghostship-hermes-profiles-test"
home_dir="$(mktemp -d)"

cleanup() {
  docker rm -f "$container_name" >/dev/null 2>&1 || true
  rm -rf "$home_dir" >/dev/null 2>&1 || true
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

wait_for_grep() {
  local command="$1"
  local pattern="$2"
  local attempts="${3:-60}"
  local delay="${4:-2}"
  local try=1

  while [ "$try" -le "$attempts" ]; do
    if eval "$command" | grep -Eq "$pattern"; then
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

wait_for_http_contains() {
  local url="$1"
  local pattern="$2"
  local attempts="${3:-60}"
  local delay="${4:-2}"
  local try=1
  local body=""

  while [ "$try" -le "$attempts" ]; do
    if body="$(curl -fsS "$url" 2>/dev/null)" && grep -q "$pattern" <<<"$body"; then
      return 0
    fi
    sleep "$delay"
    try=$((try + 1))
  done

  return 1
}

if [ "${SKIP_DOCKER_LOAD:-0}" != "1" ]; then
  docker load -i "$image_tar" >/dev/null
fi

docker rm -f "$container_name" >/dev/null 2>&1 || true

docker run -d \
  --name "$container_name" \
  -p 7681:7681 \
  -v "$home_dir:/home/hermes/.hermes" \
  "$image_tag" >/dev/null

wait_for_http "http://127.0.0.1:7681/"
wait_for_http "http://127.0.0.1:7681/api/profiles.json"

assert_http_contains "http://127.0.0.1:7681/" 'data-dashboard="ghostship-hermes-dashboard"'
assert_http_contains "http://127.0.0.1:7681/api/profiles.json" '"slug": "default"'
assert_http_contains "http://127.0.0.1:7681/profiles/default/" "ttyd"

docker exec "$container_name" bash -lc 'hermes profile create coder --clone'
docker exec "$container_name" bash -lc 'hermes profile create research --clone'
docker exec "$container_name" bash -lc 'printf "\nWEBHOOK_ENABLED=true\n" >> /home/hermes/.hermes/profiles/coder/.env'

wait_for_http_contains "http://127.0.0.1:7681/api/profiles.json" '"slug": "coder"'
wait_for_http_contains "http://127.0.0.1:7681/api/profiles.json" '"slug": "research"'
wait_for_http "http://127.0.0.1:7681/profiles/coder/"
wait_for_http "http://127.0.0.1:7681/profiles/research/"

assert_http_contains "http://127.0.0.1:7681/profiles/coder/" "ttyd"
assert_http_contains "http://127.0.0.1:7681/profiles/research/" "ttyd"

nix shell nixpkgs#chromium --command bash -lc '
  chromium --headless --disable-gpu --no-sandbox --virtual-time-budget=7000 --dump-dom http://127.0.0.1:7681/ > /tmp/dashboard-default.html
  chromium --headless --disable-gpu --no-sandbox --virtual-time-budget=7000 --dump-dom "http://127.0.0.1:7681/?profile=coder" > /tmp/dashboard-coder.html
  chromium --headless --disable-gpu --no-sandbox --virtual-time-budget=7000 --dump-dom "http://127.0.0.1:7681/?profile=research" > /tmp/dashboard-research.html

  grep -q "ghostship-hermes-dashboard" /tmp/dashboard-default.html
  grep -q "data-profile=\"default\"" /tmp/dashboard-default.html
  grep -q "src=\"/profiles/default/\"" /tmp/dashboard-default.html
  grep -q "data-profile=\"coder\"" /tmp/dashboard-coder.html
  grep -q "src=\"/profiles/coder/\"" /tmp/dashboard-coder.html
  grep -q "data-profile=\"research\"" /tmp/dashboard-research.html
  grep -q "src=\"/profiles/research/\"" /tmp/dashboard-research.html
'

wait_for_grep "docker exec $container_name bash -lc 's6-svstat /run/ghostship-hermes/services/profile-gateway-coder'" 'up'
if docker exec "$container_name" bash -lc 'test -d /run/ghostship-hermes/services/profile-gateway-research'; then
  echo "unexpected research gateway service" >&2
  exit 1
fi

docker exec "$container_name" bash -lc 'command -v rg jq python python3 gh tmux ps awk less man fzf entr openssl ip dig shellcheck bats git-lfs >/dev/null'
