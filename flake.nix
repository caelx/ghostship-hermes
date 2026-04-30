{
  description = "ghostship-hermes";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";
    hermes-agent.url = "github:NousResearch/hermes-agent/v2026.4.23";
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
          ghostshipPython311Packages = pkgs.python311Packages.overrideScope (
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

          hermesDashboard = pkgs.callPackage ./packages/hermes-dashboard/package.nix {
            python311Packages = ghostshipPython311Packages;
          };
          agentBrowser = pkgs.callPackage ./packages/agent-browser/package.nix { };
          blogwatcher = pkgs.callPackage ./packages/blogwatcher/package.nix { };
          upstreamHermesAgent = hermes-agent.packages.${system}.default;
          wrappedHermesAgent = pkgs.callPackage ./packages/hermes-agent-wrapped/package.nix {
            hermesAgentPackage = upstreamHermesAgent;
            agentBrowserPackage = agentBrowser;
          };
          ghostshipSharedPython = pkgs.buildEnv {
            name = "ghostship-shared-python-deps";
            paths = with ghostshipPython311Packages; [
              httpx
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
          hermesRelease = lib.strings.removeSuffix "\n" (
            builtins.readFile ./packages/hermes-image/hermes-release.txt
          );
          ghostshipHermesRuntime = pkgs.callPackage ./packages/hermes-image/runtime.nix { inherit hermesDashboard; };
          googleWorkspaceCli = googleworkspace-cli.packages.${system}.gws;
          ghostshipDefaultTools = pkgs.buildEnv {
            name = "ghostship-default-tools";
            paths = [
              pkgs.bitwarden-cli
              pkgs.gh
              pkgs.google-cloud-sdk
              blogwatcher
              googleWorkspaceCli
            ];
            pathsToLink = [ "/bin" ];
            ignoreCollisions = true;
          };
          agentBrowserBuildTools = pkgs.buildEnv {
            name = "agent-browser-build-tools";
            paths = [
              pkgs.cargo
              pkgs.rustc
            ];
            pathsToLink = [ "/bin" ];
          };

          baseToolPackages = [
            pkgs.bitwarden-cli
            pkgs.google-cloud-sdk
            agentBrowser
            googleWorkspaceCli
          ];

          overlayUtilities = [
            ghostshipHermesRuntime
            hermesDashboard
          ] ++ baseToolPackages;
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
              sharedGhostshipDependencyPackages = [ ghostshipSharedPython ] ++ baseToolPackages;
            };
          };
          ghostshipHermesSystem = mkHermesSystem {
            modulePath = ./packages/hermes-image/nixos-final-module.nix;
            extraSpecialArgs = {
              inherit
                blogwatcher
                ghostshipHermesRuntime
                hermesDashboard
                ;
              blogwatcherPackage = blogwatcher;
              hermesAgentPackage = wrappedHermesAgent;
              sharedGhostshipDependencyPackages = [ ghostshipSharedPython ] ++ baseToolPackages;
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
          agent-browser-build-tools = agentBrowserBuildTools;
          ghostship-default-tools = ghostshipDefaultTools;
          bw = pkgs.bitwarden-cli;
          gcloud = pkgs.google-cloud-sdk;
          tirith = pkgs.tirith;
          agent-browser = agentBrowser;
          blogwatcher = blogwatcher;
          gws = googleWorkspaceCli;
          hermes-dashboard = hermesDashboard;
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
            bw
            gcloud
            tirith
            agent-browser
            blogwatcher
            gws
            hermes-dashboard
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
          ghostshipPython311Packages = pkgs.python311Packages.overrideScope (
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
              ghostshipPython311Packages.fastapi
              ghostshipPython311Packages.uvicorn
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
