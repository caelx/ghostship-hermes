{
  lib,
  pkgs,
  modulesPath,
  config,
  ghostshipHermesRuntime,
  ghostshipHermesSkills,
  ghostshipHermesWorkstationSeed,
  hermesRelease,
  bitwardenSecretsCli,
  feed,
  googleWorkspaceCli,
  ghostshipUtilities,
  ...
}:
let
  dashboardTree = builtins.path {
    path = ./rootfs/share/ghostship-hermes/dashboard;
    name = "ghostship-hermes-dashboard";
  };

  runtimeBin = "${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime";

  commonService = {
    serviceConfig = {
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      Restart = "on-failure";
      RestartSec = "2s";
    };
    environment = {
      HOME = "/home/hermes";
      HERMES_HOME = "/opt/data";
    };
    path = config.environment.systemPackages;
  };
in
{
  imports = [
    "${modulesPath}/profiles/docker-container.nix"
  ];

  documentation = {
    doc.enable = false;
    info.enable = false;
    man.enable = false;
    nixos.enable = false;
  };

  networking.hostName = "ghostship-hermes";
  networking.useDHCP = lib.mkDefault true;
  system.stateVersion = "25.11";

  users.mutableUsers = false;
  users.allowNoPasswordLogin = true;
  users.manageLingering = true;
  users.groups.hermes.gid = 3000;
  users.users.hermes = {
    isNormalUser = true;
    uid = 3000;
    group = "hermes";
    home = "/home/hermes";
    shell = pkgs.bashInteractive;
    linger = true;
    extraGroups = [ "users" ];
  };

  services.dbus.enable = true;
  security.sudo.enable = false;

  environment.systemPackages =
    with pkgs;
    [
      bashInteractive
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
      ghostshipHermesRuntime
    ]
    ++ ghostshipUtilities;

  environment.variables = {
    HOME = "/home/hermes";
    HERMES_HOME = "/opt/data";
  };

  environment.shellInit = ''
    export PATH="$HOME/.local/bin:$PATH"
    export XDG_RUNTIME_DIR="''${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
    export DBUS_SESSION_BUS_ADDRESS="''${DBUS_SESSION_BUS_ADDRESS:-unix:path=$XDG_RUNTIME_DIR/bus}"
  '';

  nix.settings = {
    experimental-features = [
      "nix-command"
      "flakes"
    ];
    trusted-users = [
      "root"
      "hermes"
    ];
  };

  systemd.tmpfiles.rules = [
    "L+ /usr/local/bin/ghostship-hermes-runtime - - - - ${runtimeBin}"
    "L+ /usr/local/share/ghostship-hermes/skills - - - - ${ghostshipHermesSkills}"
    "L+ /usr/local/share/ghostship-hermes/workstation-seed - - - - ${ghostshipHermesWorkstationSeed}"
    "L+ /usr/local/share/ghostship-hermes/dashboard - - - - ${dashboardTree}"
  ];

  systemd.services.ghostship-storage = {
    description = "Prepare ghostship-hermes persisted storage";
    wantedBy = [ "multi-user.target" ];
    before = [
      "ghostship-workstation-bootstrap.service"
      "user@3000.service"
    ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${runtimeBin} prepare-runtime-storage";
    };
  };

  systemd.services.ghostship-workstation-bootstrap =
    commonService
    // {
      description = "Bootstrap ghostship-hermes workstation state";
      wantedBy = [ "multi-user.target" ];
      wants = [ "network-online.target" ];
      after = [
        "ghostship-storage.service"
        "network-online.target"
        "dbus.service"
      ];
      requires = [ "ghostship-storage.service" ];
      serviceConfig =
        commonService.serviceConfig
        // {
          Type = "oneshot";
          RemainAfterExit = true;
          ExecStart = "${runtimeBin} workstation-bootstrap";
        };
    };

  systemd.services.ghostship-hermes-user-manager = {
    description = "Start the hermes systemd user manager";
    wantedBy = [ "multi-user.target" ];
    after = [
      "ghostship-workstation-bootstrap.service"
      "user-runtime-dir@3000.service"
      "linger-users.service"
    ];
    requires = [
      "ghostship-workstation-bootstrap.service"
      "user-runtime-dir@3000.service"
    ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${config.systemd.package}/bin/systemctl start user@3000.service";
    };
  };

  systemd.services.ghostship-caddy =
    commonService
    // {
      description = "ghostship-hermes Caddy dashboard";
      wantedBy = [ "multi-user.target" ];
      after = [ "ghostship-workstation-bootstrap.service" ];
      requires = [ "ghostship-workstation-bootstrap.service" ];
      serviceConfig =
        commonService.serviceConfig
        // {
          Type = "simple";
          ExecStart = "${runtimeBin} caddy-service";
          Restart = "always";
        };
    };

  systemd.services.ghostship-profile-reconciler =
    commonService
    // {
      description = "ghostship-hermes profile reconciler";
      wantedBy = [ "multi-user.target" ];
      after = [
        "ghostship-workstation-bootstrap.service"
        "ghostship-hermes-user-manager.service"
      ];
      requires = [
        "ghostship-workstation-bootstrap.service"
        "ghostship-hermes-user-manager.service"
      ];
      serviceConfig =
        commonService.serviceConfig
        // {
          Type = "simple";
          ExecStart = "${runtimeBin} profile-reconciler-loop";
          Restart = "always";
        };
    };

  systemd.services.ghostship-app-update =
    commonService
    // {
      description = "ghostship-hermes agent app updater";
      wantedBy = [ "multi-user.target" ];
      after = [ "ghostship-workstation-bootstrap.service" ];
      requires = [ "ghostship-workstation-bootstrap.service" ];
      serviceConfig =
        commonService.serviceConfig
        // {
          Type = "oneshot";
          ExecStart = "${runtimeBin} update-apps-once";
          Restart = "no";
        };
    };

  systemd.timers.ghostship-app-update = {
    description = "Run ghostship-hermes app updates every 6 hours";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "20m";
      OnUnitActiveSec = "6h";
      RandomizedDelaySec = "15m";
      Unit = "ghostship-app-update.service";
    };
  };

  systemd.services.ghostship-asset-refresh =
    commonService
    // {
      description = "ghostship-hermes asset refresher";
      wantedBy = [ "multi-user.target" ];
      after = [ "ghostship-workstation-bootstrap.service" ];
      requires = [ "ghostship-workstation-bootstrap.service" ];
      serviceConfig =
        commonService.serviceConfig
        // {
          Type = "oneshot";
          ExecStart = "${runtimeBin} refresh-assets-once";
          Restart = "no";
        };
    };

  systemd.timers.ghostship-asset-refresh = {
    description = "Run ghostship-hermes asset refresh every 6 hours";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "30m";
      OnUnitActiveSec = "6h";
      RandomizedDelaySec = "20m";
      Unit = "ghostship-asset-refresh.service";
    };
  };

  systemd.services.ghostship-opencode-model-refresh =
    commonService
    // {
      description = "ghostship-hermes opencode model refresher";
      wantedBy = [ "multi-user.target" ];
      after = [ "ghostship-workstation-bootstrap.service" ];
      requires = [ "ghostship-workstation-bootstrap.service" ];
      serviceConfig =
        commonService.serviceConfig
        // {
          Type = "oneshot";
          ExecStart = "${runtimeBin} refresh-opencode-models-once";
          Restart = "no";
        };
    };

  systemd.timers.ghostship-opencode-model-refresh = {
    description = "Run ghostship-hermes opencode model refresh daily";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "45m";
      OnUnitActiveSec = "1d";
      RandomizedDelaySec = "30m";
      Unit = "ghostship-opencode-model-refresh.service";
    };
  };
}
