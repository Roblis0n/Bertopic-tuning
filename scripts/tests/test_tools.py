import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from align_snapshots import align_snapshots  # noqa: E402
from evaluate_diversity import evaluate_topics  # noqa: E402
from select_pareto import select_pareto  # noqa: E402
from validate_study_bundle import (  # noqa: E402
    validate_bundle,
    validate_parameter_governance,
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


class StudyBundleValidationTests(unittest.TestCase):
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
                        "corpus_fingerprint",
                        "analysis_unit",
                        "embedding_model",
                        "umap_config",
                        "hdbscan_config",
                        "representation_config",
                        "status",
                    ],
                    ["C-001", "structural", "", "sha256:test", "post", "encoder", "{}", "{}", "{}", "selected"],
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

    def test_missing_contract_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_bundle(Path(tmp))
            self.assertFalse(result["valid"])
            self.assertTrue(any("study-contract.json" in item for item in result["errors"]))
            self.assertTrue(any("corpus-profile.json" in item for item in result["errors"]))
            self.assertTrue(any("topic-pair-audit.csv" in item for item in result["errors"]))
            self.assertTrue(any("missing-theme-audit.csv" in item for item in result["errors"]))


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
        self.assertIn(
            "--keyword-rbo-p <registered-p-when-keyword-gate-is-used>", skill_text
        )
        self.assertNotIn("probe below, at and above", skill_text)


if __name__ == "__main__":
    unittest.main()
