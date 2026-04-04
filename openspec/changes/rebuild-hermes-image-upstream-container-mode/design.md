## Context

The original target for this change was an upstream-shaped `/data` plus `/data/home` runtime. That is no longer the active contract. The current approved direction is:

- keep the runtime as close to the upstream Hermes NixOS module as practical
- remove the Ghostship workstation layer completely
- persist the whole `/home/hermes` tree
- keep `/workspace` and `/nix` separate
- keep only the minimal dashboard plus `ghostship-*` utilities

The important upstream fact that still drives the implementation is that the NixOS module writes managed state under `${stateDir}/.hermes`. So the closest clean implementation of the new persistence model is:

- `stateDir = "/home/hermes"`
- `HOME = "/home/hermes"`
- `HERMES_HOME = "/home/hermes/.hermes"`

That is a repo-specific deviation from upstream container-mode docs, which otherwise keep managed state and HOME separate. It is approved and must be documented as such.

## Goals

- Make `/home/hermes` the persisted operator volume.
- Keep Hermes managed state and CLI profile state together under `/home/hermes/.hermes`.
- Keep `/workspace` as a separate persisted work volume.
- Keep `/nix` as a separate persisted Nix volume when mutable Nix installs should survive replacement.
- Keep the image lean and remove all repo-managed coding-agent extras and custom skills.
- Leave the final image fully tested and ready for manual dashboard inspection.

## Non-Goals

- Restoring the old Ghostship workstation runtime.
- Preserving `/data` or `/data/home` as active runtime paths.
- Reintroducing app refresh loops, seeded skills, persistent browser terminals, or honcho compatibility logic.
- Letting Hermes self-apply the system flake.

## Decisions

### 1. Persist the whole home volume

The runtime persists `/home/hermes` directly instead of maintaining a selected-directory symlink facade.

Why:

- later-installed tools keep their state automatically
- Hermes profiles are simpler to inspect
- the runtime loses a large amount of custom migration and symlink logic

Trade-off:

- this is less upstream-shaped than the `/data` split model
- it must stay explicitly documented as a repo-specific deviation

### 2. Use the Hermes NixOS module with `stateDir = "/home/hermes"`

This keeps the managed runtime declarative while letting the whole-home volume also carry the managed Hermes state.

Resulting layout:

- `/home/hermes/.hermes/config.yaml`
- `/home/hermes/.hermes/.env`
- `/home/hermes/.hermes/profiles/test`
- `/home/hermes/.hermes/profiles/coder`
- `/workspace`
- `/nix`

### 3. Keep the runtime identity fixed at `3000:3000`

The image keeps `hermes:hermes` at `3000:3000` and the runtime storage preparation ensures the persisted home, workspace, and Nix profile paths remain usable to that identity.

### 4. Keep the dashboard minimal and self-contained

The dashboard is not an upstream Hermes feature, so it stays a small approved Ghostship layer:

- static HTML/CSS/JS served by the controller itself
- old Hermes girl logo retained
- open terminal spawns a new focused tab
- close terminal removes the active tab
- no sessions means blank homepage
- `ttyd` stays loopback-only inside the container
- the dashboard binds on `0.0.0.0:7681`

### 5. Remove custom skill and workstation seeding

The image no longer seeds:

- repo `skills/`
- vendored skills
- Ghostship coding-agent environment defaults
- workstation app/update payloads

Hermes built-ins remain untouched.

### 6. Keep mutable user-level Nix

The runtime still supports:

- `nix profile install`
- `nix shell`
- user-installed binaries on PATH

This requires:

- persisted `/nix`
- prepared per-user Nix profile paths for `hermes`
- a working `nix-daemon.socket`
- `hermes` in Nix trusted users, which is a conscious security trade-off already accepted

## Risks

- Whole-home persistence can retain more state than a narrower facade. The repo mitigates that by keeping the base image lean and by documenting aggressive Docker cleanup.
- The repo-specific `stateDir = "/home/hermes"` choice diverges from upstream docs. The repo mitigates that by calling it out explicitly in runtime docs and specs.
- A brand-new empty `/nix` volume can still hide the image store. The repo mitigates that by documenting the required prepopulation step and validating ownership.

## Validation Plan

1. Build the image.
2. Import it into Docker.
3. Run the dashboard smoke test against:
   - persisted `/home/hermes`
   - persisted `/workspace`
   - persisted `/nix`
4. Run the full persistence test:
   - verify `HERMES_HOME=/home/hermes/.hermes`
   - verify `HOME=/home/hermes`
   - verify `test` and `coder`
   - verify `nix profile install` persistence
   - verify later-installed tool state persistence
   - verify multi-terminal dashboard behavior
5. Leave a final container running for manual dashboard inspection.
6. Aggressively prune stale Docker artifacts afterward so only the current needed image/container set remains.
