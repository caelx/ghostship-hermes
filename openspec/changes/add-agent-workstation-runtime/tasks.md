## 1. Workstation state and runtime model

- [ ] 1.1 Document and implement the full-home `/home/hermes` persistence contract for the workstation runtime.
- [ ] 1.2 Replace the current `s6` runtime path with a `systemd`-based runtime that supports both system services and a `hermes` user manager.
- [ ] 1.3 Align profile aliases and persistent gateway services with Hermes' native profile and `gateway install` systemd behavior where possible.
- [ ] 1.4 Define the directory layout for home-managed app installs, updater state, caches, and mirrored workstation seed content.

## 2. Seed the develop environment into the workstation

- [ ] 2.1 Add a repo-managed workstation seed tree that mirrors the selected develop-environment defaults for `.agents`, Codex, Gemini CLI, Opencode, OpenSpec, and related agent assets.
- [ ] 2.2 Implement boot-time seeding that copies missing or managed defaults into `/home/hermes` without clobbering user-managed edits.
- [ ] 2.3 Document which workstation files are seeded, which are user-owned after seeding, and how future seed refreshes interact with local changes.

## 3. App and asset update automation

- [ ] 3.1 Implement boot-time and timer-driven installation/update flows for `codex`, `gemini-cli`, `opencode`, `openspec`, and `skills` as normal workstation apps.
- [ ] 3.2 Implement timer-driven refresh for mutable agent assets, including `skills.sh` skills, plugins/extensions, OpenSpec refresh, and opencode programming-free-model config regeneration.
- [ ] 3.3 Make the updater flows atomic and failure-tolerant so an interrupted or failed refresh preserves the last working local state.

## 4. Documentation and validation

- [ ] 4.1 Rewrite the README, changelog, and runtime guidance to describe the image as a persistent agent workstation optimized for minimal disruption and maximum enablement.
- [ ] 4.2 Add local validation that proves a reused `/home/hermes` preserves workstation state across container restart and replacement.
- [ ] 4.3 Verify the final proposal, design, specs, docs, and validation steps all match the home-first workstation model before release.
