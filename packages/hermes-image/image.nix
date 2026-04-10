{
  lib,
  pkgs,
  system,
  ghostshipHermesRootfs,
  hermesRelease,
  defaultImageRef ? "ghostship-hermes:${hermesRelease}",
}:
let
  platform =
    {
      x86_64-linux = "linux/amd64";
      aarch64-linux = "linux/arm64";
    }
    .${system} or (throw "unsupported system for ghostship-hermes image bundle: ${system}");

  dockerImportChanges = pkgs.writeText "ghostship-hermes-docker-import-changes" ''
    WORKDIR /home/hermes
    ENTRYPOINT ["/init"]
    ENV HOME=/home/hermes
    ENV HERMES_HOME=/home/hermes/.hermes
    EXPOSE 7681/tcp
    VOLUME /home/hermes
    VOLUME /workspace
    LABEL org.opencontainers.image.title="ghostship-hermes"
    LABEL org.opencontainers.image.description="Lean Hermes container with a minimal dashboard, whole-home persistence, and ghostship utilities"
    LABEL org.opencontainers.image.version="${hermesRelease}"
  '';
in
pkgs.runCommand "ghostship-hermes-image" { } ''
  mkdir -p "$out"
  ln -s ${ghostshipHermesRootfs} "$out/rootfs"
  cp ${dockerImportChanges} "$out/docker-import-changes"
  printf '%s\n' '${platform}' > "$out/platform"
  printf '%s\n' '${defaultImageRef}' > "$out/default-image-ref"
''
