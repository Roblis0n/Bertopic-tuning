#!/usr/bin/env python3
"""Validate full-corpus theme reconnaissance and the user modeling gate."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "corpus-profile.json",
    "theme-reconnaissance.json",
    "theme-candidate-audit.csv",
    "modeling-authorization.json",
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
    reconnaissance = _read_json(root / "theme-reconnaissance.json", errors)
    authorization = _read_json(root / "modeling-authorization.json", errors)
    header, candidates = _read_candidates(
        root / "theme-candidate-audit.csv", errors
    )
    if not all(
        isinstance(item, dict) for item in (profile, reconnaissance, authorization)
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
    authorization_id = str(authorization.get("authorization_id", "")).strip()
    gate_status = str(authorization.get("gate_status", "")).strip()
    result.update(
        reconnaissance_id=reconnaissance_id,
        authorization_id=authorization_id,
        gate_status=gate_status,
    )

    if reconnaissance.get("schema_version") != 1:
        errors.append("theme-reconnaissance.json schema_version must be 1")
    if authorization.get("schema_version") != 1:
        errors.append("modeling-authorization.json schema_version must be 1")
    if not fingerprint:
        errors.append("theme-reconnaissance.json must contain corpus_fingerprint")
    if not reconnaissance_id:
        errors.append("theme-reconnaissance.json must contain reconnaissance_id")
    if not str(reconnaissance.get("created_at", "")).strip():
        errors.append("theme-reconnaissance.json created_at must not be blank")
    if not str(reconnaissance.get("research_question", "")).strip():
        errors.append("theme-reconnaissance.json research_question must not be blank")

    for source, value in (
        ("corpus-profile.json", profile.get("corpus_fingerprint")),
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
        reviewed = _count(
            coverage.get("reviewed_unit_count"),
            "coverage.reviewed_unit_count",
            errors,
        )
        inherited = _count(
            coverage.get("duplicate_inherited_unit_count"),
            "coverage.duplicate_inherited_unit_count",
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
        if None not in (source, eligible, reviewed, inherited, excluded, failed):
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
            if eligible != reviewed + inherited + failed:
                errors.append(
                    "coverage.eligible_unit_count must equal reviewed_unit_count + "
                    "duplicate_inherited_unit_count + failed_unit_count"
                )
            if failed != 0:
                errors.append(
                    "coverage.failed_unit_count must be zero before full-corpus "
                    "coverage is claimed"
                )
            if coverage.get("coverage_complete") is not True:
                errors.append("coverage.coverage_complete must be true")
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
            reviewed_parent = _count(
                parent.get("reviewed_parent_document_count"),
                "parent_document_coverage.reviewed_parent_document_count",
                errors,
            )
            failed_parent = _count(
                parent.get("failed_parent_document_count"),
                "parent_document_coverage.failed_parent_document_count",
                errors,
            )
            if None not in (
                eligible_parent,
                reviewed_parent,
                failed_parent,
            ):
                if eligible_parent != reviewed_parent + failed_parent:
                    errors.append("parent-document counts are inconsistent")
                if (
                    failed_parent != 0
                    or parent.get("coverage_complete") is not True
                ):
                    errors.append(
                        "parent-document coverage must be complete with zero failures"
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
        ):
            if not str(row.get(field, "")).strip():
                errors.append(f"{prefix} lacks {field}")
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

    if gate_status == "approved_for_modeling":
        if not authorization_id:
            errors.append("approved modeling requires authorization_id")
        if not str(authorization.get("user_instruction", "")).strip():
            errors.append("approved modeling requires user_instruction")
        if not str(authorization.get("decision_recorded_at", "")).strip():
            errors.append("approved modeling requires decision_recorded_at")
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


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate full-corpus theme reconnaissance"
    )
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--require-approval", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
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
