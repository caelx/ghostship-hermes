## REMOVED Requirements

### Requirement: Hermes image ships a pinned Google Workspace CLI
**Reason**: The rebuilt image is removing non-essential preinstalled utilities from the default package set in favor of an upstream-aligned lean runtime.

**Migration**: Image docs and tests SHALL stop assuming `gws` is present on PATH in the default image.

### Requirement: Repo evaluation covers the Google Workspace CLI package
**Reason**: The rebuilt Hermes image no longer depends on the Google Workspace CLI as part of its default image wiring.

**Migration**: The repo MAY keep separate package wiring for `gws` if still useful outside the image, but the image contract and its validation SHALL no longer depend on it.
