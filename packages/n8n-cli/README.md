# ghostship-n8n

`ghostship-n8n` is a JSON-first CLI for the official n8n Public API. Commands mirror the upstream operation inventory in snake_case and keep the CLI contract consistent with the other repo-owned `ghostship-*` tools.

## Environment
- `N8N_URL`
- `N8N_API_KEY`
- `N8N_PUBLIC_API_ENDPOINT` optional, defaults to `api`
- `N8N_PUBLIC_API_VERSION` optional, defaults to `v1`

## Command Contract
- Primary commands use snake_case names derived from the official n8n Public API operation inventory.
- Dedicated commands accept repeated `--path-param name=value`, repeated `--query-param key=value`, and optional `--body-json '{...}'` where needed.
- Use `request` only for debugging or temporary upstream gaps.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Write and delete commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
- `ghostship-n8n request`
- `ghostship-n8n activate_workflow`
- `ghostship-n8n add_users_to_project`
- `ghostship-n8n archive_workflow`
- `ghostship-n8n change_role`
- `ghostship-n8n change_user_role_in_project`
- `ghostship-n8n create_credential`
- `ghostship-n8n create_data_table`
- `ghostship-n8n create_project`
- `ghostship-n8n create_tag`
- `ghostship-n8n create_user`
- `ghostship-n8n create_variable`
- `ghostship-n8n create_workflow`
- `ghostship-n8n deactivate_workflow`
- `ghostship-n8n delete_credential`
- `ghostship-n8n delete_data_table`
- `ghostship-n8n delete_data_table_rows`
- `ghostship-n8n delete_execution`
- `ghostship-n8n delete_project`
- `ghostship-n8n delete_tag`
- `ghostship-n8n delete_user`
- `ghostship-n8n delete_user_from_project`
- `ghostship-n8n delete_variable`
- `ghostship-n8n delete_workflow`
- `ghostship-n8n generate_audit`
- `ghostship-n8n get_credential_type`
- `ghostship-n8n get_credentials`
- `ghostship-n8n get_data_table`
- `ghostship-n8n get_data_table_rows`
- `ghostship-n8n get_discover`
- `ghostship-n8n get_execution`
- `ghostship-n8n get_execution_tags`
- `ghostship-n8n get_executions`
- `ghostship-n8n get_installed_packages`
- `ghostship-n8n get_project_users`
- `ghostship-n8n get_projects`
- `ghostship-n8n get_tag`
- `ghostship-n8n get_tags`
- `ghostship-n8n get_user`
- `ghostship-n8n get_users`
- `ghostship-n8n get_variables`
- `ghostship-n8n get_workflow`
- `ghostship-n8n get_workflow_tags`
- `ghostship-n8n get_workflow_version`
- `ghostship-n8n get_workflows`
- `ghostship-n8n insert_data_table_rows`
- `ghostship-n8n install_package`
- `ghostship-n8n list_data_tables`
- `ghostship-n8n pull`
- `ghostship-n8n retry_execution`
- `ghostship-n8n stop_execution`
- `ghostship-n8n stop_many_executions`
- `ghostship-n8n transfer_credential`
- `ghostship-n8n transfer_workflow`
- `ghostship-n8n unarchive_workflow`
- `ghostship-n8n uninstall_package`
- `ghostship-n8n update_credential`
- `ghostship-n8n update_data_table`
- `ghostship-n8n update_data_table_rows`
- `ghostship-n8n update_execution_tags`
- `ghostship-n8n update_package`
- `ghostship-n8n update_project`
- `ghostship-n8n update_tag`
- `ghostship-n8n update_variable`
- `ghostship-n8n update_workflow`
- `ghostship-n8n update_workflow_tags`
- `ghostship-n8n upsert_data_table_row`
