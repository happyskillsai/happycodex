#!/usr/bin/env python3
"""Set source versions for a HappyCodex release build."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


DEFAULT_REPO_ROOT = Path(__file__).resolve().parent.parent
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z][0-9A-Za-z.-]*)?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Release version, for example 0.6.0 or 0.6.0-happy.1.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=DEFAULT_REPO_ROOT,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def validate_version(version: str) -> None:
    if not SEMVER_RE.fullmatch(version):
        raise SystemExit(
            "Version must be SemVer without build metadata, for example "
            "0.6.0, 0.6.0-alpha.1, or 0.6.0-happy.1."
        )


def update_cargo_workspace_version(repo_root: Path, version: str) -> None:
    cargo_toml = repo_root / "codex-rs" / "Cargo.toml"
    text = cargo_toml.read_text(encoding="utf-8")
    pattern = re.compile(
        r"(?P<header>\[workspace\.package\]\s+version\s*=\s*)\"[^\"]+\"",
        re.MULTILINE,
    )
    updated, count = pattern.subn(rf'\g<header>"{version}"', text, count=1)
    if count != 1:
        raise SystemExit(f"Unable to update [workspace.package] version in {cargo_toml}")
    cargo_toml.write_text(updated, encoding="utf-8")


def update_npm_source_version(repo_root: Path, version: str) -> None:
    package_json = repo_root / "codex-cli" / "package.json"
    data = json.loads(package_json.read_text(encoding="utf-8"))
    data["version"] = version
    package_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    validate_version(args.version)
    repo_root = args.repo_root.resolve()
    update_cargo_workspace_version(repo_root, args.version)
    update_npm_source_version(repo_root, args.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
