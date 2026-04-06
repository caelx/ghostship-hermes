## 1. Basic Scaffold

- [x] 1.1 Introduce a single declarative Nix profile matrix for `assistant`, `operations`, and `supervisor`
- [x] 1.2 Generate the basic managed profile config scaffold, env destinations, skill destinations, and service metadata from that matrix
- [x] 1.3 Switch the sticky default profile scaffold from `operations` to `assistant` while keeping the root config minimal

## 2. Hermes Settings Audit

- [ ] 2.1 Inventory the Hermes settings surface we may want to bake into Nix for the final configuration
- [ ] 2.2 Classify each setting as Nix-managed, runtime-env-managed, or Hermes-owned mutable state
- [ ] 2.3 Define the initial per-profile defaults for model/provider, terminal behavior, persona, and env boundaries without baking secrets

## 3. Runtime Integration

- [ ] 3.1 Migrate bootstrap, dashboard metadata, and long-running gateway services from the current two-profile layout to `assistant`, `operations`, and `supervisor`
- [ ] 3.2 Preserve shared and per-profile runtime skill seeding for the new profile set, including copy-once non-overwrite behavior
- [ ] 3.3 Verify the new scaffold still tolerates upstream Hermes profile creation defaults unless an explicit cleanup rule is added

## 4. Validation And Docs

- [ ] 4.1 Update image validation to prove the new managed profile scaffold and `assistant` sticky default
- [ ] 4.2 Update README and supporting docs to describe the three-profile scaffold, shared skills directory, and runtime-owned skills/secrets model
