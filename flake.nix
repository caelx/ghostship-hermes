{
  description = "ghostship-hermes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    hermes-agent.url = "github:NousResearch/hermes-agent/v2026.4.13";
    googleworkspace-cli.url = "github:googleworkspace/cli";
  };

  outputs =
    {
      self,
      nixpkgs,
      hermes-agent,
      googleworkspace-cli,
    }:
    let
      lib = nixpkgs.lib;
      sourceUrl = "https://github.com/caelx/ghostship-hermes";
      revision = self.shortRev or self.dirtyShortRev or self.rev or "dirty";
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
              websockets = prev.websockets.overridePythonAttrs (_: {
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
          ghostshipCliContract = pkgs.callPackage ./packages/ghostship-cli-contract/package.nix {
            python311Packages = routerPython311Packages;
          };
          mkGhostshipPythonUtility = packagePath: pkgs.callPackage packagePath {
            python311Packages = routerPython311Packages;
            inherit ghostshipCliContract;
          };
          hermesDashboard = pkgs.callPackage ./packages/hermes-dashboard/package.nix {
            python311Packages = routerPython311Packages;
          };
          ghostshipSearxng = mkGhostshipPythonUtility ./packages/searxng-cli/package.nix;
          ghostshipSonarr = mkGhostshipPythonUtility ./packages/sonarr-cli/package.nix;
          ghostshipRadarr = mkGhostshipPythonUtility ./packages/radarr-cli/package.nix;
          ghostshipProwlarr = mkGhostshipPythonUtility ./packages/prowlarr-cli/package.nix;
          ghostshipPlex = mkGhostshipPythonUtility ./packages/plex-cli/package.nix;
          ghostshipRomm = mkGhostshipPythonUtility ./packages/romm-cli/package.nix;
          ghostshipNzbget = mkGhostshipPythonUtility ./packages/nzbget-cli/package.nix;
          ghostshipQbittorrent = mkGhostshipPythonUtility ./packages/qbittorrent-cli/package.nix;
          ghostshipGrimmory = mkGhostshipPythonUtility ./packages/grimmory-cli/package.nix;
          ghostshipTautulli = mkGhostshipPythonUtility ./packages/tautulli-cli/package.nix;
          ghostshipBazarr = mkGhostshipPythonUtility ./packages/bazarr-cli/package.nix;
          ghostshipSynology = mkGhostshipPythonUtility ./packages/synology-cli/package.nix;
          ghostshipFlaresolverr = mkGhostshipPythonUtility ./packages/flaresolverr-cli/package.nix;
          ghostshipPyloadNg = mkGhostshipPythonUtility ./packages/pyload-ng-cli/package.nix;
          ghostshipCloakbrowser = mkGhostshipPythonUtility ./packages/cloakbrowser-cli/package.nix;
          ghostshipPricebuddy = mkGhostshipPythonUtility ./packages/pricebuddy-cli/package.nix;
          ghostshipRssBridge = mkGhostshipPythonUtility ./packages/rss-bridge-cli/package.nix;
          ghostshipChangedetection = mkGhostshipPythonUtility ./packages/changedetection-cli/package.nix;
          ghostshipBookStack = mkGhostshipPythonUtility ./packages/bookstack-cli/package.nix;
          ghostshipN8n = mkGhostshipPythonUtility ./packages/n8n-cli/package.nix;
          ghostshipChaptarr = mkGhostshipPythonUtility ./packages/chaptarr-cli/package.nix;
          agentBrowser = pkgs.callPackage ./packages/agent-browser/package.nix { };
          blogtato = pkgs.callPackage ./packages/blogtato/package.nix { };
          upstreamHermesAgent = hermes-agent.packages.${system}.default;
          wrappedHermesAgent = pkgs.callPackage ./packages/hermes-agent-wrapped/package.nix {
            hermesAgentPackage = upstreamHermesAgent;
            agentBrowserPackage = agentBrowser;
          };
          ghostshipSharedPython = pkgs.buildEnv {
            name = "ghostship-shared-python-deps";
            paths = with routerPython311Packages; [
              ghostshipCliContract
              httpx
              typer
              fastapi
              uvicorn
              websockets
              pydantic
              pydantic-core
              starlette
              click
              shellingham
              annotated-types
              typing-extensions
              typing-inspection
              python-dotenv
              python-multipart
              watchfiles
              urllib3
              yarl
              anyio
              httpcore
              certifi
              charset-normalizer
              idna
              sniffio
              aiohttp
              aiohappyeyeballs
              aiosignal
              attrs
              frozenlist
              multidict
              propcache
            ];
          };
          ghostshipHermesRouter = pkgs.callPackage ./packages/hermes-router/package.nix {
            python311Packages = routerPython311Packages;
            inherit ghostshipCliContract;
          };
          hermesRelease = lib.strings.removeSuffix "\n" (
            builtins.readFile ./packages/hermes-image/hermes-release.txt
          );
          ghostshipHermesRuntime = pkgs.callPackage ./packages/hermes-image/runtime.nix { inherit hermesDashboard; };
          googleWorkspaceCli = googleworkspace-cli.packages.${system}.gws;

          baseUtilityPackages = [
            pkgs.bws
            pkgs.google-cloud-sdk
            agentBrowser
            googleWorkspaceCli
          ];

          allUtilities = baseUtilityPackages ++ [
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
            ghostshipBookStack
            ghostshipChaptarr
            ghostshipN8n
          ];

          overlayUtilities = [
            ghostshipHermesRouter
            ghostshipHermesRuntime
            hermesDashboard
          ] ++ allUtilities;
          overlayUtilityEnv = pkgs.buildEnv {
            name = "ghostship-hermes-overlay";
            paths = overlayUtilities;
            ignoreCollisions = true;
          };

          mkHermesSystem =
            {
              modulePath,
              extraSpecialArgs ? { },
            }:
            nixpkgs.lib.nixosSystem {
              inherit system;
              specialArgs = extraSpecialArgs // {
                inherit hermesRelease;
              };
              modules = [
                ({ ... }: {
                  nixpkgs.config.allowUnfree = true;
                })
                hermes-agent.nixosModules.default
                modulePath
              ];
            };

          ghostshipHermesBaseSystem = mkHermesSystem {
            modulePath = ./packages/hermes-image/nixos-base-module.nix;
            extraSpecialArgs = {
              hermesAgentPackage = upstreamHermesAgent;
              sharedGhostshipDependencyPackages = [ ghostshipSharedPython ] ++ baseUtilityPackages;
            };
          };
          ghostshipHermesSystem = mkHermesSystem {
            modulePath = ./packages/hermes-image/nixos-final-module.nix;
            extraSpecialArgs = {
              inherit
                blogtato
                ghostshipHermesRouter
                ghostshipHermesRuntime
                hermesDashboard
                ;
              blogtatoPackage = blogtato;
              hermesAgentPackage = wrappedHermesAgent;
              ghostshipUtilities = allUtilities;
              sharedGhostshipDependencyPackages = [ ghostshipSharedPython ] ++ baseUtilityPackages;
            };
          };
          ghostshipHermesOverlayBundle = pkgs.callPackage ./packages/hermes-image/overlay-bundle.nix {
            overlayEnv = overlayUtilityEnv;
            baseClosureRoots = [ ghostshipHermesBaseSystem.config.system.build.toplevel ];
          };
          ghostshipHermesRootfs = ghostshipHermesSystem.config.system.build.tarball;
          ghostshipHermesBaseRootfs = ghostshipHermesBaseSystem.config.system.build.tarball;
          ghostshipHermesImage = pkgs.callPackage ./packages/hermes-image/image.nix {
            inherit
              system
              ghostshipHermesRootfs
              hermesRelease
              sourceUrl
              revision
              ;
          };
          ghostshipHermesBaseImage = pkgs.callPackage ./packages/hermes-image/image.nix {
            inherit
              system
              hermesRelease
              sourceUrl
              revision
              ;
            ghostshipHermesRootfs = ghostshipHermesBaseRootfs;
            defaultImageRef = "ghostship-hermes-base:${hermesRelease}";
          };
        in
        {
          bws = pkgs.bws;
          gcloud = pkgs.google-cloud-sdk;
          agent-browser = agentBrowser;
          blogtato = blogtato;
          gws = googleWorkspaceCli;
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
          ghostship-bookstack = ghostshipBookStack;
          ghostship-chaptarr = ghostshipChaptarr;
          ghostship-n8n = ghostshipN8n;
          ghostship-hermes-router = ghostshipHermesRouter;
          ghostship-hermes-runtime = ghostshipHermesRuntime;
          hermes-agent-wrapped = wrappedHermesAgent;
          ghostship-hermes-system = ghostshipHermesSystem.config.system.build.toplevel;
          ghostship-hermes-rootfs = ghostshipHermesRootfs;
          ghostship-hermes-base-image = ghostshipHermesBaseImage;
          ghostship-hermes-overlay-bundle = ghostshipHermesOverlayBundle;
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
            bws
            gcloud
            agent-browser
            blogtato
            gws
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
            ghostship-bookstack
            ghostship-chaptarr
            ghostship-n8n
            ghostship-hermes-router
            ghostship-hermes-runtime
            hermes-agent-wrapped
            ghostship-hermes-system
            ghostship-hermes-rootfs
            ghostship-hermes-base-image
            ghostship-hermes-overlay-bundle
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
              websockets = prev.websockets.overridePythonAttrs (_: {
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
              export PYTHONPATH="$PWD/packages/ghostship-cli-contract/src:$PWD/packages/searxng-cli/src:$PWD/packages/sonarr-cli/src:$PWD/packages/radarr-cli/src:$PWD/packages/prowlarr-cli/src:$PWD/packages/plex-cli/src:$PWD/packages/romm-cli/src:$PWD/packages/nzbget-cli/src:$PWD/packages/qbittorrent-cli/src:$PWD/packages/grimmory-cli/src:$PWD/packages/tautulli-cli/src:$PWD/packages/bazarr-cli/src:$PWD/packages/synology-cli/src:$PWD/packages/flaresolverr-cli/src:$PWD/packages/pyload-ng-cli/src:$PWD/packages/cloakbrowser-cli/src:$PWD/packages/pricebuddy-cli/src:$PWD/packages/rss-bridge-cli/src:$PWD/packages/changedetection-cli/src:$PWD/packages/bookstack-cli/src:$PWD/packages/hermes-router/src${PYTHONPATH:+:$PYTHONPATH}"
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
