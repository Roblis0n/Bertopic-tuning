import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_theme_reconnaissance import (  # noqa: E402
    compute_holdout_sampling_frame_sha256,
    compute_pre_model_artifact_fingerprint,
    validate_theme_reconnaissance,
)


def write_preview(
    root: Path,
    *,
    gate_status: str = "awaiting_user_direction",
    route: str = "network-short",
) -> None:
    artifact_dir = root / "fixtures"
    raw_dir = artifact_dir / "raw"
    card_dir = artifact_dir / "cards"
    raw_dir.mkdir(parents=True, exist_ok=True)
    card_dir.mkdir(parents=True, exist_ok=True)
    registered_artifacts = []
    for artifact_index in range(1, 13):
        canonical_index = (
            artifact_index - 8 if 9 <= artifact_index <= 10 else artifact_index
        )
        raw_bytes = f"fixture-unit-{canonical_index}".encode("utf-8")
        card_bytes = f"fixture-card-u{artifact_index}".encode("utf-8")
        raw_path = f"fixtures/raw/u{artifact_index}.txt"
        card_path = f"fixtures/cards/u{artifact_index}.txt"
        (root / raw_path).write_bytes(raw_bytes)
        (root / card_path).write_bytes(card_bytes)
        for artifact_path, artifact_bytes in (
            (raw_path, raw_bytes),
            (card_path, card_bytes),
        ):
            registered_artifacts.append(
                {
                    "artifact_path": artifact_path,
                    "artifact_sha256": (
                        "sha256:" + hashlib.sha256(artifact_bytes).hexdigest()
                    ),
                }
            )
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
        "reading_plan_id": "read-plan-20260722-a1",
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
            "profiled_source_unit_count": 12,
            "eligible_unit_count": 10,
            "reviewed_unit_count": 8,
            "full_text_reviewed_unit_count": 8,
            "extracted_representation_reviewed_unit_count": 0,
            "duplicate_inherited_unit_count": 2,
            "unreviewed_unit_count": 0,
            "excluded_unit_count": 2,
            "failed_unit_count": 0,
            "accounting_complete": True,
            "full_text_review_complete": True,
            "failed_unit_ids": [],
            "exclusion_basis": "two empty rows",
        },
        "parent_document_coverage": {
            "applicable": parent_applicable,
            "eligible_parent_document_count": 4 if parent_applicable else None,
            "profiled_parent_document_count": 4 if parent_applicable else None,
            "reviewed_parent_document_count": 4 if parent_applicable else None,
            "full_text_reviewed_parent_document_count": 4 if parent_applicable else None,
            "extracted_representation_reviewed_parent_document_count": 0 if parent_applicable else None,
            "duplicate_inherited_parent_document_count": 0 if parent_applicable else None,
            "unreviewed_parent_document_count": 0 if parent_applicable else None,
            "failed_parent_document_count": 0 if parent_applicable else None,
            "accounting_complete": parent_applicable,
            "full_text_review_complete": parent_applicable,
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

    reading_plan = {
        "schema_version": 1,
        "reading_plan_id": "read-plan-20260722-a1",
        "reconnaissance_id": reconnaissance_id,
        "corpus_fingerprint": fingerprint,
        "mode": "direct_full_text",
        "decision_basis": {
            "estimated_unique_full_text_tokens": 1200,
            "usable_reconnaissance_tokens": 4000,
            "time_budget": "fixture budget",
            "direct_full_text_feasible": True,
            "reason": "all eligible canonical units fit the registered budget",
        },
        "census": {
            "ledger_artifact": "corpus-reading-ledger.csv",
            "all_source_units_profiled": True,
            "profile_fields": ["unit_id", "source", "time", "language", "length"],
            "exact_duplicate_policy": "inherit only from byte-identical canonical text",
            "near_duplicate_policy": "review independently",
        },
        "extraction": {
            "streaming_or_batched": True,
            "raw_text_preserved": True,
            "unit_card_fields": ["unit_id", "raw_text", "source", "time", "language"],
            "registered_artifacts": registered_artifacts,
            "short_text_policy": "read complete canonical text",
            "long_document_policy": "read every natural section with offsets",
            "card_size_basis": "no truncation because direct full-text mode is feasible",
        },
        "selection": {
            "stratification_fields": ["source", "time", "language", "length"],
            "selection_channels": ["complete_unique_content"],
            "candidate_generation_rule": "read every eligible canonical unit",
            "escalation_rule": "not applicable because no unit is truncated or omitted",
        },
        "stopping": {
            "estimand": "complete direct review of eligible canonical content",
            "rule": "stop when the ledger contains no unreviewed eligible canonical unit",
            "status": "satisfied",
            "reconnaissance_state": "complete_for_preview",
            "termination_basis": "complete_full_text_review",
            "resource_budget_exhausted": False,
            "holdout_audit_performed": False,
            "holdout_unit_count": 0,
            "new_candidate_theme_count": 0,
            "material_change_detected": False,
            "decision": "not_applicable_full_text",
            "evidence": "full-text review complete",
        },
        "residual_risk": "ordinary interpretation uncertainty remains",
    }
    (root / "corpus-reading-plan.json").write_text(
        json.dumps(reading_plan, ensure_ascii=False), encoding="utf-8"
    )

    ledger_header = [
        "reading_plan_id",
        "unit_id",
        "parent_document_id",
        "route_subset",
        "source_group",
        "time_group",
        "language_group",
        "length_group",
        "duplicate_group_id",
        "content_sha256",
        "content_length",
        "canonical_unit_id",
        "selection_channels",
        "holdout_role",
        "review_depth",
        "extraction_artifact",
        "extraction_locator",
        "span_start",
        "span_end",
        "extraction_sha256",
        "audit_round_id",
        "sampling_frame_sha256",
        "candidate_map_freeze_sha256",
        "holdout_new_candidate_theme_ids",
        "holdout_material_change_detected",
        "candidate_theme_ids",
        "review_notes",
    ]
    ledger_rows = []
    for index in range(1, 13):
        unit_id = f"u{index}"
        if index <= 8:
            review_depth = "full_text"
            canonical = ""
            selection_channels = "complete_unique_content"
        elif index <= 10:
            review_depth = "exact_duplicate_inherited"
            canonical = f"u{index - 8}"
            selection_channels = ""
        else:
            review_depth = "excluded"
            canonical = ""
            selection_channels = ""
        ledger_candidate_ids = "PRE-C-001" if index <= 3 else (
            "PRE-F-001" if index <= 6 else ""
        )
        if route == "mixed":
            ledger_route = "network-short" if index <= 6 else "long-document"
            parent_document_id = (
                "" if index <= 6 else f"doc-{((index - 7) % 4) + 1}"
            )
        elif route == "long-document":
            ledger_route = "long-document"
            parent_document_id = f"doc-{((index - 1) % 4) + 1}"
        else:
            ledger_route = "network-short"
            parent_document_id = ""
        canonical_index = index - 8 if 9 <= index <= 10 else index
        content_sha256 = "sha256:" + hashlib.sha256(
            f"fixture-unit-{canonical_index}".encode("utf-8")
        ).hexdigest()
        content_length = len(f"fixture-unit-{canonical_index}".encode("utf-8"))
        duplicate_group_id = (
            "dup-1" if index in {1, 9} else "dup-2" if index in {2, 10} else ""
        )
        ledger_rows.append(
            [
                "read-plan-20260722-a1",
                unit_id,
                parent_document_id,
                ledger_route,
                f"source-{(index % 3) + 1}",
                "2026-Q3",
                "zh",
                "short",
                duplicate_group_id,
                content_sha256,
                content_length,
                canonical,
                selection_channels,
                "none",
                review_depth,
                f"fixtures/raw/{unit_id}.txt" if review_depth == "full_text" else "",
                f"record://{unit_id}" if review_depth == "full_text" else "",
                0 if review_depth == "full_text" else "",
                content_length if review_depth == "full_text" else "",
                content_sha256 if review_depth == "full_text" else "",
                "",
                "",
                "",
                "",
                "",
                ledger_candidate_ids,
                "reviewed fixture evidence" if review_depth == "full_text" else "",
            ]
        )
    with (root / "corpus-reading-ledger.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        csv.writer(handle).writerows([ledger_header, *ledger_rows])

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
            "false",
            "semantic_evidence_only",
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
            "false",
            "semantic_evidence_only",
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
        "prevalence_claimed",
        "claim_scope",
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
        "reading_plan_id": "read-plan-20260722-a1",
        "reading_mode": "direct_full_text",
        "progressive_reading_risk_acknowledged": False,
        "pre_model_artifact_fingerprint": (
            compute_pre_model_artifact_fingerprint(root) if approved else ""
        ),
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


def update_ledger(root: Path, update) -> None:
    path = root / "corpus-reading-ledger.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0])
    update(rows)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def refresh_progressive_holdout_bindings(root: Path) -> None:
    ledger_path = root / "corpus-reading-ledger.csv"
    with ledger_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    final_ids = {
        row["unit_id"] for row in rows if row["holdout_role"] == "final_independent"
    }
    sampling_frame_sha256 = compute_holdout_sampling_frame_sha256(final_ids)
    candidate_map_sha256 = "sha256:" + hashlib.sha256(
        (root / "theme-candidate-audit.csv").read_bytes()
    ).hexdigest()
    audit_round_id = "holdout-round-final-001"

    update_json(
        root,
        "corpus-reading-plan.json",
        lambda payload: payload["stopping"].update(
            holdout_audit_round_id=audit_round_id,
            holdout_sampling_frame_sha256=sampling_frame_sha256,
            candidate_map_freeze_sha256=candidate_map_sha256,
        ),
    )

    def bind(rows_to_bind):
        for row in rows_to_bind:
            if row["holdout_role"] == "final_independent":
                row.update(
                    audit_round_id=audit_round_id,
                    sampling_frame_sha256=sampling_frame_sha256,
                    candidate_map_freeze_sha256=candidate_map_sha256,
                    holdout_new_candidate_theme_ids="",
                    holdout_material_change_detected="false",
                )
            else:
                row.update(
                    audit_round_id="",
                    sampling_frame_sha256="",
                    candidate_map_freeze_sha256="",
                    holdout_new_candidate_theme_ids="",
                    holdout_material_change_detected="",
                )

    update_ledger(root, bind)


def make_progressive_preview(root: Path) -> None:
    def update_reconnaissance(payload):
        payload["coverage"].update(
            reviewed_unit_count=6,
            full_text_reviewed_unit_count=3,
            extracted_representation_reviewed_unit_count=3,
            unreviewed_unit_count=2,
            full_text_review_complete=False,
        )

    update_json(root, "theme-reconnaissance.json", update_reconnaissance)

    def update_plan(payload):
        payload["mode"] = "progressive_extraction"
        payload["decision_basis"].update(
            estimated_unique_full_text_tokens=320000000,
            usable_reconnaissance_tokens=60000,
            direct_full_text_feasible=False,
            reason="full-text reading exceeds the registered context and time budget",
        )
        payload["selection"].update(
            selection_channels=[
                "coverage_strata",
                "user_anchor",
                "lexical_novelty",
                "probability_holdout",
                "uncertainty_escalation",
            ],
            candidate_generation_rule=(
                "rotate across strata and channels, then add units where candidate "
                "yield or boundary uncertainty remains unresolved"
            ),
            escalation_rule=(
                "read full text for novel, ambiguous, conflicting, rare, or "
                "holdout-disconfirming evidence"
            ),
        )
        payload["stopping"].update(
            estimand="remaining undiscovered candidate-theme risk across the frame",
            rule=(
                "stop only after the registered independent holdout no longer "
                "changes the candidate map beyond the local decision boundary"
            ),
            status="satisfied",
            reconnaissance_state="complete_for_preview",
            termination_basis="local_holdout_rule_satisfied",
            resource_budget_exhausted=False,
            holdout_audit_performed=True,
            holdout_unit_count=2,
            new_candidate_theme_count=0,
            material_change_detected=False,
            decision="stop_with_residual_risk",
            evidence="independent holdout produced no new candidate in the fixture",
        )
        payload["residual_risk"] = (
            "rare themes without lexical cues may remain undiscovered"
        )

    update_json(root, "corpus-reading-plan.json", update_plan)

    def update_rows(rows):
        depths = {
            "u1": "full_text",
            "u2": "full_text",
            "u3": "extracted_representation",
            "u4": "full_text",
            "u5": "extracted_representation",
            "u6": "extracted_representation",
            "u7": "not_semantically_reviewed",
            "u8": "not_semantically_reviewed",
        }
        for row in rows:
            unit_id = row["unit_id"]
            if unit_id not in depths:
                continue
            row["review_depth"] = depths[unit_id]
            if depths[unit_id] == "full_text":
                channel_map = {
                    "u1": "coverage_strata|user_anchor",
                    "u2": "coverage_strata|lexical_novelty",
                    "u4": "coverage_strata|uncertainty_escalation",
                }
                row["selection_channels"] = channel_map[unit_id]
                row["holdout_role"] = "none"
                row["extraction_artifact"] = f"fixtures/raw/{unit_id}.txt"
                row["extraction_locator"] = f"record://{unit_id}"
                row["span_start"] = "0"
                row["span_end"] = row["content_length"]
                row["extraction_sha256"] = row["content_sha256"]
            elif depths[unit_id] == "extracted_representation":
                if unit_id in {"u5", "u6"}:
                    row["selection_channels"] = "coverage_strata|probability_holdout"
                    row["holdout_role"] = "final_independent"
                    row["candidate_theme_ids"] = ""
                else:
                    row["selection_channels"] = "coverage_strata"
                    row["holdout_role"] = "none"
                card_bytes = f"fixture-card-{unit_id}".encode("utf-8")
                row["extraction_artifact"] = f"fixtures/cards/{unit_id}.txt"
                row["extraction_locator"] = f"cards://{unit_id}"
                row["span_start"] = "0"
                row["span_end"] = str(len(card_bytes))
                row["extraction_sha256"] = "sha256:" + hashlib.sha256(
                    card_bytes
                ).hexdigest()
            else:
                row["selection_channels"] = ""
                row["holdout_role"] = "none"
                row["extraction_artifact"] = ""
                row["extraction_locator"] = ""
                row["span_start"] = ""
                row["span_end"] = ""
                row["extraction_sha256"] = ""
                row["candidate_theme_ids"] = ""
                row["review_notes"] = ""

            if unit_id in {"u1", "u2"}:
                row["candidate_theme_ids"] = "PRE-C-001"
            elif unit_id in {"u3", "u4"}:
                row["candidate_theme_ids"] = "PRE-F-001"

    update_ledger(root, update_rows)

    def update_candidate_rows(rows):
        rows[0]["evidence_unit_ids"] = "u1|u2"
        rows[1]["evidence_unit_ids"] = "u3|u4"

    update_candidates(root, update_candidate_rows)

    refresh_progressive_holdout_bindings(root)

    update_json(
        root,
        "modeling-authorization.json",
        lambda payload: payload.update(reading_mode="progressive_extraction"),
    )


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

    def test_direct_preview_requires_reading_plan_and_ledger(self):
        for missing_name in (
            "corpus-reading-plan.json",
            "corpus-reading-ledger.csv",
        ):
            with self.subTest(missing_name=missing_name):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    write_preview(root)
                    (root / missing_name).unlink()

                    result = validate_theme_reconnaissance(root)

                    self.assertFalse(result["valid"])
                    self.assertTrue(
                        any(missing_name in error for error in result["errors"]),
                        result["errors"],
                    )

    def test_progressive_extraction_can_produce_valid_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)

            result = validate_theme_reconnaissance(root)

            self.assertTrue(result["valid"], result["errors"])
            self.assertEqual(result["reading_mode"], "progressive_extraction")

    def test_progressive_mode_requires_all_selection_channels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)

            def mutate(payload):
                payload["selection"]["selection_channels"].remove(
                    "probability_holdout"
                )

            update_json(root, "corpus-reading-plan.json", mutate)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("probability_holdout" in error for error in result["errors"]),
                result["errors"],
            )

    def test_progressive_ledger_must_exercise_all_selection_channels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)

            update_ledger(
                root,
                lambda rows: rows[1].update(selection_channels="coverage_strata"),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "ledger is missing selection channel: lexical_novelty" in error
                    for error in result["errors"]
                ),
                result["errors"],
            )

    def test_progressive_holdout_count_must_match_final_independent_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)
            update_json(
                root,
                "corpus-reading-plan.json",
                lambda payload: payload["stopping"].update(holdout_unit_count=3),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("holdout_unit_count" in error for error in result["errors"]),
                result["errors"],
            )

    def test_final_independent_holdout_cannot_support_candidate_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)
            update_candidates(
                root,
                lambda rows: rows[1].update(evidence_unit_ids="u3|u4|u5"),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("final independent holdout" in error for error in result["errors"]),
                result["errors"],
            )

    def test_stop_with_residual_risk_rejects_material_holdout_change(self):
        for field, value in (
            ("new_candidate_theme_count", 3),
            ("material_change_detected", True),
        ):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    write_preview(root)
                    make_progressive_preview(root)
                    update_json(
                        root,
                        "corpus-reading-plan.json",
                        lambda payload, field=field, value=value: payload[
                            "stopping"
                        ].update({field: value}),
                    )

                    result = validate_theme_reconnaissance(root)

                    self.assertFalse(result["valid"])
                    self.assertTrue(
                        any("stop_with_residual_risk" in error for error in result["errors"]),
                        result["errors"],
                    )

    def test_progressive_stop_cannot_use_resource_exhaustion_as_evidence(self):
        for field, value in (
            ("rule", "stop when the token budget is exhausted"),
            ("evidence", "the review budget was exhausted"),
        ):
            with self.subTest(field=field):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    write_preview(root)
                    make_progressive_preview(root)
                    update_json(
                        root,
                        "corpus-reading-plan.json",
                        lambda payload, field=field, value=value: payload[
                            "stopping"
                        ].update({field: value}),
                    )

                    result = validate_theme_reconnaissance(root)

                    self.assertFalse(result["valid"])
                    self.assertTrue(
                        any("resource limit" in error for error in result["errors"]),
                        result["errors"],
                    )

    def test_progressive_stop_rejects_capacity_consumption_paraphrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)
            update_json(
                root,
                "corpus-reading-plan.json",
                lambda payload: payload["stopping"].update(
                    estimand="remaining review capacity",
                    rule="stop when all allocated review capacity has been fully consumed",
                    evidence="no review capacity remains",
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("resource limit" in error for error in result["errors"]),
                result["errors"],
            )

    def test_progressive_stop_rejects_resource_budget_exhausted_flag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)
            update_json(
                root,
                "corpus-reading-plan.json",
                lambda payload: payload["stopping"].update(
                    resource_budget_exhausted=True
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "resource_budget_exhausted=false" in error
                    for error in result["errors"]
                ),
                result["errors"],
            )

    def test_direct_full_text_rejects_holdout_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_json(
                root,
                "corpus-reading-plan.json",
                lambda payload: payload["stopping"].update(
                    holdout_unit_count=1,
                    new_candidate_theme_count=1,
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("direct_full_text stopping" in error for error in result["errors"]),
                result["errors"],
            )

    def test_reading_ledger_rejects_duplicate_unit_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_ledger(
                root,
                lambda rows: rows[1].update(unit_id=rows[0]["unit_id"]),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("duplicates unit_id" in error for error in result["errors"]),
                result["errors"],
            )

    def test_exact_duplicate_must_inherit_from_reviewed_canonical_unit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_ledger(
                root,
                lambda rows: rows[8].update(canonical_unit_id="does-not-exist"),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("canonical_unit_id" in error for error in result["errors"]),
                result["errors"],
            )

    def test_exact_duplicate_requires_matching_group_and_content_hash(self):
        cases = (
            (
                lambda rows: rows[8].update(duplicate_group_id="unrelated-group"),
                "duplicate_group_id",
            ),
            (
                lambda rows: rows[8].update(
                    content_sha256=(
                        "sha256:" + hashlib.sha256(b"different text").hexdigest()
                    )
                ),
                "content_sha256",
            ),
            (lambda rows: rows[8].update(content_sha256=""), "content_sha256"),
        )
        for mutate, expected_error in cases:
            with self.subTest(expected_error=expected_error):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    write_preview(root)
                    update_ledger(root, mutate)

                    result = validate_theme_reconnaissance(root)

                    self.assertFalse(result["valid"])
                    self.assertTrue(
                        any(expected_error in error for error in result["errors"]),
                        result["errors"],
                    )

    def test_semantic_review_requires_traceable_extraction_locator(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_ledger(
                root,
                lambda rows: rows[0].update(extraction_locator="x"),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("traceable extraction_locator" in error for error in result["errors"]),
                result["errors"],
            )

    def test_semantic_review_rejects_unregistered_locator_scheme(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_ledger(
                root,
                lambda rows: rows[0].update(extraction_locator="x://y"),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("traceable extraction_locator" in error for error in result["errors"]),
                result["errors"],
            )

    def test_registered_extraction_artifact_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            (root / "fixtures" / "raw" / "u1.txt").unlink()

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("registered extraction artifact does not exist" in error for error in result["errors"]),
                result["errors"],
            )

    def test_semantic_review_requires_registered_bounded_hashed_span(self):
        cases = (
            (
                lambda rows: rows[0].update(extraction_artifact="unregistered.jsonl"),
                "extraction_artifact is not registered",
            ),
            (
                lambda rows: rows[0].update(span_end="999999"),
                "span_end exceeds content_length",
            ),
            (
                lambda rows: rows[0].update(extraction_sha256="sha256:not-a-hash"),
                "extraction_sha256",
            ),
        )
        for mutate, expected_error in cases:
            with self.subTest(expected_error=expected_error):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    write_preview(root)
                    update_ledger(root, mutate)

                    result = validate_theme_reconnaissance(root)

                    self.assertFalse(result["valid"])
                    self.assertTrue(
                        any(expected_error in error for error in result["errors"]),
                        result["errors"],
                    )

    def test_progressive_candidate_audit_rejects_prevalence_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)
            update_candidates(
                root,
                lambda rows: rows[0].update(
                    independent_support="90% prevalence across the corpus"
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("prevalence claim" in error for error in result["errors"]),
                result["errors"],
            )

    def test_progressive_candidate_rejects_worded_prevalence_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)
            update_candidates(
                root,
                lambda rows: rows[0].update(
                    independent_support="appears in nine of every ten units"
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("prevalence claim" in error for error in result["errors"]),
                result["errors"],
            )

    def test_final_independent_holdout_cannot_use_adaptive_channels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)
            update_ledger(
                root,
                lambda rows: rows[4].update(
                    selection_channels=(
                        "coverage_strata|probability_holdout|user_anchor|"
                        "lexical_novelty|uncertainty_escalation"
                    )
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("final independent holdout cannot use adaptive" in error for error in result["errors"]),
                result["errors"],
            )

    def test_candidate_audit_requires_structured_prevalence_firewall(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_candidates(
                root,
                lambda rows: rows[0].update(
                    prevalence_claimed="true",
                    claim_scope="corpus_prevalence",
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("prevalence_claimed must be false" in error for error in result["errors"]),
                result["errors"],
            )

    def test_one_content_hash_maps_to_one_duplicate_canonical(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)

            def mutate(rows):
                shared_hash = rows[0]["content_sha256"]
                shared_length = rows[0]["content_length"]
                rows[1].update(
                    duplicate_group_id="dup-1",
                    content_sha256=shared_hash,
                    content_length=shared_length,
                    extraction_sha256=shared_hash,
                    span_end=shared_length,
                )
                rows[9].update(
                    duplicate_group_id="dup-1",
                    content_sha256=shared_hash,
                    content_length=shared_length,
                )

            update_ledger(root, mutate)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("one content hash must map to one canonical unit" in error for error in result["errors"]),
                result["errors"],
            )

    def test_duplicate_group_cannot_mix_content_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            update_ledger(
                root,
                lambda rows: rows[2].update(duplicate_group_id="dup-1"),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("duplicate_group_id dup-1 contains" in error for error in result["errors"]),
                result["errors"],
            )

    def test_candidate_evidence_must_have_been_semantically_reviewed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            make_progressive_preview(root)

            def mutate_coverage(payload):
                payload["coverage"].update(
                    reviewed_unit_count=5,
                    full_text_reviewed_unit_count=2,
                    unreviewed_unit_count=3,
                )

            update_json(root, "theme-reconnaissance.json", mutate_coverage)
            update_ledger(
                root,
                lambda rows: rows[0].update(
                    review_depth="not_semantically_reviewed",
                    selection_channels="",
                    extraction_locator="",
                    candidate_theme_ids="",
                    review_notes="",
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("candidate evidence unit u1" in error for error in result["errors"]),
                result["errors"],
            )

    def test_progressive_approval_requires_risk_acknowledgement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")
            make_progressive_preview(root)

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "progressive_reading_risk_acknowledged" in error
                    for error in result["errors"]
                ),
                result["errors"],
            )

    def test_progressive_approval_passes_with_fresh_artifact_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")
            make_progressive_preview(root)
            update_json(
                root,
                "modeling-authorization.json",
                lambda payload: payload.update(
                    progressive_reading_risk_acknowledged=True,
                    pre_model_artifact_fingerprint=(
                        compute_pre_model_artifact_fingerprint(root)
                    ),
                ),
            )

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertTrue(result["valid"], result["errors"])

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

    def test_approved_gate_is_invalidated_by_changed_candidate_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")
            update_candidates(
                root,
                lambda rows: rows[0].update(definition="changed after approval"),
            )

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("pre-model artifact fingerprint" in error for error in result["errors"]),
                result["errors"],
            )

    def test_approved_gate_is_invalidated_by_changed_research_question(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, gate_status="approved_for_modeling")
            update_json(
                root,
                "theme-reconnaissance.json",
                lambda payload: payload.update(research_question="changed after approval"),
            )

            result = validate_theme_reconnaissance(root, require_approval=True)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("pre-model artifact fingerprint" in error for error in result["errors"]),
                result["errors"],
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

    def test_long_document_route_requires_complete_parent_accounting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, route="long-document")

            def mutate(payload):
                payload["parent_document_coverage"].update(
                    reviewed_parent_document_count=3,
                    failed_parent_document_count=1,
                    accounting_complete=False,
                )

            update_json(root, "theme-reconnaissance.json", mutate)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "parent-document accounting" in error
                    for error in result["errors"]
                )
            )

    def test_parent_document_count_must_match_ledger_parent_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, route="long-document")
            update_json(
                root,
                "theme-reconnaissance.json",
                lambda payload: payload["parent_document_coverage"].update(
                    eligible_parent_document_count=3,
                    profiled_parent_document_count=3,
                    reviewed_parent_document_count=3,
                    full_text_reviewed_parent_document_count=3,
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("distinct parent_document_id" in error for error in result["errors"]),
                result["errors"],
            )

    def test_parent_full_text_and_extracted_counts_must_match_ledger_depths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, route="long-document")
            make_progressive_preview(root)

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("full_text_reviewed_parent_document_count" in error for error in result["errors"]),
                result["errors"],
            )

    def test_mixed_route_requires_both_concrete_route_subsets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, route="mixed")
            update_ledger(
                root,
                lambda rows: [row.update(route_subset="long-document") for row in rows],
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("both network-short and long-document" in error for error in result["errors"]),
                result["errors"],
            )

    def test_mixed_progressive_route_requires_semantic_review_in_each_subset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, route="mixed")
            make_progressive_preview(root)
            update_json(
                root,
                "theme-reconnaissance.json",
                lambda payload: payload["parent_document_coverage"].update(
                    reviewed_parent_document_count=0,
                    full_text_reviewed_parent_document_count=0,
                    extracted_representation_reviewed_parent_document_count=0,
                    duplicate_inherited_parent_document_count=2,
                    unreviewed_parent_document_count=2,
                    full_text_review_complete=False,
                ),
            )

            result = validate_theme_reconnaissance(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "semantic review in both network-short and long-document" in error
                    for error in result["errors"]
                ),
                result["errors"],
            )

    def test_mixed_progressive_preview_passes_when_both_subsets_are_audited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root, route="mixed")
            make_progressive_preview(root)

            update_json(
                root,
                "corpus-reading-plan.json",
                lambda payload: payload["stopping"].update(holdout_unit_count=3),
            )
            update_json(
                root,
                "theme-reconnaissance.json",
                lambda payload: (
                    payload["coverage"].update(
                        reviewed_unit_count=8,
                        extracted_representation_reviewed_unit_count=5,
                        unreviewed_unit_count=0,
                    ),
                    payload["parent_document_coverage"].update(
                        reviewed_parent_document_count=2,
                        full_text_reviewed_parent_document_count=0,
                        extracted_representation_reviewed_parent_document_count=2,
                        duplicate_inherited_parent_document_count=2,
                        unreviewed_parent_document_count=0,
                        full_text_review_complete=False,
                    ),
                ),
            )

            def audit_long_rows(rows):
                for unit_id, channels, role in (
                    (
                        "u7",
                        "coverage_strata|user_anchor|lexical_novelty|uncertainty_escalation",
                        "none",
                    ),
                    ("u8", "coverage_strata|probability_holdout", "final_independent"),
                ):
                    row = next(item for item in rows if item["unit_id"] == unit_id)
                    row.update(
                        review_depth="extracted_representation",
                        selection_channels=channels,
                        holdout_role=role,
                        extraction_artifact=f"fixtures/cards/{unit_id}.txt",
                        extraction_locator=f"cards://{unit_id}",
                        span_start="0",
                        span_end=str(len(f"fixture-card-{unit_id}".encode("utf-8"))),
                        extraction_sha256=(
                            "sha256:"
                            + hashlib.sha256(
                                f"fixture-card-{unit_id}".encode("utf-8")
                            ).hexdigest()
                        ),
                        candidate_theme_ids="",
                        review_notes="reviewed long-route fixture card",
                    )

            update_ledger(root, audit_long_rows)
            refresh_progressive_holdout_bindings(root)

            result = validate_theme_reconnaissance(root)

            self.assertTrue(result["valid"], result["errors"])

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
