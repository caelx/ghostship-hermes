## REMOVED Requirements

### Requirement: Repo vendors the upstream Google Workspace skill catalog
**Reason**: The rebuilt image no longer ships vendored Google Workspace skills as part of its default runtime experience.

**Migration**: The repo MAY retain or separately manage the vendor tree if needed outside the default image, but runtime docs and tests SHALL stop depending on it.

### Requirement: Runtime seeds vendored Google Workspace skills without overwriting user content
**Reason**: The rebuilt image removes vendored skill seeding from the default runtime contract.

**Migration**: Runtime docs and tests SHALL stop assuming the image copies vendored Google Workspace skills into Hermes profiles.

### Requirement: Repo-managed local skills remain available alongside vendored skills
**Reason**: The rebuilt image removes both vendored Google Workspace skill seeding and Ghostship-managed local default skill seeding.

**Migration**: The default image skill contract SHALL be reduced to Hermes built-in skills only, unless a future change explicitly reintroduces additional default skills.
