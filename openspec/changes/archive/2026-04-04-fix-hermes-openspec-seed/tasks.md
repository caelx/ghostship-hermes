## 1. Update OpenSpec override generation

- [x] 1.1 Change the Hermes runtime Ghostship propose override generator to emit `.worktrees/<name>/`.
- [x] 1.2 Verify the checked-in OpenSpec propose sources and the runtime-generated override text stay aligned after refresh.

## 2. Remove the retired brainstorming seed

- [x] 2.1 Remove `brainstorming` from the workstation seed AGENTS guidance, Codex skill config, and any repo-managed seed references.
- [x] 2.2 Remove the seeded `brainstorming` skill payload from the workstation seed tree.

## 3. Verify seeded and refreshed behavior

- [x] 3.1 Confirm a fresh workstation seed no longer includes `brainstorming` in the curated defaults.
- [x] 3.2 Confirm OpenSpec refresh within the Hermes image produces `.worktrees/<name>/` guidance for propose instructions.
