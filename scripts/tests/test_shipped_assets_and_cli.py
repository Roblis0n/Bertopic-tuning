#!/usr/bin/env python3

from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parents[1]
SKILL_ROOT = SCRIPTS_DIR.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
sys.path.insert(0, str(SCRIPTS_DIR))

import validate_study_bundle  # noqa: E402


class ShippedAssetsTests(unittest.TestCase):
    """The assets/ templates are what users actually copy, while the
    validators are tested against independent fixture copies. Pin the
    structural contract between the two so a validator-side rename
    cannot silently strand the shipped templates."""

    def test_shipped_csv_headers_cover_validator_required_columns(self):
        asset_root = SKILL_ROOT / "assets"
        for name, required_fields in validate_study_bundle.TABLE_FIELDS.items():
            with self.subTest(table=name):
                path = asset_root / name
                self.assertTrue(path.is_file(), f"missing shipped template: {name}")
                with path.open(encoding="utf-8", newline="") as handle:
                    header = next(csv.reader(handle), [])
                missing = sorted(set(required_fields) - set(header))
                self.assertEqual(missing, [], f"{name} header drifted from validator")

    def test_shipped_json_templates_parse(self):
        asset_root = SKILL_ROOT / "assets"
        templates = sorted(asset_root.glob("*.json"))
        self.assertTrue(templates)
        for path in templates:
            with self.subTest(template=path.name):
                json.loads(path.read_text(encoding="utf-8"))


class ValidatorCliTests(unittest.TestCase):
    """The skill invokes the validators through their CLIs, so the exit
    code is part of the contract: 0 for a valid bundle, 1 for a rejected
    one, with the JSON audit on stdout in both cases."""

    def _run_cli(self, script: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS_DIR / script), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_study_bundle_cli_exit_codes(self):
        fixture = FIXTURES / "exploratory-study-bundle"

        completed = self._run_cli("validate_study_bundle.py", str(fixture))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["valid"])

        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "bundle"
            shutil.copytree(fixture, broken)
            registry_path = broken / "experiment-registry.csv"
            lines = registry_path.read_text(encoding="utf-8").splitlines()
            lines[0] = "bogus_column," + lines[0].split(",", 1)[1]
            registry_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

            completed = self._run_cli("validate_study_bundle.py", str(broken))
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertFalse(json.loads(completed.stdout)["valid"])

    def test_tuning_trace_cli_exit_codes(self):
        fixture = FIXTURES / "exploratory-study-bundle"
        trace = fixture / "tuning-trace.json"
        registry = fixture / "experiment-registry.csv"

        completed = self._run_cli("validate_tuning_trace.py", str(trace), str(registry))
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["valid"])

        with tempfile.TemporaryDirectory() as tmp:
            broken_trace = Path(tmp) / "tuning-trace.json"
            payload = json.loads(trace.read_text(encoding="utf-8"))
            payload["assurance_level"] = "bogus-level"
            broken_trace.write_text(json.dumps(payload), encoding="utf-8")

            completed = self._run_cli(
                "validate_tuning_trace.py", str(broken_trace), str(registry)
            )
            self.assertEqual(completed.returncode, 1, completed.stderr)
            self.assertFalse(json.loads(completed.stdout)["valid"])


if __name__ == "__main__":
    unittest.main()
