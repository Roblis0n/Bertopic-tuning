import csv
import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SKILL_ROOT = SCRIPTS_DIR.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))


def load_module(name):
    return importlib.import_module(name)


def registry_rows():
    return [
        {
            "candidate_id": "baseline-a",
            "stage_id": "baseline",
            "champion_parent_id": "",
            "changed_parameter_family": "baseline",
            "analysis_unit": "post",
            "embedding_model": "encoder-a",
            "umap_config": json.dumps({"n_neighbors": 15}),
            "hdbscan_config": json.dumps(
                {
                    "min_cluster_size": 20,
                    "min_samples": 10,
                    "cluster_selection_method": "eom",
                }
            ),
            "representation_config": json.dumps({"vectorizer": "base"}),
            "taxonomy_config": json.dumps({"snapshot": "raw"}),
            "assignment_fingerprint": "assign-1",
            "semantic_review_status": "pass",
        },
        {
            "candidate_id": "embedding-b",
            "stage_id": "embedding",
            "champion_parent_id": "baseline-a",
            "changed_parameter_family": "embedding",
            "analysis_unit": "post",
            "embedding_model": "encoder-b",
            "umap_config": json.dumps({"n_neighbors": 15}),
            "hdbscan_config": json.dumps(
                {
                    "min_cluster_size": 20,
                    "min_samples": 10,
                    "cluster_selection_method": "eom",
                }
            ),
            "representation_config": json.dumps({"vectorizer": "base"}),
            "taxonomy_config": json.dumps({"snapshot": "raw"}),
            "assignment_fingerprint": "assign-2",
            "semantic_review_status": "pass",
        },
        {
            "candidate_id": "umap-c",
            "stage_id": "umap",
            "champion_parent_id": "embedding-b",
            "changed_parameter_family": "umap",
            "analysis_unit": "post",
            "embedding_model": "encoder-b",
            "umap_config": json.dumps({"n_neighbors": 30}),
            "hdbscan_config": json.dumps(
                {
                    "min_cluster_size": 20,
                    "min_samples": 10,
                    "cluster_selection_method": "eom",
                }
            ),
            "representation_config": json.dumps({"vectorizer": "base"}),
            "taxonomy_config": json.dumps({"snapshot": "raw"}),
            "assignment_fingerprint": "assign-3",
            "semantic_review_status": "fail",
        },
        {
            "candidate_id": "hdbscan-d",
            "stage_id": "hdbscan_min_cluster_size",
            "champion_parent_id": "embedding-b",
            "changed_parameter_family": "hdbscan_min_cluster_size",
            "analysis_unit": "post",
            "embedding_model": "encoder-b",
            "umap_config": json.dumps({"n_neighbors": 15}),
            "hdbscan_config": json.dumps(
                {
                    "min_cluster_size": 30,
                    "min_samples": 10,
                    "cluster_selection_method": "eom",
                }
            ),
            "representation_config": json.dumps({"vectorizer": "base"}),
            "taxonomy_config": json.dumps({"snapshot": "raw"}),
            "assignment_fingerprint": "assign-4",
            "semantic_review_status": "pass",
        },
        {
            "candidate_id": "representation-e",
            "stage_id": "representation",
            "champion_parent_id": "hdbscan-d",
            "changed_parameter_family": "representation",
            "analysis_unit": "post",
            "embedding_model": "encoder-b",
            "umap_config": json.dumps({"n_neighbors": 15}),
            "hdbscan_config": json.dumps(
                {
                    "min_cluster_size": 30,
                    "min_samples": 10,
                    "cluster_selection_method": "eom",
                }
            ),
            "representation_config": json.dumps({"vectorizer": "phrases"}),
            "taxonomy_config": json.dumps({"snapshot": "raw"}),
            "assignment_fingerprint": "assign-4",
            "semantic_review_status": "pass",
        },
    ]


def valid_trace():
    return {
        "study_id": "semantic-study",
        "assurance_level": "research",
        "baseline_candidate_id": "baseline-a",
        "current_champion_id": "representation-e",
        "stages": [
            {
                "stage_id": "analysis_unit",
                "status": "skipped",
                "champion_before": "baseline-a",
                "candidate_ids": [],
                "changed_parameter_family": "analysis_unit",
                "semantic_review_artifact": "",
                "metric_artifacts": [],
                "decision": "retain",
                "promoted_candidate_id": "",
                "champion_after": "baseline-a",
                "decision_reason": "",
                "skip_reason": "The registered units already match the research claim.",
            },
            {
                "stage_id": "embedding",
                "status": "completed",
                "champion_before": "baseline-a",
                "candidate_ids": ["embedding-b"],
                "changed_parameter_family": "embedding",
                "semantic_review_artifact": "semantic-review-embedding.json",
                "metric_artifacts": ["metrics-embedding.json"],
                "decision": "promote",
                "promoted_candidate_id": "embedding-b",
                "champion_after": "embedding-b",
                "decision_reason": "Clearer meaning boundaries in original texts.",
                "skip_reason": "",
            },
            {
                "stage_id": "umap",
                "status": "completed",
                "champion_before": "embedding-b",
                "candidate_ids": ["umap-c"],
                "changed_parameter_family": "umap",
                "semantic_review_artifact": "semantic-review-umap.json",
                "metric_artifacts": ["metrics-umap.json"],
                "decision": "retain",
                "promoted_candidate_id": "",
                "champion_after": "embedding-b",
                "decision_reason": "The challenger blurred two substantive boundaries.",
                "skip_reason": "",
            },
            {
                "stage_id": "hdbscan_min_cluster_size",
                "status": "completed",
                "champion_before": "embedding-b",
                "candidate_ids": ["hdbscan-d"],
                "changed_parameter_family": "hdbscan_min_cluster_size",
                "semantic_review_artifact": "semantic-review-hdbscan.json",
                "metric_artifacts": ["metrics-hdbscan.json"],
                "decision": "promote",
                "promoted_candidate_id": "hdbscan-d",
                "champion_after": "hdbscan-d",
                "decision_reason": "Removed a repeated artifact without losing a theme.",
                "skip_reason": "",
            },
            {
                "stage_id": "hdbscan_min_samples",
                "status": "skipped",
                "champion_before": "hdbscan-d",
                "candidate_ids": [],
                "changed_parameter_family": "hdbscan_min_samples",
                "semantic_review_artifact": "",
                "metric_artifacts": [],
                "decision": "retain",
                "promoted_candidate_id": "",
                "champion_after": "hdbscan-d",
                "decision_reason": "",
                "skip_reason": "No unresolved density-conservatism signal.",
            },
            {
                "stage_id": "hdbscan_selection_method",
                "status": "skipped",
                "champion_before": "hdbscan-d",
                "candidate_ids": [],
                "changed_parameter_family": "hdbscan_selection_method",
                "semantic_review_artifact": "",
                "metric_artifacts": [],
                "decision": "retain",
                "promoted_candidate_id": "",
                "champion_after": "hdbscan-d",
                "decision_reason": "",
                "skip_reason": "No unresolved granularity signal.",
            },
            {
                "stage_id": "representation",
                "status": "completed",
                "champion_before": "hdbscan-d",
                "candidate_ids": ["representation-e"],
                "changed_parameter_family": "representation",
                "semantic_review_artifact": "semantic-review-representation.json",
                "metric_artifacts": ["metrics-representation.json"],
                "decision": "promote",
                "promoted_candidate_id": "representation-e",
                "champion_after": "representation-e",
                "decision_reason": "Labels improved under identical assignments.",
                "skip_reason": "",
            },
            {
                "stage_id": "taxonomy",
                "status": "skipped",
                "champion_before": "representation-e",
                "candidate_ids": [],
                "changed_parameter_family": "taxonomy",
                "semantic_review_artifact": "",
                "metric_artifacts": [],
                "decision": "retain",
                "promoted_candidate_id": "",
                "champion_after": "representation-e",
                "decision_reason": "",
                "skip_reason": "No reviewed merge or split remained unresolved.",
            },
        ],
        "interaction_confirmation": {
            "required": False,
            "diagnostic_triggers": [],
            "allowed_parameter_families": [],
            "candidate_generation_rule": "",
            "candidate_ids": [],
            "semantic_review_artifact": "",
            "decision": "retain",
            "promoted_candidate_id": "",
            "decision_reason": "No material interaction signal remained.",
        },
    }


class BehaviorFixtureTests(unittest.TestCase):
    def test_pressure_scenarios_and_red_baseline_are_complete(self):
        scenarios = json.loads(
            (FIXTURES_DIR / "skill-behavior-scenarios.json").read_text(
                encoding="utf-8"
            )
        )
        baseline = json.loads(
            (FIXTURES_DIR / "skill-behavior-baseline.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(scenarios), 5)
        self.assertEqual(
            {item["scenario_id"] for item in scenarios},
            {item["scenario_id"] for item in baseline},
        )
        failures = {
            item["scenario_id"]: item["observed_failures"] for item in baseline
        }
        self.assertTrue(failures["exploratory-baseline-must-run"])
        self.assertTrue(failures["high-cosine-different-meaning"])
        self.assertTrue(failures["different-words-same-meaning"])
        self.assertTrue(failures["cumulative-champion-path"])
        self.assertEqual(failures["publication-stays-strict"], [])

    def test_pressure_scenarios_pass_after_semantic_first_rewrite(self):
        scenarios = json.loads(
            (FIXTURES_DIR / "skill-behavior-scenarios.json").read_text(
                encoding="utf-8"
            )
        )
        green = json.loads(
            (FIXTURES_DIR / "skill-behavior-green.json").read_text(
                encoding="utf-8"
            )
        )

        scenario_ids = {item["scenario_id"] for item in scenarios}
        self.assertEqual(scenario_ids, {item["scenario_id"] for item in green})
        self.assertTrue(all(item["pass"] is True for item in green))
        self.assertTrue(
            all(
                item["capture_method"]
                == "deterministic_instruction_contract_due_to_runtime_no_subagents"
                for item in green
            )
        )
        self.assertTrue(all(item["observed_behavior"].strip() for item in green))
        self.assertTrue(all(item["supporting_rules"] for item in green))


class AssurancePolicyTests(unittest.TestCase):
    def policy(self):
        return load_module("workflow_policy")

    def test_exploratory_mode_does_not_require_publication_bundle(self):
        required = self.policy().required_artifacts(
            "exploratory",
            progressive_coverage_claim=False,
            visualization_enabled=False,
        )
        self.assertIn("tuning-trace.json", required)
        self.assertIn("semantic-review.json", required)
        self.assertNotIn("corpus-reading-ledger.csv", required)
        self.assertNotIn("visualization-manifest.json", required)

    def test_publication_release_retains_full_gate(self):
        required = self.policy().required_artifacts(
            "publication_release",
            progressive_coverage_claim=True,
            visualization_enabled=True,
        )
        self.assertIn("modeling-authorization.json", required)
        self.assertIn("corpus-reading-ledger.csv", required)
        self.assertIn("human-topic-audit.csv", required)
        self.assertIn("visualization-manifest.json", required)

    def test_contract_enforces_claim_scope_provenance_and_authorization(self):
        contract = {
            "assurance_level": "exploratory",
            "claim_scope": "research",
            "authorization_basis": "user_request",
            "provisional_defaults": {
                "used": True,
                "provenance": [],
                "permitted_for_final_selection": False,
            },
            "semantic_review_policy": {
                "algorithmic_metrics_role": "triage_only",
                "original_text_required": True,
                "review_stage_winners": True,
                "review_all_finalists": True,
            },
            "cumulative_tuning_policy": {
                "one_parameter_family_per_main_stage": True,
                "carry_forward_champion": True,
                "rollback_rejected_change": True,
                "bounded_interaction_confirmation": True,
            },
        }
        errors = self.policy().validate_assurance_contract(contract)
        self.assertTrue(any("claim_scope" in item for item in errors))
        self.assertTrue(any("provenance" in item for item in errors))

        publication = deepcopy(contract)
        publication["assurance_level"] = "publication_release"
        publication["claim_scope"] = "publication_release"
        publication["authorization_basis"] = "user_request"
        publication["provisional_defaults"]["used"] = False
        errors = self.policy().validate_assurance_contract(publication)
        self.assertTrue(any("explicit_preview_approval" in item for item in errors))

    def test_missing_level_uses_legacy_strict_policy_with_warning(self):
        result = self.policy().resolve_assurance_level({})
        self.assertEqual(result["assurance_level"], "publication_release")
        self.assertTrue(result["legacy_strict"])
        self.assertTrue(result["warnings"])

    def test_reconnaissance_gate_depends_on_assurance_level(self):
        module = load_module("validate_theme_reconnaissance")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            exploratory = module.validate_reconnaissance_for_level(
                root,
                "exploratory",
                progressive_coverage_claim=False,
            )
            self.assertTrue(exploratory["valid"], exploratory["errors"])
            self.assertFalse(exploratory["approval_required"])

            research = module.validate_reconnaissance_for_level(
                root,
                "research",
                progressive_coverage_claim=False,
            )
            self.assertFalse(research["valid"])
            self.assertTrue(
                any("theme-reconnaissance.json" in item for item in research["errors"])
            )

            publication = module.validate_reconnaissance_for_level(
                root,
                "publication_release",
                progressive_coverage_claim=True,
            )
            self.assertFalse(publication["valid"])
            self.assertTrue(publication["approval_required"])

    def test_research_concise_reconnaissance_cannot_be_an_empty_object(self):
        module = load_module("validate_theme_reconnaissance")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "theme-reconnaissance.json").write_text(
                "{}\n", encoding="utf-8"
            )
            result = module.validate_reconnaissance_for_level(
                root,
                "research",
                progressive_coverage_claim=False,
            )
            self.assertFalse(result["valid"])
            self.assertTrue(
                any("research_question" in item for item in result["errors"]),
                result["errors"],
            )
            self.assertTrue(
                any("candidate_themes" in item for item in result["errors"]),
                result["errors"],
            )

    def test_research_progressive_coverage_needs_ledger_not_release_approval(self):
        module = load_module("validate_theme_reconnaissance")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            reconnaissance = {
                "schema_version": 1,
                "study_id": "research-progressive",
                "research_question": "What meanings appear in the corpus?",
                "route": "network-short",
                "review_scope": "concise_research_theme_map",
                "candidate_themes": [
                    {
                        "candidate_id": "eligibility",
                        "definition": "Entry-condition checks.",
                        "evidence_unit_ids": ["u-1"],
                    }
                ],
                "limitations": ["Coverage is bounded by the registered ledger."],
            }
            (root / "theme-reconnaissance.json").write_text(
                json.dumps(reconnaissance), encoding="utf-8"
            )
            reading_plan = {
                "reading_plan_id": "research-plan",
                "corpus_fingerprint": "sha256:research-progressive",
                "route": "network-short",
                "mode": "progressive_extraction",
                "selection": {
                    "selection_channels": sorted(
                        module.PROGRESSIVE_SELECTION_CHANNELS
                    )
                },
                "stopping": {
                    "estimand": "candidate-theme stabilization",
                    "rule": "stop under the registered local evidence rule",
                    "status": "calibrated",
                },
                "residual_risk": "Rare implicit meanings may remain.",
            }
            (root / "corpus-reading-plan.json").write_text(
                json.dumps(reading_plan), encoding="utf-8"
            )
            ledger_row = {field: "" for field in module.LEDGER_FIELDS}
            ledger_row.update(
                {
                    "reading_plan_id": "research-plan",
                    "unit_id": "u-1",
                    "route_subset": "network-short",
                    "source_group": "source-1",
                    "time_group": "time-1",
                    "language_group": "zh",
                    "length_group": "short",
                    "duplicate_group_id": "duplicate-1",
                    "content_sha256": "sha256:" + "0" * 64,
                    "content_length": "12",
                    "canonical_unit_id": "u-1",
                    "selection_channels": "|".join(
                        sorted(module.PROGRESSIVE_SELECTION_CHANNELS)
                    ),
                    "holdout_role": "none",
                    "review_depth": "full_text",
                    "candidate_theme_ids": "eligibility",
                    "review_notes": "Original text was reviewed.",
                }
            )
            with (root / "corpus-reading-ledger.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.DictWriter(
                    handle, fieldnames=sorted(module.LEDGER_FIELDS)
                )
                writer.writeheader()
                writer.writerow(ledger_row)

            result = module.validate_reconnaissance_for_level(
                root,
                "research",
                progressive_coverage_claim=True,
            )
            self.assertTrue(result["valid"], result["errors"])
            self.assertFalse(result["approval_required"])


class SemanticReviewTests(unittest.TestCase):
    def evidence(self):
        topic_payload = {
            "topics": [
                {
                    "topic_uid": "topic-a",
                    "representative_unit_ids": ["u1"],
                    "boundary_unit_ids": ["u2"],
                },
                {
                    "topic_uid": "topic-b",
                    "representative_unit_ids": ["u3"],
                    "random_unit_ids": ["u4"],
                },
                {
                    "topic_uid": "topic-c",
                    "representative_unit_ids": ["u5"],
                },
            ],
            "outlier_unit_ids": ["u6"],
        }
        units = [
            {
                "unit_id": "u1",
                "display_text": "申请补贴必须满足本地户籍和收入门槛。",
                "source_id": "s1",
                "duplicate_group_id": "d1",
            },
            {
                "unit_id": "u2",
                "display_text": "资格材料需要经过审核。",
                "source_id": "s2",
                "duplicate_group_id": "d2",
            },
            {
                "unit_id": "u3",
                "display_text": "补贴领取后只能在指定商户使用。",
                "source_id": "s3",
                "duplicate_group_id": "d3",
            },
            {
                "unit_id": "u4",
                "display_text": "到账资金存在消费范围限制。",
                "source_id": "s4",
                "duplicate_group_id": "d4",
            },
            {
                "unit_id": "u5",
                "display_text": "系统核验申请人的准入条件。",
                "source_id": "s5",
                "duplicate_group_id": "d5",
            },
            {
                "unit_id": "u6",
                "display_text": "模板页脚与来源水印。",
                "source_id": "s6",
                "duplicate_group_id": "d6",
            },
        ]
        assignments = [
            {"unit_id": row["unit_id"], "topic_uid": f"topic-{letter}"}
            for row, letter in zip(units[:5], ["a", "a", "b", "b", "c"])
        ] + [{"unit_id": "u6", "topic_uid": "-1"}]
        scorecard = {
            "most_semantically_similar_pairs": [
                {
                    "topic_a": "topic-a",
                    "topic_b": "topic-b",
                    "cosine_similarity": 0.96,
                }
            ],
            "most_lexically_overlapping_pairs": [
                {"topic_a": "topic-a", "topic_b": "topic-c", "rbo": 0.03}
            ],
        }
        return topic_payload, units, assignments, scorecard

    def test_queue_contains_original_text_but_no_semantic_verdict(self):
        module = load_module("build_semantic_review_queue")
        queue = module.build_review_queue(
            *self.evidence(),
            candidate_id="candidate-semantic-test",
            route="network-short",
        )
        pair = next(
            item
            for item in queue["pair_reviews"]
            if {item["topic_uid_a"], item["topic_uid_b"]}
            == {"topic-a", "topic-b"}
        )
        self.assertEqual(pair["algorithmic_signal_role"], "review_trigger_only")
        self.assertNotIn("relationship", pair)
        self.assertTrue(pair["evidence_units"])
        self.assertIn("display_text", pair["evidence_units"][0])
        serialized = json.dumps(queue, ensure_ascii=False)
        self.assertNotIn('"semantic_verdict"', serialized)

    def test_queue_cli_writes_lf_terminated_output_for_byte_stable_examples(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "topics.json").write_text(
                json.dumps(
                    {
                        "topics": [
                            {
                                "topic_uid": "topic-a",
                                "representative_unit_ids": ["u1"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (root / "units.csv").write_text(
                "unit_id,display_text,source_id,duplicate_group_id\n"
                "u1,Eligibility evidence,s1,d1\n",
                encoding="utf-8",
            )
            (root / "assignments.csv").write_text(
                "unit_id,topic_uid\nu1,topic-a\n",
                encoding="utf-8",
            )
            (root / "scorecard.json").write_text("{}", encoding="utf-8")
            output = root / "semantic-review-queue.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "build_semantic_review_queue.py"),
                    "--topics",
                    str(root / "topics.json"),
                    "--units",
                    str(root / "units.csv"),
                    "--assignments",
                    str(root / "assignments.csv"),
                    "--scorecard",
                    str(root / "scorecard.json"),
                    "--candidate-id",
                    "candidate-a",
                    "--route",
                    "network-short",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            output_bytes = output.read_bytes()
            self.assertNotIn(b"\r\n", output_bytes)
            self.assertTrue(output_bytes.endswith(b"\n"))

    def test_missing_evidence_id_fails(self):
        module = load_module("build_semantic_review_queue")
        topic_payload, units, assignments, scorecard = self.evidence()
        topic_payload["topics"][0]["representative_unit_ids"] = ["missing-unit"]
        with self.assertRaisesRegex(ValueError, "missing-unit"):
            module.build_review_queue(
                topic_payload,
                units,
                assignments,
                scorecard,
                candidate_id="candidate-semantic-test",
                route="network-short",
            )

    def test_semantic_review_schema_requires_meaning_and_pair_reason(self):
        module = load_module("build_semantic_review_queue")
        review = {
            "topic_cards": [
                {
                    "topic_uid": "topic-a",
                    "evidence_unit_ids": ["u1"],
                    "meaning": {
                        "object": "申请资格",
                        "claim_action_or_function": "审核准入条件",
                        "context": "补贴申请",
                        "stance_or_perspective": "申请人",
                    },
                    "label": "补贴资格审核",
                    "definition": "围绕申请前准入条件的审查。",
                    "inclusion_rules": ["资格条件"],
                    "exclusion_rules": ["领取后使用范围"],
                    "boundary_clarity": "clear",
                    "artifact_status": "substantive",
                    "counter_evidence": "没有发现使用限制内容。",
                }
            ],
            "pair_decisions": [
                {
                    "topic_uid_a": "topic-a",
                    "topic_uid_b": "topic-b",
                    "evidence_unit_ids": ["u1", "u3"],
                    "relationship": "distinct",
                    "meaning_difference": "申请前资格与领取后使用约束不同。",
                    "decision_reason": "对象所处阶段与行为功能均不同。",
                    "unresolved": False,
                }
            ],
            "coverage_decisions": [],
            "unresolved_issues": [],
        }
        errors = module.validate_semantic_review(
            review,
            required_topic_uids={"topic-a"},
            required_pair_ids={("topic-a", "topic-b")},
        )
        self.assertEqual(errors, [])

        for field in ("evidence_unit_ids", "inclusion_rules", "exclusion_rules"):
            with self.subTest(field=field):
                invalid = deepcopy(review)
                invalid["topic_cards"][0][field] = []
                errors = module.validate_semantic_review(
                    invalid,
                    required_topic_uids={"topic-a"},
                    required_pair_ids={("topic-a", "topic-b")},
                )
                self.assertTrue(any(field in item for item in errors), errors)

        invalid_pair = deepcopy(review)
        invalid_pair["pair_decisions"][0]["evidence_unit_ids"] = []
        errors = module.validate_semantic_review(
            invalid_pair,
            required_topic_uids={"topic-a"},
            required_pair_ids={("topic-a", "topic-b")},
        )
        self.assertTrue(any("evidence_unit_ids" in item for item in errors), errors)

        empty_review = {
            "topic_cards": [],
            "pair_decisions": [],
            "unresolved_issues": [],
        }
        errors = module.validate_semantic_review(
            empty_review,
            required_topic_uids=set(),
            required_pair_ids=set(),
        )
        self.assertTrue(any("at least one" in item for item in errors), errors)


class CumulativeTuningTests(unittest.TestCase):
    def test_valid_chain_promotes_and_rolls_back(self):
        module = load_module("validate_tuning_trace")
        result = module.validate_tuning_trace(
            valid_trace(), registry_rows(), assurance_level="research"
        )
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["current_champion_id"], "representation-e")
        self.assertEqual(
            result["completed_stages"],
            [
                "embedding",
                "umap",
                "hdbscan_min_cluster_size",
                "representation",
            ],
        )

    def test_rejected_candidate_cannot_become_next_parent(self):
        module = load_module("validate_tuning_trace")
        trace = valid_trace()
        trace["stages"][3]["champion_before"] = "umap-c"
        result = module.validate_tuning_trace(
            trace, registry_rows(), assurance_level="research"
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("current champion" in item for item in result["errors"]))

    def test_main_stage_cannot_change_two_families(self):
        module = load_module("validate_tuning_trace")
        rows = registry_rows()
        candidate = next(row for row in rows if row["candidate_id"] == "umap-c")
        candidate["hdbscan_config"] = json.dumps(
            {
                "min_cluster_size": 25,
                "min_samples": 10,
                "cluster_selection_method": "eom",
            }
        )
        result = module.validate_tuning_trace(
            valid_trace(), rows, assurance_level="research"
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("more than" in item for item in result["errors"]))

    def test_representation_promotion_requires_identical_assignments(self):
        module = load_module("validate_tuning_trace")
        rows = registry_rows()
        candidate = next(
            row for row in rows if row["candidate_id"] == "representation-e"
        )
        candidate["assignment_fingerprint"] = "changed"
        result = module.validate_tuning_trace(
            valid_trace(), rows, assurance_level="research"
        )
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("assignment fingerprint" in item for item in result["errors"])
        )

    def test_interaction_confirmation_must_be_triggered_and_bounded(self):
        module = load_module("validate_tuning_trace")
        trace = valid_trace()
        trace["interaction_confirmation"] = {
            "required": True,
            "diagnostic_triggers": [],
            "allowed_parameter_families": ["umap", "hdbscan_min_samples"],
            "candidate_generation_rule": "full Cartesian grid",
            "candidate_ids": ["interaction-x"],
            "semantic_review_artifact": "",
            "decision": "retain",
            "promoted_candidate_id": "",
            "decision_reason": "",
        }
        result = module.validate_tuning_trace(
            trace, registry_rows(), assurance_level="research"
        )
        self.assertFalse(result["valid"])
        self.assertTrue(any("diagnostic trigger" in item for item in result["errors"]))
        self.assertTrue(any("Cartesian" in item for item in result["errors"]))

    def test_research_trace_cannot_omit_a_main_stage_record(self):
        module = load_module("validate_tuning_trace")
        trace = valid_trace()
        trace["stages"] = [
            stage for stage in trace["stages"] if stage["stage_id"] != "taxonomy"
        ]
        result = module.validate_tuning_trace(
            trace, registry_rows(), assurance_level="research"
        )
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("Missing main stage record: taxonomy" in item for item in result["errors"])
        )

    def test_research_trace_cannot_finalize_with_a_pending_main_stage(self):
        module = load_module("validate_tuning_trace")
        trace = valid_trace()
        pending = next(
            stage for stage in trace["stages"] if stage["stage_id"] == "taxonomy"
        )
        pending["status"] = "pending"
        pending["decision"] = ""
        pending["skip_reason"] = ""
        result = module.validate_tuning_trace(
            trace, registry_rows(), assurance_level="research"
        )
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("pending" in item and "taxonomy" in item for item in result["errors"]),
            result["errors"],
        )

    def test_interaction_candidate_must_exist_and_change_only_allowed_families(self):
        module = load_module("validate_tuning_trace")
        trace = valid_trace()
        trace["interaction_confirmation"] = {
            "required": True,
            "diagnostic_triggers": [
                "UMAP neighborhood change alters the density boundary."
            ],
            "allowed_parameter_families": [
                "umap",
                "hdbscan_min_samples",
            ],
            "candidate_generation_rule": (
                "Generate only candidates that resolve the registered "
                "neighborhood-density ambiguity, then stop."
            ),
            "candidate_ids": ["interaction-missing"],
            "semantic_review_artifact": "semantic-review-interaction.json",
            "decision": "retain",
            "promoted_candidate_id": "",
            "decision_reason": "No semantic improvement.",
        }
        result = module.validate_tuning_trace(
            trace, registry_rows(), assurance_level="research"
        )
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("absent from registry" in item for item in result["errors"])
        )


class SemanticSelectionTests(unittest.TestCase):
    def test_semantic_failure_is_ineligible_before_pareto(self):
        module = load_module("select_pareto")
        rows = [
            {
                "candidate_id": "candidate-a",
                "irbo": "0.95",
                "stability": "0.95",
                "coherence": "0.8",
                "semantic_review_status": "fail",
            },
            {
                "candidate_id": "candidate-b",
                "irbo": "0.80",
                "stability": "0.85",
                "coherence": "0.7",
                "semantic_review_status": "pass",
            },
        ]
        result = module.select_pareto(
            rows,
            objectives={"irbo": "max", "stability": "max"},
            constraints=["coherence>=0.5"],
            required_fields={"semantic_review_status": "pass"},
        )
        self.assertNotIn("candidate-a", result["frontier_ids"])
        self.assertIn("candidate-a", result["ineligible_ids"])
        self.assertIn("candidate-b", result["frontier_ids"])
        self.assertFalse(result["promotion_decision_produced"])

    def test_champion_deltas_do_not_auto_promote_a_tie(self):
        module = load_module("select_pareto")
        rows = [
            {
                "candidate_id": "champion",
                "irbo": "0.8",
                "stability": "0.9",
                "semantic_review_status": "pass",
            },
            {
                "candidate_id": "tie",
                "irbo": "0.8",
                "stability": "0.9",
                "semantic_review_status": "pass",
            },
        ]
        result = module.select_pareto(
            rows,
            objectives={"irbo": "max", "stability": "max"},
            required_fields={"semantic_review_status": "pass"},
            champion_id="champion",
        )
        self.assertEqual(
            result["deltas_from_champion"]["tie"],
            {"irbo": 0.0, "stability": 0.0},
        )
        self.assertFalse(result["promotion_decision_produced"])

    def test_diversity_scorecard_declares_triage_role(self):
        module = load_module("evaluate_diversity")
        result = module.evaluate_topics(
            {
                "topics": [
                    {
                        "topic_id": "a",
                        "keywords": ["申请", "资格"],
                        "embedding": [1.0, 0.0],
                    },
                    {
                        "topic_id": "b",
                        "keywords": ["使用", "限制"],
                        "embedding": [0.9, 0.1],
                    },
                ]
            },
            top_k=2,
            rbo_p=0.9,
        )
        self.assertEqual(result["decision_role"], "diagnostic_triage_only")
        self.assertFalse(result["semantic_verdict_produced"])
        self.assertTrue(result["requires_original_text_review"])


class RouteSemanticTests(unittest.TestCase):
    def test_network_short_evidence_spans_dependence_groups(self):
        module = load_module("build_semantic_review_queue")
        queue = {
            "topic_reviews": [
                {
                    "topic_uid": "topic-a",
                    "evidence_units": [
                        {
                            "unit_id": "u1",
                            "source_id": "s1",
                            "duplicate_group_id": "d1",
                        },
                        {
                            "unit_id": "u2",
                            "source_id": "s2",
                            "duplicate_group_id": "d2",
                        },
                    ],
                }
            ]
        }
        self.assertEqual(
            module.validate_route_evidence(queue, route="network-short"), []
        )

    def test_long_document_evidence_requires_parent_ids(self):
        module = load_module("build_semantic_review_queue")
        queue = {
            "topic_reviews": [
                {
                    "topic_uid": "topic-a",
                    "claims_cross_document_support": True,
                    "evidence_units": [
                        {"unit_id": "u1", "display_text": "片段一"},
                        {
                            "unit_id": "u2",
                            "display_text": "片段二",
                            "parent_document_id": "p2",
                        },
                    ],
                }
            ]
        }
        errors = module.validate_route_evidence(queue, route="long-document")
        self.assertTrue(any("parent_document_id" in item for item in errors))

    def test_mixed_route_requires_both_subsets_and_applies_each_rule(self):
        module = load_module("build_semantic_review_queue")
        valid_queue = {
            "topic_reviews": [
                {
                    "topic_uid": "topic-a",
                    "evidence_units": [
                        {
                            "unit_id": "u1",
                            "route": "network-short",
                            "source_id": "s1",
                            "duplicate_group_id": "d1",
                        },
                        {
                            "unit_id": "u2",
                            "route": "long-document",
                            "parent_document_id": "p1",
                        },
                        {
                            "unit_id": "u3",
                            "route": "network-short",
                            "source_id": "s2",
                            "duplicate_group_id": "d2",
                        },
                    ],
                }
            ]
        }
        self.assertEqual(
            module.validate_route_evidence(valid_queue, route="mixed"), []
        )

        invalid_queue = deepcopy(valid_queue)
        invalid_queue["topic_reviews"][0]["evidence_units"] = [
            invalid_queue["topic_reviews"][0]["evidence_units"][0]
        ]
        errors = module.validate_route_evidence(invalid_queue, route="mixed")
        self.assertTrue(any("both route subsets" in item for item in errors))


class VisualizationPolicyTests(unittest.TestCase):
    def test_figure_requirements_scale_by_assurance(self):
        module = load_module("build_visualization_plan")
        self.assertEqual(
            module.figure_requirement(
                "document-map",
                assurance_level="exploratory",
                enabled_modules=set(),
            ),
            "optional",
        )
        self.assertEqual(
            module.figure_requirement(
                "document-map",
                assurance_level="research",
                enabled_modules={"document-map"},
            ),
            "required",
        )
        self.assertEqual(
            module.figure_requirement(
                "document-map",
                assurance_level="publication_release",
                enabled_modules=set(),
            ),
            "required",
        )


class DecisionIntegrityTests(unittest.TestCase):
    def semantic_review(self):
        return {
            "candidate_id": "representation-e",
            "topic_cards": [
                {
                    "topic_uid": "topic-a",
                    "evidence_unit_ids": ["u1"],
                    "meaning": {
                        "object": "资格",
                        "claim_action_or_function": "审核",
                        "context": "申请",
                        "stance_or_perspective": "申请人",
                    },
                    "label": "资格审核",
                    "definition": "申请前的准入审查。",
                    "inclusion_rules": ["申请条件"],
                    "exclusion_rules": ["资金使用"],
                    "boundary_clarity": "clear",
                    "artifact_status": "substantive",
                    "counter_evidence": "",
                }
            ],
            "pair_decisions": [],
            "coverage_decisions": [],
            "unresolved_issues": [],
        }

    def candidate_rows(self):
        return [
            {
                "candidate_id": "representation-e",
                "semantic_review_status": "pass",
                "unresolved_semantic_decisions": "0",
                "irbo": "0.8",
                "stability": "0.9",
            }
        ]

    def test_selected_model_must_equal_final_champion(self):
        module = load_module("validate_study_bundle")
        selected = {
            "candidate_id": "wrong-model",
            "assurance_level": "research",
            "selection_objectives": {"irbo": "max", "stability": "max"},
            "selection_constraints": [],
            "semantic_required_fields": {"semantic_review_status": "pass"},
            "eligible_pareto_frontier": ["representation-e"],
        }
        errors = module.validate_semantic_selection_links(
            selected,
            valid_trace(),
            self.semantic_review(),
            self.candidate_rows(),
        )
        self.assertTrue(any("current champion" in item for item in errors))

    def test_unresolved_semantic_issue_blocks_selection(self):
        module = load_module("validate_study_bundle")
        review = self.semantic_review()
        review["unresolved_issues"] = ["topic-a boundary"]
        selected = {
            "candidate_id": "representation-e",
            "assurance_level": "research",
            "selection_objectives": {"irbo": "max", "stability": "max"},
            "selection_constraints": [],
            "semantic_required_fields": {"semantic_review_status": "pass"},
            "eligible_pareto_frontier": ["representation-e"],
        }
        errors = module.validate_semantic_selection_links(
            selected, valid_trace(), review, self.candidate_rows()
        )
        self.assertTrue(any("unresolved" in item for item in errors))


class AssuranceBundleTests(unittest.TestCase):
    def validator(self):
        return load_module("validate_study_bundle")

    def test_exploratory_fixture_passes_without_publication_artifacts(self):
        root = FIXTURES_DIR / "exploratory-study-bundle"
        result = self.validator().validate_bundle(root)
        self.assertTrue(result["valid"], result["errors"])
        self.assertFalse((root / "corpus-reading-ledger.csv").exists())
        self.assertFalse((root / "visualization-manifest.json").exists())
        self.assertFalse((root / "selected-model.json").exists())

    def test_research_fixture_passes_with_semantic_champion_links(self):
        root = FIXTURES_DIR / "research-study-bundle"
        result = self.validator().validate_bundle(root)
        self.assertTrue(result["valid"], result["errors"])
        self.assertTrue((root / "selected-model.json").is_file())
        self.assertTrue((root / "semantic-review.json").is_file())
        self.assertFalse((root / "visualization-manifest.json").exists())

    def test_publication_fixture_retains_strict_bundle_and_new_links(self):
        root = FIXTURES_DIR / "lexicon-study-bundle"
        contract = json.loads(
            (root / "study-contract.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["assurance_level"], "publication_release")
        self.assertTrue((root / "tuning-trace.json").is_file())
        self.assertTrue((root / "semantic-review.json").is_file())
        result = self.validator().validate_bundle(root)
        self.assertTrue(result["valid"], result["errors"])

    def test_publication_bundle_rejects_invalid_visualization_manifest(self):
        source = FIXTURES_DIR / "lexicon-study-bundle"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "bundle"
            import shutil

            shutil.copytree(source, root)
            manifest_path = root / "visualization-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["plan_id"] = "tampered-plan"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            result = self.validator().validate_bundle(root)
            self.assertFalse(result["valid"])
            self.assertTrue(
                any("Visualization bundle:" in item for item in result["errors"])
            )

    def test_exploratory_claim_cannot_be_relabelled_as_research(self):
        source = FIXTURES_DIR / "exploratory-study-bundle"
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "bundle"
            import shutil

            shutil.copytree(source, root)
            contract_path = root / "study-contract.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["claim_scope"] = "research"
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            result = self.validator().validate_bundle(root)
            self.assertFalse(result["valid"])
            self.assertTrue(
                any("claim_scope" in item for item in result["errors"])
            )


class DocumentationIntegrationTests(unittest.TestCase):
    def test_skill_uses_semantic_first_cumulative_order(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        reference_path = (
            SKILL_ROOT / "references" / "semantic-review-and-cumulative-tuning.md"
        )
        self.assertTrue(reference_path.is_file())
        reference = reference_path.read_text(encoding="utf-8")
        self.assertLess(skill.index("Choose the assurance level"), skill.index("Route the corpus"))
        self.assertIn("original text is authoritative", skill.casefold())
        self.assertIn("diagnostic triage only", skill.casefold())
        self.assertIn("current champion", skill.casefold())
        self.assertIn("champion parent", reference.casefold())
        self.assertIn("rollback", reference.casefold())
        self.assertIn("interaction_confirmation", reference)
        self.assertIn("Cartesian grid", reference)

    def test_main_stage_order_is_complete_and_stable(self):
        reference = (
            SKILL_ROOT / "references" / "semantic-review-and-cumulative-tuning.md"
        ).read_text(encoding="utf-8")
        stage_ids = [
            "analysis_unit",
            "embedding",
            "umap",
            "hdbscan_min_cluster_size",
            "hdbscan_min_samples",
            "hdbscan_selection_method",
            "representation",
            "taxonomy",
        ]
        positions = [reference.index(stage) for stage in stage_ids]
        self.assertEqual(positions, sorted(positions))
        self.assertNotRegex(
            reference,
            r"(?i)always use exactly \d+|fixed \d+ candidates|exactly \d+ seeds",
        )

    def test_publication_full_bundle_is_conditional(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("publication_release", skill)
        self.assertIn("exploratory", skill)
        self.assertIn("research", skill)
        self.assertNotIn(
            "Do not fit a baseline or any BERTopic candidate before corpus-scale",
            skill,
        )

    def test_contract_template_does_not_hard_code_publication_reconnaissance(self):
        contract = json.loads(
            (SKILL_ROOT / "assets" / "study-contract.json").read_text(
                encoding="utf-8"
            )
        )
        policy = contract["pre_model_reconnaissance"]
        self.assertEqual(policy["requirement_basis"], "assurance_level")
        self.assertFalse(policy["required_by_level"]["exploratory"])
        self.assertEqual(
            policy["required_by_level"]["research"],
            "when_claim_depends_on_progressive_coverage",
        )
        self.assertTrue(policy["required_by_level"]["publication_release"])
        self.assertEqual(
            policy["authorization_by_level"]["exploratory"], "user_request"
        )
        self.assertEqual(
            policy["authorization_by_level"]["publication_release"],
            "explicit_preview_approval",
        )
        self.assertNotIn("required", policy)
        self.assertNotIn("user_authorization_required", policy)


if __name__ == "__main__":
    unittest.main()
