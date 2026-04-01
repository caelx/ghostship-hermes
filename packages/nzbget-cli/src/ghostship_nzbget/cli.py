from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, parse_json_option, require_env, run_app, run_cli_command

from .client import NZBGetClient

app = typer.Typer(help='NZBGet CLI interface.', no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> NZBGetClient:
    return NZBGetClient(require_env('NZBGET_URL', os.getenv('NZBGET_URL')), os.getenv('NZBGET_USER'), os.getenv('NZBGET_PASS'), default_timeout=APP_STATE['timeout'])


def _emit(data: Any, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _run(execute, *, pretty: bool) -> None:
    _emit(run_cli_command(None, execute, timeout=APP_STATE['timeout']), pretty)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    _emit(run_cli_command(build_request, execute, timeout=APP_STATE['timeout'], dry_run=dry_run), pretty)


@app.command('call')
def call(method: str, params_json: str | None = typer.Option(None, '--params-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    params = parse_json_option(params_json, '--params-json')
    _run_write(lambda: client.build_call(method, params=params), lambda timeout: client.call(method, params=params, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_version')
def get_version(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: {'version': client.get_version(timeout=timeout)}, pretty=pretty)


@app.command('shutdown')
def shutdown(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_shutdown(), lambda timeout: client.shutdown(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('reload')
def reload(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_reload(), lambda timeout: client.reload(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_status')
def get_status(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_status(timeout=timeout), pretty=pretty)


@app.command('list_groups')
def list_groups(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.list_groups(timeout=timeout), pretty=pretty)


@app.command('list_files')
def list_files(nzb_id: int, pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.list_files(nzb_id, timeout=timeout), pretty=pretty)


@app.command('get_history')
def get_history(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_history(timeout=timeout), pretty=pretty)


@app.command('append_url')
def append_url(url: str, category: str = typer.Option('', '--category'), priority: int = typer.Option(0, '--priority'), top: bool = typer.Option(False, '--top'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_append_url(url, category=category, priority=priority, top=top), lambda timeout: client.append_url(url, category=category, priority=priority, top=top, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('edit_queue')
def edit_queue(command: str, offset: int, size: int, ids_json: str = typer.Option(..., '--ids-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    ids = parse_json_option(ids_json, '--ids-json')
    _run_write(lambda: client.build_edit_queue(command, offset, size, ids), lambda timeout: client.edit_queue(command, offset, size, ids, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('disk_scan')
def disk_scan(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_disk_scan(), lambda timeout: client.disk_scan(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_log')
def get_log(id_from: int = typer.Option(0, '--id-from'), count: int = typer.Option(10, '--count'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_log(id_from, count, timeout=timeout), pretty=pretty)


@app.command('set_rate')
def set_rate(limit_kb: int, dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_set_rate(limit_kb), lambda timeout: client.set_rate(limit_kb, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('pause_download')
def pause_download(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_pause_download(), lambda timeout: client.pause_download(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('resume_download')
def resume_download(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_resume_download(), lambda timeout: client.resume_download(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('pause_post')
def pause_post(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_pause_post(), lambda timeout: client.pause_post(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('resume_post')
def resume_post(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_resume_post(), lambda timeout: client.resume_post(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('pause_scan')
def pause_scan(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_pause_scan(), lambda timeout: client.pause_scan(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('resume_scan')
def resume_scan(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_resume_scan(), lambda timeout: client.resume_scan(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_config')
def get_config(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_config(timeout=timeout), pretty=pretty)


@app.command('save_config')
def save_config(config_json: str = typer.Option(..., '--config-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    config = parse_json_option(config_json, '--config-json')
    _run_write(lambda: client.build_save_config(config), lambda timeout: client.save_config(config, timeout=timeout), dry_run=dry_run, pretty=pretty)


def main():
    run_app(app)


if __name__ == '__main__':
    main()
