## REMOVED Requirements

### Requirement: The image SHALL bundle upstream `feed` as an RSS monitoring utility
**Reason**: The rebuilt image is intentionally shrinking the default package set and keeping only upstream Hermes essentials, the minimal runtime surface, and retained `ghostship-*` utilities.

**Migration**: Image docs and tests SHALL stop assuming `feed` is present on PATH in the default image.

### Requirement: `feed` state SHALL persist under profile-scoped Hermes storage
**Reason**: The rebuilt image no longer treats `feed` as a default bundled runtime utility.

**Migration**: Any future `feed` usage SHALL be documented as an optional separately installed workflow rather than built-in image behavior.

### Requirement: Hermes SHALL have a repo-managed `feed` skill for RSS monitoring workflows
**Reason**: The rebuilt image removes Ghostship-managed default skill seeding.

**Migration**: Runtime docs and tests SHALL stop assuming the image seeds a repo-managed `feed` skill by default.

### Requirement: The `feed` skill SHALL integrate with RSS-Bridge workflows
**Reason**: The rebuilt image removes the repo-managed `feed` skill from the default runtime contract.

**Migration**: Any future RSS workflow guidance SHALL live outside the image's default seeded skill inventory.

### Requirement: Docs SHALL explain the `rss-bridge` plus `feed` division of responsibility
**Reason**: The default image no longer guarantees that `feed` is installed and available as part of the bundled runtime.

**Migration**: Documentation SHALL be updated to reflect the lean default package set and any optional RSS tooling separately.
