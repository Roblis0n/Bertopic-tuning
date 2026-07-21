#!/usr/bin/env python3
"""Evaluate a lexicon-driven BERTopic representation refresh.

The evaluator refuses to compare a representation candidate when unit assignments or
topic identities changed. Structural candidates belong in the structural loop instead.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from evaluate_diversity import evaluate_topics
from lexicon_tools import normalize_term, validate_lexicon_manifest


def _topic_map(payload: dict[str, Any], side: str) -> dict[str, dict[str, Any]]:
    topics = payload.get("topics")
    if not isinstance(topics, list) or not topics:
        raise ValueError(f"{side} topic payload must contain a non-empty topics list")
    result: dict[str, dict[str, Any]] = {}
    for index, topic in enumerate(topics):
        if not isinstance(topic, dict):
            raise ValueError(f"{side} topic at index {index} must be an object")
        topic_id = str(topic.get("topic_uid") or topic.get("topic_id", "")).strip()
        if not topic_id:
            raise ValueError(f"{side} topic at index {index} lacks topic_id/topic_uid")
        if topic_id in result:
            raise ValueError(f"{side} topic identifiers must be unique: {topic_id}")
        result[topic_id] = topic
    return result


def _assignment_map(rows: list[dict[str, Any]], side: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for index, row in enumerate(rows):
        unit_id = str(row.get("unit_id", "")).strip()
        topic_id = str(row.get("topic_uid") or row.get("topic_id", "")).strip()
        if not unit_id or not topic_id:
            raise ValueError(
                f"{side} assignment row {index + 1} requires unit_id and topic_id/topic_uid"
            )
        if unit_id in result:
            raise ValueError(f"{side} assignments contain duplicate unit_id: {unit_id}")
        result[unit_id] = topic_id
    if not result:
        raise ValueError(f"{side} assignments must not be empty")
    return result


def _assignment_fingerprint(assignments: dict[str, str]) -> str:
    content = json.dumps(
        sorted(assignments.items()), ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _lexicon_sets(manifest: dict[str, Any]) -> tuple[dict[str, str], set[str], set[str]]:
    validate_lexicon_manifest(manifest)
    rules = manifest.get("normalization", {})
    aliases = {
        normalize_term(key, rules): normalize_term(value, rules)
        for key, value in dict(manifest.get("synonym_map", {})).items()
    }
    stopwords = {
        normalize_term(item["term"] if isinstance(item, dict) else item, rules)
        for item in manifest.get("stopwords", [])
    }
    raw_custom_terms = {
        normalize_term(item["term"] if isinstance(item, dict) else item, rules)
        for item in manifest.get("custom_terms", [])
    }
    custom_terms = {aliases.get(term, term) for term in raw_custom_terms}
    return aliases, stopwords, custom_terms


def _local_topic_map(topics: dict[str, dict[str, Any]]) -> dict[str, str]:
    local_ids: dict[str, str] = {}
    for topic_uid, topic in topics.items():
        value = topic.get("local_topic_id")
        if value in (None, "") and topic.get("topic_uid") not in (None, ""):
            value = topic.get("topic_id")
        if value not in (None, ""):
            local_ids[topic_uid] = str(value).strip()
    return local_ids


def _keywords(topic: dict[str, Any], *, top_k: int) -> list[str]:
    values = topic.get("keywords")
    if not isinstance(values, list):
        raise ValueError("Every topic must contain a keywords list")
    return [str(value).strip() for value in values[:top_k] if str(value).strip()]


def _concept_payload(
    payload: dict[str, Any],
    *,
    aliases: dict[str, str],
    stopwords: set[str],
    rules: dict[str, Any],
) -> dict[str, Any]:
    topics: list[dict[str, Any]] = []
    for topic in payload["topics"]:
        seen: set[str] = set()
        keywords: list[str] = []
        for value in topic.get("keywords", []):
            term = normalize_term(value, rules)
            term = aliases.get(term, term)
            if not term or term in stopwords or term in seen:
                continue
            seen.add(term)
            keywords.append(term)
        topics.append({**topic, "keywords": keywords})
    return {**payload, "topics": topics}


def _lexical_only_payload(payload: dict[str, Any]) -> dict[str, Any]:
    topics = []
    for topic in payload["topics"]:
        lexical_topic = dict(topic)
        lexical_topic.pop("embedding", None)
        topics.append(lexical_topic)
    return {**payload, "topics": topics}


def _keyword_diagnostics(
    topics: dict[str, dict[str, Any]],
    *,
    top_k: int,
    rules: dict[str, Any],
) -> tuple[list[str], dict[str, list[tuple[str, int]]]]:
    flattened: list[str] = []
    occurrences: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for topic_id, topic in topics.items():
        for rank, value in enumerate(_keywords(topic, top_k=top_k), start=1):
            term = normalize_term(value, rules)
            flattened.append(term)
            occurrences[term].append((topic_id, rank))
    return flattened, occurrences


def _candidate_rows(
    after_occurrences: dict[str, list[tuple[str, int]]],
    *,
    aliases: dict[str, str],
    custom_terms: set[str],
    after_terms: set[str],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for term, occurrences in sorted(after_occurrences.items()):
        topic_ids = sorted({topic_id for topic_id, _ in occurrences})
        if len(topic_ids) > 1:
            candidates.append(
                {
                    "candidate_type": "cross_topic_term",
                    "term": term,
                    "canonical_term": "",
                    "topic_count": len(topic_ids),
                    "topic_uids": topic_ids,
                    "best_rank": min(rank for _, rank in occurrences),
                    "evidence": "ranked keyword appears in multiple topics; review without automatic removal",
                    "status": "proposed",
                }
            )
    for variant, canonical in sorted(aliases.items()):
        if variant in after_terms:
            candidates.append(
                {
                    "candidate_type": "unresolved_synonym",
                    "term": variant,
                    "canonical_term": canonical,
                    "topic_count": len({topic for topic, _ in after_occurrences.get(variant, [])}),
                    "topic_uids": sorted(
                        {topic for topic, _ in after_occurrences.get(variant, [])}
                    ),
                    "best_rank": min(
                        (rank for _, rank in after_occurrences.get(variant, [])),
                        default=None,
                    ),
                    "evidence": "active synonym variant remains in the refreshed topic representation",
                    "status": "proposed",
                }
            )
    for term in sorted(custom_terms.difference(after_terms)):
        candidates.append(
            {
                "candidate_type": "missing_custom_term",
                "term": term,
                "canonical_term": "",
                "topic_count": 0,
                "topic_uids": [],
                "best_rank": None,
                "evidence": "active protected term is absent from refreshed top keywords; inspect corpus support",
                "status": "proposed",
            }
        )
    return candidates


def evaluate_representation_update(
    before_payload: dict[str, Any],
    after_payload: dict[str, Any],
    before_assignment_rows: list[dict[str, Any]],
    after_assignment_rows: list[dict[str, Any]],
    lexicon_manifest: dict[str, Any],
    *,
    top_k: int,
    rbo_p: float,
) -> dict[str, Any]:
    """Compare representation snapshots after proving structural invariants."""
    before_topics = _topic_map(before_payload, "Before")
    after_topics = _topic_map(after_payload, "After")
    if set(before_topics) != set(after_topics):
        raise ValueError("Representation refresh rejected because topic identifiers changed")
    before_local_topics = _local_topic_map(before_topics)
    after_local_topics = _local_topic_map(after_topics)
    if before_local_topics != after_local_topics:
        raise ValueError(
            "Representation refresh rejected because local topic identifiers changed"
        )

    before_assignments = _assignment_map(before_assignment_rows, "Before")
    after_assignments = _assignment_map(after_assignment_rows, "After")
    if before_assignments != after_assignments:
        changed_units = sorted(
            unit_id
            for unit_id in set(before_assignments).union(after_assignments)
            if before_assignments.get(unit_id) != after_assignments.get(unit_id)
        )
        raise ValueError(
            "Representation refresh rejected because assignments changed for units: "
            + ", ".join(changed_units[:20])
        )
    allowed_assignment_topics = set(before_topics).union(before_local_topics.values())
    missing_assignment_topics = sorted(
        set(before_assignments.values()).difference(allowed_assignment_topics, {"-1"})
    )
    if missing_assignment_topics:
        raise ValueError(
            "Representation refresh rejected because assignment topics are absent from the topic catalog: "
            + ", ".join(missing_assignment_topics[:20])
        )

    aliases, stopwords, custom_terms = _lexicon_sets(lexicon_manifest)
    rules = lexicon_manifest.get("normalization", {})
    before_terms, before_occurrences = _keyword_diagnostics(
        before_topics, top_k=top_k, rules=rules
    )
    after_terms, after_occurrences = _keyword_diagnostics(
        after_topics, top_k=top_k, rules=rules
    )
    after_term_set = set(after_terms)

    lexical_before = _lexical_only_payload(before_payload)
    lexical_after = _lexical_only_payload(after_payload)
    concept_before = _concept_payload(
        lexical_before, aliases=aliases, stopwords=stopwords, rules=rules
    )
    concept_after = _concept_payload(
        lexical_after, aliases=aliases, stopwords=stopwords, rules=rules
    )
    fingerprint = _assignment_fingerprint(before_assignments)
    topic_changes = []
    for topic_id in sorted(before_topics):
        before_keywords = _keywords(before_topics[topic_id], top_k=top_k)
        after_keywords = _keywords(after_topics[topic_id], top_k=top_k)
        topic_changes.append(
            {
                "topic_uid": topic_id,
                "before_keywords": before_keywords,
                "after_keywords": after_keywords,
                "added": [term for term in after_keywords if term not in before_keywords],
                "removed": [term for term in before_keywords if term not in after_keywords],
            }
        )

    return {
        "lexicon_bundle_id": lexicon_manifest.get("bundle_id", ""),
        "structural_invariants": {
            "assignments_unchanged": True,
            "topic_ids_unchanged": True,
            "local_topic_ids_unchanged": True,
            "assignment_fingerprint": fingerprint,
            "unit_count": len(before_assignments),
            "topic_count": len(before_topics),
        },
        "scorecards": {
            "structural_metrics_policy": "carry_forward_unchanged",
            "surface": {
                "before": evaluate_topics(lexical_before, top_k=top_k, rbo_p=rbo_p),
                "after": evaluate_topics(lexical_after, top_k=top_k, rbo_p=rbo_p),
            },
            "concept_normalized": {
                "before": evaluate_topics(concept_before, top_k=top_k, rbo_p=rbo_p),
                "after": evaluate_topics(concept_after, top_k=top_k, rbo_p=rbo_p),
            },
        },
        "lexicon_diagnostics": {
            "stopword_leakage_before": sum(term in stopwords for term in before_terms),
            "stopword_leakage_after": sum(term in stopwords for term in after_terms),
            "synonym_variants_before": sorted(set(before_terms).intersection(aliases)),
            "synonym_variants_after": sorted(after_term_set.intersection(aliases)),
            "custom_terms_recovered": sorted(custom_terms.intersection(after_term_set)),
            "custom_terms_missing": sorted(custom_terms.difference(after_term_set)),
        },
        "topic_keyword_changes": topic_changes,
        "lexicon_candidates": _candidate_rows(
            after_occurrences,
            aliases=aliases,
            custom_terms=custom_terms,
            after_terms=after_term_set,
        ),
        "decision_required": True,
    }


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _read_assignments(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_candidates(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "candidate_id",
        "candidate_type",
        "term",
        "canonical_term",
        "topic_count",
        "topic_uids",
        "best_rank",
        "evidence",
        "status",
        "decision_reason",
        "reviewer",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            writer.writerow(
                {
                    "candidate_id": f"lexicon-candidate-{index:04d}",
                    "candidate_type": row.get("candidate_type", ""),
                    "term": row.get("term", ""),
                    "canonical_term": row.get("canonical_term", ""),
                    "topic_count": row.get("topic_count", ""),
                    "topic_uids": "|".join(row.get("topic_uids", [])),
                    "best_rank": row.get("best_rank", ""),
                    "evidence": row.get("evidence", ""),
                    "status": row.get("status", "proposed"),
                    "decision_reason": "",
                    "reviewer": "",
                }
            )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare lexicon-driven BERTopic representations under frozen assignments."
    )
    parser.add_argument("--before-topics", required=True, type=Path)
    parser.add_argument("--after-topics", required=True, type=Path)
    parser.add_argument("--before-assignments", required=True, type=Path)
    parser.add_argument("--after-assignments", required=True, type=Path)
    parser.add_argument("--lexicon-manifest", required=True, type=Path)
    parser.add_argument("--top-k", required=True, type=int)
    parser.add_argument("--rbo-p", required=True, type=float)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--candidate-output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = evaluate_representation_update(
        _read_json(args.before_topics),
        _read_json(args.after_topics),
        _read_assignments(args.before_assignments),
        _read_assignments(args.after_assignments),
        _read_json(args.lexicon_manifest),
        top_k=args.top_k,
        rbo_p=args.rbo_p,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if args.candidate_output:
        _write_candidates(args.candidate_output, result["lexicon_candidates"])
    print(f"Wrote representation comparison: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
