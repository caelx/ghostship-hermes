# Environment

## State Roots

- `HOME=/home/hermes`: persisted user home and tool state.
- `HERMES_HOME=/home/hermes/.hermes`: Hermes config, skills, auth, memory, and `.env`.
- `/workspace`: persisted work-products mount.
- `/nix`: persisted Nix store/profile area.
- `/opt/hermes`: image-owned Hermes install.
- `/opt/ghostship`: image-owned Ghostship assets, helpers, browser binaries, and wiki seed.

## Runtime Env

The boot process writes managed Hermes-facing environment variables to both:

- `/run/ghostship/hermes.env`
- `/home/hermes/.hermes/.env`

Existing non-managed keys in `.env` are preserved. Image-owned keys such as
`HOME`, `HERMES_HOME`, `PATH`, `GHOSTSHIP_*`, `NPM_CONFIG_PREFIX`, and XDG roots
are not downstream knobs.

## Service Discovery

Most service APIs are reached by container DNS names on the shared Podman network,
for example `http://prowlarr:9696`, `http://pyload:8000`, and
`http://firecrawl-api:3002`. Use the `*_URL` variables from `.env` rather than
hardcoding hosts.

Never print token values. Load them from `.env` in process memory and pass them
as headers, query params, or login fields according to [[api/service-env]].
