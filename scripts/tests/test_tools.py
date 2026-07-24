import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from align_snapshots import align_snapshots  # noqa: E402
from evaluate_diversity import evaluate_topics  # noqa: E402
from lexicon_tools import compile_lexicon_bundle  # noqa: E402
from select_pareto import select_pareto  # noqa: E402
from validate_theme_reconnaissance import (  # noqa: E402
    compute_pre_model_artifact_fingerprint,
)
from validate_study_bundle import (  # noqa: E402
    validate_bundle,
    validate_lexicon_governance,
    validate_lexicon_sources,
    validate_parameter_governance,
    validate_visualization_policy,
)


class DiversityEvaluationTests(unittest.TestCase):
    def test_repeated_topics_are_not_mistaken_for_diversity(self):
        payload = {
            "topics": [
                {
                    "topic_id": "A",
                    "keywords": ["疫苗", "接种", "免疫"],
                    "embedding": [1.0, 0.0],
                    "size": 60,
                },
                {
                    "topic_id": "B",
                    "keywords": ["疫苗", "接种", "免疫"],
                    "embedding": [1.0, 0.0],
                    "size": 40,
                },
            ]
        }

        result = evaluate_topics(
            payload,
            top_k=3,
            rbo_p=0.9,
            semantic_redundancy_threshold=0.95,
        )

        self.assertAlmostEqual(result["topic_diversity"], 0.5)
        self.assertAlmostEqual(result["mean_pairwise_irbo"], 0.0)
        self.assertAlmostEqual(result["semantic_diversity_median"], 0.0)
        self.assertAlmostEqual(result["semantic_redundancy_fraction"], 1.0)

    def test_lexically_and_semantically_distinct_topics_score_as_distinct(self):
        payload = {
            "topics": [
                {
                    "topic_id": "A",
                    "keywords": ["疫苗", "接种", "免疫"],
                    "embedding": [1.0, 0.0],
                    "size": 50,
                },
                {
                    "topic_id": "B",
                    "keywords": ["住房", "租金", "保障房"],
                    "embedding": [0.0, 1.0],
                    "size": 50,
                },
            ]
        }

        result = evaluate_topics(
            payload,
            top_k=3,
            rbo_p=0.9,
            semantic_redundancy_threshold=0.95,
        )

        self.assertAlmostEqual(result["topic_diversity"], 1.0)
        self.assertAlmostEqual(result["mean_pairwise_irbo"], 1.0)
        self.assertAlmostEqual(result["semantic_diversity_median"], 1.0)
        self.assertAlmostEqual(result["effective_topic_count"], 2.0)

    def test_missing_embeddings_are_reported_not_silently_scored(self):
        payload = {
            "topics": [
                {"topic_id": "A", "keywords": ["甲", "乙"]},
                {"topic_id": "B", "keywords": ["丙", "丁"]},
            ]
        }
        result = evaluate_topics(payload, top_k=2, rbo_p=0.9)
        self.assertIsNone(result["semantic_diversity_median"])
        self.assertTrue(any("embedding" in warning for warning in result["warnings"]))

    def test_concept_normalization_prevents_synonym_fragmentation(self):
        payload = {
            "topics": [
                {"topic_id": "A", "keywords": ["AI", "创新", "的"]},
                {"topic_id": "B", "keywords": ["人工智能", "创新", "应用"]},
            ]
        }

        result = evaluate_topics(
            payload,
            top_k=3,
            rbo_p=0.9,
            keyword_aliases={"AI": "人工智能"},
            excluded_keywords={"的"},
        )

        self.assertIn("concept_normalized", result)
        self.assertLess(
            result["concept_normalized"]["topic_diversity"],
            result["topic_diversity"],
        )

    def test_empty_frozen_lexicon_still_emits_concept_scorecard(self):
        payload = {
            "topics": [
                {"topic_id": "A", "keywords": ["甲", "乙"]},
                {"topic_id": "B", "keywords": ["丙", "丁"]},
            ]
        }

        result = evaluate_topics(
            payload,
            top_k=2,
            rbo_p=0.9,
            keyword_aliases={},
            excluded_keywords=set(),
        )

        self.assertIn("concept_normalized", result)
        self.assertEqual(
            result["concept_normalized"]["topic_diversity"],
            result["topic_diversity"],
        )


class ParetoSelectionTests(unittest.TestCase):
    def test_constraints_filter_and_frontier_preserves_tradeoffs(self):
        rows = [
            {
                "candidate_id": "A",
                "irbo": "0.80",
                "semantic_diversity": "0.85",
                "stability": "0.70",
                "coherence": "0.60",
                "outlier_fraction": "0.20",
            },
            {
                "candidate_id": "B",
                "irbo": "0.90",
                "semantic_diversity": "0.75",
                "stability": "0.80",
                "coherence": "0.60",
                "outlier_fraction": "0.30",
            },
            {
                "candidate_id": "C",
                "irbo": "0.70",
                "semantic_diversity": "0.70",
                "stability": "0.50",
                "coherence": "0.55",
                "outlier_fraction": "0.05",
            },
            {
                "candidate_id": "D",
                "irbo": "0.99",
                "semantic_diversity": "0.99",
                "stability": "0.99",
                "coherence": "0.20",
                "outlier_fraction": "0.01",
            },
        ]

        result = select_pareto(
            rows,
            objectives={
                "irbo": "max",
                "semantic_diversity": "max",
                "stability": "max",
            },
            constraints=["coherence>=0.5"],
            id_field="candidate_id",
        )

        self.assertEqual(set(result["frontier_ids"]), {"A", "B"})
        self.assertEqual(result["ineligible_ids"], ["D"])
        self.assertEqual(result["dominated_ids"], ["C"])
        self.assertNotIn("outlier_fraction", result["objectives"])


class SnapshotAlignmentTests(unittest.TestCase):
    def test_one_to_one_topics_are_continued(self):
        old_topics = [
            {"topic_uid": "T-A", "embedding": [1.0, 0.0]},
            {"topic_uid": "T-B", "embedding": [0.0, 1.0]},
        ]
        new_topics = [
            {"topic_uid": "N-X", "embedding": [0.99, 0.01]},
            {"topic_uid": "N-Y", "embedding": [0.01, 0.99]},
        ]

        result = align_snapshots(
            old_topics,
            new_topics,
            thresholds={"semantic": 0.90},
        )

        pairs = {(row["old_topic_uid"], row["new_topic_uid"]) for row in result["continuity"]}
        self.assertEqual(pairs, {("T-A", "N-X"), ("T-B", "N-Y")})
        self.assertEqual(result["new_topics"], [])
        self.assertEqual(result["retired_topics"], [])

    def test_one_to_many_is_flagged_as_split_candidate(self):
        old_topics = [{"topic_uid": "T-A", "embedding": [1.0, 0.0]}]
        new_topics = [
            {"topic_uid": "N-X", "embedding": [1.0, 0.0]},
            {"topic_uid": "N-Y", "embedding": [0.98, 0.02]},
        ]

        result = align_snapshots(
            old_topics,
            new_topics,
            thresholds={"semantic": 0.95},
        )

        self.assertEqual(result["split_candidates"][0]["old_topic_uid"], "T-A")
        self.assertEqual(
            set(result["split_candidates"][0]["new_topic_uids"]),
            {"N-X", "N-Y"},
        )

    def test_keyword_alignment_can_use_a_frozen_synonym_map(self):
        old_topics = [
            {
                "topic_uid": "T-A",
                "embedding": [1.0, 0.0],
                "keywords": ["AI", "创新"],
            }
        ]
        new_topics = [
            {
                "topic_uid": "N-X",
                "embedding": [1.0, 0.0],
                "keywords": ["人工智能", "创新"],
            }
        ]

        result = align_snapshots(
            old_topics,
            new_topics,
            thresholds={"semantic": 0.9, "keyword": 0.9},
            keyword_rbo_p=0.9,
            keyword_aliases={"AI": "人工智能"},
        )

        self.assertEqual(len(result["continuity"]), 1)
        evidence = result["continuity"][0]
        self.assertLess(evidence["keyword_rbo_surface"], 0.9)
        self.assertAlmostEqual(evidence["keyword_rbo_canonical"], 1.0)


class StudyBundleValidationTests(unittest.TestCase):
    def test_visualization_policy_accepts_the_layered_research_contract(self):
        policy = {
            "required": True,
            "contract_artifact": "visualization-contract.json",
            "plan_artifact": "visualization-plan.json",
            "manifest_artifact": "visualization-manifest.json",
            "validation_command": (
                "python scripts/validate_visualization_bundle.py "
                "<study-bundle-directory>"
            ),
            "layer_model": [
                "structure",
                "representation",
                "taxonomy",
                "governance",
            ],
            "shared_document_coordinates_required": True,
            "topic_minus_one_visible": True,
        }

        self.assertEqual(validate_visualization_policy(policy), [])

    def test_visualization_policy_rejects_missing_layers_or_hidden_outliers(self):
        policy = {
            "required": True,
            "contract_artifact": "visualization-contract.json",
            "plan_artifact": "visualization-plan.json",
            "manifest_artifact": "visualization-manifest.json",
            "validation_command": (
                "python scripts/validate_visualization_bundle.py "
                "<study-bundle-directory>"
            ),
            "layer_model": ["structure", "representation", "taxonomy"],
            "shared_document_coordinates_required": False,
            "topic_minus_one_visible": False,
        }

        errors = validate_visualization_policy(policy)

        self.assertTrue(any("layer_model" in error for error in errors))
        self.assertTrue(
            any("shared_document_coordinates_required" in error for error in errors)
        )
        self.assertTrue(any("topic_minus_one_visible" in error for error in errors))

    def test_parameter_governance_rejects_parameter_copying(self):
        contract = {
            "paper_transfer_policy": "copy-paper-parameters",
            "calibration_plan": "use common values",
        }

        errors = validate_parameter_governance(contract)

        self.assertTrue(any("paper_transfer_policy" in item for item in errors))
        self.assertTrue(any("calibration_plan" in item for item in errors))

    def test_complete_bundle_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            contract = {
                "study_id": "study-001",
                "route": "network-short",
                "research_question": "发现可复现且彼此区分的公共议题",
                "analysis_unit": "post",
                "diversity_definition": ["lexical", "semantic", "coverage", "stability"],
                "minimum_meaningful_theme": {"basis": "domain_review", "value": "documented"},
                "calibration_plan": {
                    "unjustified_value_token": "pending_local_calibration",
                    "candidate_generation_policy": "adaptive-local-evidence",
                    "stop_rule_required": True,
                    "thresholds": [
                        {
                            "name": "semantic_redundancy_threshold",
                            "status": "calibrated",
                            "evidence_basis": "held-out labeled topic pairs",
                            "candidate_generation_rule": "add candidates only where the decision boundary is unresolved",
                            "stop_rule": "stop when the registered precision target is met",
                            "artifact": "semantic-threshold-audit.json",
                        }
                    ],
                },
                "validation_groups": ["account", "time"],
                "embedding_context_policy": "parent context for underspecified posts",
                "selection_policy": "pareto",
                "outlier_role": "diagnostic_guardrail_only",
                "paper_transfer_policy": "mechanisms-and-local-tests-not-parameters",
                "pre_model_reconnaissance": {
                    "required": True,
                    "user_theme_mode": "coverage_and_interpretation_anchor",
                    "allow_emergent_themes": True,
                    "reading_plan_artifact": "corpus-reading-plan.json",
                    "reading_ledger_artifact": "corpus-reading-ledger.csv",
                    "reconnaissance_artifact": "theme-reconnaissance.json",
                    "candidate_audit_artifact": "theme-candidate-audit.csv",
                    "authorization_artifact": "modeling-authorization.json",
                    "authorization_id": "auth-study-001",
                    "user_authorization_required": True,
                },
            }
            (root / "study-contract.json").write_text(
                json.dumps(contract, ensure_ascii=False), encoding="utf-8"
            )
            (root / "corpus-profile.json").write_text(
                json.dumps(
                    {
                        "corpus_fingerprint": "sha256:test",
                        "unit_count": 100,
                        "length_profile": {"tokenizer": "test-tokenizer"},
                        "group_fields": ["account", "time"],
                    }
                ),
                encoding="utf-8",
            )
            reconnaissance = {
                "schema_version": 1,
                "reconnaissance_id": "recon-study-001",
                "reading_plan_id": "read-plan-study-001",
                "corpus_fingerprint": "sha256:test",
                "route": "network-short",
                "created_at": "2026-07-21T12:00:00+08:00",
                "research_question": "发现可复现且彼此区分的公共议题",
                "user_theme": {
                    "mainline": "公共议题",
                    "mode": "coverage_and_interpretation_anchor",
                    "allow_emergent_themes": True,
                    "inclusion_intent": "公共议题及相关表达",
                    "exclusion_intent": "纯平台模板",
                },
                "coverage": {
                    "source_unit_count": 100,
                    "profiled_source_unit_count": 100,
                    "eligible_unit_count": 100,
                    "reviewed_unit_count": 100,
                    "full_text_reviewed_unit_count": 100,
                    "extracted_representation_reviewed_unit_count": 0,
                    "duplicate_inherited_unit_count": 0,
                    "unreviewed_unit_count": 0,
                    "excluded_unit_count": 0,
                    "failed_unit_count": 0,
                    "accounting_complete": True,
                    "full_text_review_complete": True,
                    "failed_unit_ids": [],
                    "exclusion_basis": "no exclusions",
                },
                "parent_document_coverage": {
                    "applicable": False,
                    "eligible_parent_document_count": None,
                    "profiled_parent_document_count": None,
                    "reviewed_parent_document_count": None,
                    "full_text_reviewed_parent_document_count": None,
                    "extracted_representation_reviewed_parent_document_count": None,
                    "duplicate_inherited_parent_document_count": None,
                    "unreviewed_parent_document_count": None,
                    "failed_parent_document_count": None,
                    "accounting_complete": False,
                    "full_text_review_complete": False,
                },
                "topic_count_estimate": {
                    "interpretation": "pre_model_hypothesis_not_target_k",
                    "coarse": {
                        "lower_bound": 1,
                        "point_estimate": 1,
                        "upper_bound": 1,
                        "candidate_theme_ids": ["PRE-C-001"],
                        "basis": "one broad public-issue family in the fixture",
                    },
                    "fine": {
                        "lower_bound": 1,
                        "point_estimate": 1,
                        "upper_bound": 2,
                        "candidate_theme_ids": ["PRE-F-001"],
                        "basis": "one supported issue with one unresolved split",
                    },
                },
                "unresolved_boundaries": ["PRE-F-001 may split with more evidence"],
                "excluded_artifact_candidate_ids": [],
                "strongest_counter_evidence": "the compact fixture limits granularity",
            }
            (root / "theme-reconnaissance.json").write_text(
                json.dumps(reconnaissance, ensure_ascii=False), encoding="utf-8"
            )
            raw_dir = root / "fixtures" / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            raw_payloads = {}
            registered_artifacts = []
            for index in range(1, 101):
                raw_bytes = f"study-fixture-unit-{index}".ljust(100, "_").encode(
                    "utf-8"
                )
                raw_payloads[index] = raw_bytes
                artifact_path = f"fixtures/raw/u{index}.txt"
                (root / artifact_path).write_bytes(raw_bytes)
                registered_artifacts.append(
                    {
                        "artifact_path": artifact_path,
                        "artifact_sha256": (
                            "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
                        ),
                    }
                )
            (root / "corpus-reading-plan.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "reading_plan_id": "read-plan-study-001",
                        "reconnaissance_id": "recon-study-001",
                        "corpus_fingerprint": "sha256:test",
                        "mode": "direct_full_text",
                        "decision_basis": {
                            "estimated_unique_full_text_tokens": 1000,
                            "usable_reconnaissance_tokens": 5000,
                            "time_budget": "fixture budget",
                            "direct_full_text_feasible": True,
                            "reason": "the complete fixture fits the budget",
                        },
                        "census": {
                            "ledger_artifact": "corpus-reading-ledger.csv",
                            "all_source_units_profiled": True,
                            "profile_fields": [
                                "unit_id",
                                "source",
                                "time",
                                "language",
                                "length",
                            ],
                            "exact_duplicate_policy": "inherit only exact content",
                            "near_duplicate_policy": "review independently",
                        },
                        "extraction": {
                            "streaming_or_batched": True,
                            "raw_text_preserved": True,
                            "unit_card_fields": ["unit_id", "raw_text"],
                            "registered_artifacts": registered_artifacts,
                            "short_text_policy": "read complete text",
                            "long_document_policy": "read all sections",
                            "card_size_basis": "no truncation in direct mode",
                        },
                        "selection": {
                            "stratification_fields": [
                                "source",
                                "time",
                                "language",
                                "length",
                            ],
                            "selection_channels": ["complete_unique_content"],
                            "candidate_generation_rule": "read every eligible unit",
                            "escalation_rule": "not applicable in complete review",
                        },
                        "stopping": {
                            "estimand": "complete eligible-content review",
                            "rule": "stop when every eligible unit is read",
                            "status": "satisfied",
                            "reconnaissance_state": "complete_for_preview",
                            "termination_basis": "complete_full_text_review",
                            "resource_budget_exhausted": False,
                            "holdout_audit_performed": False,
                            "holdout_unit_count": 0,
                            "new_candidate_theme_count": 0,
                            "material_change_detected": False,
                            "decision": "not_applicable_full_text",
                            "evidence": "all eligible units were read",
                        },
                        "residual_risk": "ordinary interpretation uncertainty",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with (root / "corpus-reading-ledger.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
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
                )
                for index in range(1, 101):
                    raw_bytes = raw_payloads[index]
                    content_sha256 = "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
                    writer.writerow(
                        [
                            "read-plan-study-001",
                            f"u{index}",
                            "",
                            "network-short",
                            f"source-{index % 3}",
                            "2026-Q3",
                            "zh",
                            "short",
                            "",
                            content_sha256,
                            len(raw_bytes),
                            "",
                            "complete_unique_content",
                            "none",
                            "full_text",
                            f"fixtures/raw/u{index}.txt",
                            f"record://u{index}",
                            0,
                            len(raw_bytes),
                            content_sha256,
                            "",
                            "",
                            "",
                            "",
                            "",
                            "PRE-C-001|PRE-F-001" if index <= 2 else "",
                            "reviewed fixture evidence",
                        ]
                    )
            with (root / "theme-candidate-audit.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
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
                )
                writer.writerows(
                    [
                        [
                            "recon-study-001",
                            "PRE-C-001",
                            "",
                            "coarse",
                            "network-short",
                            "公共议题",
                            "issue-family",
                            "mainline",
                            "公共事务相关表达",
                            "涉及公共议题",
                            "纯平台模板",
                            "multiple independent sources",
                            "u1|u2",
                            "source-a|source-b",
                            "low",
                            "compact fixture",
                            "false",
                            "semantic_evidence_only",
                            "accepted",
                            "按预估继续",
                        ],
                        [
                            "recon-study-001",
                            "PRE-F-001",
                            "PRE-C-001",
                            "fine",
                            "network-short",
                            "具体议题",
                            "subtheme",
                            "supporting",
                            "公共议题的具体表达",
                            "具体政策或服务表达",
                            "无实质内容的模板",
                            "multiple independent sources",
                            "u1|u2",
                            "source-a|source-b",
                            "low",
                            "possible split with more evidence",
                            "false",
                            "semantic_evidence_only",
                            "accepted",
                            "按预估继续",
                        ],
                    ]
                )
            (root / "modeling-authorization.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "authorization_id": "auth-study-001",
                        "reconnaissance_id": "recon-study-001",
                        "reading_plan_id": "read-plan-study-001",
                        "reading_mode": "direct_full_text",
                        "progressive_reading_risk_acknowledged": False,
                        "pre_model_artifact_fingerprint": (
                            compute_pre_model_artifact_fingerprint(root)
                        ),
                        "corpus_fingerprint": "sha256:test",
                        "gate_status": "approved_for_modeling",
                        "modeling_may_start": True,
                        "user_theme_mode": "coverage_and_interpretation_anchor",
                        "allow_emergent_themes": True,
                        "user_instruction": "按预估继续",
                        "resolved_candidate_theme_ids": [
                            "PRE-C-001",
                            "PRE-F-001",
                        ],
                        "decision_recorded_at": "2026-07-21T12:30:00+08:00",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (root / "selected-model.json").write_text(
                json.dumps({"candidate_id": "C-001"}), encoding="utf-8"
            )
            (root / "decision-report.md").write_text("# Decision\n\nEvidence-based.", encoding="utf-8")

            tables = {
                "experiment-registry.csv": (
                    [
                        "candidate_id",
                        "run_type",
                        "parent_snapshot_id",
                        "authorization_id",
                        "corpus_fingerprint",
                        "analysis_unit",
                        "embedding_model",
                        "umap_config",
                        "hdbscan_config",
                        "representation_config",
                        "status",
                    ],
                    ["C-001", "structural", "", "auth-study-001", "sha256:test", "post", "encoder", "{}", "{}", "{}", "selected"],
                ),
                "candidate-metrics.csv": (
                    [
                        "candidate_id",
                        "topic_count",
                        "td",
                        "irbo",
                        "semantic_diversity",
                        "coverage",
                        "stability",
                        "coherence",
                        "human_labelability",
                        "outlier_fraction",
                    ],
                    ["C-001", "2", "1", "1", "1", "0.8", "0.8", "0.7", "0.9", "0.2"],
                ),
                "topic-catalog.csv": (
                    [
                        "snapshot_id",
                        "topic_uid",
                        "local_topic_id",
                        "label",
                        "definition",
                        "inclusion",
                        "exclusion",
                        "size",
                        "representative_units",
                        "nearest_topic_uid",
                        "nearest_similarity",
                        "status",
                    ],
                    ["S-001", "T-001", "0", "议题", "定义", "包含", "排除", "10", "u1|u2", "T-002", "0.2", "active"],
                ),
                "topic-lineage.csv": (
                    [
                        "old_snapshot_id",
                        "old_topic_uid",
                        "new_snapshot_id",
                        "new_topic_uid",
                        "event_type",
                        "evidence",
                        "human_decision",
                    ],
                    None,
                ),
                "human-topic-audit.csv": (
                    [
                        "snapshot_id",
                        "topic_uid",
                        "sample_type",
                        "unit_id",
                        "relevance",
                        "coherence",
                        "distinctiveness",
                        "label_fit",
                        "notes",
                        "reviewer",
                    ],
                    ["S-001", "T-001", "random", "u1", "4", "4", "4", "4", "", "reviewer-1"],
                ),
                "topic-pair-audit.csv": (
                    [
                        "snapshot_id",
                        "topic_uid_a",
                        "topic_uid_b",
                        "lexical_overlap",
                        "semantic_similarity",
                        "definition_distinction",
                        "merge_decision",
                        "evidence",
                        "reviewer",
                    ],
                    ["S-001", "T-001", "T-002", "0.1", "0.2", "distinct", "keep_separate", "packet-1", "reviewer-1"],
                ),
                "missing-theme-audit.csv": (
                    [
                        "snapshot_id",
                        "sample_group",
                        "unit_id",
                        "reference_theme",
                        "matched_topic_uid",
                        "coverage_status",
                        "evidence",
                        "reviewer",
                    ],
                    ["S-001", "time-holdout", "u1", "议题", "T-001", "covered", "u1", "reviewer-1"],
                ),
                "evidence-log.csv": (
                    [
                        "citation",
                        "claim_used",
                        "evidence_type",
                        "scope_limit",
                        "accessed_on",
                    ],
                    ["doi:test", "方法依据", "paper", "示例", "2026-07-21"],
                ),
            }
            for name, (header, row) in tables.items():
                with (root / name).open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.writer(handle)
                    writer.writerow(header)
                    if row is not None:
                        writer.writerow(row)

            result = validate_bundle(root)
            self.assertTrue(result["valid"], result["errors"])

    def test_complete_lexicon_enabled_fixture_passes(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "lexicon-study-bundle"

        result = validate_bundle(fixture)

        self.assertTrue(result["valid"], result["errors"])

    def test_modeling_registry_rejects_mismatched_authorization(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "lexicon-study-bundle"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in fixture.iterdir():
                if source.is_file():
                    (root / source.name).write_bytes(source.read_bytes())
            registry = root / "experiment-registry.csv"
            with registry.open(
                "r", encoding="utf-8-sig", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0])
            rows[0]["authorization_id"] = "auth-wrong"
            with registry.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            result = validate_bundle(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("authorization_id" in error for error in result["errors"]),
                result["errors"],
            )

    def test_study_contract_must_bind_approved_authorization_id(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "lexicon-study-bundle"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in fixture.iterdir():
                if source.is_file():
                    (root / source.name).write_bytes(source.read_bytes())
            contract_path = root / "study-contract.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["pre_model_reconnaissance"]["authorization_id"] = "auth-wrong"
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False), encoding="utf-8"
            )

            result = validate_bundle(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "pre_model_reconnaissance.authorization_id does not match" in error
                    for error in result["errors"]
                ),
                result["errors"],
            )

    def test_mixed_route_inherits_long_document_contract_requirements(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "lexicon-study-bundle"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in fixture.iterdir():
                if source.is_file():
                    (root / source.name).write_bytes(source.read_bytes())
            contract_path = root / "study-contract.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["route"] = "mixed"
            contract["route_subsets"] = {
                "network-short": "posts",
                "long-document": "reports",
            }
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False), encoding="utf-8"
            )

            result = validate_bundle(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "Long-document route requires study-contract.json field: chunking_policy"
                    in error
                    for error in result["errors"]
                ),
                result["errors"],
            )

    def test_modeling_registry_rejects_missing_authorization(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "lexicon-study-bundle"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in fixture.iterdir():
                if source.is_file():
                    (root / source.name).write_bytes(source.read_bytes())
            registry = root / "experiment-registry.csv"
            with registry.open(
                "r", encoding="utf-8-sig", newline=""
            ) as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0])
            rows[0]["authorization_id"] = ""
            with registry.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            result = validate_bundle(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "modeling run lacks authorization_id" in error
                    for error in result["errors"]
                ),
                result["errors"],
            )

    def test_modeling_registry_rejects_mismatched_corpus_fingerprint(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "lexicon-study-bundle"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in fixture.iterdir():
                if source.is_file():
                    (root / source.name).write_bytes(source.read_bytes())
            registry = root / "experiment-registry.csv"
            with registry.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0])
            rows[0]["corpus_fingerprint"] = "sha256:wrong-corpus"
            with registry.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            result = validate_bundle(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("corpus_fingerprint" in error for error in result["errors"]),
                result["errors"],
            )

    def test_modeling_registry_rejects_unknown_run_type(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "lexicon-study-bundle"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in fixture.iterdir():
                if source.is_file():
                    (root / source.name).write_bytes(source.read_bytes())
            registry = root / "experiment-registry.csv"
            with registry.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
                fieldnames = list(rows[0])
            rows[0].update(run_type="mystery", authorization_id="")
            with registry.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            result = validate_bundle(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any("unknown run_type" in error for error in result["errors"]),
                result["errors"],
            )

    def test_study_contract_must_match_approved_research_question(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "lexicon-study-bundle"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for source in fixture.iterdir():
                if source.is_file():
                    (root / source.name).write_bytes(source.read_bytes())
            contract_path = root / "study-contract.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["research_question"] = "changed after reconnaissance approval"
            contract_path.write_text(
                json.dumps(contract, ensure_ascii=False), encoding="utf-8"
            )

            result = validate_bundle(root)

            self.assertFalse(result["valid"])
            self.assertTrue(
                any(
                    "research_question does not match the approved reconnaissance"
                    in error
                    for error in result["errors"]
                ),
                result["errors"],
            )

    def test_missing_contract_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_bundle(Path(tmp))
            self.assertFalse(result["valid"])
            self.assertTrue(any("study-contract.json" in item for item in result["errors"]))
            self.assertTrue(any("corpus-profile.json" in item for item in result["errors"]))
            self.assertTrue(any("topic-pair-audit.csv" in item for item in result["errors"]))
            self.assertTrue(any("missing-theme-audit.csv" in item for item in result["errors"]))

    def test_enabled_lexicon_policy_requires_iteration_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "study-contract.json").write_text(
                json.dumps(
                    {
                        "route": "network-short",
                        "lexicon_policy": {
                            "enabled": True,
                            "apply_to": "lexical_text",
                            "bundle_manifest": "lexicon-manifest.json",
                            "candidate_generation_rule": "rank all model-derived diagnostics for review",
                            "stop_rule": "stop when every candidate has a disposition",
                            "assignment_invariant_required": True,
                        },
                    }
                ),
                encoding="utf-8",
            )

            result = validate_bundle(root)

            for name in (
                "lexicon-config.json",
                "synonyms.csv",
                "stopwords.csv",
                "custom-terms.csv",
                "lexicon-manifest.json",
                "lexicon-candidate-audit.csv",
                "lexicon-lineage.csv",
                "representation-iteration.csv",
            ):
                self.assertTrue(
                    any(name in error for error in result["errors"]),
                    (name, result["errors"]),
                )

    def test_lexicon_governance_rejects_nonlexical_or_changed_assignments(self):
        contract = {
            "lexicon_policy": {
                "enabled": True,
                "apply_to": "embedding_text",
                "bundle_manifest": "lexicon-manifest.json",
                "candidate_generation_rule": "review diagnostics",
                "stop_rule": "all candidates adjudicated",
                "assignment_invariant_required": True,
            }
        }
        manifest = {
            "bundle_id": "lexicon-test",
            "content_sha256": "abc",
            "apply_to": "embedding_text",
            "conflicts": [],
        }
        iteration_rows = [
            {
                "lexicon_bundle_id": "lexicon-test",
                "assignment_fingerprint": "sha256:test",
                "assignment_unchanged": "false",
            }
        ]

        errors = validate_lexicon_governance(contract, manifest, iteration_rows)

        self.assertTrue(any("lexical_text" in error for error in errors))
        self.assertTrue(any("assignment_unchanged" in error for error in errors))

    def test_lexicon_governance_requires_registry_links(self):
        contract = {
            "lexicon_policy": {
                "enabled": True,
                "apply_to": "lexical_text",
                "bundle_manifest": "lexicon-manifest.json",
                "candidate_generation_rule": "review diagnostics",
                "stop_rule": "all candidates adjudicated",
                "assignment_invariant_required": True,
            }
        }
        manifest = {
            "bundle_id": "lexicon-test",
            "content_sha256": "abc",
            "apply_to": "lexical_text",
            "conflicts": [],
        }
        iteration_rows = [
            {
                "lexicon_bundle_id": "lexicon-test",
                "assignment_fingerprint": "sha256:test",
                "assignment_unchanged": "true",
            }
        ]

        errors = validate_lexicon_governance(
            contract,
            manifest,
            iteration_rows,
            registry_rows=[{"candidate_id": "R-1", "run_type": "representation"}],
        )

        self.assertTrue(any("representation_snapshot_id" in error for error in errors))
        self.assertTrue(any("lexicon_bundle_id" in error for error in errors))
        self.assertTrue(any("assignment_fingerprint" in error for error in errors))

    def test_lexicon_governance_links_iterations_without_rejecting_history(self):
        contract = {
            "lexicon_policy": {
                "enabled": True,
                "apply_to": "lexical_text",
                "bundle_manifest": "lexicon-manifest.json",
                "candidate_generation_rule": "review diagnostics",
                "stop_rule": "all candidates adjudicated",
                "assignment_invariant_required": True,
                "human_review_required": True,
            }
        }
        manifest = {
            "bundle_id": "lexicon-current",
            "content_sha256": "abc",
            "apply_to": "lexical_text",
            "conflicts": [],
        }
        iteration_rows = [
            {
                "candidate_id": "R-2",
                "representation_snapshot_id": "representation-current",
                "lexicon_bundle_id": "lexicon-current",
                "assignment_fingerprint": "sha256:current",
                "assignment_unchanged": "true",
                "surface_scorecard": "surface.json",
                "concept_scorecard": "concept.json",
                "human_labelability": "0.9",
                "pareto_status": "frontier",
                "decision": "selected",
                "decision_reason": "improved labels",
            }
        ]
        registry_rows = [
            {
                "candidate_id": "R-1",
                "run_type": "representation",
                "representation_snapshot_id": "representation-old",
                "lexicon_bundle_id": "lexicon-old",
                "assignment_fingerprint": "sha256:old",
            },
            {
                "candidate_id": "R-2",
                "run_type": "representation",
                "representation_snapshot_id": "representation-current",
                "lexicon_bundle_id": "lexicon-current",
                "assignment_fingerprint": "sha256:current",
            },
        ]

        errors = validate_lexicon_governance(
            contract, manifest, iteration_rows, registry_rows=registry_rows
        )

        self.assertEqual(errors, [])

    def test_lexicon_governance_rejects_unlinked_iteration(self):
        contract = {
            "lexicon_policy": {
                "enabled": True,
                "apply_to": "lexical_text",
                "bundle_manifest": "lexicon-manifest.json",
                "candidate_generation_rule": "review diagnostics",
                "stop_rule": "all candidates adjudicated",
                "assignment_invariant_required": True,
                "human_review_required": True,
            }
        }
        manifest = {
            "bundle_id": "lexicon-current",
            "content_sha256": "abc",
            "apply_to": "lexical_text",
            "conflicts": [],
        }
        iteration_rows = [
            {
                "candidate_id": "R-2",
                "representation_snapshot_id": "representation-current",
                "lexicon_bundle_id": "lexicon-current",
                "assignment_fingerprint": "sha256:current",
                "assignment_unchanged": "true",
                "surface_scorecard": "surface.json",
                "concept_scorecard": "concept.json",
                "human_labelability": "0.9",
                "pareto_status": "frontier",
                "decision": "selected",
                "decision_reason": "improved labels",
            }
        ]
        registry_rows = [
            {
                "candidate_id": "R-2",
                "run_type": "representation",
                "representation_snapshot_id": "different-snapshot",
                "lexicon_bundle_id": "lexicon-current",
                "assignment_fingerprint": "sha256:current",
            }
        ]

        errors = validate_lexicon_governance(
            contract, manifest, iteration_rows, registry_rows=registry_rows
        )

        self.assertTrue(any("matching representation registry row" in error for error in errors))

    def test_lexicon_source_tables_must_match_compiled_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = {
                "schema_version": 1,
                "bundle_name": "test",
                "parent_bundle_id": "",
                "apply_to": "lexical_text",
                "normalization": {
                    "unicode_form": None,
                    "casefold": False,
                    "collapse_whitespace": True,
                },
                "tokenizer": {"name": "fixture", "revision": "1"},
                "files": {
                    "synonyms": "synonyms.csv",
                    "stopwords": "stopwords.csv",
                    "custom_terms": "custom-terms.csv",
                },
            }
            (root / "lexicon-config.json").write_text(
                json.dumps(config, ensure_ascii=False), encoding="utf-8"
            )
            tables = {
                "synonyms.csv": [
                    ["canonical_term", "variant", "status", "source", "reason"],
                    ["人工智能", "AI", "active", "review", "alias"],
                ],
                "stopwords.csv": [["term", "status", "source", "reason"]],
                "custom-terms.csv": [
                    ["term", "display_form", "term_type", "status", "source", "reason"]
                ],
            }
            for name, rows in tables.items():
                with (root / name).open("w", encoding="utf-8", newline="") as handle:
                    csv.writer(handle).writerows(rows)
            manifest = compile_lexicon_bundle(root / "lexicon-config.json")
            with (root / "stopwords.csv").open("a", encoding="utf-8", newline="") as handle:
                csv.writer(handle).writerow(["平台", "active", "audit", "artifact"])

            errors = validate_lexicon_sources(root, manifest)

            self.assertTrue(any("does not match" in error for error in errors), errors)

    def test_lexicon_manifest_operational_content_must_match_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = {
                "schema_version": 1,
                "bundle_name": "test",
                "parent_bundle_id": "",
                "apply_to": "lexical_text",
                "normalization": {
                    "unicode_form": None,
                    "casefold": False,
                    "collapse_whitespace": True,
                },
                "tokenizer": {"name": "fixture", "revision": "1"},
                "files": {
                    "synonyms": "synonyms.csv",
                    "stopwords": "stopwords.csv",
                    "custom_terms": "custom-terms.csv",
                },
            }
            (root / "lexicon-config.json").write_text(
                json.dumps(config, ensure_ascii=False), encoding="utf-8"
            )
            tables = {
                "synonyms.csv": [
                    ["canonical_term", "variant", "status", "source", "reason"],
                    ["人工智能", "AI", "active", "review", "alias"],
                ],
                "stopwords.csv": [["term", "status", "source", "reason"]],
                "custom-terms.csv": [
                    ["term", "display_form", "term_type", "status", "source", "reason"]
                ],
            }
            for name, rows in tables.items():
                with (root / name).open("w", encoding="utf-8", newline="") as handle:
                    csv.writer(handle).writerows(rows)
            manifest = compile_lexicon_bundle(root / "lexicon-config.json")
            manifest["synonym_map"] = {"AI": "错误概念"}

            errors = validate_lexicon_sources(root, manifest)

            self.assertTrue(any("synonym_map" in error for error in errors), errors)

    def test_disabled_lexicon_policy_allows_empty_optional_iteration_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (root / "representation-iteration.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.writer(handle)
                writer.writerow(
                    [
                        "candidate_id",
                        "parent_representation_snapshot_id",
                        "representation_snapshot_id",
                        "lexicon_bundle_id",
                        "assignment_fingerprint",
                        "assignment_unchanged",
                        "surface_scorecard",
                        "concept_scorecard",
                        "human_labelability",
                        "pareto_status",
                        "decision",
                        "decision_reason",
                    ]
                )

            result = validate_bundle(root)

            self.assertFalse(
                any(
                    error == "representation-iteration.csv must contain at least one evidence row"
                    for error in result["errors"]
                ),
                result["errors"],
            )


class SkillInstructionTests(unittest.TestCase):
    def test_skill_identity_matches_bertopic_tuning(self):
        skill_root = Path(__file__).resolve().parents[2]
        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        try:
            openai_yaml = (skill_root / "agents" / "openai.yaml").read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError as exc:
            self.fail(f"agents/openai.yaml must be UTF-8: {exc}")

        self.assertEqual(skill_root.name, "bertopic-tuning")
        self.assertIn("\nname: bertopic-tuning\n", skill_text)
        self.assertIn('# BERTopic Tuning', skill_text)
        self.assertIn('display_name: "BERTopic Tuning"', openai_yaml)
        self.assertIn("$bertopic-tuning", openai_yaml)
        self.assertNotIn("academic-bertopic-tuning", skill_text + openai_yaml)

    def test_hashed_text_resources_use_stable_line_endings(self):
        skill_root = Path(__file__).resolve().parents[2]
        attributes_path = skill_root / ".gitattributes"
        if attributes_path.is_file():
            attributes = attributes_path.read_text(encoding="utf-8")
            self.assertIn("*.csv text eol=lf", attributes)
            self.assertIn("*.json text eol=lf", attributes)
        for relative in (
            "assets/lexicon-config.json",
            "assets/synonyms.csv",
            "assets/stopwords.csv",
            "assets/custom-terms.csv",
            "assets/corpus-reading-plan.json",
            "assets/corpus-reading-ledger.csv",
            "assets/theme-reconnaissance.json",
            "assets/theme-candidate-audit.csv",
            "assets/modeling-authorization.json",
            "assets/visualization-contract.json",
            "assets/visualization-manifest.json",
        ):
            self.assertNotIn(b"\r\n", (skill_root / relative).read_bytes(), relative)

    def test_theme_reconnaissance_assets_have_auditable_schemas(self):
        skill_root = Path(__file__).resolve().parents[2]
        asset_root = skill_root / "assets"

        reconnaissance = json.loads(
            (asset_root / "theme-reconnaissance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(reconnaissance["schema_version"], 1)
        self.assertEqual(
            reconnaissance["user_theme"]["mode"],
            "coverage_and_interpretation_anchor",
        )
        self.assertTrue(reconnaissance["user_theme"]["allow_emergent_themes"])
        self.assertIn("coverage", reconnaissance)
        self.assertIn("reading_plan_id", reconnaissance)
        self.assertIn("profiled_source_unit_count", reconnaissance["coverage"])
        self.assertIn("full_text_reviewed_unit_count", reconnaissance["coverage"])
        self.assertIn(
            "extracted_representation_reviewed_unit_count",
            reconnaissance["coverage"],
        )
        self.assertIn("unreviewed_unit_count", reconnaissance["coverage"])
        self.assertIn("coarse", reconnaissance["topic_count_estimate"])
        self.assertIn("fine", reconnaissance["topic_count_estimate"])

        reading_plan = json.loads(
            (asset_root / "corpus-reading-plan.json").read_text(encoding="utf-8")
        )
        self.assertEqual(reading_plan["schema_version"], 1)
        self.assertIn("mode", reading_plan)
        self.assertIn("selection_channels", reading_plan["selection"])
        self.assertIn("holdout_audit_performed", reading_plan["stopping"])
        self.assertIn("material_change_detected", reading_plan["stopping"])
        self.assertIn("reconnaissance_state", reading_plan["stopping"])
        self.assertIn("termination_basis", reading_plan["stopping"])
        self.assertIn("resource_budget_exhausted", reading_plan["stopping"])
        self.assertIn("registered_artifacts", reading_plan["extraction"])

        with (asset_root / "corpus-reading-ledger.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            ledger_header = set(next(csv.reader(handle)))
        self.assertTrue(
            {
                "reading_plan_id",
                "unit_id",
                "selection_channels",
                "holdout_role",
                "review_depth",
                "content_sha256",
                "content_length",
                "extraction_artifact",
                "extraction_locator",
                "span_start",
                "span_end",
                "extraction_sha256",
            }.issubset(ledger_header)
        )

        with (asset_root / "theme-candidate-audit.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            header = set(next(csv.reader(handle)))
        required = {
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
        }
        self.assertTrue(required.issubset(header), required.difference(header))

        authorization = json.loads(
            (asset_root / "modeling-authorization.json").read_text(encoding="utf-8")
        )
        self.assertEqual(authorization["gate_status"], "awaiting_user_direction")
        self.assertFalse(authorization["modeling_may_start"])
        self.assertIn("reading_plan_id", authorization)
        self.assertIn("reading_mode", authorization)
        self.assertIn("pre_model_artifact_fingerprint", authorization)
        self.assertFalse(authorization["progressive_reading_risk_acknowledged"])
        self.assertEqual(
            authorization["user_theme_mode"],
            "coverage_and_interpretation_anchor",
        )

        contract = json.loads(
            (asset_root / "study-contract.json").read_text(encoding="utf-8")
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
        self.assertEqual(
            policy["authorization_artifact"], "modeling-authorization.json"
        )
        self.assertEqual(
            policy["reading_plan_artifact"], "corpus-reading-plan.json"
        )
        self.assertEqual(
            policy["reading_ledger_artifact"], "corpus-reading-ledger.csv"
        )
        self.assertIn("authorization_id", policy)

        with (asset_root / "experiment-registry.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as handle:
            registry_header = set(next(csv.reader(handle)))
        self.assertIn("authorization_id", registry_header)

    def test_corpus_scale_reconnaissance_is_integrated_and_guarded(self):
        skill_root = Path(__file__).resolve().parents[2]
        required_text = {
            "SKILL.md": "references/publication-release-workflow.md",
            "references/publication-release-workflow.md": "awaiting_user_direction",
            "references/corpus-theme-reconnaissance.md": (
                "Assurance routing"
            ),
            "references/scalable-corpus-reading.md": "probability_holdout",
            "references/network-short-text.md": "duplicate_inherited_unit_count",
            "references/long-document.md": "parent_document_coverage",
            "references/study-contract-and-reporting.md": (
                "modeling-authorization.json"
            ),
            "references/bertopic-implementation.md": "approved_for_modeling",
            "agents/openai.yaml": "语义优先",
        }
        for relative, needle in required_text.items():
            path = skill_root / relative
            self.assertTrue(path.is_file(), relative)
            self.assertIn(needle, path.read_text(encoding="utf-8"), relative)

        repository_readme = skill_root / "README.md"
        if repository_readme.is_file():
            self.assertIn(
                "validate_theme_reconnaissance.py",
                repository_readme.read_text(encoding="utf-8"),
            )

        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        assurance_position = skill_text.index("Choose the assurance level")
        baseline_position = skill_text.index("Establish the baseline champion")
        self.assertLess(assurance_position, baseline_position)
        self.assertIn("do not impose a second approval ritual", skill_text)
        self.assertIn("explicit preview", skill_text)
        self.assertNotIn(
            "Do not fit a baseline or any BERTopic candidate before corpus-scale",
            skill_text,
        )

    def test_parameter_transfer_firewall_is_explicit(self):
        skill_root = Path(__file__).resolve().parents[2]
        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        short_text = (skill_root / "references" / "network-short-text.md").read_text(
            encoding="utf-8"
        )
        diversity_text = (
            skill_root / "references" / "diversity-evaluation.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Do not invent operational numbers", skill_text)
        self.assertIn("pending_local_calibration", skill_text)
        self.assertIn("Do not emit a fixed multiplier grid", short_text)
        self.assertIn("not a mandatory shortlist", short_text)
        self.assertIn("Do not prescribe a universal reviewer count", diversity_text)
        self.assertIn("one parameter family", skill_text)
        self.assertNotIn("probe below, at and above", skill_text)

    def test_lexicon_iteration_workflow_is_discoverable_and_guarded(self):
        skill_root = Path(__file__).resolve().parents[2]
        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        lexicon_reference = skill_root / "references" / "lexicon-management-and-iteration.md"

        self.assertIn("synonym", skill_text.split("---", 2)[1].casefold())
        self.assertIn("stopword", skill_text.split("---", 2)[1].casefold())
        self.assertIn("references/lexicon-management-and-iteration.md", skill_text)
        self.assertTrue(lexicon_reference.is_file())
        reference_text = lexicon_reference.read_text(encoding="utf-8")
        self.assertIn("scripts/build_lexicon_bundle.py", reference_text)
        self.assertIn("scripts/evaluate_representation_update.py", reference_text)
        self.assertIn("phrase protection", reference_text)
        self.assertIn("synonym canonicalization", reference_text)
        self.assertIn("stopword filtering", reference_text)
        self.assertIn("closed vocabulary", reference_text)
        self.assertIn("assignments_unchanged", reference_text)

    def test_lexicon_asset_templates_have_auditable_schemas(self):
        skill_root = Path(__file__).resolve().parents[2]
        asset_root = skill_root / "assets"
        expected_headers = {
            "synonyms.csv": {"canonical_term", "variant", "status", "source", "reason"},
            "stopwords.csv": {"term", "status", "source", "reason"},
            "custom-terms.csv": {
                "term",
                "display_form",
                "term_type",
                "status",
                "source",
                "reason",
            },
            "lexicon-candidate-audit.csv": {
                "candidate_id",
                "candidate_type",
                "term",
                "evidence",
                "status",
                "decision_reason",
                "reviewer",
            },
            "lexicon-lineage.csv": {
                "old_bundle_id",
                "new_bundle_id",
                "change_type",
                "term",
                "human_decision",
            },
            "representation-iteration.csv": {
                "candidate_id",
                "representation_snapshot_id",
                "lexicon_bundle_id",
                "assignment_fingerprint",
                "assignment_unchanged",
                "decision",
            },
        }
        for name, required in expected_headers.items():
            with (asset_root / name).open("r", encoding="utf-8-sig", newline="") as handle:
                header = set(next(csv.reader(handle)))
            self.assertTrue(required.issubset(header), (name, required.difference(header)))

        config = json.loads((asset_root / "lexicon-config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["apply_to"], "lexical_text")
        contract = json.loads((asset_root / "study-contract.json").read_text(encoding="utf-8"))
        self.assertIn("lexicon_policy", contract)
        self.assertTrue(contract["lexicon_policy"]["assignment_invariant_required"])

        extended_headers = {
            "experiment-registry.csv": {
                "representation_snapshot_id",
                "lexicon_bundle_id",
                "assignment_fingerprint",
            },
            "candidate-metrics.csv": {
                "concept_td",
                "concept_irbo",
                "stopword_leakage",
                "synonym_residual",
                "custom_term_recovery",
            },
            "topic-catalog.csv": {"representation_snapshot_id", "lexicon_bundle_id"},
        }
        for name, required in extended_headers.items():
            with (asset_root / name).open("r", encoding="utf-8-sig", newline="") as handle:
                header = set(next(csv.reader(handle)))
            self.assertTrue(required.issubset(header), (name, required.difference(header)))

        decision_report = (asset_root / "decision-report.md").read_text(encoding="utf-8")
        self.assertIn("Lexicon resources and representation iteration", decision_report)

    def test_lexicon_feature_is_integrated_across_routes_and_handoff(self):
        skill_root = Path(__file__).resolve().parents[2]
        required_text = {
            "references/network-short-text.md": "lexicon bundle",
            "references/long-document.md": "lexicon bundle",
            "references/diversity-evaluation.md": "concept-normalized",
            "references/bertopic-implementation.md": "build_count_vectorizer",
            "references/iteration-and-lineage.md": "lexicon lineage",
            "references/study-contract-and-reporting.md": "lexicon-manifest.json",
            "agents/openai.yaml": "同义词",
        }
        for relative, needle in required_text.items():
            content = (skill_root / relative).read_text(encoding="utf-8")
            self.assertIn(needle, content, relative)
        repository_only_text = {
            "README.md": "build_lexicon_bundle.py",
            "HANDOFF.md": "evaluate_representation_update.py",
        }
        for relative, needle in repository_only_text.items():
            path = skill_root / relative
            if path.is_file():
                self.assertIn(needle, path.read_text(encoding="utf-8"), relative)


if __name__ == "__main__":
    unittest.main()
