{
  pkgs,
  overlayEnv,
  baseClosureRoots ? [ ],
}:
let
  overlayClosureInfo = pkgs.closureInfo {
    rootPaths = [ overlayEnv ];
  };
  baseClosureInfo = pkgs.closureInfo {
    rootPaths = baseClosureRoots;
  };
in
pkgs.runCommand "ghostship-hermes-overlay-bundle" { } ''
  mkdir -p "$out/overlay-root/nix/store" "$out/overlay-root/opt"

  base_paths_file="$TMPDIR/base-store-paths"
  touch "$base_paths_file"
  if [ -s ${baseClosureInfo}/store-paths ]; then
    sort -u ${baseClosureInfo}/store-paths > "$base_paths_file"
  fi

  while IFS= read -r store_path; do
    [ -n "$store_path" ] || continue
    if grep -Fxq "$store_path" "$base_paths_file"; then
      continue
    fi
    cp -a "$store_path" "$out/overlay-root/nix/store/"
  done < ${overlayClosureInfo}/store-paths

  cp -a ${overlayEnv} "$out/overlay-root/opt/ghostship-overlay"

  cat > "$out/Dockerfile" <<'DOCKERFILE'
ARG BASE_IMAGE
FROM ''${BASE_IMAGE}
COPY overlay-root/ /
DOCKERFILE
''
