#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
from pathlib import Path


UBOL_MANIFEST_KEY = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAp/MSGg4v7Hu7nTUgWcxphFKUqUbghGuuflP0qxbAgT1vwp67s3/"
    "ZR1Rd4RbrB1fzq4V6725eD5rX/bx6qooObsNe4UgNzWwHzwH1/Q/1cSC8Exdv8qkqooTL/WqjwWoe+WfRo4XaPHQqVCmb/"
    "ttkdDs6MEJXPYvk0ueNOKaApOG2mDhx5/uP1/cJ0UlNdI0cGMaalfWcQX/cIoq0abJVKyKTk76i9zXQWluuhScaYNSY1aISOlIAuQlpJZywP/"
    "ttMu8HtEfedbusb1qtLiBb/n30MZnbzyRg5iW8arOl6tvh9RIZkQYHtWK5szAuXm825ESX89RiB72+Cj8K86LHXQIDAQAB"
)

def extension_id_from_key(key: str) -> str:
    digest = hashlib.sha256(base64.b64decode(key)).digest()[:16]
    return "".join(chr(ord("a") + (byte >> 4)) + chr(ord("a") + (byte & 15)) for byte in digest)


UBOL_EXTENSION_ID = extension_id_from_key(UBOL_MANIFEST_KEY)

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
    manifest["key"] = UBOL_MANIFEST_KEY

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
    (target_dir.with_suffix(".extension-id")).write_text(UBOL_EXTENSION_ID + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("target_dir", type=Path)
    args = parser.parse_args()

    install_extension(args.source_dir, args.target_dir)


if __name__ == "__main__":
    main()
