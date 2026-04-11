{ ... }:
{
  _module.args.includeRepoContent = false;
  imports = [
    ./nixos-module.nix
  ];
}
