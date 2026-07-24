#!/usr/bin/env python3
"""Validate corpus reconnaissance, scalable reading evidence, and the modeling gate."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "corpus-profile.json",
    "corpus-reading-plan.json",
    "corpus-reading-ledger.csv",
    "theme-reconnaissance.json",
    "theme-candidate-audit.csv",
    "modeling-authorization.json",
}

LEDGER_FIELDS = {
    "reading_plan_id",
    "unit_id",
    "parent_document_id",
    "route_subset",
    "source_group",
    "time_group",
    "language_group",
    "length_group",
    "duplicate_group_id",
    "content_sha256",
    "content_length",
    "canonical_unit_id",
    "selection_channels",
    "holdout_role",
    "review_depth",
    "extraction_artifact",
    "extraction_locator",
    "span_start",
    "span_end",
    "extraction_sha256",
    "audit_round_id",
    "sampling_frame_sha256",
    "candidate_map_freeze_sha256",
    "holdout_new_candidate_theme_ids",
    "holdout_material_change_detected",
    "candidate_theme_ids",
    "review_notes",
}

CANDIDATE_FIELDS = {
    "reconnaissance_id",
    "candidate_theme_id",
    "parent_candidate_theme_id",
    "hierarchy_level",
    "route_subset",
    "provisional_label",
    "theme_type",
    "relation_to_user_mainline",
    "definition",
    "inclusion",
    "exclusion",
    "independent_support",
    "evidence_unit_ids",
    "source_or_parent_spread",
    "duplicate_or_artifact_risk",
    "uncertainty",
    "prevalence_claimed",
    "claim_scope",
    "user_disposition",
    "user_instruction",
}

RELATIONS = {
    "mainline",
    "supporting",
    "contextual",
    "emergent",
    "artifact",
    "uncertain",
}
HIERARCHY_LEVELS = {"coarse", "fine"}
GATE_STATES = {
    "awaiting_user_direction",
    "revision_requested",
    "approved_for_modeling",
    "stop",
}
DISPOSITIONS = {
    "accepted",
    "rejected",
    "merge_requested",
    "split_requested",
    "deferred",
}
ROUTES = {"network-short", "long-document", "mixed"}
READING_MODES = {"direct_full_text", "progressive_extraction"}
REVIEW_DEPTHS = {
    "full_text",
    "extracted_representation",
    "not_semantically_reviewed",
    "exact_duplicate_inherited",
    "excluded",
    "failed",
}
SEMANTIC_REVIEW_DEPTHS = {"full_text", "extracted_representation"}
PROGRESSIVE_SELECTION_CHANNELS = {
    "coverage_strata",
    "user_anchor",
    "lexical_novelty",
    "probability_holdout",
    "uncertainty_escalation",
}
HOLDOUT_ROLES = {"none", "development_released", "final_independent"}
FINAL_HOLDOUT_PROHIBITED_CHANNELS = {
    "user_anchor",
    "lexical_novelty",
    "uncertainty_escalation",
}
CONTENT_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$", re.IGNORECASE)
EXTRACTION_LOCATOR_PATTERN = re.compile(
    r"^(?P<scheme>record|raw|cards|span)://(?P<target>[A-Za-z0-9._:@%+\-]+)$",
    re.IGNORECASE,
)
STOPPING_RESOURCE_LIMIT_PATTERN = re.compile(
    r"\bbudget\b|\btokens?\b|\bquota\b|\bdeadline\b|"
    r"\bcapacity\b|\ballocated\b|\bconsum(?:e|ed|ption)\b|"
    r"\bdeplet(?:e|ed|ion)\b|\btimebox\b|\bwall[- ]clock\b|"
    r"\bno\s+(?:review\s+)?(?:capacity|resources?)\s+remains?\b|"
    r"\bresource\s+(?:limit|ceiling|cap|exhaust)|"
    r"\btime\s+(?:limit|budget|expired|ran\s+out)|"
    r"预算|令牌|时限|截止|耗尽|用完|资源(?:不足|上限)",
    re.IGNORECASE,
)
NUMERIC_PREVALENCE_PATTERN = re.compile(
    r"(?:\d+(?:\.\d+)?\s*%|\b\d+(?:\.\d+)?\s*percent(?:age)?\b)",
    re.IGNORECASE,
)
PREVALENCE_TERM_PATTERN = re.compile(
    r"\b(?:prevalence|incidence|frequency|proportion|majority|minority)\b|"
    r"占比|比例|流行率|发生率|频率|大多数|少数",
    re.IGNORECASE,
)
WORDED_PREVALENCE_PATTERN = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+"
    r"(?:of|in)\s+(?:every\s+)?"
    r"(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+"
    r"(?:units?|documents?|records?|texts?|posts?)\b|"
    r"\b(?:almost|nearly)\s+all\b|\bmost\s+(?:units?|documents?|records?|texts?|posts?)\b|"
    r"(?:每|其中)(?:十|百|千|\d+)(?:个|条|篇)?(?:中|里)?(?:有)?(?:九|\d+)",
    re.IGNORECASE,
)
NEGATED_PREVALENCE_PATTERN = re.compile(
    r"(?:cannot|can't|do\s+not|does\s+not|not)\s+(?:estimate|infer|claim|show).*"
    r"(?:prevalence|incidence|frequency|proportion)|"
    r"(?:prevalence|incidence|frequency|proportion)\s+(?:is\s+)?not\s+estimated|"
    r"(?:不|不能|无法|不可)(?:估计|推断|声称|说明).*(?:占比|比例|流行率|发生率|频率)",
    re.IGNORECASE,
)
BOUND_PRE_MODEL_ARTIFACTS = (
    "corpus-profile.json",
    "corpus-reading-plan.json",
    "corpus-reading-ledger.csv",
    "theme-reconnaissance.json",
    "theme-candidate-audit.csv",
)


def compute_pre_model_artifact_fingerprint(root: Path) -> str:
    """Return a streaming fingerprint for every artifact an approval authorizes."""

    bundle_hasher = hashlib.sha256()
    for name in BOUND_PRE_MODEL_ARTIFACTS:
        encoded_name = name.encode("utf-8")
        file_hasher = hashlib.sha256()
        with (root / name).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                file_hasher.update(chunk)
        bundle_hasher.update(len(encoded_name).to_bytes(4, "big"))
        bundle_hasher.update(encoded_name)
        bundle_hasher.update(file_hasher.digest())
    return f"sha256:{bundle_hasher.hexdigest()}"


def _contains_unsupported_prevalence_claim(value: str) -> bool:
    """Return true when adaptive reconnaissance text asserts corpus prevalence."""

    rendered = str(value or "").strip()
    if not rendered:
        return False
    if NUMERIC_PREVALENCE_PATTERN.search(rendered):
        return True
    if WORDED_PREVALENCE_PATTERN.search(rendered):
        return True
    if not PREVALENCE_TERM_PATTERN.search(rendered):
        return False
    return not NEGATED_PREVALENCE_PATTERN.search(rendered)


def _read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Cannot read valid JSON from {path.name}: {exc}")
        return None


def _read_candidates(
    path: Path, errors: list[str]
) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader.fieldnames or []), list(reader)
    except (OSError, csv.Error) as exc:
        errors.append(f"Cannot read CSV {path.name}: {exc}")
        return [], []


def _count(value: Any, field: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        errors.append(f"{field} must be a non-negative integer")
        return None
    return value


def _nonempty_string_list(
    value: Any, field: str, errors: list[str]
) -> list[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{field} must be a non-empty list")
        return []
    rendered = [str(item).strip() for item in value]
    if any(not item for item in rendered):
        errors.append(f"{field} must not contain blank values")
    if len(rendered) != len(set(rendered)):
        errors.append(f"{field} must contain unique values")
    return rendered


def _csv_nonnegative_int(
    value: Any, field: str, errors: list[str], *, allow_blank: bool = False
) -> int | None:
    rendered = str(value or "").strip()
    if allow_blank and not rendered:
        return None
    if not rendered.isdigit():
        errors.append(f"{field} must be a non-negative integer")
        return None
    return int(rendered)


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"


def compute_holdout_sampling_frame_sha256(unit_ids: set[str]) -> str:
    """Return an order-independent, length-delimited holdout-frame fingerprint."""

    hasher = hashlib.sha256()
    for unit_id in sorted(unit_ids):
        encoded = unit_id.encode("utf-8")
        hasher.update(len(encoded).to_bytes(8, "big"))
        hasher.update(encoded)
    return f"sha256:{hasher.hexdigest()}"


def _sha256_span(path: Path, start: int, end: int) -> str:
    hasher = hashlib.sha256()
    remaining = end - start
    with path.open("rb") as handle:
        handle.seek(start)
        while remaining:
            chunk = handle.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            hasher.update(chunk)
            remaining -= len(chunk)
    return f"sha256:{hasher.hexdigest()}"


def _register_extraction_artifacts(
    value: Any, root: Path, errors: list[str]
) -> dict[str, Path]:
    """Validate registered extraction artifacts and return resolved paths."""

    if not isinstance(value, list) or not value:
        errors.append("extraction.registered_artifacts must be a non-empty list")
        return {}

    root_resolved = root.resolve()
    registered: dict[str, Path] = {}
    for index, item in enumerate(value, start=1):
        prefix = f"extraction.registered_artifacts item {index}"
        if not isinstance(item, dict):
            errors.append(
                f"{prefix} must be an object with artifact_path and artifact_sha256"
            )
            continue
        artifact_path = str(item.get("artifact_path", "")).strip()
        artifact_sha256 = str(item.get("artifact_sha256", "")).strip()
        if not artifact_path:
            errors.append(f"{prefix} artifact_path must not be blank")
            continue
        if artifact_path in registered:
            errors.append(f"{prefix} duplicates artifact_path {artifact_path}")
            continue
        relative = Path(artifact_path)
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"{prefix} artifact_path must stay within the bundle")
            continue
        resolved = (root / relative).resolve()
        try:
            resolved.relative_to(root_resolved)
        except ValueError:
            errors.append(f"{prefix} artifact_path must stay within the bundle")
            continue
        if not CONTENT_SHA256_PATTERN.fullmatch(artifact_sha256):
            errors.append(
                f"{prefix} artifact_sha256 must be sha256: followed by "
                "64 hexadecimal characters"
            )
            continue
        if not resolved.is_file():
            errors.append(
                f"registered extraction artifact does not exist: {artifact_path}"
            )
            continue
        try:
            actual_sha256 = _sha256_file(resolved)
        except OSError as exc:
            errors.append(
                f"cannot read registered extraction artifact {artifact_path}: {exc}"
            )
            continue
        if actual_sha256.casefold() != artifact_sha256.casefold():
            errors.append(
                f"registered extraction artifact hash does not match: {artifact_path}"
            )
            continue
        registered[artifact_path] = resolved
    return registered


def _audit_reading_ledger(
    path: Path,
    *,
    reading_plan_id: str,
    reading_mode: str,
    route: str,
    registered_artifacts: dict[str, Path],
    holdout_audit_round_id: str,
    holdout_sampling_frame_sha256: str,
    candidate_map_freeze_sha256: str,
    evidence_unit_ids: set[str],
    errors: list[str],
) -> dict[str, Any]:
    audit: dict[str, Any] = {
        "row_count": 0,
        "unique_unit_count": 0,
        "depth_counts": {depth: 0 for depth in REVIEW_DEPTHS},
        "evidence_depths": {},
        "evidence_holdout_roles": {},
        "observed_selection_channels": set(),
        "holdout_role_counts": {role: 0 for role in HOLDOUT_ROLES},
        "route_subset_counts": {name: 0 for name in ("network-short", "long-document")},
        "route_subset_depth_counts": {
            name: {depth: 0 for depth in REVIEW_DEPTHS}
            for name in ("network-short", "long-document")
        },
        "route_subset_channels": {
            name: set() for name in ("network-short", "long-document")
        },
        "route_subset_holdout_counts": {
            name: {role: 0 for role in HOLDOUT_ROLES}
            for name in ("network-short", "long-document")
        },
        "distinct_long_document_parent_count": 0,
        "distinct_semantically_reviewed_long_document_parent_count": 0,
        "derived_full_text_long_document_parent_count": 0,
        "derived_extracted_long_document_parent_count": 0,
        "final_holdout_unit_ids": set(),
        "holdout_new_candidate_theme_ids": set(),
        "holdout_material_change_count": 0,
    }
    try:
        with tempfile.TemporaryDirectory(
            prefix="bertopic-ledger-audit-", ignore_cleanup_errors=True
        ) as tmp:
            database = Path(tmp) / "ledger.sqlite3"
            with closing(sqlite3.connect(database)) as connection:
                connection.execute("PRAGMA journal_mode=OFF")
                connection.execute("PRAGMA synchronous=OFF")
                connection.execute(
                    "CREATE TABLE units ("
                    "unit_id TEXT PRIMARY KEY, "
                    "parent_document_id TEXT NOT NULL, "
                    "route_subset TEXT NOT NULL, "
                    "review_depth TEXT NOT NULL, "
                    "duplicate_group_id TEXT NOT NULL, "
                    "content_sha256 TEXT NOT NULL, "
                    "content_length INTEGER)"
                )
                connection.execute(
                    "CREATE TABLE duplicate_links ("
                    "row_number INTEGER NOT NULL, "
                    "unit_id TEXT NOT NULL, "
                    "canonical_unit_id TEXT NOT NULL)"
                )
                with path.open("r", encoding="utf-8-sig", newline="") as handle:
                    reader = csv.DictReader(handle)
                    header = set(reader.fieldnames or [])
                    missing = sorted(LEDGER_FIELDS.difference(header))
                    errors.extend(
                        f"corpus-reading-ledger.csv lacks required column: {field}"
                        for field in missing
                    )
                    if missing:
                        return audit
                    for index, row in enumerate(reader, start=2):
                        audit["row_count"] += 1
                        prefix = f"corpus-reading-ledger.csv row {index}"
                        if str(row.get("reading_plan_id", "")).strip() != reading_plan_id:
                            errors.append(f"{prefix} reading_plan_id does not match")

                        unit_id = str(row.get("unit_id", "")).strip()
                        parent_document_id = str(
                            row.get("parent_document_id", "")
                        ).strip()
                        route_subset = str(row.get("route_subset", "")).strip()
                        depth = str(row.get("review_depth", "")).strip()
                        duplicate_group_id = str(
                            row.get("duplicate_group_id", "")
                        ).strip()
                        content_sha256 = str(row.get("content_sha256", "")).strip()
                        content_length = _csv_nonnegative_int(
                            row.get("content_length"),
                            f"{prefix} content_length",
                            errors,
                        )
                        holdout_role = str(row.get("holdout_role", "")).strip()
                        rendered_channels = str(
                            row.get("selection_channels", "")
                        ).strip()
                        row_channels = {
                            item.strip()
                            for item in rendered_channels.split("|")
                            if item.strip()
                        }

                        if not unit_id:
                            errors.append(f"{prefix} lacks unit_id")
                        else:
                            try:
                                connection.execute(
                                    "INSERT INTO units VALUES (?, ?, ?, ?, ?, ?, ?)",
                                    (
                                        unit_id,
                                        parent_document_id,
                                        route_subset,
                                        depth,
                                        duplicate_group_id,
                                        content_sha256,
                                        content_length,
                                    ),
                                )
                            except sqlite3.IntegrityError:
                                errors.append(f"{prefix} duplicates unit_id {unit_id}")

                        if route_subset not in {"network-short", "long-document"}:
                            errors.append(
                                f"{prefix} route_subset must be network-short or "
                                "long-document"
                            )
                        else:
                            audit["route_subset_counts"][route_subset] += 1
                            if route == "network-short" and route_subset != route:
                                errors.append(
                                    f"{prefix} route_subset does not match network-short route"
                                )
                            elif route == "long-document" and route_subset != route:
                                errors.append(
                                    f"{prefix} route_subset does not match long-document route"
                                )
                            if route_subset == "long-document" and not parent_document_id:
                                errors.append(
                                    f"{prefix} long-document unit lacks parent_document_id"
                                )

                        if depth not in REVIEW_DEPTHS:
                            errors.append(f"{prefix} has an invalid review_depth")
                            continue
                        audit["depth_counts"][depth] += 1
                        if route_subset in audit["route_subset_depth_counts"]:
                            audit["route_subset_depth_counts"][route_subset][depth] += 1

                        if not CONTENT_SHA256_PATTERN.fullmatch(content_sha256):
                            errors.append(
                                f"{prefix} content_sha256 must be sha256: followed by "
                                "64 hexadecimal characters"
                            )

                        if holdout_role not in HOLDOUT_ROLES:
                            errors.append(f"{prefix} has an invalid holdout_role")
                        else:
                            audit["holdout_role_counts"][holdout_role] += 1
                            if route_subset in audit["route_subset_holdout_counts"]:
                                audit["route_subset_holdout_counts"][route_subset][
                                    holdout_role
                                ] += 1
                            if reading_mode == "direct_full_text" and holdout_role != "none":
                                errors.append(
                                    f"{prefix} direct_full_text requires holdout_role=none"
                                )
                            if holdout_role != "none":
                                if depth not in SEMANTIC_REVIEW_DEPTHS:
                                    errors.append(
                                        f"{prefix} holdout row must be semantically reviewed"
                                    )
                                if "probability_holdout" not in row_channels:
                                    errors.append(
                                        f"{prefix} holdout row lacks probability_holdout channel"
                                    )
                            elif "probability_holdout" in row_channels:
                                errors.append(
                                    f"{prefix} probability_holdout channel requires a "
                                    "holdout_role"
                                )
                            if (
                                holdout_role == "final_independent"
                                and str(row.get("candidate_theme_ids", "")).strip()
                            ):
                                errors.append(
                                    f"{prefix} final independent holdout cannot carry "
                                    "candidate_theme_ids"
                                )
                            if holdout_role == "final_independent":
                                adaptive_channels = sorted(
                                    FINAL_HOLDOUT_PROHIBITED_CHANNELS.intersection(
                                        row_channels
                                    )
                                )
                                if adaptive_channels:
                                    errors.append(
                                        f"{prefix} final independent holdout cannot use "
                                        "adaptive candidate-selection channels: "
                                        + ", ".join(adaptive_channels)
                                    )
                                row_audit_round_id = str(
                                    row.get("audit_round_id", "")
                                ).strip()
                                row_sampling_frame_sha256 = str(
                                    row.get("sampling_frame_sha256", "")
                                ).strip()
                                row_candidate_map_freeze_sha256 = str(
                                    row.get("candidate_map_freeze_sha256", "")
                                ).strip()
                                if row_audit_round_id != holdout_audit_round_id:
                                    errors.append(
                                        f"{prefix} audit_round_id must match the registered "
                                        "final holdout audit round"
                                    )
                                if (
                                    row_sampling_frame_sha256
                                    != holdout_sampling_frame_sha256
                                ):
                                    errors.append(
                                        f"{prefix} sampling_frame_sha256 must match the "
                                        "registered final holdout frame"
                                    )
                                if (
                                    row_candidate_map_freeze_sha256
                                    != candidate_map_freeze_sha256
                                ):
                                    errors.append(
                                        f"{prefix} candidate_map_freeze_sha256 must match "
                                        "the frozen candidate map"
                                    )
                                audit["final_holdout_unit_ids"].add(unit_id)
                                audit["holdout_new_candidate_theme_ids"].update(
                                    item.strip()
                                    for item in str(
                                        row.get("holdout_new_candidate_theme_ids", "")
                                    ).split("|")
                                    if item.strip()
                                )
                                holdout_material_change = str(
                                    row.get("holdout_material_change_detected", "")
                                ).strip().casefold()
                                if holdout_material_change not in {"true", "false"}:
                                    errors.append(
                                        f"{prefix} holdout_material_change_detected must "
                                        "be true or false"
                                    )
                                elif holdout_material_change == "true":
                                    audit["holdout_material_change_count"] += 1
                            elif any(
                                str(row.get(field, "")).strip()
                                for field in (
                                    "audit_round_id",
                                    "sampling_frame_sha256",
                                    "candidate_map_freeze_sha256",
                                    "holdout_new_candidate_theme_ids",
                                    "holdout_material_change_detected",
                                )
                            ):
                                errors.append(
                                    f"{prefix} non-final row cannot carry final holdout "
                                    "audit fields"
                                )

                        if depth in SEMANTIC_REVIEW_DEPTHS:
                            if not rendered_channels:
                                errors.append(f"{prefix} lacks selection_channels")
                            else:
                                audit["observed_selection_channels"].update(row_channels)
                                if route_subset in audit["route_subset_channels"]:
                                    audit["route_subset_channels"][route_subset].update(
                                        row_channels
                                    )
                            extraction_artifact = str(
                                row.get("extraction_artifact", "")
                            ).strip()
                            artifact_path = registered_artifacts.get(extraction_artifact)
                            if artifact_path is None:
                                errors.append(
                                    f"{prefix} extraction_artifact is not registered in "
                                    "corpus-reading-plan.json"
                                )
                            extraction_locator = str(
                                row.get("extraction_locator", "")
                            ).strip()
                            locator_match = EXTRACTION_LOCATOR_PATTERN.fullmatch(
                                extraction_locator
                            )
                            if not locator_match or locator_match.group("target") != unit_id:
                                errors.append(
                                    f"{prefix} requires a traceable extraction_locator "
                                    "using a supported scheme and the row unit_id"
                                )
                            elif depth == "full_text" and locator_match.group(
                                "scheme"
                            ).lower() not in {"record", "raw"}:
                                errors.append(
                                    f"{prefix} full_text extraction_locator must use "
                                    "record:// or raw://"
                                )
                            elif depth == "extracted_representation" and locator_match.group(
                                "scheme"
                            ).lower() not in {"cards", "span"}:
                                errors.append(
                                    f"{prefix} extracted_representation locator must use "
                                    "cards:// or span://"
                                )
                            span_start = _csv_nonnegative_int(
                                row.get("span_start"),
                                f"{prefix} span_start",
                                errors,
                            )
                            span_end = _csv_nonnegative_int(
                                row.get("span_end"),
                                f"{prefix} span_end",
                                errors,
                            )
                            valid_span = (
                                span_start is not None
                                and span_end is not None
                                and span_end > span_start
                            )
                            if span_start is not None and span_end is not None:
                                if span_end <= span_start:
                                    errors.append(
                                        f"{prefix} span_end must be greater than span_start"
                                    )
                                if (
                                    depth == "full_text"
                                    and content_length is not None
                                    and span_end - span_start > content_length
                                ):
                                    errors.append(
                                        f"{prefix} span_end exceeds content_length"
                                    )
                                if (
                                    depth == "full_text"
                                    and content_length is not None
                                    and span_end - span_start != content_length
                                ):
                                    errors.append(
                                        f"{prefix} full_text review must cover the complete "
                                        "source content length"
                                    )
                            artifact_size: int | None = None
                            if artifact_path is not None and valid_span:
                                try:
                                    artifact_size = artifact_path.stat().st_size
                                except OSError as exc:
                                    errors.append(
                                        f"{prefix} cannot inspect extraction_artifact: {exc}"
                                    )
                                else:
                                    if span_end > artifact_size:
                                        errors.append(
                                            f"{prefix} span_end exceeds extraction artifact size"
                                        )
                            extraction_sha256 = str(
                                row.get("extraction_sha256", "")
                            ).strip()
                            if not CONTENT_SHA256_PATTERN.fullmatch(extraction_sha256):
                                errors.append(
                                    f"{prefix} extraction_sha256 must be sha256: followed "
                                    "by 64 hexadecimal characters"
                                )
                            elif (
                                depth == "full_text"
                                and CONTENT_SHA256_PATTERN.fullmatch(content_sha256)
                                and extraction_sha256.casefold()
                                != content_sha256.casefold()
                            ):
                                errors.append(
                                    f"{prefix} full_text extraction_sha256 must equal "
                                    "content_sha256"
                                )
                            if (
                                artifact_path is not None
                                and valid_span
                                and artifact_size is not None
                                and span_end <= artifact_size
                                and CONTENT_SHA256_PATTERN.fullmatch(extraction_sha256)
                            ):
                                try:
                                    actual_span_sha256 = _sha256_span(
                                        artifact_path, span_start, span_end
                                    )
                                except OSError as exc:
                                    errors.append(
                                        f"{prefix} cannot hash extraction span: {exc}"
                                    )
                                else:
                                    if (
                                        actual_span_sha256.casefold()
                                        != extraction_sha256.casefold()
                                    ):
                                        errors.append(
                                            f"{prefix} extraction_sha256 does not match "
                                            "the registered artifact span"
                                        )
                            if not str(row.get("review_notes", "")).strip():
                                errors.append(f"{prefix} lacks review_notes")
                        elif depth == "exact_duplicate_inherited":
                            canonical = str(row.get("canonical_unit_id", "")).strip()
                            if not canonical:
                                errors.append(
                                    f"{prefix} exact duplicate lacks canonical_unit_id"
                                )
                            elif canonical == unit_id:
                                errors.append(
                                    f"{prefix} canonical_unit_id cannot equal unit_id"
                                )
                            elif unit_id:
                                connection.execute(
                                    "INSERT INTO duplicate_links VALUES (?, ?, ?)",
                                    (index, unit_id, canonical),
                                )
                            if not duplicate_group_id:
                                errors.append(
                                    f"{prefix} exact duplicate lacks duplicate_group_id"
                                )
                            if str(row.get("candidate_theme_ids", "")).strip():
                                errors.append(
                                    f"{prefix} exact duplicate cannot carry "
                                    "candidate_theme_ids"
                                )
                        elif str(row.get("candidate_theme_ids", "")).strip():
                            errors.append(
                                f"{prefix} non-reviewed unit cannot carry candidate_theme_ids"
                            )

                        if unit_id in evidence_unit_ids:
                            if unit_id in audit["evidence_depths"]:
                                errors.append(
                                    f"candidate evidence unit {unit_id} appears more than once "
                                    "in corpus-reading-ledger.csv"
                                )
                            audit["evidence_depths"][unit_id] = depth
                            audit["evidence_holdout_roles"][unit_id] = holdout_role

                connection.commit()
                audit["unique_unit_count"] = connection.execute(
                    "SELECT COUNT(*) FROM units"
                ).fetchone()[0]
                audit["distinct_long_document_parent_count"] = connection.execute(
                    "SELECT COUNT(DISTINCT parent_document_id) FROM units "
                    "WHERE route_subset = 'long-document' AND parent_document_id <> ''"
                ).fetchone()[0]
                audit[
                    "distinct_semantically_reviewed_long_document_parent_count"
                ] = connection.execute(
                    "SELECT COUNT(DISTINCT parent_document_id) FROM units "
                    "WHERE route_subset = 'long-document' "
                    "AND parent_document_id <> '' "
                    "AND review_depth IN ('full_text', 'extracted_representation')"
                ).fetchone()[0]
                audit["derived_full_text_long_document_parent_count"] = connection.execute(
                    "SELECT COUNT(*) FROM ("
                    "SELECT parent_document_id FROM units "
                    "WHERE route_subset = 'long-document' AND parent_document_id <> '' "
                    "GROUP BY parent_document_id "
                    "HAVING SUM(CASE WHEN review_depth IN "
                    "('full_text', 'extracted_representation') THEN 1 ELSE 0 END) > 0 "
                    "AND SUM(CASE WHEN review_depth IN "
                    "('extracted_representation', 'not_semantically_reviewed', 'failed') "
                    "THEN 1 ELSE 0 END) = 0)"
                ).fetchone()[0]
                audit["derived_extracted_long_document_parent_count"] = connection.execute(
                    "SELECT COUNT(*) FROM ("
                    "SELECT parent_document_id FROM units "
                    "WHERE route_subset = 'long-document' AND parent_document_id <> '' "
                    "GROUP BY parent_document_id "
                    "HAVING SUM(CASE WHEN review_depth IN "
                    "('full_text', 'extracted_representation') THEN 1 ELSE 0 END) > 0 "
                    "AND SUM(CASE WHEN review_depth IN "
                    "('extracted_representation', 'not_semantically_reviewed', 'failed') "
                    "THEN 1 ELSE 0 END) > 0)"
                ).fetchone()[0]
                for (
                    row_number,
                    unit_id,
                    canonical_id,
                    canonical_depth,
                    duplicate_group_id,
                    canonical_group_id,
                    content_sha256,
                    canonical_content_sha256,
                    content_length,
                    canonical_content_length,
                ) in connection.execute(
                    "SELECT d.row_number, d.unit_id, d.canonical_unit_id, "
                    "canonical.review_depth, duplicate.duplicate_group_id, "
                    "canonical.duplicate_group_id, duplicate.content_sha256, "
                    "canonical.content_sha256, duplicate.content_length, "
                    "canonical.content_length FROM duplicate_links d "
                    "LEFT JOIN units duplicate ON duplicate.unit_id = d.unit_id "
                    "LEFT JOIN units canonical ON canonical.unit_id = d.canonical_unit_id"
                ):
                    if canonical_depth is None:
                        errors.append(
                            "corpus-reading-ledger.csv row "
                            f"{row_number} canonical_unit_id {canonical_id} does not exist"
                        )
                    elif canonical_depth not in SEMANTIC_REVIEW_DEPTHS:
                        errors.append(
                            "corpus-reading-ledger.csv row "
                            f"{row_number} canonical_unit_id {canonical_id} is not "
                            "semantically reviewed"
                        )
                    if not canonical_group_id:
                        errors.append(
                            "corpus-reading-ledger.csv row "
                            f"{row_number} canonical unit {canonical_id} lacks matching "
                            "duplicate_group_id"
                        )
                    elif duplicate_group_id != canonical_group_id:
                        errors.append(
                            "corpus-reading-ledger.csv row "
                            f"{row_number} duplicate_group_id does not match canonical "
                            f"unit {canonical_id}"
                        )
                    if content_sha256 != canonical_content_sha256:
                        errors.append(
                            "corpus-reading-ledger.csv row "
                            f"{row_number} content_sha256 does not match canonical "
                            f"unit {canonical_id}"
                        )
                    if content_length != canonical_content_length:
                        errors.append(
                            "corpus-reading-ledger.csv row "
                            f"{row_number} content_length does not match canonical "
                            f"unit {canonical_id}"
                        )
                for content_sha256, canonical_count in connection.execute(
                    "SELECT duplicate.content_sha256, "
                    "COUNT(DISTINCT d.canonical_unit_id) FROM duplicate_links d "
                    "JOIN units duplicate ON duplicate.unit_id = d.unit_id "
                    "GROUP BY duplicate.content_sha256 "
                    "HAVING COUNT(DISTINCT d.canonical_unit_id) > 1"
                ):
                    errors.append(
                        "corpus-reading-ledger.csv content_sha256 "
                        f"{content_sha256} maps to {canonical_count} canonical units; "
                        "one content hash must map to one canonical unit"
                    )
                for duplicate_group_id, hash_count in connection.execute(
                    "SELECT duplicate_group_id, COUNT(DISTINCT content_sha256) "
                    "FROM units WHERE duplicate_group_id <> '' "
                    "GROUP BY duplicate_group_id "
                    "HAVING COUNT(DISTINCT content_sha256) > 1"
                ):
                    errors.append(
                        "corpus-reading-ledger.csv duplicate_group_id "
                        f"{duplicate_group_id} contains {hash_count} content hashes; "
                        "an exact-duplicate group must contain one content hash"
                    )
    except (OSError, csv.Error, sqlite3.Error) as exc:
        errors.append(f"Cannot read CSV {path.name}: {exc}")
    return audit


def validate_theme_reconnaissance(
    root: Path,
    *,
    require_approval: bool = False,
) -> dict[str, Any]:
    """Return a machine-readable audit of reconnaissance and authorization."""
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    result: dict[str, Any] = {
        "valid": False,
        "errors": errors,
        "warnings": warnings,
        "reconnaissance_id": "",
        "reading_plan_id": "",
        "reading_mode": "",
        "corpus_fingerprint": "",
        "route": "",
        "research_question": "",
        "authorization_id": "",
        "gate_status": "",
    }
    if not root.is_dir():
        errors.append(f"Reconnaissance directory does not exist: {root}")
        return result

    for name in sorted(REQUIRED_FILES):
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")
    if errors:
        return result

    profile = _read_json(root / "corpus-profile.json", errors)
    reading_plan = _read_json(root / "corpus-reading-plan.json", errors)
    reconnaissance = _read_json(root / "theme-reconnaissance.json", errors)
    authorization = _read_json(root / "modeling-authorization.json", errors)
    header, candidates = _read_candidates(
        root / "theme-candidate-audit.csv", errors
    )
    if not all(
        isinstance(item, dict)
        for item in (profile, reading_plan, reconnaissance, authorization)
    ):
        return result

    missing_columns = sorted(CANDIDATE_FIELDS.difference(header))
    errors.extend(
        f"theme-candidate-audit.csv lacks required column: {field}"
        for field in missing_columns
    )
    if not candidates:
        errors.append(
            "theme-candidate-audit.csv must contain at least one candidate theme"
        )

    fingerprint = str(reconnaissance.get("corpus_fingerprint", "")).strip()
    reconnaissance_id = str(
        reconnaissance.get("reconnaissance_id", "")
    ).strip()
    reading_plan_id = str(reading_plan.get("reading_plan_id", "")).strip()
    reading_mode = str(reading_plan.get("mode", "")).strip()
    authorization_id = str(authorization.get("authorization_id", "")).strip()
    gate_status = str(authorization.get("gate_status", "")).strip()
    result.update(
        reconnaissance_id=reconnaissance_id,
        reading_plan_id=reading_plan_id,
        reading_mode=reading_mode,
        corpus_fingerprint=fingerprint,
        route=str(reconnaissance.get("route", "")).strip(),
        research_question=str(reconnaissance.get("research_question", "")).strip(),
        authorization_id=authorization_id,
        gate_status=gate_status,
    )

    if reconnaissance.get("schema_version") != 1:
        errors.append("theme-reconnaissance.json schema_version must be 1")
    if authorization.get("schema_version") != 1:
        errors.append("modeling-authorization.json schema_version must be 1")
    if reading_plan.get("schema_version") != 1:
        errors.append("corpus-reading-plan.json schema_version must be 1")
    if not fingerprint:
        errors.append("theme-reconnaissance.json must contain corpus_fingerprint")
    if not reconnaissance_id:
        errors.append("theme-reconnaissance.json must contain reconnaissance_id")
    if not reading_plan_id:
        errors.append("corpus-reading-plan.json must contain reading_plan_id")
    if str(reconnaissance.get("reading_plan_id", "")).strip() != reading_plan_id:
        errors.append("theme-reconnaissance.json reading_plan_id does not match")
    if str(reading_plan.get("reconnaissance_id", "")).strip() != reconnaissance_id:
        errors.append("corpus-reading-plan.json reconnaissance_id does not match")
    if not str(reconnaissance.get("created_at", "")).strip():
        errors.append("theme-reconnaissance.json created_at must not be blank")
    if not str(reconnaissance.get("research_question", "")).strip():
        errors.append("theme-reconnaissance.json research_question must not be blank")

    for source, value in (
        ("corpus-profile.json", profile.get("corpus_fingerprint")),
        ("corpus-reading-plan.json", reading_plan.get("corpus_fingerprint")),
        (
            "modeling-authorization.json",
            authorization.get("corpus_fingerprint"),
        ),
    ):
        if str(value or "").strip() != fingerprint:
            errors.append(
                f"{source} corpus_fingerprint does not match "
                "theme-reconnaissance.json"
            )
    if (
        str(authorization.get("reconnaissance_id", "")).strip()
        != reconnaissance_id
    ):
        errors.append("modeling-authorization.json reconnaissance_id does not match")
    if str(authorization.get("reading_plan_id", "")).strip() != reading_plan_id:
        errors.append("modeling-authorization.json reading_plan_id does not match")
    if str(authorization.get("reading_mode", "")).strip() != reading_mode:
        errors.append("modeling-authorization.json reading_mode does not match")

    route = str(reconnaissance.get("route", "")).strip()
    if route not in ROUTES:
        errors.append(
            "theme-reconnaissance.json route must be network-short, "
            "long-document, or mixed"
        )

    user_theme = reconnaissance.get("user_theme")
    if not isinstance(user_theme, dict):
        errors.append("theme-reconnaissance.json user_theme must be an object")
    else:
        if not str(user_theme.get("mainline", "")).strip():
            errors.append("user_theme.mainline must not be blank")
        if user_theme.get("mode") != "coverage_and_interpretation_anchor":
            errors.append(
                "user_theme.mode must be coverage_and_interpretation_anchor"
            )
        if user_theme.get("allow_emergent_themes") is not True:
            errors.append("user_theme.allow_emergent_themes must be true")

    if reading_mode not in READING_MODES:
        errors.append(
            "corpus-reading-plan.json mode must be direct_full_text or "
            "progressive_extraction"
        )

    decision_basis = reading_plan.get("decision_basis")
    if not isinstance(decision_basis, dict):
        errors.append("corpus-reading-plan.json decision_basis must be an object")
    else:
        estimated_tokens = _count(
            decision_basis.get("estimated_unique_full_text_tokens"),
            "decision_basis.estimated_unique_full_text_tokens",
            errors,
        )
        usable_tokens = _count(
            decision_basis.get("usable_reconnaissance_tokens"),
            "decision_basis.usable_reconnaissance_tokens",
            errors,
        )
        if estimated_tokens == 0:
            errors.append(
                "decision_basis.estimated_unique_full_text_tokens must be positive"
            )
        if usable_tokens == 0:
            errors.append(
                "decision_basis.usable_reconnaissance_tokens must be positive"
            )
        if not str(decision_basis.get("time_budget", "")).strip():
            errors.append("decision_basis.time_budget must not be blank")
        if not str(decision_basis.get("reason", "")).strip():
            errors.append("decision_basis.reason must not be blank")
        feasible = decision_basis.get("direct_full_text_feasible")
        if not isinstance(feasible, bool):
            errors.append(
                "decision_basis.direct_full_text_feasible must be a boolean"
            )
        elif reading_mode == "direct_full_text" and feasible is not True:
            errors.append(
                "direct_full_text mode requires direct_full_text_feasible=true"
            )
        elif reading_mode == "progressive_extraction" and feasible is not False:
            errors.append(
                "progressive_extraction mode requires "
                "direct_full_text_feasible=false"
            )

    census = reading_plan.get("census")
    if not isinstance(census, dict):
        errors.append("corpus-reading-plan.json census must be an object")
    else:
        if census.get("ledger_artifact") != "corpus-reading-ledger.csv":
            errors.append(
                "census.ledger_artifact must be corpus-reading-ledger.csv"
            )
        if census.get("all_source_units_profiled") is not True:
            errors.append("census.all_source_units_profiled must be true")
        _nonempty_string_list(
            census.get("profile_fields"), "census.profile_fields", errors
        )
        for field in ("exact_duplicate_policy", "near_duplicate_policy"):
            if not str(census.get(field, "")).strip():
                errors.append(f"census.{field} must not be blank")

    extraction = reading_plan.get("extraction")
    registered_artifacts: dict[str, Path] = {}
    if not isinstance(extraction, dict):
        errors.append("corpus-reading-plan.json extraction must be an object")
    else:
        if extraction.get("streaming_or_batched") is not True:
            errors.append("extraction.streaming_or_batched must be true")
        if extraction.get("raw_text_preserved") is not True:
            errors.append("extraction.raw_text_preserved must be true")
        _nonempty_string_list(
            extraction.get("unit_card_fields"),
            "extraction.unit_card_fields",
            errors,
        )
        registered_artifacts = _register_extraction_artifacts(
            extraction.get("registered_artifacts"), root, errors
        )
        for field in (
            "short_text_policy",
            "long_document_policy",
            "card_size_basis",
        ):
            if not str(extraction.get(field, "")).strip():
                errors.append(f"extraction.{field} must not be blank")

    selection = reading_plan.get("selection")
    selection_channels: list[str] = []
    if not isinstance(selection, dict):
        errors.append("corpus-reading-plan.json selection must be an object")
    else:
        _nonempty_string_list(
            selection.get("stratification_fields"),
            "selection.stratification_fields",
            errors,
        )
        selection_channels = _nonempty_string_list(
            selection.get("selection_channels"),
            "selection.selection_channels",
            errors,
        )
        for field in ("candidate_generation_rule", "escalation_rule"):
            if not str(selection.get(field, "")).strip():
                errors.append(f"selection.{field} must not be blank")
    if reading_mode == "direct_full_text":
        if "complete_unique_content" not in selection_channels:
            errors.append(
                "direct_full_text mode requires selection channel "
                "complete_unique_content"
            )
    elif reading_mode == "progressive_extraction":
        missing_channels = sorted(
            PROGRESSIVE_SELECTION_CHANNELS.difference(selection_channels)
        )
        errors.extend(
            f"progressive_extraction selection is missing channel: {channel}"
            for channel in missing_channels
        )

    stopping = reading_plan.get("stopping")
    holdout_count: int | None = None
    new_candidate_count: int | None = None
    material_change: bool | None = None
    holdout_audit_round_id = ""
    holdout_sampling_frame_sha256 = ""
    candidate_map_freeze_sha256 = ""
    if not isinstance(stopping, dict):
        errors.append("corpus-reading-plan.json stopping must be an object")
    else:
        for field in ("estimand", "rule", "evidence"):
            if not str(stopping.get(field, "")).strip():
                errors.append(f"stopping.{field} must not be blank")
        stopping_text = " ".join(
            str(stopping.get(field, ""))
            for field in ("estimand", "rule", "evidence")
        )
        if STOPPING_RESOURCE_LIMIT_PATTERN.search(stopping_text):
            errors.append(
                "stopping evidence must satisfy the local semantic/holdout rule; "
                "a time, token, budget, or other resource limit cannot be a "
                "stopping basis"
            )
        if stopping.get("status") != "satisfied":
            errors.append("stopping.status must be satisfied before preview")
        if stopping.get("reconnaissance_state") != "complete_for_preview":
            errors.append(
                "stopping.reconnaissance_state must be complete_for_preview before preview"
            )
        if stopping.get("resource_budget_exhausted") is not False:
            errors.append(
                "stopping.resource_budget_exhausted=false is required before preview; "
                "resource exhaustion produces an interim reconnaissance"
            )
        holdout_count = _count(
            stopping.get("holdout_unit_count"),
            "stopping.holdout_unit_count",
            errors,
        )
        new_candidate_count = _count(
            stopping.get("new_candidate_theme_count"),
            "stopping.new_candidate_theme_count",
            errors,
        )
        material_change = stopping.get("material_change_detected")
        if not isinstance(material_change, bool):
            errors.append("stopping.material_change_detected must be a boolean")
        if reading_mode == "direct_full_text":
            if stopping.get("termination_basis") != "complete_full_text_review":
                errors.append(
                    "direct_full_text stopping.termination_basis must be "
                    "complete_full_text_review"
                )
            if stopping.get("holdout_audit_performed") is not False:
                errors.append(
                    "direct_full_text mode requires holdout_audit_performed=false"
                )
            if stopping.get("decision") != "not_applicable_full_text":
                errors.append(
                    "direct_full_text stopping.decision must be "
                    "not_applicable_full_text"
                )
            if material_change is not False:
                errors.append(
                    "direct_full_text stopping requires material_change_detected=false"
                )
            if holdout_count not in (None, 0) or new_candidate_count not in (None, 0):
                errors.append(
                    "direct_full_text stopping requires zero holdout units and zero "
                    "new candidate themes"
                )
        elif reading_mode == "progressive_extraction":
            if stopping.get("termination_basis") != "local_holdout_rule_satisfied":
                errors.append(
                    "progressive_extraction stopping.termination_basis must be "
                    "local_holdout_rule_satisfied"
                )
            if stopping.get("holdout_audit_performed") is not True:
                errors.append(
                    "progressive_extraction requires an independent holdout audit"
                )
            if holdout_count == 0:
                errors.append(
                    "progressive_extraction stopping.holdout_unit_count must be "
                    "positive"
                )
            if stopping.get("decision") != "stop_with_residual_risk":
                errors.append(
                    "progressive_extraction stopping.decision must be "
                    "stop_with_residual_risk before preview"
                )
            if new_candidate_count not in (None, 0) or material_change is not False:
                errors.append(
                    "stop_with_residual_risk requires zero new candidate themes and "
                    "material_change_detected=false"
                )
            holdout_audit_round_id = str(
                stopping.get("holdout_audit_round_id", "")
            ).strip()
            holdout_sampling_frame_sha256 = str(
                stopping.get("holdout_sampling_frame_sha256", "")
            ).strip()
            candidate_map_freeze_sha256 = str(
                stopping.get("candidate_map_freeze_sha256", "")
            ).strip()
            if not holdout_audit_round_id:
                errors.append(
                    "progressive_extraction stopping.holdout_audit_round_id must not "
                    "be blank"
                )
            for field, value in (
                ("holdout_sampling_frame_sha256", holdout_sampling_frame_sha256),
                ("candidate_map_freeze_sha256", candidate_map_freeze_sha256),
            ):
                if not CONTENT_SHA256_PATTERN.fullmatch(value):
                    errors.append(
                        f"progressive_extraction stopping.{field} must be sha256: "
                        "followed by 64 hexadecimal characters"
                    )
            try:
                actual_candidate_map_sha256 = _sha256_file(
                    root / "theme-candidate-audit.csv"
                )
            except OSError as exc:
                errors.append(f"cannot hash theme-candidate-audit.csv: {exc}")
            else:
                if (
                    CONTENT_SHA256_PATTERN.fullmatch(candidate_map_freeze_sha256)
                    and candidate_map_freeze_sha256.casefold()
                    != actual_candidate_map_sha256.casefold()
                ):
                    errors.append(
                        "stopping.candidate_map_freeze_sha256 does not match the "
                        "frozen theme-candidate-audit.csv"
                    )
    if not str(reading_plan.get("residual_risk", "")).strip():
        errors.append("corpus-reading-plan.json residual_risk must not be blank")

    evidence_unit_ids: set[str] = set()
    for row in candidates:
        evidence_unit_ids.update(
            item.strip()
            for item in str(row.get("evidence_unit_ids", "")).split("|")
            if item.strip()
        )
    ledger_audit = _audit_reading_ledger(
        root / "corpus-reading-ledger.csv",
        reading_plan_id=reading_plan_id,
        reading_mode=reading_mode,
        route=route,
        registered_artifacts=registered_artifacts,
        holdout_audit_round_id=holdout_audit_round_id,
        holdout_sampling_frame_sha256=holdout_sampling_frame_sha256,
        candidate_map_freeze_sha256=candidate_map_freeze_sha256,
        evidence_unit_ids=evidence_unit_ids,
        errors=errors,
    )
    if reading_mode == "progressive_extraction":
        required_subsets = (
            ("network-short", "long-document") if route == "mixed" else (route,)
        )
        for route_subset in required_subsets:
            subset_depths = ledger_audit["route_subset_depth_counts"].get(
                route_subset, {}
            )
            subset_semantic_count = sum(
                subset_depths.get(depth, 0) for depth in SEMANTIC_REVIEW_DEPTHS
            )
            if subset_semantic_count == 0:
                errors.append(
                    "progressive_extraction requires semantic review in both "
                    "network-short and long-document route subsets"
                    if route == "mixed"
                    else f"progressive_extraction requires semantic review in {route_subset}"
                )
            missing_subset_channels = sorted(
                PROGRESSIVE_SELECTION_CHANNELS.difference(
                    ledger_audit["route_subset_channels"].get(route_subset, set())
                )
            )
            if route == "mixed":
                errors.extend(
                    "progressive_extraction ledger route subset "
                    f"{route_subset} is missing selection channel: {channel}"
                    for channel in missing_subset_channels
                )
            else:
                errors.extend(
                    "progressive_extraction ledger is missing selection channel: "
                    f"{channel}"
                    for channel in missing_subset_channels
                )
            if (
                ledger_audit["route_subset_holdout_counts"]
                .get(route_subset, {})
                .get("final_independent", 0)
                == 0
            ):
                errors.append(
                    "progressive_extraction ledger route subset "
                    f"{route_subset} requires an independent final holdout"
                )
        final_holdout_count = ledger_audit["holdout_role_counts"].get(
            "final_independent", 0
        )
        if holdout_count is not None and final_holdout_count != holdout_count:
            errors.append(
                "stopping.holdout_unit_count must equal the number of "
                "final_independent rows in corpus-reading-ledger.csv"
            )
        actual_holdout_frame_sha256 = compute_holdout_sampling_frame_sha256(
            ledger_audit["final_holdout_unit_ids"]
        )
        if (
            CONTENT_SHA256_PATTERN.fullmatch(holdout_sampling_frame_sha256)
            and actual_holdout_frame_sha256.casefold()
            != holdout_sampling_frame_sha256.casefold()
        ):
            errors.append(
                "stopping.holdout_sampling_frame_sha256 does not match the final "
                "independent holdout unit set"
            )
        if (
            new_candidate_count is not None
            and len(ledger_audit["holdout_new_candidate_theme_ids"])
            != new_candidate_count
        ):
            errors.append(
                "stopping.new_candidate_theme_count must equal the distinct candidate "
                "themes reported by final holdout rows"
            )
        derived_material_change = (
            ledger_audit["holdout_material_change_count"] > 0
            or bool(ledger_audit["holdout_new_candidate_theme_ids"])
        )
        if isinstance(material_change, bool) and derived_material_change != material_change:
            errors.append(
                "stopping.material_change_detected must equal the final holdout row outcomes"
            )
    if route == "mixed" and not all(
        ledger_audit["route_subset_counts"].get(name, 0) > 0
        for name in ("network-short", "long-document")
    ):
        errors.append(
            "mixed route ledger must contain both network-short and long-document "
            "route subsets"
        )
    for evidence_unit_id in sorted(evidence_unit_ids):
        evidence_depth = ledger_audit["evidence_depths"].get(evidence_unit_id)
        if evidence_depth not in SEMANTIC_REVIEW_DEPTHS:
            errors.append(
                f"candidate evidence unit {evidence_unit_id} must have full_text "
                "or extracted_representation review in corpus-reading-ledger.csv"
            )
        if (
            ledger_audit["evidence_holdout_roles"].get(evidence_unit_id)
            == "final_independent"
        ):
            errors.append(
                f"candidate evidence unit {evidence_unit_id} is part of the final "
                "independent holdout and cannot support the frozen candidate map"
            )

    coverage = reconnaissance.get("coverage")
    if not isinstance(coverage, dict):
        errors.append("theme-reconnaissance.json coverage must be an object")
    else:
        source = _count(
            coverage.get("source_unit_count"),
            "coverage.source_unit_count",
            errors,
        )
        eligible = _count(
            coverage.get("eligible_unit_count"),
            "coverage.eligible_unit_count",
            errors,
        )
        profiled = _count(
            coverage.get("profiled_source_unit_count"),
            "coverage.profiled_source_unit_count",
            errors,
        )
        reviewed = _count(
            coverage.get("reviewed_unit_count"),
            "coverage.reviewed_unit_count",
            errors,
        )
        full_text_reviewed = _count(
            coverage.get("full_text_reviewed_unit_count"),
            "coverage.full_text_reviewed_unit_count",
            errors,
        )
        extracted_reviewed = _count(
            coverage.get("extracted_representation_reviewed_unit_count"),
            "coverage.extracted_representation_reviewed_unit_count",
            errors,
        )
        inherited = _count(
            coverage.get("duplicate_inherited_unit_count"),
            "coverage.duplicate_inherited_unit_count",
            errors,
        )
        unreviewed = _count(
            coverage.get("unreviewed_unit_count"),
            "coverage.unreviewed_unit_count",
            errors,
        )
        excluded = _count(
            coverage.get("excluded_unit_count"),
            "coverage.excluded_unit_count",
            errors,
        )
        failed = _count(
            coverage.get("failed_unit_count"),
            "coverage.failed_unit_count",
            errors,
        )
        profile_count = _count(
            profile.get("unit_count"),
            "corpus-profile.json unit_count",
            errors,
        )
        if None not in (
            source,
            profiled,
            eligible,
            reviewed,
            full_text_reviewed,
            extracted_reviewed,
            inherited,
            unreviewed,
            excluded,
            failed,
        ):
            if profile_count is not None and source != profile_count:
                errors.append(
                    "coverage.source_unit_count must match "
                    "corpus-profile.json unit_count"
                )
            if source != eligible + excluded:
                errors.append(
                    "coverage.source_unit_count must equal "
                    "eligible_unit_count + excluded_unit_count"
                )
            if profiled != source:
                errors.append(
                    "coverage.profiled_source_unit_count must equal "
                    "source_unit_count"
                )
            if reviewed != full_text_reviewed + extracted_reviewed:
                errors.append(
                    "coverage.reviewed_unit_count must equal "
                    "full_text_reviewed_unit_count + "
                    "extracted_representation_reviewed_unit_count"
                )
            if eligible != reviewed + inherited + unreviewed + failed:
                errors.append(
                    "coverage.eligible_unit_count must equal reviewed_unit_count + "
                    "duplicate_inherited_unit_count + unreviewed_unit_count + "
                    "failed_unit_count"
                )
            if failed != 0:
                errors.append(
                    "coverage.failed_unit_count must be zero before corpus "
                    "accounting is complete"
                )
            if coverage.get("accounting_complete") is not True:
                errors.append("coverage.accounting_complete must be true")
            expected_full_text_complete = (
                extracted_reviewed == 0 and unreviewed == 0 and failed == 0
            )
            if coverage.get("full_text_review_complete") is not expected_full_text_complete:
                errors.append(
                    "coverage.full_text_review_complete is inconsistent with "
                    "extracted, unreviewed, or failed counts"
                )
            if reading_mode == "direct_full_text" and not expected_full_text_complete:
                errors.append(
                    "direct_full_text mode requires every eligible canonical unit "
                    "to receive full-text review"
                )
            if reading_mode == "progressive_extraction" and reviewed == 0:
                errors.append(
                    "progressive_extraction requires at least one semantically "
                    "reviewed unit"
                )

            depth_counts = ledger_audit["depth_counts"]
            ledger_expectations = {
                "full_text": full_text_reviewed,
                "extracted_representation": extracted_reviewed,
                "not_semantically_reviewed": unreviewed,
                "exact_duplicate_inherited": inherited,
                "excluded": excluded,
                "failed": failed,
            }
            if ledger_audit["row_count"] != source:
                errors.append(
                    "corpus-reading-ledger.csv row count must equal "
                    "coverage.source_unit_count"
                )
            if ledger_audit["unique_unit_count"] != source:
                errors.append(
                    "corpus-reading-ledger.csv must contain exactly one unique "
                    "unit_id per source unit"
                )
            for depth, expected in ledger_expectations.items():
                if depth_counts.get(depth) != expected:
                    errors.append(
                        f"corpus-reading-ledger.csv {depth} count must equal "
                        f"the corresponding coverage count ({expected})"
                    )
        failed_ids = coverage.get("failed_unit_ids")
        if not isinstance(failed_ids, list):
            errors.append("coverage.failed_unit_ids must be a list")
        elif failed is not None and len(failed_ids) != failed:
            errors.append(
                "coverage.failed_unit_ids length must equal failed_unit_count"
            )

    parent = reconnaissance.get("parent_document_coverage")
    if route in {"long-document", "mixed"}:
        if not isinstance(parent, dict) or parent.get("applicable") is not True:
            errors.append(
                "Long-document and mixed routes require applicable "
                "parent_document_coverage"
            )
        else:
            eligible_parent = _count(
                parent.get("eligible_parent_document_count"),
                "parent_document_coverage.eligible_parent_document_count",
                errors,
            )
            profiled_parent = _count(
                parent.get("profiled_parent_document_count"),
                "parent_document_coverage.profiled_parent_document_count",
                errors,
            )
            reviewed_parent = _count(
                parent.get("reviewed_parent_document_count"),
                "parent_document_coverage.reviewed_parent_document_count",
                errors,
            )
            full_text_parent = _count(
                parent.get("full_text_reviewed_parent_document_count"),
                "parent_document_coverage.full_text_reviewed_parent_document_count",
                errors,
            )
            extracted_parent = _count(
                parent.get(
                    "extracted_representation_reviewed_parent_document_count"
                ),
                "parent_document_coverage."
                "extracted_representation_reviewed_parent_document_count",
                errors,
            )
            inherited_parent = _count(
                parent.get("duplicate_inherited_parent_document_count"),
                "parent_document_coverage."
                "duplicate_inherited_parent_document_count",
                errors,
            )
            unreviewed_parent = _count(
                parent.get("unreviewed_parent_document_count"),
                "parent_document_coverage.unreviewed_parent_document_count",
                errors,
            )
            failed_parent = _count(
                parent.get("failed_parent_document_count"),
                "parent_document_coverage.failed_parent_document_count",
                errors,
            )
            if None not in (
                eligible_parent,
                profiled_parent,
                reviewed_parent,
                full_text_parent,
                extracted_parent,
                inherited_parent,
                unreviewed_parent,
                failed_parent,
            ):
                if profiled_parent != eligible_parent:
                    errors.append(
                        "parent_document_coverage.profiled_parent_document_count "
                        "must equal eligible_parent_document_count"
                    )
                if (
                    profiled_parent
                    != ledger_audit["distinct_long_document_parent_count"]
                ):
                    errors.append(
                        "parent_document_coverage.profiled_parent_document_count "
                        "must equal the number of distinct parent_document_id values "
                        "in the long-document ledger subset"
                    )
                if reviewed_parent != full_text_parent + extracted_parent:
                    errors.append(
                        "parent_document_coverage.reviewed_parent_document_count "
                        "must equal full-text plus extracted-representation counts"
                    )
                if (
                    reviewed_parent
                    != ledger_audit[
                        "distinct_semantically_reviewed_long_document_parent_count"
                    ]
                ):
                    errors.append(
                        "parent_document_coverage.reviewed_parent_document_count "
                        "must equal the number of distinct semantically reviewed "
                        "parent_document_id values in the long-document ledger subset"
                    )
                if (
                    full_text_parent
                    != ledger_audit[
                        "derived_full_text_long_document_parent_count"
                    ]
                ):
                    errors.append(
                        "parent_document_coverage."
                        "full_text_reviewed_parent_document_count must equal the "
                        "full-text parent set derived from ledger depths"
                    )
                if (
                    extracted_parent
                    != ledger_audit[
                        "derived_extracted_long_document_parent_count"
                    ]
                ):
                    errors.append(
                        "parent_document_coverage."
                        "extracted_representation_reviewed_parent_document_count "
                        "must equal the partial/extracted parent set derived from "
                        "ledger depths"
                    )
                if eligible_parent != (
                    reviewed_parent
                    + inherited_parent
                    + unreviewed_parent
                    + failed_parent
                ):
                    errors.append("parent-document counts are inconsistent")
                if failed_parent != 0 or parent.get("accounting_complete") is not True:
                    errors.append(
                        "parent-document accounting must be complete with zero failures"
                    )
                expected_parent_full_text_complete = (
                    extracted_parent == 0
                    and unreviewed_parent == 0
                    and failed_parent == 0
                )
                if (
                    parent.get("full_text_review_complete")
                    is not expected_parent_full_text_complete
                ):
                    errors.append(
                        "parent_document_coverage.full_text_review_complete is "
                        "inconsistent with extracted, unreviewed, or failed counts"
                    )
                if (
                    reading_mode == "direct_full_text"
                    and not expected_parent_full_text_complete
                ):
                    errors.append(
                        "direct_full_text mode requires complete parent-document "
                        "full-text review"
                    )

    candidate_ids: list[str] = []
    for index, row in enumerate(candidates, start=2):
        prefix = f"theme-candidate-audit.csv row {index}"
        candidate_id = str(row.get("candidate_theme_id", "")).strip()
        if not candidate_id:
            errors.append(f"{prefix} lacks candidate_theme_id")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix} duplicates candidate_theme_id {candidate_id}")
        else:
            candidate_ids.append(candidate_id)
        if str(row.get("reconnaissance_id", "")).strip() != reconnaissance_id:
            errors.append(f"{prefix} reconnaissance_id does not match")
        if str(row.get("hierarchy_level", "")).strip() not in HIERARCHY_LEVELS:
            errors.append(f"{prefix} hierarchy_level must be coarse or fine")
        if (
            str(row.get("relation_to_user_mainline", "")).strip()
            not in RELATIONS
        ):
            errors.append(f"{prefix} has an invalid relation_to_user_mainline")
        for field in (
            "route_subset",
            "provisional_label",
            "theme_type",
            "definition",
            "inclusion",
            "exclusion",
            "independent_support",
            "evidence_unit_ids",
            "source_or_parent_spread",
            "duplicate_or_artifact_risk",
            "uncertainty",
            "claim_scope",
        ):
            if not str(row.get(field, "")).strip():
                errors.append(f"{prefix} lacks {field}")
        if str(row.get("prevalence_claimed", "")).strip().lower() != "false":
            errors.append(
                f"{prefix} prevalence_claimed must be false; adaptive "
                "reconnaissance cannot authorize a corpus prevalence claim"
            )
        if str(row.get("claim_scope", "")).strip() != "semantic_evidence_only":
            errors.append(
                f"{prefix} claim_scope must be semantic_evidence_only"
            )
        for field in (
            "provisional_label",
            "definition",
            "inclusion",
            "exclusion",
            "independent_support",
            "source_or_parent_spread",
            "duplicate_or_artifact_risk",
            "uncertainty",
            "user_instruction",
        ):
            if _contains_unsupported_prevalence_claim(row.get(field, "")):
                errors.append(
                    f"{prefix} contains an unsupported prevalence claim in {field}"
                )
        disposition = str(row.get("user_disposition", "")).strip()
        if disposition and disposition not in DISPOSITIONS:
            errors.append(f"{prefix} has an invalid user_disposition")
        if disposition and not str(row.get("user_instruction", "")).strip():
            errors.append(
                f"{prefix} requires user_instruction when disposition is recorded"
            )

    candidate_id_set = set(candidate_ids)
    candidate_levels = {
        str(row.get("candidate_theme_id", "")).strip(): str(
            row.get("hierarchy_level", "")
        ).strip()
        for row in candidates
        if str(row.get("candidate_theme_id", "")).strip()
    }
    candidate_relations = {
        str(row.get("candidate_theme_id", "")).strip(): str(
            row.get("relation_to_user_mainline", "")
        ).strip()
        for row in candidates
        if str(row.get("candidate_theme_id", "")).strip()
    }
    for index, row in enumerate(candidates, start=2):
        parent_id = str(row.get("parent_candidate_theme_id", "")).strip()
        candidate_id = str(row.get("candidate_theme_id", "")).strip()
        level = str(row.get("hierarchy_level", "")).strip()
        if parent_id and parent_id not in candidate_id_set:
            errors.append(
                f"theme-candidate-audit.csv row {index} references unknown "
                "parent_candidate_theme_id"
            )
        if parent_id and parent_id == candidate_id:
            errors.append(
                f"theme-candidate-audit.csv row {index} cannot be its own parent"
            )
        if level == "coarse" and parent_id:
            errors.append(
                f"theme-candidate-audit.csv row {index} coarse theme cannot "
                "have a parent"
            )
        if (
            level == "fine"
            and parent_id
            and candidate_levels.get(parent_id) != "coarse"
        ):
            errors.append(
                f"theme-candidate-audit.csv row {index} fine-theme parent "
                "must be coarse"
            )

    estimated_candidate_ids: set[str] = set()
    estimate = reconnaissance.get("topic_count_estimate")
    if not isinstance(estimate, dict):
        errors.append(
            "theme-reconnaissance.json topic_count_estimate must be an object"
        )
    else:
        if estimate.get("interpretation") != "pre_model_hypothesis_not_target_k":
            errors.append(
                "topic_count_estimate.interpretation must be "
                "pre_model_hypothesis_not_target_k"
            )
        for level in ("coarse", "fine"):
            item = estimate.get(level)
            if not isinstance(item, dict):
                errors.append(f"topic_count_estimate.{level} must be an object")
                continue
            lower = _count(
                item.get("lower_bound"),
                f"topic_count_estimate.{level}.lower_bound",
                errors,
            )
            point = _count(
                item.get("point_estimate"),
                f"topic_count_estimate.{level}.point_estimate",
                errors,
            )
            upper = _count(
                item.get("upper_bound"),
                f"topic_count_estimate.{level}.upper_bound",
                errors,
            )
            if (
                None not in (lower, point, upper)
                and not lower <= point <= upper
            ):
                errors.append(
                    f"topic_count_estimate.{level} must satisfy "
                    "lower_bound <= point_estimate <= upper_bound"
                )
            ids = item.get("candidate_theme_ids")
            if not isinstance(ids, list) or not ids:
                errors.append(
                    f"topic_count_estimate.{level}.candidate_theme_ids "
                    "must be a non-empty list"
                )
            else:
                rendered_ids = [str(value) for value in ids]
                estimated_candidate_ids.update(rendered_ids)
                if len(rendered_ids) != len(set(rendered_ids)):
                    errors.append(
                        f"topic_count_estimate.{level}.candidate_theme_ids "
                        "must be unique"
                    )
                unknown = sorted(set(rendered_ids).difference(candidate_ids))
                if unknown:
                    errors.append(
                        f"topic_count_estimate.{level} references unknown "
                        f"candidate IDs: {unknown}"
                    )
                wrong_level = sorted(
                    candidate_id
                    for candidate_id in rendered_ids
                    if candidate_levels.get(candidate_id) != level
                )
                if wrong_level:
                    errors.append(
                        f"topic_count_estimate.{level} references candidates "
                        f"from another hierarchy level: {wrong_level}"
                    )
                if point is not None and point != len(set(rendered_ids)):
                    errors.append(
                        f"topic_count_estimate.{level}.point_estimate must equal "
                        "the number of listed candidate_theme_ids"
                    )
            if not str(item.get("basis", "")).strip():
                errors.append(
                    f"topic_count_estimate.{level}.basis must not be blank"
                )

    excluded_artifacts = reconnaissance.get("excluded_artifact_candidate_ids")
    if not isinstance(excluded_artifacts, list):
        errors.append("excluded_artifact_candidate_ids must be a list")
    else:
        rendered_artifacts = [str(value) for value in excluded_artifacts]
        artifact_candidate_ids = {
            candidate_id
            for candidate_id, relation in candidate_relations.items()
            if relation == "artifact"
        }
        unknown_artifacts = sorted(set(rendered_artifacts).difference(candidate_ids))
        if unknown_artifacts:
            errors.append(
                "excluded_artifact_candidate_ids contains unknown candidate IDs: "
                f"{unknown_artifacts}"
            )
        non_artifacts = sorted(
            candidate_id
            for candidate_id in rendered_artifacts
            if candidate_relations.get(candidate_id) != "artifact"
        )
        if non_artifacts:
            errors.append(
                "excluded_artifact_candidate_ids contains non-artifact themes: "
                f"{non_artifacts}"
            )
        if set(rendered_artifacts) != artifact_candidate_ids:
            errors.append(
                "excluded_artifact_candidate_ids must list every artifact candidate "
                "and no substantive candidate"
            )
        estimated_artifacts = sorted(
            estimated_candidate_ids.intersection(artifact_candidate_ids)
        )
        if estimated_artifacts:
            errors.append(
                "artifact candidates cannot remain in topic-count estimates: "
                f"{estimated_artifacts}"
            )

    if gate_status not in GATE_STATES:
        errors.append("modeling-authorization.json has an invalid gate_status")
    may_start = authorization.get("modeling_may_start")
    if not isinstance(may_start, bool):
        errors.append("modeling_may_start must be a boolean")
    elif may_start != (gate_status == "approved_for_modeling"):
        errors.append(
            "modeling_may_start must be true only for approved_for_modeling"
        )
    if (
        authorization.get("user_theme_mode")
        != "coverage_and_interpretation_anchor"
    ):
        errors.append(
            "modeling-authorization.json user_theme_mode must be "
            "coverage_and_interpretation_anchor"
        )
    if authorization.get("allow_emergent_themes") is not True:
        errors.append(
            "modeling-authorization.json allow_emergent_themes must be true"
        )
    risk_acknowledged = authorization.get(
        "progressive_reading_risk_acknowledged"
    )
    if not isinstance(risk_acknowledged, bool):
        errors.append(
            "progressive_reading_risk_acknowledged must be a boolean"
        )
    elif reading_mode == "direct_full_text" and risk_acknowledged is not False:
        errors.append(
            "direct_full_text authorization requires "
            "progressive_reading_risk_acknowledged=false"
        )

    recorded_pre_model_fingerprint = authorization.get(
        "pre_model_artifact_fingerprint"
    )
    if not isinstance(recorded_pre_model_fingerprint, str):
        errors.append("pre_model_artifact_fingerprint must be a string")
        recorded_pre_model_fingerprint = ""
    recorded_pre_model_fingerprint = recorded_pre_model_fingerprint.strip()
    if gate_status == "approved_for_modeling" and not recorded_pre_model_fingerprint:
        errors.append(
            "approved modeling requires a pre-model artifact fingerprint"
        )
    if recorded_pre_model_fingerprint:
        try:
            current_pre_model_fingerprint = compute_pre_model_artifact_fingerprint(root)
        except OSError as exc:
            errors.append(f"Cannot fingerprint pre-model artifacts: {exc}")
        else:
            if recorded_pre_model_fingerprint != current_pre_model_fingerprint:
                errors.append(
                    "pre-model artifact fingerprint does not match the authorized "
                    "reading plan, ledger, profile, reconnaissance, and candidate map"
                )

    if gate_status == "approved_for_modeling":
        if not authorization_id:
            errors.append("approved modeling requires authorization_id")
        if not str(authorization.get("user_instruction", "")).strip():
            errors.append("approved modeling requires user_instruction")
        if not str(authorization.get("decision_recorded_at", "")).strip():
            errors.append("approved modeling requires decision_recorded_at")
        if (
            reading_mode == "progressive_extraction"
            and risk_acknowledged is not True
        ):
            errors.append(
                "approved progressive_extraction requires "
                "progressive_reading_risk_acknowledged=true"
            )
        resolved = authorization.get("resolved_candidate_theme_ids")
        if (
            not isinstance(resolved, list)
            or len(resolved) != len(set(map(str, resolved)))
            or set(map(str, resolved)) != set(candidate_ids)
        ):
            errors.append(
                "resolved_candidate_theme_ids must match every candidate theme exactly"
            )
        for index, row in enumerate(candidates, start=2):
            disposition = str(row.get("user_disposition", "")).strip()
            if disposition not in DISPOSITIONS:
                errors.append(
                    f"theme-candidate-audit.csv row {index} requires a valid "
                    "user_disposition"
                )
            if not str(row.get("user_instruction", "")).strip():
                errors.append(
                    f"theme-candidate-audit.csv row {index} requires "
                    "user_instruction"
                )

    if require_approval and gate_status != "approved_for_modeling":
        errors.append("gate_status must be approved_for_modeling before modeling")

    result["valid"] = not errors
    return result


def validate_reconnaissance_for_level(
    root: Path,
    assurance_level: str,
    *,
    progressive_coverage_claim: bool,
) -> dict[str, Any]:
    """Apply reconnaissance obligations that match the intended claim.

    Exploratory work may start from a compact profile and direct inspection.
    Research needs a concise theme map; its full reading ledger is validated
    only when the claim relies on progressive coverage. Publication retains
    the existing complete preview and explicit approval gate.
    """

    root = Path(root)
    if assurance_level == "exploratory":
        errors: list[str] = []
        warnings: list[str] = []
        path = root / "theme-reconnaissance.json"
        if path.is_file():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8-sig"))
                if not isinstance(loaded, dict):
                    errors.append(
                        "theme-reconnaissance.json must contain a JSON object"
                    )
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"Cannot read theme-reconnaissance.json: {exc}")
        else:
            warnings.append(
                "Exploratory assurance does not require "
                "theme-reconnaissance.json before a requested baseline"
            )
        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "assurance_level": assurance_level,
            "approval_required": False,
        }

    if assurance_level == "research":
        errors = []
        warnings = []
        loaded: dict[str, Any] | None = None
        path = root / "theme-reconnaissance.json"
        if not path.is_file():
            errors.append(
                "Research assurance requires concise theme-reconnaissance.json"
            )
        else:
            try:
                loaded = json.loads(path.read_text(encoding="utf-8-sig"))
            except (OSError, json.JSONDecodeError) as exc:
                loaded = None
                errors.append(f"Cannot read theme-reconnaissance.json: {exc}")
            if loaded is not None and not isinstance(loaded, dict):
                errors.append(
                    "theme-reconnaissance.json must contain a JSON object"
                )
            elif isinstance(loaded, dict):
                for field in ("research_question", "review_scope"):
                    if not str(loaded.get(field, "")).strip():
                        errors.append(
                            f"Research theme-reconnaissance.json requires {field}"
                        )
                if loaded.get("review_scope") != "concise_research_theme_map":
                    errors.append(
                        "Research theme-reconnaissance.json review_scope must be "
                        "'concise_research_theme_map'"
                    )
                if loaded.get("route") not in {
                    "network-short",
                    "long-document",
                    "mixed",
                }:
                    errors.append(
                        "Research theme-reconnaissance.json route must be "
                        "network-short, long-document, or mixed"
                    )
                themes = loaded.get("candidate_themes")
                if not isinstance(themes, list) or not themes:
                    errors.append(
                        "Research theme-reconnaissance.json candidate_themes "
                        "must be a non-empty list"
                    )
                else:
                    seen_ids: set[str] = set()
                    for index, theme in enumerate(themes):
                        if not isinstance(theme, dict):
                            errors.append(
                                "Research candidate_themes entries must be objects"
                            )
                            continue
                        candidate_id = str(
                            theme.get("candidate_id", "")
                        ).strip()
                        if not candidate_id:
                            errors.append(
                                f"candidate_themes[{index}] requires candidate_id"
                            )
                        elif candidate_id in seen_ids:
                            errors.append(
                                f"Duplicate research candidate theme: {candidate_id}"
                            )
                        seen_ids.add(candidate_id)
                        if not str(theme.get("definition", "")).strip():
                            errors.append(
                                f"candidate_themes[{index}] requires definition"
                            )
                        _nonempty_string_list(
                            theme.get("evidence_unit_ids"),
                            f"candidate_themes[{index}].evidence_unit_ids",
                            errors,
                        )
                _nonempty_string_list(
                    loaded.get("limitations"),
                    "theme-reconnaissance.json limitations",
                    errors,
                )

        if progressive_coverage_claim:
            plan_path = root / "corpus-reading-plan.json"
            ledger_path = root / "corpus-reading-ledger.csv"
            if not plan_path.is_file():
                errors.append(
                    "Research progressive coverage requires "
                    "corpus-reading-plan.json"
                )
            if not ledger_path.is_file():
                errors.append(
                    "Research progressive coverage requires "
                    "corpus-reading-ledger.csv"
                )

            reading_plan = (
                _read_json(plan_path, errors) if plan_path.is_file() else None
            )
            if reading_plan is not None and not isinstance(reading_plan, dict):
                errors.append("corpus-reading-plan.json must contain a JSON object")
                reading_plan = None

            reading_plan_id = ""
            route = str((loaded or {}).get("route", "")).strip()
            if isinstance(reading_plan, dict):
                reading_plan_id = str(
                    reading_plan.get("reading_plan_id", "")
                ).strip()
                if not reading_plan_id:
                    errors.append(
                        "Research corpus-reading-plan.json requires reading_plan_id"
                    )
                if reading_plan.get("mode") != "progressive_extraction":
                    errors.append(
                        "Research progressive coverage requires reading plan "
                        "mode 'progressive_extraction'"
                    )
                if not str(
                    reading_plan.get("corpus_fingerprint", "")
                ).strip():
                    errors.append(
                        "Research corpus-reading-plan.json requires "
                        "corpus_fingerprint"
                    )
                plan_route = str(reading_plan.get("route", route)).strip()
                if plan_route and route and plan_route != route:
                    errors.append(
                        "Research reading plan route disagrees with "
                        "theme-reconnaissance.json"
                    )
                selection = reading_plan.get("selection")
                channels = (
                    selection.get("selection_channels")
                    if isinstance(selection, dict)
                    else None
                )
                registered_channels = set(
                    _nonempty_string_list(
                        channels,
                        "corpus-reading-plan.json "
                        "selection.selection_channels",
                        errors,
                    )
                )
                missing_channels = sorted(
                    PROGRESSIVE_SELECTION_CHANNELS.difference(
                        registered_channels
                    )
                )
                if missing_channels:
                    errors.append(
                        "Research progressive reading plan is missing selection "
                        "channel(s): "
                        + ", ".join(missing_channels)
                    )
                stopping = reading_plan.get("stopping")
                if not isinstance(stopping, dict):
                    errors.append(
                        "Research corpus-reading-plan.json stopping must be an object"
                    )
                else:
                    for field in ("estimand", "rule", "status"):
                        if not str(stopping.get(field, "")).strip():
                            errors.append(
                                "Research corpus-reading-plan.json "
                                f"stopping.{field} must not be blank"
                            )
                if not str(reading_plan.get("residual_risk", "")).strip():
                    errors.append(
                        "Research corpus-reading-plan.json residual_risk "
                        "must not be blank"
                    )

            if ledger_path.is_file():
                header, rows = _read_candidates(ledger_path, errors)
                for field in sorted(LEDGER_FIELDS.difference(header)):
                    errors.append(
                        "corpus-reading-ledger.csv lacks required column: "
                        f"{field}"
                    )
                if not rows:
                    errors.append(
                        "Research corpus-reading-ledger.csv must contain "
                        "at least one row"
                    )
                seen_units: set[str] = set()
                reviewed_units: set[str] = set()
                observed_channels: set[str] = set()
                observed_subsets: set[str] = set()
                for index, row in enumerate(rows, start=2):
                    prefix = f"corpus-reading-ledger.csv row {index}"
                    unit_id = str(row.get("unit_id", "")).strip()
                    if not unit_id:
                        errors.append(f"{prefix} lacks unit_id")
                    elif unit_id in seen_units:
                        errors.append(f"Duplicate ledger unit_id: {unit_id}")
                    seen_units.add(unit_id)
                    if (
                        reading_plan_id
                        and str(row.get("reading_plan_id", "")).strip()
                        != reading_plan_id
                    ):
                        errors.append(f"{prefix} reading_plan_id does not match")
                    subset = str(row.get("route_subset", "")).strip()
                    if subset not in {"network-short", "long-document"}:
                        errors.append(
                            f"{prefix} route_subset must be network-short "
                            "or long-document"
                        )
                    else:
                        observed_subsets.add(subset)
                    if (
                        subset == "long-document"
                        and not str(row.get("parent_document_id", "")).strip()
                    ):
                        errors.append(
                            f"{prefix} long-document evidence requires "
                            "parent_document_id"
                        )
                    review_depth = str(row.get("review_depth", "")).strip()
                    if review_depth not in REVIEW_DEPTHS:
                        errors.append(f"{prefix} has invalid review_depth")
                    if unit_id and review_depth in SEMANTIC_REVIEW_DEPTHS:
                        reviewed_units.add(unit_id)
                    observed_channels.update(
                        item.strip()
                        for item in str(
                            row.get("selection_channels", "")
                        ).split("|")
                        if item.strip()
                    )

                missing_observed_channels = sorted(
                    PROGRESSIVE_SELECTION_CHANNELS.difference(observed_channels)
                )
                if missing_observed_channels:
                    errors.append(
                        "Research progressive ledger is missing selection "
                        "channel evidence: "
                        + ", ".join(missing_observed_channels)
                    )
                if route == "mixed" and not {
                    "network-short",
                    "long-document",
                }.issubset(observed_subsets):
                    errors.append(
                        "Research mixed-route ledger requires both route subsets"
                    )
                if route in {"network-short", "long-document"} and any(
                    subset != route for subset in observed_subsets
                ):
                    errors.append(
                        "Research ledger route_subset disagrees with "
                        "theme-reconnaissance.json"
                    )

                required_evidence_ids = {
                    str(unit_id).strip()
                    for theme in (loaded or {}).get("candidate_themes", [])
                    if isinstance(theme, dict)
                    for unit_id in theme.get("evidence_unit_ids", [])
                    if str(unit_id).strip()
                }
                for unit_id in sorted(
                    required_evidence_ids.difference(reviewed_units)
                ):
                    errors.append(
                        "Research candidate theme evidence lacks full-text or "
                        f"extracted-representation review in the ledger: {unit_id}"
                    )
        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "assurance_level": assurance_level,
            "approval_required": False,
        }

    if assurance_level == "publication_release":
        result = validate_theme_reconnaissance(root, require_approval=True)
        result = dict(result)
        result["assurance_level"] = assurance_level
        result["approval_required"] = True
        return result

    return {
        "valid": False,
        "errors": [
            "assurance_level must be exploratory, research, or publication_release"
        ],
        "warnings": [],
        "assurance_level": assurance_level,
        "approval_required": True,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate corpus reconnaissance and scalable reading evidence"
    )
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--require-approval", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = validate_theme_reconnaissance(
        args.bundle,
        require_approval=args.require_approval,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote reconnaissance audit: {args.output}")
    else:
        print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
