#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

usage() {
  cat >&2 <<'EOF'
usage: build_publishable_image_in_base.sh [local-base-image-ref] [flake-attr] [bundle-output-dir]

Start a temporary container from the local ghostship-hermes base image,
run the requested Nix image-bundle build inside that container so it can reuse
the baked /nix/store closure, and stage a portable bundle directory back to the host.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to build the publishable image bundle inside ghostship-hermes-base" >&2
  exit 1
fi

if ! docker version >/dev/null 2>&1; then
  echo "docker is installed but not reachable from this shell" >&2
  exit 1
fi

base_image="${1:-}"
flake_attr="${2:-}"
bundle_output_dir="${3:-}"

if [ -z "$base_image" ] || [ -z "$flake_attr" ] || [ -z "$bundle_output_dir" ]; then
  usage
  exit 1
fi

if ! docker image inspect "$base_image" >/dev/null 2>&1; then
  echo "base image is not available locally: $base_image" >&2
  exit 1
fi

mkdir -p "$(dirname "$bundle_output_dir")"
bundle_output_dir="$(cd "$(dirname "$bundle_output_dir")" && pwd)/$(basename "$bundle_output_dir")"
rm -rf "$bundle_output_dir"
mkdir -p "$bundle_output_dir"

container_name="ghostship-hermes-build-${RANDOM}-$$"

cleanup() {
  status=$?
  if [ $status -ne 0 ]; then
    docker logs "$container_name" >&2 || true
  fi
  docker rm -f "$container_name" >/dev/null 2>&1 || true
  exit $status
}
trap cleanup EXIT

docker run -d --name "$container_name"   -v "$repo_root:/src:ro"   -v "$bundle_output_dir:/out"   "$base_image" >/dev/null

ready=0
for _ in $(seq 1 60); do
  if docker exec "$container_name" /bin/sh -lc 'PATH="/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin:$PATH"; systemctl is-active nix-daemon.socket >/dev/null 2>&1 && command -v nix >/dev/null 2>&1'; then
    ready=1
    break
  fi
  if [ "$(docker inspect -f '{{.State.Running}}' "$container_name" 2>/dev/null || true)" != "true" ]; then
    echo "temporary base container exited before the in-image build started" >&2
    exit 1
  fi
  sleep 2
done

if [ "$ready" -ne 1 ]; then
  echo "timed out waiting for the temporary base container to expose nix-daemon.socket" >&2
  exit 1
fi

docker exec   -e FLAKE_ATTR="$flake_attr"   "$container_name" /bin/sh -lc '
    set -euo pipefail
    export PATH="/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin:$PATH"
    export HOME=/root
    git config --global --add safe.directory /src
    cd /src
    bundle="$(nix build --no-link --print-out-paths "$FLAKE_ATTR")"
    find /out -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    cp -aL "$bundle"/. /out/
  '

printf '%s\n' "$bundle_output_dir"
