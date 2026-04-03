#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required for workstation validation" >&2
  exit 1
fi

if [ ! -d /nix/store ]; then
  echo "/nix/store is required for the safe /nix bind-mount validation path" >&2
  exit 1
fi

image_output="${GHOSTSHIP_IMAGE_OUTPUT:-}"
image_tar="${GHOSTSHIP_IMAGE_TAR:-}"

if [ -z "$image_output" ] && [ -z "$image_tar" ]; then
  image_output="$(nix build --no-link --print-out-paths .#ghostship-hermes-image)"
fi

if [ -z "$image_tar" ] && [ -n "$image_output" ]; then
  if [ -d "$image_output" ]; then
    image_tar="$(find "$image_output" -type f -name '*.tar.xz' | head -n 1)"
  else
    image_tar="$image_output"
  fi
fi

image_ref="ghostship-hermes-systemd-validate:$(date +%s)"

if [ -z "$image_tar" ]; then
  echo "failed to locate compressed NixOS rootfs tarball under $image_output" >&2
  exit 1
fi

tmp_root="$(mktemp -d)"
opt_data="$tmp_root/opt-data"
workspace="$tmp_root/workspace"
container_one="ghostship-validate-$$-1"
container_two="ghostship-validate-$$-2"
validation_profile="/home/hermes/.local/state/nix/profiles/workstation-validation"
host_uid="$(id -u)"
host_gid="$(id -g)"

cleanup() {
  docker rm -f "$container_one" "$container_two" >/dev/null 2>&1 || true
  if docker image inspect "$image_ref" >/dev/null 2>&1; then
    docker run --rm --entrypoint /sw/bin/sh -u 0:0 -v "$tmp_root:/cleanup" "$image_ref" -lc '
      /sw/bin/chown -R '"$host_uid:$host_gid"' /cleanup >/dev/null 2>&1 || true
      /sw/bin/chmod -R u+w /cleanup >/dev/null 2>&1 || true
    ' >/dev/null 2>&1 || true
  fi
  docker image rm -f "$image_ref" >/dev/null 2>&1 || true
  rm -rf "$tmp_root"
}
trap cleanup EXIT

mkdir -p "$opt_data" "$workspace"

xz -dc "$image_tar" | docker import - "$image_ref" >/dev/null

wait_for_container_ready() {
  local container_name="$1"
  local tries=0

  until docker exec "$container_name" /sw/bin/bash -lc '
    /sw/bin/systemctl is-active ghostship-storage.service >/dev/null &&
    /sw/bin/systemctl is-active ghostship-workstation-bootstrap.service >/dev/null &&
    /sw/bin/systemctl is-active ghostship-hermes-user-manager.service >/dev/null &&
    /sw/bin/systemctl is-active user@3000.service >/dev/null &&
    /sw/bin/systemctl is-active ghostship-caddy.service >/dev/null &&
    /sw/bin/systemctl is-active ghostship-profile-reconciler.service >/dev/null &&
    test -x /opt/data/hermes-agent/venv/bin/hermes
  '; do
    tries=$((tries + 1))
    if [ "$tries" -ge 90 ]; then
      echo "container $container_name did not become ready" >&2
      docker logs "$container_name" >&2 || true
      docker exec "$container_name" /sw/bin/bash -lc '
        /sw/bin/systemctl --no-pager --full status ghostship-storage.service ghostship-workstation-bootstrap.service ghostship-hermes-user-manager.service user@3000.service ghostship-caddy.service ghostship-profile-reconciler.service || true
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
    -e PATH=/home/hermes/.local/bin:/sw/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/bin \
    -e XDG_RUNTIME_DIR=/run/user/3000 \
    -e DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/3000/bus \
    "$container_name" \
    /sw/bin/bash -lc "$*"
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

wait_for_root_condition() {
  local container_name="$1"
  local command="$2"
  local tries=0

  until docker exec "$container_name" /sw/bin/bash -lc "$command"; do
    tries=$((tries + 1))
    if [ "$tries" -ge 60 ]; then
      echo "timed out waiting for root condition: $command" >&2
      return 1
    fi
    sleep 2
  done
}

docker run -d \
  --name "$container_one" \
  --privileged \
  --cgroupns=host \
  --tmpfs /run \
  --tmpfs /run/lock \
  --tmpfs /tmp \
  -e container=docker \
  -v "$opt_data:/opt/data" \
  -v "$workspace:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -v /nix:/nix \
  "$image_ref" /init >/dev/null

wait_for_container_ready "$container_one"

docker exec "$container_one" /sw/bin/bash -lc '/sw/bin/curl -fsS http://127.0.0.1:7681/api/profiles.json >/dev/null'
docker exec "$container_one" /sw/bin/bash -lc '! command -v sudo >/dev/null'
run_as_hermes "$container_one" 'hermes profile create coder >/tmp/profile-create.log && test -x /home/hermes/.local/bin/coder'
wait_for_root_condition "$container_one" '/sw/bin/curl -fsS http://127.0.0.1:7681/api/profiles.json | grep -F "\"coder\"" >/dev/null'
wait_for_hermes_condition "$container_one" 'test -L /home/hermes/.config/systemd/user/ghostship-profile-ttyd-coder.service'
wait_for_hermes_condition "$container_one" 'systemctl --user is-active ghostship-profile-ttyd-coder.service >/dev/null'
wait_for_root_condition "$container_one" '/sw/bin/curl -fsS -o /dev/null http://127.0.0.1:7681/profiles/coder/'
run_as_hermes "$container_one" 'hermes gateway install >/tmp/gateway-install.log'
wait_for_hermes_condition "$container_one" 'find /home/hermes/.config/systemd/user -maxdepth 1 -type f -name "hermes-gateway-*.service" | grep -q .'
run_as_hermes "$container_one" 'mkdir -p /home/hermes/.config/probe && printf "persisted\n" > /home/hermes/.config/probe/value'
run_as_hermes "$container_one" 'printf "workspace-data\n" > /home/hermes/workspace/work-item.txt'
run_as_hermes "$container_one" "nix profile install --accept-flake-config --profile $validation_profile nixpkgs#hello >/tmp/nix-profile-install.log"
run_as_hermes "$container_one" "$validation_profile/bin/hello >/dev/null"

docker rm -f "$container_one" >/dev/null

docker run -d \
  --name "$container_two" \
  --privileged \
  --cgroupns=host \
  --tmpfs /run \
  --tmpfs /run/lock \
  --tmpfs /tmp \
  -e container=docker \
  -v "$opt_data:/opt/data" \
  -v "$workspace:/workspace" \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -v /nix:/nix \
  "$image_ref" /init >/dev/null

wait_for_container_ready "$container_two"

docker exec "$container_two" /sw/bin/bash -lc '/sw/bin/curl -fsS http://127.0.0.1:7681/api/profiles.json | grep -F "\"coder\"" >/dev/null'
docker exec "$container_two" /sw/bin/bash -lc 'test "$(readlink -f /home/hermes/.config)" = "/opt/data/home/.config"'
docker exec "$container_two" /sw/bin/bash -lc 'test "$(readlink -f /home/hermes/.hermes)" = "/opt/data/home/.hermes"'
docker exec "$container_two" /sw/bin/bash -lc 'test "$(readlink -f /home/hermes/workspace)" = "/workspace"'
docker exec "$container_two" /sw/bin/bash -lc '/sw/bin/systemctl is-active user@3000.service >/dev/null'

run_as_hermes "$container_two" 'grep -Fx "persisted" /home/hermes/.config/probe/value >/dev/null'
run_as_hermes "$container_two" 'grep -Fx "workspace-data" /home/hermes/workspace/work-item.txt >/dev/null'
run_as_hermes "$container_two" 'hermes profile list | grep -F "coder" >/dev/null'
run_as_hermes "$container_two" 'test -d /home/hermes/.hermes/profiles/coder'
wait_for_hermes_condition "$container_two" 'test -L /home/hermes/.config/systemd/user/ghostship-profile-ttyd-coder.service'
wait_for_hermes_condition "$container_two" 'systemctl --user is-active ghostship-profile-ttyd-coder.service >/dev/null'
wait_for_root_condition "$container_two" '/sw/bin/curl -fsS -o /dev/null http://127.0.0.1:7681/profiles/coder/'
wait_for_hermes_condition "$container_two" 'find /home/hermes/.config/systemd/user -maxdepth 1 -type f -name "hermes-gateway-*.service" | grep -q .'
run_as_hermes "$container_two" 'hermes gateway status | grep -F "hermes-gateway-" >/dev/null'
run_as_hermes "$container_two" "$validation_profile/bin/hello >/dev/null"

printf 'validated Docker workstation persistence with %s\n' "$image_ref"
