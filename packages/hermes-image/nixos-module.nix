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
  wrappedHermesAgent,
  ...
}:
let
  managedProfiles = [
    "assistant"
    "operations"
    "supervisor"
  ];
  defaultProfile = "assistant";
  runtimeFlakeRefDefault = "github:caelx/ghostship-hermes";
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
      webhookEnabled = true;
      webhookPort = 8644;
      webhookSecretEnv = "WEBHOOK_ASSISTANT_SECRET";
    };
    operations = {
      personality = "operations";
      modelProvider = "openai-codex";
      modelDefault = "gpt-5.4";
      terminalCwd = "/workspace";
      discordBotTokenEnv = "DISCORD_OPERATIONS_BOT_TOKEN";
      discordAllowedUsersEnv = "DISCORD_OPERATIONS_ALLOWED_USERS";
      discordChannelEnv = "DISCORD_OPERATIONS_CHANNEL_ID";
      webhookEnabled = true;
      webhookPort = 8645;
      webhookSecretEnv = "WEBHOOK_OPERATIONS_SECRET";
    };
    supervisor = {
      personality = "supervisor";
      modelProvider = "openai-codex";
      modelDefault = "gpt-5.4";
      terminalCwd = "/workspace";
      discordBotTokenEnv = "DISCORD_SUPERVISOR_BOT_TOKEN";
      discordAllowedUsersEnv = "DISCORD_SUPERVISOR_ALLOWED_USERS";
      discordChannelEnv = "DISCORD_SUPERVISOR_CHANNEL_ID";
      webhookEnabled = true;
      webhookPort = 8646;
      webhookSecretEnv = "WEBHOOK_SUPERVISOR_SECRET";
    };
  };
  auxiliaryModelDefault = "gemini-3.1-flash-lite-preview";
  auxiliaryBaseUrl = "https://generativelanguage.googleapis.com/v1beta/openai/";
  auxiliaryApiKeyRef = "\${GOOGLE_AI_STUDIO_API_KEY}";
  certificateFile = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
  runtimeBin = "${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime";
  yamlFormat = pkgs.formats.yaml { };
  sharedProfileEnvKeys = [
    "GOOGLE_AI_STUDIO_API_KEY"
    "OPENROUTER_API_KEY"
    "OPENROUTER_BASE_URL"
    "OPENROUTER_HTTP_REFERER"
    "OPENROUTER_TITLE"
    "OPENAI_API_KEY"
    "OPENAI_BASE_URL"
    "OPENCODE_API_KEY"
    "OPENCODE_GO_API_KEY"
    "OPENCODE_BASE_URL"
    "GITHUB_TOKEN"
    "GH_TOKEN"
    "HASS_TOKEN"
    "HASS_URL"
    "BWS_ACCESS_TOKEN"
    "BWS_SERVER_URL"
    "BROWSERBASE_API_KEY"
    "BROWSERBASE_PROJECT_ID"
    "BROWSER_USE_API_KEY"
    "BROWSERBASE_PROXIES"
    "BROWSERBASE_ADVANCED_STEALTH"
    "BROWSERBASE_KEEP_ALIVE"
    "BROWSERBASE_SESSION_TIMEOUT"
    "BROWSER_INACTIVITY_TIMEOUT"
    "CAMOFOX_URL"
    "SEARXNG_URL"
    "SONARR_URL"
    "SONARR_API_KEY"
    "RADARR_URL"
    "RADARR_API_KEY"
    "PROWLARR_URL"
    "PROWLARR_API_KEY"
    "PLEX_URL"
    "PLEX_TOKEN"
    "ROMM_URL"
    "ROMM_TOKEN"
    "ROMM_USERNAME"
    "ROMM_PASSWORD"
    "NZBGET_URL"
    "NZBGET_USER"
    "NZBGET_PASS"
    "QBITTORRENT_URL"
    "QBITTORRENT_USER"
    "QBITTORRENT_PASS"
    "GRIMMORY_URL"
    "GRIMMORY_TOKEN"
    "GRIMMORY_USERNAME"
    "GRIMMORY_PASSWORD"
    "TAUTULLI_URL"
    "TAUTULLI_API_KEY"
    "BAZARR_URL"
    "BAZARR_API_KEY"
    "SYNOLOGY_URL"
    "SYNOLOGY_USER"
    "SYNOLOGY_PASS"
    "SYNOLOGY_VERIFY_SSL"
    "FLARESOLVERR_URL"
    "PYLOAD_URL"
    "PYLOAD_USER"
    "PYLOAD_PASS"
    "CLOAKBROWSER_URL"
    "CLOAKBROWSER_TOKEN"
    "PRICEBUDDY_URL"
    "PRICEBUDDY_TOKEN"
    "RSS_BRIDGE_URL"
    "CHANGEDETECTION_URL"
    "CHANGEDETECTION_API_KEY"
    "CHAPTARR_URL"
    "CHAPTARR_API_KEY"
    "CHAPTARR_API_PATH"
    "CHAPTARR_API_VERSION"
    "N8N_URL"
    "N8N_API_KEY"
    "N8N_PUBLIC_API_ENDPOINT"
    "N8N_PUBLIC_API_VERSION"
  ];
  profileBrowserCdpEnvKeys = [
    "BROWSER_ASSISTANT_CDP_URL"
    "BROWSER_OPERATIONS_CDP_URL"
    "BROWSER_SUPERVISOR_CDP_URL"
  ];
  discordEnvKeys = [
    "DISCORD_GENERAL_CHANNEL_ID"
    "DISCORD_ASSISTANT_BOT_TOKEN"
    "DISCORD_ASSISTANT_ALLOWED_USERS"
    "DISCORD_ASSISTANT_CHANNEL_ID"
    "DISCORD_OPERATIONS_BOT_TOKEN"
    "DISCORD_OPERATIONS_ALLOWED_USERS"
    "DISCORD_OPERATIONS_CHANNEL_ID"
    "DISCORD_SUPERVISOR_BOT_TOKEN"
    "DISCORD_SUPERVISOR_ALLOWED_USERS"
    "DISCORD_SUPERVISOR_CHANNEL_ID"
  ];
  toolingProjectRoot = "/home/hermes/.hermes/hermes-agent";
  managedUserProfile = "/home/hermes/.local/state/nix/profiles/ghostship-managed";
  managedUserPackages = [
    {
      name = "hermes-agent-wrapped";
      bootstrapRef = "${wrappedHermesAgent}";
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
    {
      name = "gh";
      ref = "nixpkgs#gh";
    }
    {
      name = "openssh";
      ref = "nixpkgs#openssh";
    }
  ];
  managedNpmPackages = [
    "@openai/codex"
    "opencode-ai"
  ];
  managedNpmBins = [
    "codex"
    "opencode"
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
        auto_thread = false;
        reactions = true;
      };
      display = {
        compact = true;
        streaming = true;
        tool_progress = "all";
        background_process_notifications = "result";
        bell_on_complete = false;
        show_reasoning = false;
        skin = "default";
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
    gh
    jq
    nix
    nodejs_22
    openssh
    ripgrep
  ];

  servicePath = systemPackages ++ toolingFallbackPackages ++ ghostshipUtilities ++ [ config.services.hermes-agent.package ];
  fallbackCommandEnv = pkgs.buildEnv {
    name = "ghostship-hermes-fallback-env";
    paths = servicePath;
  };
  hermesUserPathPrefix = "/home/hermes/.local/bin:${managedUserProfile}/bin:/home/hermes/.nix-profile/bin";
  hermesUserDefaultPath = "${hermesUserPathPrefix}:${fallbackCommandEnv}/bin";
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
      gatewayPidPath = "${profileRoot}/gateway.pid";
      soulPath = "${profileRoot}/SOUL.md";
      skillPath = "${profileRoot}/skills";
      serviceName = "ghostship-hermes-profile-${profile}";
      serviceDescription = "ghostship-hermes ${profile} gateway";
      serviceWorkingDirectory = profileDef.terminalCwd;
      gatewayScript = pkgs.writeShellScript "ghostship-hermes-profile-${profile}-gateway.sh" ''
        set -euo pipefail

        export PATH="${hermesUserPathPrefix}:$PATH"
        read -r _gateway_stat < "/proc/$$/stat"
        set -- $_gateway_stat
        _gateway_start_time="$22"
        cat > ${lib.escapeShellArg "${profileRoot}/gateway.pid"} <<EOF
{"pid": $$, "kind": "hermes-gateway", "argv": ["hermes", "gateway", "run", "--replace", "--profile", "${profile}"], "start_time": ''${_gateway_start_time}}
EOF

        exec hermes -p ${profile} gateway run --replace
      '';
      gatewayPreStartScript = pkgs.writeShellScript "ghostship-hermes-profile-${profile}-pre-start.sh" ''
        set -euo pipefail
        rm -f ${lib.escapeShellArg "${profileRoot}/gateway.pid"}
      '';
      gatewayPostStopScript = pkgs.writeShellScript "ghostship-hermes-profile-${profile}-post-stop.sh" ''
        set -euo pipefail
        rm -f ${lib.escapeShellArg "${profileRoot}/gateway.pid"}
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
      wantedBy = [ ];
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
        ExecStartPre = profileDef.gatewayPreStartScript;
        ExecStart = profileDef.gatewayScript;
        ExecStopPost = profileDef.gatewayPostStopScript;
        Restart = "always";
        RestartSec = "2s";
      };
    };
  bootstrapHermesScript = pkgs.writeShellScript "ghostship-hermes-bootstrap.sh" ''
    set -euo pipefail

    export PATH="${hermesUserPathPrefix}:$PATH"

    profiles_root="${managedProfileRoot}"
    mkdir -p "$profiles_root"

    if [ -f /etc/ghostship-hermes-release ]; then
      install -D -m 0644 /etc/ghostship-hermes-release /home/hermes/.ghostship-hermes-release
    fi

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

      config_target="${profileDefinitions.${profile}.configPath}"
      config_tmp="$(mktemp "''${config_target}.tmp.XXXXXX")"
      trap 'rm -f "$config_tmp"' EXIT
      install -D -m 0600 ${profileDefinitions.${profile}.configFile} "$config_tmp"
      if [ -f "$config_target" ] && cmp -s "$config_tmp" "$config_target"; then
        rm -f "$config_tmp"
      else
        mv -f "$config_tmp" "$config_target"
      fi
      trap - EXIT
      install -D -m 0600 /dev/null "${profileDefinitions.${profile}.profileRoot}/.managed"
    '') managedProfiles}

    install -D -m 0600 /dev/null "/home/hermes/.hermes/.managed"

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

    manage_seeded_soul() {
      source_path="$1"
      target_path="$2"
      marker_path="''${target_path}.ghostship-seeded-sha256"
      root_soul="/home/hermes/.hermes/SOUL.md"
      legacy_root_soul="/home/hermes/SOUL.md"

      [ -f "$source_path" ] || return 0

      source_hash="$(${pkgs.coreutils}/bin/sha256sum "$source_path" | ${pkgs.gawk}/bin/awk '{print $1}')"

      if [ ! -e "$target_path" ]; then
        install -D -m 0600 "$source_path" "$target_path"
        printf '%s\n' "$source_hash" >"$marker_path"
        chmod 0600 "$marker_path"
        return 0
      fi

      target_hash="$(${pkgs.coreutils}/bin/sha256sum "$target_path" | ${pkgs.gawk}/bin/awk '{print $1}')"

      if [ -f "$marker_path" ]; then
        marker_hash="$(tr -d '\n' <"$marker_path")"
        if [ "$target_hash" = "$marker_hash" ] && [ "$target_hash" != "$source_hash" ]; then
          install -D -m 0600 "$source_path" "$target_path"
          printf '%s\n' "$source_hash" >"$marker_path"
          chmod 0600 "$marker_path"
        fi
        return 0
      fi

      for generic_path in "$root_soul" "$legacy_root_soul"; do
        [ -f "$generic_path" ] || continue
        generic_hash="$(${pkgs.coreutils}/bin/sha256sum "$generic_path" | ${pkgs.gawk}/bin/awk '{print $1}')"
        if [ "$target_hash" = "$generic_hash" ]; then
          install -D -m 0600 "$source_path" "$target_path"
          printf '%s\n' "$source_hash" >"$marker_path"
          chmod 0600 "$marker_path"
          return 0
        fi
      done
    }

    reconcile_seed_skills() {
      shared_source="''${GHOSTSHIP_HERMES_SHARED_SKILLS_DIR:-${sharedSkillSourceDir}}"
      profile_root="''${GHOSTSHIP_HERMES_PROFILE_SKILLS_ROOT:-${profileSkillSourceRoot}}"

      copy_skill_tree_if_missing "$shared_source" "/home/hermes/.hermes/skills"

      profile_source="''${profile_root}/assistant/skills"
      copy_skill_tree_if_missing "$profile_source" "${profileDefinitions.assistant.skillPath}"
      manage_seeded_soul "''${profile_root}/assistant/SOUL.md" "${profileDefinitions.assistant.soulPath}"
      profile_source="''${profile_root}/operations/skills"
      copy_skill_tree_if_missing "$profile_source" "${profileDefinitions.operations.skillPath}"
      manage_seeded_soul "''${profile_root}/operations/SOUL.md" "${profileDefinitions.operations.soulPath}"
      profile_source="''${profile_root}/supervisor/skills"
      copy_skill_tree_if_missing "$profile_source" "${profileDefinitions.supervisor.skillPath}"
      manage_seeded_soul "''${profile_root}/supervisor/SOUL.md" "${profileDefinitions.supervisor.soulPath}"
    }

    write_profile_env() {
      target="$1"
      terminal_cwd="$2"
      bot_token_env="''${3:-}"
      allowed_users_env="''${4:-}"
      role_channel_env="''${5:-}"
      webhook_enabled="''${6:-}"
      webhook_port="''${7:-}"
      webhook_secret_env="''${8:-}"
      browser_cdp_env="''${9:-}"
      target_dir="$(dirname "$target")"
      tmp_target="$(mktemp "$target_dir/.env.tmp.XXXXXX")"
      general_channel="''${DISCORD_GENERAL_CHANNEL_ID:-}"
      cleanup_tmp() {
        rm -f "$tmp_target"
      }
      trap cleanup_tmp EXIT
      umask 077
      {
        printf 'TERMINAL_CWD=%s\n' "$terminal_cwd"
        for key in ${lib.escapeShellArgs sharedProfileEnvKeys}; do
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
        if [ -n "$browser_cdp_env" ]; then
          browser_cdp_url="''${!browser_cdp_env:-}"
          if [ -n "$browser_cdp_url" ]; then
            printf 'BROWSER_CDP_URL=%s\n' "$browser_cdp_url"
          fi
        fi
        if [ "$webhook_enabled" = "true" ]; then
          printf 'WEBHOOK_ENABLED=true\n'
        fi
        if [ -n "$webhook_port" ]; then
          printf 'WEBHOOK_PORT=%s\n' "$webhook_port"
        fi
        if [ -n "$webhook_secret_env" ]; then
          webhook_secret="''${!webhook_secret_env:-}"
          if [ -n "$webhook_secret" ]; then
            printf 'WEBHOOK_SECRET=%s\n' "$webhook_secret"
          fi
        fi
      } >"$tmp_target"
      chmod 0600 "$tmp_target"
      if [ -f "$target" ] && cmp -s "$tmp_target" "$target"; then
        rm -f "$tmp_target"
      else
        mv -f "$tmp_target" "$target"
      fi
      trap - EXIT
    }

    write_profile_env "${profileDefinitions.assistant.profileRoot}/.env" "${profileDefinitions.assistant.serviceWorkingDirectory}" "${profileDefinitions.assistant.discordBotTokenEnv}" "${profileDefinitions.assistant.discordAllowedUsersEnv}" "${profileDefinitions.assistant.discordChannelEnv}" "${if profileDefinitions.assistant.webhookEnabled then "true" else "false"}" "${toString profileDefinitions.assistant.webhookPort}" "${profileDefinitions.assistant.webhookSecretEnv}" "BROWSER_ASSISTANT_CDP_URL"
    write_profile_env "${profileDefinitions.operations.profileRoot}/.env" "${profileDefinitions.operations.serviceWorkingDirectory}" "${profileDefinitions.operations.discordBotTokenEnv}" "${profileDefinitions.operations.discordAllowedUsersEnv}" "${profileDefinitions.operations.discordChannelEnv}" "${if profileDefinitions.operations.webhookEnabled then "true" else "false"}" "${toString profileDefinitions.operations.webhookPort}" "${profileDefinitions.operations.webhookSecretEnv}" "BROWSER_OPERATIONS_CDP_URL"
    write_profile_env "${profileDefinitions.supervisor.profileRoot}/.env" "${profileDefinitions.supervisor.serviceWorkingDirectory}" "${profileDefinitions.supervisor.discordBotTokenEnv}" "${profileDefinitions.supervisor.discordAllowedUsersEnv}" "${profileDefinitions.supervisor.discordChannelEnv}" "${if profileDefinitions.supervisor.webhookEnabled then "true" else "false"}" "${toString profileDefinitions.supervisor.webhookPort}" "${profileDefinitions.supervisor.webhookSecretEnv}" "BROWSER_SUPERVISOR_CDP_URL"
    reconcile_seed_skills

    rm -f /home/hermes/.hermes/active_profile

    hermes -p ${lib.escapeShellArg defaultProfile} config path >/dev/null 2>&1 || true
    hermes -p ${lib.escapeShellArg defaultProfile} config env-path >/dev/null 2>&1 || true
  '';

  managedUserToolingScript = pkgs.writeShellScript "ghostship-hermes-user-tooling.sh" ''
    set -euo pipefail

    mode="''${1:-bootstrap}"
    export HOME=/home/hermes
    export HERMES_HOME=/home/hermes/.hermes
    export GHOSTSHIP_HERMES_PROJECT_ROOT="''${GHOSTSHIP_HERMES_PROJECT_ROOT:-${toolingProjectRoot}}"
    export GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF="''${GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF:-${runtimeFlakeRefDefault}}"
    export GHOSTSHIP_HERMES_MANAGED_PROFILE="''${GHOSTSHIP_HERMES_MANAGED_PROFILE:-${managedUserProfile}}"
    export PATH="${hermesUserPathPrefix}:${lib.makeBinPath servicePath}:$PATH"
    export npm_config_update_notifier=false
    export npm_config_fund=false
    export npm_config_cache="$HOME/.cache/npm"
    export GHOSTSHIP_TOOLING_MODE="$mode"

    mkdir -p "$GHOSTSHIP_HERMES_PROJECT_ROOT" "$HOME/.local/bin" "$npm_config_cache" "$(dirname "$GHOSTSHIP_HERMES_MANAGED_PROFILE")"

    python3 - <<'PY2'
import json
import os
import subprocess
from pathlib import Path

mode = os.environ.get("GHOSTSHIP_TOOLING_MODE", "bootstrap")
runtime_flake_ref = os.environ.get("GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF", "github:caelx/ghostship-hermes")
managed_profile = os.environ["GHOSTSHIP_HERMES_MANAGED_PROFILE"]
project_root = Path(os.environ["GHOSTSHIP_HERMES_PROJECT_ROOT"])
home = Path(os.environ["HOME"])
specs = json.loads(r"""${builtins.toJSON managedUserPackages}""")
managed_npm_packages = json.loads(r"""${builtins.toJSON managedNpmPackages}""")
managed_npm_bins = json.loads(r"""${builtins.toJSON managedNpmBins}""")
result = subprocess.run(
    ["nix", "profile", "list", "--profile", managed_profile, "--json"],
    check=False,
    capture_output=True,
    text=True,
)
if result.returncode == 0:
    elements = json.loads(result.stdout).get("elements", {})
else:
    elements = {}

for item in specs:
    name = item["name"]
    for entry_name in sorted(
        key for key in elements if key == name or key.startswith(f"{name}-")
    ):
        subprocess.run(
            ["nix", "profile", "remove", "--profile", managed_profile, entry_name],
            check=True,
        )
    if mode == "refresh" and name == "hermes-agent-wrapped":
        ref = f"{runtime_flake_ref}#hermes-agent-wrapped"
    else:
        ref = item.get("bootstrapRef") or item["ref"]
    subprocess.run(["nix", "profile", "add", "--profile", managed_profile, ref], check=True)

package_json = project_root / "package.json"
package_json.write_text(
    json.dumps(
        {
            "name": "ghostship-hermes-runtime-tools",
            "private": True,
            "devDependencies": {pkg: "latest" for pkg in managed_npm_packages},
        },
        indent=2,
    )
    + "\n"
)
subprocess.run(["npm", "install", "--silent"], cwd=project_root, check=True)

local_bin = home / ".local" / "bin"
project_bin_root = project_root / "node_modules" / ".bin"
agent_browser_link = local_bin / "agent-browser"
for entry in local_bin.iterdir():
    if not entry.is_symlink():
        continue
    try:
        target = entry.resolve(strict=False)
    except OSError:
        continue
    if target.parent == project_bin_root and entry.name not in managed_npm_bins:
        entry.unlink(missing_ok=True)

for bin_name in managed_npm_bins:
    target = project_bin_root / bin_name
    link = local_bin / bin_name
    if target.exists():
        link.unlink(missing_ok=True)
        link.symlink_to(target)

if agent_browser_link.is_symlink():
    try:
        target = agent_browser_link.resolve(strict=False)
    except OSError:
        target = None
    if target is None or project_root in target.parents:
        agent_browser_link.unlink(missing_ok=True)
PY2
  '';

  serviceEnvironment = {
    HERMES_HOME = "/home/hermes/.hermes";
    GHOSTSHIP_HERMES_PROJECT_ROOT = toolingProjectRoot;
    GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF = runtimeFlakeRefDefault;
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
    GHOSTSHIP_HERMES_MANAGED_PROFILE = managedUserProfile;
  };

in
{
  # Hermes v2026.4.8 orders its setup activation after a `setupSecrets` phase
  # that is not defined in this image module stack. Provide a no-op compatibility
  # hook so the upstream module can evaluate without requiring an external secret
  # management module.
  system.activationScripts.setupSecrets = lib.mkDefault (lib.stringAfter [ "users" ] "");

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
  environment.etc."profile.d/ghostship-hermes-user-path.sh".text = ''
    if [ "$(id -u)" = "3000" ]; then
      export HOME=/home/hermes
      export PATH="${hermesUserDefaultPath}:$PATH"
      export HERMES_HOME=/home/hermes/.hermes
      export GHOSTSHIP_HERMES_PROJECT_ROOT=${toolingProjectRoot}
      export TERMINAL_CWD=/workspace
      export SSL_CERT_FILE=${certificateFile}
      export NIX_SSL_CERT_FILE=${certificateFile}
    fi
  '';
  environment.shellInit = ''
    if [ "$(id -u)" = "3000" ]; then
      export HOME=/home/hermes
    fi
    export PATH="${hermesUserDefaultPath}:$PATH"
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
    package = wrappedHermesAgent;
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
      PassEnvironment = sharedProfileEnvKeys ++ profileBrowserCdpEnvKeys;
      ExecStart = "${managedUserToolingScript} bootstrap";
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
        "GHOSTSHIP_HERMES_SHARED_SKILLS_DIR"
        "GHOSTSHIP_HERMES_PROFILE_SKILLS_ROOT"
      ] ++ sharedProfileEnvKeys ++ profileBrowserCdpEnvKeys ++ discordEnvKeys;
      ExecStart = bootstrapHermesScript;
    };
  };


  systemd.services.ghostship-hermes-startup = {
    description = "Start ghostship-hermes runtime services";
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
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = pkgs.writeShellScript "ghostship-hermes-startup.sh" ''
        set -euo pipefail
        ${pkgs.systemd}/bin/systemctl start           ghostship-dashboard-controller.service           ghostship-hermes-router.service           ghostship-hermes-profile-assistant.service           ghostship-hermes-profile-operations.service           ghostship-hermes-profile-supervisor.service
      '';
    };
  };

  systemd.services.ghostship-hermes-router = {
    description = "ghostship-hermes model router";
    wantedBy = [ ];
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
    wantedBy = [ ];
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


  systemd.services.ghostship-hermes-profile-assistant-restart = {
    description = "Restart ghostship-hermes assistant gateway after profile changes";
    serviceConfig = {
      Type = "oneshot";
      ExecStart = pkgs.writeShellScript "ghostship-hermes-profile-assistant-restart.sh" ''
        exec ${pkgs.systemd}/bin/systemctl try-restart ghostship-hermes-profile-assistant.service
      '';
    };
  };

  systemd.services.ghostship-hermes-profile-operations-restart = {
    description = "Restart ghostship-hermes operations gateway after profile changes";
    serviceConfig = {
      Type = "oneshot";
      ExecStart = pkgs.writeShellScript "ghostship-hermes-profile-operations-restart.sh" ''
        exec ${pkgs.systemd}/bin/systemctl try-restart ghostship-hermes-profile-operations.service
      '';
    };
  };

  systemd.services.ghostship-hermes-profile-supervisor-restart = {
    description = "Restart ghostship-hermes supervisor gateway after profile changes";
    serviceConfig = {
      Type = "oneshot";
      ExecStart = pkgs.writeShellScript "ghostship-hermes-profile-supervisor-restart.sh" ''
        exec ${pkgs.systemd}/bin/systemctl try-restart ghostship-hermes-profile-supervisor.service
      '';
    };
  };

  systemd.paths.ghostship-hermes-profile-assistant-restart = {
    wantedBy = [ "multi-user.target" ];
    pathConfig = {
      PathChanged = [
        "${profileDefinitions.assistant.configPath}"
        "${profileDefinitions.assistant.profileRoot}/.env"
      ];
      Unit = "ghostship-hermes-profile-assistant-restart.service";
    };
  };

  systemd.paths.ghostship-hermes-profile-operations-restart = {
    wantedBy = [ "multi-user.target" ];
    pathConfig = {
      PathChanged = [
        "${profileDefinitions.operations.configPath}"
        "${profileDefinitions.operations.profileRoot}/.env"
      ];
      Unit = "ghostship-hermes-profile-operations-restart.service";
    };
  };

  systemd.paths.ghostship-hermes-profile-supervisor-restart = {
    wantedBy = [ "multi-user.target" ];
    pathConfig = {
      PathChanged = [
        "${profileDefinitions.supervisor.configPath}"
        "${profileDefinitions.supervisor.profileRoot}/.env"
      ];
      Unit = "ghostship-hermes-profile-supervisor-restart.service";
    };
  };

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
      PassEnvironment = sharedProfileEnvKeys ++ profileBrowserCdpEnvKeys;
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
