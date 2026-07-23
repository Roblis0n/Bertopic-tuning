#!/usr/bin/env python3
"""Validate a rendered, layered BERTopic research-visualization bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from build_visualization_plan import REQUIRED_OUTPUTS, build_plan


HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
REMOTE_SCRIPT_PATTERN = re.compile(
    r"<script\b[^>]*\bsrc\s*=\s*[\"']\s*(?:https?:)?//",
    re.IGNORECASE,
)
REMOTE_STYLESHEET_PATTERN = re.compile(
    r"<link\b[^>]*\bhref\s*=\s*[\"']\s*(?:https?:)?//",
    re.IGNORECASE,
)
SOURCE_DATA_SUFFIXES = {
    ".csv",
    ".tsv",
    ".json",
    ".parquet",
    ".arrow",
    ".feather",
}


def _read_json(path: Path, label: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Cannot read valid JSON from {label}: {exc}")
        return None
    if not isinstance(loaded, dict):
        errors.append(f"{label} must contain a JSON object")
        return None
    return loaded


def _safe_artifact_path(
    root: Path,
    relative: Any,
    context: str,
    errors: list[str],
) -> Path | None:
    text = str(relative or "").strip()
    if not text:
        errors.append(f"{context}.path must not be blank")
        return None
    candidate = Path(text)
    if candidate.is_absolute():
        errors.append(f"{context}.path must be a safe relative path inside the bundle")
        return None
    try:
        root_resolved = root.resolve()
        resolved = (root / candidate).resolve()
    except OSError as exc:
        errors.append(f"Cannot resolve {context}.path: {exc}")
        return None
    if resolved != root_resolved and root_resolved not in resolved.parents:
        errors.append(f"{context}.path must be a safe relative path inside the bundle")
        return None
    return resolved


def _read_hashed_artifact(
    root: Path,
    record: Any,
    context: str,
    errors: list[str],
) -> tuple[Path | None, bytes | None]:
    if not isinstance(record, dict):
        errors.append(f"{context} must be an object with path and sha256")
        return None, None
    path = _safe_artifact_path(root, record.get("path"), context, errors)
    digest = str(record.get("sha256", "")).strip()
    if not HASH_PATTERN.fullmatch(digest):
        errors.append(f"{context}.sha256 must use sha256:<64 lowercase hex>")
    if path is None:
        return None, None
    try:
        payload = path.read_bytes()
    except OSError as exc:
        errors.append(f"Cannot read {context} at {record.get('path')}: {exc}")
        return path, None
    actual = "sha256:" + hashlib.sha256(payload).hexdigest()
    if HASH_PATTERN.fullmatch(digest) and digest != actual:
        errors.append(
            f"SHA-256 mismatch for {context}: expected {digest}, found {actual}"
        )
    return path, payload


def _decode_nonblank(
    payload: bytes | None,
    context: str,
    errors: list[str],
) -> str | None:
    if payload is None:
        return None
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        errors.append(f"{context} must be valid UTF-8 text")
        return None
    if not text.strip():
        errors.append(f"{context} must not be blank")
    return text


def _validate_output(
    root: Path,
    output_name: str,
    record: Any,
    context: str,
    used_paths: dict[Path, str],
    errors: list[str],
) -> None:
    path, payload = _read_hashed_artifact(root, record, context, errors)
    if path is not None:
        previous = used_paths.get(path)
        if previous is not None:
            errors.append(
                f"{context}.path duplicates the output artifact already used by {previous}"
            )
        else:
            used_paths[path] = context
    if path is None or payload is None:
        return

    suffix = path.suffix.casefold()
    if output_name == "interactive_html":
        if suffix != ".html":
            errors.append(f"{context}.path must end in .html")
        text = _decode_nonblank(payload, context, errors)
        if text is not None:
            if "<html" not in text.casefold():
                errors.append(f"{context} must contain an HTML document")
            if REMOTE_SCRIPT_PATTERN.search(text) or REMOTE_STYLESHEET_PATTERN.search(
                text
            ):
                errors.append(
                    f"{context} contains an external script or stylesheet despite "
                    "the self-contained HTML policy"
                )
        if not isinstance(record, dict) or record.get("self_contained") is not True:
            errors.append(f"{context}.self_contained must be true")
        return

    if output_name == "static_vector":
        if suffix == ".svg":
            text = _decode_nonblank(payload, context, errors)
            if text is not None and "<svg" not in text.casefold():
                errors.append(f"{context} does not contain an SVG document")
        elif suffix == ".pdf":
            if not payload.startswith(b"%PDF-"):
                errors.append(f"{context} does not contain a PDF signature")
        else:
            errors.append(f"{context}.path must end in .svg or .pdf")
        return

    if output_name == "static_raster":
        if suffix != ".png":
            errors.append(f"{context}.path must end in .png")
        if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append(f"{context} does not contain a valid PNG signature")
        return

    if output_name == "source_data":
        if suffix not in SOURCE_DATA_SUFFIXES:
            errors.append(
                f"{context}.path must use a registered tabular or JSON data suffix"
            )
        if not payload:
            errors.append(f"{context} must not be empty")
        return

    if output_name == "caption":
        if suffix not in {".md", ".txt"}:
            errors.append(f"{context}.path must end in .md or .txt")
        _decode_nonblank(payload, context, errors)
        return

    if output_name == "alt_text":
        if suffix not in {".txt", ".md"}:
            errors.append(f"{context}.path must end in .txt or .md")
        _decode_nonblank(payload, context, errors)


def _match_field(
    figure_id: str,
    manifest_row: dict[str, Any],
    planned_row: dict[str, Any],
    field: str,
    errors: list[str],
) -> None:
    if manifest_row.get(field) != planned_row.get(field):
        errors.append(
            f"Figure {figure_id} {field} does not match visualization-plan.json"
        )


def _validate_manifest_figure(
    root: Path,
    manifest_row: dict[str, Any],
    planned_row: dict[str, Any],
    used_paths: dict[Path, str],
    errors: list[str],
) -> None:
    figure_id = planned_row["figure_id"]
    if manifest_row.get("status") != "rendered":
        errors.append(f"Figure {figure_id} status must be rendered")
    for field in (
        "layer",
        "research_question",
        "input_artifact_ids",
        "relation_basis",
        "coordinate_artifact_id",
        "relation_artifact_id",
        "color_map_artifact_id",
        "outlier_policy",
    ):
        _match_field(figure_id, manifest_row, planned_row, field, errors)

    for field in ("research_question", "interpretation", "limitations"):
        if not str(manifest_row.get(field, "")).strip():
            errors.append(f"Figure {figure_id} {field} must not be blank")
    parameters = manifest_row.get("render_parameters")
    if not isinstance(parameters, dict) or not parameters:
        errors.append(f"Figure {figure_id} render_parameters must be a nonempty object")
    if manifest_row.get("title_location") != "caption":
        errors.append(f"Figure {figure_id} title_location must be caption")

    outputs = manifest_row.get("outputs")
    if not isinstance(outputs, dict):
        errors.append(f"Figure {figure_id} outputs must be an object")
        return
    for output_name in REQUIRED_OUTPUTS:
        if output_name not in outputs:
            errors.append(f"Figure {figure_id} lacks output: {output_name}")
            continue
        _validate_output(
            root,
            output_name,
            outputs[output_name],
            f"Figure {figure_id} output {output_name}",
            used_paths,
            errors,
        )


def _validate_input_artifacts(
    root: Path,
    contract: dict[str, Any],
    planned_figures: list[dict[str, Any]],
    errors: list[str],
) -> None:
    artifacts = contract.get("data_artifacts")
    if not isinstance(artifacts, dict):
        return
    required_ids = sorted(
        {
            artifact_id
            for figure in planned_figures
            for artifact_id in figure.get("input_artifact_ids", [])
        }
    )
    for artifact_id in required_ids:
        record = artifacts.get(artifact_id)
        _read_hashed_artifact(
            root,
            record,
            f"Input artifact {artifact_id}",
            errors,
        )


def validate_visualization_bundle(root: Path) -> dict[str, Any]:
    """Return a machine-readable audit of a rendered visualization bundle."""
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    base_result: dict[str, Any] = {
        "valid": False,
        "errors": errors,
        "warnings": warnings,
        "study_id": "",
        "snapshot_id": "",
        "plan_id": "",
        "rendered_figure_count": 0,
    }
    if not root.exists() or not root.is_dir():
        errors.append(f"Visualization bundle directory does not exist: {root}")
        return base_result

    filenames = (
        "visualization-contract.json",
        "visualization-plan.json",
        "visualization-manifest.json",
    )
    for filename in filenames:
        if not (root / filename).is_file():
            errors.append(f"Missing required file: {filename}")
    if errors:
        return base_result

    contract = _read_json(
        root / "visualization-contract.json",
        "visualization-contract.json",
        errors,
    )
    plan = _read_json(
        root / "visualization-plan.json",
        "visualization-plan.json",
        errors,
    )
    manifest = _read_json(
        root / "visualization-manifest.json",
        "visualization-manifest.json",
        errors,
    )
    if contract is None or plan is None or manifest is None:
        return base_result

    expected_plan = build_plan(contract)
    base_result.update(
        study_id=str(expected_plan.get("study_id", "")),
        snapshot_id=str(expected_plan.get("snapshot_id", "")),
        plan_id=str(expected_plan.get("plan_id", "")),
    )
    if plan != expected_plan:
        errors.append(
            "visualization-plan.json does not match the deterministic plan "
            "rebuilt from visualization-contract.json"
        )
    for error in expected_plan.get("contract_errors", []):
        errors.append(f"Visualization contract: {error}")

    planned_figures = [
        figure
        for figure in expected_plan["figures"]
        if figure["status"] != "not_applicable"
    ]
    for figure in planned_figures:
        if figure["status"] == "blocked_missing_inputs":
            missing = ", ".join(figure["missing_artifact_ids"])
            errors.append(
                f"Required figure {figure['figure_id']} is blocked by missing "
                f"input artifacts: {missing}"
            )
    ready_figures = [
        figure for figure in planned_figures if figure["status"] == "ready"
    ]
    _validate_input_artifacts(root, contract, ready_figures, errors)

    identity_pairs = (
        ("study_id", expected_plan["study_id"]),
        ("snapshot_id", expected_plan["snapshot_id"]),
        ("plan_id", expected_plan["plan_id"]),
    )
    for field, expected in identity_pairs:
        if manifest.get(field) != expected:
            errors.append(
                f"visualization-manifest.json {field} does not match the plan"
            )
    if manifest.get("schema_version") != 1:
        errors.append("visualization-manifest.json schema_version must be 1")

    manifest_rows = manifest.get("figures")
    if not isinstance(manifest_rows, list):
        errors.append("visualization-manifest.json figures must be a list")
        manifest_rows = []
    rows_by_id: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(manifest_rows):
        if not isinstance(row, dict):
            errors.append(f"visualization-manifest.json figures[{index}] must be an object")
            continue
        figure_id = str(row.get("figure_id", "")).strip()
        if not figure_id:
            errors.append(
                f"visualization-manifest.json figures[{index}] lacks figure_id"
            )
            continue
        if figure_id in rows_by_id:
            errors.append(f"Duplicate rendered figure: {figure_id}")
            continue
        rows_by_id[figure_id] = row

    planned_by_id = {
        figure["figure_id"]: figure for figure in expected_plan["figures"]
    }
    for figure_id in sorted(set(rows_by_id).difference(planned_by_id)):
        errors.append(f"Unplanned rendered figure: {figure_id}")
    for figure_id, row in rows_by_id.items():
        planned = planned_by_id.get(figure_id)
        if planned and planned["status"] == "not_applicable":
            errors.append(f"Figure {figure_id} is rendered but the plan marks it not_applicable")

    used_paths: dict[Path, str] = {}
    for planned in ready_figures:
        figure_id = planned["figure_id"]
        row = rows_by_id.get(figure_id)
        if row is None:
            errors.append(f"Missing rendered figure: {figure_id}")
            continue
        _validate_manifest_figure(root, row, planned, used_paths, errors)

    document_row = rows_by_id.get("document-map")
    projection_id = str(
        contract.get("document_projection", {}).get(
            "coordinate_artifact_id", ""
        )
    )
    if document_row and document_row.get("coordinate_artifact_id") != projection_id:
        errors.append(
            "document-map HTML, vector, and PNG must share the frozen "
            "document_projection coordinate_artifact_id"
        )

    heatmap = rows_by_id.get("topic-similarity-heatmap")
    hierarchy = rows_by_id.get("topic-hierarchy")
    if heatmap and hierarchy:
        for field in ("relation_basis", "relation_artifact_id"):
            if heatmap.get(field) != hierarchy.get(field):
                errors.append(
                    f"topic-similarity-heatmap and topic-hierarchy must share {field}"
                )

    for figure_id in (
        "document-map",
        "topic-prevalence",
        "outlier-diagnostics",
    ):
        row = rows_by_id.get(figure_id)
        if row and row.get("outlier_policy") != "include_topic_minus_one":
            errors.append(
                f"Figure {figure_id} outlier_policy must include Topic -1 explicitly"
            )

    base_result["rendered_figure_count"] = len(rows_by_id)
    base_result["valid"] = not errors
    return base_result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a layered BERTopic research-visualization bundle"
    )
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output", type=Path, help="Optional JSON audit output")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = validate_visualization_bundle(args.bundle)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
