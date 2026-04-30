from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from urllib.request import Request, urlopen


RELEASE_FILE = Path("packages/hermes-image/hermes-release.txt")
CHANGELOG_FILE = Path("CHANGELOG.md")
FLAKE_FILE = Path("flake.nix")
AGENT_BROWSER_PACKAGE = Path("packages/agent-browser/package.nix")
BLOGWATCHER_PACKAGE = Path("packages/blogwatcher/package.nix")
DASHBOARD_FRONTEND = Path("packages/hermes-dashboard/frontend")
DASHBOARD_PACKAGE = Path("packages/hermes-dashboard/package.nix")
DASHBOARD_PYTHON = Path("packages/hermes-dashboard")
LATEST_RELEASE_URL = "https://api.github.com/repos/NousResearch/hermes-agent/releases/latest"
BLOGWATCHER_RELEASE_URL = "https://api.github.com/repos/JulienTant/blogwatcher-cli/releases/latest"
NPM_AGENT_BROWSER_URL = "https://registry.npmjs.org/agent-browser/latest"


def _github_headers(user_agent: str) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": user_agent,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_json(url: str, headers: dict[str, str] | None = None) -> object:
    request = Request(url, headers=headers or {"User-Agent": "ghostship-hermes-software-updater"})
    with urlopen(request) as response:  # noqa: S310 - GitHub API endpoint
        return json.load(response)


def fetch_latest_tag() -> str:
    payload = _fetch_json(LATEST_RELEASE_URL, _github_headers("ghostship-hermes-software-updater"))
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub API returned a non-object release payload")
    tag_name = payload["tag_name"].strip()
    if not tag_name:
        raise RuntimeError("GitHub API returned an empty tag_name")
    return tag_name


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)


def update_changelog_note(note: str) -> None:
    content = CHANGELOG_FILE.read_text()
    marker = "## Unreleased\n"
    if note in content:
        return
    CHANGELOG_FILE.write_text(content.replace(marker, f"{marker}\n{note}", 1))


def update_flake_input(tag_name: str) -> None:
    content = FLAKE_FILE.read_text()
    updated = re.sub(
        r'github:NousResearch/hermes-agent/v[^"]+',
        f"github:NousResearch/hermes-agent/{tag_name}",
        content,
        count=1,
    )
    if updated == content:
        raise RuntimeError("failed to locate hermes-agent flake input in flake.nix")
    FLAKE_FILE.write_text(updated)


def update_hermes_release() -> None:
    latest = fetch_latest_tag()
    current = RELEASE_FILE.read_text().strip()
    if latest == current:
        return
    RELEASE_FILE.write_text(f"{latest}\n")
    update_flake_input(latest)
    update_changelog_note(f"- Pinned Hermes release updated to `{latest}`.\n")


def update_flake_lock() -> None:
    _run(["nix", "flake", "update"])


def update_agent_browser() -> None:
    payload = _fetch_json(NPM_AGENT_BROWSER_URL)
    if not isinstance(payload, dict):
        raise RuntimeError("npm registry returned a non-object agent-browser payload")

    version = str(payload["version"]).strip()
    integrity = str(payload["dist"]["integrity"]).strip()
    if not version or not integrity:
        raise RuntimeError("npm registry returned incomplete agent-browser metadata")

    content = AGENT_BROWSER_PACKAGE.read_text()
    content = re.sub(r'version = "[^"]+";', f'version = "{version}";', content, count=1)
    content = re.sub(r'hash = "sha512-[^"]+";', f'hash = "{integrity}";', content, count=1)
    AGENT_BROWSER_PACKAGE.write_text(content)


def _latest_blogwatcher_tag() -> str:
    payload = _fetch_json(BLOGWATCHER_RELEASE_URL, _github_headers("ghostship-hermes-software-updater"))
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub API returned a non-object blogwatcher release payload")
    tag_name = str(payload["tag_name"]).strip()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag_name):
        raise RuntimeError(f"unexpected blogwatcher release tag: {tag_name!r}")
    return tag_name


def _prefetch_sri(url: str) -> str:
    prefetch = _run(["nix-prefetch-url", url]).stdout.strip().splitlines()[-1]
    converted = _run(["nix", "hash", "convert", "--hash-algo", "sha256", "--to", "sri", prefetch]).stdout.strip()
    if not converted.startswith("sha256-"):
        raise RuntimeError(f"failed to prefetch {url}")
    return converted


def update_blogwatcher() -> None:
    tag = _latest_blogwatcher_tag()
    version = tag.removeprefix("v")
    amd64_url = f"https://github.com/JulienTant/blogwatcher-cli/releases/download/{tag}/blogwatcher-cli_linux_amd64.tar.gz"
    arm64_url = f"https://github.com/JulienTant/blogwatcher-cli/releases/download/{tag}/blogwatcher-cli_linux_arm64.tar.gz"
    amd64_hash = _prefetch_sri(amd64_url)
    arm64_hash = _prefetch_sri(arm64_url)

    content = BLOGWATCHER_PACKAGE.read_text()
    content = re.sub(r'version = "[^"]+";', f'version = "{version}";', content, count=1)
    content = re.sub(
        r'https://github\.com/JulienTant/blogwatcher-cli/releases/download/v[^/]+/blogwatcher-cli_linux_amd64\.tar\.gz',
        amd64_url,
        content,
        count=1,
    )
    content = re.sub(
        r'https://github\.com/JulienTant/blogwatcher-cli/releases/download/v[^/]+/blogwatcher-cli_linux_arm64\.tar\.gz',
        arm64_url,
        content,
        count=1,
    )
    hashes = iter((amd64_hash, arm64_hash))
    content = re.sub(r'hash = "sha256-[^"]+";', lambda _match: f'hash = "{next(hashes)}";', content, count=2)
    BLOGWATCHER_PACKAGE.write_text(content)


def update_dashboard_frontend() -> None:
    package_json = json.loads((DASHBOARD_FRONTEND / "package.json").read_text())
    dependencies = sorted((package_json.get("dependencies") or {}).keys())
    dev_dependencies = sorted((package_json.get("devDependencies") or {}).keys())

    if dependencies:
        _run(["npm", "install", "--package-lock-only", "--save", *(f"{name}@latest" for name in dependencies)], cwd=DASHBOARD_FRONTEND)
    if dev_dependencies:
        _run(["npm", "install", "--package-lock-only", "--save-dev", *(f"{name}@latest" for name in dev_dependencies)], cwd=DASHBOARD_FRONTEND)


def update_dashboard_python_lock() -> None:
    if not shutil.which("uv"):
        raise RuntimeError("uv is required to update packages/hermes-dashboard/uv.lock")
    _run(["uv", "lock", "--upgrade"], cwd=DASHBOARD_PYTHON)


def update_dashboard_npm_hash() -> None:
    result = _run(["nix", "run", "nixpkgs#prefetch-npm-deps", "--", str(DASHBOARD_FRONTEND / "package-lock.json")])
    hashes = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("sha256-")]
    if not hashes:
        raise RuntimeError("failed to compute dashboard npmDepsHash")

    content = DASHBOARD_PACKAGE.read_text()
    updated = re.sub(r'npmDepsHash = "sha256-[^"]+";', f'npmDepsHash = "{hashes[-1]}";', content, count=1)
    if updated == content and hashes[-1] not in content:
        raise RuntimeError("failed to locate dashboard npmDepsHash")
    DASHBOARD_PACKAGE.write_text(updated)


def main() -> None:
    update_hermes_release()
    update_flake_lock()
    update_agent_browser()
    update_blogwatcher()
    update_dashboard_frontend()
    update_dashboard_python_lock()
    update_dashboard_npm_hash()
    update_changelog_note("- Refreshed pinned software versions through the managed updater.\n")


if __name__ == "__main__":
    main()
