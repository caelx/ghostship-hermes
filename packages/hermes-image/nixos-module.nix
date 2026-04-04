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
    path = ./rootfs/share/ghostship-hermes/dashboard;
    name = "ghostship-hermes-dashboard";
  };

  certificateFile = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
  runtimeBin = "${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime";

  basePackages = with pkgs; [
    bashInteractive
    cacert
    caddy
    coreutils
    curl
    git
    jq
    nix
    procps
    python3
    ttyd
    util-linux
    ghostshipHermesRuntime
  ];

  serviceEnvironment = {
    HERMES_HOME = "/data/.hermes";
    MESSAGING_CWD = "/workspace";
    SSL_CERT_FILE = certificateFile;
    NIX_SSL_CERT_FILE = certificateFile;
  };

  userServiceEnvironment = serviceEnvironment // {
    HOME = "/home/hermes";
  };

  caddyConfig = pkgs.writeText "ghostship-hermes-caddyfile" ''
    :7681 {
      root * ${dashboardTree}
      handle /api/* {
        reverse_proxy 127.0.0.1:7683
      }
      handle /healthz {
        reverse_proxy 127.0.0.1:7683
      }
      handle /terminal* {
        reverse_proxy 127.0.0.1:7682
      }
      file_server
    }
  '';
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

  environment.systemPackages = basePackages ++ ghostshipUtilities;
  environment.variables = serviceEnvironment;
  environment.shellInit = ''
    if [ "$(id -u)" = "3000" ]; then
      export HOME=/home/hermes
    fi
    export PATH="$HOME/.local/bin:$HOME/.nix-profile/bin:$PATH"
    export HERMES_HOME=/data/.hermes
    export MESSAGING_CWD=/workspace
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
    addToSystemPackages = true;
    createUser = false;
    user = "hermes";
    group = "hermes";
    stateDir = "/data";
    workingDirectory = "/workspace";
    extraArgs = [
      "run"
      "--replace"
    ];
    environment = {
      TERMINAL_CWD = "/workspace";
    };
    settings = {
      model.default = "anthropic/claude-sonnet-4";
      terminal = {
        backend = "local";
        cwd = "/workspace";
        timeout = 180;
      };
    };
    extraPackages = [ pkgs.nix ] ++ ghostshipUtilities;
  };

  systemd.tmpfiles.rules = [
    "L+ /usr/local/share/ghostship-hermes/dashboard - - - - ${dashboardTree}"
  ];

  systemd.services.ghostship-storage = {
    description = "Prepare ghostship-hermes persisted storage";
    wantedBy = [ "multi-user.target" ];
    before = [
      "hermes-agent.service"
      "ghostship-dashboard-controller.service"
      "ghostship-caddy.service"
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
      WorkingDirectory = lib.mkForce "/workspace";
    };
  };

  systemd.services.ghostship-dashboard-controller = {
    description = "ghostship-hermes dashboard controller";
    wantedBy = [ "multi-user.target" ];
    wants = [ "network-online.target" ];
    after = [
      "ghostship-storage.service"
      "network-online.target"
    ];
    requires = [ "ghostship-storage.service" ];
    environment = userServiceEnvironment;
    path = config.environment.systemPackages;
    serviceConfig = {
      Type = "simple";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/workspace";
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

  systemd.services.ghostship-caddy = {
    description = "ghostship-hermes dashboard";
    wantedBy = [ "multi-user.target" ];
    after = [
      "ghostship-storage.service"
      "ghostship-dashboard-controller.service"
    ];
    requires = [
      "ghostship-storage.service"
      "ghostship-dashboard-controller.service"
    ];
    environment = userServiceEnvironment;
    path = config.environment.systemPackages;
    serviceConfig = {
      Type = "simple";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/workspace";
      ExecStart = "${pkgs.caddy}/bin/caddy run --config ${caddyConfig} --adapter caddyfile";
      Restart = "always";
      RestartSec = "2s";
    };
  };

  system.extraDependencies = basePackages ++ ghostshipUtilities ++ [ config.services.hermes-agent.package ];

  environment.etc."ghostship-hermes-release".text = hermesRelease + "\n";
}
