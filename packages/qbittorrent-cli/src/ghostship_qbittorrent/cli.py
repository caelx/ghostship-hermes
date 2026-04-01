from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, parse_json_option, parse_params, require_env, run_app, run_cli_command

from .client import QBitClient

app = typer.Typer(help='qBittorrent CLI interface.', no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> QBitClient:
    return QBitClient(require_env('QBITTORRENT_URL', os.getenv('QBITTORRENT_URL')), os.getenv('QBITTORRENT_USER'), os.getenv('QBITTORRENT_PASS'), default_timeout=APP_STATE['timeout'])


def _emit(data: Any, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _run(execute, *, pretty: bool) -> None:
    _emit(run_cli_command(None, execute, timeout=APP_STATE['timeout']), pretty)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    _emit(run_cli_command(build_request, execute, timeout=APP_STATE['timeout'], dry_run=dry_run), pretty)


@app.command('request')
def request(method: str, path: str, param: list[str] = typer.Option([], '--param'), data: list[str] = typer.Option([], '--data'), body_json: str | None = typer.Option(None, '--body-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    params = parse_params(param) or None
    form_data = parse_params(data) or None
    payload = parse_json_option(body_json, '--body-json')
    _run_write(lambda: client.build_request(method, path, params=params, data=form_data, json_data=payload), lambda timeout: client.request(method, path, params=params, data=form_data, json_data=payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('login')
def login(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_login(), lambda timeout: {'ok': client.login(timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('logout')
def logout(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_logout(), lambda timeout: {'ok': client.logout(timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('get_app_version')
def get_app_version(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: {'version': client.get_app_version(timeout=timeout)}, pretty=pretty)


@app.command('get_api_version')
def get_api_version(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: {'version': client.get_api_version(timeout=timeout)}, pretty=pretty)


@app.command('shutdown')
def shutdown(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_shutdown(), lambda timeout: {'ok': client.shutdown(timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('get_preferences')
def get_preferences(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_preferences(timeout=timeout), pretty=pretty)


@app.command('set_preferences')
def set_preferences(body_json: str = typer.Option(..., '--body-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    prefs = parse_json_option(body_json, '--body-json')
    _run_write(lambda: client.build_set_preferences(prefs), lambda timeout: {'ok': client.set_preferences(prefs, timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('get_log')
def get_log(last_known_id: int = typer.Option(-1, '--last-known-id'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_log(last_known_id=last_known_id, timeout=timeout), pretty=pretty)


@app.command('get_main_data')
def get_main_data(rid: int = typer.Option(0, '--rid'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_main_data(rid=rid, timeout=timeout), pretty=pretty)


@app.command('get_transfer_info')
def get_transfer_info(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_transfer_info(timeout=timeout), pretty=pretty)


@app.command('get_speed_limits_mode')
def get_speed_limits_mode(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: {'mode': client.get_speed_limits_mode(timeout=timeout)}, pretty=pretty)


@app.command('toggle_speed_limits_mode')
def toggle_speed_limits_mode(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_toggle_speed_limits_mode(), lambda timeout: {'ok': client.toggle_speed_limits_mode(timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('get_torrents')
def get_torrents(filter_type: str | None = typer.Option(None, '--filter-type'), category: str | None = typer.Option(None, '--category'), sort: str | None = typer.Option(None, '--sort'), reverse: bool = typer.Option(False, '--reverse'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_torrents(filter_type=filter_type, category=category, sort=sort, reverse=reverse, timeout=timeout), pretty=pretty)


@app.command('add_torrent')
def add_torrent(url: list[str], save_path: str | None = typer.Option(None, '--save-path'), category: str | None = typer.Option(None, '--category'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_add_torrent(url, save_path=save_path, category=category), lambda timeout: {'ok': client.add_torrent(url, save_path=save_path, category=category, timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('delete_torrents')
def delete_torrents(hashes: list[str], delete_files: bool = typer.Option(False, '--delete-files'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_delete_torrents(hashes, delete_files=delete_files), lambda timeout: {'ok': client.delete_torrents(hashes, delete_files=delete_files, timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('pause_torrents')
def pause_torrents(hashes: list[str], dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_pause_torrents(hashes), lambda timeout: {'ok': client.pause_torrents(hashes, timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('resume_torrents')
def resume_torrents(hashes: list[str], dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_resume_torrents(hashes), lambda timeout: {'ok': client.resume_torrents(hashes, timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('search_start')
def search_start(pattern: str, category: str = typer.Option('all', '--category'), plugins: str = typer.Option('all', '--plugins'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_search_start(pattern, category=category, plugins=plugins), lambda timeout: client.search_start(pattern, category=category, plugins=plugins, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('search_status')
def search_status(search_id: int | None = typer.Option(None, '--search-id'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.search_status(search_id, timeout=timeout), pretty=pretty)


@app.command('search_results')
def search_results(search_id: int, limit: int = typer.Option(10, '--limit'), offset: int = typer.Option(0, '--offset'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.search_results(search_id, limit=limit, offset=offset, timeout=timeout), pretty=pretty)


@app.command('get_rss_data')
def get_rss_data(with_data: bool = typer.Option(True, '--with-data/--no-with-data'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_rss_data(with_data=with_data, timeout=timeout), pretty=pretty)


def main():
    run_app(app)


if __name__ == '__main__':
    main()
