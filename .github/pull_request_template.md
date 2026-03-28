## Summary

- change:
- reason:

## Verification

- [ ] `python3 scripts/python_utility.py lock packages/searxng-cli`
- [ ] `python3 scripts/python_utility.py test packages/searxng-cli`
- [ ] `python3 scripts/python_utility.py build packages/searxng-cli`
- [ ] `nix build .#packages.x86_64-linux.ghostship-hermes-runtime`
- [ ] `nix build .#packages.aarch64-linux.ghostship-hermes-image`
