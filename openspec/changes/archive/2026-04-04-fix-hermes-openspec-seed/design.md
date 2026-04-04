## Context

The repo-managed OpenSpec propose sources already point agents at `.worktrees/<name>/`, but the Hermes runtime still regenerates its Ghostship override block with the stale singular `.worktree/<name>/` path. Separately, the workstation seed continues to ship `brainstorming` in its AGENTS guidance, Codex skill configuration, and seeded skill tree even though that skill has been removed from the desired curated Hermes environment.

The workstation seed is intentionally copy-if-missing and non-destructive. That preserves user-managed persisted state, but it also means removing a seed entry from the image does not delete previously seeded content from existing `/opt/data/home` state.

## Goals / Non-Goals

**Goals:**
- Make Hermes-regenerated OpenSpec instructions match the current `.worktrees/<name>/` repo policy.
- Remove `brainstorming` from the curated workstation defaults that ship with the Hermes image.
- Clean up repo-managed references so fresh seeded environments do not advertise a removed skill.

**Non-Goals:**
- Automatically delete previously seeded `brainstorming` files from existing persisted homes.
- Redesign the broader workstation seeding model or make seeding destructive.
- Change upstream OpenSpec artifact schemas or the non-Ghostship portions of the OpenSpec skills.

## Decisions

### Decision: Fix the runtime override generator, not just the checked-in skill copies

Update `create_openspec_override_file()` in `packages/hermes-image/runtime.nix` so the generated Ghostship propose override uses `.worktrees/<name>/`.

Why:
- The runtime refresh flow is the authoritative source for the image's regenerated OpenSpec overrides.
- Patching only the tracked `.codex`, `.gemini`, or `.opencode` files would still allow a later `openspec update` to reinsert the stale `.worktree` text inside Hermes.

Alternative considered:
- Update only the checked-in propose skill files.
  Rejected because the runtime refresh path would continue to diverge from the repo sources.

### Decision: Remove `brainstorming` from the workstation seed and its repo-managed references

Update the workstation seed so it no longer:
- recommends `brainstorming` in `.agents/AGENTS.md`
- enables `brainstorming` in the seeded Codex config
- references `brainstorming` from repo-managed helper skills
- ships the `packages/hermes-image/workstation-seed/.agents/skills/brainstorming/` payload

Why:
- The curated Hermes defaults should only ship skills that are still intended to be available.
- Leaving the payload or references in place makes the image contradict the current repo policy.

Alternative considered:
- Leave the skill payload in the image but disable it in config.
  Rejected because the image would still ship a removed skill and stale guidance.

### Decision: Keep this change non-destructive for existing persisted homes

Do not add automatic pruning of previously seeded `brainstorming` content in this change.

Why:
- The current seeding contract is explicitly copy-if-missing and non-destructive.
- Automatically deleting skill directories or rewriting existing user config in `/opt/data/home` carries migration risk and would broaden the change beyond correcting the shipped defaults.

Alternative considered:
- Add a boot-time migration that removes stale `brainstorming` state from persisted homes.
  Rejected for now because it changes the persistence contract and needs separate review.

## Risks / Trade-offs

- Existing persisted Hermes homes will still contain previously seeded `brainstorming` files and references.
  Mitigation: scope the change to fresh seeds and refreshed overrides, and note the retained state as an operational follow-up if cleanup becomes necessary.

- Removing the seeded skill payload could leave stale repo-managed references if one is missed.
  Mitigation: perform a repo-wide search for `brainstorming` within the workstation seed and update every remaining reference in the same change.

- The OpenSpec override fix touches generated runtime content rather than only static seed files.
  Mitigation: keep the change narrowly focused on the propose override block and verify the generated text after implementation.

## Migration Plan

1. Update the image source so new builds seed the corrected defaults.
2. Verify a fresh seeded home does not contain `brainstorming` references and that refreshed OpenSpec overrides use `.worktrees/<name>/`.
3. Leave existing persisted homes unchanged by this change; handle any cleanup later as an explicit migration if needed.

## Open Questions

- Should a later change add an explicit opt-in cleanup command or migration path for operators who want to remove previously seeded `brainstorming` state from persisted homes?
