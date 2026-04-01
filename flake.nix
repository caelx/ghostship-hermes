{
  description = "ghostship-hermes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      lib = nixpkgs.lib;
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = lib.genAttrs systems;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };

          # Utility packages
          ghostshipSearxng = pkgs.callPackage ./packages/searxng-cli/package.nix { };
          ghostshipSonarr = pkgs.callPackage ./packages/sonarr-cli/package.nix { };
          ghostshipRadarr = pkgs.callPackage ./packages/radarr-cli/package.nix { };
          ghostshipProwlarr = pkgs.callPackage ./packages/prowlarr-cli/package.nix { };
          ghostshipPlex = pkgs.callPackage ./packages/plex-cli/package.nix { };
          ghostshipRomm = pkgs.callPackage ./packages/romm-cli/package.nix { };
          ghostshipNzbget = pkgs.callPackage ./packages/nzbget-cli/package.nix { };
          ghostshipQbittorrent = pkgs.callPackage ./packages/qbittorrent-cli/package.nix { };
          ghostshipGrimmory = pkgs.callPackage ./packages/grimmory-cli/package.nix { };
          ghostshipTautulli = pkgs.callPackage ./packages/tautulli-cli/package.nix { };
          ghostshipBazarr = pkgs.callPackage ./packages/bazarr-cli/package.nix { };
          ghostshipSynology = pkgs.callPackage ./packages/synology-cli/package.nix { };
          ghostshipFlaresolverr = pkgs.callPackage ./packages/flaresolverr-cli/package.nix { };
          ghostshipPyloadNg = pkgs.callPackage ./packages/pyload-ng-cli/package.nix { };
          ghostshipCloakbrowser = pkgs.callPackage ./packages/cloakbrowser-cli/package.nix { };
          ghostshipPricebuddy = pkgs.callPackage ./packages/pricebuddy-cli/package.nix { };
          ghostshipRssBridge = pkgs.callPackage ./packages/rss-bridge-cli/package.nix { };
          honchoAi = pkgs.callPackage ./packages/honcho-ai/package.nix { };

          hermesRelease = lib.strings.removeSuffix "\n" (
            builtins.readFile ./packages/hermes-image/hermes-release.txt
          );
          ghostshipHermesRuntime = pkgs.callPackage ./packages/hermes-image/runtime.nix {
            inherit hermesRelease;
          };

          allUtilities = [
            ghostshipSearxng
            ghostshipSonarr
            ghostshipRadarr
            ghostshipProwlarr
            ghostshipPlex
            ghostshipRomm
            ghostshipNzbget
            ghostshipQbittorrent
            ghostshipGrimmory
            ghostshipTautulli
            ghostshipBazarr
            ghostshipSynology
            ghostshipFlaresolverr
            ghostshipPyloadNg
            ghostshipCloakbrowser
            ghostshipPricebuddy
            ghostshipRssBridge
          ];
        in
        {
          ghostship-searxng = ghostshipSearxng;
          ghostship-sonarr = ghostshipSonarr;
          ghostship-radarr = ghostshipRadarr;
          ghostship-prowlarr = ghostshipProwlarr;
          ghostship-plex = ghostshipPlex;
          ghostship-romm = ghostshipRomm;
          ghostship-nzbget = ghostshipNzbget;
          ghostship-qbittorrent = ghostshipQbittorrent;
          ghostship-grimmory = ghostshipGrimmory;
          ghostship-tautulli = ghostshipTautulli;
          ghostship-bazarr = ghostshipBazarr;
          ghostship-synology = ghostshipSynology;
          ghostship-flaresolverr = ghostshipFlaresolverr;
          ghostship-pyload-ng = ghostshipPyloadNg;
          ghostship-cloakbrowser = ghostshipCloakbrowser;
          ghostship-pricebuddy = ghostshipPricebuddy;
          ghostship-rss-bridge = ghostshipRssBridge;

          ghostship-hermes-runtime = ghostshipHermesRuntime;

          ghostship-hermes-image = pkgs.callPackage ./packages/hermes-image/image.nix {
            inherit
              ghostshipHermesRuntime
              hermesRelease
              pkgs
              honchoAi
              ;
            ghostshipUtilities = allUtilities;
          };
        }
      );

      checks = forAllSystems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };
        in
        {
          inherit (self.packages.${system})
            ghostship-searxng
            ghostship-sonarr
            ghostship-radarr
            ghostship-prowlarr
            ghostship-plex
            ghostship-romm
            ghostship-nzbget
            ghostship-qbittorrent
            ghostship-grimmory
            ghostship-tautulli
            ghostship-bazarr
            ghostship-synology
            ghostship-flaresolverr
            ghostship-pyload-ng
            ghostship-cloakbrowser
            ghostship-pricebuddy
            ghostship-rss-bridge
            ghostship-hermes-runtime
            ghostship-hermes-image;
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = import nixpkgs {
            inherit system;
            config.allowUnfree = true;
          };
          pythonEnv = pkgs.python311.withPackages (
            ps: with ps; [
              hatchling
              httpx
              mypy
              pytest
              typer
            ]
          );
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              bash
              coreutils
              curl
              fd
              gh
              git
              jq
              nodejs_22
              pythonEnv
              ripgrep
              tmux
              uv
              yq-go
            ];
            shellHook = ''
              export PIP_DISABLE_PIP_VERSION_CHECK=1
              export PYTHONPATH="$PWD/packages/searxng-cli/src:$PWD/packages/sonarr-cli/src:$PWD/packages/radarr-cli/src:$PWD/packages/prowlarr-cli/src:$PWD/packages/plex-cli/src:$PWD/packages/romm-cli/src:$PWD/packages/nzbget-cli/src:$PWD/packages/qbittorrent-cli/src:$PWD/packages/grimmory-cli/src:$PWD/packages/tautulli-cli/src:$PWD/packages/bazarr-cli/src:$PWD/packages/synology-cli/src:$PWD/packages/flaresolverr-cli/src:$PWD/packages/pyload-ng-cli/src:$PWD/packages/cloakbrowser-cli/src:$PWD/packages/pricebuddy-cli/src:$PWD/packages/rss-bridge-cli/src${PYTHONPATH:+:$PYTHONPATH}"
            '';
          };
        }
      );

      formatter = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
        in
        pkgs.nixfmt-rfc-style
      );
    };
}
