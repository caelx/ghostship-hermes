## ADDED Requirements

### Requirement: The image SHALL bundle upstream `feed` as an RSS monitoring utility
The Hermes image SHALL include upstream `feed` as a first-class packaged utility so Hermes can subscribe to feeds, fetch updates, search stored entries, and manage RSS triage state inside the container.

#### Scenario: `feed` is available in the image
- **WHEN** the image is built from this change
- **THEN** the resulting runtime MUST include the `feed` CLI on `PATH`
- **THEN** the packaged tool MUST come from a pinned upstream `feed` release rather than an ad hoc runtime install

### Requirement: `feed` state SHALL persist under profile-scoped Hermes storage
The `feed` SQLite database SHALL live under Hermes-managed profile storage so each Hermes profile has isolated feed state that survives container replacement.

#### Scenario: default profile uses persistent Hermes storage
- **WHEN** the default Hermes profile runs `feed`
- **THEN** `FEED_DB_PATH` MUST resolve under `/home/hermes/.hermes`
- **THEN** the database path MUST be stable across container replacement

#### Scenario: named profile gets isolated feed state
- **WHEN** a named Hermes profile runs `feed`
- **THEN** `FEED_DB_PATH` MUST resolve under that profile’s `HERMES_HOME`
- **THEN** its feed database MUST be isolated from other Hermes profiles

### Requirement: Hermes SHALL have a repo-managed `feed` skill for RSS monitoring workflows
The seeded Hermes skill pack SHALL include a repo-managed `feed` skill that teaches Hermes how to subscribe to feeds, fetch updates, search stored entries, and triage items as part of RSS monitoring workflows.

#### Scenario: `feed` skill explains durable triage workflows
- **WHEN** Hermes loads the `feed` skill
- **THEN** the skill MUST describe `feed` as the persistent RSS reader and monitoring engine
- **THEN** the skill MUST provide start-here and common-workflow guidance for adding feeds, fetching, scanning unread entries, searching history, and reading full entries

### Requirement: The `feed` skill SHALL integrate with RSS-Bridge workflows
The `feed` skill SHALL explain how to pair `ghostship-rss-bridge` with `feed` so agents can move from source discovery to durable feed monitoring.

#### Scenario: feed URL is generated from RSS-Bridge
- **WHEN** Hermes needs to monitor a site or source that requires RSS-Bridge
- **THEN** the skill MUST direct Hermes to use `ghostship-rss-bridge` to discover or build the canonical feed URL first
- **THEN** the skill MUST direct Hermes to add that feed URL to `feed` for ongoing monitoring and triage

### Requirement: Docs SHALL explain the `rss-bridge` plus `feed` division of responsibility
The repo documentation SHALL describe RSS-Bridge as the feed URL generation layer and `feed` as the persistent subscription, fetch, search, and monitoring layer.

#### Scenario: user reads image documentation
- **WHEN** a user reads the image documentation after this change
- **THEN** the docs MUST describe `feed` as the main RSS reader and monitoring utility in the image
- **THEN** the docs MUST explain how it complements, rather than replaces, `ghostship-rss-bridge`
