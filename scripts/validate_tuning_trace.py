#!/usr/bin/env python3
"""Validate cumulative, one-parameter-family BERTopic tuning traces."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


MAIN_STAGE_ORDER: tuple[str, ...] = (
    "analysis_unit",
    "embedding",
    "umap",
    "hdbscan_min_cluster_size",
    "hdbscan_min_samples",
    "hdbscan_selection_method",
    "representation",
    "taxonomy",
)

ASSURANCE_LEVELS = {"exploratory", "research", "publication_release"}
DECISIONS = {"promote", "retain", "defer"}
HDBSCAN_KEY_TO_FAMILY = {
    "min_cluster_size": "hdbscan_min_cluster_size",
    "min_samples": "hdbscan_min_samples",
    "cluster_selection_method": "hdbscan_selection_method",
}
INTERACTION_PROHIBITIONS = (
    "cartesian",
    "full grid",
    "exhaustive grid",
    "unrestricted grid",
    "all combinations",
    "笛卡尔",
    "全网格",
)


def _nonblank(value: Any) -> bool:
    return value is not None and bool(str(value).strip())


def _parse_jsonish(value: Any) -> Any:
    if isinstance(value, (dict, list, int, float, bool)) or value is None:
        return value
    text = str(value).strip()
    if not text:
        return ""
    if text[0] in "[{\"" or text in {"true", "false", "null"}:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text


def _changed(left: Any, right: Any) -> bool:
    return _parse_jsonish(left) != _parse_jsonish(right)


def _hdbscan_changes(parent: dict[str, Any], child: dict[str, Any]) -> set[str]:
    before = _parse_jsonish(parent.get("hdbscan_config", ""))
    after = _parse_jsonish(child.get("hdbscan_config", ""))
    if before == after:
        return set()
    if not isinstance(before, dict) or not isinstance(after, dict):
        return {"hdbscan_unknown"}
    keys = set(before).union(after)
    families: set[str] = set()
    for key in keys:
        if before.get(key) != after.get(key):
            families.add(HDBSCAN_KEY_TO_FAMILY.get(key, "hdbscan_other"))
    return families


def scientific_change_families(
    parent: dict[str, Any],
    child: dict[str, Any],
) -> set[str]:
    """Return scientific parameter families changed from parent to child."""

    families: set[str] = set()
    if any(
        _changed(parent.get(field, ""), child.get(field, ""))
        for field in (
            "analysis_unit",
            "segmentation_config",
            "chunking_config",
            "corpus_fingerprint",
        )
    ):
        families.add("analysis_unit")
    if any(
        _changed(parent.get(field, ""), child.get(field, ""))
        for field in (
            "embedding_model",
            "embedding_revision",
            "embedding_instruction",
            "embedding_pooling",
            "embedding_truncation",
        )
    ):
        families.add("embedding")
    if _changed(parent.get("umap_config", ""), child.get("umap_config", "")):
        families.add("umap")
    families.update(_hdbscan_changes(parent, child))
    if any(
        _changed(parent.get(field, ""), child.get(field, ""))
        for field in (
            "representation_config",
            "representation_snapshot_id",
            "lexicon_bundle_id",
            "vectorizer_config",
            "ctfidf_config",
        )
    ):
        families.add("representation")
    if any(
        _changed(parent.get(field, ""), child.get(field, ""))
        for field in (
            "taxonomy_config",
            "taxonomy_snapshot_id",
            "taxonomy_mapping",
        )
    ):
        families.add("taxonomy")
    return families


def _truthy_unresolved(value: Any) -> bool:
    if value in (None, "", 0, 0.0, False):
        return False
    return str(value).strip().casefold() not in {"0", "false", "none", "no"}


def validate_tuning_trace(
    trace: dict[str, Any],
    registry_rows: list[dict[str, str]],
    *,
    assurance_level: str,
) -> dict[str, Any]:
    """Validate stage order, parentage, promotion, rollback, and interactions."""

    errors: list[str] = []
    warnings: list[str] = []
    if assurance_level not in ASSURANCE_LEVELS:
        errors.append(
            "assurance_level must be exploratory, research, or publication_release"
        )
    if not isinstance(trace, dict):
        return {
            "valid": False,
            "errors": ["tuning trace must be a JSON object"],
            "warnings": [],
            "current_champion_id": "",
            "completed_stages": [],
        }

    registry: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(registry_rows, start=2):
        candidate_id = str(row.get("candidate_id", "")).strip()
        if not candidate_id:
            errors.append(f"experiment registry row {index} lacks candidate_id")
            continue
        if candidate_id in registry:
            errors.append(f"Duplicate registry candidate_id: {candidate_id}")
            continue
        registry[candidate_id] = dict(row)

    baseline = str(trace.get("baseline_candidate_id", "")).strip()
    if not baseline:
        errors.append("baseline_candidate_id must not be blank")
    elif baseline not in registry:
        errors.append(f"Baseline candidate is absent from registry: {baseline}")
    current = baseline

    stages = trace.get("stages")
    if not isinstance(stages, list):
        stages = []
        errors.append("stages must be a list")

    seen_stages: set[str] = set()
    last_stage_position = -1
    completed_stages: list[str] = []
    for index, stage in enumerate(stages):
        if not isinstance(stage, dict):
            errors.append(f"stages[{index}] must be an object")
            continue
        stage_id = str(stage.get("stage_id", "")).strip()
        if stage_id not in MAIN_STAGE_ORDER:
            errors.append(f"Unknown main stage: {stage_id or '<blank>'}")
            continue
        position = MAIN_STAGE_ORDER.index(stage_id)
        if stage_id in seen_stages:
            errors.append(f"Duplicate main stage: {stage_id}")
        if position <= last_stage_position:
            errors.append(f"Main stage is out of order: {stage_id}")
        seen_stages.add(stage_id)
        last_stage_position = max(last_stage_position, position)

        champion_before = str(stage.get("champion_before", "")).strip()
        if champion_before != current:
            errors.append(
                f"Stage {stage_id} champion_before must equal current champion "
                f"{current!r}, not {champion_before!r}"
            )
        family = str(stage.get("changed_parameter_family", "")).strip()
        if family != stage_id:
            errors.append(
                f"Stage {stage_id} changed_parameter_family must be {stage_id!r}"
            )

        status = str(stage.get("status", "")).strip()
        decision = str(stage.get("decision", "")).strip()
        candidate_ids = stage.get("candidate_ids")
        if not isinstance(candidate_ids, list):
            errors.append(f"Stage {stage_id} candidate_ids must be a list")
            candidate_ids = []
        candidate_ids = [
            str(candidate_id).strip()
            for candidate_id in candidate_ids
            if _nonblank(candidate_id)
        ]

        if status == "skipped":
            if candidate_ids:
                errors.append(f"Skipped stage {stage_id} cannot list candidates")
            if not _nonblank(stage.get("skip_reason")):
                errors.append(f"Skipped stage {stage_id} requires skip_reason")
            if decision != "retain":
                errors.append(f"Skipped stage {stage_id} decision must be retain")
        elif status == "completed":
            completed_stages.append(stage_id)
            if not candidate_ids:
                errors.append(f"Completed stage {stage_id} requires candidates")
            if decision not in DECISIONS:
                errors.append(
                    f"Stage {stage_id} decision must be promote, retain, or defer"
                )
        elif status in {"pending", ""}:
            message = f"Stage {stage_id} is pending and not completed"
            if assurance_level in {"research", "publication_release"}:
                errors.append(message)
            else:
                warnings.append(message)
        else:
            errors.append(f"Stage {stage_id} has unknown status {status!r}")

        parent_row = registry.get(current, {})
        promoted_by_registry: list[str] = []
        for candidate_id in candidate_ids:
            candidate = registry.get(candidate_id)
            if candidate is None:
                errors.append(
                    f"Stage {stage_id} candidate is absent from registry: "
                    f"{candidate_id}"
                )
                continue
            parent_id = str(candidate.get("champion_parent_id", "")).strip()
            if parent_id != current:
                errors.append(
                    f"Candidate {candidate_id} champion parent must be current "
                    f"champion {current!r}, not {parent_id!r}"
                )
            candidate_family = str(
                candidate.get("changed_parameter_family", "")
            ).strip()
            if candidate_family != stage_id:
                errors.append(
                    f"Candidate {candidate_id} changed_parameter_family must be "
                    f"{stage_id!r}"
                )
            change_families = scientific_change_families(parent_row, candidate)
            if not change_families:
                errors.append(
                    f"Candidate {candidate_id} does not change the registered "
                    f"{stage_id} family"
                )
            extra = change_families.difference({stage_id})
            if extra:
                errors.append(
                    f"Candidate {candidate_id} changes more than one parameter "
                    f"family at main stage {stage_id}: "
                    + ", ".join(sorted(change_families))
                )
            if stage_id not in change_families and change_families:
                errors.append(
                    f"Candidate {candidate_id} does not change the stage family "
                    f"{stage_id}; observed {sorted(change_families)}"
                )
            if stage_id == "representation":
                before = str(parent_row.get("assignment_fingerprint", "")).strip()
                after = str(candidate.get("assignment_fingerprint", "")).strip()
                if not before or after != before:
                    errors.append(
                        f"Representation candidate {candidate_id} assignment "
                        "fingerprint must match its champion parent"
                    )
            if str(candidate.get("comparison_to_champion", "")).strip() == "promote":
                promoted_by_registry.append(candidate_id)

        if len(promoted_by_registry) > 1:
            errors.append(
                f"Stage {stage_id} has multiple registry candidates marked promote"
            )

        promoted = str(stage.get("promoted_candidate_id", "")).strip()
        champion_after = str(stage.get("champion_after", "")).strip()
        if decision == "promote":
            if promoted not in candidate_ids:
                errors.append(
                    f"Stage {stage_id} promoted_candidate_id must be one of its "
                    "candidate_ids"
                )
            if champion_after != promoted:
                errors.append(
                    f"Stage {stage_id} champion_after must equal its promoted candidate"
                )
            candidate = registry.get(promoted, {})
            if assurance_level in {"research", "publication_release"}:
                if (
                    str(candidate.get("semantic_review_status", "")).strip()
                    != "pass"
                ):
                    errors.append(
                        f"Promoted candidate {promoted} requires a passed semantic review"
                    )
                if not _nonblank(stage.get("semantic_review_artifact")):
                    errors.append(
                        f"Promoted stage {stage_id} requires semantic_review_artifact"
                    )
            if (
                str(candidate.get("meaning_distinctiveness", "")).strip()
                == "worse"
            ):
                errors.append(
                    f"Candidate {promoted} cannot be promoted with worse meaning "
                    "distinctiveness"
                )
            if _truthy_unresolved(
                candidate.get("unresolved_semantic_decisions")
            ):
                errors.append(
                    f"Candidate {promoted} has unresolved semantic decisions"
                )
            current = promoted or current
        elif decision in {"retain", "defer"} or status == "skipped":
            if promoted:
                errors.append(
                    f"Stage {stage_id} cannot name a promoted candidate when "
                    f"decision is {decision!r}"
                )
            if champion_after != current:
                errors.append(
                    f"Stage {stage_id} must retain current champion {current!r}; "
                    f"rejected or deferred candidates cannot become champion_after"
                )
        elif status == "completed":
            errors.append(f"Stage {stage_id} lacks a valid decision")

    if assurance_level in {"research", "publication_release"}:
        for missing_stage in MAIN_STAGE_ORDER:
            if missing_stage not in seen_stages:
                errors.append(f"Missing main stage record: {missing_stage}")

    interaction = trace.get("interaction_confirmation", {})
    if not isinstance(interaction, dict):
        errors.append("interaction_confirmation must be an object")
        interaction = {}
    if interaction.get("required") is True:
        triggers = interaction.get("diagnostic_triggers")
        if not isinstance(triggers, list) or not triggers or not all(
            _nonblank(value) for value in triggers
        ):
            errors.append(
                "Interaction confirmation requires at least one nonblank "
                "diagnostic trigger"
            )
        families = interaction.get("allowed_parameter_families")
        if not isinstance(families, list) or not families or not all(
            _nonblank(value) for value in families
        ):
            errors.append(
                "Interaction confirmation requires named allowed parameter families"
            )
        rule = str(interaction.get("candidate_generation_rule", "")).strip()
        if not rule:
            errors.append(
                "Interaction confirmation requires a bounded candidate_generation_rule"
            )
        folded = rule.casefold()
        if any(term.casefold() in folded for term in INTERACTION_PROHIBITIONS):
            errors.append(
                "Interaction confirmation cannot use an unrestricted Cartesian grid"
            )
        candidates = interaction.get("candidate_ids")
        if not isinstance(candidates, list) or not candidates:
            errors.append("Required interaction confirmation needs candidate_ids")
            candidates = []
        else:
            candidates = [
                str(candidate_id).strip()
                for candidate_id in candidates
                if _nonblank(candidate_id)
            ]
        allowed_families = {
            str(family).strip()
            for family in (families or [])
            if _nonblank(family)
        }
        parent_row = registry.get(current, {})
        for candidate_id in candidates:
            candidate = registry.get(candidate_id)
            if candidate is None:
                errors.append(
                    f"Interaction candidate is absent from registry: {candidate_id}"
                )
                continue
            parent_id = str(candidate.get("champion_parent_id", "")).strip()
            if parent_id != current:
                errors.append(
                    f"Interaction candidate {candidate_id} champion parent must "
                    f"be current champion {current!r}"
                )
            changed = scientific_change_families(parent_row, candidate)
            if not changed:
                errors.append(
                    f"Interaction candidate {candidate_id} has no registered "
                    "scientific change"
                )
            disallowed = changed.difference(allowed_families)
            if disallowed:
                errors.append(
                    f"Interaction candidate {candidate_id} changes families "
                    "outside allowed_parameter_families: "
                    + ", ".join(sorted(disallowed))
                )
        interaction_decision = str(interaction.get("decision", "")).strip()
        if interaction_decision not in DECISIONS:
            errors.append(
                "Interaction confirmation decision must be promote, retain, or defer"
            )
        promoted = str(interaction.get("promoted_candidate_id", "")).strip()
        if interaction_decision == "promote":
            if promoted not in (candidates or []):
                errors.append(
                    "Interaction promoted_candidate_id must be one of candidate_ids"
                )
            if assurance_level in {"research", "publication_release"} and not _nonblank(
                interaction.get("semantic_review_artifact")
            ):
                errors.append(
                    "Promoted interaction candidate requires semantic_review_artifact"
                )
            promoted_row = registry.get(promoted, {})
            if (
                assurance_level in {"research", "publication_release"}
                and str(
                    promoted_row.get("semantic_review_status", "")
                ).strip()
                != "pass"
            ):
                errors.append(
                    "Promoted interaction candidate requires a passed semantic review"
                )
            if promoted:
                current = promoted
        elif promoted:
            errors.append(
                "Interaction cannot name promoted_candidate_id when retaining/defering"
            )
    else:
        if interaction.get("candidate_ids"):
            errors.append(
                "Non-required interaction confirmation cannot contain candidates"
            )

    declared_current = str(trace.get("current_champion_id", "")).strip()
    if declared_current != current:
        errors.append(
            f"current_champion_id must equal final champion {current!r}, "
            f"not {declared_current!r}"
        )
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "current_champion_id": current,
        "completed_stages": completed_stages,
    }


def _read_registry(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a cumulative BERTopic tuning champion trace"
    )
    parser.add_argument("trace", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument(
        "--assurance-level",
        choices=sorted(ASSURANCE_LEVELS),
        help="Override the assurance level stored in the trace",
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    trace = json.loads(args.trace.read_text(encoding="utf-8-sig"))
    assurance_level = args.assurance_level or str(
        trace.get("assurance_level", "")
    ).strip()
    result = validate_tuning_trace(
        trace,
        _read_registry(args.registry),
        assurance_level=assurance_level,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote tuning trace audit: {args.output}")
    else:
        print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
