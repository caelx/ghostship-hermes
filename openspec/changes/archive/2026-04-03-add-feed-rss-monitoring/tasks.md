## 1. Package and bundle `feed`

- [x] 1.1 Add a pinned upstream `feed` package to `flake.nix` and expose it as a first-class flake package
- [x] 1.2 Add the packaged `feed` utility to the Hermes image bundle alongside the other curated non-`ghostship-*` tools

## 2. Wire persistent profile-scoped runtime state

- [x] 2.1 Export `FEED_DB_PATH` from the Hermes runtime to `$HERMES_HOME/feed/feed.db`
- [x] 2.2 Ensure the runtime creates the parent `feed` directory under each profile’s `HERMES_HOME`

## 3. Add the Hermes skill and RSS workflow guidance

- [x] 3.1 Create `skills/feed/SKILL.md` as a repo-managed workflow skill using `skills-creator` guidance
- [x] 3.2 Make the `feed` skill explain the `ghostship-rss-bridge` to `feed` handoff for durable monitoring and triage workflows

## 4. Document and verify the integration

- [x] 4.1 Update `README.md`, `CHANGELOG.md`, and any affected repo guidance to describe `feed` as the main RSS reader and monitoring utility
- [x] 4.2 Verify the new `feed` package builds and that the relevant runtime/image outputs still evaluate or build cleanly
