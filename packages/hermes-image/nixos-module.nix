{
  config,
  lib,
  modulesPath,
  pkgs,
  ghostshipHermesRouter,
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

  managedProfiles = [
    "operations"
    "coder"
  ];
  defaultProfile = "operations";
  certificateFile = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
  runtimeBin = "${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime";
  yamlFormat = pkgs.formats.yaml { };
  profileConfig = {
    display.personality = "kawaii";
    model.default = "openrouter/free";
    terminal = {
      backend = "local";
      cwd = "/home/hermes";
      timeout = 180;
    };
  };
  managedProfileNames = lib.concatStringsSep "," managedProfiles;
  managedProfileRoot = "/home/hermes/.hermes/profiles";

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
    ghostshipHermesRouter
    ghostshipHermesRuntime
  ];

  servicePath = runtimePackages ++ ghostshipUtilities ++ [ config.services.hermes-agent.package ];
  userCommandEnv = pkgs.buildEnv {
    name = "ghostship-hermes-user-env";
    paths = servicePath;
  };
  profileConfigFile = yamlFormat.generate "ghostship-hermes-profile-config.yaml" profileConfig;
  bootstrapHermesScript = pkgs.writeShellScript "ghostship-hermes-bootstrap.sh" ''
    set -euo pipefail

    profiles_root="${managedProfileRoot}"
    mkdir -p "$profiles_root"

    for existing in "$profiles_root"/*; do
      [ -d "$existing" ] || continue
      keep=0
      case "$(basename "$existing")" in
        ${lib.concatMapStringsSep "|" (profile: lib.escapeShellArg profile) managedProfiles})
          keep=1
          ;;
      esac
      if [ "$keep" -eq 0 ]; then
        rm -rf "$existing"
        rm -f "/home/hermes/.local/bin/$(basename "$existing")"
      fi
    done

    ${lib.concatMapStringsSep "\n" (profile: ''
      if [ ! -d "${managedProfileRoot}/${profile}" ]; then
        hermes profile create ${lib.escapeShellArg profile} --clone >/dev/null 2>&1 \
          || hermes profile create ${lib.escapeShellArg profile} >/dev/null 2>&1 \
          || true
      fi

      install -D -m 0600 ${profileConfigFile} "${managedProfileRoot}/${profile}/config.yaml"
    '') managedProfiles}

    write_profile_env() {
      target="$1"
      umask 077
      {
        printf 'TERMINAL_CWD=/home/hermes\n'
        for key in OPENROUTER_API_KEY OPENROUTER_BASE_URL OPENROUTER_HTTP_REFERER OPENROUTER_TITLE; do
          value="''${!key:-}"
          if [ -n "$value" ]; then
            printf '%s=%s\n' "$key" "$value"
          fi
        done
      } >"$target"
    }

    write_profile_env "/home/hermes/.hermes/.env"
    write_profile_env "/home/hermes/.hermes/profiles/operations/.env"
    write_profile_env "/home/hermes/.hermes/profiles/coder/.env"

    if [ -n "''${OPENROUTER_TEST_MODEL:-}" ]; then
      hermes config set model.default "$OPENROUTER_TEST_MODEL" >/dev/null 2>&1 || true
      hermes -p operations config set model.default "$OPENROUTER_TEST_MODEL" >/dev/null 2>&1 || true
      hermes -p coder config set model.default "$OPENROUTER_TEST_MODEL" >/dev/null 2>&1 || true
    fi

    hermes profile use ${lib.escapeShellArg defaultProfile} >/dev/null 2>&1 || true

    hermes config path >/dev/null 2>&1 || true
    hermes config env-path >/dev/null 2>&1 || true
  '';

  serviceEnvironment = {
    HERMES_HOME = "/home/hermes/.hermes";
    TERMINAL_CWD = "/home/hermes";
    GHOSTSHIP_TERMINAL_CWD = "/home/hermes";
    GHOSTSHIP_DASHBOARD_HOST = "0.0.0.0";
    GHOSTSHIP_DASHBOARD_ROOT = dashboardTree;
    GHOSTSHIP_HERMES_PROFILES = managedProfileNames;
    GHOSTSHIP_HERMES_DEFAULT_PROFILE = defaultProfile;
    GHOSTSHIP_ROUTER_HOST = "127.0.0.1";
    GHOSTSHIP_ROUTER_PORT = "8788";
    GHOSTSHIP_ROUTER_STATE_DIR = "/home/hermes/.local/state/ghostship-hermes/router";
    GHOSTSHIP_ROUTER_DB_PATH = "/home/hermes/.local/state/ghostship-hermes/router/router.db";
    GHOSTSHIP_ROUTER_REFRESH_INTERVAL = "300";
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
    } // profileConfig;
    extraPackages = [ pkgs.nix ] ++ ghostshipUtilities;
  };

  users.users.hermes.packages = [ userCommandEnv ];

  systemd.services.ghostship-storage = {
    description = "Prepare ghostship-hermes persisted storage";
    wantedBy = [ "multi-user.target" ];
    before = [
      "hermes-agent.service"
      "ghostship-dashboard-controller.service"
      "ghostship-hermes-router.service"
    ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${runtimeBin} prepare-storage";
    };
  };

  systemd.services.hermes-agent = {
    wantedBy = lib.mkForce [ ];
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
    ];
    requires = [
      "ghostship-storage.service"
    ];
    environment = userServiceEnvironment;
    path = servicePath;
    serviceConfig = {
      Type = "oneshot";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      PassEnvironment = [
        "OPENROUTER_API_KEY"
        "OPENROUTER_BASE_URL"
        "OPENROUTER_HTTP_REFERER"
        "OPENROUTER_TITLE"
        "OPENCODE_API_KEY"
        "OPENCODE_BASE_URL"
        "OPENROUTER_TEST_MODEL"
      ];
      ExecStart = bootstrapHermesScript;
    };
  };

  systemd.services.ghostship-hermes-router = {
    description = "ghostship-hermes model router";
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
      PassEnvironment = [
        "OPENROUTER_API_KEY"
        "OPENROUTER_BASE_URL"
        "OPENROUTER_HTTP_REFERER"
        "OPENROUTER_TITLE"
        "OPENCODE_API_KEY"
        "OPENCODE_BASE_URL"
        "GHOSTSHIP_ROUTER_GEMINI_FALLBACK_MODEL"
        "GHOSTSHIP_ROUTER_ASSISTED_BUCKET_MODEL"
      ];
      ExecStart = "${ghostshipHermesRouter}/bin/ghostship-hermes-router";
      Restart = "always";
      RestartSec = "2s";
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

  systemd.services.ghostship-hermes-profile-operations = {
    description = "ghostship-hermes operations gateway";
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
    environment = userServiceEnvironment // {
      HERMES_MANAGED = "true";
    };
    path = servicePath;
    serviceConfig = {
      Type = "simple";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      ExecStart = "${config.services.hermes-agent.package}/bin/hermes -p operations gateway run --replace";
      Restart = "always";
      RestartSec = "2s";
    };
  };

  systemd.services.ghostship-hermes-profile-coder = {
    description = "ghostship-hermes coder gateway";
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
    environment = userServiceEnvironment // {
      HERMES_MANAGED = "true";
    };
    path = servicePath;
    serviceConfig = {
      Type = "simple";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      ExecStart = "${config.services.hermes-agent.package}/bin/hermes -p coder gateway run --replace";
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
