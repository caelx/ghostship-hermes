## Context

The image already packages a mix of repo-owned `ghostship-*` CLIs, first-party upstream tools like `bw` and `gws`, and a seeded skill set assembled from local and vendored sources. RSS-Bridge is already present as a typed utility for bridge discovery and canonical feed URL generation, but there is no stateful RSS reader in the image that can subscribe to feeds, persist unread state, search historical content, and give Hermes a long-lived event-monitoring surface.

Upstream `feed` is a good fit because it is a pure Go CLI with a single SQLite database, explicit `FEED_DB_PATH` configuration, and an upstream agent-oriented skill. The main integration constraints in this repo are: persistent state must live under Hermes-managed storage, profile isolation should follow `HERMES_HOME`, and the skill should be optimized for this image’s existing RSS-Bridge workflow rather than copied wholesale if doing so would hide important repo-specific guidance.

## Goals / Non-Goals

**Goals:**
- Package upstream `feed` as a first-class image utility.
- Persist the `feed` database under Hermes profile storage so each Hermes profile gets isolated feed state.
- Add a concise, repo-managed `feed` skill using `skills-creator` principles and tuned for RSS-Bridge plus `feed` workflows.
- Document `feed` as the main RSS triage and monitoring engine in the image.

**Non-Goals:**
- Build a `ghostship-feed` wrapper CLI.
- Replace `ghostship-rss-bridge`; RSS-Bridge remains the source-discovery and feed-URL construction layer.
- Add background schedulers, notifications, or daemonized polling beyond what `feed` already does on demand.
- Vendor the upstream `rss-digest` skill unchanged if that weakens Hermes-specific workflow guidance.

## Decisions

### Package `feed` as a first-class flake utility
`feed` should be added to `flake.nix` the same way the image already exposes `bw` and `gws`: as a directly packaged upstream tool that is appended into the image utility bundle.

Why:
- `feed` is not a repo-owned service API client, so a `ghostship-*` wrapper would add maintenance cost without improving the core experience.
- The tool is already designed for agent-facing CLI use and keeps its own SQLite-backed state locally.
- A pinned package keeps the image reproducible and aligns with how other non-wrapper utilities are handled.

Alternatives considered:
- Runtime install with `go install`. Rejected because it weakens reproducibility and image build determinism.
- A `ghostship-feed` wrapper. Rejected because the repo’s wrapper convention is for typed service clients, not for general-purpose upstream tools.

### Store the database under `$HERMES_HOME/feed/feed.db`
The runtime should export `FEED_DB_PATH` to `$HERMES_HOME/feed/feed.db`, not the upstream default under `~/.local/share/feed/feed.db`.

Why:
- `HERMES_HOME` is already profile-scoped in the container runtime.
- Hermes persistence is centered on `/home/hermes/.hermes`, which is already the declared volume for durable user state.
- This gives each Hermes profile its own feed subscriptions, unread state, and search index without extra plumbing.

Alternatives considered:
- Leave the upstream default path. Rejected because it would place the DB outside the repo’s intended persistence model.
- Set one image-wide shared path. Rejected because it would collapse all profiles into one feed state store.

### Write a repo-managed `feed` skill optimized for RSS-Bridge integration
The skill should live under `skills/feed/` and be written as a bespoke workflow skill using `skills-creator` guidance. It should teach Hermes to move from source discovery to feed subscription to triage and search.

Why:
- The repo already has `ghostship-rss-bridge`, and that integration is central to the user’s requested workflow.
- A Hermes-specific skill can emphasize the right sequence: discover or build feed URLs with RSS-Bridge, add them to `feed`, fetch and scan entries, then search or read content for event monitoring.
- The upstream `rss-digest` skill is useful inspiration, but it assumes a generic install surface and does not explain the repo’s existing RSS-Bridge layer.

Alternatives considered:
- Vendor upstream `rss-digest` unchanged. Rejected because it misses the repo-specific bridge-to-reader workflow.
- Add a large reference bundle. Rejected because the workflow is compact enough to live cleanly in one `SKILL.md`.

### Keep RSS-Bridge and `feed` as separate responsibilities
The resulting image should present `ghostship-rss-bridge` as the feed-source generation tool and `feed` as the durable monitoring and triage engine.

Why:
- RSS-Bridge is action-driven and stateless; it generates feed URLs from upstream site schemas.
- `feed` is stateful and optimized for storing, fetching, triaging, and searching entries over time.
- Keeping those roles explicit will make the skills easier for agents to trigger correctly.

Alternatives considered:
- Collapse the guidance into one RSS skill. Rejected because it would blur discovery and persistent triage responsibilities.

## Risks / Trade-offs

- [Skill overlap with RSS-Bridge] → Keep `rss-bridge` focused on URL generation and make `feed` explicitly about stored subscriptions, fetches, and triage.
- [Upstream skill drift] → Use the upstream `rss-digest` skill as input, but maintain the repo-managed `feed` skill as the canonical Hermes workflow for this image.
- [Profile-state confusion] → Document that `FEED_DB_PATH` is profile-scoped under `HERMES_HOME`, not global across all Hermes profiles.
- [Packaging churn] → Pin a specific upstream `feed` release tag and keep the package minimal so updates remain low-risk.

## Migration Plan

1. Add a pinned `feed` package to the flake and include it in the image utility set.
2. Export `FEED_DB_PATH` in the runtime and ensure the parent directory is created under `HERMES_HOME`.
3. Add a repo-managed `skills/feed/SKILL.md`.
4. Update README and changelog entries to explain the `rss-bridge` plus `feed` workflow.
5. Verify the package builds and the runtime/image outputs still evaluate cleanly.

Rollback strategy:
- Remove the `feed` package from the flake and image bundle, drop the runtime `FEED_DB_PATH` export, and remove the skill/docs additions.

## Open Questions

- Whether the image should also seed a starter OPML file or leave feed population entirely to RSS-Bridge discovery and explicit `feed add` / `feed import` workflows.
