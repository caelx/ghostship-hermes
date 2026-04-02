## Context

The repo currently ships a broad set of Hermes skills under `skills/`, but most service skills are lightweight command catalogs with only minimal workflow guidance. They are consistent, but they do not use the available context budget well: trigger descriptions are often narrow, operator decision-making is underspecified, and mutation workflows are not consistently structured around inspect, dry-run, mutate, and verify steps.

The requested rewrite should optimize the skill pack using `skills-creator` guidance while preserving the repo's CLI contract and service-specific safety expectations. The user also wants domain-specific guidance rather than maximum uniformity, and wants the upstream `agent-browser` skill copied as-is instead of being rewritten into the repo's current CloakBrowser-specific format.

## Goals / Non-Goals

**Goals:**
- Rewrite the repo-managed skills around family templates that emphasize full operator workflows.
- Improve skill trigger quality by strengthening frontmatter descriptions.
- Preserve domain-specific guidance instead of collapsing every service into the same generic command sheet.
- Keep workflow-specialized skills bespoke when a family template would hide important context.
- Copy the provided upstream `agent-browser` skill content unchanged.

**Non-Goals:**
- Change the underlying `ghostship-*` CLI APIs or command names.
- Add new CLIs, new service integrations, or new runtime behavior.
- Rebuild every skill into a large multi-file reference package if the content fits cleanly in `SKILL.md`.
- Preserve the current CloakBrowser-specific `agent-browser` skill wording.

## Decisions

### Organize the rewrite around family templates
The skills should be grouped into a small number of workflow families:
- media managers: `sonarr`, `radarr`, `bazarr`, `prowlarr`
- library and observability: `plex`, `tautulli`, `romm`, `grimmory`
- download clients: `qbittorrent`, `nzbget`, `pyload-ng`
- infra and access: `cloakbrowser`, `flaresolverr`, `searxng`, `synology`

Each family template should share section structure while leaving the actual operator guidance domain-specific.

Alternative considered:
- Rewrite every skill independently. Rejected because it would make the pack inconsistent and harder to maintain.
- Use one universal template for all service skills. Rejected because it would flatten domain differences and weaken operator guidance.

### Optimize for full operator workflows, not command inventories
Each rewritten service skill should emphasize task sequences:
- start with safe inspection
- identify the relevant object IDs or current state
- use `--dry-run` before meaningful writes or deletes where available
- execute the mutation
- re-read state to verify the outcome

Alternative considered:
- Keep command-dump-style skills with only minor copy edits. Rejected because that would not materially improve skill quality.

### Keep selected skills bespoke
`current-environment`, `hermes-nix`, `pricebuddy`, and `rss-bridge` should remain bespoke because they encode workflow or environment guidance that does not fit the service-family templates well.

Alternative considered:
- Force every skill into a family template. Rejected because it would reduce useful guidance for specialized tools.

### Copy `agent-browser` as-is
The supplied upstream `agent-browser` skill should replace the repo copy without reinterpretation so it stays aligned with the richer upstream workflow and reference structure.

Alternative considered:
- Adapt the upstream skill to the repo's current CloakBrowser-only stance. Rejected because the user explicitly wants the upstream skill copied as-is.

### Keep progressive disclosure light
Most rewritten skills should remain single-file `SKILL.md` documents because the underlying CLIs already provide the deterministic command surface. Additional references should only be introduced when a skill would otherwise become too large or too diffuse.

## Risks / Trade-offs

- [Template overreach] → Keep family structure consistent, but tune guidance per domain instead of mass-applying identical wording.
- [Trigger regressions] → Rewrite frontmatter descriptions carefully so they mention both the tool and the situations that should trigger it.
- [Overlong skills] → Keep command lists short and focus on start-here paths, common workflows, and fallback commands.
- [Agent-browser mismatch with repo assumptions] → Copy the upstream skill exactly as requested and treat any repo-specific constraints as a follow-up change if needed.

## Migration Plan

1. Define the family templates and bespoke exceptions.
2. Rewrite each repo-managed skill into its new structure.
3. Replace the repo `agent-browser` skill with the supplied upstream version.
4. Review the rewritten pack for consistency, trigger quality, and unnecessary verbosity.

Rollback strategy:
- Restore the previous `skills/` contents from git if the rewritten skills degrade trigger quality or remove essential workflow guidance.

## Open Questions

- Whether the upstream `agent-browser` skill should remain fully generic long term or later gain a separate repo-specific companion skill for CloakBrowser integration.
