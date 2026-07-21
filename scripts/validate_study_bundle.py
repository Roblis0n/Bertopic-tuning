#!/usr/bin/env python3
"""Validate the minimum reproducibility bundle for an academic BERTopic study."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "study-contract.json",
    "corpus-profile.json",
    "experiment-registry.csv",
    "candidate-metrics.csv",
    "selected-model.json",
    "topic-catalog.csv",
    "topic-lineage.csv",
    "human-topic-audit.csv",
    "topic-pair-audit.csv",
    "missing-theme-audit.csv",
    "evidence-log.csv",
    "decision-report.md",
}

CORPUS_PROFILE_FIELDS = {
    "corpus_fingerprint",
    "unit_count",
    "length_profile",
    "group_fields",
}

CONTRACT_FIELDS = {
    "study_id",
    "route",
    "research_question",
    "analysis_unit",
    "diversity_definition",
    "minimum_meaningful_theme",
    "calibration_plan",
    "validation_groups",
    "embedding_context_policy",
    "selection_policy",
    "outlier_role",
    "paper_transfer_policy",
}

TABLE_FIELDS = {
    "experiment-registry.csv": {
        "candidate_id",
        "run_type",
        "parent_snapshot_id",
        "corpus_fingerprint",
        "analysis_unit",
        "embedding_model",
        "umap_config",
        "hdbscan_config",
        "representation_config",
        "status",
    },
    "candidate-metrics.csv": {
        "candidate_id",
        "topic_count",
        "td",
        "irbo",
        "semantic_diversity",
        "coverage",
        "stability",
        "coherence",
        "human_labelability",
        "outlier_fraction",
    },
    "topic-catalog.csv": {
        "snapshot_id",
        "topic_uid",
        "local_topic_id",
        "label",
        "definition",
        "inclusion",
        "exclusion",
        "size",
        "representative_units",
        "nearest_topic_uid",
        "nearest_similarity",
        "status",
    },
    "topic-lineage.csv": {
        "old_snapshot_id",
        "old_topic_uid",
        "new_snapshot_id",
        "new_topic_uid",
        "event_type",
        "evidence",
        "human_decision",
    },
    "human-topic-audit.csv": {
        "snapshot_id",
        "topic_uid",
        "sample_type",
        "unit_id",
        "relevance",
        "coherence",
        "distinctiveness",
        "label_fit",
        "notes",
        "reviewer",
    },
    "topic-pair-audit.csv": {
        "snapshot_id",
        "topic_uid_a",
        "topic_uid_b",
        "lexical_overlap",
        "semantic_similarity",
        "definition_distinction",
        "merge_decision",
        "evidence",
        "reviewer",
    },
    "missing-theme-audit.csv": {
        "snapshot_id",
        "sample_group",
        "unit_id",
        "reference_theme",
        "matched_topic_uid",
        "coverage_status",
        "evidence",
        "reviewer",
    },
    "evidence-log.csv": {
        "citation",
        "claim_used",
        "evidence_type",
        "scope_limit",
        "accessed_on",
    },
}

NONEMPTY_TABLES = {
    "experiment-registry.csv",
    "candidate-metrics.csv",
    "topic-catalog.csv",
    "human-topic-audit.csv",
    "topic-pair-audit.csv",
    "missing-theme-audit.csv",
    "evidence-log.csv",
}


def _read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Cannot read valid JSON from {path.name}: {exc}")
        return None


def _read_table(path: Path, errors: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader.fieldnames or []), list(reader)
    except (OSError, csv.Error) as exc:
        errors.append(f"Cannot read CSV {path.name}: {exc}")
        return [], []


def validate_parameter_governance(contract: dict[str, Any]) -> list[str]:
    """Validate that a completed study derived numbers locally instead of copying them."""
    errors: list[str] = []
    if contract.get("paper_transfer_policy") != "mechanisms-and-local-tests-not-parameters":
        errors.append(
            "paper_transfer_policy must be 'mechanisms-and-local-tests-not-parameters'"
        )

    plan = contract.get("calibration_plan")
    if not isinstance(plan, dict):
        errors.append(
            "calibration_plan must be a structured object with local candidate-generation and stop rules"
        )
        return errors

    if plan.get("unjustified_value_token") != "pending_local_calibration":
        errors.append(
            "calibration_plan.unjustified_value_token must be 'pending_local_calibration'"
        )
    if plan.get("candidate_generation_policy") != "adaptive-local-evidence":
        errors.append(
            "calibration_plan.candidate_generation_policy must be 'adaptive-local-evidence'"
        )
    if plan.get("stop_rule_required") is not True:
        errors.append("calibration_plan.stop_rule_required must be true")

    records = plan.get("thresholds")
    if not isinstance(records, list) or not records:
        errors.append(
            "calibration_plan.thresholds must contain completed local calibration records"
        )
        return errors

    required_record_fields = {
        "name",
        "status",
        "evidence_basis",
        "candidate_generation_rule",
        "stop_rule",
        "artifact",
    }
    allowed_statuses = {"calibrated", "sensitivity_frontier"}
    for index, record in enumerate(records):
        prefix = f"calibration_plan.thresholds[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = sorted(required_record_fields.difference(record))
        errors.extend(f"{prefix} lacks required field: {field}" for field in missing)
        for field in sorted(required_record_fields.difference({"status"})):
            if field in record and not str(record.get(field, "")).strip():
                errors.append(f"{prefix}.{field} must not be blank")
        status = record.get("status")
        if status == "pending_local_calibration":
            errors.append(f"{prefix} is still pending local calibration")
        elif status not in allowed_statuses:
            errors.append(
                f"{prefix}.status must be calibrated or sensitivity_frontier"
            )

    return errors


def validate_bundle(root: Path) -> dict[str, Any]:
    """Return a machine-readable audit of a study bundle."""
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    if not root.exists() or not root.is_dir():
        return {
            "valid": False,
            "errors": [f"Study bundle directory does not exist: {root}"],
            "warnings": [],
        }

    missing = sorted(name for name in REQUIRED_FILES if not (root / name).is_file())
    errors.extend(f"Missing required file: {name}" for name in missing)

    contract: dict[str, Any] | None = None
    contract_path = root / "study-contract.json"
    if contract_path.is_file():
        loaded = _read_json(contract_path, errors)
        if isinstance(loaded, dict):
            contract = loaded
            missing_fields = sorted(CONTRACT_FIELDS.difference(contract))
            errors.extend(
                f"study-contract.json lacks required field: {field}"
                for field in missing_fields
            )
            route = contract.get("route")
            if route not in {"network-short", "long-document", "mixed"}:
                errors.append(
                    "study-contract.json route must be network-short, long-document, or mixed"
                )
            axes = contract.get("diversity_definition")
            required_axes = {"lexical", "semantic", "coverage", "stability"}
            if not isinstance(axes, list) or not required_axes.issubset(set(axes)):
                errors.append(
                    "diversity_definition must include lexical, semantic, coverage, and stability"
                )
            if contract.get("selection_policy") != "pareto":
                errors.append("selection_policy must be 'pareto' to preserve explicit trade-offs")
            if contract.get("outlier_role") != "diagnostic_guardrail_only":
                errors.append(
                    "outlier_role must be 'diagnostic_guardrail_only'; it is not a primary objective"
                )
            errors.extend(validate_parameter_governance(contract))
            if not contract.get("minimum_meaningful_theme"):
                errors.append("minimum_meaningful_theme must be justified before clustering")

            if route == "long-document":
                for field in (
                    "chunking_policy",
                    "parent_document_id_field",
                    "aggregation_policy",
                ):
                    if not contract.get(field):
                        errors.append(
                            f"Long-document route requires study-contract.json field: {field}"
                        )
                groups = contract.get("validation_groups", [])
                if "document" not in groups:
                    errors.append(
                        "Long-document validation_groups must include document-level resampling"
                    )
            if route == "mixed" and not contract.get("route_subsets"):
                errors.append("Mixed route requires an explicit route_subsets mapping")
        elif loaded is not None:
            errors.append("study-contract.json must contain a JSON object")

    profile_path = root / "corpus-profile.json"
    if profile_path.is_file():
        loaded = _read_json(profile_path, errors)
        if isinstance(loaded, dict):
            missing_fields = sorted(CORPUS_PROFILE_FIELDS.difference(loaded))
            errors.extend(
                f"corpus-profile.json lacks required field: {field}"
                for field in missing_fields
            )
        elif loaded is not None:
            errors.append("corpus-profile.json must contain a JSON object")

    tables: dict[str, list[dict[str, str]]] = {}
    for name, required_fields in TABLE_FIELDS.items():
        path = root / name
        if not path.is_file():
            continue
        header, rows = _read_table(path, errors)
        tables[name] = rows
        missing_columns = sorted(required_fields.difference(header))
        errors.extend(f"{name} lacks required column: {field}" for field in missing_columns)
        if name in NONEMPTY_TABLES and not rows:
            errors.append(f"{name} must contain at least one evidence row")

    selected_model: dict[str, Any] | None = None
    selected_path = root / "selected-model.json"
    if selected_path.is_file():
        loaded = _read_json(selected_path, errors)
        if isinstance(loaded, dict):
            selected_model = loaded
            if not str(selected_model.get("candidate_id", "")).strip():
                errors.append("selected-model.json must contain candidate_id")
        elif loaded is not None:
            errors.append("selected-model.json must contain a JSON object")

    if selected_model:
        selected_id = str(selected_model.get("candidate_id"))
        registry_ids = {
            str(row.get("candidate_id", ""))
            for row in tables.get("experiment-registry.csv", [])
        }
        metric_ids = {
            str(row.get("candidate_id", ""))
            for row in tables.get("candidate-metrics.csv", [])
        }
        if registry_ids and selected_id not in registry_ids:
            errors.append(
                f"Selected candidate {selected_id} is absent from experiment-registry.csv"
            )
        if metric_ids and selected_id not in metric_ids:
            errors.append(
                f"Selected candidate {selected_id} is absent from candidate-metrics.csv"
            )

    report_path = root / "decision-report.md"
    if report_path.is_file():
        try:
            if len(report_path.read_text(encoding="utf-8").strip()) < 20:
                errors.append("decision-report.md is too short to document a decision")
        except OSError as exc:
            errors.append(f"Cannot read decision-report.md: {exc}")

    lineage_rows = tables.get("topic-lineage.csv", [])
    if not lineage_rows:
        warnings.append(
            "topic-lineage.csv has no rows; this is acceptable only for the initial snapshot"
        )

    if contract and contract.get("route") == "network-short":
        groups = contract.get("validation_groups", [])
        if not groups:
            errors.append(
                "Network-short route requires source/account/thread/time validation groups"
            )

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an academic BERTopic study bundle")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path, help="Optional JSON audit output")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = validate_bundle(args.bundle)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote bundle audit: {args.output}")
    else:
        print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
