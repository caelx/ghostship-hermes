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
  imageContents = with pkgs; [
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
    s6
    tree
    ttyd
    unzip
    uv
    visidata
    wget
    yq-go
    yt-dlp
    zip
    util-linux
    codex
    gemini-cli
    opencode
    rootfs
  ] ++ ghostshipUtilities;
in
dockerTools.buildImage {
  name = "ghostship-hermes";
  tag = hermesRelease;
  copyToRoot = pkgs.buildEnv {
    name = "ghostship-hermes-root";
    paths = imageContents;
    pathsToLink = [ "/" ];
  };
  extraCommands = ''
    mkdir -p usr/local/bin
    cp ${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime usr/local/bin/ghostship-hermes-runtime
    chmod 0755 usr/local/bin/ghostship-hermes-runtime
  '';
  config = {
    WorkingDir = "/home/hermes";
    Entrypoint = [ "/usr/local/bin/ghostship-hermes-runtime" ];
    Cmd = [ "entrypoint" ];
    Env = [
      "HOME=/home/hermes"
      "HERMES_HOME=/home/hermes/.hermes"
      "GHOSTSHIP_HERMES_REF=${hermesRelease}"
      "GHOSTSHIP_DEFAULT_SKILLS=${skillsTree}"
      "NIX_CONFIG=experimental-features = nix-command flakes"
      "SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt"
      "NIX_SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt"
      "PATH=/usr/local/bin:/home/hermes/.hermes/hermes-agent/venv/bin:/home/hermes/.hermes/hermes-agent/node_modules/.bin:/bin"
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
