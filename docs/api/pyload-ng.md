# pyLoad-ng API Spec Sheet

Canonical artifacts:
- Raw spec mirror: [pyload-openapi.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/pyload-openapi.json)
- Companion reference: this file

## Service Identity

- Product: pyLoad-ng
- Version mirrored in repo: `1.2.0`
- Base API URL: `http(s)://<host>/api`
- Primary auth: `X-API-Key` header on `/api/*`; basic auth only gates `/api` docs and the Swagger export

## Raw Spec Summary

- Format: OpenAPI JSON
- Path count: `84`
- Canonical source quality: official OpenAPI plus repo summary

## Live Validation Notes

- Anonymous `/api/*` requests returned `401 Invalid API credentials` on the deployed instance.
- HTTP Basic auth succeeded for `/api` and `/api/openapi.json`, but still returned `401 Invalid API credentials` for `/api/status_server`.
- The deployed instance advertises `ApiKeyAuth` with header name `X-API-Key` and stores API credentials in the `apikeys` database table.
- `ghostship-pyload-ng` therefore uses `PYLOAD_API_KEY` for authenticated API calls.

## Full Endpoint and Use-Case Inventory

The inventory below is taken directly from the mirrored upstream machine-readable specification.

### pyLoad REST
- `POST /api/add_files`: Adds files to specific package.
- `POST /api/add_package`: Adds a package, with links to desired destination.
- `POST /api/add_user`: creates new user login.
- `POST /api/change_password`: changes password for specific user.
- `POST /api/check_and_add_packages`: Checks online status, retrieves names, and will add packages. Because of these packages are not added immediately, only for internal use.
- `GET /api/check_auth`: Check authentication and returns details.
- `POST /api/check_online_status`: Initiates online status check.
- `POST /api/check_online_status_container`: checks online status of urls and a submitted container file.
- `POST /api/check_urls`: Gets urls and returns pluginname mapped to list of matched urls.
- `POST /api/delete_files`: Deletes several file entries from pyload.
- `POST /api/delete_finished`: Deletes all finished files and completely finished packages.
- `POST /api/delete_packages`: Deletes packages and containing links.
- `GET /api/free_space`: Available free space at download directory in bytes.
- `POST /api/generate_and_add_packages`: Generates and add packages.
- `POST /api/generate_packages`: Parses links, generates packages names from urls.
- `GET /api/getAllUserData`: returns all known user and info.
- `GET /api/getUserData`: similar to `check_auth` but returns UserData type.
- `GET /api/get_account_types`: All available account types.
- `GET /api/get_accounts`: Get information about all entered accounts.
- `GET /api/get_all_info`: Returns all information stored by addon plugins. Values are always strings.
- `GET /api/get_all_userdata`: returns all known user and info.
- `GET /api/get_cachedir`: No documentation available
- `GET /api/get_captcha_task`: Returns a captcha task.
- `GET /api/get_captcha_task_status`: Get information about captcha task.
- `GET /api/get_collector`: same as `get_queue` for collector.
- `GET /api/get_collector_data`: same as `get_queue_data` for collector.
- `GET /api/get_config`: Retrieves complete config of core.
- `GET /api/get_config_dict`: Retrieves complete config in dict format, not for RPC.
- `GET /api/get_config_value`: Retrieve config value.
- `GET /api/get_events`: Lists occurred events, may be affected to changes in the future.
- `GET /api/get_file_data`: Get complete information about a specific file.
- `GET /api/get_file_order`: Information about file order within package.
- `GET /api/get_info_by_plugin`: Returns information stored by a specific plugin.
- `GET /api/get_log`: Returns most recent log entries.
- `GET /api/get_package_data`: Returns complete information about package, and included files.
- `GET /api/get_package_info`: Returns information about package, without detailed information about containing files.
- `GET /api/get_package_order`: Returns information about package order.
- `GET /api/get_plugin_config`: Retrieves complete config for all plugins.
- `GET /api/get_plugin_config_dict`: Plugin config as dict, not for RPC.
- `GET /api/get_queue`: Returns info about queue and packages, **not** about files, see `get_queue_data` or `get_package_data` instead.
- `GET /api/get_queue_data`: Return complete data about everything in queue, this is very expensive use it sparely. See `get_queue` for alternative.
- `GET /api/get_server_version`: pyLoad Core version.
- `GET /api/get_services`: A dict of available services, these can be defined by addon plugins.
- `GET /api/get_userdata`: similar to `check_auth` but returns UserData pe.
- `GET /api/get_userdir`: No documentation available
- `GET /api/has_service`: Checks whether a service is available.
- `POST /api/is_authorized`: checks if the user is authorized for specific method.
- `GET /api/is_captcha_waiting`: Indicates whether a captcha task is available.
- `GET /api/is_time_download`: Checks if pyload will start new downloads according to time in config.
- `GET /api/is_time_reconnect`: Checks if pyload will try to make a reconnect.
- `POST /api/kill`: Clean way to quit pyLoad.
- `POST /api/move_files`: Move multiple files to another package.
- `POST /api/move_package`: Set a new package location.
- `POST /api/order_file`: Gives a new position to a file within its package.
- `POST /api/order_package`: Gives a package a new position.
- `POST /api/parse_urls`: Parses html content or any arbitrary text for links and returns result of `check_urls`
- `POST /api/pause_server`: Pause server: It won't start any new downloads, but nothing gets aborted.
- `GET /api/poll_results`: Polls the result available for ResultID.
- `POST /api/pull_from_queue`: Moves package from Queue to Collector.
- `POST /api/push_to_queue`: Moves package from Collector to Queue.
- `POST /api/recheck_package`: Probes online status of all files in a package, also a default action when package is added.
- `POST /api/remove_account`: Remove account from pyload.
- `POST /api/remove_user`: deletes a user login.
- `POST /api/restart`: Restart pyload core.
- `POST /api/restart_failed`: Restarts all failed failes.
- `POST /api/restart_file`: Resets file status, so it will be downloaded again.
- `POST /api/restart_package`: Restarts a package, resets every containing files.
- `POST /api/service_call`: Calls a service (a method in addon plugin).
- `POST /api/set_captcha_result`: Set result for a captcha task.
- `POST /api/set_config_value`: Set new config value.
- `POST /api/set_package_data`: Allows to modify several package attributes.
- `POST /api/set_package_name`: Renames a package.
- `POST /api/set_user_permission`: No documentation available
- `GET /api/status_downloads`: Status of all currently running downloads.
- `GET /api/status_server`: Some general information about the current status of pyLoad.
- `POST /api/stop_all_downloads`: Aborts all running downloads.
- `POST /api/stop_downloads`: Aborts specific downloads.
- `POST /api/toggle_pause`: Toggle pause state.
- `POST /api/toggle_proxy`: Toggle proxy activation.
- `POST /api/toggle_reconnect`: Toggle reconnect activation.
- `POST /api/unpause_server`: Unpause server: New Downloads will be started.
- `POST /api/update_account`: Changes pw/options for specific account.
- `POST /api/upload_container`: Uploads and adds a container file to pyLoad.
- `GET /api/user_exists`: Check if a user actually exists in the database.

## Repo Utility Surface

`ghostship-pyload-ng` currently uses:
- server status and downloads
- queue inspection
- package and file adds
- package deletion
- pause toggle
- config dictionary
- cleanup and retry helpers
- account listing and mutation
- free space and server version

## Source Material

- Local mirrored raw spec: [pyload-openapi.json](/home/nixos/dev/personal/ghostship-hermes/docs/api/pyload-openapi.json)
