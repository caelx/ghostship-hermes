#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

usage() {
  cat >&2 <<'EOF'
usage: build_publishable_image_in_base.sh [local-base-image-ref] [flake-attr] [bundle-output-dir]

Run the requested Nix image-bundle build inside the local ghostship-hermes base
image so the build can reuse the baked /nix/store closure, then stage the
portable bundle directory back to the host.
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

docker run --rm   --entrypoint /bin/sh   -v "$repo_root:/src:ro"   -v "$bundle_output_dir:/out"   -e FLAKE_ATTR="$flake_attr"   "$base_image"   -lc '
    set -euo pipefail
    export PATH="/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin:$PATH"
    export HOME=/tmp/ghostship-build-home
    export NIX_CONFIG="experimental-features = nix-command flakes
sandbox = false"
    mkdir -p "$HOME" /out
    git config --global --add safe.directory /src
    cd /src
    bundle="$(nix build --no-link --print-out-paths "$FLAKE_ATTR")"
    find /out -mindepth 1 -maxdepth 1 -exec rm -rf {} +
    cp -aL "$bundle"/. /out/
  '

printf '%s\n' "$bundle_output_dir"
