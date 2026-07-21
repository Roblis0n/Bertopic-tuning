#!/usr/bin/env python3
"""Evaluate lexical and semantic topic diversity from a portable JSON bundle.

The script deliberately does not choose thresholds. Analytical choices must come
from the study contract or a validation-derived calibration procedure.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable


def _normalize_keyword(value: Any) -> str:
    return " ".join(str(value).strip().casefold().split())


def _cosine(left: Iterable[float], right: Iterable[float]) -> float:
    a = [float(value) for value in left]
    b = [float(value) for value in right]
    if len(a) != len(b) or not a:
        raise ValueError("Topic embeddings must be non-empty and have equal dimensions")
    denominator = math.sqrt(sum(value * value for value in a)) * math.sqrt(
        sum(value * value for value in b)
    )
    if denominator == 0:
        raise ValueError("Topic embeddings must not be zero vectors")
    return max(-1.0, min(1.0, sum(x * y for x, y in zip(a, b)) / denominator))


def _rbo(left: list[str], right: list[str], p: float, depth: int) -> float:
    """Return extrapolated rank-biased overlap at a finite depth."""
    if not 0 < p < 1:
        raise ValueError("rbo_p must be strictly between 0 and 1")
    if depth < 1:
        raise ValueError("top_k must be at least 1")

    seen_left: set[str] = set()
    seen_right: set[str] = set()
    weighted_agreement = 0.0
    agreement_at_depth = 0.0
    for rank in range(1, depth + 1):
        if rank <= len(left):
            seen_left.add(left[rank - 1])
        if rank <= len(right):
            seen_right.add(right[rank - 1])
        agreement_at_depth = len(seen_left.intersection(seen_right)) / rank
        weighted_agreement += agreement_at_depth * (p ** (rank - 1))
    return (1 - p) * weighted_agreement + agreement_at_depth * (p**depth)


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile of an empty list")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _effective_topic_count(topics: list[dict[str, Any]]) -> float | None:
    if not all("size" in topic and topic["size"] is not None for topic in topics):
        return None
    sizes = [float(topic["size"]) for topic in topics]
    if any(value < 0 for value in sizes) or sum(sizes) <= 0:
        raise ValueError("Topic sizes must be non-negative and have a positive sum")
    total = sum(sizes)
    entropy = -sum((value / total) * math.log(value / total) for value in sizes if value > 0)
    return math.exp(entropy)


def evaluate_topics(
    payload: dict[str, Any],
    *,
    top_k: int,
    rbo_p: float,
    semantic_redundancy_threshold: float | None = None,
) -> dict[str, Any]:
    """Compute a diversity scorecard without collapsing it into one scalar."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if not 0 < rbo_p < 1:
        raise ValueError("rbo_p must be strictly between 0 and 1")
    if semantic_redundancy_threshold is not None and not -1 <= semantic_redundancy_threshold <= 1:
        raise ValueError("semantic_redundancy_threshold must be within [-1, 1]")

    raw_topics = payload.get("topics")
    if not isinstance(raw_topics, list) or not raw_topics:
        raise ValueError("Input JSON must contain a non-empty 'topics' list")

    topics: list[dict[str, Any]] = []
    topic_ids: set[str] = set()
    warnings: list[str] = []
    for index, raw in enumerate(raw_topics):
        if not isinstance(raw, dict):
            raise ValueError(f"Topic at index {index} must be an object")
        topic_id = str(raw.get("topic_id", raw.get("topic_uid", ""))).strip()
        if not topic_id:
            raise ValueError(f"Topic at index {index} lacks topic_id/topic_uid")
        if topic_id in topic_ids:
            raise ValueError(f"Duplicate topic identifier: {topic_id}")
        topic_ids.add(topic_id)

        raw_keywords = raw.get("keywords")
        if not isinstance(raw_keywords, list):
            raise ValueError(f"Topic {topic_id} must contain a keywords list")
        keywords = [_normalize_keyword(value) for value in raw_keywords]
        keywords = [value for value in keywords if value]
        if len(keywords) < top_k:
            warnings.append(
                f"Topic {topic_id} provides {len(keywords)} keywords, fewer than requested top_k={top_k}"
            )
        topic = dict(raw)
        topic["topic_id"] = topic_id
        topic["keywords"] = keywords[:top_k]
        topics.append(topic)

    keyword_slots = len(topics) * top_k
    distinct_keywords = {
        keyword for topic in topics for keyword in topic["keywords"]
    }
    topic_diversity = len(distinct_keywords) / keyword_slots

    pairwise_irbo: list[dict[str, Any]] = []
    for left, right in combinations(topics, 2):
        rbo = _rbo(left["keywords"], right["keywords"], rbo_p, top_k)
        pairwise_irbo.append(
            {
                "topic_a": left["topic_id"],
                "topic_b": right["topic_id"],
                "rbo": rbo,
                "irbo": 1 - rbo,
            }
        )
    mean_pairwise_irbo = (
        statistics.fmean(row["irbo"] for row in pairwise_irbo)
        if pairwise_irbo
        else None
    )
    if not pairwise_irbo:
        warnings.append("At least two topics are required for inter-topic lexical diversity")

    have_all_embeddings = all(
        isinstance(topic.get("embedding"), list) and topic["embedding"]
        for topic in topics
    )
    pairwise_semantic: list[dict[str, Any]] = []
    semantic_diversity_median: float | None = None
    semantic_redundancy_fraction: float | None = None
    nearest_summary: dict[str, float] | None = None
    if have_all_embeddings and len(topics) >= 2:
        dimensions = {len(topic["embedding"]) for topic in topics}
        if len(dimensions) != 1:
            raise ValueError("All topic embeddings must have the same dimension")
        for left, right in combinations(topics, 2):
            similarity = _cosine(left["embedding"], right["embedding"])
            pairwise_semantic.append(
                {
                    "topic_a": left["topic_id"],
                    "topic_b": right["topic_id"],
                    "cosine_similarity": similarity,
                }
            )

        nearest_values: list[float] = []
        for topic in topics:
            similarities = [
                row["cosine_similarity"]
                for row in pairwise_semantic
                if topic["topic_id"] in (row["topic_a"], row["topic_b"])
            ]
            nearest_values.append(max(similarities))
        median_nearest = statistics.median(nearest_values)
        semantic_diversity_median = 1 - median_nearest
        nearest_summary = {
            "median": median_nearest,
            "p90": _percentile(nearest_values, 0.9),
            "maximum": max(nearest_values),
        }
        if semantic_redundancy_threshold is not None:
            semantic_redundancy_fraction = sum(
                row["cosine_similarity"] >= semantic_redundancy_threshold
                for row in pairwise_semantic
            ) / len(pairwise_semantic)
    else:
        warnings.append(
            "Semantic diversity was not scored because every topic needs a compatible embedding and at least two topics"
        )

    pairwise_irbo.sort(key=lambda row: row["rbo"], reverse=True)
    pairwise_semantic.sort(key=lambda row: row["cosine_similarity"], reverse=True)

    return {
        "topic_count": len(topics),
        "top_k": top_k,
        "rbo_p": rbo_p,
        "topic_diversity": topic_diversity,
        "mean_pairwise_irbo": mean_pairwise_irbo,
        "semantic_diversity_median": semantic_diversity_median,
        "nearest_topic_similarity": nearest_summary,
        "semantic_redundancy_threshold": semantic_redundancy_threshold,
        "semantic_redundancy_fraction": semantic_redundancy_fraction,
        "effective_topic_count": _effective_topic_count(topics),
        "most_lexically_overlapping_pairs": pairwise_irbo[:20],
        "most_semantically_similar_pairs": pairwise_semantic[:20],
        "warnings": warnings,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a BERTopic topic catalog without selecting a model for you."
    )
    parser.add_argument("--input", required=True, type=Path, help="Topic JSON input")
    parser.add_argument("--output", required=True, type=Path, help="Scorecard JSON output")
    parser.add_argument("--top-k", required=True, type=int, help="Pre-registered keyword depth")
    parser.add_argument(
        "--rbo-p",
        required=True,
        type=float,
        help="Pre-registered rank-bias persistence in (0, 1)",
    )
    parser.add_argument(
        "--semantic-redundancy-threshold",
        type=float,
        help="Optional validation-derived cosine threshold; no default is assumed",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = evaluate_topics(
        payload,
        top_k=args.top_k,
        rbo_p=args.rbo_p,
        semantic_redundancy_threshold=args.semantic_redundancy_threshold,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote diversity scorecard: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
