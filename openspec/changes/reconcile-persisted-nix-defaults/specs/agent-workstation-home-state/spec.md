## MODIFIED Requirements

### Requirement: Downstream docs define the safe `/nix` persistence flow
The workstation docs SHALL describe a supported downstream procedure for first-use seeding and later reuse of `/nix` so operators can preserve the Nix store across restart and container replacement without hiding the image’s required store contents behind an unsafe empty mount. The supported reuse flow SHALL include boot-time reconciliation of the image-managed Nix default profile on reused non-empty `/nix` mounts.

#### Scenario: Named-volume guidance explains first use and reuse
- **WHEN** a downstream operator follows the documented named-volume pattern for `/nix`
- **THEN** the docs show how the volume is seeded on first use
- **AND** the docs show how the same `/nix` volume is reused across later image upgrades and container replacements
- **AND** the docs explain that later boots reconcile the image-managed Nix default profile into that reused volume

#### Scenario: Bind-mount guidance explains explicit seeding
- **WHEN** a downstream operator chooses a bind-mounted host path for `/nix`
- **THEN** the docs show the explicit one-time seeding step required before normal workstation use
- **AND** the docs warn that an unseeded empty bind mount is not a supported `/nix` startup path
- **AND** the docs explain how later boots reconcile the image-managed Nix default profile without overwriting unrelated user-managed Nix content
