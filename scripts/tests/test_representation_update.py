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

from evaluate_representation_update import evaluate_representation_update  # noqa: E402


class RepresentationUpdateTests(unittest.TestCase):
    def _manifest(self, *, custom_terms=None):
        canonical = {
            "schema_version": 1,
            "bundle_name": "test",
            "parent_bundle_id": "",
            "apply_to": "lexical_text",
            "normalization": {
                "unicode_form": None,
                "casefold": False,
                "collapse_whitespace": True,
            },
            "tokenizer": {"name": "test-tokenizer", "revision": "fixture"},
            "synonyms": [
                {
                    "variant": "AI",
                    "canonical_term": "人工智能",
                    "source": "test",
                    "reason": "alias",
                }
            ],
            "stopwords": [{"term": "的"}],
            "custom_terms": custom_terms or [{"term": "消费券"}],
        }
        content_sha256 = hashlib.sha256(
            json.dumps(
                canonical,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return {
            **canonical,
            "bundle_id": f"lexicon-{content_sha256[:16]}",
            "content_sha256": content_sha256,
            "synonym_map": {"AI": "人工智能"},
            "source_files": [],
            "counts": {
                "synonyms": 1,
                "stopwords": 1,
                "custom_terms": len(canonical["custom_terms"]),
            },
            "conflicts": [],
        }

    def _topics(self):
        before = {
            "topics": [
                {
                    "topic_id": "T-A",
                    "keywords": ["AI", "的", "创新"],
                    "embedding": [1.0, 0.0],
                    "size": 2,
                },
                {
                    "topic_id": "T-B",
                    "keywords": ["补贴", "消费", "创新"],
                    "embedding": [0.0, 1.0],
                    "size": 1,
                },
            ]
        }
        after = {
            "topics": [
                {
                    "topic_id": "T-A",
                    "keywords": ["人工智能", "创新", "消费券"],
                    "embedding": [1.0, 0.0],
                    "size": 2,
                },
                {
                    "topic_id": "T-B",
                    "keywords": ["补贴", "消费券", "创新"],
                    "embedding": [0.0, 1.0],
                    "size": 1,
                },
            ]
        }
        return before, after

    def test_reports_lexicon_effects_under_frozen_assignments(self):
        before, after = self._topics()
        assignments = [
            {"unit_id": "u-1", "topic_id": "T-A"},
            {"unit_id": "u-2", "topic_id": "T-A"},
            {"unit_id": "u-3", "topic_id": "T-B"},
        ]

        result = evaluate_representation_update(
            before,
            after,
            assignments,
            list(reversed(assignments)),
            self._manifest(),
            top_k=3,
            rbo_p=0.9,
        )

        self.assertTrue(result["structural_invariants"]["assignments_unchanged"])
        self.assertTrue(result["structural_invariants"]["topic_ids_unchanged"])
        self.assertEqual(result["lexicon_diagnostics"]["stopword_leakage_before"], 1)
        self.assertEqual(result["lexicon_diagnostics"]["stopword_leakage_after"], 0)
        self.assertEqual(result["lexicon_diagnostics"]["synonym_variants_after"], [])
        self.assertEqual(result["lexicon_diagnostics"]["custom_terms_recovered"], ["消费券"])
        self.assertIn("surface", result["scorecards"])
        self.assertIn("concept_normalized", result["scorecards"])
        self.assertIsNone(
            result["scorecards"]["surface"]["after"]["semantic_diversity_median"]
        )
        self.assertEqual(
            result["scorecards"]["structural_metrics_policy"],
            "carry_forward_unchanged",
        )
        self.assertTrue(
            any(
                row["candidate_type"] == "cross_topic_term"
                and row["term"] == "创新"
                for row in result["lexicon_candidates"]
            )
        )

    def test_custom_synonym_variant_is_recovered_as_its_canonical_term(self):
        before, after = self._topics()
        manifest = self._manifest(custom_terms=[{"term": "AI"}])
        assignments = [{"unit_id": "u-1", "topic_id": "T-A"}]

        result = evaluate_representation_update(
            before,
            after,
            assignments,
            assignments,
            manifest,
            top_k=3,
            rbo_p=0.9,
        )

        self.assertEqual(
            result["lexicon_diagnostics"]["custom_terms_recovered"], ["人工智能"]
        )
        self.assertEqual(result["lexicon_diagnostics"]["custom_terms_missing"], [])

    def test_rejects_changed_assignments(self):
        before, after = self._topics()
        before_assignments = [{"unit_id": "u-1", "topic_id": "T-A"}]
        after_assignments = [{"unit_id": "u-1", "topic_id": "T-B"}]

        with self.assertRaisesRegex(ValueError, "assignments changed"):
            evaluate_representation_update(
                before,
                after,
                before_assignments,
                after_assignments,
                self._manifest(),
                top_k=3,
                rbo_p=0.9,
            )

    def test_rejects_changed_topic_identity_set(self):
        before, after = self._topics()
        after["topics"][1]["topic_id"] = "T-C"
        assignments = [{"unit_id": "u-1", "topic_id": "T-A"}]

        with self.assertRaisesRegex(ValueError, "topic identifiers changed"):
            evaluate_representation_update(
                before,
                after,
                assignments,
                assignments,
                self._manifest(),
                top_k=3,
                rbo_p=0.9,
            )

    def test_rejects_changed_local_topic_id_under_a_stable_topic_uid(self):
        before, after = self._topics()
        for topic, uid in zip(before["topics"], ("U-A", "U-B")):
            topic["topic_uid"] = uid
            topic["local_topic_id"] = topic["topic_id"]
        for topic, uid in zip(after["topics"], ("U-A", "U-B")):
            topic["topic_uid"] = uid
            topic["local_topic_id"] = topic["topic_id"]
        after["topics"][1]["local_topic_id"] = "changed-local-id"
        assignments = [{"unit_id": "u-1", "topic_uid": "U-A"}]

        with self.assertRaisesRegex(ValueError, "local topic identifiers changed"):
            evaluate_representation_update(
                before,
                after,
                assignments,
                assignments,
                self._manifest(),
                top_k=3,
                rbo_p=0.9,
            )

    def test_rejects_assignment_topic_absent_from_the_topic_catalog(self):
        before, after = self._topics()
        assignments = [{"unit_id": "u-1", "topic_id": "T-MISSING"}]

        with self.assertRaisesRegex(ValueError, "absent from the topic catalog"):
            evaluate_representation_update(
                before,
                after,
                assignments,
                assignments,
                self._manifest(),
                top_k=3,
                rbo_p=0.9,
            )

    def test_cli_writes_scorecard_and_candidate_audit(self):
        before, after = self._topics()
        assignments = [
            {"unit_id": "u-1", "topic_id": "T-A"},
            {"unit_id": "u-2", "topic_id": "T-B"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {
                "before": root / "before.json",
                "after": root / "after.json",
                "manifest": root / "manifest.json",
                "before_assignments": root / "before-assignments.csv",
                "after_assignments": root / "after-assignments.csv",
                "output": root / "comparison.json",
                "candidates": root / "lexicon-candidates.csv",
            }
            paths["before"].write_text(json.dumps(before, ensure_ascii=False), encoding="utf-8")
            paths["after"].write_text(json.dumps(after, ensure_ascii=False), encoding="utf-8")
            paths["manifest"].write_text(
                json.dumps(self._manifest(), ensure_ascii=False), encoding="utf-8"
            )
            for key in ("before_assignments", "after_assignments"):
                with paths[key].open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=["unit_id", "topic_id"])
                    writer.writeheader()
                    writer.writerows(assignments)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPTS_DIR / "evaluate_representation_update.py"),
                    "--before-topics",
                    str(paths["before"]),
                    "--after-topics",
                    str(paths["after"]),
                    "--before-assignments",
                    str(paths["before_assignments"]),
                    "--after-assignments",
                    str(paths["after_assignments"]),
                    "--lexicon-manifest",
                    str(paths["manifest"]),
                    "--top-k",
                    "3",
                    "--rbo-p",
                    "0.9",
                    "--output",
                    str(paths["output"]),
                    "--candidate-output",
                    str(paths["candidates"]),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            comparison = json.loads(paths["output"].read_text(encoding="utf-8"))
            self.assertTrue(comparison["structural_invariants"]["assignments_unchanged"])
            with paths["candidates"].open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(any(row["candidate_type"] == "cross_topic_term" for row in rows))


if __name__ == "__main__":
    unittest.main()
