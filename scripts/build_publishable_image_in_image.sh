#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

usage() {
  cat >&2 <<'EOF'
usage: build_publishable_image_in_image.sh [local-build-image-ref] [flake-attr] [bundle-output-dir]

Run the requested Nix image-bundle build inside a local ghostship-hermes image
so the build can reuse that image's baked /nix/store closure, then stage the
portable bundle directory back to the host.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to build the publishable image bundle inside a local image" >&2
  exit 1
fi

if ! docker version >/dev/null 2>&1; then
  echo "docker is installed but not reachable from this shell" >&2
  exit 1
fi

build_image="${1:-}"
flake_attr="${2:-}"
bundle_output_dir="${3:-}"

if [ -z "$build_image" ] || [ -z "$flake_attr" ] || [ -z "$bundle_output_dir" ]; then
  usage
  exit 1
fi

if ! docker image inspect "$build_image" >/dev/null 2>&1; then
  echo "build image is not available locally: $build_image" >&2
  exit 1
fi

mkdir -p "$(dirname "$bundle_output_dir")"
bundle_output_dir="$(cd "$(dirname "$bundle_output_dir")" && pwd)/$(basename "$bundle_output_dir")"
rm -rf "$bundle_output_dir"
mkdir -p "$bundle_output_dir"

shell_candidates=(
  /bin/sh
  /run/current-system/sw/bin/sh
  /nix/var/nix/profiles/default/bin/sh
  /nix/var/nix/profiles/system/sw/bin/sh
)

build_shell=""
for candidate in "${shell_candidates[@]}"; do
  if docker run --rm --entrypoint "$candidate" "$build_image" -lc 'exit 0' >/dev/null 2>&1; then
    build_shell="$candidate"
    break
  fi
done

if [ -z "$build_shell" ]; then
  echo "failed to find a working shell entrypoint inside $build_image" >&2
  exit 1
fi

docker run --rm   --entrypoint "$build_shell"   -v "$repo_root:/src:ro"   -v "$bundle_output_dir:/out"   -e FLAKE_ATTR="$flake_attr"   "$build_image"   -lc '
    set -euo pipefail
    export PATH="/run/current-system/sw/bin:/nix/var/nix/profiles/default/bin:/nix/var/nix/profiles/system/sw/bin:$PATH"
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
