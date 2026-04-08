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
  rootTerminalCwd = "/workspace";
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
    "OPENROUTER_API_KEY"
    "OPENCODE_API_KEY"
    "OPENCODE_GO_API_KEY"
    "GITHUB_TOKEN"
    "GH_TOKEN"
    "HASS_TOKEN"
    "HASS_URL"
    "BWS_ACCESS_TOKEN"
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
  toolingProjectRoot = "/home/hermes/.hermes/hermes-agent";
  managedUserPackages = [
    {
      name = "hermes-agent";
      ref = "github:NousResearch/hermes-agent/${hermesRelease}#default";
    }
    {
      name = "git";
      ref = "nixpkgs#git";
    }
    {
      name = "curl";
      ref = "nixpkgs#curl";
    }
    {
      name = "jq";
      ref = "nixpkgs#jq";
    }
    {
      name = "python3";
      ref = "nixpkgs#python3";
    }
    {
      name = "nix";
      ref = "nixpkgs#nix";
    }
    {
      name = "ripgrep";
      ref = "nixpkgs#ripgrep";
    }
    {
      name = "nodejs_22";
      ref = "nixpkgs#nodejs_22";
    }
  ];
  managedNpmPackages = [
    "@openai/codex"
    "@google/gemini-cli"
    "opencode-ai"
    "agent-browser"
  ];
  managedNpmBins = [
    "codex"
    "gemini"
    "opencode"
    "agent-browser"
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
  systemPackages = with pkgs; [
    bashInteractive
    cacert
    coreutils
    findutils
    gnugrep
    gnused
    procps
    tirith
    ttyd
    util-linux
    ghostshipHermesRouter
    ghostshipHermesRuntime
    hermesDashboard
  ];

  toolingFallbackPackages = with pkgs; [
    curl
    git
    jq
    nix
    nodejs_22
    python3
    ripgrep
  ];

  servicePath = systemPackages ++ toolingFallbackPackages ++ ghostshipUtilities ++ [ config.services.hermes-agent.package ];
  fallbackCommandEnv = pkgs.buildEnv {
    name = "ghostship-hermes-fallback-env";
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

        export PATH="/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:$PATH"

        exec hermes -p ${profile} gateway run --replace
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
        EnvironmentFile = [ "-${profileDef.profileRoot}/.env" ];
        ExecStart = profileDef.gatewayScript;
        Restart = "always";
        RestartSec = "2s";
      };
    };
  bootstrapHermesScript = pkgs.writeShellScript "ghostship-hermes-bootstrap.sh" ''
    set -euo pipefail

    export PATH="/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:$PATH"

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
      bot_token_env="''${3:-}"
      allowed_users_env="''${4:-}"
      role_channel_env="''${5:-}"
      general_channel="''${DISCORD_GENERAL_CHANNEL_ID:-}"
      umask 077
      {
        printf 'TERMINAL_CWD=%s\n' "$terminal_cwd"
        for key in ${lib.escapeShellArgs sharedHermesEnvKeys}; do
          value="''${!key:-}"
          if [ -n "$value" ]; then
            printf '%s=%s\n' "$key" "$value"
          fi
        done
        if [ -z "''${OPENCODE_API_KEY:-}" ] && [ -n "''${OPENCODE_GO_API_KEY:-}" ]; then
          printf 'OPENCODE_API_KEY=%s\n' "''${OPENCODE_GO_API_KEY}"
        fi
        if [ -n "$bot_token_env" ]; then
          bot_token="''${!bot_token_env:-}"
          if [ -n "$bot_token" ]; then
            printf 'DISCORD_BOT_TOKEN=%s\n' "$bot_token"
          fi
        fi
        if [ -n "$allowed_users_env" ]; then
          allowed_users="''${!allowed_users_env:-}"
          if [ -n "$allowed_users" ]; then
            printf 'DISCORD_ALLOWED_USERS=%s\n' "$allowed_users"
          fi
        fi
        if [ -n "$role_channel_env" ]; then
          role_channel="''${!role_channel_env:-}"
          if [ -n "$role_channel" ]; then
            printf 'DISCORD_FREE_RESPONSE_CHANNELS=%s\n' "$role_channel"
          fi
        fi
        if [ -n "$general_channel" ]; then
          printf 'DISCORD_HOME_CHANNEL=%s\n' "$general_channel"
        fi
      } >"$target"
    }

    write_profile_env "${profileDefinitions.assistant.profileRoot}/.env" "${profileDefinitions.assistant.serviceWorkingDirectory}" "${profileDefinitions.assistant.discordBotTokenEnv}" "${profileDefinitions.assistant.discordAllowedUsersEnv}" "${profileDefinitions.assistant.discordChannelEnv}"
    write_profile_env "${profileDefinitions.operations.profileRoot}/.env" "${profileDefinitions.operations.serviceWorkingDirectory}" "${profileDefinitions.operations.discordBotTokenEnv}" "${profileDefinitions.operations.discordAllowedUsersEnv}" "${profileDefinitions.operations.discordChannelEnv}"
    write_profile_env "${profileDefinitions.supervisor.profileRoot}/.env" "${profileDefinitions.supervisor.serviceWorkingDirectory}" "${profileDefinitions.supervisor.discordBotTokenEnv}" "${profileDefinitions.supervisor.discordAllowedUsersEnv}" "${profileDefinitions.supervisor.discordChannelEnv}"
    reconcile_seed_skills

    hermes profile use ${lib.escapeShellArg defaultProfile} >/dev/null 2>&1 || true

    hermes config path >/dev/null 2>&1 || true
    hermes config env-path >/dev/null 2>&1 || true
  '';

  managedUserToolingScript = pkgs.writeShellScript "ghostship-hermes-user-tooling.sh" ''
    set -euo pipefail

    mode="''${1:-bootstrap}"
    export HOME=/home/hermes
    export HERMES_HOME=/home/hermes/.hermes
    export GHOSTSHIP_HERMES_PROJECT_ROOT="''${GHOSTSHIP_HERMES_PROJECT_ROOT:-${toolingProjectRoot}}"
    export PATH="$HOME/.local/bin:$HOME/.nix-profile/bin:${lib.makeBinPath servicePath}:$PATH"
    export npm_config_update_notifier=false
    export npm_config_fund=false
    export npm_config_cache="$HOME/.cache/npm"
    export GHOSTSHIP_TOOLING_MODE="$mode"

    mkdir -p "$GHOSTSHIP_HERMES_PROJECT_ROOT" "$HOME/.local/bin" "$npm_config_cache"

    python3 - <<'PY2'
import json
import os
import subprocess

mode = os.environ.get("GHOSTSHIP_TOOLING_MODE", "bootstrap")
specs = json.loads(r"""${builtins.toJSON managedUserPackages}""")
result = subprocess.run(["nix", "profile", "list", "--json"], check=True, capture_output=True, text=True)
installed = set(json.loads(result.stdout).get("elements", {}).keys())
missing = [item["ref"] for item in specs if item["name"] not in installed]
if missing:
    subprocess.run(["nix", "profile", "add", *missing], check=True)
if mode == "refresh":
    subprocess.run(["nix", "profile", "upgrade", "--all"], check=True)
PY2

    cd "$GHOSTSHIP_HERMES_PROJECT_ROOT"
    if [ ! -f package.json ]; then
      cat > package.json <<'JSON'
{
  "name": "ghostship-hermes-runtime-tools",
  "private": true
}
JSON
    fi

    npm install --silent --save-dev ${lib.escapeShellArgs (map (pkg: "${pkg}@latest") managedNpmPackages)}

    for bin in ${lib.escapeShellArgs managedNpmBins}; do
      if [ -x "$GHOSTSHIP_HERMES_PROJECT_ROOT/node_modules/.bin/$bin" ]; then
        ln -sfn "$GHOSTSHIP_HERMES_PROJECT_ROOT/node_modules/.bin/$bin" "$HOME/.local/bin/$bin"
      fi
    done
  '';

  serviceEnvironment = {
    HERMES_HOME = "/home/hermes/.hermes";
    GHOSTSHIP_HERMES_PROJECT_ROOT = toolingProjectRoot;
    TERMINAL_CWD = "/workspace";
    GHOSTSHIP_TERMINAL_CWD = "/workspace";
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
  networking.resolvconf.enable = false;
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
  environment.systemPackages = systemPackages;
  environment.shellInit = ''
    if [ "$(id -u)" = "3000" ]; then
      export HOME=/home/hermes
    fi
    export PATH="/home/hermes/.local/bin:/home/hermes/.nix-profile/bin:${fallbackCommandEnv}/bin:$PATH"
    export HERMES_HOME=/home/hermes/.hermes
    export GHOSTSHIP_HERMES_PROJECT_ROOT=${toolingProjectRoot}
    export TERMINAL_CWD=/workspace
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
      TERMINAL_CWD = "/workspace";
    };
    settings = {
    } // rootConfig;
    extraPackages = [ pkgs.nix ] ++ ghostshipUtilities;
  };


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

  systemd.services.ghostship-hermes-user-tooling = {
    description = "Converge ghostship-hermes user tooling";
    wantedBy = [ "multi-user.target" ];
    wants = [ "network-online.target" ];
    after = [
      "ghostship-storage.service"
      "nix-daemon.service"
      "network-online.target"
    ];
    requires = [
      "ghostship-storage.service"
      "nix-daemon.service"
    ];
    before = [
      "ghostship-hermes-bootstrap.service"
      "ghostship-hermes-router.service"
      "ghostship-dashboard-controller.service"
      "ghostship-hermes-profile-assistant.service"
      "ghostship-hermes-profile-operations.service"
      "ghostship-hermes-profile-supervisor.service"
    ];
    environment = userServiceEnvironment;
    path = servicePath;
    serviceConfig = {
      Type = "oneshot";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      PassEnvironment = sharedHermesEnvKeys;
      ExecStart = "${managedUserToolingScript} bootstrap";
    };
  };

  systemd.services.ghostship-hermes-bootstrap = {
    description = "Bootstrap ghostship-hermes Hermes profiles";
    wantedBy = [ "multi-user.target" ];
    after = [
      "ghostship-storage.service"
      "ghostship-hermes-user-tooling.service"
    ];
    requires = [
      "ghostship-storage.service"
      "ghostship-hermes-user-tooling.service"
    ];
    environment = userServiceEnvironment;
    path = servicePath;
    serviceConfig = {
      Type = "oneshot";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      PassEnvironment = [
        "GHOSTSHIP_HERMES_SHARED_SKILLS_DIR"
        "GHOSTSHIP_HERMES_PROFILE_SKILLS_ROOT"
      ] ++ sharedHermesEnvKeys;
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
      "ghostship-hermes-user-tooling.service"
      "network-online.target"
    ];
    requires = [
      "ghostship-storage.service"
      "ghostship-hermes-bootstrap.service"
      "ghostship-hermes-user-tooling.service"
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
      "ghostship-hermes-user-tooling.service"
      "network-online.target"
    ];
    requires = [
      "ghostship-storage.service"
      "ghostship-hermes-bootstrap.service"
      "ghostship-hermes-user-tooling.service"
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

  systemd.services.nix-daemon = {
    wantedBy = lib.mkForce [ "multi-user.target" ];
    after = [ "ghostship-storage.service" ];
    requires = [ "ghostship-storage.service" ];
  };

  systemd.sockets.nix-daemon = {
    wantedBy = lib.mkForce [ "multi-user.target" ];
    after = [ "ghostship-storage.service" ];
    requires = [ "ghostship-storage.service" ];
  };

  systemd.services.ghostship-hermes-user-tooling-refresh = {
    description = "Refresh ghostship-hermes user tooling";
    after = [ "network-online.target" "nix-daemon.service" ];
    requires = [ "nix-daemon.service" ];
    wants = [ "network-online.target" ];
    environment = userServiceEnvironment;
    path = servicePath;
    serviceConfig = {
      Type = "oneshot";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      PassEnvironment = sharedHermesEnvKeys;
      ExecStart = "${managedUserToolingScript} refresh";
    };
  };

  systemd.timers.ghostship-hermes-user-tooling-refresh = {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "15min";
      OnUnitActiveSec = "1d";
      Persistent = true;
      Unit = "ghostship-hermes-user-tooling-refresh.service";
    };
  };

  system.extraDependencies = servicePath ++ [ fallbackCommandEnv ];

  environment.etc."ghostship-hermes-release".text = hermesRelease + "\n";
}
