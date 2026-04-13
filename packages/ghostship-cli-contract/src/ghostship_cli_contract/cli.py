from __future__ import annotations

import json
import mimetypes
import sys
from pathlib import Path
from typing import Any, Callable

import click
import httpx
import typer

from .errors import CliContractError, ConfigError, InvalidInputError, UnknownCliError, exit_code_for_error
from .http import DEFAULT_TIMEOUT
from .models import RequestSpec


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, 'to_dict') and callable(value.to_dict):
        return value.to_dict()
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    return value


def echo_json(data: Any, pretty: bool = False, *, stream: Any = None) -> None:
    target = stream if stream is not None else sys.stdout
    json.dump(_to_jsonable(data), target, indent=2 if pretty else None)
    target.write('\n')


def parse_json_option(value: str | None, option_name: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise InvalidInputError(f"{option_name} must be valid JSON: {exc}") from exc


def parse_params(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if '=' not in value:
            raise InvalidInputError(f"parameter must use key=value form: {value}")
        key, raw = value.split('=', 1)
        params[key] = raw
    return params


def parse_file_params(values: list[str]) -> dict[str, tuple[str, bytes, str]]:
    files: dict[str, tuple[str, bytes, str]] = {}
    for value in values:
        if '=' not in value:
            raise InvalidInputError(f"file parameter must use key=path form: {value}")
        key, raw_path = value.split('=', 1)
        path = Path(raw_path).expanduser()
        if not path.is_file():
            raise InvalidInputError(f"file parameter path must exist and be a file: {raw_path}")
        content_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        files[key] = (path.name, path.read_bytes(), content_type)
    return files


def write_response_output(response: httpx.Response, output: str | Path) -> dict[str, Any]:
    output_path = Path(output)
    content_disposition = response.headers.get('content-disposition', '')
    suggested_name = None
    for part in content_disposition.split(';'):
        part = part.strip()
        if part.startswith('filename='):
            suggested_name = part.split('=', 1)[1].strip('"')
            break
    if output_path.exists() and output_path.is_dir():
        target = output_path / (suggested_name or Path(response.request.url.path).name or 'response.bin')
    else:
        target = output_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(response.content)
    return {
        'status': 'success',
        'output': str(target),
        'status_code': response.status_code,
        'content_type': response.headers.get('content-type'),
        'bytes_written': len(response.content),
    }


def render_dry_run(spec: RequestSpec) -> dict[str, Any]:
    return spec.to_dict()


def run_cli_command(build_request: Callable[[], RequestSpec] | None, execute: Callable[[float], Any], *, timeout: float = DEFAULT_TIMEOUT, dry_run: bool = False) -> Any:
    if dry_run:
        if build_request is None:
            raise InvalidInputError('dry-run is not supported for this command')
        return render_dry_run(build_request())
    return execute(timeout)


def handle_cli_error(error: Exception) -> None:
    if not isinstance(error, CliContractError):
        error = UnknownCliError(str(error))
    echo_json(error.to_dict(), stream=sys.stderr)
    raise typer.Exit(code=exit_code_for_error(error))


def require_env(name: str, value: str | None) -> str:
    if not value:
        raise ConfigError(f"{name} environment variable must be set")
    return value


def run_app(app: typer.Typer, argv: list[str] | None = None) -> None:
    try:
        app(args=argv, standalone_mode=False)
    except CliContractError as exc:
        handle_cli_error(exc)
    except (click.BadParameter, click.MissingParameter, click.UsageError) as exc:
        handle_cli_error(InvalidInputError(str(exc)))
    except click.ClickException as exc:
        handle_cli_error(InvalidInputError(str(exc)))
    except typer.Exit:
        raise
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)
