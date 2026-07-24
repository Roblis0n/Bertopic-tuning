#!/usr/bin/env python3
"""Validate the minimum reproducibility bundle for an academic BERTopic study."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from lexicon_tools import compile_lexicon_bundle
from build_semantic_review_queue import validate_semantic_review
from select_pareto import select_pareto
from validate_theme_reconnaissance import (
    validate_reconnaissance_for_level,
    validate_theme_reconnaissance,
)
from validate_tuning_trace import validate_tuning_trace
from validate_visualization_bundle import validate_visualization_bundle
from workflow_policy import (
    required_artifacts,
    resolve_assurance_level,
    validate_assurance_contract,
)


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
    "corpus-reading-plan.json",
    "corpus-reading-ledger.csv",
    "theme-reconnaissance.json",
    "theme-candidate-audit.csv",
    "modeling-authorization.json",
}

LEXICON_REQUIRED_FILES = {
    "lexicon-config.json",
    "synonyms.csv",
    "stopwords.csv",
    "custom-terms.csv",
    "lexicon-manifest.json",
    "lexicon-candidate-audit.csv",
    "lexicon-lineage.csv",
    "representation-iteration.csv",
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
    "pre_model_reconnaissance",
}

TABLE_FIELDS = {
    "experiment-registry.csv": {
        "candidate_id",
        "run_type",
        "parent_snapshot_id",
        "authorization_id",
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
    "lexicon-candidate-audit.csv": {
        "candidate_id",
        "candidate_type",
        "term",
        "canonical_term",
        "evidence",
        "status",
        "decision_reason",
        "reviewer",
    },
    "lexicon-lineage.csv": {
        "old_bundle_id",
        "new_bundle_id",
        "change_type",
        "term",
        "canonical_term",
        "evidence",
        "human_decision",
        "decision_reason",
        "effective_at",
    },
    "representation-iteration.csv": {
        "candidate_id",
        "parent_representation_snapshot_id",
        "representation_snapshot_id",
        "lexicon_bundle_id",
        "assignment_fingerprint",
        "assignment_unchanged",
        "surface_scorecard",
        "concept_scorecard",
        "human_labelability",
        "pareto_status",
        "decision",
        "decision_reason",
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

EXPECTED_VISUALIZATION_POLICY = {
    "required": True,
    "contract_artifact": "visualization-contract.json",
    "plan_artifact": "visualization-plan.json",
    "manifest_artifact": "visualization-manifest.json",
    "validation_command": (
        "python scripts/validate_visualization_bundle.py <study-bundle-directory>"
    ),
    "layer_model": [
        "structure",
        "representation",
        "taxonomy",
        "governance",
    ],
    "shared_document_coordinates_required": True,
    "topic_minus_one_visible": True,
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


def validate_visualization_policy(policy: Any) -> list[str]:
    """Validate links to the standalone layered-visualization contract."""
    if not isinstance(policy, dict):
        return ["visualization_policy must be an object"]
    errors: list[str] = []
    for field, expected in EXPECTED_VISUALIZATION_POLICY.items():
        if policy.get(field) != expected:
            errors.append(f"visualization_policy.{field} must be {expected!r}")
    return errors


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


def _is_true(value: Any) -> bool:
    return value is True or str(value).strip().casefold() in {"true", "1", "yes"}


def validate_lexicon_governance(
    contract: dict[str, Any],
    manifest: dict[str, Any] | None,
    iteration_rows: list[dict[str, Any]],
    registry_rows: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Validate optional lexicon governance without treating it as structural tuning."""
    policy = contract.get("lexicon_policy")
    if not isinstance(policy, dict) or not policy.get("enabled"):
        return []

    errors: list[str] = []
    required_policy_fields = {
        "apply_to",
        "bundle_manifest",
        "candidate_generation_rule",
        "stop_rule",
        "assignment_invariant_required",
        "human_review_required",
    }
    for field in sorted(required_policy_fields):
        if field not in policy or policy.get(field) in (None, ""):
            errors.append(f"lexicon_policy lacks required field: {field}")
    if policy.get("apply_to") != "lexical_text":
        errors.append("lexicon_policy.apply_to must be lexical_text")
    if policy.get("assignment_invariant_required") is not True:
        errors.append("lexicon_policy.assignment_invariant_required must be true")
    if policy.get("human_review_required") is not True:
        errors.append("lexicon_policy.human_review_required must be true")
    if policy.get("bundle_manifest") != "lexicon-manifest.json":
        errors.append("lexicon_policy.bundle_manifest must be lexicon-manifest.json")

    if not isinstance(manifest, dict):
        errors.append("lexicon-manifest.json must contain a JSON object")
    else:
        if manifest.get("apply_to") != "lexical_text":
            errors.append("lexicon-manifest.json apply_to must be lexical_text")
        if not str(manifest.get("bundle_id", "")).strip():
            errors.append("lexicon-manifest.json must contain bundle_id")
        if not str(manifest.get("content_sha256", "")).strip():
            errors.append("lexicon-manifest.json must contain content_sha256")
        if manifest.get("conflicts") not in ([], None):
            errors.append("lexicon-manifest.json contains unresolved conflicts")

    current_bundle_id = (
        str(manifest.get("bundle_id", "")).strip()
        if isinstance(manifest, dict)
        else ""
    )
    if not iteration_rows:
        errors.append("representation-iteration.csv must contain at least one completed refresh")
    for index, row in enumerate(iteration_rows, start=2):
        prefix = f"representation-iteration.csv row {index}"
        for field in (
            "candidate_id",
            "representation_snapshot_id",
            "lexicon_bundle_id",
            "assignment_fingerprint",
        ):
            if not str(row.get(field, "")).strip():
                errors.append(f"{prefix} lacks {field}")
        if not _is_true(row.get("assignment_unchanged")):
            errors.append(f"{prefix} assignment_unchanged must be true")
    if current_bundle_id and not any(
        str(row.get("lexicon_bundle_id", "")).strip() == current_bundle_id
        for row in iteration_rows
    ):
        errors.append(
            "representation-iteration.csv must contain the current lexicon bundle"
        )

    if registry_rows is not None:
        representation_rows = [
            row
            for row in registry_rows
            if str(row.get("run_type", "")).strip().casefold() == "representation"
        ]
        if not representation_rows:
            errors.append(
                "experiment-registry.csv must contain a representation run for the enabled lexicon policy"
            )
        for index, row in enumerate(representation_rows, start=2):
            prefix = f"experiment-registry.csv representation row {index}"
            for field in (
                "candidate_id",
                "representation_snapshot_id",
                "lexicon_bundle_id",
                "assignment_fingerprint",
            ):
                if not str(row.get(field, "")).strip():
                    errors.append(f"{prefix} lacks {field}")
        registry_links = {
            (
                str(row.get("candidate_id", "")).strip(),
                str(row.get("representation_snapshot_id", "")).strip(),
                str(row.get("lexicon_bundle_id", "")).strip(),
                str(row.get("assignment_fingerprint", "")).strip(),
            )
            for row in representation_rows
        }
        for index, row in enumerate(iteration_rows, start=2):
            link = (
                str(row.get("candidate_id", "")).strip(),
                str(row.get("representation_snapshot_id", "")).strip(),
                str(row.get("lexicon_bundle_id", "")).strip(),
                str(row.get("assignment_fingerprint", "")).strip(),
            )
            if all(link) and link not in registry_links:
                errors.append(
                    f"representation-iteration.csv row {index} has no matching representation registry row"
                )
        if current_bundle_id and not any(
            str(row.get("lexicon_bundle_id", "")).strip() == current_bundle_id
            for row in representation_rows
        ):
            errors.append(
                "experiment-registry.csv must link the current lexicon bundle to a representation run"
            )
    return errors


def validate_lexicon_sources(
    root: Path, manifest: dict[str, Any] | None
) -> list[str]:
    """Recompile editable lexicon sources and verify that the manifest is current."""
    root = Path(root)
    if not isinstance(manifest, dict):
        return ["Cannot validate lexicon sources without a valid manifest"]
    config_path = root / "lexicon-config.json"
    if not config_path.is_file():
        return ["Cannot validate lexicon sources: lexicon-config.json is missing"]
    try:
        compiled = compile_lexicon_bundle(config_path)
    except ValueError as exc:
        return [f"Cannot compile lexicon source tables: {exc}"]
    errors: list[str] = []
    controlled_fields = (
        "schema_version",
        "bundle_name",
        "parent_bundle_id",
        "apply_to",
        "normalization",
        "tokenizer",
        "synonyms",
        "stopwords",
        "custom_terms",
        "bundle_id",
        "content_sha256",
        "synonym_map",
        "counts",
        "conflicts",
    )
    for field in controlled_fields:
        if compiled.get(field) != manifest.get(field):
            errors.append(
                f"lexicon-manifest.json {field} does not match the editable source tables"
            )
    compiled_sources = {
        (row.get("kind"), row.get("path")): row.get("sha256")
        for row in compiled.get("source_files", [])
    }
    manifest_sources = {
        (row.get("kind"), row.get("path")): row.get("sha256")
        for row in manifest.get("source_files", [])
        if isinstance(row, dict)
    }
    if compiled_sources != manifest_sources:
        errors.append(
            "lexicon-manifest.json source file hashes do not match the editable source tables"
        )
    return errors


def validate_semantic_selection_links(
    selected_model: dict[str, Any],
    tuning_trace: dict[str, Any],
    semantic_review: dict[str, Any],
    candidate_rows: list[dict[str, str]],
) -> list[str]:
    """Validate that the selected model follows the semantic champion chain."""

    errors: list[str] = []
    selected_id = str(selected_model.get("candidate_id", "")).strip()
    champion_id = str(tuning_trace.get("current_champion_id", "")).strip()
    if not selected_id:
        errors.append("selected-model.json candidate_id must not be blank")
    if selected_id != champion_id:
        errors.append(
            "selected-model.json candidate_id must equal the tuning trace "
            f"current champion {champion_id!r}"
        )

    final_stage_champion = str(
        tuning_trace.get("baseline_candidate_id", "")
    ).strip()
    stages = tuning_trace.get("stages", [])
    if isinstance(stages, list):
        for stage in stages:
            if isinstance(stage, dict) and str(
                stage.get("champion_after", "")
            ).strip():
                final_stage_champion = str(stage["champion_after"]).strip()
    interaction = tuning_trace.get("interaction_confirmation", {})
    if (
        isinstance(interaction, dict)
        and interaction.get("decision") == "promote"
        and str(interaction.get("promoted_candidate_id", "")).strip()
    ):
        final_stage_champion = str(
            interaction["promoted_candidate_id"]
        ).strip()
    if champion_id != final_stage_champion:
        errors.append(
            "tuning-trace current_champion_id does not equal the final "
            f"champion_after {final_stage_champion!r}"
        )

    assurance_level = str(
        selected_model.get(
            "assurance_level", tuning_trace.get("assurance_level", "")
        )
    ).strip()
    trace_level = str(tuning_trace.get("assurance_level", "")).strip()
    if assurance_level and trace_level and assurance_level != trace_level:
        errors.append(
            "selected-model.json assurance_level disagrees with tuning-trace.json"
        )

    review_candidate = str(semantic_review.get("candidate_id", "")).strip()
    if review_candidate and review_candidate != selected_id:
        errors.append(
            "semantic-review.json candidate_id does not match the selected model"
        )
    unresolved = semantic_review.get("unresolved_issues", [])
    if not isinstance(unresolved, list):
        errors.append("semantic-review.json unresolved_issues must be a list")
    elif any(str(item).strip() for item in unresolved):
        errors.append(
            "Selected model has unresolved semantic issues in semantic-review.json"
        )
    pair_decisions = semantic_review.get("pair_decisions", [])
    if isinstance(pair_decisions, list) and any(
        isinstance(item, dict) and item.get("unresolved") is True
        for item in pair_decisions
    ):
        errors.append("Selected model has unresolved semantic pair decisions")

    indexed_rows = {
        str(row.get("candidate_id", "")).strip(): row
        for row in candidate_rows
        if str(row.get("candidate_id", "")).strip()
    }
    selected_row = indexed_rows.get(selected_id)
    if selected_id and selected_row is None:
        errors.append(
            f"Selected candidate {selected_id} is absent from candidate-metrics.csv"
        )
    if (
        selected_row is not None
        and assurance_level in {"research", "publication_release"}
    ):
        if str(selected_row.get("semantic_review_status", "")).strip() != "pass":
            errors.append(
                "Research/publication selected candidate requires "
                "semantic_review_status=pass"
            )
        unresolved_count = str(
            selected_row.get("unresolved_semantic_decisions", "")
        ).strip()
        if unresolved_count not in {"", "0", "0.0", "false", "False"}:
            errors.append(
                "Selected candidate has unresolved semantic decisions in "
                "candidate-metrics.csv"
            )
    if (
        assurance_level in {"research", "publication_release"}
        and selected_model.get("provisional_defaults_used") is True
    ):
        errors.append(
            "Research/publication selection cannot use provisional exploratory "
            "defaults as final justification"
        )

    objectives = selected_model.get("selection_objectives", {})
    constraints = selected_model.get("selection_constraints", [])
    required_fields = selected_model.get("semantic_required_fields", {})
    if objectives:
        if not isinstance(objectives, dict):
            errors.append("selection_objectives must be an object")
        elif not isinstance(constraints, list):
            errors.append("selection_constraints must be a list")
        elif not isinstance(required_fields, dict):
            errors.append("semantic_required_fields must be an object")
        else:
            try:
                selection = select_pareto(
                    candidate_rows,
                    objectives={
                        str(field): str(direction)
                        for field, direction in objectives.items()
                    },
                    constraints=[str(item) for item in constraints],
                    required_fields={
                        str(field): str(expected)
                        for field, expected in required_fields.items()
                    },
                    champion_id=champion_id or None,
                )
            except ValueError as exc:
                errors.append(f"Cannot recompute model selection: {exc}")
            else:
                if selection["eligible_count"] >= 2:
                    declared = {
                        str(item).strip()
                        for item in selected_model.get(
                            "eligible_pareto_frontier", []
                        )
                        if str(item).strip()
                    }
                    actual = set(selection["frontier_ids"])
                    if declared != actual:
                        errors.append(
                            "selected-model.json eligible_pareto_frontier does "
                            "not match recomputed semantic-eligible frontier"
                        )
                    if selected_id not in actual:
                        errors.append(
                            "Selected candidate is not on the recomputed eligible "
                            "Pareto frontier"
                        )
    return errors


def _validate_legacy_bundle(root: Path) -> dict[str, Any]:
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
            reconnaissance_policy = contract.get("pre_model_reconnaissance")
            expected_reconnaissance_policy = {
                "required": True,
                "user_theme_mode": "coverage_and_interpretation_anchor",
                "allow_emergent_themes": True,
                "reading_plan_artifact": "corpus-reading-plan.json",
                "reading_ledger_artifact": "corpus-reading-ledger.csv",
                "reconnaissance_artifact": "theme-reconnaissance.json",
                "candidate_audit_artifact": "theme-candidate-audit.csv",
                "authorization_artifact": "modeling-authorization.json",
                "user_authorization_required": True,
            }
            if not isinstance(reconnaissance_policy, dict):
                errors.append(
                    "study-contract.json pre_model_reconnaissance must be an object"
                )
            else:
                for field, expected in expected_reconnaissance_policy.items():
                    if reconnaissance_policy.get(field) != expected:
                        errors.append(
                            f"pre_model_reconnaissance.{field} must be {expected!r}"
                        )
                if not str(reconnaissance_policy.get("authorization_id", "")).strip():
                    errors.append(
                        "pre_model_reconnaissance.authorization_id must not be blank"
                    )
            errors.extend(validate_parameter_governance(contract))
            if "visualization_policy" in contract:
                errors.extend(
                    validate_visualization_policy(contract["visualization_policy"])
                )
            if not contract.get("minimum_meaningful_theme"):
                errors.append("minimum_meaningful_theme must be justified before clustering")

            if route in {"long-document", "mixed"}:
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
            if route == "mixed":
                route_subsets = contract.get("route_subsets")
                expected_route_subsets = {"network-short", "long-document"}
                if not isinstance(route_subsets, dict):
                    errors.append("Mixed route requires an explicit route_subsets mapping")
                else:
                    actual_route_subsets = set(route_subsets)
                    for missing_subset in sorted(
                        expected_route_subsets.difference(actual_route_subsets)
                    ):
                        errors.append(
                            f"Mixed route route_subsets is missing {missing_subset}"
                        )
                    for unexpected_subset in sorted(
                        actual_route_subsets.difference(expected_route_subsets)
                    ):
                        errors.append(
                            f"Mixed route route_subsets has unsupported key "
                            f"{unexpected_subset}"
                        )
                    for subset in sorted(expected_route_subsets):
                        if subset in route_subsets and not str(
                            route_subsets.get(subset, "")
                        ).strip():
                            errors.append(
                                f"Mixed route route_subsets.{subset} analysis unit "
                                "must not be blank"
                            )
        elif loaded is not None:
            errors.append("study-contract.json must contain a JSON object")

    lexicon_enabled = bool(
        contract
        and isinstance(contract.get("lexicon_policy"), dict)
        and contract["lexicon_policy"].get("enabled")
    )
    if lexicon_enabled:
        missing_lexicon = sorted(
            name for name in LEXICON_REQUIRED_FILES if not (root / name).is_file()
        )
        errors.extend(f"Missing required file: {name}" for name in missing_lexicon)

    profile: dict[str, Any] = {}
    profile_path = root / "corpus-profile.json"
    if profile_path.is_file():
        loaded = _read_json(profile_path, errors)
        if isinstance(loaded, dict):
            profile = loaded
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

    reconnaissance_audit = validate_theme_reconnaissance(
        root, require_approval=True
    )
    errors.extend(
        f"Theme reconnaissance: {item}"
        for item in reconnaissance_audit["errors"]
    )
    approved_authorization_id = str(
        reconnaissance_audit.get("authorization_id", "")
    ).strip()
    if contract:
        if str(contract.get("research_question", "")).strip() != str(
            reconnaissance_audit.get("research_question", "")
        ).strip():
            errors.append(
                "study-contract.json research_question does not match the approved "
                "reconnaissance"
            )
        if str(contract.get("route", "")).strip() != str(
            reconnaissance_audit.get("route", "")
        ).strip():
            errors.append(
                "study-contract.json route does not match the approved reconnaissance"
            )
        reconnaissance_policy = contract.get("pre_model_reconnaissance")
        contract_authorization_id = (
            str(reconnaissance_policy.get("authorization_id", "")).strip()
            if isinstance(reconnaissance_policy, dict)
            else ""
        )
        if contract_authorization_id != approved_authorization_id:
            errors.append(
                "pre_model_reconnaissance.authorization_id does not match the "
                "approved reconnaissance"
            )
    modeling_run_types = {
        "baseline",
        "structural",
        "representation",
        "taxonomy",
        "mapping",
    }
    approved_corpus_fingerprint = str(
        profile.get("corpus_fingerprint", "")
    ).strip()
    for index, row in enumerate(
        tables.get("experiment-registry.csv", []), start=2
    ):
        run_type = str(row.get("run_type", "")).strip().casefold()
        if run_type not in modeling_run_types:
            errors.append(
                f"experiment-registry.csv row {index} has unknown run_type "
                f"{run_type or '<blank>'}"
            )
        row_authorization_id = str(row.get("authorization_id", "")).strip()
        if not row_authorization_id:
            errors.append(
                f"experiment-registry.csv row {index} modeling run lacks "
                "authorization_id"
            )
        elif row_authorization_id != approved_authorization_id:
            errors.append(
                f"experiment-registry.csv row {index} authorization_id does "
                "not match the approved reconnaissance"
            )
        row_corpus_fingerprint = str(row.get("corpus_fingerprint", "")).strip()
        if row_corpus_fingerprint != approved_corpus_fingerprint:
            errors.append(
                f"experiment-registry.csv row {index} corpus_fingerprint does "
                "not match the approved corpus"
            )

    lexicon_manifest: dict[str, Any] | None = None
    lexicon_manifest_path = root / "lexicon-manifest.json"
    if lexicon_manifest_path.is_file():
        loaded = _read_json(lexicon_manifest_path, errors)
        if isinstance(loaded, dict):
            lexicon_manifest = loaded
        elif loaded is not None:
            errors.append("lexicon-manifest.json must contain a JSON object")
    if contract:
        errors.extend(
            validate_lexicon_governance(
                contract,
                lexicon_manifest,
                tables.get("representation-iteration.csv", []),
                tables.get("experiment-registry.csv", []),
            )
        )
    if lexicon_enabled:
        errors.extend(validate_lexicon_sources(root, lexicon_manifest))

    if lexicon_enabled:
        allowed_candidate_statuses = {"accepted", "rejected", "deferred"}
        for index, row in enumerate(
            tables.get("lexicon-candidate-audit.csv", []), start=2
        ):
            status = str(row.get("status", "")).strip().casefold()
            if status not in allowed_candidate_statuses:
                errors.append(
                    f"lexicon-candidate-audit.csv row {index} status must be accepted, rejected, or deferred"
                )
            for field in ("decision_reason", "reviewer"):
                if not str(row.get(field, "")).strip():
                    errors.append(
                        f"lexicon-candidate-audit.csv row {index} lacks {field}"
                    )

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


def _merge_audits(*audits: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    for audit in audits:
        errors.extend(str(item) for item in audit.get("errors", []))
        warnings.extend(str(item) for item in audit.get("warnings", []))
    return {
        "valid": not errors,
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _read_required_json(
    root: Path,
    name: str,
    errors: list[str],
) -> dict[str, Any]:
    path = root / name
    if not path.is_file():
        return {}
    loaded = _read_json(path, errors)
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        errors.append(f"{name} must contain a JSON object")
        return {}
    return loaded


def _validate_assurance_bundle(
    root: Path,
    contract: dict[str, Any],
    *,
    assurance_level: str,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    errors.extend(validate_assurance_contract(contract))

    progressive = contract.get("progressive_coverage_claim") is True
    visualization_policy = contract.get("visualization_policy", {})
    visualization_enabled = bool(
        isinstance(visualization_policy, dict)
        and visualization_policy.get("required") is True
    )
    required = required_artifacts(
        assurance_level,
        progressive_coverage_claim=progressive,
        visualization_enabled=visualization_enabled,
    )
    missing = sorted(name for name in required if not (root / name).is_file())
    errors.extend(f"Missing required file: {name}" for name in missing)

    profile = _read_required_json(root, "corpus-profile.json", errors)
    for field in CORPUS_PROFILE_FIELDS:
        if field not in profile:
            errors.append(f"corpus-profile.json lacks required field: {field}")

    registry_header: list[str] = []
    registry_rows: list[dict[str, str]] = []
    registry_path = root / "experiment-registry.csv"
    if registry_path.is_file():
        registry_header, registry_rows = _read_table(registry_path, errors)
        registry_required = {
            "candidate_id",
            "run_type",
            "stage_id",
            "champion_parent_id",
            "changed_parameter_family",
            "corpus_fingerprint",
            "analysis_unit",
            "embedding_model",
            "umap_config",
            "hdbscan_config",
            "representation_config",
            "assignment_fingerprint",
            "semantic_review_status",
            "status",
        }
        for field in sorted(registry_required.difference(registry_header)):
            errors.append(f"experiment-registry.csv lacks required column: {field}")
        if not registry_rows:
            errors.append("experiment-registry.csv must contain at least one row")

    metrics_header: list[str] = []
    metric_rows: list[dict[str, str]] = []
    metrics_path = root / "candidate-metrics.csv"
    if metrics_path.is_file():
        metrics_header, metric_rows = _read_table(metrics_path, errors)
        metrics_required = {
            "candidate_id",
            "stage_id",
            "champion_parent_id",
            "semantic_review_status",
            "meaning_distinctiveness",
            "boundary_clarity",
            "theme_coverage_judgment",
            "artifact_risk",
            "unresolved_semantic_decisions",
            "comparison_to_champion",
        }
        for field in sorted(metrics_required.difference(metrics_header)):
            errors.append(f"candidate-metrics.csv lacks required column: {field}")
        if not metric_rows:
            errors.append("candidate-metrics.csv must contain at least one row")

    trace = _read_required_json(root, "tuning-trace.json", errors)
    if trace:
        trace_audit = validate_tuning_trace(
            trace,
            registry_rows,
            assurance_level=assurance_level,
        )
        errors.extend(
            f"Tuning trace: {item}" for item in trace_audit["errors"]
        )
        warnings.extend(
            f"Tuning trace: {item}" for item in trace_audit["warnings"]
        )

    review = _read_required_json(root, "semantic-review.json", errors)
    required_topic_uids: set[str] = set()
    topic_catalog_path = root / "topic-catalog.csv"
    if topic_catalog_path.is_file():
        _, topic_rows = _read_table(topic_catalog_path, errors)
        required_topic_uids = {
            str(row.get("topic_uid", "")).strip()
            for row in topic_rows
            if str(row.get("topic_uid", "")).strip()
        }
    if review:
        review_errors = validate_semantic_review(
            review,
            required_topic_uids=(
                required_topic_uids
                if assurance_level in {"research", "publication_release"}
                else set()
            ),
            required_pair_ids=set(),
        )
        errors.extend(
            f"Semantic review: {item}" for item in review_errors
        )

    selected = _read_required_json(root, "selected-model.json", errors)
    if selected and trace and review:
        errors.extend(
            validate_semantic_selection_links(
                selected,
                trace,
                review,
                metric_rows,
            )
        )

    if assurance_level in {"research", "publication_release"}:
        reconnaissance = validate_reconnaissance_for_level(
            root,
            assurance_level,
            progressive_coverage_claim=progressive,
        )
        errors.extend(
            f"Theme reconnaissance: {item}"
            for item in reconnaissance.get("errors", [])
        )
        warnings.extend(
            f"Theme reconnaissance: {item}"
            for item in reconnaissance.get("warnings", [])
        )

    if visualization_enabled:
        visualization = validate_visualization_bundle(root)
        errors.extend(
            f"Visualization bundle: {item}"
            for item in visualization.get("errors", [])
        )
        warnings.extend(
            f"Visualization bundle: {item}"
            for item in visualization.get("warnings", [])
        )

    report_path = root / "decision-report.md"
    if report_path.is_file():
        try:
            report = report_path.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"Cannot read decision-report.md: {exc}")
        else:
            if len(report.strip()) < 20:
                errors.append("decision-report.md is too short to document a decision")
            expected_marker = f"assurance level: {assurance_level}"
            if expected_marker not in report.casefold():
                errors.append(
                    "decision-report.md assurance level disagrees with "
                    "study-contract.json"
                )

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def validate_bundle(root: Path) -> dict[str, Any]:
    """Validate a legacy or assurance-aware BERTopic study bundle."""

    root = Path(root)
    if not root.exists() or not root.is_dir():
        return {
            "valid": False,
            "errors": [f"Study bundle directory does not exist: {root}"],
            "warnings": [],
        }
    contract_path = root / "study-contract.json"
    if not contract_path.is_file():
        return _validate_legacy_bundle(root)
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return _validate_legacy_bundle(root)
    if not isinstance(contract, dict):
        return _validate_legacy_bundle(root)

    try:
        resolved = resolve_assurance_level(contract)
    except ValueError as exc:
        return {"valid": False, "errors": [str(exc)], "warnings": []}
    level = resolved["assurance_level"]
    if resolved["legacy_strict"]:
        legacy = _validate_legacy_bundle(root)
        legacy["warnings"] = list(legacy["warnings"]) + resolved["warnings"]
        return legacy

    assurance_audit = _validate_assurance_bundle(
        root,
        contract,
        assurance_level=level,
    )
    if level == "publication_release":
        legacy_audit = _validate_legacy_bundle(root)
        return _merge_audits(legacy_audit, assurance_audit)
    return assurance_audit


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
