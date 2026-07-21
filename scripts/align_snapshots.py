#!/usr/bin/env python3
"""Align BERTopic snapshots and flag continuity, split, and merge candidates.

Alignment thresholds are mandatory inputs. The script does not embed universal
similarity cutoffs or arbitrary weighted composites.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluate_diversity import _cosine, _normalize_keyword, _rbo
from lexicon_tools import validate_lexicon_manifest


def _hungarian_maximize(scores: list[list[float]]) -> list[tuple[int, int]]:
    """Return a maximum-weight one-to-one assignment for a rectangular matrix."""
    if not scores or not scores[0]:
        return []
    if any(len(row) != len(scores[0]) for row in scores):
        raise ValueError("Assignment matrix must be rectangular")

    transposed = len(scores) > len(scores[0])
    working = [list(row) for row in scores]
    if transposed:
        working = [list(row) for row in zip(*working)]

    row_count = len(working)
    column_count = len(working[0])
    cost = [[1.0 - value for value in row] for row in working]
    u = [0.0] * (row_count + 1)
    v = [0.0] * (column_count + 1)
    p = [0] * (column_count + 1)
    way = [0] * (column_count + 1)

    for i in range(1, row_count + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (column_count + 1)
        used = [False] * (column_count + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, column_count + 1):
                if used[j]:
                    continue
                current = cost[i0 - 1][j - 1] - u[i0] - v[j]
                if current < minv[j]:
                    minv[j] = current
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(column_count + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    assignment = [(p[j] - 1, j - 1) for j in range(1, column_count + 1) if p[j]]
    if transposed:
        assignment = [(column, row) for row, column in assignment]
    return assignment


def _topic_id(topic: dict[str, Any], index: int, side: str) -> str:
    value = str(topic.get("topic_uid", topic.get("topic_id", ""))).strip()
    if not value:
        raise ValueError(f"{side} topic at index {index} lacks topic_uid/topic_id")
    return value


def _keyword_rbo(
    old_topic: dict[str, Any],
    new_topic: dict[str, Any],
    *,
    p: float,
    aliases: dict[str, str] | None = None,
    excluded: set[str] | None = None,
) -> float | None:
    normalized_aliases = {
        _normalize_keyword(key): _normalize_keyword(value)
        for key, value in (aliases or {}).items()
    }
    normalized_excluded = {_normalize_keyword(value) for value in (excluded or set())}

    def normalize(values: list[Any]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for value in values:
            term = _normalize_keyword(value)
            term = normalized_aliases.get(term, term)
            if not term or term in normalized_excluded or term in seen:
                continue
            seen.add(term)
            result.append(term)
        return result

    old_keywords = normalize(old_topic.get("keywords", []))
    new_keywords = normalize(new_topic.get("keywords", []))
    if not old_keywords or not new_keywords:
        return None
    depth = max(len(old_keywords), len(new_keywords))
    return _rbo(old_keywords, new_keywords, p, depth)


def _document_jaccard(old_topic: dict[str, Any], new_topic: dict[str, Any]) -> float | None:
    old_values = old_topic.get("anchor_unit_ids", old_topic.get("representative_unit_ids"))
    new_values = new_topic.get("anchor_unit_ids", new_topic.get("representative_unit_ids"))
    if not isinstance(old_values, list) or not isinstance(new_values, list):
        return None
    old_set = {str(value) for value in old_values}
    new_set = {str(value) for value in new_values}
    union = old_set.union(new_set)
    if not union:
        return None
    return len(old_set.intersection(new_set)) / len(union)


def _qualifies(evidence: dict[str, Any], thresholds: dict[str, float]) -> bool:
    field_map = {
        "semantic": "semantic_similarity",
        "keyword": "keyword_rbo",
        "document": "document_jaccard",
    }
    return all(
        evidence.get(field_map[name]) is not None
        and evidence[field_map[name]] >= threshold
        for name, threshold in thresholds.items()
    )


def align_snapshots(
    old_topics: list[dict[str, Any]],
    new_topics: list[dict[str, Any]],
    *,
    thresholds: dict[str, float],
    keyword_rbo_p: float | None = None,
    keyword_aliases: dict[str, str] | None = None,
    excluded_keywords: set[str] | None = None,
) -> dict[str, Any]:
    """Align two topic catalogs using explicit, validation-derived evidence gates."""
    if not old_topics or not new_topics:
        raise ValueError("Both old_topics and new_topics must be non-empty")
    if "semantic" not in thresholds:
        raise ValueError("thresholds must include a validation-derived 'semantic' cutoff")
    unknown = set(thresholds).difference({"semantic", "keyword", "document"})
    if unknown:
        raise ValueError(f"Unknown threshold types: {sorted(unknown)}")
    if not -1 <= float(thresholds["semantic"]) <= 1:
        raise ValueError("semantic threshold must lie within [-1, 1]")
    for name in ("keyword", "document"):
        if name in thresholds and not 0 <= float(thresholds[name]) <= 1:
            raise ValueError(f"{name} threshold must lie within [0, 1]")
    if "keyword" in thresholds and keyword_rbo_p is None:
        raise ValueError("keyword_rbo_p is required when a keyword threshold is used")
    if keyword_rbo_p is not None and not 0 < keyword_rbo_p < 1:
        raise ValueError("keyword_rbo_p must be strictly between 0 and 1")

    old_ids = [_topic_id(topic, index, "Old") for index, topic in enumerate(old_topics)]
    new_ids = [_topic_id(topic, index, "New") for index, topic in enumerate(new_topics)]
    if len(set(old_ids)) != len(old_ids):
        raise ValueError("Old topic identifiers must be unique")
    if len(set(new_ids)) != len(new_ids):
        raise ValueError("New topic identifiers must be unique")

    semantic_matrix: list[list[float]] = []
    evidence_rows: list[dict[str, Any]] = []
    evidence_by_pair: dict[tuple[int, int], dict[str, Any]] = {}
    warnings: set[str] = set()
    for old_index, old_topic in enumerate(old_topics):
        semantic_row: list[float] = []
        if not isinstance(old_topic.get("embedding"), list):
            raise ValueError(f"Old topic {old_ids[old_index]} lacks an embedding")
        for new_index, new_topic in enumerate(new_topics):
            if not isinstance(new_topic.get("embedding"), list):
                raise ValueError(f"New topic {new_ids[new_index]} lacks an embedding")
            semantic = _cosine(old_topic["embedding"], new_topic["embedding"])
            semantic_row.append(semantic)
            keyword_surface = (
                _keyword_rbo(old_topic, new_topic, p=float(keyword_rbo_p))
                if keyword_rbo_p is not None
                else None
            )
            keyword_canonical = (
                _keyword_rbo(
                    old_topic,
                    new_topic,
                    p=float(keyword_rbo_p),
                    aliases=keyword_aliases,
                    excluded=excluded_keywords,
                )
                if keyword_rbo_p is not None
                else None
            )
            keyword = (
                keyword_canonical
                if keyword_aliases or excluded_keywords
                else keyword_surface
            )
            document = _document_jaccard(old_topic, new_topic)
            evidence = {
                "old_topic_uid": old_ids[old_index],
                "new_topic_uid": new_ids[new_index],
                "semantic_similarity": semantic,
                "keyword_rbo": keyword,
                "keyword_rbo_surface": keyword_surface,
                "keyword_rbo_canonical": keyword_canonical,
                "document_jaccard": document,
            }
            evidence["qualifies"] = _qualifies(evidence, thresholds)
            if "keyword" in thresholds and keyword is None:
                warnings.add("Some topic pairs lack keyword lists required by the keyword gate")
            if "document" in thresholds and document is None:
                warnings.add("Some topic pairs lack anchor unit IDs required by the document gate")
            evidence_rows.append(evidence)
            evidence_by_pair[(old_index, new_index)] = evidence
        semantic_matrix.append(semantic_row)

    qualifying_edges = {
        pair for pair, evidence in evidence_by_pair.items() if evidence["qualifies"]
    }
    old_neighbors: dict[int, list[int]] = {index: [] for index in range(len(old_topics))}
    new_neighbors: dict[int, list[int]] = {index: [] for index in range(len(new_topics))}
    for old_index, new_index in qualifying_edges:
        old_neighbors[old_index].append(new_index)
        new_neighbors[new_index].append(old_index)

    assignment = _hungarian_maximize(semantic_matrix)
    provisional_matches = [
        evidence_by_pair[pair] for pair in assignment if pair in qualifying_edges
    ]
    continuity = [
        evidence_by_pair[(old_index, new_index)]
        for old_index, new_index in assignment
        if (old_index, new_index) in qualifying_edges
        and len(old_neighbors[old_index]) == 1
        and len(new_neighbors[new_index]) == 1
    ]

    split_candidates = [
        {
            "old_topic_uid": old_ids[old_index],
            "new_topic_uids": [new_ids[index] for index in sorted(neighbors)],
            "evidence": [evidence_by_pair[(old_index, index)] for index in sorted(neighbors)],
        }
        for old_index, neighbors in old_neighbors.items()
        if len(neighbors) >= 2
    ]
    merge_candidates = [
        {
            "old_topic_uids": [old_ids[index] for index in sorted(neighbors)],
            "new_topic_uid": new_ids[new_index],
            "evidence": [evidence_by_pair[(index, new_index)] for index in sorted(neighbors)],
        }
        for new_index, neighbors in new_neighbors.items()
        if len(neighbors) >= 2
    ]

    evidence_rows.sort(
        key=lambda row: (row["qualifies"], row["semantic_similarity"]), reverse=True
    )
    return {
        "thresholds": {name: float(value) for name, value in thresholds.items()},
        "keyword_rbo_p": keyword_rbo_p,
        "keyword_normalization_applied": bool(keyword_aliases or excluded_keywords),
        "continuity": continuity,
        "provisional_one_to_one_matches": provisional_matches,
        "split_candidates": split_candidates,
        "merge_candidates": merge_candidates,
        "new_topics": [
            new_ids[index] for index, neighbors in new_neighbors.items() if not neighbors
        ],
        "retired_topics": [
            old_ids[index] for index, neighbors in old_neighbors.items() if not neighbors
        ],
        "pair_evidence": evidence_rows,
        "warnings": sorted(warnings),
        "human_review_required": bool(split_candidates or merge_candidates),
    }


def _load_topics(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    topics = payload.get("topics") if isinstance(payload, dict) else payload
    if not isinstance(topics, list):
        raise ValueError(f"{path} must contain a topic list or an object with 'topics'")
    return topics


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Align two BERTopic topic snapshots")
    parser.add_argument("--old", required=True, type=Path, help="Old topic JSON")
    parser.add_argument("--new", required=True, type=Path, help="New topic JSON")
    parser.add_argument(
        "--thresholds",
        required=True,
        type=Path,
        help="JSON object with validation-derived semantic/keyword/document cutoffs",
    )
    parser.add_argument(
        "--keyword-rbo-p",
        type=float,
        help="Required only when the threshold file includes a keyword gate",
    )
    parser.add_argument(
        "--lexicon-manifest",
        type=Path,
        help="Optional compiled lexicon manifest for canonical keyword evidence",
    )
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
    if not isinstance(thresholds, dict):
        raise ValueError("Threshold file must contain a JSON object")
    keyword_aliases: dict[str, str] | None = None
    excluded_keywords: set[str] | None = None
    if args.lexicon_manifest:
        manifest = json.loads(args.lexicon_manifest.read_text(encoding="utf-8-sig"))
        validate_lexicon_manifest(manifest)
        keyword_aliases = dict(manifest.get("synonym_map", {}))
        excluded_keywords = {
            str(item.get("term", "") if isinstance(item, dict) else item)
            for item in manifest.get("stopwords", [])
        }
    result = align_snapshots(
        _load_topics(args.old),
        _load_topics(args.new),
        thresholds=thresholds,
        keyword_rbo_p=args.keyword_rbo_p,
        keyword_aliases=keyword_aliases,
        excluded_keywords=excluded_keywords,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote snapshot alignment: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
