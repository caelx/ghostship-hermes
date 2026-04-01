# ghostship-pricebuddy

`ghostship-pricebuddy` is a JSON-first CLI for the PriceBuddy REST API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `PRICEBUDDY_URL`
- `PRICEBUDDY_TOKEN`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Write and delete commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
- `ghostship-pricebuddy request`
- `ghostship-pricebuddy get_current_user`
- `ghostship-pricebuddy list_products`
- `ghostship-pricebuddy get_product`
- `ghostship-pricebuddy create_product`
- `ghostship-pricebuddy update_product`
- `ghostship-pricebuddy delete_product`
- `ghostship-pricebuddy list_product_sources`
- `ghostship-pricebuddy get_product_source`
- `ghostship-pricebuddy create_product_source`
- `ghostship-pricebuddy update_product_source`
- `ghostship-pricebuddy delete_product_source`
- `ghostship-pricebuddy search_product_source`
- `ghostship-pricebuddy search_all_product_sources`
- `ghostship-pricebuddy list_stores`
- `ghostship-pricebuddy get_store`
- `ghostship-pricebuddy create_store`
- `ghostship-pricebuddy update_store`
- `ghostship-pricebuddy delete_store`
- `ghostship-pricebuddy list_tags`
- `ghostship-pricebuddy get_tag`
- `ghostship-pricebuddy create_tag`
- `ghostship-pricebuddy update_tag`
- `ghostship-pricebuddy delete_tag`

## Examples
```bash
ghostship-pricebuddy get_current_user --pretty
ghostship-pricebuddy list_products --status p --include tags --pretty
ghostship-pricebuddy search_all_product_sources "steam deck"
ghostship-pricebuddy create_tag --name handhelds --dry-run --pretty
```
