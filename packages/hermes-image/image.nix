{
  dockerTools,
  pkgs,
  ghostshipHermesRuntime,
  ghostshipHermesSkills,
  ghostshipHermesWorkstationSeed,
  hermesRelease,
  ghostshipUtilities,
  honchoAi,
  bitwardenCli,
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

  honchoPython = pkgs.python311.withPackages (_: [ honchoAi ]);

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
    bitwardenCli
    feed
    googleWorkspaceCli
    honchoPython
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
    ln -s ${honchoPython}/bin/python3 usr/local/bin/python
  '';
  config = {
    WorkingDir = "/home/hermes";
    Entrypoint = [ "/usr/local/bin/ghostship-hermes-runtime" ];
    Cmd = [ "entrypoint" ];
    Env = [
      "HOME=/home/hermes"
      "HERMES_HOME=/home/hermes/.hermes"
      "BITWARDENCLI_APPDATA_DIR=/home/hermes/.hermes/bitwarden-cli"
      "GHOSTSHIP_HERMES_REF=${hermesRelease}"
      "GHOSTSHIP_DEFAULT_SKILLS=${ghostshipHermesSkills}"
      "GHOSTSHIP_WORKSTATION_SEED=/usr/local/share/ghostship-hermes/workstation-seed"
      "GHOSTSHIP_DASHBOARD_DIR=/usr/local/share/ghostship-hermes/dashboard"
      "NIX_CONFIG=experimental-features = nix-command flakes"
      "SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt"
      "NIX_SSL_CERT_FILE=/etc/ssl/certs/ca-bundle.crt"
      "PATH=/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:/nix/var/nix/profiles/default/bin:/usr/local/bin:/home/hermes/.hermes/hermes-agent/venv/bin:/home/hermes/.hermes/hermes-agent/node_modules/.bin:/bin"
      "PYTHONPATH=${honchoPython}/${pkgs.python311.sitePackages}"
    ];
    ExposedPorts = {
      "7681/tcp" = { };
    };
    Volumes = {
      "/home/hermes" = { };
    };
    Labels = {
      "org.opencontainers.image.title" = "ghostship-hermes";
      "org.opencontainers.image.description" = "Persistent Hermes agent workstation with a Caddy dashboard, per-profile ttyd terminals, and self-updating agent tooling";
      "org.opencontainers.image.version" = hermesRelease;
    };
  };
}
