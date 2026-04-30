# Ghostship Wiki Schema

## Domain

Ghostship Hermes runtime knowledge: the workstation image, local tools, model
configuration, browser automation, and reachable service APIs on `chill-penguin`.

## Conventions

- Markdown files use lowercase names with hyphens.
- API references live under `api/`.
- Keep examples generic and reference environment variable names, never secret values.
- Prefer direct API contracts and small code examples over workflow instructions.
- Add new agent-generated notes outside repo-managed files, or add them under a new
  directory that is not copied from the image seed.
- When updating a managed page, keep it short enough for an agent to scan quickly.

## Managed Content

The image owns the files copied from `/opt/ghostship/ghostship-wiki`. Boot sync
overwrites those files. It does not delete files that are absent from the image
source, so agent-maintained pages survive image replacement.

## Source Quality

- `docs/api` contains restored OpenAPI/Swagger mirrors and Markdown API sheets.
- `api/firecrawl.md` uses the public Firecrawl API docs plus the deployed
  `FIRECRAWL_API_URL` / `FIRECRAWL_API_KEY` environment contract.
- Service environment mapping is derived from the deployed Hermes `.env` key set
  on `chill-penguin`; values are intentionally omitted.
