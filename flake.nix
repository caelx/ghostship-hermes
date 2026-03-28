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
          ghostshipSearxng = pkgs.callPackage ./packages/searxng-cli/package.nix { };
          hermesRelease = lib.strings.removeSuffix "\n" (
            builtins.readFile ./packages/hermes-image/hermes-release.txt
          );
          ghostshipHermesRuntime = pkgs.callPackage ./packages/hermes-image/runtime.nix {
            inherit hermesRelease;
          };
        in
        {
          ghostship-searxng = ghostshipSearxng;
          ghostship-hermes-runtime = ghostshipHermesRuntime;
        }
        // lib.optionalAttrs (system == "aarch64-linux") {
          ghostship-hermes-image = pkgs.callPackage ./packages/hermes-image/image.nix {
            inherit
              ghostshipHermesRuntime
              hermesRelease
              ghostshipSearxng
              pkgs
              ;
          };
          default = pkgs.callPackage ./packages/hermes-image/image.nix {
            inherit
              ghostshipHermesRuntime
              hermesRelease
              ghostshipSearxng
              pkgs
              ;
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
          ghostship-searxng = self.packages.${system}.ghostship-searxng;
          ghostship-hermes-runtime = self.packages.${system}.ghostship-hermes-runtime;
        }
        // lib.optionalAttrs (system == "aarch64-linux") {
          ghostship-hermes-image = self.packages.${system}.ghostship-hermes-image;
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
              rich
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
              export PYTHONPATH="$PWD/packages/searxng-cli/src''${PYTHONPATH:+:$PYTHONPATH}"
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
