{
  dockerTools,
  pkgs,
  ghostshipHermesRuntime,
  hermesRelease,
  ghostshipUtilities,
}:
let
  skillsTree = builtins.path {
    path = ../../skills;
    name = "ghostship-hermes-skills";
  };

  rootfs = builtins.path {
    path = ./rootfs;
    name = "ghostship-hermes-rootfs";
  };
in
dockerTools.buildLayeredImage {
  name = "ghostship-hermes";
  tag = hermesRelease;
  contents = with pkgs; [
    bash
    bat
    binutils
    bubblewrap
    cacert
    coreutils
    curl
    delta
    exiftool
    fd
    ffmpeg
    file
    findutils
    gh
    ghostshipHermesRuntime
    git
    gnugrep
    gnused
    hn-text
    jq
    lsof
    miller
    nix
    nodejs_22
    p7zip
    psmisc
    python311
    ripgrep
    ripgrep-all
    rsync
    sqlite-utils
    strace
    tmux
    tree
    ttyd
    unzip
    uv
    visidata
    wget
    yq-go
    yt-dlp
    zip
    codex
    gemini-cli
    opencode
    rootfs
  ] ++ ghostshipUtilities;

  config = {
    WorkingDir = "/home/hermes";
    Entrypoint = [
      "${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime"
      "entrypoint"
    ];
    Env = [
      "HOME=/home/hermes"
      "HERMES_HOME=/home/hermes/.hermes"
      "GHOSTSHIP_HERMES_REF=${hermesRelease}"
      "GHOSTSHIP_DEFAULT_SKILLS=${skillsTree}"
      "NIX_CONFIG=experimental-features = nix-command flakes"
      "SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt"
      "NIX_SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt"
      "PATH=/home/hermes/.hermes/hermes-agent/venv/bin:/home/hermes/.hermes/hermes-agent/node_modules/.bin:/bin"
    ];
    ExposedPorts = {
      "7681/tcp" = { };
    };
    Volumes = {
      "/home/hermes/.hermes" = { };
      "/nix" = { };
    };
    Labels = {
      "org.opencontainers.image.title" = "ghostship-hermes";
      "org.opencontainers.image.description" = "Hermes container with ttyd and curated operator tooling";
      "org.opencontainers.image.version" = hermesRelease;
    };
  };
}
