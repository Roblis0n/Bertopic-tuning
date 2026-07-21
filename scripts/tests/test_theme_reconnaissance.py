import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_theme_reconnaissance import validate_theme_reconnaissance  # noqa: E402


def write_preview(
    root: Path,
    *,
    gate_status: str = "awaiting_user_direction",
    route: str = "network-short",
) -> None:
    fingerprint = "sha256:corpus-test"
    reconnaissance_id = "recon-20260721-a1"
    candidate_ids = ["PRE-C-001", "PRE-F-001"]
    approved = gate_status == "approved_for_modeling"

    (root / "corpus-profile.json").write_text(
        json.dumps({"corpus_fingerprint": fingerprint, "unit_count": 12}),
        encoding="utf-8",
    )
    parent_applicable = route in {"long-document", "mixed"}
    reconnaissance = {
        "schema_version": 1,
        "reconnaissance_id": reconnaissance_id,
        "corpus_fingerprint": fingerprint,
        "route": route,
        "created_at": "2026-07-21T12:00:00+08:00",
        "research_question": "识别围绕公共服务的主题及新兴问题",
        "user_theme": {
            "mainline": "公共服务",
            "mode": "coverage_and_interpretation_anchor",
            "allow_emergent_themes": True,
            "inclusion_intent": "服务可及性与体验",
            "exclusion_intent": "纯平台模板",
        },
        "coverage": {
            "source_unit_count": 12,
            "eligible_unit_count": 10,
            "reviewed_unit_count": 8,
            "duplicate_inherited_unit_count": 2,
            "excluded_unit_count": 2,
            "failed_unit_count": 0,
            "coverage_complete": True,
            "failed_unit_ids": [],
            "exclusion_basis": "two empty rows",
        },
        "parent_document_coverage": {
            "applicable": parent_applicable,
            "eligible_parent_document_count": 4 if parent_applicable else None,
            "reviewed_parent_document_count": 4 if parent_applicable else None,
            "failed_parent_document_count": 0 if parent_applicable else None,
            "coverage_complete": parent_applicable,
        },
        "topic_count_estimate": {
            "interpretation": "pre_model_hypothesis_not_target_k",
            "coarse": {
                "lower_bound": 1,
                "point_estimate": 1,
                "upper_bound": 1,
                "candidate_theme_ids": ["PRE-C-001"],
                "basis": "one stable parent theme across independent sources",
            },
            "fine": {
                "lower_bound": 1,
                "point_estimate": 1,
                "upper_bound": 2,
                "candidate_theme_ids": ["PRE-F-001"],
                "basis": "one stable subtheme and one unresolved split boundary",
            },
        },
        "unresolved_boundaries": ["PRE-F-001 may split by service channel"],
        "excluded_artifact_candidate_ids": [],
        "strongest_counter_evidence": "one source uses the same term differently",
    }
    (root / "theme-reconnaissance.json").write_text(
        json.dumps(reconnaissance, ensure_ascii=False), encoding="utf-8"
    )

    rows = [
        [
            reconnaissance_id,
            "PRE-C-001",
            "",
            "coarse",
            route,
            "服务体验",
            "experience",
            "mainline",
            "对公共服务过程的评价",
            "实际服务经历",
            "纯平台模板",
            "four independent sources",
            "u1|u2|u3",
            "source-a|source-b|source-c|source-d",
            "low; exact duplicates accounted separately",
            "boundary with access complaints",
            "accepted" if approved else "",
            "按预估继续" if approved else "",
        ],
        [
            reconnaissance_id,
            "PRE-F-001",
            "PRE-C-001",
            "fine",
            route,
            "办理便利性",
            "process",
            "supporting",
            "办理步骤与渠道便利程度",
            "渠道或流程评价",
            "服务结果评价",
            "three independent sources",
            "u4|u5|u6",
            "source-a|source-c|source-e",
            "low",
            "possible online/offline split",
            "accepted" if approved else "",
            "按预估继续" if approved else "",
        ],
    ]
    header = [
        "reconnaissance_id",
        "candidate_theme_id",
        "parent_candidate_theme_id",
        "hierarchy_level",
        "route_subset",
        "provisional_label",
        "theme_type",
        "relation_to_user_mainline",
        "definition",
        "inclusion",
        "exclusion",
        "independent_support",
        "evidence_unit_ids",
        "source_or_parent_spread",
        "duplicate_or_artifact_risk",
        "uncertainty",
        "user_disposition",
        "user_instruction",
    ]
    with (root / "theme-candidate-audit.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        csv.writer(handle).writerows([header, *rows])

    authorization = {
        "schema_version": 1,
        "authorization_id": "auth-20260721-a1" if approved else "",
        "reconnaissance_id": reconnaissance_id,
        "corpus_fingerprint": fingerprint,
        "gate_status": gate_status,
        "modeling_may_start": approved,
        "user_theme_mode": "coverage_and_interpretation_anchor",
        "allow_emergent_themes": True,
        "user_instruction": "按预估继续" if approved else "",
        "resolved_candidate_theme_ids": candidate_ids if approved else [],
        "decision_recorded_at": "2026-07-21T12:30:00+08:00" if approved else "",
    }
    (root / "modeling-authorization.json").write_text(
        json.dumps(authorization, ensure_ascii=False), encoding="utf-8"
    )


def update_json(root: Path, name: str, update) -> None:
    path = root / name
    payload = json.loads(path.read_text(encoding="utf-8"))
    update(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def update_candidates(root: Path, update) -> None:
    path = root / "theme-candidate-audit.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    update(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class ThemeReconnaissanceValidationTests(unittest.TestCase):
    def test_missing_required_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            (root / "theme-candidate-audit.csv").unlink()

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertIn(
                "Missing required file: theme-candidate-audit.csv",
                result["errors"],
            )

    def test_malformed_authorization_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            (root / "modeling-authorization.json").write_text(
                "{not-json", encoding="utf-8"
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "Cannot read valid JSON from modeling-authorization.json"
                    in error
                    for error in result["errors"]
                )
            )

    def test_complete_preview_can_wait_for_user_direction(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)

            result = validate_theme_reconnaissance(root)

            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["gate_status"], "awaiting_user_direction")

    def test_approval_is_required_only_when_requested(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("approved_for_modeling" in error for error in result["errors"])
            )

    def test_incomplete_coverage_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            path = root / "theme-reconnaissance.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["coverage"]["failed_unit_count"] = 1
            path.write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("eligible_unit_count" in error for error in result["errors"])
            )
            self.assertTrue(
                any("failed_unit_count" in error for error in result["errors"])
            )

    def test_negative_coverage_count_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)

            def mutate(payload):
                payload["coverage"]["duplicate_inherited_unit_count"] = -1

            update_json(root, "theme-reconnaissance.json", mutate)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "duplicate_inherited_unit_count must be a non-negative integer"
                    in error
                    for error in result["errors"]
                )
            )

    def test_artifact_candidate_cannot_remain_in_topic_count_estimate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            candidate_path = root / "theme-candidate-audit.csv"
            with candidate_path.open(
                "r", encoding="utf-8-sig", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0])
            rows[1]["relation_to_user_mainline"] = "artifact"
            with candidate_path.open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("artifact" in error for error in result["errors"]),
                result["errors"],
            )

    def test_approved_preview_passes_approval_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["authorization_id"], "auth-20260721-a1")

    def test_mismatched_fingerprint_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_json(
                root,
                "modeling-authorization.json",
                lambda payload: payload.update(corpus_fingerprint="sha256:other"),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("corpus_fingerprint" in error for error in result["errors"])
            )

    def test_approved_gate_is_invalidated_by_changed_corpus_fingerprint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")
            update_json(
                root,
                "corpus-profile.json",
                lambda payload: payload.update(corpus_fingerprint="sha256:changed"),
            )

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "corpus-profile.json corpus_fingerprint" in error
                    for error in result["errors"]
                )
            )

    def test_candidate_reconnaissance_id_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_candidates(
                root,
                lambda rows: rows[0].update(reconnaissance_id="recon-other"),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "row 2 reconnaissance_id does not match" in error
                    for error in result["errors"]
                )
            )

    def test_unordered_topic_range_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)

            def mutate(payload):
                payload["topic_count_estimate"]["fine"].update(
                    lower_bound=3,
                    point_estimate=2,
                    upper_bound=1,
                )

            update_json(root, "theme-reconnaissance.json", mutate)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "lower_bound <= point_estimate" in error
                    for error in result["errors"]
                )
            )

    def test_point_estimate_must_match_listed_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)

            def mutate(payload):
                payload["topic_count_estimate"]["fine"]["point_estimate"] = 2
                payload["topic_count_estimate"]["fine"]["upper_bound"] = 2

            update_json(root, "theme-reconnaissance.json", mutate)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "number of listed candidate_theme_ids" in error
                    for error in result["errors"]
                )
            )

    def test_unknown_estimate_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)

            def mutate(payload):
                payload["topic_count_estimate"]["fine"][
                    "candidate_theme_ids"
                ] = ["PRE-F-UNKNOWN"]

            update_json(root, "theme-reconnaissance.json", mutate)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("unknown candidate IDs" in error for error in result["errors"])
            )

    def test_duplicate_candidate_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_candidates(
                root,
                lambda rows: rows[1].update(candidate_theme_id="PRE-C-001"),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("duplicates candidate_theme_id" in error for error in result["errors"])
            )

    def test_blank_candidate_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_candidates(
                root,
                lambda rows: rows[1].update(candidate_theme_id=""),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("row 3 lacks candidate_theme_id" in error for error in result["errors"])
            )

    def test_unknown_hierarchy_and_mainline_relation_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_candidates(
                root,
                lambda rows: rows[0].update(
                    hierarchy_level="middle",
                    relation_to_user_mainline="adjacent",
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("hierarchy_level must be coarse or fine" in error for error in result["errors"])
            )
            self.assertTrue(
                any("invalid relation_to_user_mainline" in error for error in result["errors"])
            )

    def test_unknown_parent_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_candidates(
                root,
                lambda rows: rows[1].update(
                    parent_candidate_theme_id="PRE-C-UNKNOWN"
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "unknown parent_candidate_theme_id" in error
                    for error in result["errors"]
                )
            )

    def test_self_referential_parent_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_candidates(
                root,
                lambda rows: rows[1].update(
                    parent_candidate_theme_id="PRE-F-001"
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("cannot be its own parent" in error for error in result["errors"])
            )

    def test_source_count_must_match_corpus_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_json(
                root,
                "corpus-profile.json",
                lambda payload: payload.update(unit_count=13),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "source_unit_count must match" in error
                    for error in result["errors"]
                )
            )

    def test_blank_research_question_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_json(
                root,
                "theme-reconnaissance.json",
                lambda payload: payload.update(research_question=""),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("research_question" in error for error in result["errors"])
            )

    def test_blank_creation_timestamp_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_json(
                root,
                "theme-reconnaissance.json",
                lambda payload: payload.update(created_at=""),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(any("created_at" in error for error in result["errors"]))

    def test_blank_evidence_unit_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_candidates(
                root,
                lambda rows: rows[0].update(evidence_unit_ids=""),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("row 2 lacks evidence_unit_ids" in error for error in result["errors"])
            )

    def test_emergent_themes_must_remain_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)

            def mutate(payload):
                payload["user_theme"]["allow_emergent_themes"] = False

            update_json(root, "theme-reconnaissance.json", mutate)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "user_theme.allow_emergent_themes" in error
                    for error in result["errors"]
                )
            )

    def test_long_document_route_requires_complete_parent_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, route="long-document")

            def mutate(payload):
                payload["parent_document_coverage"].update(
                    reviewed_parent_document_count=3,
                    failed_parent_document_count=1,
                    coverage_complete=False,
                )

            update_json(root, "theme-reconnaissance.json", mutate)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "parent-document coverage" in error
                    for error in result["errors"]
                )
            )

    def test_modeling_flag_cannot_bypass_waiting_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_json(
                root,
                "modeling-authorization.json",
                lambda payload: payload.update(modeling_may_start=True),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("true only" in error for error in result["errors"])
            )

    def test_modeling_flag_cannot_bypass_revision_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="revision_requested")
            update_json(
                root,
                "modeling-authorization.json",
                lambda payload: payload.update(modeling_may_start=True),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("true only" in error for error in result["errors"])
            )

    def test_revision_and_stop_states_are_valid_pauses(self):
        for gate_status in ("revision_requested", "stop"):
            with self.subTest(gate_status=gate_status):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    write_preview(root, gate_status=gate_status)

                    preview = validate_theme_reconnaissance(root)
                    modeling = validate_theme_reconnaissance(
                        root, require_approval=True
                    )

                    self.assertTrue(preview["valid"], preview["errors"])
                    self.assertFalse(modeling["valid"])
                    self.assertTrue(
                        any(
                            "approved_for_modeling" in error
                            for error in modeling["errors"]
                        )
                    )

    def test_unknown_gate_state_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_json(
                root,
                "modeling-authorization.json",
                lambda payload: payload.update(gate_status="ready"),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("invalid gate_status" in error for error in result["errors"])
            )

    def test_approved_gate_requires_modeling_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")
            update_json(
                root,
                "modeling-authorization.json",
                lambda payload: payload.update(modeling_may_start=False),
            )

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("true only for approved_for_modeling" in error for error in result["errors"])
            )

    def test_approved_gate_requires_every_candidate_disposition(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")
            update_candidates(
                root,
                lambda rows: rows[1].update(user_disposition=""),
            )

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "requires a valid user_disposition" in error
                    for error in result["errors"]
                )
            )

    def test_unknown_candidate_disposition_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")
            update_candidates(
                root,
                lambda rows: rows[0].update(user_disposition="maybe"),
            )

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("invalid user_disposition" in error for error in result["errors"])
            )

    def test_approved_gate_requires_exact_resolved_candidate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")
            update_json(
                root,
                "modeling-authorization.json",
                lambda payload: payload.update(
                    resolved_candidate_theme_ids=["PRE-C-001"]
                ),
            )

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "match every candidate theme exactly" in error
                    for error in result["errors"]
                )
            )

    def test_approved_gate_requires_decision_timestamp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")
            update_json(
                root,
                "modeling-authorization.json",
                lambda payload: payload.update(decision_recorded_at=""),
            )

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("decision_recorded_at" in error for error in result["errors"])
            )

    def test_cli_returns_zero_for_valid_waiting_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPTS_DIR / "validate_theme_reconnaissance.py"),
                    str(root),
                ],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(json.loads(completed.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
