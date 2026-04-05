## REMOVED Requirements

### Requirement: Hermes image ships the official Bitwarden CLI
**Reason**: The rebuilt image is reducing the default package set to upstream Hermes essentials, retained `ghostship-*` utilities, and the minimal browser/runtime surface. `bws` is no longer part of the required default image inventory.

**Migration**: Image docs and tests SHALL stop assuming `bws` is present on PATH in the default image.

### Requirement: Hermes runtime supports a documented Bitwarden appdata location
**Reason**: The rebuilt image no longer defines a default preinstalled Bitwarden runtime path contract.

**Migration**: Any future Bitwarden usage in this image SHALL be documented as an operator-managed or separately installed workflow rather than a built-in runtime convention.
