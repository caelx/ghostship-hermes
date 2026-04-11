{ ... }:
{
  _module.args.includeRepoContent = false;
  _module.args.includeManagedRuntime = false;
  imports = [
    ./nixos-module.nix
  ];
}
