## Context

The repo has already shifted broad operator tooling away from the immutable image and into the dedicated managed Nix profile at `/home/hermes/.local/state/nix/profiles/ghostship-managed`. That managed layer currently installs `hermes`, `git`, `curl`, `jq`, `nix`, `ripgrep`, `node`, `gh`, and `openssh`, while the dev shell separately includes `fd`, `tmux`, `uv`, `yq-go`, and a Python environment.

That leaves three gaps:

- the runtime contract and the actual managed profile inventory are out of sync
- Hermes lacks several lightweight operator tools that are already standard in repo workflows
- adding plain `python3` does not satisfy the desired Python contract, because `python3` alone has no `pip`, and adding `python3` plus `python3Packages.pip` still does not make `python3 -m pip` work

The design therefore needs to expand the managed tool inventory without diluting the repo's "minimum viable immutable system layer" rule.

## Goals / Non-Goals

**Goals:**
- Expose `fd`, `uv`, `yq-go`, and `tmux` through the managed Hermes user profile.
- Expose one managed Python runtime that supports `python3`, `pip`, and `python3 -m pip`.
- Keep the new tools on the normal Hermes-user PATH via the existing managed profile wiring.
- Update docs and validation so the runtime contract is explicit and testable.

**Non-Goals:**
- Expand the immutable default-image CLI policy to treat these tools as new baked admin/debug exceptions.
- Rework the broader multi-profile versus single-agent topology in the same change.
- Replace the repo's Python packaging flows or convert Python utility builds away from their current `uv`-based project structure.

## Decisions

### 1. Keep the new operator tools in the managed user profile, not the immutable image

The change will add `fd`, `uv`, `yq-go`, and `tmux` to the managed user-tooling convergence path rather than broadening `environment.systemPackages` or the approved default-image CLI list.

Rationale:

- The current runtime spec already says broad operator tooling should prefer the mutable managed layer.
- These tools are operator conveniences, not boot-critical services.
- Keeping them mutable preserves the repo's lean-image direction and avoids turning optional workflow helpers into new immutable-policy exceptions.

Alternatives considered:

- Add `tmux` or the whole set directly to the image layer. Rejected because it widens the baked CLI policy without a boot or supervision need.
- Leave the tools dev-shell-only. Rejected because the request is specifically about the Hermes runtime, not just local development.

### 2. Model Python as one pip-capable managed environment

The managed profile will install a single repo-defined Python environment that exposes `python3`, `pip`, and `python3 -m pip` consistently, instead of separate `python3` and `pip` packages.

Rationale:

- `nixpkgs#python3` alone does not provide `pip`.
- `nixpkgs#python3` plus `nixpkgs#python3Packages.pip` exposes a `pip` binary, but `python3 -m pip` still fails because the interpreter does not have the module on its path.
- A dedicated Python environment keeps the interpreter and pip module aligned and makes the user-facing contract testable.

Alternatives considered:

- Add only `python3`. Rejected because it does not satisfy the requested Python workflow.
- Add `python3` and a separate `pip` package. Rejected because it gives an inconsistent Python experience.
- Treat Python packaging as image-layer-only. Rejected because the runtime contract already prefers mutable user tooling for updateable operator tools.

### 3. Validate the tooling contract at command level

The implementation should verify not just command discovery but command execution for the newly managed tooling, especially Python and pip.

Rationale:

- `command -v pip` is not enough if `python3 -m pip` still fails.
- The current repo has already learned that path presence can hide broken execution paths.
- The managed runtime contract is user-facing, so it should be validated from the same Hermes-user PATH that operators use.

Alternatives considered:

- Rely on documentation and manual inspection only. Rejected because this change is specifically about runtime command behavior.

## Risks / Trade-offs

- [Risk] A repo-defined Python environment may increase managed-profile closure size. → Mitigation: keep the environment narrowly scoped to the interpreter plus pip support and reuse nixpkgs Python packaging rather than a large custom toolchain.
- [Risk] Adding `tmux`, `uv`, and other helper tools could blur the line between runtime and full workstation. → Mitigation: keep the change limited to a small explicit managed-tool inventory and preserve the existing immutable-image policy.
- [Risk] Docs currently state that runtime pip does not exist, so partial updates would leave the repo contradictory. → Mitigation: update README and `docs/nix-setup.md` in the same change as the runtime wiring.

## Migration Plan

1. Define the managed runtime-tooling contract in OpenSpec, including the pip-capable Python requirement.
2. Add the new managed tooling entries and the repo-defined Python environment to the managed user-tooling convergence path.
3. Update runtime validation to exercise `python3`, `pip`, and `python3 -m pip` along with the new helper CLIs from the Hermes-user PATH.
4. Rewrite runtime docs to describe the managed tool inventory and the new Python/pip behavior.

Rollback strategy:

- Revert the managed tooling entries and restore the prior docs if the expanded tool inventory proves too heavy or the Python environment choice causes unexpected conflicts.
- Because the tools live in the managed profile instead of the immutable image, rollback remains a convergence-path change rather than a base-image contract reset.

## Open Questions

- None for proposal scope. The requested Python contract is explicit enough to define the managed environment shape now.
