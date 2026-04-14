#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

usage() {
  cat >&2 <<'EOF'
usage: export_publishable_image.sh [image-ref] [image-archive-path]

Build the Ubuntu workstation image from packages/hermes-image/Dockerfile and
optionally save it as a local archive tar.
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
    echo "docker or podman is required to build ghostship-hermes" >&2
    exit 1
  fi
fi

if ! "$container_engine" version >/dev/null 2>&1; then
  echo "$container_engine is installed but not reachable from this shell" >&2
  exit 1
fi

image_ref="${1:-ghostship-hermes:$(tr -d '\n' < packages/hermes-image/hermes-release.txt)}"
archive_path="${2:-}"
hermes_ref="$(tr -d '\n' < packages/hermes-image/hermes-release.txt)"

"$container_engine" build \
  --build-arg "HERMES_REF=${hermes_ref}" \
  --tag "$image_ref" \
  --file packages/hermes-image/Dockerfile \
  .

if [ -n "$archive_path" ]; then
  mkdir -p "$(dirname "$archive_path")"
  "$container_engine" image save -o "$archive_path" "$image_ref"
fi

printf '%s\n' "$image_ref"
