{
  dockerTools,
  pkgs,
  ghostshipHermesRuntime,
  ghostshipHermesSkills,
  ghostshipHermesWorkstationSeed,
  hermesRelease,
  ghostshipUtilities,
  bitwardenSecretsCli,
  feed,
  googleWorkspaceCli,
}:
let
  dashboardTree = builtins.path {
    path = ./rootfs/share/ghostship-hermes/dashboard;
    name = "ghostship-hermes-dashboard";
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
    caddy
    coreutils
    curl
    delta
    dnsutils
    entr
    exiftool
    fd
    ffmpeg
    file
    findutils
    fzf
    gawk
    gh
    git
    git-lfs
    gnugrep
    gnused
    hn-text
    iproute2
    iputils
    jq
    less
    lsof
    man-db
    man-pages
    miller
    nix
    nodejs_22
    openssl
    p7zip
    procps
    psmisc
    ripgrep
    ripgrep-all
    rsync
    sqlite-utils
    strace
    shellcheck
    bats
    systemd
    dbus
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
    util-linux
    codex
    gemini-cli
    opencode
    bitwardenSecretsCli
    feed
    googleWorkspaceCli
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
    mkdir -p usr/local/share/ghostship-hermes/dashboard
    mkdir -p usr/local/share/ghostship-hermes/workstation-seed
    cp ${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime usr/local/bin/ghostship-hermes-runtime
    chmod 0755 usr/local/bin/ghostship-hermes-runtime
    cp -R ${dashboardTree}/. usr/local/share/ghostship-hermes/dashboard/
    cp -R ${ghostshipHermesWorkstationSeed}/. usr/local/share/ghostship-hermes/workstation-seed/
  '';
  config = {
    WorkingDir = "/home/hermes";
    Entrypoint = [ "/usr/local/bin/ghostship-hermes-runtime" ];
    Cmd = [ "entrypoint" ];
    Env = [
      "HOME=/home/hermes"
      "HERMES_HOME=/opt/data"
    ];
    ExposedPorts = {
      "7681/tcp" = { };
    };
    Volumes = {
      "/opt/data" = { };
      "/workspace" = { };
    };
    Labels = {
      "org.opencontainers.image.title" = "ghostship-hermes";
      "org.opencontainers.image.description" = "Persistent Hermes agent workstation with a Caddy dashboard, per-profile ttyd terminals, and self-updating agent tooling";
      "org.opencontainers.image.version" = hermesRelease;
    };
  };
}
