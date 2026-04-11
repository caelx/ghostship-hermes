{
  config,
  lib,
  modulesPath,
  pkgs,
  ghostshipHermesRouter ? null,
  ghostshipHermesRuntime ? null,
  ghostshipUtilities ? [ ],
  hermesDashboard ? null,
  hermesRelease,
  includeRepoContent ? false,
  includeManagedRuntime ? false,
  hermesAgentPackage,
  sharedGhostshipDependencyPackages ? [ ],
  ...
}:
let
  managedGatewayServiceName = "hermes-gateway";
  managedUserRuntimeDir = "/run/user/3000";
  runtimeFlakeRefDefault = "github:caelx/ghostship-hermes";
  rootTerminalCwd = "/workspace";
  managedHermesHome = "/home/hermes/.hermes";
  managedSkillsSourceDir = "/home/hermes/seeds/skills";
  managedSoulSourcePath = "/home/hermes/seeds/SOUL.md";
  managedEnvPath = "${managedHermesHome}/.env";
  managedGatewayPidPath = "${managedHermesHome}/gateway.pid";
  managedSoulPath = "${managedHermesHome}/SOUL.md";
  managedSkillsPath = "${managedHermesHome}/skills";
  managedAuthPath = "${managedHermesHome}/auth.json";
  unmanagedDefaultSoulHash = "2765a846e1bb371d78d3b93b403dfb0f8d1ba1a9895edb5f608367abfe81194d";
  managedWebhookPort = 8644;
  managedLayoutVersion = "single-agent-v1";
  auxiliaryModelDefault = "gemini-3.1-flash-lite-preview";
  auxiliaryBaseUrl = "https://generativelanguage.googleapis.com/v1beta/openai/";
  auxiliaryApiKeyRef = "\${GOOGLE_AI_STUDIO_API_KEY}";
  certificateFile = "${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt";
  repoOverlayBinDir = "/opt/ghostship-overlay/bin";
  routerCommand = if includeRepoContent then "${ghostshipHermesRouter}/bin/ghostship-hermes-router" else "${repoOverlayBinDir}/ghostship-hermes-router";
  runtimeCommand = if includeRepoContent then "${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime" else "${repoOverlayBinDir}/ghostship-hermes-runtime";
  dashboardCommand = if includeRepoContent then "${hermesDashboard}/bin/hermes-dashboard" else "${repoOverlayBinDir}/hermes-dashboard";
  yamlFormat = pkgs.formats.yaml { };
  managedRuntimeEnvKeys = [
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
    "N8N_URL"
    "N8N_API_KEY"
  ];
  managedDiscordEnvKeys = [
    "DISCORD_BOT_TOKEN"
    "DISCORD_ALLOWED_USERS"
    "DISCORD_FREE_RESPONSE_CHANNELS"
    "DISCORD_HOME_CHANNEL"
  ];
  managedBrowserEnvKeys = [
    "BROWSER_CDP_URL"
    "HERMES_HUD_PROJECTS_DIR"
    "GHOSTSHIP_HUD_DEFAULT_PROFILE_NAME"
  ];
  managedWebhookEnvKeys = [
    "WEBHOOK_SECRET"
  ];
  toolingProjectRoot = "/home/hermes/.hermes/hermes-agent";
  managedUserProfile = "/home/hermes/.local/state/nix/profiles/ghostship-managed";
  managedPythonWithPip = pkgs.python3.withPackages (ps: [ ps.pip ]);
  managedUserPackages = [
    {
      name = "hermes-agent-wrapped";
      bootstrapRef = "${hermesAgentPackage}";
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
      name = "fd";
      ref = "nixpkgs#fd";
    }
    {
      name = "python3";
      bootstrapRef = "${managedPythonWithPip}";
      priority = 4;
    }
    {
      name = "uv";
      ref = "nixpkgs#uv";
    }
    {
      name = "yq-go";
      ref = "nixpkgs#yq-go";
    }
    {
      name = "tmux";
      ref = "nixpkgs#tmux";
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
  managedAgentConfig =
    let
      directGemini = {
        model = auxiliaryModelDefault;
        base_url = auxiliaryBaseUrl;
        api_key = auxiliaryApiKeyRef;
      };
    in
    {
      display.personality = "assistant";
      model = {
        provider = "opencode-go";
        default = "minimax-m2.7";
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
        provider = "custom";
        model = "agentic";
        base_url = "http://127.0.0.1:8788/v1";
        api_key_env = "OPENAI_API_KEY";
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
      auxiliary = {
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
        cwd = rootTerminalCwd;
        timeout = 180;
      };
    };
  sharedDependencyPackages = with pkgs; [
    bashInteractive
    cacert
    coreutils
    curl
    diffutils
    findutils
    git
    gh
    gnugrep
    gnused
    jq
    nix
    nodejs_22
    openssh
    procps
    ripgrep
    tirith
    ttyd
    util-linux
  ] ++ sharedGhostshipDependencyPackages;

  repoCommandPackages = lib.optionals includeRepoContent (
    [
      ghostshipHermesRouter
      ghostshipHermesRuntime
      hermesDashboard
    ]
    ++ ghostshipUtilities
  );

  systemPackages = sharedDependencyPackages ++ repoCommandPackages;
  servicePath = sharedDependencyPackages ++ [ config.services.hermes-agent.package ] ++ repoCommandPackages;
  fallbackCommandPath = lib.makeBinPath servicePath;
  hermesUserPathPrefix = "/home/hermes/.local/bin:${managedUserProfile}/bin:/home/hermes/.nix-profile/bin";
  overlayPathSegment = lib.optionalString (!includeRepoContent) "${repoOverlayBinDir}:";
  hermesUserDefaultPath = "${hermesUserPathPrefix}:${overlayPathSegment}${fallbackCommandPath}";
  storagePreparationScript = pkgs.writeShellScript "ghostship-hermes-prepare-storage" ''
    set -euo pipefail

    export HERMES_USER="''${HERMES_USER:-hermes}"
    export HERMES_UID="''${HERMES_UID:-3000}"
    export HERMES_GID="''${HERMES_GID:-3000}"
    export HOME="''${HOME:-/home/hermes}"
    export HERMES_HOME="''${HERMES_HOME:-/home/hermes/.hermes}"
    export GHOSTSHIP_WORKSPACE_ROOT="''${GHOSTSHIP_WORKSPACE_ROOT:-/workspace}"
    export GHOSTSHIP_DASHBOARD_STATE_DIR="''${GHOSTSHIP_DASHBOARD_STATE_DIR:-/home/hermes/.local/state/ghostship-hermes/dashboard}"
    export GHOSTSHIP_ROUTER_STATE_DIR="''${GHOSTSHIP_ROUTER_STATE_DIR:-/home/hermes/.local/state/ghostship-hermes/router}"
    export XDG_CONFIG_HOME="''${XDG_CONFIG_HOME:-$HOME/.config}"
    export XDG_DATA_HOME="''${XDG_DATA_HOME:-$HOME/.local/share}"
    export XDG_STATE_HOME="''${XDG_STATE_HOME:-$HOME/.local/state}"
    export XDG_CACHE_HOME="''${XDG_CACHE_HOME:-$HOME/.cache}"
    export GHOSTSHIP_AGENT_TOOLS_PREFIX="''${GHOSTSHIP_AGENT_TOOLS_PREFIX:-$HOME/.local/share/ghostship-agent-tools/npm}"

    ensure_dir() {
      local path="$1"
      local mode="$2"
      install -d -m "$mode" "$path"
      chown "$HERMES_UID:$HERMES_GID" "$path"
    }

    prepare_nix_profile_state() {
      local profile_root gc_root profile_link

      profile_root="/nix/var/nix/profiles/per-user/$HERMES_USER"
      gc_root="/nix/var/nix/gcroots/per-user/$HERMES_USER"
      profile_link="$HOME/.nix-profile"

      install -d -m 0755 /nix/var/nix/daemon-socket >/dev/null 2>&1 || true
      install -d -m 0755 /nix/var/nix/profiles/per-user >/dev/null 2>&1 || true
      install -d -m 0755 "$profile_root" "$gc_root" >/dev/null 2>&1 || true
      chown -R "$HERMES_UID:$HERMES_GID" "$profile_root" "$gc_root" >/dev/null 2>&1 || true

      ln -sfn "$profile_root/profile" "$profile_link"
      chown -h "$HERMES_UID:$HERMES_GID" "$profile_link" >/dev/null 2>&1 || true
    }

    install -d -m 1777 /tmp
    ensure_dir "$GHOSTSHIP_WORKSPACE_ROOT" 0750
    ensure_dir "$HOME" 0750
    ensure_dir "$HERMES_HOME" 0750
    ensure_dir "$GHOSTSHIP_DASHBOARD_STATE_DIR" 0750
    ensure_dir "$GHOSTSHIP_ROUTER_STATE_DIR" 0750

    prepare_nix_profile_state
    ensure_dir "$XDG_CONFIG_HOME" 0750
    ensure_dir "$XDG_DATA_HOME" 0750
    ensure_dir "$XDG_STATE_HOME" 0750
    ensure_dir "$XDG_CACHE_HOME" 0750
    ensure_dir "$HOME/.local/bin" 0750
    ensure_dir "$GHOSTSHIP_AGENT_TOOLS_PREFIX" 0750
    ensure_dir "$XDG_CACHE_HOME/npm" 0750
    ensure_dir "$HOME/.config/systemd/user" 0750
    ensure_dir "$HOME/.ssh" 0700
    ensure_dir "$HOME/.gnupg" 0700
    ensure_dir "$HOME/.pki" 0700
    chown -R "$HERMES_UID:$HERMES_GID" "$HOME" "$GHOSTSHIP_WORKSPACE_ROOT" >/dev/null 2>&1 || true
    chmod 0750 "$HOME" "$GHOSTSHIP_WORKSPACE_ROOT" "$HERMES_HOME"
  '';

  managedGatewayScript = pkgs.writeShellScript "ghostship-hermes-gateway.sh" ''
    set -euo pipefail

    export PATH="${hermesUserPathPrefix}:$PATH"
    read -r _gateway_stat < "/proc/$$/stat"
    set -- $_gateway_stat
    _gateway_start_time="$22"
    cat > ${lib.escapeShellArg managedGatewayPidPath} <<EOF
{"pid": $$, "kind": "hermes-gateway", "argv": ["hermes", "gateway", "run", "--replace"], "start_time": ''${_gateway_start_time}}
EOF

    exec hermes gateway run --replace
  '';
  managedGatewayPreStartScript = pkgs.writeShellScript "ghostship-hermes-gateway-pre-start.sh" ''
    set -euo pipefail
    rm -f ${lib.escapeShellArg managedGatewayPidPath}

    config_path=${lib.escapeShellArg (managedHermesHome + "/config.yaml")}
    env_path=${lib.escapeShellArg managedEnvPath}
    for _ in $(${pkgs.coreutils}/bin/seq 1 60); do
      if [ -f "$config_path" ] && [ -f "$env_path" ] && ${pkgs.curl}/bin/curl -fsS http://127.0.0.1:8788/readyz >/dev/null 2>&1; then
        exit 0
      fi
      ${pkgs.coreutils}/bin/sleep 1
    done

    echo "managed gateway prerequisites did not become ready" >&2
    exit 1
  '';
  managedGatewayPostStopScript = pkgs.writeShellScript "ghostship-hermes-gateway-post-stop.sh" ''
    set -euo pipefail
    rm -f ${lib.escapeShellArg managedGatewayPidPath}
  '';
  bootstrapHermesScript = pkgs.writeShellScript "ghostship-hermes-bootstrap.sh" ''
    set -euo pipefail

    export PATH="${hermesUserPathPrefix}:$PATH"
    managed_home="${managedHermesHome}"
    managed_layout_marker="$managed_home/.ghostship-managed-layout"

    if [ -f /etc/ghostship-hermes-release ]; then
      install -D -m 0644 /etc/ghostship-hermes-release /home/hermes/.ghostship-hermes-release
    fi

    reset_legacy_profile_state() {
      if [ ! -d "$managed_home/profiles" ] && [ ! -f "$managed_home/active_profile" ]; then
        return 0
      fi

      marker_value=""
      if [ -f "$managed_layout_marker" ]; then
        marker_value="$(tr -d '\n' <"$managed_layout_marker")"
      fi
      if [ "$marker_value" = "${managedLayoutVersion}" ]; then
        return 0
      fi

      rm -rf \
        "$managed_home/profiles" \
        "${managedSkillsPath}"
      rm -f \
        "$managed_home/active_profile" \
        "${managedEnvPath}" \
        "${managedGatewayPidPath}" \
        "${managedSoulPath}" \
        "${managedSoulPath}.ghostship-seeded-sha256" \
        "${managedAuthPath}" \
        "$managed_home/.managed" \
        "$managed_home/memory_store.db"
    }

    mkdir -p "$managed_home"
    reset_legacy_profile_state
    printf '%s\n' "${managedLayoutVersion}" >"$managed_layout_marker"
    chmod 0600 "$managed_layout_marker"
    install -D -m 0600 /dev/null "$managed_home/.managed"

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
          chmod -R u+rwX "$target_root/$skill_name"
        fi
      done < <(find "$source_root" -mindepth 1 -maxdepth 1 -type d | sort)
    }

    materialize_and_normalize_skills() {
      target_root="$1"

      mkdir -p "$target_root"
      hermes skills list >/dev/null 2>&1 || true
      [ -d "$target_root" ] || return 0
      chmod -R u+rwX "$target_root"
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

      if [ "$target_hash" = "${unmanagedDefaultSoulHash}" ]; then
        install -D -m 0600 "$source_path" "$target_path"
        printf '%s\n' "$source_hash" >"$marker_path"
        chmod 0600 "$marker_path"
        return 0
      fi

      if [ "$target_hash" = "$source_hash" ]; then
        printf '%s\n' "$source_hash" >"$marker_path"
        chmod 0600 "$marker_path"
      fi
    }

    reconcile_seed_content() {
      skill_source="''${GHOSTSHIP_HERMES_SKILLS_DIR:-${managedSkillsSourceDir}}"
      soul_source="''${GHOSTSHIP_HERMES_SOUL_PATH:-${managedSoulSourcePath}}"

      copy_skill_tree_if_missing "$skill_source" "${managedSkillsPath}"
      materialize_and_normalize_skills "${managedSkillsPath}"
      manage_seeded_soul "$soul_source" "${managedSoulPath}"
    }

    reconcile_managed_config() {
      config_path="${managedHermesHome}/config.yaml"
      [ -f "$config_path" ] || return 0

      tmp_path="$(mktemp "$managed_home/config.yaml.tmp.XXXXXX")"
      ${pkgs.gawk}/bin/awk '
        BEGIN { in_model = 0 }
        /^model:[[:space:]]*$/ {
          in_model = 1
          print
          next
        }
        in_model && /^[^[:space:]]/ {
          in_model = 0
        }
        in_model && $0 == "  base_url: http://127.0.0.1:8788/v1" {
          next
        }
        { print }
      ' "$config_path" >"$tmp_path"
      chmod 0600 "$tmp_path"
      if ! cmp -s "$tmp_path" "$config_path"; then
        mv -f "$tmp_path" "$config_path"
      else
        rm -f "$tmp_path"
      fi
    }

    reconcile_gateway_user_unit_path() {
      managed_unit="/etc/systemd/user/${managedGatewayServiceName}.service"
      user_unit_dir="$HOME/.config/systemd/user"
      user_unit="$user_unit_dir/${managedGatewayServiceName}.service"

      [ -e "$managed_unit" ] || return 0
      mkdir -p "$user_unit_dir"
      ln -sfn "$managed_unit" "$user_unit"
    }

    write_managed_env() {
      target="$1"
      target_dir="$(dirname "$target")"
      tmp_target="$(mktemp "$target_dir/.env.tmp.XXXXXX")"
      cleanup_tmp() {
        rm -f "$tmp_target"
      }
      trap cleanup_tmp EXIT
      umask 077
      {
        printf 'TERMINAL_CWD=%s\n' "${rootTerminalCwd}"
        for key in ${lib.escapeShellArgs managedRuntimeEnvKeys}; do
          value="''${!key:-}"
          if [ -n "$value" ]; then
            printf '%s=%s\n' "$key" "$value"
          fi
        done
        if [ -z "''${OPENCODE_API_KEY:-}" ] && [ -n "''${OPENCODE_GO_API_KEY:-}" ]; then
          printf 'OPENCODE_API_KEY=%s\n' "''${OPENCODE_GO_API_KEY}"
        fi
        for key in ${lib.escapeShellArgs (managedDiscordEnvKeys ++ managedBrowserEnvKeys ++ managedWebhookEnvKeys)}; do
          value="''${!key:-}"
          if [ -n "$value" ]; then
            printf '%s=%s\n' "$key" "$value"
          fi
        done
        printf 'WEBHOOK_ENABLED=true\n'
        printf 'WEBHOOK_PORT=%s\n' "${toString managedWebhookPort}"
      } >"$tmp_target"
      chmod 0600 "$tmp_target"
      if [ -f "$target" ] && cmp -s "$tmp_target" "$target"; then
        rm -f "$tmp_target"
      else
        mv -f "$tmp_target" "$target"
      fi
      trap - EXIT
    }

    write_managed_env "${managedEnvPath}"
    reconcile_seed_content

    rm -rf "$managed_home/profiles"
    rm -f "$managed_home/active_profile"

    hermes config path >/dev/null 2>&1 || true
    hermes config env-path >/dev/null 2>&1 || true
    reconcile_managed_config
    reconcile_gateway_user_unit_path
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
    command = ["nix", "profile", "add", "--profile", managed_profile]
    priority = item.get("priority")
    if priority is not None:
        command.extend(["--priority", str(priority)])
    command.append(ref)
    subprocess.run(command, check=True)

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
    TERMINAL_CWD = "/workspace";
    SSL_CERT_FILE = certificateFile;
    NIX_SSL_CERT_FILE = certificateFile;
  } // lib.optionalAttrs includeManagedRuntime {
    GHOSTSHIP_HERMES_PROJECT_ROOT = toolingProjectRoot;
    GHOSTSHIP_HERMES_RUNTIME_FLAKE_REF = runtimeFlakeRefDefault;
    GHOSTSHIP_TERMINAL_CWD = "/workspace";
    GHOSTSHIP_DASHBOARD_HOST = "0.0.0.0";
    GHOSTSHIP_DASHBOARD_PORT = "7681";
    GHOSTSHIP_TTYD_PORT_BASE = "7682";
    GHOSTSHIP_HERMES_GATEWAY_SERVICE = "${managedGatewayServiceName}.service";
    HERMES_HUD_PROJECTS_DIR = "/workspace";
    GHOSTSHIP_HUD_DEFAULT_PROFILE_NAME = "Managed Agent";
    GHOSTSHIP_ROUTER_HOST = "127.0.0.1";
    GHOSTSHIP_ROUTER_PORT = "8788";
    API_SERVER_HOST = "127.0.0.1";
    API_SERVER_PORT = "8788";
    GHOSTSHIP_ROUTER_STATE_DIR = "/home/hermes/.local/state/ghostship-hermes/router";
    GHOSTSHIP_ROUTER_DB_PATH = "/home/hermes/.local/state/ghostship-hermes/router/router.db";
    GHOSTSHIP_ROUTER_REFRESH_INTERVAL = "300";
    GHOSTSHIP_ROUTER_DISABLED_MODELS = "openrouter/free";
  };

  userServiceEnvironment = serviceEnvironment // {
    HOME = "/home/hermes";
    XDG_RUNTIME_DIR = managedUserRuntimeDir;
    DBUS_SESSION_BUS_ADDRESS = "unix:path=${managedUserRuntimeDir}/bus";
  } // lib.optionalAttrs includeManagedRuntime {
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
      export XDG_RUNTIME_DIR=${managedUserRuntimeDir}
      if [ -S ${managedUserRuntimeDir}/bus ]; then
        export DBUS_SESSION_BUS_ADDRESS=unix:path=${managedUserRuntimeDir}/bus
      fi
      ${lib.optionalString includeManagedRuntime "export GHOSTSHIP_HERMES_PROJECT_ROOT=${toolingProjectRoot}"}
      export TERMINAL_CWD=/workspace
      export SSL_CERT_FILE=${certificateFile}
      export NIX_SSL_CERT_FILE=${certificateFile}
    fi
  '';
  environment.shellInit = ''
    if [ "$(id -u)" = "3000" ]; then
      export HOME=/home/hermes
      export XDG_RUNTIME_DIR=${managedUserRuntimeDir}
      if [ -S ${managedUserRuntimeDir}/bus ]; then
        export DBUS_SESSION_BUS_ADDRESS=unix:path=${managedUserRuntimeDir}/bus
      fi
    fi
    export PATH="${hermesUserDefaultPath}:$PATH"
    export HERMES_HOME=/home/hermes/.hermes
    ${lib.optionalString includeManagedRuntime "export GHOSTSHIP_HERMES_PROJECT_ROOT=${toolingProjectRoot}"}
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
    package = hermesAgentPackage;
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
    settings = { } // managedAgentConfig;
    extraPackages = [ pkgs.nix ] ++ lib.optionals includeRepoContent ghostshipUtilities;
  };

  systemd.services.ghostship-storage = {
    description = "Prepare ghostship-hermes persisted storage";
    wantedBy = [ "multi-user.target" ];
    before = [
      "hermes-agent.service"
    ] ++ lib.optionals includeManagedRuntime [
      "ghostship-hermes-hudui.service"
      "ghostship-hermes-router.service"
      "${managedGatewayServiceName}.service"
    ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      ExecStart = "${storagePreparationScript}";
    };
  };

  systemd.services.hermes-agent = {
    wantedBy = lib.mkForce [ ];
    after = [ "ghostship-storage.service" ];
    requires = [ "ghostship-storage.service" ];
    environment = lib.mkForce (
      userServiceEnvironment
      // lib.optionalAttrs includeManagedRuntime {
        HERMES_MANAGED = "true";
      }
    );
    serviceConfig = {
      User = lib.mkForce "hermes";
      Group = lib.mkForce "hermes";
      WorkingDirectory = lib.mkForce "/home/hermes";
    };
  };
  systemd.services.ghostship-hermes-user-tooling = lib.mkIf includeManagedRuntime {
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
      "ghostship-hermes-hudui.service"
      "${managedGatewayServiceName}.service"
    ];
    environment = userServiceEnvironment;
    path = servicePath;
    serviceConfig = {
      Type = "oneshot";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      PassEnvironment = managedRuntimeEnvKeys ++ managedBrowserEnvKeys;
      ExecStart = "${managedUserToolingScript} bootstrap";
    };
  };

  systemd.services.ghostship-hermes-bootstrap = lib.mkIf includeManagedRuntime {
    description = "Bootstrap ghostship-hermes managed runtime";
    wantedBy = [ "multi-user.target" ];
    after = [ "ghostship-storage.service" ];
    requires = [ "ghostship-storage.service" ];
    environment = userServiceEnvironment;
    path = servicePath;
    serviceConfig = {
      Type = "oneshot";
      User = "hermes";
      Group = "hermes";
      WorkingDirectory = "/home/hermes";
      PassEnvironment = [
        "GHOSTSHIP_HERMES_SKILLS_DIR"
        "GHOSTSHIP_HERMES_SOUL_PATH"
      ] ++ managedRuntimeEnvKeys ++ managedDiscordEnvKeys ++ managedBrowserEnvKeys ++ managedWebhookEnvKeys;
      ExecStart = bootstrapHermesScript;
    };
  };

  systemd.services.ghostship-hermes-startup = lib.mkIf includeManagedRuntime {
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
        ${pkgs.systemd}/bin/systemctl start \
          user@3000.service \
          ghostship-hermes-hudui.service \
          ghostship-hermes-router.service

        for _ in $(${pkgs.coreutils}/bin/seq 1 30); do
          if [ -S ${managedUserRuntimeDir}/bus ]; then
            break
          fi
          ${pkgs.coreutils}/bin/sleep 1
        done

        exec ${pkgs.util-linux}/bin/runuser -u hermes -- env \
          XDG_RUNTIME_DIR=${managedUserRuntimeDir} \
          DBUS_SESSION_BUS_ADDRESS=unix:path=${managedUserRuntimeDir}/bus \
          ${pkgs.systemd}/bin/systemctl --user start \
            ghostship-hermes-gateway-restart.path \
            ${managedGatewayServiceName}.service
      '';
    };
  };

  systemd.services.ghostship-hermes-router = lib.mkIf includeManagedRuntime {
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
      ExecStart = routerCommand;
      Restart = "always";
      RestartSec = "2s";
      LimitNOFILE = 65536;
    };
  };

  systemd.services.ghostship-hermes-hudui = lib.mkIf includeManagedRuntime {
    description = "ghostship-hermes HUDUI browser";
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
      ExecStart = dashboardCommand;
      Restart = "always";
      RestartSec = "2s";
    };
  };

  systemd.user.services.${managedGatewayServiceName} = lib.mkIf includeManagedRuntime {
    description = "Hermes managed gateway";
    wantedBy = [ "default.target" ];
    wants = [ "network-online.target" ];
    after = [ "network-online.target" ];
    environment = userServiceEnvironment // {
      HERMES_MANAGED = "true";
    };
    path = servicePath;
    serviceConfig = {
      Type = "simple";
      WorkingDirectory = rootTerminalCwd;
      EnvironmentFile = [ "-${managedEnvPath}" ];
      ExecStartPre = managedGatewayPreStartScript;
      ExecStart = managedGatewayScript;
      ExecStopPost = managedGatewayPostStopScript;
      Restart = "always";
      RestartSec = "2s";
    };
  };

  systemd.user.services.ghostship-hermes-gateway-restart = lib.mkIf includeManagedRuntime {
    description = "Restart Hermes managed gateway after runtime changes";
    serviceConfig = {
      Type = "oneshot";
      ExecStart = pkgs.writeShellScript "ghostship-hermes-gateway-restart.sh" ''
        exec ${pkgs.systemd}/bin/systemctl --user try-restart ${managedGatewayServiceName}.service
      '';
    };
  };

  systemd.user.paths.ghostship-hermes-gateway-restart = lib.mkIf includeManagedRuntime {
    wantedBy = [ "default.target" ];
    pathConfig = {
      PathChanged = [
        "${managedHermesHome}/config.yaml"
        "${managedEnvPath}"
        "${managedAuthPath}"
        "${managedSoulPath}"
      ];
      Unit = "ghostship-hermes-gateway-restart.service";
    };
  };

  systemd.services.ghostship-hermes-user-tooling-refresh = lib.mkIf includeManagedRuntime {
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
      PassEnvironment = managedRuntimeEnvKeys ++ managedBrowserEnvKeys;
      ExecStart = "${managedUserToolingScript} refresh";
    };
  };

  systemd.timers.ghostship-hermes-user-tooling-refresh = lib.mkIf includeManagedRuntime {
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnBootSec = "15min";
      OnUnitActiveSec = "1d";
      Persistent = true;
      Unit = "ghostship-hermes-user-tooling-refresh.service";
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

  system.extraDependencies = servicePath ++ [ storagePreparationScript ];

  environment.etc."ghostship-hermes-release".text = hermesRelease + "\n";
}
