from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path


def project_name(project_dir: Path) -> str:
    pyproject = project_dir / "pyproject.toml"
    if not pyproject.is_file():
        raise SystemExit(f"missing pyproject.toml in {project_dir}")

    for line in pyproject.read_text().splitlines():
        if line.startswith("name = "):
            return line.split("=", 1)[1].strip().strip('"')

    raise SystemExit(f"could not find project name in {pyproject}")


def validate_layout(project_dir: Path) -> None:
    expected = [
        project_dir / "pyproject.toml",
        project_dir / "package.nix",
        project_dir / "src",
        project_dir / "tests",
    ]
    missing = [path for path in expected if not path.exists()]
    if missing:
        joined = ", ".join(str(path) for path in missing)
        raise SystemExit(f"project layout is incomplete: {joined}")


def run(cmd: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(cmd, check=True, env=env)


def command_lock(project_dir: Path) -> None:
    run(["uv", "lock", "--project", str(project_dir)])


def command_test(project_dir: Path) -> None:
    env = os.environ.copy()
    src_dir = project_dir / "src"
    env["PYTHONPATH"] = (
        f"{src_dir}:{env['PYTHONPATH']}"
        if env.get("PYTHONPATH")
        else str(src_dir)
    )
    run(
        [
            "uv",
            "run",
            "--with",
            "pytest",
            "--with",
            "typer",
            "--with",
            "httpx",
            "pytest",
            str(project_dir / "tests"),
            "-q",
        ],
        env=env,
    )


def command_build(project_dir: Path) -> None:
    run(["uv", "build", "--project", str(project_dir)])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standardize lock, test, and build commands for ghostship Python utilities."
    )
    parser.add_argument("action", choices=["lock", "test", "build"])
    parser.add_argument("project_dir", help="Path to the utility package directory")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    validate_layout(project_dir)

    name = project_name(project_dir)
    if not name.startswith("ghostship-"):
        raise SystemExit(f"utility project name must start with 'ghostship-': {name}")

    actions = {
        "lock": command_lock,
        "test": command_test,
        "build": command_build,
    }
    actions[args.action](project_dir)


if __name__ == "__main__":
    main()
