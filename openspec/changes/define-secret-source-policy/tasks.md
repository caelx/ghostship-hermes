## 1. Central policy documentation

- [x] 1.1 Update `README.md` so it distinguishes Bitwarden-managed secrets from local environment/config values and explains that utility env vars are the runtime interface, not the durable source of truth for secrets.
- [x] 1.2 Update `docs/python-utilities.md` so new `ghostship-*` packages inherit the same source-of-truth policy for bootstrap secrets, Bitwarden-managed credentials, and local topology values.
- [x] 1.3 Update `AGENTS.md` to record the durable policy for `BWS_ACCESS_TOKEN`, Bitwarden-managed service and website credentials, and local env/config topology values.

## 2. Skill and workflow alignment

- [x] 2.1 Update `skills/bitwarden/SKILL.md` so it teaches the bootstrap-secret boundary, Bitwarden-managed secret classes, local topology exceptions, and narrow per-command secret materialization.
- [x] 2.2 Review repo-managed service skills and update any examples or wording that still imply secrets should live primarily in shared env files rather than being fetched from `bws`.

## 3. Verification and release hygiene

- [x] 3.1 Search the repo for outdated env-only guidance and reconcile any remaining conflicts in central docs or skill text.
- [x] 3.2 Update `CHANGELOG.md` with the new secrets/config policy guidance and documentation alignment.
- [x] 3.3 Verify the updated docs and skill examples remain Fish-compatible and consistent with the current `ghostship-*` runtime env-var contract.
