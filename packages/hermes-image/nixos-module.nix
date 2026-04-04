{
  config,
  lib,
  modulesPath,
  pkgs,
  ghostshipHermesRuntime,
  ghostshipUtilities,
  hermesRelease,
  ...
}:
let
  dashboardTree = builtins.path {
    path = ./dashboard;
    name = "ghostship-hermes-dashboard";
  };

  bootstrapProfiles = [
    "test"
    "coder"
  ];
  certificateFile = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
  runtimeBin = "${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime";

  runtimePackages = with pkgs; [
    bashInteractive
    cacert
    coreutils
    curl
    findutils
    git
    gnugrep
    gnused
    jq
    nix
    procps
    python3
    tirith
    ttyd
    util-linux
    ghostshipHermesRuntime
  ];

  servicePath = runtimePackages ++ ghostshipUtilities ++ [ config.services.hermes-agent.package ];
  userCommandEnv = pkgs.buildEnv {
    name = "ghostship-hermes-user-env";
    paths = servicePath;
  };
  bootstrapHermesScript = pkgs.writeShellScript "ghostship-hermes-bootstrap.sh" ''
    set -euo pipefail

    ${lib.concatMapStringsSep "\n" (profile: ''
      if [ ! -d "/home/hermes/.hermes/profiles/${profile}" ]; then
        hermes profile create ${lib.escapeShellArg profile} --clone >/dev/null 2>&1 \
          || hermes profile create ${lib.escapeShellArg profile} >/dev/null 2>&1 \
          || true
      fi
    '') bootstrapProfiles}

    hermes config path >/dev/null 2>&1 || true
    hermes config env-path >/dev/null 2>&1 || true
  '';

  serviceEnvironment = {
    HERMES_HOME = "/home/hermes/.hermes";
    TERMINAL_CWD = "/home/hermes";
    GHOSTSHIP_TERMINAL_CWD = "/home/hermes";
    GHOSTSHIP_DASHBOARD_HOST = "0.0.0.0";
    GHOSTSHIP_DASHBOARD_ROOT = dashboardTree;
    SSL_CERT_FILE = certificateFile;
    NIX_SSL_CERT_FILE = certificateFile;
  };

  userServiceEnvironment = serviceEnvironment // {
    HOME = "/home/hermes";
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
  networking.firewall.allowedTCPPorts = [ 7681 ];
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

  environment.variables = serviceEnvironment;
  environment.shellInit = ''
    if [ "$(id -u)" = "3000" ]; then
      export HOME=/home/hermes
    fi
    export PATH="${userCommandEnv}/bin:$HOME/.local/bin:$HOME/.nix-profile/bin:$PATH"
    export HERMES_HOME=/home/hermes/.hermes
    export TERMINAL_CWD=/home/hermes
    export SSL_CERT_FILE=${certificateFile}
    export NIX_SSL_CERT_FILE=${certificateFile}
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

  services.hermes-agent = {
    enable = true;
    addToSystemPackages = false;
    createUser = false;
    user = "hermes";
    group = "hermes";
    stateDir = "/home/hermes";
    workingDirectory = "/home/hermes";
    extraArgs = [
      "run"
      "--replace"
    ];
    environment = {
      TERMINAL_CWD = "/home/hermes";
    };
    settings = {
      display.personality = "kawaii";
      model.default = "anthropic/claude-sonnet-4";
      terminal = {
        backend = "local";
        cwd = "/home/hermes";
        timeout = 180;
      };
    };
    extraPackages = [ pkgs.nix ] ++ ghostshipUtilities;
  };

  users.users.hermes.packages = [ userCommandEnv ];

  systemd.services.ghostship-storage = {
    description = "Prepare ghostship-hermes persisted storage";
    wantedBy = [ "multi-user.target" ];
    before = [
      "hermes-agent.service"
      "ghostship-dashboard-controller.service"
    ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${runtimeBin} prepare-storage";
    };
  };

  systemd.services.hermes-agent = {
    after = [ "ghostship-storage.service" ];
    requires = [ "ghostship-storage.service" ];
    environment = lib.mkForce (
      userServiceEnvironment
      // {
        HERMES_MANAGED = "true";
      }
    );
    serviceConfig = {
      User = lib.mkForce "hermes";
      Group = lib.mkForce "hermes";
      WorkingDirectory = lib.mkForce "/home/hermes";
    };
  };

  systemd.services.ghostship-hermes-bootstrap = {
    description = "Bootstrap ghostship-hermes Hermes profiles";
    wantedBy = [ "multi-user.target" ];
    after = [
      "ghostship-storage.service"
      "hermes-agent.service"
    ];
    requires = [
      "ghostship-storage.service"
      "hermes-agent.service"
    ];
    environment = userServiceEnvironment;
    path = servicePath;
    serviceConfig = {
      Type = "oneshot";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      ExecStart = bootstrapHermesScript;
    };
  };

  systemd.services.ghostship-dashboard-controller = {
    description = "ghostship-hermes dashboard controller";
    wantedBy = [ "multi-user.target" ];
    wants = [ "network-online.target" ];
    after = [
      "ghostship-storage.service"
      "ghostship-hermes-bootstrap.service"
      "network-online.target"
    ];
    requires = [
      "ghostship-storage.service"
      "ghostship-hermes-bootstrap.service"
    ];
    environment = userServiceEnvironment;
    path = servicePath;
    serviceConfig = {
      Type = "simple";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      ExecStart = "${runtimeBin} dashboard-controller";
      Restart = "always";
      RestartSec = "2s";
    };
  };

  systemd.sockets.nix-daemon = {
    wantedBy = lib.mkForce [ "multi-user.target" ];
    after = [ "ghostship-storage.service" ];
    requires = [ "ghostship-storage.service" ];
  };

  system.extraDependencies = servicePath ++ [ userCommandEnv ];

  environment.etc."ghostship-hermes-release".text = hermesRelease + "\n";
}
