## REMOVED Requirements

### Requirement: Hermes seeds a repo-managed Bitwarden skill
**Reason**: The rebuilt image removes Ghostship-managed default skill seeding while leaving only Hermes built-in skills untouched.

**Migration**: Runtime docs and tests SHALL stop assuming the default image seeds a Bitwarden skill into `~/.hermes/skills`.

### Requirement: Bitwarden skill defines the official stateless auth workflow
**Reason**: The rebuilt image no longer ships the repo-managed Bitwarden skill as part of its default runtime contract.

**Migration**: Any Bitwarden workflow guidance SHALL move to repository documentation or a separately installed skill rather than the image's default skill inventory.

### Requirement: Bitwarden skill covers shared secret retrieval conventions
**Reason**: The rebuilt image no longer ships the repo-managed Bitwarden skill as part of its default runtime contract.

**Migration**: Operators and future change proposals SHALL treat Bitwarden usage as optional runtime guidance, not default seeded image behavior.
