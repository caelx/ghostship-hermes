#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


UBOL_DEFAULT_RULESETS = [
    "ublock-filters",
    "easylist",
    "easyprivacy",
    "pgl",
    "adguard-spyware-url",
    "block-lan",
    "ublock-badware",
    "urlhaus-full",
    "annoyances-ai",
    "annoyances-cookies",
    "annoyances-notifications",
    "annoyances-others",
    "annoyances-overlays",
    "annoyances-social",
    "annoyances-widgets",
]


def js_array(values: list[str]) -> str:
    return "[\n" + "".join(f"        '{value}',\n" for value in values) + "    ]"


def patch_manifest(target_dir: Path) -> None:
    manifest_path = target_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    enabled_ids = set(UBOL_DEFAULT_RULESETS)
    rulesets = manifest["declarative_net_request"]["rule_resources"]
    missing = enabled_ids.difference(ruleset["id"] for ruleset in rulesets)
    if missing:
        raise ValueError(f"uBO Lite rulesets missing from manifest: {sorted(missing)}")
    for ruleset in rulesets:
        ruleset["enabled"] = ruleset["id"] in enabled_ids

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def patch_text_file(path: Path, replacements: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8")
    for before, after in replacements.items():
        if before not in text:
            raise ValueError(f"expected snippet not found in {path}: {before!r}")
        text = text.replace(before, after, 1)
    path.write_text(text, encoding="utf-8")


def patch_defaults(target_dir: Path) -> None:
    patch_manifest(target_dir)
    patch_text_file(
        target_dir / "js/config.js",
        {
            "    enabledRulesets: [],": f"    enabledRulesets: {js_array(UBOL_DEFAULT_RULESETS)},",
            "    strictBlockMode: webextFlavor !== 'safari',": "    strictBlockMode: true,",
        },
    )
    patch_text_file(
        target_dir / "js/mode-manager.js",
        {
            """export const defaultFilteringModes = {
    none: [],
    basic: [],
    optimal: [ 'all-urls' ],
    complete: [],
};""": """export const defaultFilteringModes = {
    none: [],
    basic: [],
    optimal: [],
    complete: [ 'all-urls' ],
};""",
        },
    )


def install_extension(source_dir: Path, target_dir: Path) -> None:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_dir, target_dir)

    patch_defaults(target_dir)

    if not (target_dir / "managed_storage.json").is_file():
        raise FileNotFoundError(target_dir / "managed_storage.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("target_dir", type=Path)
    args = parser.parse_args()

    install_extension(args.source_dir, args.target_dir)


if __name__ == "__main__":
    main()
