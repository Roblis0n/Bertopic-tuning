#!/usr/bin/env python3
"""Build a standalone BERTopic Tuning plugin from the Git index."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from validate_plugin_contract import validate_plugin_contract


PLUGIN_NAME = "bertopic-tuning"
POLICY_PATH = PurePosixPath(".codex-plugin/package-policy.json")
SKILL_DESTINATION = Path("skills") / PLUGIN_NAME
REGULAR_GIT_MODES = {"100644": 0o644, "100755": 0o755}
SYMLINK_GIT_MODE = "120000"
NORMALIZED_MTIME_NS = 315_532_800_000_000_000
ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)


class PackagingError(ValueError):
    """Raised when a package request violates the source packaging policy."""


@dataclass(frozen=True)
class IndexEntry:
    path: PurePosixPath
    object_id: str
    git_mode: str

    @property
    def file_mode(self) -> int:
        return REGULAR_GIT_MODES[self.git_mode]


@dataclass(frozen=True)
class PackageFile:
    source: PurePosixPath
    destination: PurePosixPath
    index_entry: IndexEntry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the standalone BERTopic Tuning Codex plugin."
    )
    parser.add_argument(
        "--output",
        required=True,
        help=(
            "New output directory named bertopic-tuning. It must be outside "
            "the source repository."
        ),
    )
    parser.add_argument(
        "--archive",
        help=(
            "Optional new deterministic ZIP path named bertopic-tuning.zip. "
            "Release builds should provide this argument."
        ),
    )
    parser.add_argument(
        "--codex-home",
        help=(
            "Optional Codex home containing the official skill-creator and "
            "plugin-creator validators. Both run before outputs are published."
        ),
    )
    return parser.parse_args()


def safe_relative_path(raw_path: Any, label: str) -> PurePosixPath:
    if not isinstance(raw_path, str) or not raw_path:
        raise PackagingError(f"{label} must be a non-empty safe POSIX relative path")
    if "\\" in raw_path or ":" in raw_path:
        raise PackagingError(f"{label} must be a safe POSIX relative path: {raw_path!r}")
    posix_path = PurePosixPath(raw_path)
    windows_path = PureWindowsPath(raw_path)
    if (
        raw_path != posix_path.as_posix()
        or posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or bool(windows_path.root)
        or any(part in {"", ".", ".."} for part in posix_path.parts)
    ):
        raise PackagingError(f"{label} must be a safe POSIX relative path: {raw_path!r}")
    return posix_path


def run_git(source_root: Path, *arguments: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(source_root), *arguments],
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        detail = ""
        if isinstance(error, subprocess.CalledProcessError):
            detail = error.stderr.decode("utf-8", errors="replace").strip()
        suffix = f": {detail}" if detail else ""
        raise PackagingError(f"unable to read Git index{suffix}") from error
    return result.stdout


def load_git_index(source_root: Path) -> dict[PurePosixPath, IndexEntry]:
    try:
        repository_root = Path(
            run_git(source_root, "rev-parse", "--show-toplevel")
            .decode("utf-8")
            .strip()
        ).resolve()
    except UnicodeDecodeError as error:
        raise PackagingError("Git repository root is not valid UTF-8") from error
    if repository_root != source_root.resolve():
        raise PackagingError("builder must run from the Git worktree root")

    raw_index = run_git(source_root, "ls-files", "--stage", "-z")
    entries: dict[PurePosixPath, IndexEntry] = {}
    unmerged: set[str] = set()
    for raw_record in raw_index.split(b"\0"):
        if not raw_record:
            continue
        try:
            metadata, raw_path = raw_record.split(b"\t", 1)
            git_mode, object_id, stage = metadata.decode("ascii").split(" ")
            path_text = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as error:
            raise PackagingError("unable to parse Git index entry") from error
        path = safe_relative_path(path_text, "Git index path")
        if stage != "0":
            unmerged.add(path_text)
            continue
        if path in entries:
            raise PackagingError(f"duplicate Git index entry: {path}")
        entries[path] = IndexEntry(path, object_id, git_mode)
    if unmerged:
        names = ", ".join(sorted(unmerged))
        raise PackagingError(f"Git index contains unmerged entries: {names}")
    return entries


def require_regular_index_entry(
    entries: dict[PurePosixPath, IndexEntry],
    path: PurePosixPath,
) -> IndexEntry:
    entry = entries.get(path)
    if entry is None:
        raise PackagingError(f"whitelisted source is not tracked in the Git index: {path}")
    if entry.git_mode == SYMLINK_GIT_MODE:
        raise PackagingError(f"Git index symlink is not allowed in a plugin package: {path}")
    if entry.git_mode not in REGULAR_GIT_MODES:
        raise PackagingError(
            f"unsupported Git index mode {entry.git_mode!r} for plugin source: {path}"
        )
    return entry


def read_index_blob(source_root: Path, entry: IndexEntry) -> bytes:
    return run_git(source_root, "cat-file", "blob", entry.object_id)


def load_policy(
    source_root: Path,
    index_entries: dict[PurePosixPath, IndexEntry],
) -> list[PackageFile]:
    policy_entry = require_regular_index_entry(index_entries, POLICY_PATH)
    try:
        payload = json.loads(read_index_blob(source_root, policy_entry).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PackagingError("Git-index packaging policy must be valid UTF-8 JSON") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise PackagingError("packaging policy schema_version must be 1")
    if payload.get("skill_name") != PLUGIN_NAME:
        raise PackagingError(f"packaging policy skill_name must be {PLUGIN_NAME}")
    raw_files = payload.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        raise PackagingError("packaging policy files must be a non-empty array")

    mappings: list[PackageFile] = []
    destinations: set[PurePosixPath] = set()
    for index, raw_mapping in enumerate(raw_files):
        if not isinstance(raw_mapping, dict) or set(raw_mapping) != {
            "source",
            "destination",
        }:
            raise PackagingError(f"packaging policy files[{index}] has invalid fields")
        source = safe_relative_path(raw_mapping["source"], f"files[{index}].source")
        destination = safe_relative_path(
            raw_mapping["destination"], f"files[{index}].destination"
        )
        if destination in destinations:
            raise PackagingError(f"duplicate package destination: {destination}")
        destinations.add(destination)
        mappings.append(
            PackageFile(
                source=source,
                destination=destination,
                index_entry=require_regular_index_entry(index_entries, source),
            )
        )

    canonical = [
        mapping.source
        for mapping in mappings
        if mapping.destination == PurePosixPath(f"skills/{PLUGIN_NAME}/SKILL.md")
    ]
    if canonical != [PurePosixPath("SKILL.md")]:
        raise PackagingError(
            "policy must project canonical SKILL.md exactly once to the plugin skill"
        )
    return mappings


def validate_new_path(
    source_root: Path,
    requested_path: Path,
    *,
    expected_name: str,
    label: str,
) -> Path:
    requested = requested_path.expanduser().absolute()
    if requested.name != expected_name:
        raise PackagingError(f"{label} must be named {expected_name}")
    if os.path.lexists(requested):
        raise PackagingError(f"{label} already exists: {requested}")
    resolved = requested.resolve(strict=False)
    if resolved == Path(resolved.anchor):
        raise PackagingError(f"{label} cannot be a filesystem root")
    if resolved == source_root or resolved.is_relative_to(source_root):
        raise PackagingError(f"{label} must be outside the source repository")
    if source_root.is_relative_to(resolved):
        raise PackagingError(f"{label} cannot contain the source repository")
    return resolved


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


def contained_destination(staging_root: Path, relative: PurePosixPath) -> Path:
    staging = staging_root.resolve()
    destination = staging.joinpath(*relative.parts).resolve(strict=False)
    if not destination.is_relative_to(staging):
        raise PackagingError(f"package destination escapes staging: {relative}")
    return destination


def write_index_files(
    source_root: Path,
    staging_root: Path,
    mappings: list[PackageFile],
) -> dict[PurePosixPath, int]:
    modes: dict[PurePosixPath, int] = {}
    for mapping in mappings:
        destination = contained_destination(staging_root, mapping.destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(read_index_blob(source_root, mapping.index_entry))
        os.chmod(destination, mapping.index_entry.file_mode)
        modes[mapping.destination] = mapping.index_entry.file_mode
    return modes


def normalize_tree_metadata(
    staging_root: Path,
    modes: dict[PurePosixPath, int],
) -> None:
    for relative, mode in modes.items():
        path = contained_destination(staging_root, relative)
        os.chmod(path, mode)
        os.utime(path, ns=(NORMALIZED_MTIME_NS, NORMALIZED_MTIME_NS))
    directories = sorted(
        (path for path in staging_root.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in [*directories, staging_root]:
        os.chmod(directory, 0o755)
        os.utime(directory, ns=(NORMALIZED_MTIME_NS, NORMALIZED_MTIME_NS))


def write_deterministic_zip(
    staging_root: Path,
    archive_path: Path,
    modes: dict[PurePosixPath, int],
) -> None:
    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as bundle:
        for relative in sorted(modes, key=lambda path: path.as_posix()):
            info = zipfile.ZipInfo(relative.as_posix(), ZIP_DATE_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | modes[relative]) << 16
            info.flag_bits |= 0x800
            bundle.writestr(
                info,
                contained_destination(staging_root, relative).read_bytes(),
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )
    os.chmod(archive_path, 0o644)
    os.utime(archive_path, ns=(NORMALIZED_MTIME_NS, NORMALIZED_MTIME_NS))


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


def run_vendored_contract(staging_root: Path) -> None:
    errors = validate_plugin_contract(staging_root)
    if errors:
        raise PackagingError("vendored plugin contract failed: " + "; ".join(errors))


def build_plugin(
    source_root: Path,
    requested_output: Path,
    requested_archive: Path | None = None,
    codex_home: Path | None = None,
) -> tuple[Path, Path | None, int]:
    source_root = source_root.resolve()
    output = validate_new_path(
        source_root,
        requested_output,
        expected_name=PLUGIN_NAME,
        label="output directory",
    )
    archive = None
    if requested_archive is not None:
        archive = validate_new_path(
            source_root,
            requested_archive,
            expected_name=f"{PLUGIN_NAME}.zip",
            label="archive",
        )
        if archive.is_relative_to(output):
            raise PackagingError("archive must be outside the output directory")

    index_entries = load_git_index(source_root)
    mappings = load_policy(source_root, index_entries)
    validators = resolve_validators(codex_home)
    output.parent.mkdir(parents=True, exist_ok=True)
    if archive is not None:
        archive.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent)
    ).resolve()
    archive_staging: Path | None = None
    published_output = False
    try:
        modes = write_index_files(source_root, staging, mappings)
        run_vendored_contract(staging)
        run_official_validators(staging, validators)
        normalize_tree_metadata(staging, modes)
        if archive is not None:
            handle, raw_archive_staging = tempfile.mkstemp(
                prefix=f".{archive.name}.staging-",
                suffix=".zip",
                dir=archive.parent,
            )
            os.close(handle)
            archive_staging = Path(raw_archive_staging)
            write_deterministic_zip(staging, archive_staging, modes)

        if os.path.lexists(output):
            raise PackagingError(f"output directory already exists: {output}")
        if archive is not None and os.path.lexists(archive):
            raise PackagingError(f"archive already exists: {archive}")
        staging.rename(output)
        published_output = True
        if archive is not None and archive_staging is not None:
            archive_staging.rename(archive)
            archive_staging = None
    except Exception:
        if published_output and output.exists():
            shutil.rmtree(output)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        if archive_staging is not None and archive_staging.exists():
            archive_staging.unlink()
    return output, archive, len(mappings)


def main() -> None:
    args = parse_args()
    source_root = Path(__file__).resolve().parents[1]
    try:
        output, archive, file_count = build_plugin(
            source_root,
            Path(args.output),
            Path(args.archive) if args.archive else None,
            Path(args.codex_home) if args.codex_home else None,
        )
    except (PackagingError, OSError, subprocess.CalledProcessError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    print(f"Built standalone plugin: {output}")
    if archive is not None:
        print(f"Built deterministic archive: {archive}")
    print(f"Whitelisted Git-index files: {file_count}")


if __name__ == "__main__":
    main()
