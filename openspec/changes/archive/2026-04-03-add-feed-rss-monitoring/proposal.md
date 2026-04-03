## Why

The image already has `ghostship-rss-bridge` for turning sites into feed URLs, but it lacks a stateful RSS engine that can persist subscriptions, fetch updates, search historical entries, and help Hermes monitor feeds for events that matter over time. Adding upstream `feed` closes that gap and gives Hermes a local, profile-scoped RSS inbox that pairs naturally with RSS-Bridge.

## What Changes

- Add upstream `feed` to the image as a first-class packaged utility instead of a repo-owned `ghostship-*` wrapper.
- Persist the `feed` SQLite database under Hermes-managed profile storage so feed state survives container replacement and stays isolated per Hermes profile.
- Add a repo-managed `feed` skill, written with `skills-creator` guidance, that teaches Hermes how to combine RSS-Bridge feed URL generation with `feed` subscription, fetch, search, triage, and event-monitoring workflows.
- Document `feed` as the main RSS reader/monitoring tool in the image and clarify how it complements `ghostship-rss-bridge`.

## Capabilities

### New Capabilities
- `feed-monitoring`: Bundle upstream `feed`, wire persistent profile-scoped storage, and provide a Hermes skill for RSS monitoring and triage workflows that integrate with RSS-Bridge.

### Modified Capabilities

## Impact

- Affected code: `flake.nix`, `packages/hermes-image/`, `skills/`, and repo docs such as `README.md` and `CHANGELOG.md`
- Affected systems: image tool bundle, Hermes runtime environment, seeded skills, and Hermes profile persistence
- Dependencies: upstream `odysseus0/feed` release packaging and Hermes skill authoring aligned with `skills-creator`
