#!/usr/bin/env python3
"""Assurance-aware workflow policy for BERTopic studies.

The policy controls evidence obligations. It does not infer topic meaning,
select a model, or manufacture numerical thresholds.
"""

from __future__ import annotations

from typing import Any


ASSURANCE_LEVELS: tuple[str, ...] = (
    "exploratory",
    "research",
    "publication_release",
)

EXPLORATORY_REQUIRED = {
    "study-contract.json",
    "corpus-profile.json",
    "experiment-registry.csv",
    "candidate-metrics.csv",
    "tuning-trace.json",
    "semantic-review.json",
    "decision-report.md",
}

RESEARCH_ADDITIONAL = {
    "selected-model.json",
    "topic-catalog.csv",
    "theme-reconnaissance.json",
    "missing-theme-audit.csv",
}

PUBLICATION_ADDITIONAL = {
    "corpus-reading-plan.json",
    "corpus-reading-ledger.csv",
    "theme-candidate-audit.csv",
    "modeling-authorization.json",
    "topic-lineage.csv",
    "human-topic-audit.csv",
    "topic-pair-audit.csv",
    "evidence-log.csv",
    "visualization-contract.json",
    "visualization-plan.json",
    "visualization-manifest.json",
}

VISUALIZATION_ARTIFACTS = {
    "visualization-contract.json",
    "visualization-plan.json",
    "visualization-manifest.json",
}

PROGRESSIVE_READING_ARTIFACTS = {
    "corpus-reading-plan.json",
    "corpus-reading-ledger.csv",
}

AUTHORIZATION_BASES = {
    "user_request",
    "explicit_preview_approval",
    "external_release_approval",
}


def resolve_assurance_level(contract: dict[str, Any]) -> dict[str, Any]:
    """Resolve explicit assurance or retain legacy strict behavior.

    A missing level is intentionally not interpreted as exploratory. Existing
    bundles remain publication-strict until they are migrated deliberately.
    """

    raw = str(contract.get("assurance_level", "")).strip()
    if not raw:
        return {
            "assurance_level": "publication_release",
            "legacy_strict": True,
            "warnings": [
                "study-contract.json has no assurance_level; applying legacy "
                "publication_release requirements until the bundle is migrated"
            ],
        }
    if raw not in ASSURANCE_LEVELS:
        raise ValueError(
            f"Unknown assurance_level {raw!r}; expected one of "
            f"{', '.join(ASSURANCE_LEVELS)}"
        )
    return {
        "assurance_level": raw,
        "legacy_strict": False,
        "warnings": [],
    }


def required_artifacts(
    assurance_level: str,
    *,
    progressive_coverage_claim: bool,
    visualization_enabled: bool,
) -> set[str]:
    """Return artifacts that must exist for the declared claim level."""

    if assurance_level not in ASSURANCE_LEVELS:
        raise ValueError(
            f"Unknown assurance_level {assurance_level!r}; expected one of "
            f"{', '.join(ASSURANCE_LEVELS)}"
        )

    required = set(EXPLORATORY_REQUIRED)
    if assurance_level in {"research", "publication_release"}:
        required.update(RESEARCH_ADDITIONAL)
    if assurance_level == "research" and progressive_coverage_claim:
        required.update(PROGRESSIVE_READING_ARTIFACTS)
    if assurance_level == "research" and visualization_enabled:
        required.update(VISUALIZATION_ARTIFACTS)
    if assurance_level == "publication_release":
        required.update(PUBLICATION_ADDITIONAL)
    return required


def _nonblank_items(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(bool(str(item).strip()) for item in value)
    )


def validate_assurance_contract(contract: dict[str, Any]) -> list[str]:
    """Validate claim, authorization, semantic, and cumulative-tuning policy."""

    errors: list[str] = []
    try:
        resolved = resolve_assurance_level(contract)
    except ValueError as exc:
        return [str(exc)]

    level = resolved["assurance_level"]
    claim_scope = str(contract.get("claim_scope", "")).strip()
    expected_scope = {
        "exploratory": "exploratory_only",
        "research": "research",
        "publication_release": "publication_release",
    }[level]
    if claim_scope != expected_scope:
        errors.append(
            f"claim_scope must be {expected_scope!r} for assurance_level {level!r}"
        )

    authorization_basis = str(contract.get("authorization_basis", "")).strip()
    if authorization_basis not in AUTHORIZATION_BASES:
        errors.append(
            "authorization_basis must be user_request, "
            "explicit_preview_approval, or external_release_approval"
        )
    if (
        level == "publication_release"
        and authorization_basis != "explicit_preview_approval"
    ):
        errors.append(
            "publication_release requires authorization_basis "
            "'explicit_preview_approval'"
        )

    defaults = contract.get("provisional_defaults")
    if not isinstance(defaults, dict):
        errors.append("provisional_defaults must be an object")
    else:
        used = defaults.get("used")
        if not isinstance(used, bool):
            errors.append("provisional_defaults.used must be boolean")
        if used and not _nonblank_items(defaults.get("provenance")):
            errors.append(
                "provisional_defaults.provenance must contain nonblank evidence "
                "when provisional defaults are used"
            )
        if defaults.get("permitted_for_final_selection") is not False:
            errors.append(
                "provisional_defaults.permitted_for_final_selection must be false"
            )
        if level in {"research", "publication_release"} and used:
            errors.append(
                f"{level} cannot use provisional exploratory defaults as final evidence"
            )

    semantic = contract.get("semantic_review_policy")
    if not isinstance(semantic, dict):
        errors.append("semantic_review_policy must be an object")
    else:
        if semantic.get("algorithmic_metrics_role") != "triage_only":
            errors.append(
                "semantic_review_policy.algorithmic_metrics_role must be "
                "'triage_only'"
            )
        if semantic.get("original_text_required") is not True:
            errors.append(
                "semantic_review_policy.original_text_required must be true"
            )
        if level in {"research", "publication_release"}:
            if semantic.get("review_stage_winners") is not True:
                errors.append(
                    "research/publication requires semantic review of stage winners"
                )
            if semantic.get("review_all_finalists") is not True:
                errors.append(
                    "research/publication requires semantic review of all finalists"
                )

    cumulative = contract.get("cumulative_tuning_policy")
    if not isinstance(cumulative, dict):
        errors.append("cumulative_tuning_policy must be an object")
    else:
        required_true = (
            "one_parameter_family_per_main_stage",
            "carry_forward_champion",
            "rollback_rejected_change",
            "bounded_interaction_confirmation",
        )
        for field in required_true:
            if cumulative.get(field) is not True:
                errors.append(f"cumulative_tuning_policy.{field} must be true")

    return errors


def requires_explicit_preview_approval(contract: dict[str, Any]) -> bool:
    """Return whether modeling must wait for a separately approved preview."""

    try:
        level = resolve_assurance_level(contract)["assurance_level"]
    except ValueError:
        return True
    return level == "publication_release"
