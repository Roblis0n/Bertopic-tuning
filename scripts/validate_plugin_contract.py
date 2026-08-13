#!/usr/bin/env python3
"""Validate the vendored, standard-library Codex plugin contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
from urllib.parse import urlparse


PLUGIN_NAME = "bertopic-tuning"
TODO_MARKER = "[TODO:"
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\."
    r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
HEX_COLOR_RE = re.compile(r"^#[0-9A-F]{6}$", re.IGNORECASE)
TOP_LEVEL_FIELDS = {
    "id",
    "name",
    "version",
    "description",
    "skills",
    "apps",
    "mcpServers",
    "interface",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
}
INTERFACE_FIELDS = {
    "displayName",
    "shortDescription",
    "longDescription",
    "developerName",
    "category",
    "capabilities",
    "websiteURL",
    "privacyPolicyURL",
    "termsOfServiceURL",
    "brandColor",
    "composerIcon",
    "logo",
    "logoDark",
    "screenshots",
    "defaultPrompt",
    "default_prompt",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a BERTopic Tuning plugin without external dependencies."
    )
    parser.add_argument("plugin_path", help="Path to the plugin root")
    return parser.parse_args()


def add_unknown_field_errors(
    payload: dict[str, Any],
    allowed: set[str],
    prefix: str,
    errors: list[str],
) -> None:
    for field in sorted(set(payload) - allowed):
        errors.append(f"{prefix} field `{field}` is not accepted")


def require_string(
    payload: dict[str, Any],
    field: str,
    prefix: str,
    errors: list[str],
) -> str | None:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{prefix} field `{field}` must be a non-empty string")
        return None
    return value


def validate_optional_https_url(
    payload: dict[str, Any],
    field: str,
    prefix: str,
    errors: list[str],
) -> None:
    value = payload.get(field)
    if value is None:
        return
    parsed = urlparse(value) if isinstance(value, str) else None
    if parsed is None or parsed.scheme != "https" or not parsed.netloc:
        errors.append(f"{prefix} field `{field}` must be an absolute https URL")


def contains_todo(value: Any) -> bool:
    if isinstance(value, str):
        return TODO_MARKER in value
    if isinstance(value, list):
        return any(contains_todo(item) for item in value)
    if isinstance(value, dict):
        return any(contains_todo(item) for item in value.values())
    return False


def safe_asset_path(
    base: Path,
    plugin_root: Path,
    raw_path: Any,
    field: str,
    errors: list[str],
) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        errors.append(f"{field} must be a non-empty relative path")
        return None
    if "\\" in raw_path or ":" in raw_path:
        errors.append(f"{field} must stay inside the plugin archive")
        return None
    path = PurePosixPath(raw_path)
    windows_path = PureWindowsPath(raw_path)
    if (
        path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        errors.append(f"{field} must stay inside the plugin archive")
        return None
    resolved = base.joinpath(*path.parts).resolve(strict=False)
    if not resolved.is_relative_to(plugin_root.resolve()) or not resolved.is_file():
        errors.append(f"{field} points to a missing or unsafe file")
        return None
    return resolved


def parse_skill_frontmatter(skill_path: Path, label: str, errors: list[str]) -> None:
    try:
        text = skill_path.read_text(encoding="utf-8")
    except OSError:
        errors.append(f"{label} is unreadable")
        return
    if not text.startswith("---\n"):
        errors.append(f"{label} must start with YAML frontmatter")
        return
    end = text.find("\n---", 4)
    if end == -1:
        errors.append(f"{label} frontmatter is not closed")
        return
    frontmatter = text[4:end]
    name_match = re.search(r"(?m)^name:\s*([^\n]+)$", frontmatter)
    description_match = re.search(r"(?m)^description:\s*([^\n]+)$", frontmatter)
    if name_match is None or name_match.group(1).strip().strip("'\"") != PLUGIN_NAME:
        errors.append(f"{label} frontmatter name must be {PLUGIN_NAME}")
    if description_match is None or not description_match.group(1).strip().strip("'\""):
        errors.append(f"{label} frontmatter description must be non-empty")


def validate_skills(plugin_root: Path, errors: list[str]) -> None:
    skills_root = plugin_root / "skills"
    expected_skill = skills_root / PLUGIN_NAME
    if not skills_root.is_dir() or not expected_skill.is_dir():
        errors.append(f"plugin must contain skills/{PLUGIN_NAME}")
        return
    skill_directories = sorted(
        path.name
        for path in skills_root.iterdir()
        if path.is_dir() and not path.name.startswith(".")
    )
    if skill_directories != [PLUGIN_NAME]:
        errors.append(f"plugin skill directories must be exactly [{PLUGIN_NAME!r}]")
    parse_skill_frontmatter(
        expected_skill / "SKILL.md",
        f"skill `{PLUGIN_NAME}` SKILL.md",
        errors,
    )
    agent_yaml = expected_skill / "agents" / "openai.yaml"
    if not agent_yaml.is_file():
        errors.append(f"skill `{PLUGIN_NAME}` is missing agents/openai.yaml")
    else:
        agent_text = agent_yaml.read_text(encoding="utf-8")
        if "default_prompt:" not in agent_text or f"${PLUGIN_NAME}" not in agent_text:
            errors.append(
                f"skill `{PLUGIN_NAME}` agents/openai.yaml must explicitly prompt ${PLUGIN_NAME}"
            )


def validate_plugin_contract(plugin_root: Path) -> list[str]:
    plugin_root = plugin_root.resolve()
    errors: list[str] = []
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError:
        return ["missing or unreadable .codex-plugin/plugin.json"]
    except json.JSONDecodeError:
        return [".codex-plugin/plugin.json must be valid JSON"]
    if not isinstance(manifest, dict):
        return [".codex-plugin/plugin.json must contain an object"]
    if contains_todo(manifest):
        errors.append("plugin manifest contains a [TODO: ...] placeholder")
    add_unknown_field_errors(manifest, TOP_LEVEL_FIELDS, "plugin.json", errors)

    name = require_string(manifest, "name", "plugin.json", errors)
    if name is not None and name != PLUGIN_NAME:
        errors.append(f"plugin.json field `name` must be {PLUGIN_NAME}")
    version = require_string(manifest, "version", "plugin.json", errors)
    if version is not None and SEMVER_RE.fullmatch(version) is None:
        errors.append("plugin.json field `version` must be strict semver")
    require_string(manifest, "description", "plugin.json", errors)

    author = manifest.get("author")
    if not isinstance(author, dict):
        errors.append("plugin.json field `author` must be an object")
    else:
        add_unknown_field_errors(author, {"name", "email", "url"}, "author", errors)
        require_string(author, "name", "author", errors)
        if "email" in author:
            require_string(author, "email", "author", errors)
        validate_optional_https_url(author, "url", "author", errors)

    skills_path = manifest.get("skills")
    if not isinstance(skills_path, str) or skills_path.rstrip("/").removeprefix("./") != "skills":
        errors.append("plugin.json field `skills` must resolve to skills")
    for field in ("homepage", "repository"):
        validate_optional_https_url(manifest, field, "plugin.json", errors)
    if "license" in manifest:
        require_string(manifest, "license", "plugin.json", errors)
    keywords = manifest.get("keywords")
    if keywords is not None and (
        not isinstance(keywords, list)
        or not all(isinstance(item, str) and item.strip() for item in keywords)
    ):
        errors.append("plugin.json field `keywords` must be an array of strings")

    interface = manifest.get("interface")
    if not isinstance(interface, dict):
        errors.append("plugin.json field `interface` must be an object")
    else:
        add_unknown_field_errors(interface, INTERFACE_FIELDS, "interface", errors)
        for field in (
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
        ):
            require_string(interface, field, "interface", errors)
        capabilities = interface.get("capabilities")
        if not isinstance(capabilities, list) or not all(
            isinstance(item, str) and item.strip() for item in capabilities
        ):
            errors.append("interface field `capabilities` must be an array of strings")
        prompts = interface.get("defaultPrompt", interface.get("default_prompt"))
        if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3 or not all(
            isinstance(prompt, str) and 0 < len(prompt.strip()) <= 128
            for prompt in prompts
        ):
            errors.append("interface defaultPrompt must contain 1-3 strings of at most 128 characters")
        color = interface.get("brandColor")
        if color is not None and (
            not isinstance(color, str) or HEX_COLOR_RE.fullmatch(color) is None
        ):
            errors.append("interface field `brandColor` must use #RRGGBB")
        for field in ("websiteURL", "privacyPolicyURL", "termsOfServiceURL"):
            validate_optional_https_url(interface, field, "interface", errors)
        for field in ("composerIcon", "logo", "logoDark"):
            if field in interface:
                safe_asset_path(
                    plugin_root,
                    plugin_root,
                    interface[field],
                    f"interface.{field}",
                    errors,
                )
        screenshots = interface.get("screenshots", [])
        if not isinstance(screenshots, list):
            errors.append("interface field `screenshots` must be an array")
        else:
            for index, raw_path in enumerate(screenshots):
                path = safe_asset_path(
                    plugin_root,
                    plugin_root,
                    raw_path,
                    f"interface.screenshots[{index}]",
                    errors,
                )
                if path is not None and (
                    path.suffix.lower() != ".png"
                    or path.parent != (plugin_root / "assets").resolve()
                ):
                    errors.append(
                        f"interface.screenshots[{index}] must be a PNG under assets"
                    )

    validate_skills(plugin_root, errors)
    return errors


def main() -> None:
    args = parse_args()
    plugin_root = Path(args.plugin_path).expanduser().resolve()
    errors = validate_plugin_contract(plugin_root)
    if errors:
        print("Vendored plugin contract failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"Vendored plugin contract passed: {plugin_root}")


if __name__ == "__main__":
    main()
