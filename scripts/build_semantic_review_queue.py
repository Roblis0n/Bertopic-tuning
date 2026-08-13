#!/usr/bin/env python3
"""Build an original-text review queue from BERTopic diagnostics.

This module deliberately stops before substantive judgment. Similarity,
overlap, confidence, and outlier signals determine reading order only.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RELATIONSHIPS: tuple[str, ...] = (
    "distinct",
    "overlapping",
    "parent_child",
    "merge_candidate",
    "split_signal",
    "artifact",
    "uncertain",
)

BOUNDARY_CLARITY = {"clear", "mixed", "uncertain"}
ARTIFACT_STATUS = {"substantive", "artifact", "uncertain"}
EVIDENCE_ID_FIELDS = (
    "representative_unit_ids",
    "random_unit_ids",
    "boundary_unit_ids",
    "source_diverse_unit_ids",
    "parent_diverse_unit_ids",
    "nearest_pair_unit_ids",
    "evidence_unit_ids",
)
DEPENDENCE_FIELDS = (
    "duplicate_group_id",
    "source_id",
    "account_id",
    "thread_id",
    "time_group",
)


def _nonblank(value: Any) -> bool:
    return value is not None and bool(str(value).strip())


def _unit_record(row: dict[str, Any]) -> dict[str, Any]:
    unit_id = str(row.get("unit_id", "")).strip()
    if not unit_id:
        raise ValueError("Every evidence unit must have a nonblank unit_id")
    display_text = row.get("display_text")
    if not _nonblank(display_text):
        display_text = row.get("original_text")
    if not _nonblank(display_text):
        raise ValueError(f"Evidence unit {unit_id} lacks display_text/original_text")

    keep_fields = (
        "unit_id",
        "source_id",
        "parent_document_id",
        "duplicate_group_id",
        "account_id",
        "thread_id",
        "time_group",
        "start_offset",
        "end_offset",
        "artifact_path",
        "record_locator",
        "route",
        "route_subset",
    )
    record = {
        field: row[field]
        for field in keep_fields
        if field in row and _nonblank(row[field])
    }
    record["unit_id"] = unit_id
    record["display_text"] = str(display_text)
    return record


def _topic_id(topic: dict[str, Any]) -> str:
    value = topic.get("topic_uid", topic.get("topic_id", ""))
    return str(value).strip()


def _topic_evidence_ids(
    topic: dict[str, Any],
    assigned_ids: list[str],
) -> list[str]:
    evidence_ids: list[str] = []
    for field in EVIDENCE_ID_FIELDS:
        values = topic.get(field, [])
        if values is None:
            continue
        if not isinstance(values, list):
            raise ValueError(f"{field} for topic {_topic_id(topic)} must be a list")
        evidence_ids.extend(str(value).strip() for value in values if _nonblank(value))

    # A portable topic export may mark already selected evidence in assignments.
    # It is used only when the topic record did not provide an explicit queue.
    if not evidence_ids:
        evidence_ids.extend(assigned_ids)
    return list(dict.fromkeys(evidence_ids))


def _signal_pairs(scorecard: dict[str, Any]) -> list[dict[str, Any]]:
    signals: dict[tuple[str, str], dict[str, Any]] = {}
    mappings = (
        ("most_semantically_similar_pairs", "semantic_similarity"),
        ("most_lexically_overlapping_pairs", "lexical_overlap"),
        ("review_trigger_pairs", "registered_review_trigger"),
    )
    for field, signal_type in mappings:
        rows = scorecard.get(field, [])
        if rows is None:
            continue
        if not isinstance(rows, list):
            raise ValueError(f"{field} must be a list")
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError(f"{field} entries must be objects")
            left = str(
                row.get("topic_uid_a", row.get("topic_a", ""))
            ).strip()
            right = str(
                row.get("topic_uid_b", row.get("topic_b", ""))
            ).strip()
            if not left or not right or left == right:
                continue
            key = tuple(sorted((left, right)))
            pair = signals.setdefault(
                key,
                {
                    "topic_uid_a": key[0],
                    "topic_uid_b": key[1],
                    "algorithmic_signal_role": "review_trigger_only",
                    "algorithmic_signals": [],
                },
            )
            signal = {
                "signal_type": signal_type,
                "source_field": field,
            }
            for metric in (
                "cosine_similarity",
                "rbo",
                "lexical_overlap",
                "distance",
                "confidence",
            ):
                if metric in row:
                    signal[metric] = row[metric]
            pair["algorithmic_signals"].append(signal)
    return list(signals.values())


def build_review_queue(
    topic_payload: dict[str, Any],
    unit_rows: list[dict[str, Any]],
    assignment_rows: list[dict[str, Any]],
    diversity_scorecard: dict[str, Any],
    *,
    candidate_id: str,
    route: str,
) -> dict[str, Any]:
    """Create evidence cards and pair queues without emitting a semantic verdict."""

    if route not in {"network-short", "long-document", "mixed"}:
        raise ValueError("route must be network-short, long-document, or mixed")
    if not _nonblank(candidate_id):
        raise ValueError("candidate_id must not be blank")
    topics = topic_payload.get("topics")
    if not isinstance(topics, list) or not topics:
        raise ValueError("topic_payload must contain a non-empty topics list")

    units: dict[str, dict[str, Any]] = {}
    for row in unit_rows:
        record = _unit_record(row)
        if record["unit_id"] in units:
            raise ValueError(f"Duplicate evidence unit_id: {record['unit_id']}")
        units[record["unit_id"]] = record

    assigned_by_topic: dict[str, list[str]] = {}
    for row in assignment_rows:
        unit_id = str(row.get("unit_id", "")).strip()
        topic_uid = str(row.get("topic_uid", row.get("topic_id", ""))).strip()
        if not unit_id or not topic_uid:
            raise ValueError("Assignment rows require unit_id and topic_uid/topic_id")
        if unit_id not in units:
            raise ValueError(f"Assignment references missing evidence unit {unit_id}")
        assigned_by_topic.setdefault(topic_uid, []).append(unit_id)

    topic_reviews: list[dict[str, Any]] = []
    evidence_by_topic: dict[str, list[dict[str, Any]]] = {}
    seen_topics: set[str] = set()
    for topic in topics:
        if not isinstance(topic, dict):
            raise ValueError("Each topic must be an object")
        topic_uid = _topic_id(topic)
        if not topic_uid:
            raise ValueError("Every topic requires topic_uid or topic_id")
        if topic_uid in seen_topics:
            raise ValueError(f"Duplicate topic identifier: {topic_uid}")
        seen_topics.add(topic_uid)
        evidence_ids = _topic_evidence_ids(
            topic, assigned_by_topic.get(topic_uid, [])
        )
        missing = [unit_id for unit_id in evidence_ids if unit_id not in units]
        if missing:
            raise ValueError(
                f"Topic {topic_uid} references missing evidence unit(s): "
                + ", ".join(missing)
            )
        evidence = [units[unit_id] for unit_id in evidence_ids]
        evidence_by_topic[topic_uid] = evidence
        topic_reviews.append(
            {
                "topic_uid": topic_uid,
                "algorithmic_signal_role": "review_trigger_only",
                "evidence_units": evidence,
                "review_prompts": [
                    "What object is this topic about?",
                    "What claim, action, or function connects the evidence?",
                    "What context and perspective delimit the topic?",
                    "Which original texts contradict the proposed boundary?",
                ],
            }
        )

    pair_reviews: list[dict[str, Any]] = []
    for pair in _signal_pairs(diversity_scorecard):
        left = pair["topic_uid_a"]
        right = pair["topic_uid_b"]
        if left not in evidence_by_topic or right not in evidence_by_topic:
            raise ValueError(
                f"Algorithmic pair references unknown topic(s): {left}, {right}"
            )
        evidence: list[dict[str, Any]] = []
        used: set[str] = set()
        for record in evidence_by_topic[left] + evidence_by_topic[right]:
            if record["unit_id"] not in used:
                used.add(record["unit_id"])
                evidence.append(record)
        pair["evidence_units"] = evidence
        pair["review_prompts"] = [
            "Do the topics concern the same substantive object?",
            "Are their functions, stages, contexts, or perspectives different?",
            "Write the inclusion and exclusion boundary before choosing a relationship.",
        ]
        pair_reviews.append(pair)

    outlier_ids = [
        str(value).strip()
        for value in topic_payload.get("outlier_unit_ids", [])
        if _nonblank(value)
    ]
    missing_outliers = [unit_id for unit_id in outlier_ids if unit_id not in units]
    if missing_outliers:
        raise ValueError(
            "Outlier review references missing evidence unit(s): "
            + ", ".join(missing_outliers)
        )

    queue = {
        "schema_version": 1,
        "candidate_id": str(candidate_id).strip(),
        "route": route,
        "decision_role": "original_text_review_queue_only",
        "algorithmic_metrics_role": "diagnostic_triage_only",
        "semantic_verdict_produced": False,
        "topic_reviews": topic_reviews,
        "pair_reviews": pair_reviews,
        "coverage_reviews": [
            {
                "review_type": "topic_minus_one_missing_theme",
                "algorithmic_signal_role": "review_trigger_only",
                "evidence_units": [units[unit_id] for unit_id in outlier_ids],
            }
        ]
        if outlier_ids
        else [],
    }
    route_errors = validate_route_evidence(queue, route=route)
    if route_errors:
        queue["route_evidence_warnings"] = route_errors
    return queue


def validate_semantic_review(
    review: dict[str, Any],
    *,
    required_topic_uids: set[str],
    required_pair_ids: set[tuple[str, str]],
) -> list[str]:
    """Validate recorded human/Codex judgments against required review scope."""

    errors: list[str] = []
    cards = review.get("topic_cards")
    if not isinstance(cards, list):
        return ["semantic review topic_cards must be a list"]
    if not cards:
        errors.append("semantic review requires at least one topic card")

    cards_by_id: dict[str, dict[str, Any]] = {}
    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            errors.append(f"topic_cards[{index}] must be an object")
            continue
        topic_uid = str(card.get("topic_uid", "")).strip()
        if not topic_uid:
            errors.append(f"topic_cards[{index}] lacks topic_uid")
            continue
        if topic_uid in cards_by_id:
            errors.append(f"Duplicate topic card: {topic_uid}")
            continue
        cards_by_id[topic_uid] = card
        evidence_ids = card.get("evidence_unit_ids")
        if (
            not isinstance(evidence_ids, list)
            or not evidence_ids
            or not all(_nonblank(value) for value in evidence_ids)
        ):
            errors.append(f"Topic card {topic_uid} requires evidence_unit_ids")
        meaning = card.get("meaning")
        if not isinstance(meaning, dict):
            errors.append(f"Topic card {topic_uid} meaning must be an object")
        else:
            for field in (
                "object",
                "claim_action_or_function",
                "context",
                "stance_or_perspective",
            ):
                if not _nonblank(meaning.get(field)):
                    errors.append(f"Topic card {topic_uid} meaning.{field} is blank")
        for field in ("label", "definition"):
            if not _nonblank(card.get(field)):
                errors.append(f"Topic card {topic_uid} {field} is blank")
        for field in ("inclusion_rules", "exclusion_rules"):
            values = card.get(field)
            if (
                not isinstance(values, list)
                or not values
                or not all(_nonblank(value) for value in values)
            ):
                errors.append(
                    f"Topic card {topic_uid} {field} must be a non-empty list"
                )
        if card.get("boundary_clarity") not in BOUNDARY_CLARITY:
            errors.append(
                f"Topic card {topic_uid} has invalid boundary_clarity"
            )
        if card.get("artifact_status") not in ARTIFACT_STATUS:
            errors.append(f"Topic card {topic_uid} has invalid artifact_status")

    for topic_uid in sorted(required_topic_uids.difference(cards_by_id)):
        errors.append(f"Missing required topic card: {topic_uid}")

    decisions = review.get("pair_decisions")
    if not isinstance(decisions, list):
        errors.append("semantic review pair_decisions must be a list")
        decisions = []
    found_pairs: set[tuple[str, str]] = set()
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            errors.append(f"pair_decisions[{index}] must be an object")
            continue
        left = str(decision.get("topic_uid_a", "")).strip()
        right = str(decision.get("topic_uid_b", "")).strip()
        if not left or not right or left == right:
            errors.append(f"pair_decisions[{index}] has invalid topic pair")
            continue
        pair_id = tuple(sorted((left, right)))
        if pair_id in found_pairs:
            errors.append(f"Duplicate pair decision: {pair_id[0]} / {pair_id[1]}")
        found_pairs.add(pair_id)
        if decision.get("relationship") not in RELATIONSHIPS:
            errors.append(
                f"Pair {pair_id[0]} / {pair_id[1]} has invalid relationship"
            )
        for field in (
            "evidence_unit_ids",
            "meaning_difference",
            "decision_reason",
        ):
            value = decision.get(field)
            if field == "evidence_unit_ids":
                valid = (
                    isinstance(value, list)
                    and bool(value)
                    and all(_nonblank(item) for item in value)
                )
            else:
                valid = _nonblank(value)
            if not valid:
                errors.append(
                    f"Pair {pair_id[0]} / {pair_id[1]} lacks {field}"
                )
        if not isinstance(decision.get("unresolved"), bool):
            errors.append(
                f"Pair {pair_id[0]} / {pair_id[1]} unresolved must be boolean"
            )

    normalized_required = {
        tuple(sorted((str(left), str(right))))
        for left, right in required_pair_ids
    }
    for left, right in sorted(normalized_required.difference(found_pairs)):
        errors.append(f"Missing required pair decision: {left} / {right}")
    if not isinstance(review.get("unresolved_issues", []), list):
        errors.append("semantic review unresolved_issues must be a list")
    return errors


def validate_route_evidence(
    queue: dict[str, Any],
    *,
    route: str,
) -> list[str]:
    """Check traceability and dependence diversity without making a verdict."""

    if route not in {"network-short", "long-document", "mixed"}:
        return ["route must be network-short, long-document, or mixed"]
    warnings: list[str] = []
    reviews = queue.get("topic_reviews", [])
    if not isinstance(reviews, list):
        return ["topic_reviews must be a list"]

    if route == "mixed":
        mixed_subsets = {
            str(
                row.get("route", row.get("route_subset", ""))
            ).strip()
            for review in reviews
            if isinstance(review, dict)
            for row in review.get("evidence_units", [])
            if isinstance(row, dict)
        }
        expected_subsets = {"network-short", "long-document"}
        if not expected_subsets.issubset(mixed_subsets):
            warnings.append(
                "Mixed-route semantic evidence must contain both route subsets: "
                "network-short and long-document"
            )

    for review in reviews:
        if not isinstance(review, dict):
            warnings.append("topic_reviews entries must be objects")
            continue
        topic_uid = str(review.get("topic_uid", "")).strip() or "<unknown>"
        evidence = review.get("evidence_units", [])
        if not isinstance(evidence, list):
            warnings.append(f"Topic {topic_uid} evidence_units must be a list")
            continue
        short_evidence = (
            evidence
            if route == "network-short"
            else [
                row
                for row in evidence
                if str(
                    row.get("route", row.get("route_subset", ""))
                ).strip()
                == "network-short"
            ]
        )
        long_evidence = (
            evidence
            if route == "long-document"
            else [
                row
                for row in evidence
                if str(
                    row.get("route", row.get("route_subset", ""))
                ).strip()
                == "long-document"
            ]
        )

        if route in {"network-short", "mixed"} and len(short_evidence) > 1:
            available_fields = [
                field
                for field in DEPENDENCE_FIELDS
                if any(_nonblank(row.get(field)) for row in short_evidence)
            ]
            if available_fields and all(
                len(
                    {
                        str(row.get(field, "")).strip()
                        for row in short_evidence
                        if _nonblank(row.get(field))
                    }
                )
                <= 1
                for field in available_fields
            ):
                warnings.append(
                    f"Topic {topic_uid} evidence comes from one registered "
                    "short-text dependence group"
                )

        if route in {"long-document", "mixed"}:
            missing_parent = [
                str(row.get("unit_id", "<unknown>"))
                for row in long_evidence
                if not _nonblank(row.get("parent_document_id"))
            ]
            if missing_parent:
                warnings.append(
                    f"Topic {topic_uid} evidence lacks parent_document_id for: "
                    + ", ".join(missing_parent)
                )
            if review.get("claims_cross_document_support") is True:
                parent_ids = {
                    str(row.get("parent_document_id", "")).strip()
                    for row in long_evidence
                    if _nonblank(row.get("parent_document_id"))
                }
                if len(parent_ids) < 2:
                    warnings.append(
                        f"Topic {topic_uid} claims cross-document support but "
                        "evidence does not span independent parent documents"
                    )
    return warnings


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an original-text semantic review queue without a verdict"
    )
    parser.add_argument("--topics", required=True, type=Path)
    parser.add_argument("--units", required=True, type=Path)
    parser.add_argument("--assignments", required=True, type=Path)
    parser.add_argument("--scorecard", required=True, type=Path)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument(
        "--route",
        required=True,
        choices=("network-short", "long-document", "mixed"),
    )
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    queue = build_review_queue(
        json.loads(args.topics.read_text(encoding="utf-8-sig")),
        _read_csv(args.units),
        _read_csv(args.assignments),
        json.loads(args.scorecard.read_text(encoding="utf-8-sig")),
        candidate_id=args.candidate_id,
        route=args.route,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(queue, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote semantic review queue: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
