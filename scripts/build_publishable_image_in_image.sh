#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

usage() {
  cat >&2 <<'USAGE'
usage: build_publishable_image_in_image.sh [local-build-image-ref] [flake-attr] [bundle-output-dir]

Run the requested Nix image-bundle build inside a local ghostship-hermes image
so the build can reuse that image's baked /nix/store closure, then stage the
portable bundle directory back to the host.
USAGE
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

temp_container="$(docker create "$build_image")"
listing_file="$(mktemp)"
cleanup() {
  docker rm -f "$temp_container" >/dev/null 2>&1 || true
  rm -f "$listing_file"
}
trap cleanup EXIT

docker export "$temp_container" | tar -tf - > "$listing_file"

normalize_listing_path() {
  sed 's#^\./##; s#^#/#'
}

system_path_bin="$(
  (
    grep -E '^(\./)?nix/store/[^/]+-system-path/bin/bash$' "$listing_file" || true
  ) | head -n 1 | normalize_listing_path | sed 's#/bash$##'
)"

build_shell="$(
  {
    grep -E '^(\./)?nix/store/[^/]+-system-path/bin/bash$' "$listing_file" || true
    grep -E '^(\./)?nix/store/[^/]+-bash-interactive-[^/]+/bin/bash$' "$listing_file" || true
    grep -E '^(\./)?nix/store/[^/]+-bash-[^/]+/bin/bash$' "$listing_file" || true
    grep -E '^(\./)?nix/store/[^/]+-system-path/bin/sh$' "$listing_file" || true
    grep -E '^(\./)?nix/store/[^/]+-busybox-[^/]+/bin/sh$' "$listing_file" || true
    grep -E '^(\./)?bin/sh$' "$listing_file" || true
  } | head -n 1 | normalize_listing_path
)"

certificate_bundle="$(
  {
    grep -E '^(\./)?nix/store/[^/]+-etc/etc/ssl/certs/ca-bundle.crt$' "$listing_file" || true
    grep -E '^(\./)?nix/store/[^/]+-nss-cacert-[^/]+/etc/ssl/certs/ca-bundle.crt$' "$listing_file" || true
    grep -E '^(\./)?etc/ssl/certs/ca-bundle.crt$' "$listing_file" || true
    grep -E '^(\./)?etc/ssl/certs/ca-certificates.crt$' "$listing_file" || true
  } | head -n 1 | normalize_listing_path
)"

if [ -z "$build_shell" ]; then
  echo "failed to find a working shell entrypoint inside $build_image" >&2
  exit 1
fi

if [ -z "$certificate_bundle" ]; then
  echo "failed to find a CA bundle inside $build_image" >&2
  exit 1
fi

if [ -z "$system_path_bin" ]; then
  system_path_bin="$(dirname "$build_shell")"
fi

docker run --rm   --entrypoint "$build_shell"   -v "$repo_root:/src:ro"   -v "$bundle_output_dir:/out"   -e FLAKE_ATTR="$flake_attr"   -e SYSTEM_PATH_BIN="$system_path_bin"   -e CERTIFICATE_BUNDLE="$certificate_bundle"   "$build_image"   -lc '
    set -euo pipefail
    export PATH="$SYSTEM_PATH_BIN:$PATH"
    export HOME=/tmp/ghostship-build-home
    export SSL_CERT_FILE="$CERTIFICATE_BUNDLE"
    export NIX_SSL_CERT_FILE="$CERTIFICATE_BUNDLE"
    export CURL_CA_BUNDLE="$CERTIFICATE_BUNDLE"
    export GIT_SSL_CAINFO="$CERTIFICATE_BUNDLE"
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
