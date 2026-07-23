import base64
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SKILL_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from build_visualization_plan import CORE_FIGURE_IDS, build_plan  # noqa: E402
from validate_visualization_bundle import validate_visualization_bundle  # noqa: E402


CORE_ARTIFACT_IDS = {
    "topic_terms",
    "topic_catalog",
    "topic_color_map",
    "document_topics",
    "document_coordinates",
    "document_projection_parameters",
    "topic_coordinates",
    "topic_projection_parameters",
    "topic_similarity",
    "topic_hierarchy",
    "candidate_metrics",
    "stability_metrics",
    "outlier_diagnostics",
    "coverage_diagnostics",
}

ROUTE_ARTIFACT_IDS = {
    "short_text_artifacts",
    "parent_document_topics",
}

CONDITIONAL_ARTIFACT_IDS = {
    "topics_over_time",
    "topics_by_group",
    "topic_geography",
    "topic_lineage",
    "document_topic_distributions",
}

ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def sha256_value(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def write_bytes(root: Path, relative: str, payload: bytes) -> dict[str, str]:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return {"path": relative.replace("\\", "/"), "sha256": sha256_value(payload)}


def write_text(root: Path, relative: str, text: str) -> dict[str, str]:
    return write_bytes(root, relative, text.encode("utf-8"))


def make_contract(
    root: Path,
    *,
    route: str = "network-short",
    enabled_modules: set[str] | None = None,
    missing_artifacts: set[str] | None = None,
) -> dict:
    enabled_modules = set(enabled_modules or set())
    missing_artifacts = set(missing_artifacts or set())
    artifact_ids = (
        CORE_ARTIFACT_IDS | ROUTE_ARTIFACT_IDS | CONDITIONAL_ARTIFACT_IDS
    )
    data_artifacts = {}
    for artifact_id in sorted(artifact_ids - missing_artifacts):
        data_artifacts[artifact_id] = write_text(
            root,
            f"inputs/{artifact_id}.json",
            json.dumps(
                {"artifact_id": artifact_id, "fixture": True},
                ensure_ascii=False,
                sort_keys=True,
            ),
        )

    field_map = {
        "unit_id": "record_key",
        "topic_id": "cluster_code",
        "topic_uid": "stable_topic_key",
        "topic_label": "topic_title",
        "parent_document_id": "container_key",
        "time": "event_period",
        "group": "comparison_cohort",
        "latitude": "northing_value",
        "longitude": "easting_value",
    }
    conditional_modules = {
        "time": {
            "enabled": "time" in enabled_modules,
            "field_map_keys": ["time"],
            "data_artifact_ids": ["topics_over_time"],
        },
        "group": {
            "enabled": "group" in enabled_modules,
            "field_map_keys": ["group"],
            "data_artifact_ids": ["topics_by_group"],
        },
        "geography": {
            "enabled": "geography" in enabled_modules,
            "field_map_keys": ["latitude", "longitude"],
            "data_artifact_ids": ["topic_geography"],
        },
        "lineage": {
            "enabled": "lineage" in enabled_modules,
            "field_map_keys": [],
            "data_artifact_ids": ["topic_lineage"],
        },
        "document_distribution": {
            "enabled": "document_distribution" in enabled_modules,
            "field_map_keys": [],
            "data_artifact_ids": ["document_topic_distributions"],
        },
    }
    return {
        "schema_version": 1,
        "study_id": "study-generic-fixture",
        "snapshot_id": "snapshot-generic-fixture",
        "route": route,
        "field_map": field_map,
        "data_artifacts": data_artifacts,
        "document_projection": {
            "basis": "document_embeddings",
            "coordinate_artifact_id": "document_coordinates",
            "method": "registered_projection",
            "parameters_artifact_id": "document_projection_parameters",
            "seed_or_determinism": "recorded-in-run-registry",
        },
        "relation_spaces": {
            "topic_map": {
                "basis": "semantic_topic_embeddings",
                "relation_artifact_id": "topic_coordinates",
                "parameters_artifact_id": "topic_projection_parameters",
            },
            "taxonomy": {
                "basis": "semantic_topic_embeddings",
                "relation_artifact_id": "topic_similarity",
                "hierarchy_artifact_id": "topic_hierarchy",
            },
        },
        "conditional_modules": conditional_modules,
        "topic_color_map_artifact_id": "topic_color_map",
        "outlier_topic_id": "-1",
        "export_policy": {
            "self_contained_html": True,
            "static_vector": True,
            "static_raster_png": True,
            "source_data": True,
            "caption": True,
            "alt_text": True,
            "sha256": True,
            "static_title_location": "caption",
            "colorblind_safe": True,
        },
    }


def figure_by_id(plan: dict, figure_id: str) -> dict:
    return next(
        figure for figure in plan["figures"] if figure["figure_id"] == figure_id
    )


def _write_figure_outputs(root: Path, figure_id: str) -> dict[str, dict]:
    stem = figure_id.replace("-", "_")
    outputs = {
        "interactive_html": write_text(
            root,
            f"figures/{stem}.html",
            (
                "<!doctype html><html><head><meta charset=\"utf-8\"></head>"
                f"<body><div id=\"{stem}\">self-contained figure</div></body></html>"
            ),
        ),
        "static_vector": write_text(
            root,
            f"figures/{stem}.svg",
            (
                "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"10\" height=\"10\">"
                "<rect width=\"10\" height=\"10\" fill=\"#0072B2\"/></svg>"
            ),
        ),
        "static_raster": write_bytes(
            root,
            f"figures/{stem}.png",
            ONE_PIXEL_PNG,
        ),
        "source_data": write_text(
            root,
            f"figure-data/{stem}.csv",
            "item,value\nfixture,1\n",
        ),
        "caption": write_text(
            root,
            f"captions/{stem}.md",
            f"Figure caption for {figure_id}. Data and relation basis are registered.",
        ),
        "alt_text": write_text(
            root,
            f"captions/{stem}.txt",
            f"Accessible description of {figure_id} with its principal visual relationship.",
        ),
    }
    outputs["interactive_html"]["self_contained"] = True
    return outputs


def write_complete_visualization_bundle(
    root: Path,
    *,
    route: str = "network-short",
    enabled_modules: set[str] | None = None,
) -> dict:
    contract = make_contract(
        root,
        route=route,
        enabled_modules=enabled_modules,
    )
    plan = build_plan(contract)
    (root / "visualization-contract.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (root / "visualization-plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    manifest_figures = []
    for planned in plan["figures"]:
        if planned["status"] != "ready":
            continue
        manifest_figures.append(
            {
                "figure_id": planned["figure_id"],
                "layer": planned["layer"],
                "status": "rendered",
                "research_question": planned["research_question"],
                "interpretation": (
                    "Interpretation is limited to the registered snapshot, inputs, "
                    "relation basis, and analysis unit."
                ),
                "limitations": (
                    "The figure is descriptive and does not replace held-out, "
                    "stability, coverage, or human-audit evidence."
                ),
                "input_artifact_ids": planned["input_artifact_ids"],
                "relation_basis": planned["relation_basis"],
                "coordinate_artifact_id": planned["coordinate_artifact_id"],
                "relation_artifact_id": planned["relation_artifact_id"],
                "color_map_artifact_id": planned["color_map_artifact_id"],
                "outlier_policy": planned["outlier_policy"],
                "title_location": "caption",
                "render_parameters": {
                    "source": "registered-local-study-parameters"
                },
                "outputs": _write_figure_outputs(root, planned["figure_id"]),
            }
        )

    manifest = {
        "schema_version": 1,
        "study_id": contract["study_id"],
        "snapshot_id": contract["snapshot_id"],
        "plan_id": plan["plan_id"],
        "figures": manifest_figures,
    }
    (root / "visualization-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return {
        "contract": contract,
        "plan": plan,
        "manifest": manifest,
    }


def rewrite_manifest(root: Path, manifest: dict) -> None:
    (root / "visualization-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def refresh_output_hash(root: Path, output: dict) -> None:
    output["sha256"] = sha256_value((root / output["path"]).read_bytes())


class VisualizationPlanTests(unittest.TestCase):
    def test_core_catalog_contains_baseline_views_and_governance_figures(self):
        expected = (
            "topic-term-barchart",
            "document-map",
            "topic-map",
            "topic-similarity-heatmap",
            "topic-hierarchy",
            "ctfidf-term-score-decline",
            "topic-prevalence",
            "candidate-pareto",
            "topic-stability",
            "outlier-diagnostics",
            "coverage-leakage-audit",
        )
        self.assertEqual(CORE_FIGURE_IDS, expected)

        with tempfile.TemporaryDirectory() as tmp:
            plan = build_plan(make_contract(Path(tmp)))
        core_ids = tuple(
            figure["figure_id"]
            for figure in plan["figures"]
            if figure["requirement"] == "core"
        )
        self.assertEqual(core_ids, expected)

        preferred = {
            figure["figure_id"]: figure["preferred_outputs"]
            for figure in plan["figures"]
        }
        self.assertEqual(
            preferred["topic-term-barchart"]["interactive_html"],
            "visualize_barchart.html",
        )
        self.assertEqual(
            preferred["document-map"]["interactive_html"],
            "visualize_documents.html",
        )
        self.assertEqual(
            preferred["document-map"]["static_raster"],
            "figure_bertopic_datamap.png",
        )
        self.assertEqual(
            preferred["topic-map"]["interactive_html"],
            "visualize_topics.html",
        )
        self.assertEqual(
            preferred["topic-similarity-heatmap"]["interactive_html"],
            "visualize_heatmap.html",
        )
        self.assertEqual(
            preferred["topic-hierarchy"]["interactive_html"],
            "visualize_hierarchy.html",
        )
        self.assertEqual(
            preferred["ctfidf-term-score-decline"]["static_raster"],
            "figure_ctfidf_term_score_decline.png",
        )

    def test_plan_is_deterministic_and_preserves_generic_field_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract = make_contract(Path(tmp))
            first = build_plan(contract)
            second = build_plan(deepcopy(contract))

        self.assertEqual(first, second)
        self.assertEqual(first["field_map"], contract["field_map"])
        self.assertNotIn("created_at", first)
        self.assertEqual(first["contract_errors"], [])

    def test_missing_core_inputs_block_figures_instead_of_omitting_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract = make_contract(
                Path(tmp),
                missing_artifacts={"topic_terms"},
            )
            plan = build_plan(contract)

        bars = figure_by_id(plan, "topic-term-barchart")
        decline = figure_by_id(plan, "ctfidf-term-score-decline")
        self.assertEqual(bars["status"], "blocked_missing_inputs")
        self.assertEqual(decline["status"], "blocked_missing_inputs")
        self.assertEqual(bars["missing_artifact_ids"], ["topic_terms"])
        self.assertGreaterEqual(plan["summary"]["blocked_required_count"], 2)

    def test_route_specific_figures_follow_the_route(self):
        expected = {
            "network-short": {
                "short-text-artifact-audit": "ready",
                "parent-document-topic-profile": "not_applicable",
            },
            "long-document": {
                "short-text-artifact-audit": "not_applicable",
                "parent-document-topic-profile": "ready",
            },
            "mixed": {
                "short-text-artifact-audit": "ready",
                "parent-document-topic-profile": "ready",
            },
        }
        for route, statuses in expected.items():
            with self.subTest(route=route), tempfile.TemporaryDirectory() as tmp:
                plan = build_plan(make_contract(Path(tmp), route=route))
                for figure_id, status in statuses.items():
                    self.assertEqual(
                        figure_by_id(plan, figure_id)["status"],
                        status,
                    )

    def test_metadata_figures_activate_only_from_registered_modules(self):
        enabled = {"time", "group", "lineage"}
        with tempfile.TemporaryDirectory() as tmp:
            plan = build_plan(
                make_contract(Path(tmp), enabled_modules=enabled)
            )

        expected = {
            "topics-over-time": "ready",
            "topics-by-group": "ready",
            "topic-lineage": "ready",
            "topic-geography": "not_applicable",
            "document-topic-distribution": "not_applicable",
        }
        for figure_id, status in expected.items():
            self.assertEqual(figure_by_id(plan, figure_id)["status"], status)

    def test_enabled_module_requires_its_field_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract = make_contract(Path(tmp), enabled_modules={"time"})
            contract["field_map"]["time"] = ""
            plan = build_plan(contract)

        self.assertTrue(
            any(
                "conditional_modules.time" in error and "field_map.time" in error
                for error in plan["contract_errors"]
            ),
            plan["contract_errors"],
        )

    def test_relation_basis_and_topic_minus_one_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            plan = build_plan(make_contract(Path(tmp)))

        self.assertEqual(
            figure_by_id(plan, "topic-map")["relation_basis"],
            "semantic_topic_embeddings",
        )
        self.assertEqual(
            figure_by_id(plan, "topic-similarity-heatmap")[
                "relation_artifact_id"
            ],
            "topic_similarity",
        )
        for figure_id in (
            "document-map",
            "topic-prevalence",
            "outlier-diagnostics",
        ):
            self.assertEqual(
                figure_by_id(plan, figure_id)["outlier_policy"],
                "include_topic_minus_one",
            )

    def test_core_geometry_and_color_artifact_ids_cannot_be_redirected(self):
        with tempfile.TemporaryDirectory() as tmp:
            contract = make_contract(Path(tmp))
            contract["document_projection"]["coordinate_artifact_id"] = (
                "topic_coordinates"
            )
            contract["document_projection"]["parameters_artifact_id"] = (
                "topic_projection_parameters"
            )
            contract["relation_spaces"]["topic_map"]["relation_artifact_id"] = (
                "topic_similarity"
            )
            contract["relation_spaces"]["topic_map"]["parameters_artifact_id"] = (
                "document_projection_parameters"
            )
            contract["relation_spaces"]["taxonomy"]["relation_artifact_id"] = (
                "topic_coordinates"
            )
            contract["relation_spaces"]["taxonomy"]["hierarchy_artifact_id"] = (
                "topic_terms"
            )
            contract["topic_color_map_artifact_id"] = "topic_catalog"

            plan = build_plan(contract)

        joined = "\n".join(plan["contract_errors"])
        for field in (
            "document_projection.coordinate_artifact_id",
            "document_projection.parameters_artifact_id",
            "relation_spaces.topic_map.relation_artifact_id",
            "relation_spaces.topic_map.parameters_artifact_id",
            "relation_spaces.taxonomy.relation_artifact_id",
            "relation_spaces.taxonomy.hierarchy_artifact_id",
            "topic_color_map_artifact_id",
        ):
            self.assertIn(field, joined)


class VisualizationBundleTests(unittest.TestCase):
    def test_complete_bundle_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_complete_visualization_bundle(
                root,
                route="mixed",
                enabled_modules={
                    "time",
                    "group",
                    "geography",
                    "lineage",
                    "document_distribution",
                },
            )

            audit = validate_visualization_bundle(root)

        self.assertTrue(audit["valid"], audit["errors"])
        self.assertEqual(audit["errors"], [])
        self.assertGreater(audit["rendered_figure_count"], len(CORE_FIGURE_IDS))

    def test_missing_required_figure_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            manifest = bundle["manifest"]
            manifest["figures"] = [
                row
                for row in manifest["figures"]
                if row["figure_id"] != "topic-term-barchart"
            ]
            rewrite_manifest(root, manifest)

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(
            any("Missing rendered figure: topic-term-barchart" in error for error in audit["errors"]),
            audit["errors"],
        )

    def test_stale_or_manually_edited_plan_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_complete_visualization_bundle(root)
            plan_path = root / "visualization-plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            plan["figures"][0]["research_question"] = "edited after planning"
            plan_path.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(
            any("does not match the deterministic plan" in error for error in audit["errors"]),
            audit["errors"],
        )

    def test_manifest_snapshot_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            manifest = bundle["manifest"]
            manifest["snapshot_id"] = "different-snapshot"
            rewrite_manifest(root, manifest)

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(any("snapshot_id" in error for error in audit["errors"]))

    def test_output_hash_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            row = next(
                item
                for item in bundle["manifest"]["figures"]
                if item["figure_id"] == "topic-map"
            )
            path = root / row["outputs"]["caption"]["path"]
            path.write_text("tampered caption", encoding="utf-8")

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(any("SHA-256 mismatch" in error for error in audit["errors"]))

    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            row = bundle["manifest"]["figures"][0]
            row["outputs"]["caption"] = {
                "path": "../outside.md",
                "sha256": sha256_value(b"outside"),
            }
            rewrite_manifest(root, bundle["manifest"])

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(any("safe relative path" in error for error in audit["errors"]))

    def test_remote_html_dependency_is_rejected_even_when_hash_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            row = next(
                item
                for item in bundle["manifest"]["figures"]
                if item["figure_id"] == "document-map"
            )
            output = row["outputs"]["interactive_html"]
            html_path = root / output["path"]
            html_path.write_text(
                (
                    "<html><head><script src=\"https://cdn.example/plot.js\"></script>"
                    "</head><body></body></html>"
                ),
                encoding="utf-8",
            )
            refresh_output_hash(root, output)
            rewrite_manifest(root, bundle["manifest"])

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(
            any("external script or stylesheet" in error for error in audit["errors"]),
            audit["errors"],
        )

    def test_invalid_png_signature_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            row = bundle["manifest"]["figures"][0]
            output = row["outputs"]["static_raster"]
            (root / output["path"]).write_bytes(b"not-a-png")
            refresh_output_hash(root, output)
            rewrite_manifest(root, bundle["manifest"])

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(any("PNG signature" in error for error in audit["errors"]))

    def test_relation_basis_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            row = next(
                item
                for item in bundle["manifest"]["figures"]
                if item["figure_id"] == "topic-map"
            )
            row["relation_basis"] = "ctfidf_lexical"
            rewrite_manifest(root, bundle["manifest"])

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(any("relation_basis" in error for error in audit["errors"]))

    def test_heatmap_and_hierarchy_must_share_taxonomy_relation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            row = next(
                item
                for item in bundle["manifest"]["figures"]
                if item["figure_id"] == "topic-hierarchy"
            )
            row["relation_artifact_id"] = "topic_coordinates"
            rewrite_manifest(root, bundle["manifest"])

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(
            any("relation_artifact_id" in error for error in audit["errors"]),
            audit["errors"],
        )

    def test_document_map_must_keep_the_frozen_coordinate_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            row = next(
                item
                for item in bundle["manifest"]["figures"]
                if item["figure_id"] == "document-map"
            )
            row["coordinate_artifact_id"] = "topic_coordinates"
            rewrite_manifest(root, bundle["manifest"])

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(
            any("coordinate_artifact_id" in error for error in audit["errors"]),
            audit["errors"],
        )

    def test_topic_minus_one_policy_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            row = next(
                item
                for item in bundle["manifest"]["figures"]
                if item["figure_id"] == "topic-prevalence"
            )
            row["outlier_policy"] = "excluded"
            rewrite_manifest(root, bundle["manifest"])

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(any("outlier_policy" in error for error in audit["errors"]))

    def test_static_title_must_live_in_the_caption(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_complete_visualization_bundle(root)
            bundle["manifest"]["figures"][0]["title_location"] = "inside-plot"
            rewrite_manifest(root, bundle["manifest"])

            audit = validate_visualization_bundle(root)

        self.assertFalse(audit["valid"])
        self.assertTrue(any("title_location" in error for error in audit["errors"]))


class VisualizationCliTests(unittest.TestCase):
    def test_require_ready_rejects_blocked_plan_but_writes_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = make_contract(
                root,
                missing_artifacts={"topic_terms"},
            )
            contract_path = root / "visualization-contract.json"
            output_path = root / "visualization-plan.json"
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPTS_DIR / "build_visualization_plan.py"),
                    "--contract",
                    str(contract_path),
                    "--output",
                    str(output_path),
                    "--require-ready",
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(output_path.is_file())
            plan = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertGreater(plan["summary"]["blocked_required_count"], 0)

    def test_validator_cli_accepts_complete_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_complete_visualization_bundle(root)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPTS_DIR / "validate_visualization_bundle.py"),
                    str(root),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["valid"])


class VisualizationDocumentationTests(unittest.TestCase):
    def test_visualization_reference_covers_all_required_views_and_layers(self):
        required_text = {
            "SKILL.md": [
                "references/research-grade-visualization.md",
                "build_visualization_plan.py",
                "validate_visualization_bundle.py",
                "structure",
                "representation",
                "taxonomy",
                "governance",
            ],
            "README.md": [
                "build_visualization_plan.py",
                "validate_visualization_bundle.py",
                "visualization-contract.json",
                "visualization-manifest.json",
            ],
            "references/research-grade-visualization.md": [
                "visualize_barchart.html",
                "visualize_documents.html",
                "figure_bertopic_datamap.png",
                "visualize_topics.html",
                "visualize_heatmap.html",
                "visualize_hierarchy.html",
                "figure_ctfidf_term_score_decline.png",
                "visualize_document_datamap",
                "visualize_term_rank",
                "topic_minus_one",
                "self_contained_html",
            ],
            "agents/openai.yaml": ["分层研究级图谱"],
        }
        for relative, needles in required_text.items():
            path = SKILL_ROOT / relative
            self.assertTrue(path.is_file(), relative)
            text = path.read_text(encoding="utf-8")
            for needle in needles:
                self.assertIn(needle, text, f"{relative}: {needle}")

    def test_visualization_templates_are_generic_and_complete(self):
        contract_path = SKILL_ROOT / "assets" / "visualization-contract.json"
        manifest_path = SKILL_ROOT / "assets" / "visualization-manifest.json"
        self.assertTrue(contract_path.is_file())
        self.assertTrue(manifest_path.is_file())
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(contract["outlier_topic_id"], "-1")
        self.assertTrue(contract["export_policy"]["self_contained_html"])
        self.assertEqual(
            set(contract["relation_spaces"]),
            {"topic_map", "taxonomy"},
        )
        self.assertEqual(manifest["figures"], [])
        self.assertTrue(
            all(value == "" for value in contract["field_map"].values())
        )
        self.assertEqual(contract["study_id"], "")
        self.assertEqual(contract["snapshot_id"], "")
        self.assertEqual(contract["route"], "")


if __name__ == "__main__":
    unittest.main()
