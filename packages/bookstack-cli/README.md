# ghostship-bookstack

`ghostship-bookstack` is a JSON-first CLI for the BookStack REST API. Commands mirror the verified upstream operation inventory from the repo's committed BookStack docs snapshot, with multipart uploads and binary export/image endpoints handled through the same CLI surface.

## Environment
- `BOOKSTACK_URL`
- `BOOKSTACK_TOKEN_ID`
- `BOOKSTACK_TOKEN_SECRET`

## Command Contract
- Primary commands use snake_case names derived from the committed BookStack docs inventory.
- Use `request` as the escape hatch for temporary upstream drift or debugging.
- Output is JSON by default. Binary response operations require `--output` and then return JSON metadata about the saved file.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Write and delete commands accept `--dry-run` and print the exact request object instead of calling the API.
- Multipart operations accept repeated `--form-param key=value` and `--file key=path` options.

## Commands
- `ghostship-bookstack request`
- `ghostship-bookstack docs_display`
- `ghostship-bookstack docs_json`
- `ghostship-bookstack pages_list`
- `ghostship-bookstack pages_create`
- `ghostship-bookstack pages_read`
- `ghostship-bookstack pages_update`
- `ghostship-bookstack pages_delete`
- `ghostship-bookstack pages_export_html`
- `ghostship-bookstack pages_export_pdf`
- `ghostship-bookstack pages_export_plain_text`
- `ghostship-bookstack pages_export_markdown`
- `ghostship-bookstack pages_export_zip`
- `ghostship-bookstack chapters_list`
- `ghostship-bookstack chapters_create`
- `ghostship-bookstack chapters_read`
- `ghostship-bookstack chapters_update`
- `ghostship-bookstack chapters_delete`
- `ghostship-bookstack chapters_export_html`
- `ghostship-bookstack chapters_export_pdf`
- `ghostship-bookstack chapters_export_plain_text`
- `ghostship-bookstack chapters_export_markdown`
- `ghostship-bookstack chapters_export_zip`
- `ghostship-bookstack books_list`
- `ghostship-bookstack books_create`
- `ghostship-bookstack books_read`
- `ghostship-bookstack books_update`
- `ghostship-bookstack books_delete`
- `ghostship-bookstack books_export_html`
- `ghostship-bookstack books_export_pdf`
- `ghostship-bookstack books_export_plain_text`
- `ghostship-bookstack books_export_markdown`
- `ghostship-bookstack books_export_zip`
- `ghostship-bookstack shelves_list`
- `ghostship-bookstack shelves_create`
- `ghostship-bookstack shelves_read`
- `ghostship-bookstack shelves_update`
- `ghostship-bookstack shelves_delete`
- `ghostship-bookstack attachments_list`
- `ghostship-bookstack attachments_create`
- `ghostship-bookstack attachments_read`
- `ghostship-bookstack attachments_update`
- `ghostship-bookstack attachments_delete`
- `ghostship-bookstack audit_log_list`
- `ghostship-bookstack comments_list`
- `ghostship-bookstack comments_create`
- `ghostship-bookstack comments_read`
- `ghostship-bookstack comments_update`
- `ghostship-bookstack comments_delete`
- `ghostship-bookstack content_permissions_read`
- `ghostship-bookstack content_permissions_update`
- `ghostship-bookstack image_gallery_list`
- `ghostship-bookstack image_gallery_create`
- `ghostship-bookstack image_gallery_read_data_for_url`
- `ghostship-bookstack image_gallery_read`
- `ghostship-bookstack image_gallery_read_data`
- `ghostship-bookstack image_gallery_update`
- `ghostship-bookstack image_gallery_delete`
- `ghostship-bookstack imports_list`
- `ghostship-bookstack imports_create`
- `ghostship-bookstack imports_read`
- `ghostship-bookstack imports_run`
- `ghostship-bookstack imports_delete`
- `ghostship-bookstack recycle_bin_list`
- `ghostship-bookstack recycle_bin_restore`
- `ghostship-bookstack recycle_bin_destroy`
- `ghostship-bookstack roles_list`
- `ghostship-bookstack roles_create`
- `ghostship-bookstack roles_read`
- `ghostship-bookstack roles_update`
- `ghostship-bookstack roles_delete`
- `ghostship-bookstack search_all`
- `ghostship-bookstack system_read`
- `ghostship-bookstack users_list`
- `ghostship-bookstack users_create`
- `ghostship-bookstack users_read`
- `ghostship-bookstack users_update`
- `ghostship-bookstack users_delete`

## Runtime Topology
- Prefer an internal BookStack API origin for Hermes runtime validation, such as `http://bookstack`, when the service is available on the container network.
- If `BOOKSTACK_URL` points at an external Cloudflare-protected hostname, the runtime must also provide the required Cloudflare Access headers or the CLI will correctly surface the redirect/auth failure.
- A minimal smoke check after deploy is:
  - `ghostship-bookstack --timeout 30 books_list --pretty`
  - `ghostship-bookstack --timeout 30 request GET /books --pretty`
  - `ghostship-bookstack --timeout 30 docs_display --pretty`

## Examples
```fish
ghostship-bookstack pages_list --pretty
ghostship-bookstack books_create --body-json '{"name":"Runbook","description":"Operator docs"}' --dry-run --pretty
ghostship-bookstack attachments_create --form-param name=guide.pdf --form-param uploaded_to=123 --file file=./guide.pdf --dry-run --pretty
ghostship-bookstack pages_export_markdown --path-param id=42 --output ./page-42.md --pretty
```
