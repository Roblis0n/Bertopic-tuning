#!/usr/bin/env python3
"""Build a standalone BERTopic Tuning plugin from an explicit file policy."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


POLICY_PATH = Path(".codex-plugin/package-policy.json")
SKILL_DESTINATION = Path("skills/bertopic-tuning")


class PackagingError(ValueError):
    """Raised when a package request violates the source packaging policy."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the standalone BERTopic Tuning Codex plugin."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="New output directory. It must be outside the source repository.",
    )
    parser.add_argument(
        "--codex-home",
        help=(
            "Optional Codex home containing the official skill-creator and "
            "plugin-creator validators. Both run before the output is published."
        ),
    )
    return parser.parse_args()


def safe_relative_path(raw_path: Any, label: str) -> PurePosixPath:
    if not isinstance(raw_path, str) or not raw_path:
        raise PackagingError(f"{label} must be a non-empty relative path")
    path = PurePosixPath(raw_path)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise PackagingError(f"{label} must be a safe relative path: {raw_path!r}")
    return path


def load_policy(source_root: Path) -> list[tuple[PurePosixPath, PurePosixPath]]:
    policy_path = source_root / POLICY_PATH
    try:
        payload = json.loads(policy_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PackagingError(f"unable to read packaging policy: {policy_path}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise PackagingError("packaging policy schema_version must be 1")
    if payload.get("skill_name") != "bertopic-tuning":
        raise PackagingError("packaging policy skill_name must be bertopic-tuning")
    raw_files = payload.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise PackagingError("packaging policy files must be a non-empty array")

    mappings: list[tuple[PurePosixPath, PurePosixPath]] = []
    destinations: set[PurePosixPath] = set()
    for index, entry in enumerate(raw_files):
        if not isinstance(entry, dict) or set(entry) != {"source", "destination"}:
            raise PackagingError(f"packaging policy files[{index}] has invalid fields")
        source = safe_relative_path(entry["source"], f"files[{index}].source")
        destination = safe_relative_path(
            entry["destination"], f"files[{index}].destination"
        )
        if destination in destinations:
            raise PackagingError(f"duplicate package destination: {destination}")
        destinations.add(destination)
        mappings.append((source, destination))

    canonical = [
        source
        for source, destination in mappings
        if destination == PurePosixPath("skills/bertopic-tuning/SKILL.md")
    ]
    if canonical != [PurePosixPath("SKILL.md")]:
        raise PackagingError(
            "policy must project canonical SKILL.md exactly once to the plugin skill"
        )
    return mappings


def validate_output_path(source_root: Path, requested_output: Path) -> Path:
    requested = requested_output.expanduser().absolute()
    if os.path.lexists(requested):
        raise PackagingError(f"output path already exists: {requested}")
    output = requested.resolve(strict=False)
    if output == Path(output.anchor):
        raise PackagingError("output path cannot be a filesystem root")
    if output == source_root or output.is_relative_to(source_root):
        raise PackagingError("output path must be outside the source repository")
    if source_root.is_relative_to(output):
        raise PackagingError("output path cannot contain the source repository")
    return output


def resolve_validators(codex_home: Path | None) -> tuple[Path, Path] | None:
    if codex_home is None:
        return None
    root = codex_home.expanduser().resolve()
    skill_validator = (
        root
        / "skills"
        / ".system"
        / "skill-creator"
        / "scripts"
        / "quick_validate.py"
    )
    plugin_validator = (
        root
        / "skills"
        / ".system"
        / "plugin-creator"
        / "scripts"
        / "validate_plugin.py"
    )
    for validator in (skill_validator, plugin_validator):
        if not validator.is_file():
            raise PackagingError(f"official validator not found: {validator}")
    return skill_validator, plugin_validator


def copy_whitelist(
    source_root: Path,
    staging_root: Path,
    mappings: list[tuple[PurePosixPath, PurePosixPath]],
) -> None:
    resolved_source_root = source_root.resolve()
    for source_relative, destination_relative in mappings:
        source = (source_root / source_relative.as_posix()).resolve()
        if not source.is_relative_to(resolved_source_root) or not source.is_file():
            raise PackagingError(f"whitelisted source file is missing or unsafe: {source_relative}")
        destination = staging_root / destination_relative.as_posix()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def run_official_validators(
    staging_root: Path,
    validators: tuple[Path, Path] | None,
) -> None:
    if validators is None:
        return
    skill_validator, plugin_validator = validators
    commands = (
        (skill_validator, staging_root / SKILL_DESTINATION),
        (plugin_validator, staging_root),
    )
    for validator, target in commands:
        subprocess.run(
            [sys.executable, "-X", "utf8", "-B", str(validator), str(target)],
            check=True,
        )


def build_plugin(
    source_root: Path,
    requested_output: Path,
    codex_home: Path | None = None,
) -> tuple[Path, int]:
    source_root = source_root.resolve()
    output = validate_output_path(source_root, requested_output)
    mappings = load_policy(source_root)
    validators = resolve_validators(codex_home)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent)
    ).resolve()
    try:
        copy_whitelist(source_root, staging, mappings)
        run_official_validators(staging, validators)
        staging.replace(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return output, len(mappings)


def main() -> None:
    args = parse_args()
    source_root = Path(__file__).resolve().parents[1]
    try:
        output, file_count = build_plugin(
            source_root,
            Path(args.output),
            Path(args.codex_home) if args.codex_home else None,
        )
    except (PackagingError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    print(f"Built standalone plugin: {output}")
    print(f"Whitelisted files: {file_count}")


if __name__ == "__main__":
    main()
