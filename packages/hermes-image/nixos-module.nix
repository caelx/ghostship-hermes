{
  config,
  lib,
  modulesPath,
  pkgs,
  ghostshipHermesRouter,
  ghostshipHermesRuntime,
  ghostshipUtilities,
  hermesDashboard,
  hermesRelease,
  ...
}:
let
  managedProfiles = [
    "assistant"
    "operations"
    "supervisor"
  ];
  defaultProfile = "assistant";
  rootTerminalCwd = "/home/hermes";
  managedProfileRoot = "/home/hermes/.hermes/profiles";
  sharedSkillSourceDir = "/home/hermes/seeds/shared/skills";
  profileSkillSourceRoot = "/home/hermes/seeds/profiles";
  profileScaffold = {
    assistant = {
      personality = "assistant";
      modelProvider = "openai-codex";
      modelDefault = "gpt-5.4";
      terminalCwd = "/workspace";
      discordBotTokenEnv = "DISCORD_ASSISTANT_BOT_TOKEN";
      discordAllowedUsersEnv = "DISCORD_ASSISTANT_ALLOWED_USERS";
      discordChannelEnv = "DISCORD_ASSISTANT_CHANNEL_ID";
    };
    operations = {
      personality = "operations";
      modelProvider = "openai-codex";
      modelDefault = "gpt-5.4";
      terminalCwd = "/workspace";
      discordBotTokenEnv = "DISCORD_OPERATIONS_BOT_TOKEN";
      discordAllowedUsersEnv = "DISCORD_OPERATIONS_ALLOWED_USERS";
      discordChannelEnv = "DISCORD_OPERATIONS_CHANNEL_ID";
    };
    supervisor = {
      personality = "supervisor";
      modelProvider = "openai-codex";
      modelDefault = "gpt-5.4";
      terminalCwd = "/workspace";
      discordBotTokenEnv = "DISCORD_SUPERVISOR_BOT_TOKEN";
      discordAllowedUsersEnv = "DISCORD_SUPERVISOR_ALLOWED_USERS";
      discordChannelEnv = "DISCORD_SUPERVISOR_CHANNEL_ID";
    };
  };
  auxiliaryModelDefault = "gemini-3.1-flash-lite-preview";
  auxiliaryBaseUrl = "https://generativelanguage.googleapis.com/v1beta/openai/";
  auxiliaryApiKeyRef = "\${GOOGLE_AI_STUDIO_API_KEY}";
  certificateFile = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
  runtimeBin = "${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime";
  yamlFormat = pkgs.formats.yaml { };
  sharedHermesEnvKeys = [
    "GOOGLE_AI_STUDIO_API_KEY"
    "OPENCODE_GO_API_KEY"
    "BROWSERBASE_API_KEY"
    "BROWSERBASE_PROJECT_ID"
    "BROWSER_USE_API_KEY"
    "BROWSERBASE_PROXIES"
    "BROWSERBASE_ADVANCED_STEALTH"
    "BROWSERBASE_KEEP_ALIVE"
    "BROWSERBASE_SESSION_TIMEOUT"
    "BROWSER_INACTIVITY_TIMEOUT"
    "CAMOFOX_URL"
    "BROWSER_CDP_URL"
  ];
  rootConfig = {
    terminal = {
      backend = "local";
      cwd = rootTerminalCwd;
      timeout = 180;
    };
  };
  mkProfileConfig =
    _profileName: profileDef:
    {
      display.personality = profileDef.personality;
      model = {
        provider = profileDef.modelProvider;
        default = profileDef.modelDefault;
      };
      memory = {
        provider = "holographic";
        memory_enabled = true;
        user_profile_enabled = true;
        nudge_interval = 10;
        flush_min_turns = 6;
      };
      plugins.hermes-memory-store = {
        db_path = "$HERMES_HOME/memory_store.db";
        auto_extract = false;
        default_trust = 0.5;
      };
      fallback_model = {
        provider = "opencode-go";
        model = "minimax-m2.7";
      };
      timezone = "Pacific/Honolulu";
      agent = {
        max_turns = 110;
        reasoning_effort = "high";
        verbose = false;
      };
      compression = {
        enabled = true;
        threshold = 0.50;
        target_ratio = 0.25;
        protect_last_n = 20;
      };
      session_reset = {
        mode = "none";
        idle_minutes = 1440;
        at_hour = 4;
      };
      browser = {
        cloud_provider = "local";
        inactivity_timeout = 120;
        command_timeout = 30;
        record_sessions = false;
      };
      approvals = {
        mode = "off";
      };
      security = {
        redact_secrets = true;
        tirith_enabled = true;
        tirith_path = "tirith";
        tirith_timeout = 5;
        tirith_fail_open = true;
        website_blocklist = {
          enabled = false;
          domains = [ ];
          shared_files = [ ];
        };
      };
      checkpoints = {
        enabled = true;
        max_snapshots = 50;
      };
      streaming = {
        enabled = true;
        transport = "edit";
        edit_interval = 0.3;
        buffer_threshold = 40;
      };
      stt = {
        enabled = false;
      };
      human_delay = {
        mode = "off";
      };
      auxiliary = let
        directGemini = {
          model = auxiliaryModelDefault;
          base_url = auxiliaryBaseUrl;
          api_key = auxiliaryApiKeyRef;
        };
      in {
        vision = directGemini;
        web_extract = directGemini;
        approval = directGemini;
        compression = directGemini;
        session_search = directGemini;
        skills_hub = directGemini;
        mcp = directGemini;
        flush_memories = directGemini;
      };
      discord = {
        require_mention = true;
        auto_thread = true;
        reactions = true;
      };
      display = {
        compact = false;
        tool_progress = "new";
        background_process_notifications = "result";
      };
      group_sessions_per_user = true;
      terminal = {
        backend = "local";
        cwd = profileDef.terminalCwd;
        timeout = 180;
      };
    };
  managedProfileNames = lib.concatStringsSep "," managedProfiles;
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
    hermesDashboard
  ];

  servicePath = runtimePackages ++ ghostshipUtilities ++ [ config.services.hermes-agent.package ];
  userCommandEnv = pkgs.buildEnv {
    name = "ghostship-hermes-user-env";
    paths = servicePath;
  };
  profileDefinitions = lib.genAttrs managedProfiles (
    profile:
    let
      profileDef = profileScaffold.${profile};
      profileRoot = "${managedProfileRoot}/${profile}";
    in
    profileDef
    // {
      name = profile;
      profileRoot = profileRoot;
      configPath = "${profileRoot}/config.yaml";
      soulPath = "${profileRoot}/SOUL.md";
      skillPath = "${profileRoot}/skills";
      serviceName = "ghostship-hermes-profile-${profile}";
      serviceDescription = "ghostship-hermes ${profile} gateway";
      serviceWorkingDirectory = profileDef.terminalCwd;
      gatewayScript = pkgs.writeShellScript "ghostship-hermes-profile-${profile}-gateway.sh" ''
        set -euo pipefail

        bot_token="''${${profileDef.discordBotTokenEnv}:-}"
        allowed_users="''${${profileDef.discordAllowedUsersEnv}:-}"
        role_channel="''${${profileDef.discordChannelEnv}:-}"
        general_channel="''${DISCORD_GENERAL_CHANNEL_ID:-}"

        if [ -n "$bot_token" ]; then
          export DISCORD_BOT_TOKEN="$bot_token"
        fi
        if [ -n "$allowed_users" ]; then
          export DISCORD_ALLOWED_USERS="$allowed_users"
        fi
        if [ -n "$role_channel" ]; then
          export DISCORD_FREE_RESPONSE_CHANNELS="$role_channel"
        fi
        if [ -n "$general_channel" ]; then
          export DISCORD_HOME_CHANNEL="$general_channel"
        fi

        exec ${config.services.hermes-agent.package}/bin/hermes -p ${profile} gateway run --replace
      '';
      configFile = yamlFormat.generate "ghostship-hermes-profile-${profile}-config.yaml" (mkProfileConfig profile profileDef);
    }
  );
  mkProfileGatewayService =
    profile:
    let
      profileDef = profileDefinitions.${profile};
    in
    {
      description = profileDef.serviceDescription;
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
        WorkingDirectory = profileDef.serviceWorkingDirectory;
        PassEnvironment = [
          "BWS_ACCESS_TOKEN"
          "DISCORD_GENERAL_CHANNEL_ID"
          profileDef.discordBotTokenEnv
          profileDef.discordAllowedUsersEnv
          profileDef.discordChannelEnv
        ] ++ sharedHermesEnvKeys;
        ExecStart = profileDef.gatewayScript;
        Restart = "always";
        RestartSec = "2s";
      };
    };
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
      if [ ! -d "${profileDefinitions.${profile}.profileRoot}" ]; then
        hermes profile create ${lib.escapeShellArg profile} --clone >/dev/null 2>&1 \
          || hermes profile create ${lib.escapeShellArg profile} >/dev/null 2>&1 \
          || true
      fi

      install -D -m 0600 ${profileDefinitions.${profile}.configFile} "${profileDefinitions.${profile}.configPath}"
    '') managedProfiles}

    copy_skill_tree_if_missing() {
      source_root="$1"
      target_root="$2"

      [ -d "$source_root" ] || return 0
      mkdir -p "$target_root"

      while IFS= read -r skill_dir; do
        [ -f "$skill_dir/SKILL.md" ] || continue
        skill_name="$(basename "$skill_dir")"
        if [ ! -e "$target_root/$skill_name" ]; then
          cp -R "$skill_dir" "$target_root/$skill_name"
        fi
      done < <(find "$source_root" -mindepth 1 -maxdepth 1 -type d | sort)
    }

    copy_file_if_missing() {
      source_path="$1"
      target_path="$2"

      [ -f "$source_path" ] || return 0
      [ -e "$target_path" ] && return 0
      install -D -m 0600 "$source_path" "$target_path"
    }

    reconcile_seed_skills() {
      shared_source="''${GHOSTSHIP_HERMES_SHARED_SKILLS_DIR:-${sharedSkillSourceDir}}"
      profile_root="''${GHOSTSHIP_HERMES_PROFILE_SKILLS_ROOT:-${profileSkillSourceRoot}}"

      copy_skill_tree_if_missing "$shared_source" "/home/hermes/.hermes/skills"

      profile_source="''${profile_root}/assistant/skills"
      copy_skill_tree_if_missing "$profile_source" "${profileDefinitions.assistant.skillPath}"
      copy_file_if_missing "''${profile_root}/assistant/SOUL.md" "${profileDefinitions.assistant.soulPath}"
      profile_source="''${profile_root}/operations/skills"
      copy_skill_tree_if_missing "$profile_source" "${profileDefinitions.operations.skillPath}"
      copy_file_if_missing "''${profile_root}/operations/SOUL.md" "${profileDefinitions.operations.soulPath}"
      profile_source="''${profile_root}/supervisor/skills"
      copy_skill_tree_if_missing "$profile_source" "${profileDefinitions.supervisor.skillPath}"
      copy_file_if_missing "''${profile_root}/supervisor/SOUL.md" "${profileDefinitions.supervisor.soulPath}"
    }

    write_profile_env() {
      target="$1"
      terminal_cwd="$2"
      umask 077
      {
        printf 'TERMINAL_CWD=%s\n' "$terminal_cwd"
        for key in ${lib.escapeShellArgs sharedHermesEnvKeys}; do
          value="''${!key:-}"
          if [ -n "$value" ]; then
            printf '%s=%s\n' "$key" "$value"
          fi
        done
      } >"$target"
    }

    write_profile_env "/home/hermes/.hermes/.env" "${rootTerminalCwd}"
    reconcile_seed_skills

    hermes profile use ${lib.escapeShellArg defaultProfile} >/dev/null 2>&1 || true

    hermes config path >/dev/null 2>&1 || true
    hermes config env-path >/dev/null 2>&1 || true
  '';

  serviceEnvironment = {
    HERMES_HOME = "/home/hermes/.hermes";
    TERMINAL_CWD = "/home/hermes";
    GHOSTSHIP_TERMINAL_CWD = "/home/hermes";
    GHOSTSHIP_DASHBOARD_HOST = "0.0.0.0";
    GHOSTSHIP_HERMES_PROFILES = managedProfileNames;
    GHOSTSHIP_HERMES_DEFAULT_PROFILE = defaultProfile;
    GHOSTSHIP_ROUTER_HOST = "127.0.0.1";
    GHOSTSHIP_ROUTER_PORT = "8788";
    API_SERVER_HOST = "127.0.0.1";
    API_SERVER_PORT = "8788";
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
    doc.enable = true;
    info.enable = true;
    man.enable = true;
    nixos.enable = true;
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
  environment.systemPackages = servicePath;
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
    } // rootConfig;
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
        "GOOGLE_AI_STUDIO_API_KEY"
        "OPENCODE_GO_API_KEY"
        "GHOSTSHIP_HERMES_SHARED_SKILLS_DIR"
        "GHOSTSHIP_HERMES_PROFILE_SKILLS_ROOT"
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
        "OPENCODE_GO_API_KEY"
        "OPENCODE_BASE_URL"
        "GHOSTSHIP_ROUTER_API_KEY"
        "GHOSTSHIP_ROUTER_CORS_ORIGINS"
        "API_SERVER_KEY"
        "API_SERVER_CORS_ORIGINS"
        "GHOSTSHIP_ROUTER_ASSISTED_BUCKET_MODEL"
        "GHOSTSHIP_ROUTER_ASSISTED_BUCKET_BATCH_SIZE"
        "GHOSTSHIP_ROUTER_RANKING_ENABLED"
        "GHOSTSHIP_ROUTER_RANKING_INTERVAL"
        "GHOSTSHIP_ROUTER_RANKING_WORKER_MODEL"
        "GHOSTSHIP_ROUTER_RANKING_SHORTLIST_SIZE"
        "GHOSTSHIP_ROUTER_ROLLING_WINDOW_SECONDS"
        "GHOSTSHIP_ROUTER_PROVIDER_COOLDOWN_SECONDS"
        "GHOSTSHIP_ROUTER_PROVIDER_FAILURE_THRESHOLD"
        "GHOSTSHIP_ROUTER_PROVIDER_RATE_LIMIT_THRESHOLD"
        "GHOSTSHIP_ROUTER_PROVIDER_TIMEOUT_THRESHOLD"
        "GHOSTSHIP_ROUTER_PROVIDER_EXHAUSTION_THRESHOLD"
        "GHOSTSHIP_ROUTER_DISABLED_PROVIDERS"
        "GHOSTSHIP_ROUTER_DISABLED_MODELS"
        "GHOSTSHIP_ROUTER_PROVIDER_WEIGHT_OVERRIDES"
        "GHOSTSHIP_ROUTER_MODEL_WEIGHT_OVERRIDES"
        "GHOSTSHIP_ROUTER_ALIAS_PIN_AUXILIARY"
        "GHOSTSHIP_ROUTER_ALIAS_PIN_CODING"
        "GHOSTSHIP_ROUTER_ALIAS_PIN_AGENTIC"
        "GHOSTSHIP_ROUTER_ALIAS_PIN_VISION"
        "GHOSTSHIP_ROUTER_ALIAS_PIN_TTS"
      ];
      ExecStart = "${ghostshipHermesRouter}/bin/ghostship-hermes-router";
      Restart = "always";
      RestartSec = "2s";
      LimitNOFILE = 65536;
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
      PassEnvironment = [ ];
      ExecStart = "${runtimeBin} dashboard-controller";
      Restart = "always";
      RestartSec = "2s";
    };
  };

  systemd.services.ghostship-hermes-profile-assistant = mkProfileGatewayService "assistant";

  systemd.services.ghostship-hermes-profile-operations = mkProfileGatewayService "operations";

  systemd.services.ghostship-hermes-profile-supervisor = mkProfileGatewayService "supervisor";

  systemd.sockets.nix-daemon = {
    wantedBy = lib.mkForce [ "multi-user.target" ];
    after = [ "ghostship-storage.service" ];
    requires = [ "ghostship-storage.service" ];
  };

  system.extraDependencies = servicePath ++ [ userCommandEnv ];

  environment.etc."ghostship-hermes-release".text = hermesRelease + "\n";
}
