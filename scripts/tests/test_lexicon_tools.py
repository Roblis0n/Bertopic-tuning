import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from lexicon_tools import (  # noqa: E402
    build_count_vectorizer,
    compile_lexicon_bundle,
    make_lexicon_tokenizer,
)


class LexiconBundleTests(unittest.TestCase):
    def _write_bundle_sources(
        self,
        root: Path,
        *,
        synonyms: list[list[str]] | None = None,
        stopwords: list[list[str]] | None = None,
        custom_terms: list[list[str]] | None = None,
        bom: bool = False,
    ) -> Path:
        config = {
            "schema_version": 1,
            "bundle_name": "消费券研究词表",
            "parent_bundle_id": "",
            "apply_to": "lexical_text",
            "normalization": {
                "unicode_form": None,
                "casefold": False,
                "collapse_whitespace": True,
            },
            "tokenizer": {"name": "test-tokenizer", "revision": "fixture"},
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
            "synonyms.csv": (
                ["canonical_term", "variant", "status", "source", "reason"],
                synonyms or [],
            ),
            "stopwords.csv": (
                ["term", "status", "source", "reason"],
                stopwords or [],
            ),
            "custom-terms.csv": (
                ["term", "display_form", "term_type", "status", "source", "reason"],
                custom_terms or [],
            ),
        }
        for name, (header, rows) in tables.items():
            encoding = "utf-8-sig" if bom else "utf-8"
            with (root / name).open("w", encoding=encoding, newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(header)
                writer.writerows(rows)
        return root / "lexicon-config.json"

    def test_rejects_variant_mapped_to_multiple_canonical_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_bundle_sources(
                Path(tmp),
                synonyms=[
                    ["人工智能", "AI", "active", "domain-review", "统一简称"],
                    ["人工智能技术", "AI", "active", "domain-review", "另一含义"],
                ],
            )

            with self.assertRaisesRegex(ValueError, "multiple canonical"):
                compile_lexicon_bundle(config)

    def test_rejects_duplicate_synonym_with_conflicting_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_bundle_sources(
                Path(tmp),
                synonyms=[
                    ["人工智能", "AI", "active", "review-a", "简称"],
                    ["人工智能", "AI", "active", "review-b", "平台写法"],
                ],
            )

            with self.assertRaisesRegex(ValueError, "conflicting active records"):
                compile_lexicon_bundle(config)

    def test_bundle_id_is_stable_across_row_order_and_bom(self):
        rows = [
            ["人工智能", "AI", "active", "domain-review", "统一简称"],
            ["电子消费券", "数字消费券", "active", "domain-review", "统一表述"],
        ]
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = self._write_bundle_sources(
                Path(first_tmp), synonyms=rows, bom=False
            )
            second = self._write_bundle_sources(
                Path(second_tmp), synonyms=list(reversed(rows)), bom=True
            )

            first_bundle = compile_lexicon_bundle(first)
            second_bundle = compile_lexicon_bundle(second)

            self.assertEqual(first_bundle["bundle_id"], second_bundle["bundle_id"])
            self.assertEqual(
                first_bundle["content_sha256"], second_bundle["content_sha256"]
            )

    def test_custom_phrase_synonym_and_stopword_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_bundle_sources(
                Path(tmp),
                synonyms=[
                    ["人工智能", "AI", "active", "domain-review", "统一简称"]
                ],
                stopwords=[["的", "active", "topic-audit", "无主题信息"]],
                custom_terms=[
                    ["消费券", "消费券", "domain_phrase", "active", "domain-review", "保护短语"]
                ],
            )
            bundle = compile_lexicon_bundle(config)
            tokenizer = make_lexicon_tokenizer(lambda text: list(text), bundle)

            self.assertEqual(tokenizer("消费券的AI"), ["消费券", "人工智能"])

    def test_ascii_alias_does_not_match_inside_a_longer_word(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_bundle_sources(
                Path(tmp),
                synonyms=[
                    ["人工智能", "AI", "active", "domain-review", "统一简称"]
                ],
            )
            bundle = compile_lexicon_bundle(config)
            tokenizer = make_lexicon_tokenizer(lambda text: text.split(), bundle)

            self.assertEqual(tokenizer("RAIL AI"), ["RAIL", "人工智能"])

    def test_rejects_custom_term_that_is_also_a_stopword(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_bundle_sources(
                Path(tmp),
                stopwords=[["平台", "active", "topic-audit", "来源伪影"]],
                custom_terms=[
                    ["平台", "平台", "domain_phrase", "active", "domain-review", "领域概念"]
                ],
            )

            with self.assertRaisesRegex(ValueError, "both a stopword and a custom term"):
                compile_lexicon_bundle(config)

    def test_rejects_duplicate_stopword_with_conflicting_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_bundle_sources(
                Path(tmp),
                stopwords=[
                    ["平台", "active", "source-a", "来源伪影"],
                    ["平台", "active", "source-b", "通用词"],
                ],
            )

            with self.assertRaisesRegex(ValueError, "conflicting active records"):
                compile_lexicon_bundle(config)

    def test_fixed_vocabulary_requires_explicit_closed_vocabulary_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_bundle_sources(Path(tmp))
            bundle = compile_lexicon_bundle(config)

            with self.assertRaisesRegex(ValueError, "closed vocabulary"):
                build_count_vectorizer(
                    bundle,
                    base_tokenizer=lambda text: text.split(),
                    vocabulary=["消费券"],
                )

    def test_build_bundle_cli_writes_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = self._write_bundle_sources(
                root,
                custom_terms=[
                    ["消费券", "消费券", "domain_phrase", "active", "domain-review", "保护短语"]
                ],
            )
            output = root / "lexicon-manifest.json"

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPTS_DIR / "build_lexicon_bundle.py"),
                    "--config",
                    str(config),
                    "--output",
                    str(output),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            manifest = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(manifest["bundle_id"].startswith("lexicon-"))
            self.assertEqual(manifest["counts"]["custom_terms"], 1)

    def test_source_tables_must_stay_inside_the_bundle_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle_root = root / "bundle"
            bundle_root.mkdir()
            config = self._write_bundle_sources(bundle_root)
            payload = json.loads(config.read_text(encoding="utf-8"))
            payload["files"]["synonyms"] = "../synonyms.csv"
            config.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "inside the lexicon bundle directory"):
                compile_lexicon_bundle(config)

    def test_tokenizer_identity_is_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_bundle_sources(Path(tmp))
            payload = json.loads(config.read_text(encoding="utf-8"))
            payload["tokenizer"]["revision"] = ""
            config.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "tokenizer.revision"):
                compile_lexicon_bundle(config)

    def test_tokenizer_rejects_a_bundle_with_unresolved_conflicts(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_bundle_sources(Path(tmp))
            bundle = compile_lexicon_bundle(config)
            bundle["conflicts"] = [{"term": "平台"}]

            with self.assertRaisesRegex(ValueError, "unresolved conflicts"):
                make_lexicon_tokenizer(lambda text: text.split(), bundle)

    def test_tokenizer_rejects_a_manifest_with_a_tampered_synonym_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = self._write_bundle_sources(
                Path(tmp),
                synonyms=[
                    ["人工智能", "AI", "active", "domain-review", "统一简称"]
                ],
            )
            bundle = compile_lexicon_bundle(config)
            bundle["synonym_map"] = {"AI": "错误概念"}

            with self.assertRaisesRegex(ValueError, "synonym_map"):
                make_lexicon_tokenizer(lambda text: text.split(), bundle)


if __name__ == "__main__":
    unittest.main()
