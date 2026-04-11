{ ... }:
{
  _module.args.includeRepoContent = true;
  _module.args.includeManagedRuntime = true;
  imports = [
    ./nixos-module.nix
  ];
}
