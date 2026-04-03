## Why

The repo currently mixes two partially overlapping models: `ghostship-*` utilities consume environment variables at runtime, while the Hermes runtime and seeded Bitwarden skill now treat Bitwarden Secrets Manager as the preferred source of service credentials. That ambiguity makes it unclear which values belong in Bitwarden, which belong in local env/config, and how website credentials should be handled alongside API secrets.

## What Changes

- Define a repo policy that separates bootstrap secrets, Bitwarden-managed secrets, and local environment/config values.
- Standardize `BWS_ACCESS_TOKEN` as the only operator-injected bootstrap secret and treat Bitwarden Secrets Manager as the source of truth for service credentials and website automation credentials that fit a machine-account workflow.
- Clarify that `ghostship-*` utilities may continue to consume environment variables as their runtime interface, but those variables should usually be materialized from Bitwarden only for the specific command or workflow that needs them.
- Define local environment/config values such as service URLs, hostnames, ports, profile names, and workspace-specific paths as non-secret topology that should stay in env/config rather than Bitwarden by default.
- Update repo documentation and seeded skills so they consistently teach the same source-of-truth rules and the same decision boundary for secrets versus local config.

## Capabilities

### New Capabilities
- `secret-source-policy`: Define the repo-wide policy for what belongs in Bitwarden Secrets Manager versus local environment/config, including bootstrap secret handling and per-command secret materialization guidance.

### Modified Capabilities
- `bitwarden-cli-skill`: Expand the Bitwarden skill requirements so they explicitly teach the repo policy for bootstrap secrets, Bitwarden-managed service and website credentials, and local topology values that should remain outside Bitwarden.

## Impact

- `README.md`, `docs/python-utilities.md`, `AGENTS.md`, and repo-managed skills that currently describe environment-variable configuration or Bitwarden workflows
- The operator workflow for provisioning service credentials, website credentials, and local environment data into Hermes
- Future `ghostship-*` utilities and helper tooling that need a clear source-of-truth contract for configuration and secrets
