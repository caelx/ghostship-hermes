## Context

The image currently assembles its toolchain through the repo flake and seeds repo-managed skills from `skills/` into `~/.hermes/skills` on first start. This change introduces a large external CLI and a large external skill catalog, so the design has to preserve three repo invariants: reproducible image builds, offline first-start seeding, and non-destructive behavior toward user-managed skill content.

Upstream `googleworkspace/cli` already offers a Nix flake, a broad Google Workspace command surface, JSON-native output, and a large `SKILL.md` catalog. The main design work is therefore integration and lifecycle management rather than inventing new application behavior.

## Goals / Non-Goals

**Goals:**
- Add `gws` to the Hermes image through the repo flake using a pinned upstream flake revision.
- Vendor the full upstream Google Workspace skill catalog into this repo as reviewable source content.
- Seed vendored Google Workspace skills into `~/.hermes/skills` without overwriting existing user-managed or previously seeded content.
- Keep Google Workspace CLI versioning and vendored skills aligned to the same upstream revision.
- Update repo-managed Nix guidance so repo and image workflows are explicitly flake-first.
- Document authentication expectations for a dedicated Google account, including narrow-scope guidance for Gmail on testing-mode personal accounts.

**Non-Goals:**
- Rewriting or curating the upstream Google Workspace skill content beyond minimal repo-integration glue.
- Building a Ghostship-specific wrapper CLI around `gws`.
- Adding profile-aware Google credential orchestration in the runtime bootstrap.
- Supporting runtime downloads of skills or binaries outside the pinned repo revision.

## Decisions

### Use a pinned flake input for `googleworkspace/cli`

The repo will add an upstream flake input and expose `gws` through local package wiring rather than installing through `npm` or fetching a prebuilt binary. This keeps the build graph declarative, lets `nix flake check --no-build` validate the package wiring, and aligns with the repo preference that image composition be driven by flakes.

Alternative considered: fetch a release tarball or install with `npm`. Rejected because it creates a second packaging path outside the repo flake, complicates upgrades, and weakens reproducibility.

### Vendor the full upstream skill tree as committed repo content

The upstream skills will be copied into a repo-owned vendor location and committed. Image builds and first-start skill seeding will read from that local tree, not from the network. The vendor snapshot and the pinned flake input should be updated together.

Alternative considered: fetch skills during image build or container startup. Rejected because it breaks offline reproducibility and makes the seeded skill inventory depend on live network state.

### Preserve upstream skill names and keep local Ghostship skills alongside them

The vendored upstream `gws-*`, persona, and recipe skill names should remain unchanged so upstream documentation and examples still match the seeded runtime. Existing local skills such as `hermes-nix`, `agent-browser`, and `current-environment` remain in the repo-managed skill set and continue to seed beside the Google Workspace skills.

Alternative considered: rename upstream skills under a Ghostship prefix. Rejected because it increases maintenance burden and diverges from upstream usage guidance with little benefit.

### Reuse the existing first-start copy-once seeding contract

The runtime already copies missing skill directories from the default skill tree into `~/.hermes/skills`. This behavior will be retained for the vendored Google Workspace skills so seeded defaults remain additive and do not overwrite user-managed content.

Alternative considered: force-sync the skill tree on every start. Rejected because it would overwrite user edits and break the repo invariant that seeding does not clobber managed content in the user profile.

### Tighten the Nix guidance around flake-native workflows

The existing `hermes-nix` skill should be updated rather than creating a second overlapping Nix skill. It should explicitly prefer `nix run`, `nix shell`, `nix develop`, and repo `.#` outputs, and it should explain when `nix profile install` remains appropriate for persistent user-level tools.

Alternative considered: add a separate new Nix skill. Rejected because it splits overlapping guidance and increases ambiguity for agents.

## Risks / Trade-offs

- [Upstream skill volume increases repo size and review noise] -> Commit the vendor tree under a dedicated location and treat updates as pinned snapshot refreshes tied to a specific upstream revision.
- [Upstream flake or package shape may change] -> Wrap the upstream package through local flake wiring so integration points stay explicit and reviewable.
- [Broad OAuth scope requests can fail for personal Gmail accounts in testing mode] -> Document narrow-scope auth flows for Gmail-first use and avoid steering users toward the broad preset for unverified personal accounts.
- [Vendored skill names could collide with local names in the future] -> Keep upstream names unchanged, keep local skills intentionally named, and fail review on any future collision before release.
- [Seeding more skills increases first-start copy work] -> Continue using local file copy-once behavior and avoid runtime network fetches.

## Migration Plan

1. Add and pin the upstream `googleworkspace/cli` flake input in the repo flake.
2. Wire the upstream `gws` package into local packages and the Hermes image contents.
3. Vendor the upstream skills snapshot into the repo and point default skill seeding at the combined tree.
4. Update `hermes-nix` and relevant docs to describe the new flake-first and Google Workspace workflows.
5. Verify flake evaluation and image assembly with the new input and seeded skill tree.
6. If rollback is needed, remove the flake input and vendored skill tree together so the runtime returns to the prior curated skill set without partial integration.

## Open Questions

- Should the repo keep the vendored skills under a dedicated `vendor/` path or flatten them into the top-level `skills/` tree during update workflows?
- Do we want a small local wrapper skill for account/auth conventions, or should the broad upstream skill set plus updated README be the only Google Workspace guidance layer?
