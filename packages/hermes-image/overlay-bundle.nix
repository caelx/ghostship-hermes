{ pkgs, overlayEnv }:
let
  closureInfo = pkgs.closureInfo {
    rootPaths = [ overlayEnv ];
  };
in
pkgs.runCommand "ghostship-hermes-overlay-bundle" { } ''
  mkdir -p "$out/overlay-root/nix/store" "$out/overlay-root/opt"

  while IFS= read -r store_path; do
    [ -n "$store_path" ] || continue
    cp -a "$store_path" "$out/overlay-root/nix/store/"
  done < ${closureInfo}/store-paths

  cp -a ${overlayEnv} "$out/overlay-root/opt/ghostship-overlay"

  cat > "$out/Dockerfile" <<'DOCKERFILE'
ARG BASE_IMAGE
FROM ''${BASE_IMAGE}
COPY overlay-root/ /
DOCKERFILE
''
