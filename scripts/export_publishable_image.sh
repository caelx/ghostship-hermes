#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

usage() {
  cat >&2 <<'EOF'
usage: export_publishable_image.sh [image-bundle-path] [image-ref] [image-archive-path]

Build or reuse the explicit ghostship-hermes image bundle, import its rootfs into
the local container engine with the repo-managed metadata contract, and optionally
save the resulting image as an archive tar.
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

container_engine="${CONTAINER_ENGINE:-}"
if [ -z "$container_engine" ]; then
  if command -v docker >/dev/null 2>&1; then
    container_engine="docker"
  elif command -v podman >/dev/null 2>&1; then
    container_engine="podman"
  else
    echo "docker or podman is required to materialize a publishable ghostship-hermes image" >&2
    exit 1
  fi
fi

if ! "$container_engine" version >/dev/null 2>&1; then
  echo "$container_engine is installed but not reachable from this shell" >&2
  exit 1
fi

image_bundle="${1:-}"
image_ref="${2:-}"
archive_path="${3:-}"

if [ -z "$image_bundle" ]; then
  image_bundle="$(nix build --no-link --print-out-paths .#ghostship-hermes-image)"
fi

image_bundle="$(readlink -f "$image_bundle")"

if [ ! -d "$image_bundle" ]; then
  usage
  echo "image bundle path is not a directory: $image_bundle" >&2
  exit 1
fi

changes_file="$image_bundle/docker-import-changes"
platform_file="$image_bundle/platform"
default_ref_file="$image_bundle/default-image-ref"
rootfs_dir="$(readlink -f "$image_bundle/rootfs")"

if [ ! -f "$changes_file" ] || [ ! -f "$platform_file" ] || [ ! -f "$default_ref_file" ] || [ ! -e "$rootfs_dir" ]; then
  echo "image bundle is missing required files under $image_bundle" >&2
  exit 1
fi

if [ -z "$image_ref" ]; then
  image_ref="$(tr -d '\n' < "$default_ref_file")"
fi

platform="$(tr -d '\n' < "$platform_file")"
rootfs_tar="$(find "$rootfs_dir" -type f -name '*.tar.xz' | head -n 1)"

if [ -z "$rootfs_tar" ]; then
  echo "failed to locate compressed rootfs tarball under $rootfs_dir" >&2
  exit 1
fi

if "$container_engine" image inspect "$image_ref" >/dev/null 2>&1; then
  "$container_engine" image rm -f "$image_ref" >/dev/null
fi

change_args=()
while IFS= read -r change; do
  [ -n "$change" ] || continue
  if [ "$container_engine" = "podman" ] && [[ "$change" == HEALTHCHECK* ]]; then
    continue
  fi
  change_args+=(--change "$change")
done < "$changes_file"

import_args=("${change_args[@]}")
if [ "$container_engine" = "docker" ]; then
  import_args=(--platform "$platform" "${import_args[@]}")
fi

xz -dc "$rootfs_tar" | "$container_engine" import "${import_args[@]}" - "$image_ref" >/dev/null

if [ -n "$archive_path" ]; then
  mkdir -p "$(dirname "$archive_path")"
  save_args=(-o "$archive_path")
  if [ "$container_engine" = "docker" ]; then
    save_args=(--platform "$platform" "${save_args[@]}")
  fi
  "$container_engine" image save "${save_args[@]}" "$image_ref"
fi

printf '%s\n' "$image_ref"
