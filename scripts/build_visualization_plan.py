#!/usr/bin/env python3
"""Build a deterministic, layered research-visualization plan for BERTopic."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_OUTPUTS = (
    "interactive_html",
    "static_vector",
    "static_raster",
    "source_data",
    "caption",
    "alt_text",
)

HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")

CORE_FIGURES: tuple[dict[str, Any], ...] = (
    {
        "figure_id": "topic-term-barchart",
        "layer": "representation",
        "research_question": (
            "Which ranked c-TF-IDF terms represent each topic, and how concentrated "
            "is the lexical evidence within topics?"
        ),
        "input_artifact_ids": (
            "topic_terms",
            "topic_catalog",
            "topic_color_map",
        ),
        "basis_source": "ctfidf",
        "outlier_policy": "exclude_with_declared_scope",
        "preferred_outputs": {
            "interactive_html": "visualize_barchart.html",
            "static_vector": "figure_topic_term_barchart.svg",
            "static_raster": "figure_topic_term_barchart.png",
        },
    },
    {
        "figure_id": "document-map",
        "layer": "structure",
        "research_question": (
            "How are modeled units arranged in the frozen document-embedding "
            "projection, including Topic -1 and topic boundaries?"
        ),
        "input_artifact_ids": (
            "document_topics",
            "document_coordinates",
            "document_projection_parameters",
            "topic_catalog",
            "topic_color_map",
        ),
        "basis_source": "document_projection",
        "outlier_policy": "include_topic_minus_one",
        "preferred_outputs": {
            "interactive_html": "visualize_documents.html",
            "static_vector": "figure_bertopic_datamap.svg",
            "static_raster": "figure_bertopic_datamap.png",
        },
    },
    {
        "figure_id": "topic-map",
        "layer": "structure",
        "research_question": (
            "How are topics positioned in the registered topic relation space, "
            "and which relations require closer evidence review?"
        ),
        "input_artifact_ids": (
            "topic_coordinates",
            "topic_projection_parameters",
            "topic_catalog",
            "topic_color_map",
        ),
        "basis_source": "topic_map",
        "outlier_policy": "exclude_with_declared_scope",
        "preferred_outputs": {
            "interactive_html": "visualize_topics.html",
            "static_vector": "visualize_topics.svg",
            "static_raster": "visualize_topics.png",
        },
    },
    {
        "figure_id": "topic-similarity-heatmap",
        "layer": "taxonomy",
        "research_question": (
            "Which topic pairs are most similar in the registered taxonomy "
            "relation space at the selected hierarchy level?"
        ),
        "input_artifact_ids": (
            "topic_similarity",
            "topic_catalog",
            "topic_color_map",
        ),
        "basis_source": "taxonomy",
        "outlier_policy": "exclude_with_declared_scope",
        "preferred_outputs": {
            "interactive_html": "visualize_heatmap.html",
            "static_vector": "visualize_heatmap.svg",
            "static_raster": "visualize_heatmap.png",
        },
    },
    {
        "figure_id": "topic-hierarchy",
        "layer": "taxonomy",
        "research_question": (
            "Which evidence-linked topic merges form a defensible coarser "
            "taxonomy, and at what relation distances?"
        ),
        "input_artifact_ids": (
            "topic_similarity",
            "topic_hierarchy",
            "topic_catalog",
            "topic_color_map",
        ),
        "basis_source": "taxonomy",
        "outlier_policy": "exclude_with_declared_scope",
        "preferred_outputs": {
            "interactive_html": "visualize_hierarchy.html",
            "static_vector": "visualize_hierarchy.svg",
            "static_raster": "visualize_hierarchy.png",
        },
    },
    {
        "figure_id": "ctfidf-term-score-decline",
        "layer": "representation",
        "research_question": (
            "How quickly does ranked c-TF-IDF evidence decline within each "
            "topic, and where do additional terms stop adding much distinction?"
        ),
        "input_artifact_ids": (
            "topic_terms",
            "topic_catalog",
            "topic_color_map",
        ),
        "basis_source": "ctfidf",
        "outlier_policy": "exclude_with_declared_scope",
        "preferred_outputs": {
            "interactive_html": "visualize_term_rank.html",
            "static_vector": "figure_ctfidf_term_score_decline.svg",
            "static_raster": "figure_ctfidf_term_score_decline.png",
        },
    },
    {
        "figure_id": "topic-prevalence",
        "layer": "governance",
        "research_question": (
            "What counts and shares do all assigned topics have, including "
            "Topic -1, at the declared analysis unit?"
        ),
        "input_artifact_ids": (
            "document_topics",
            "topic_catalog",
            "topic_color_map",
        ),
        "basis_source": "none",
        "outlier_policy": "include_topic_minus_one",
        "preferred_outputs": {
            "interactive_html": "visualize_topic_prevalence.html",
            "static_vector": "figure_topic_prevalence.svg",
            "static_raster": "figure_topic_prevalence.png",
        },
    },
    {
        "figure_id": "candidate-pareto",
        "layer": "governance",
        "research_question": (
            "Which candidate models remain non-dominated after declared quality "
            "constraints, and what trade-offs distinguish them?"
        ),
        "input_artifact_ids": ("candidate_metrics",),
        "basis_source": "none",
        "outlier_policy": "reported_guardrail_not_objective",
        "preferred_outputs": {
            "interactive_html": "visualize_candidate_pareto.html",
            "static_vector": "figure_candidate_pareto.svg",
            "static_raster": "figure_candidate_pareto.png",
        },
    },
    {
        "figure_id": "topic-stability",
        "layer": "governance",
        "research_question": (
            "Which substantive topics survive the registered seeds, group-aware "
            "resamples, or snapshot perturbations, and with what uncertainty?"
        ),
        "input_artifact_ids": (
            "stability_metrics",
            "topic_catalog",
            "topic_color_map",
        ),
        "basis_source": "registered_stability_evidence",
        "outlier_policy": "reported_separately",
        "preferred_outputs": {
            "interactive_html": "visualize_topic_stability.html",
            "static_vector": "figure_topic_stability.svg",
            "static_raster": "figure_topic_stability.png",
        },
    },
    {
        "figure_id": "outlier-diagnostics",
        "layer": "governance",
        "research_question": (
            "What composes Topic -1, which registered groups or artifacts "
            "contribute to it, and which topics are its nearest alternatives?"
        ),
        "input_artifact_ids": (
            "document_topics",
            "outlier_diagnostics",
            "topic_color_map",
        ),
        "basis_source": "registered_outlier_evidence",
        "outlier_policy": "include_topic_minus_one",
        "preferred_outputs": {
            "interactive_html": "visualize_outlier_diagnostics.html",
            "static_vector": "figure_outlier_diagnostics.svg",
            "static_raster": "figure_outlier_diagnostics.png",
        },
    },
    {
        "figure_id": "coverage-leakage-audit",
        "layer": "governance",
        "research_question": (
            "Which reference themes and validation groups are covered, and where "
            "does source or group leakage threaten interpretation?"
        ),
        "input_artifact_ids": (
            "candidate_metrics",
            "coverage_diagnostics",
        ),
        "basis_source": "registered_coverage_evidence",
        "outlier_policy": "reported_as_coverage_evidence",
        "preferred_outputs": {
            "interactive_html": "visualize_coverage_leakage.html",
            "static_vector": "figure_coverage_leakage.svg",
            "static_raster": "figure_coverage_leakage.png",
        },
    },
)

CORE_FIGURE_IDS = tuple(figure["figure_id"] for figure in CORE_FIGURES)

ROUTE_FIGURES: tuple[dict[str, Any], ...] = (
    {
        "figure_id": "short-text-artifact-audit",
        "layer": "governance",
        "routes": {"network-short", "mixed"},
        "research_question": (
            "Are short-text topics driven by substantive content rather than "
            "duplicate families, sources, accounts, templates, or platform tokens?"
        ),
        "input_artifact_ids": (
            "short_text_artifacts",
            "topic_color_map",
        ),
        "basis_source": "registered_short_text_artifact_evidence",
        "outlier_policy": "include_topic_minus_one",
        "preferred_outputs": {
            "interactive_html": "visualize_short_text_artifacts.html",
            "static_vector": "figure_short_text_artifacts.svg",
            "static_raster": "figure_short_text_artifacts.png",
        },
    },
    {
        "figure_id": "parent-document-topic-profile",
        "layer": "governance",
        "routes": {"long-document", "mixed"},
        "research_question": (
            "How do segment-level topics contribute to parent-document profiles "
            "without collapsing multi-topic documents to one hard label?"
        ),
        "input_artifact_ids": (
            "parent_document_topics",
            "topic_color_map",
        ),
        "basis_source": "registered_parent_document_aggregation",
        "outlier_policy": "include_topic_minus_one",
        "preferred_outputs": {
            "interactive_html": "visualize_parent_document_topics.html",
            "static_vector": "figure_parent_document_topics.svg",
            "static_raster": "figure_parent_document_topics.png",
        },
    },
)

CONDITIONAL_FIGURES: tuple[dict[str, Any], ...] = (
    {
        "figure_id": "topics-over-time",
        "module": "time",
        "layer": "governance",
        "research_question": (
            "How does prevalence within the frozen global taxonomy change across "
            "the registered time field?"
        ),
        "input_artifact_ids": (
            "topics_over_time",
            "topic_color_map",
        ),
        "basis_source": "registered_time_topic_evidence",
        "outlier_policy": "report_explicitly_or_exclude_with_reason",
        "preferred_outputs": {
            "interactive_html": "visualize_topics_over_time.html",
            "static_vector": "figure_topics_over_time.svg",
            "static_raster": "figure_topics_over_time.png",
        },
    },
    {
        "figure_id": "topics-by-group",
        "module": "group",
        "layer": "governance",
        "research_question": (
            "How do topic prevalences differ across the registered substantive "
            "groups under one shared taxonomy?"
        ),
        "input_artifact_ids": (
            "topics_by_group",
            "topic_color_map",
        ),
        "basis_source": "registered_group_topic_evidence",
        "outlier_policy": "report_explicitly_or_exclude_with_reason",
        "preferred_outputs": {
            "interactive_html": "visualize_topics_by_group.html",
            "static_vector": "figure_topics_by_group.svg",
            "static_raster": "figure_topics_by_group.png",
        },
    },
    {
        "figure_id": "topic-geography",
        "module": "geography",
        "layer": "governance",
        "research_question": (
            "How are topic prevalences distributed across the registered "
            "geographic units without confusing location density with theme strength?"
        ),
        "input_artifact_ids": (
            "topic_geography",
            "topic_color_map",
        ),
        "basis_source": "registered_geographic_topic_evidence",
        "outlier_policy": "report_explicitly_or_exclude_with_reason",
        "preferred_outputs": {
            "interactive_html": "visualize_topic_geography.html",
            "static_vector": "figure_topic_geography.svg",
            "static_raster": "figure_topic_geography.png",
        },
    },
    {
        "figure_id": "topic-lineage",
        "module": "lineage",
        "layer": "governance",
        "research_question": (
            "Which permanent topics continue, split, merge, emerge, or retire "
            "across registered snapshots?"
        ),
        "input_artifact_ids": (
            "topic_lineage",
            "topic_color_map",
        ),
        "basis_source": "registered_lineage_evidence",
        "outlier_policy": "reported_separately",
        "preferred_outputs": {
            "interactive_html": "visualize_topic_lineage.html",
            "static_vector": "figure_topic_lineage.svg",
            "static_raster": "figure_topic_lineage.png",
        },
    },
    {
        "figure_id": "document-topic-distribution",
        "module": "document_distribution",
        "layer": "governance",
        "research_question": (
            "Which selected documents have concentrated or mixed topic evidence "
            "under the registered distribution method?"
        ),
        "input_artifact_ids": (
            "document_topic_distributions",
            "topic_color_map",
        ),
        "basis_source": "registered_document_topic_distribution",
        "outlier_policy": "report_explicitly_or_exclude_with_reason",
        "preferred_outputs": {
            "interactive_html": "visualize_document_topic_distribution.html",
            "static_vector": "figure_document_topic_distribution.svg",
            "static_raster": "figure_document_topic_distribution.png",
        },
    },
)

EXPECTED_CONDITIONALS = {
    "time": {
        "field_map_keys": ["time"],
        "data_artifact_ids": ["topics_over_time"],
    },
    "group": {
        "field_map_keys": ["group"],
        "data_artifact_ids": ["topics_by_group"],
    },
    "geography": {
        "field_map_keys": ["latitude", "longitude"],
        "data_artifact_ids": ["topic_geography"],
    },
    "lineage": {
        "field_map_keys": [],
        "data_artifact_ids": ["topic_lineage"],
    },
    "document_distribution": {
        "field_map_keys": [],
        "data_artifact_ids": ["document_topic_distributions"],
    },
}

EXPECTED_EXPORT_POLICY = {
    "self_contained_html": True,
    "static_vector": True,
    "static_raster_png": True,
    "source_data": True,
    "caption": True,
    "alt_text": True,
    "sha256": True,
    "static_title_location": "caption",
    "colorblind_safe": True,
}

ALLOWED_RELATION_BASES = {
    "semantic_topic_embeddings",
    "document_topic_centroids",
    "ctfidf_lexical",
}

ASSURANCE_LEVELS = {
    "exploratory",
    "research",
    "publication_release",
}


def figure_requirement(
    figure_id: str,
    *,
    assurance_level: str,
    enabled_modules: set[str],
) -> str:
    """Return the evidence obligation for one planned figure.

    A blank level is legacy strict behavior, so existing contracts cannot
    silently downgrade their visualization obligations.
    """

    level = assurance_level or "publication_release"
    if level not in ASSURANCE_LEVELS:
        raise ValueError(
            "assurance_level must be exploratory, research, or publication_release"
        )
    if level == "exploratory":
        return "optional"
    if level == "research":
        return "required" if figure_id in enabled_modules else "optional"
    return "required"


def _canonical_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _nonblank(value: Any) -> bool:
    return bool(str(value).strip())


def _registered_artifact(contract: dict[str, Any], artifact_id: str) -> bool:
    artifacts = contract.get("data_artifacts")
    if not isinstance(artifacts, dict):
        return False
    record = artifacts.get(artifact_id)
    if not isinstance(record, dict):
        return False
    path = str(record.get("path", "")).strip()
    digest = str(record.get("sha256", "")).strip()
    return bool(path and HASH_PATTERN.fullmatch(digest))


def validate_contract(contract: dict[str, Any]) -> list[str]:
    """Validate the generic planning contract without requiring files to exist."""
    errors: list[str] = []
    if contract.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    for field in ("study_id", "snapshot_id"):
        if not _nonblank(contract.get(field)):
            errors.append(f"{field} must not be blank")

    route = contract.get("route")
    if route not in {"network-short", "long-document", "mixed"}:
        errors.append("route must be network-short, long-document, or mixed")

    field_map = contract.get("field_map")
    if not isinstance(field_map, dict):
        errors.append("field_map must be an object")
        field_map = {}
    for field in ("unit_id", "topic_id", "topic_uid", "topic_label"):
        if not _nonblank(field_map.get(field)):
            errors.append(f"field_map.{field} must not be blank")
    if route in {"long-document", "mixed"} and not _nonblank(
        field_map.get("parent_document_id")
    ):
        errors.append(
            "field_map.parent_document_id must not be blank for long-document or mixed"
        )

    artifacts = contract.get("data_artifacts")
    if not isinstance(artifacts, dict):
        errors.append("data_artifacts must be an object")
        artifacts = {}
    for artifact_id, record in artifacts.items():
        prefix = f"data_artifacts.{artifact_id}"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        path = str(record.get("path", "")).strip()
        digest = str(record.get("sha256", "")).strip()
        if bool(path) != bool(digest):
            errors.append(f"{prefix} must register both path and sha256")
        if digest and not HASH_PATTERN.fullmatch(digest):
            errors.append(f"{prefix}.sha256 must use sha256:<64 lowercase hex>")

    projection = contract.get("document_projection")
    if not isinstance(projection, dict):
        errors.append("document_projection must be an object")
        projection = {}
    for field in (
        "basis",
        "coordinate_artifact_id",
        "method",
        "parameters_artifact_id",
        "seed_or_determinism",
    ):
        if not _nonblank(projection.get(field)):
            errors.append(f"document_projection.{field} must not be blank")
    if (
        _nonblank(projection.get("basis"))
        and projection.get("basis") != "document_embeddings"
    ):
        errors.append("document_projection.basis must be document_embeddings")
    expected_projection_ids = {
        "coordinate_artifact_id": "document_coordinates",
        "parameters_artifact_id": "document_projection_parameters",
    }
    for field, expected in expected_projection_ids.items():
        if _nonblank(projection.get(field)) and projection.get(field) != expected:
            errors.append(
                f"document_projection.{field} must be {expected!r}"
            )

    relation_spaces = contract.get("relation_spaces")
    if not isinstance(relation_spaces, dict):
        errors.append("relation_spaces must be an object")
        relation_spaces = {}
    for name in ("topic_map", "taxonomy"):
        relation = relation_spaces.get(name)
        if not isinstance(relation, dict):
            errors.append(f"relation_spaces.{name} must be an object")
            continue
        for field in ("basis", "relation_artifact_id"):
            if not _nonblank(relation.get(field)):
                errors.append(f"relation_spaces.{name}.{field} must not be blank")
        basis = relation.get("basis")
        if _nonblank(basis) and basis not in ALLOWED_RELATION_BASES:
            errors.append(
                f"relation_spaces.{name}.basis must explicitly identify a "
                "semantic, centroid, or c-TF-IDF lexical space"
            )
    topic_relation = relation_spaces.get("topic_map", {})
    if isinstance(topic_relation, dict) and not _nonblank(
        topic_relation.get("parameters_artifact_id")
    ):
        errors.append(
            "relation_spaces.topic_map.parameters_artifact_id must not be blank"
        )
    if isinstance(topic_relation, dict):
        expected_topic_ids = {
            "relation_artifact_id": "topic_coordinates",
            "parameters_artifact_id": "topic_projection_parameters",
        }
        for field, expected in expected_topic_ids.items():
            if _nonblank(topic_relation.get(field)) and topic_relation.get(
                field
            ) != expected:
                errors.append(
                    f"relation_spaces.topic_map.{field} must be {expected!r}"
                )
    taxonomy_relation = relation_spaces.get("taxonomy", {})
    if isinstance(taxonomy_relation, dict) and not _nonblank(
        taxonomy_relation.get("hierarchy_artifact_id")
    ):
        errors.append(
            "relation_spaces.taxonomy.hierarchy_artifact_id must not be blank"
        )
    if isinstance(taxonomy_relation, dict):
        expected_taxonomy_ids = {
            "relation_artifact_id": "topic_similarity",
            "hierarchy_artifact_id": "topic_hierarchy",
        }
        for field, expected in expected_taxonomy_ids.items():
            if _nonblank(taxonomy_relation.get(field)) and taxonomy_relation.get(
                field
            ) != expected:
                errors.append(
                    f"relation_spaces.taxonomy.{field} must be {expected!r}"
                )

    conditional_modules = contract.get("conditional_modules")
    if not isinstance(conditional_modules, dict):
        errors.append("conditional_modules must be an object")
        conditional_modules = {}
    for name, expected in EXPECTED_CONDITIONALS.items():
        module = conditional_modules.get(name)
        prefix = f"conditional_modules.{name}"
        if not isinstance(module, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not isinstance(module.get("enabled"), bool):
            errors.append(f"{prefix}.enabled must be true or false")
        if module.get("field_map_keys") != expected["field_map_keys"]:
            errors.append(
                f"{prefix}.field_map_keys must equal {expected['field_map_keys']!r}"
            )
        if module.get("data_artifact_ids") != expected["data_artifact_ids"]:
            errors.append(
                f"{prefix}.data_artifact_ids must equal "
                f"{expected['data_artifact_ids']!r}"
            )
        if module.get("enabled") is True:
            for field in expected["field_map_keys"]:
                if not _nonblank(field_map.get(field)):
                    errors.append(
                        f"{prefix} requires nonblank field_map.{field}"
                    )

    color_map_id = contract.get("topic_color_map_artifact_id")
    if not _nonblank(color_map_id):
        errors.append("topic_color_map_artifact_id must not be blank")
    elif color_map_id != "topic_color_map":
        errors.append(
            "topic_color_map_artifact_id must be 'topic_color_map'"
        )
    if contract.get("outlier_topic_id") != "-1":
        errors.append("outlier_topic_id must be '-1' for BERTopic")

    export_policy = contract.get("export_policy")
    if not isinstance(export_policy, dict):
        errors.append("export_policy must be an object")
    else:
        for field, expected in EXPECTED_EXPORT_POLICY.items():
            if export_policy.get(field) != expected:
                errors.append(f"export_policy.{field} must be {expected!r}")

    return errors


def _basis_links(
    definition: dict[str, Any],
    contract: dict[str, Any],
) -> tuple[str, str, str]:
    source = definition["basis_source"]
    projection = contract.get("document_projection", {})
    relations = contract.get("relation_spaces", {})
    if source == "ctfidf":
        return "ctfidf_lexical", "", "topic_terms"
    if source == "document_projection":
        return (
            str(projection.get("basis", "")),
            str(projection.get("coordinate_artifact_id", "")),
            "",
        )
    if source == "topic_map":
        relation = relations.get("topic_map", {})
        artifact_id = str(relation.get("relation_artifact_id", ""))
        return str(relation.get("basis", "")), artifact_id, artifact_id
    if source == "taxonomy":
        relation = relations.get("taxonomy", {})
        return (
            str(relation.get("basis", "")),
            "",
            str(relation.get("relation_artifact_id", "")),
        )
    if source == "none":
        return "not_applicable", "", ""
    return source, "", ""


def _materialize_figure(
    definition: dict[str, Any],
    contract: dict[str, Any],
    *,
    requirement: str,
    assurance_requirement: str,
    active: bool,
    activation_reason: str,
) -> dict[str, Any]:
    input_ids = list(definition["input_artifact_ids"])
    missing = sorted(
        artifact_id
        for artifact_id in input_ids
        if not _registered_artifact(contract, artifact_id)
    )
    if not active:
        status = "not_applicable"
        missing = []
    elif missing:
        status = (
            "blocked_missing_inputs"
            if assurance_requirement == "required"
            else "optional_missing_inputs"
        )
    else:
        status = "ready"
    basis, coordinate_id, relation_id = _basis_links(definition, contract)
    color_id = (
        str(contract.get("topic_color_map_artifact_id", ""))
        if "topic_color_map" in input_ids
        else ""
    )
    return {
        "figure_id": definition["figure_id"],
        "layer": definition["layer"],
        "requirement": requirement,
        "assurance_requirement": assurance_requirement,
        "status": status,
        "activation_reason": activation_reason,
        "research_question": definition["research_question"],
        "input_artifact_ids": input_ids,
        "missing_artifact_ids": missing,
        "relation_basis": basis,
        "coordinate_artifact_id": coordinate_id,
        "relation_artifact_id": relation_id,
        "color_map_artifact_id": color_id,
        "outlier_policy": definition["outlier_policy"],
        "required_outputs": list(REQUIRED_OUTPUTS),
        "preferred_outputs": dict(definition["preferred_outputs"]),
        "static_title_location": "caption",
    }


def build_plan(contract: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic plan that never drops a required missing figure."""
    if not isinstance(contract, dict):
        raise TypeError("contract must be a JSON object")
    contract_digest = (
        "sha256:" + hashlib.sha256(_canonical_bytes(contract)).hexdigest()
    )
    assurance_level = str(
        contract.get("assurance_level", "publication_release")
    ).strip() or "publication_release"
    configured_figures = contract.get("decision_relevant_figure_ids", [])
    if not isinstance(configured_figures, list):
        configured_figures = []
    enabled_figure_ids = {
        str(figure_id).strip()
        for figure_id in configured_figures
        if _nonblank(figure_id)
    }
    modules = contract.get("conditional_modules")
    if not isinstance(modules, dict):
        modules = {}
    for definition in CONDITIONAL_FIGURES:
        module = modules.get(definition["module"])
        if isinstance(module, dict) and module.get("enabled") is True:
            enabled_figure_ids.add(definition["figure_id"])

    figures: list[dict[str, Any]] = []
    figures.extend(
        _materialize_figure(
            definition,
            contract,
            requirement="core",
            assurance_requirement=figure_requirement(
                definition["figure_id"],
                assurance_level=assurance_level,
                enabled_modules=enabled_figure_ids,
            ),
            active=True,
            activation_reason="mandatory_core_figure",
        )
        for definition in CORE_FIGURES
    )

    route = contract.get("route")
    for definition in ROUTE_FIGURES:
        active = route in definition["routes"]
        figures.append(
            _materialize_figure(
                definition,
                contract,
                requirement="route",
                assurance_requirement=figure_requirement(
                    definition["figure_id"],
                    assurance_level=assurance_level,
                    enabled_modules=enabled_figure_ids,
                ),
                active=active,
                activation_reason=(
                    f"route={route}"
                    if active
                    else f"not_applicable_for_route={route}"
                ),
            )
        )

    for definition in CONDITIONAL_FIGURES:
        module_name = definition["module"]
        module = modules.get(module_name)
        active = bool(isinstance(module, dict) and module.get("enabled") is True)
        figures.append(
            _materialize_figure(
                definition,
                contract,
                requirement="conditional",
                assurance_requirement=figure_requirement(
                    definition["figure_id"],
                    assurance_level=assurance_level,
                    enabled_modules=enabled_figure_ids,
                ),
                active=active,
                activation_reason=(
                    f"conditional_module={module_name}:enabled"
                    if active
                    else f"conditional_module={module_name}:disabled"
                ),
            )
        )

    required_figures = [
        figure
        for figure in figures
        if figure["status"] != "not_applicable"
        and figure["assurance_requirement"] == "required"
    ]
    summary = {
        "figure_count": len(figures),
        "required_figure_count": len(required_figures),
        "ready_required_count": sum(
            figure["status"] == "ready" for figure in required_figures
        ),
        "blocked_required_count": sum(
            figure["status"] == "blocked_missing_inputs"
            for figure in required_figures
        ),
        "not_applicable_count": sum(
            figure["status"] == "not_applicable" for figure in figures
        ),
        "optional_figure_count": sum(
            figure["status"] != "not_applicable"
            and figure["assurance_requirement"] == "optional"
            for figure in figures
        ),
    }
    return {
        "schema_version": 1,
        "plan_id": f"visualization-plan-{contract_digest.split(':', 1)[1][:16]}",
        "contract_sha256": contract_digest,
        "study_id": contract.get("study_id", ""),
        "snapshot_id": contract.get("snapshot_id", ""),
        "assurance_level": assurance_level,
        "route": route,
        "field_map": deepcopy_json(contract.get("field_map", {})),
        "outlier_topic_id": contract.get("outlier_topic_id", ""),
        "contract_errors": validate_contract(contract),
        "summary": summary,
        "figures": figures,
    }


def deepcopy_json(value: Any) -> Any:
    """Copy JSON-compatible data without importing a broader utility."""
    return json.loads(json.dumps(value, ensure_ascii=False))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a deterministic layered BERTopic visualization plan"
    )
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="Return non-zero when any required figure lacks registered inputs",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        loaded = json.loads(args.contract.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {
                    "valid": False,
                    "errors": [f"Cannot read visualization contract: {exc}"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    if not isinstance(loaded, dict):
        print(
            json.dumps(
                {
                    "valid": False,
                    "errors": ["Visualization contract must contain a JSON object"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    plan = build_plan(loaded)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "valid": not plan["contract_errors"],
                "output": str(args.output),
                "plan_id": plan["plan_id"],
                "summary": plan["summary"],
                "contract_errors": plan["contract_errors"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if plan["contract_errors"]:
        return 1
    if args.require_ready and plan["summary"]["blocked_required_count"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
