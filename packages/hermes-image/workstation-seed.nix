{ pkgs }:
let
  workstationSeedTree = builtins.path {
    path = ./workstation-seed;
    name = "ghostship-hermes-workstation-seed-tree";
  };
in
pkgs.runCommand "ghostship-hermes-workstation-seed" { } ''
  mkdir -p "$out"
  cp -R ${workstationSeedTree}/. "$out/"
''
