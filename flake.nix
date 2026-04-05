{
  description = "ghostship-hermes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    hermes-agent.url = "github:NousResearch/hermes-agent/v2026.4.3";
  };

  outputs =
    {
      self,
      nixpkgs,
      hermes-agent,
    }:
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
          routerPython311Packages = pkgs.python311Packages.overrideScope (
            final: prev: {
              watchfiles = prev.watchfiles.overridePythonAttrs (_: {
                doCheck = false;
              });
              fastapi-cli = prev.fastapi-cli.overridePythonAttrs (_: {
                doCheck = false;
              });
              fastapi = prev.fastapi.overridePythonAttrs (_: {
                doCheck = false;
              });
            }
          );

          # Utility packages
          ghostshipCliContract = pkgs.callPackage ./packages/ghostship-cli-contract/package.nix { };
          routerGhostshipCliContract = pkgs.callPackage ./packages/ghostship-cli-contract/package.nix {
            python311Packages = routerPython311Packages;
          };
          hermesDashboard = pkgs.callPackage ./packages/hermes-dashboard/package.nix {
            python311Packages = routerPython311Packages;
          };
          ghostshipSearxng = pkgs.callPackage ./packages/searxng-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipSonarr = pkgs.callPackage ./packages/sonarr-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipRadarr = pkgs.callPackage ./packages/radarr-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipProwlarr = pkgs.callPackage ./packages/prowlarr-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipPlex = pkgs.callPackage ./packages/plex-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipRomm = pkgs.callPackage ./packages/romm-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipNzbget = pkgs.callPackage ./packages/nzbget-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipQbittorrent = pkgs.callPackage ./packages/qbittorrent-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipGrimmory = pkgs.callPackage ./packages/grimmory-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipTautulli = pkgs.callPackage ./packages/tautulli-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipBazarr = pkgs.callPackage ./packages/bazarr-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipSynology = pkgs.callPackage ./packages/synology-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipFlaresolverr = pkgs.callPackage ./packages/flaresolverr-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipPyloadNg = pkgs.callPackage ./packages/pyload-ng-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipCloakbrowser = pkgs.callPackage ./packages/cloakbrowser-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipPricebuddy = pkgs.callPackage ./packages/pricebuddy-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipRssBridge = pkgs.callPackage ./packages/rss-bridge-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipChangedetection = pkgs.callPackage ./packages/changedetection-cli/package.nix { inherit ghostshipCliContract; };
          ghostshipHermesRouter = pkgs.callPackage ./packages/hermes-router/package.nix {
            python311Packages = routerPython311Packages;
            ghostshipCliContract = routerGhostshipCliContract;
          };
          hermesRelease = lib.strings.removeSuffix "\n" (
            builtins.readFile ./packages/hermes-image/hermes-release.txt
          );
          ghostshipHermesRuntime = pkgs.callPackage ./packages/hermes-image/runtime.nix { inherit hermesDashboard; };

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
            ghostshipChangedetection
          ];

          ghostshipHermesSystem = nixpkgs.lib.nixosSystem {
            inherit system;
            specialArgs = {
              inherit
                ghostshipHermesRouter
                ghostshipHermesRuntime
                hermesRelease
                hermesDashboard
                ;
              ghostshipUtilities = allUtilities;
            };
            modules = [
              ({ ... }: {
                nixpkgs.config.allowUnfree = true;
              })
              hermes-agent.nixosModules.default
              ./packages/hermes-image/nixos-module.nix
            ];
          };
          ghostshipHermesRootfs = ghostshipHermesSystem.config.system.build.tarball;
          ghostshipHermesImage = pkgs.callPackage ./packages/hermes-image/image.nix {
            inherit
              system
              ghostshipHermesRootfs
              hermesRelease
              ;
          };
        in
        {
          hermes-dashboard = hermesDashboard;
          ghostship-cli-contract = ghostshipCliContract;
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
          ghostship-changedetection = ghostshipChangedetection;
          ghostship-hermes-router = ghostshipHermesRouter;
          ghostship-hermes-runtime = ghostshipHermesRuntime;
          ghostship-hermes-system = ghostshipHermesSystem.config.system.build.toplevel;
          ghostship-hermes-rootfs = ghostshipHermesRootfs;
          ghostship-hermes-image = ghostshipHermesImage;
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
            hermes-dashboard
            ghostship-cli-contract
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
            ghostship-changedetection
            ghostship-hermes-router
            ghostship-hermes-runtime
            ghostship-hermes-system
            ghostship-hermes-rootfs
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
          routerPython311Packages = pkgs.python311Packages.overrideScope (
            final: prev: {
              watchfiles = prev.watchfiles.overridePythonAttrs (_: {
                doCheck = false;
              });
              fastapi-cli = prev.fastapi-cli.overridePythonAttrs (_: {
                doCheck = false;
              });
              fastapi = prev.fastapi.overridePythonAttrs (_: {
                doCheck = false;
              });
            }
          );
          pythonEnv = pkgs.python311.withPackages (
            ps: with ps; [
              hatchling
              httpx
              mypy
              pytest
              typer
              routerPython311Packages.fastapi
              routerPython311Packages.uvicorn
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
              export PYTHONPATH="$PWD/packages/ghostship-cli-contract/src:$PWD/packages/searxng-cli/src:$PWD/packages/sonarr-cli/src:$PWD/packages/radarr-cli/src:$PWD/packages/prowlarr-cli/src:$PWD/packages/plex-cli/src:$PWD/packages/romm-cli/src:$PWD/packages/nzbget-cli/src:$PWD/packages/qbittorrent-cli/src:$PWD/packages/grimmory-cli/src:$PWD/packages/tautulli-cli/src:$PWD/packages/bazarr-cli/src:$PWD/packages/synology-cli/src:$PWD/packages/flaresolverr-cli/src:$PWD/packages/pyload-ng-cli/src:$PWD/packages/cloakbrowser-cli/src:$PWD/packages/pricebuddy-cli/src:$PWD/packages/rss-bridge-cli/src:$PWD/packages/changedetection-cli/src:$PWD/packages/hermes-router/src${PYTHONPATH:+:$PYTHONPATH}"
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
