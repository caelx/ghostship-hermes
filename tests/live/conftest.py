from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIRS = sorted(str(path) for path in REPO_ROOT.glob("packages/*-cli/src"))


def _load_envrc() -> dict[str, str]:
    envrc = REPO_ROOT / ".envrc"
    if not envrc.is_file():
        return os.environ.copy()

    command = "set -a; source ./.envrc >/dev/null 2>&1; env -0"
    result = subprocess.run(
        ["bash", "-lc", command],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=False,
        env=os.environ.copy(),
    )

    loaded: dict[str, str] = {}
    for entry in result.stdout.split(b"\0"):
        if not entry:
            continue
        key, _, value = entry.partition(b"=")
        loaded[key.decode()] = value.decode()
    return loaded


def _pythonpath(existing: str | None = None) -> str:
    paths = SRC_DIRS.copy()
    if existing:
        paths.append(existing)
    return os.pathsep.join(paths)


def _cloudflare_access_headers(env: dict[str, str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = env.get("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = env.get("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


def _maybe_cache_grimmory_token(env: dict[str, str]) -> None:
    if env.get("GRIMMORY_TOKEN"):
        return

    base_url = env.get("GRIMMORY_URL")
    username = env.get("GRIMMORY_USERNAME")
    password = env.get("GRIMMORY_PASSWORD")
    if not base_url or not username or not password:
        return

    try:
        response = httpx.post(
            f"{base_url.rstrip('/')}/api/v1/auth/login",
            json={"username": username, "password": password},
            headers=_cloudflare_access_headers(env),
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPError:
        return

    payload = response.json()
    token = payload.get("accessToken") or payload.get("access_token")
    if token:
        env["GRIMMORY_TOKEN"] = token


@pytest.fixture(scope="session")
def live_env() -> dict[str, str]:
    env = _load_envrc()
    env["PYTHONPATH"] = _pythonpath(env.get("PYTHONPATH"))
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")

    client_id = env.get("CF_ACCESS_CLIENT_ID")
    client_secret = env.get("CF_ACCESS_CLIENT_SECRET")
    if client_id:
        env["GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID"] = client_id
    if client_secret:
        env["GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET"] = client_secret

    _maybe_cache_grimmory_token(env)
    return env


@pytest.fixture(scope="session")
def cli_runner(live_env: dict[str, str]):
    def run(module: str, *args: str) -> Any:
        result = subprocess.run(
            [sys.executable, "-m", module, *args],
            cwd=REPO_ROOT,
            env=live_env,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            stderr = result.stderr.strip()
            stdout = result.stdout.strip()
            message = stderr or stdout or f"exit code {result.returncode}"
            raise AssertionError(f"{module} {' '.join(args)} failed: {message}")

        stdout = result.stdout.strip()
        assert stdout, f"{module} {' '.join(args)} returned no output"
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise AssertionError(
                f"{module} {' '.join(args)} did not return JSON: {stdout}"
            ) from exc

    return run


def first_item(payload: Any) -> Any | None:
    if isinstance(payload, list):
        return payload[0] if payload else None
    if isinstance(payload, dict):
        for key in ("records", "results", "series", "movies", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list) and value:
                return value[0]
        for value in payload.values():
            if isinstance(value, list) and value:
                return value[0]
    return None


def pick_id(item: Any, *keys: str) -> Any | None:
    if not isinstance(item, dict):
        return None
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return None
