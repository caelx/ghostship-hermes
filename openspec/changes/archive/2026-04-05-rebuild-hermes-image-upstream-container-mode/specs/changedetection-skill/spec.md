## REMOVED Requirements

### Requirement: Hermes SHALL seed a repo-managed changedetection skill
**Reason**: The rebuilt image removes Ghostship-managed default skill seeding while retaining only Hermes built-in skills by default.

**Migration**: Runtime docs and tests SHALL stop assuming the image seeds a repo-managed `changedetection` skill into `~/.hermes/skills`.

### Requirement: The changedetection skill SHALL teach the `bws` to `ghostship-changedetection` workflow
**Reason**: The rebuilt image no longer ships the repo-managed `changedetection` skill as part of its default runtime contract.

**Migration**: Any future changedetection workflow guidance SHALL live in repository docs or optional user-installed skills rather than the image's default seeded skill inventory.

### Requirement: The changedetection skill SHALL follow inspect -> dry-run -> mutate -> verify workflows
**Reason**: The rebuilt image no longer ships the repo-managed `changedetection` skill as part of its default runtime contract.

**Migration**: The retained `ghostship-changedetection` CLI remains part of the image, but its usage guidance is no longer guaranteed through default skill seeding.
