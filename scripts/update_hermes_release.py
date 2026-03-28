from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen


RELEASE_FILE = Path("packages/hermes-image/hermes-release.txt")
CHANGELOG_FILE = Path("CHANGELOG.md")
LATEST_RELEASE_URL = "https://api.github.com/repos/NousResearch/hermes-agent/releases/latest"


def fetch_latest_tag() -> str:
    with urlopen(LATEST_RELEASE_URL) as response:  # noqa: S310 - GitHub API endpoint
        payload = json.load(response)
    tag_name = payload["tag_name"].strip()
    if not tag_name:
        raise RuntimeError("GitHub API returned an empty tag_name")
    return tag_name


def update_changelog(tag_name: str) -> None:
    content = CHANGELOG_FILE.read_text()
    marker = "## Unreleased\n"
    note = f"- Pinned Hermes release updated to `{tag_name}`.\n"
    if note in content:
        return
    CHANGELOG_FILE.write_text(content.replace(marker, f"{marker}\n{note}", 1))


def main() -> None:
    latest = fetch_latest_tag()
    current = RELEASE_FILE.read_text().strip()
    if latest == current:
        return
    RELEASE_FILE.write_text(f"{latest}\n")
    update_changelog(latest)


if __name__ == "__main__":
    main()
