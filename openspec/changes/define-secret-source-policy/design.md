## Context

The repo already standardizes `bws` as the supported Bitwarden integration and treats `BWS_ACCESS_TOKEN` as an operator-provided input, but several docs still describe environment variables as the primary source of configuration for `ghostship-*` utilities. That leaves an unclear boundary between durable secret storage, runtime process configuration, and non-secret local environment data such as service URLs and profile-specific topology.

This ambiguity now matters more because the repo is expected to manage both API/service credentials and website credentials. Those credentials do not all behave the same way, but they still need one clear policy that future docs, skills, and utility packages can follow.

## Goals / Non-Goals

**Goals:**
- Define one repo-wide source-of-truth policy for bootstrap secrets, Bitwarden-managed secrets, and local environment/config values.
- Preserve the current `ghostship-*` runtime interface so existing utilities can continue to consume environment variables without immediate code churn.
- Clarify that website credentials can live in Bitwarden when they fit a machine-account or scripted workflow, while documenting the boundary for credentials that do not.
- Align central docs and repo-managed skills so they teach the same workflow and the same decision boundary.

**Non-Goals:**
- Rework every existing utility to call `bws` directly instead of consuming environment variables.
- Eliminate environment variables as a runtime interface for `ghostship-*` utilities.
- Introduce a full credential-broker implementation in this change.
- Force all interactive website authentication patterns into Bitwarden-managed automation workflows.

## Decisions

### Use a three-tier source-of-truth model

The repo policy will distinguish three classes of values:

1. Bootstrap secret inputs:
   - `BWS_ACCESS_TOKEN` remains the required operator-injected secret.
   - `BWS_SERVER_URL` remains optional runtime config for self-hosted Bitwarden.
2. Bitwarden-managed secrets:
   - Service API keys, usernames/passwords, bearer tokens, cookie seeds, OAuth client secrets, and website credentials that fit a machine-account workflow live in Bitwarden Secrets Manager.
   - When a command still expects environment variables, those values are materialized from `bws` only for the relevant command or workflow.
3. Local environment/config values:
   - Service URLs, hostnames, ports, profile names, workspace paths, and similar local topology stay in env/config by default rather than Bitwarden.

This keeps Bitwarden focused on real secrets, keeps local deployment topology easy to override, and avoids a large ambient shell environment loaded with every secret in the estate.

Alternatives considered:
- Keep all service and website values in one large shared environment. Rejected because it preserves broad secret exposure and does not use Bitwarden as the source of truth.
- Move all config, including local topology, into Bitwarden. Rejected because non-secret per-environment routing data changes for local operations more often and does not benefit from secret storage.

### Keep environment variables as the utility consumption interface

The shared CLI contract already expects environment variables, and existing `ghostship-*` packages are written around that model. This change will treat those variables as the runtime consumption layer, not the durable source of truth for secrets.

That means the policy can say both of the following without contradiction:
- Secrets belong in Bitwarden.
- `ghostship-*` commands may still receive those secrets through environment variables at process launch time.

Alternatives considered:
- Require each utility to add first-class `bws` integration immediately. Rejected because it adds broad implementation churn without being necessary to define the policy or update the docs.

### Treat website credentials as Bitwarden-managed only when they fit automation

The policy will explicitly include website credentials as Bitwarden-managed secrets when they are compatible with automation, such as usernames/passwords, app passwords, bearer tokens, cookies, or similar secrets. The policy will also explicitly exclude interactive-only authentication models such as passkeys, WebAuthn hardware prompts, or human SSO sessions from the default Bitwarden automation pattern.

This keeps the policy realistic and avoids overpromising support for website login flows that cannot be represented safely as ordinary machine secrets.

Alternatives considered:
- Treat website credentials as a separate policy outside Bitwarden. Rejected because the user wants one consistent secret system and many website workflows still reduce to machine secrets.
- Treat all website auth as compatible with the same pattern. Rejected because some flows are fundamentally interactive and should not be documented as normal `bws`-to-env workflows.

### Update the central docs and seeded Bitwarden skill together

The authoritative behavior in practice is split across `README.md`, `docs/python-utilities.md`, `AGENTS.md`, and the repo-managed `bitwarden` skill. This change will update all of them together so future package work and operator workflows inherit the same language and the same examples.

Alternatives considered:
- Update only `README.md`. Rejected because repo maintainers and agents also rely directly on `AGENTS.md`, `docs/python-utilities.md`, and seeded skills.

## Risks / Trade-offs

- [Docs continue to mix “env config” with “secret source of truth”] -> Update the central docs and Bitwarden skill in one change and reuse the same terminology in each file.
- [Maintainers may overuse Bitwarden for non-secret local topology] -> Define a default rule that URLs, hosts, ports, profile names, and paths stay in env/config unless there is a clear secret value involved.
- [Operators may assume all website auth fits the same automation pattern] -> Document explicit exclusions for interactive-only auth models.
- [Future utilities may interpret the policy inconsistently] -> Add the repo-wide policy to the Python utility guidance so new packages inherit the same baseline.

## Migration Plan

1. Add a new repo policy spec that defines the source-of-truth split.
2. Update the existing Bitwarden skill spec so the seeded skill teaches the same boundary.
3. Revise central docs to align with the policy, especially places that currently imply environment variables are the durable source of configuration.
4. Keep the existing utility runtime interface unchanged so there is no immediate breaking change for operators.

Rollback:
- Revert the policy and doc updates together so the repo returns to the prior “env vars only” guidance.

## Open Questions

- Should a later change add a shared helper such as `ghostship-secrets exec ...` to materialize Bitwarden secrets for child processes automatically?
- Do any existing package READMEs need service-specific updates beyond the central docs in this change?
