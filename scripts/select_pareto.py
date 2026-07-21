#!/usr/bin/env python3
"""Select a Pareto frontier from BERTopic candidate metrics.

No objective, constraint, or weight is implicit. The study contract must supply
all of them so outlier fraction, topic count, or coherence cannot silently take
over the selection decision.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path
from typing import Any


CONSTRAINT_PATTERN = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*(<=|>=|==|<|>)\s*"
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*$"
)


def _number(row: dict[str, Any], field: str, candidate_id: str) -> float:
    if field not in row or row[field] in (None, ""):
        raise ValueError(f"Candidate {candidate_id} lacks numeric field '{field}'")
    try:
        value = float(row[field])
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Candidate {candidate_id} has a non-numeric value for '{field}': {row[field]!r}"
        ) from exc
    if not math.isfinite(value):
        raise ValueError(f"Candidate {candidate_id} has a non-finite value for '{field}'")
    return value


def _parse_constraint(specification: str) -> tuple[str, str, float]:
    match = CONSTRAINT_PATTERN.match(specification)
    if not match:
        raise ValueError(
            f"Invalid constraint {specification!r}; expected forms such as coherence>=0.4"
        )
    field, operator, threshold = match.groups()
    return field, operator, float(threshold)


def _passes(value: float, operator: str, threshold: float) -> bool:
    return {
        ">=": value >= threshold,
        "<=": value <= threshold,
        ">": value > threshold,
        "<": value < threshold,
        "==": value == threshold,
    }[operator]


def _dominates(
    left: dict[str, float], right: dict[str, float], objectives: dict[str, str]
) -> bool:
    no_worse = True
    strictly_better = False
    for field, direction in objectives.items():
        if direction == "max":
            no_worse = no_worse and left[field] >= right[field]
            strictly_better = strictly_better or left[field] > right[field]
        else:
            no_worse = no_worse and left[field] <= right[field]
            strictly_better = strictly_better or left[field] < right[field]
    return no_worse and strictly_better


def select_pareto(
    rows: list[dict[str, Any]],
    *,
    objectives: dict[str, str],
    constraints: list[str] | None = None,
    id_field: str = "candidate_id",
) -> dict[str, Any]:
    """Filter candidates by explicit floors/ceilings, then find non-dominated rows."""
    if not rows:
        raise ValueError("At least one candidate row is required")
    if not objectives:
        raise ValueError("At least one explicit Pareto objective is required")
    invalid_directions = {
        field: direction
        for field, direction in objectives.items()
        if direction not in {"max", "min"}
    }
    if invalid_directions:
        raise ValueError(f"Objective directions must be 'max' or 'min': {invalid_directions}")

    parsed_constraints = [_parse_constraint(item) for item in (constraints or [])]
    identifiers: set[str] = set()
    normalized: list[tuple[str, dict[str, Any], dict[str, float]]] = []
    ineligible_ids: list[str] = []
    ineligible_reasons: dict[str, list[str]] = {}

    required_fields = set(objectives).union(field for field, _, _ in parsed_constraints)
    for index, row in enumerate(rows):
        candidate_id = str(row.get(id_field, "")).strip()
        if not candidate_id:
            raise ValueError(f"Row {index + 1} lacks identifier field '{id_field}'")
        if candidate_id in identifiers:
            raise ValueError(f"Duplicate candidate identifier: {candidate_id}")
        identifiers.add(candidate_id)
        values = {field: _number(row, field, candidate_id) for field in required_fields}

        failures = [
            f"{field}{operator}{threshold:g}"
            for field, operator, threshold in parsed_constraints
            if not _passes(values[field], operator, threshold)
        ]
        if failures:
            ineligible_ids.append(candidate_id)
            ineligible_reasons[candidate_id] = failures
        else:
            normalized.append((candidate_id, row, values))

    frontier: list[tuple[str, dict[str, Any], dict[str, float]]] = []
    dominated_ids: list[str] = []
    dominated_by: dict[str, list[str]] = {}
    for candidate in normalized:
        candidate_id, _, candidate_values = candidate
        dominators = [
            other_id
            for other_id, _, other_values in normalized
            if other_id != candidate_id
            and _dominates(other_values, candidate_values, objectives)
        ]
        if dominators:
            dominated_ids.append(candidate_id)
            dominated_by[candidate_id] = dominators
        else:
            frontier.append(candidate)

    return {
        "id_field": id_field,
        "objectives": objectives,
        "constraints": constraints or [],
        "eligible_count": len(normalized),
        "frontier_ids": [candidate_id for candidate_id, _, _ in frontier],
        "dominated_ids": dominated_ids,
        "ineligible_ids": ineligible_ids,
        "dominated_by": dominated_by,
        "ineligible_reasons": ineligible_reasons,
        "frontier": [row for _, row, _ in frontier],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find the non-dominated BERTopic candidates under an explicit study contract."
    )
    parser.add_argument("--input", required=True, type=Path, help="Candidate metrics CSV")
    parser.add_argument("--output", required=True, type=Path, help="Pareto result JSON")
    parser.add_argument("--id-field", default="candidate_id")
    parser.add_argument("--maximize", action="append", default=[], help="Metric to maximize")
    parser.add_argument("--minimize", action="append", default=[], help="Metric to minimize")
    parser.add_argument(
        "--constraint",
        action="append",
        default=[],
        help="Validation-derived gate such as coherence>=0.4",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    objectives: dict[str, str] = {}
    for field in args.maximize:
        if field in objectives:
            raise ValueError(f"Objective listed more than once: {field}")
        objectives[field] = "max"
    for field in args.minimize:
        if field in objectives:
            raise ValueError(f"Objective listed in both directions: {field}")
        objectives[field] = "min"

    with args.input.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    result = select_pareto(
        rows,
        objectives=objectives,
        constraints=args.constraint,
        id_field=args.id_field,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote Pareto selection: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
