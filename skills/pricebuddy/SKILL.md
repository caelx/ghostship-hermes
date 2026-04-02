---
name: pricebuddy
description: Operate PriceBuddy from the Hermes image with `ghostship-pricebuddy`. Use when inspecting products, stores, tags, and product sources; running source searches; or performing guarded PriceBuddy mutations with the typed CLI and JSON output.
---

# PriceBuddy Skill

Use `ghostship-pricebuddy` when you need to inspect or change PriceBuddy state with typed JSON-first commands.

## Prerequisites

- `PRICEBUDDY_URL`
- `PRICEBUDDY_TOKEN`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete commands support `--dry-run`.
- Product sources and stores often require nested scraping strategy data, so inspect command help before mutating.

## Start Here

- Auth and identity check: `ghostship-pricebuddy get_current_user`
- Browse products: `ghostship-pricebuddy list_products`
- Browse stores and tags before product writes: `ghostship-pricebuddy list_stores`, `ghostship-pricebuddy list_tags`
- Inspect product sources before broader search work: `ghostship-pricebuddy list_product_sources`

## Common Workflows

- Add or update a product:
  - `list_products` to avoid duplicates.
  - `list_stores` and `list_tags` to discover supporting IDs.
  - `create_product --dry-run ...`, then `create_product ...` for new products.
  - `update_product --dry-run ...`, then `update_product ...` for changes.
  - `get_product <id>` to verify the resulting state.
- Work with product sources:
  - `list_product_sources`
  - `get_product_source <id>` to inspect an existing definition.
  - `search_product_source <id> ...` or `search_all_product_sources ...` before changing source definitions.
  - `create_product_source --dry-run ...` or `update_product_source --dry-run ...`, then the real mutation once the shape is correct.
  - Re-read `get_product_source <id>` after mutation.
- Safe write-path testing:
  - Prefer `create_tag`, `update_tag`, and `delete_tag` for disposable write-path checks.
  - `list_tags`
  - `create_tag --dry-run ...`, then `create_tag ...`
  - `delete_tag --dry-run <id>`, then `delete_tag <id>`

## Mutation Guardrails

- Confirm related IDs for stores, tags, and product sources before product mutations.
- Use `--dry-run` for every create, update, and delete command.
- Read `ghostship-pricebuddy <command> --help` when nested strategy flags are involved instead of guessing the request shape.
- Verify post-state with `get_*` or `list_*` commands after changes.

## Fallback

- Use `ghostship-pricebuddy request` only when a dedicated command does not exist.
