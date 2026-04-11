{ ... }:
{
  _module.args.includeRepoContent = true;
  imports = [
    ./nixos-module.nix
  ];
}
