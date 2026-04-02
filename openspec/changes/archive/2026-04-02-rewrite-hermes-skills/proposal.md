## Why

The repo-managed Hermes skills are consistent but not optimized for trigger quality or full operator workflows. Most service skills are still thin command catalogs, which makes them less effective than they could be for agent decision-making, safe mutations, and domain-specific diagnosis.

## What Changes

- Rewrite the repo-managed skills around family templates instead of flat command-reference patterns.
- Emphasize domain-specific operator workflows, including read, mutate, diagnose, and verify sequences for each service family.
- Keep workflow-oriented skills bespoke where a family template would hide important container or service-specific guidance.
- Replace the current repo `agent-browser` skill with the provided upstream `agent-browser` skill content unchanged.
- Preserve the repo CLI contract in every rewritten service skill: exact snake_case commands, `--timeout`, `--dry-run` for write/delete operations where available, and passthrough commands only as fallback escape hatches.

## Capabilities

### New Capabilities
- `repo-skills`: Define the structure, workflow guidance, and exception rules for repo-managed Hermes skills, including family-template rewrites and the upstream `agent-browser` copy-through rule.

### Modified Capabilities

## Impact

- Affected code: `skills/`
- Affected docs/process: the repo-managed skill pack seeded into Hermes profiles
- Dependencies: the provided upstream `agent-browser` skill content and the `skills-creator` guidance used to optimize the rewritten skills
- Systems: Hermes skill triggering, operator guidance, and service-specific task execution inside the container
