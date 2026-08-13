import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath


SKILL_ROOT = Path(__file__).resolve().parents[2]
BUILDER = SKILL_ROOT / "scripts" / "build_plugin.py"
POLICY = SKILL_ROOT / ".codex-plugin" / "package-policy.json"


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        payload = path.read_bytes()
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


class PluginPackagingTests(unittest.TestCase):
    def run_builder(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-X", "utf8", "-B", str(BUILDER), *arguments],
            cwd=SKILL_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )

    def build(self, output: Path, *arguments: str) -> None:
        result = self.run_builder("--output", str(output), *arguments)
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def load_policy(self) -> dict:
        return json.loads(POLICY.read_text(encoding="utf-8"))

    def test_policy_has_one_canonical_skill_projection_and_safe_destinations(self):
        policy = self.load_policy()
        projections = [
            item
            for item in policy["files"]
            if item["destination"] == "skills/bertopic-tuning/SKILL.md"
        ]
        self.assertEqual(projections, [{
            "source": "SKILL.md",
            "destination": "skills/bertopic-tuning/SKILL.md",
        }])
        destinations = [item["destination"] for item in policy["files"]]
        self.assertEqual(len(destinations), len(set(destinations)))
        for destination in destinations:
            path = PurePosixPath(destination)
            self.assertFalse(path.is_absolute(), destination)
            self.assertNotIn("..", path.parts, destination)
        sources = {item["source"] for item in policy["files"]}
        self.assertNotIn("skills/bertopic-tuning/SKILL.md", sources)
        self.assertNotIn("scripts/build_plugin.py", sources)
        self.assertFalse(any(source.startswith("scripts/tests/") for source in sources))

    def test_build_rejects_an_existing_output_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "existing"
            output.mkdir()
            result = self.run_builder("--output", str(output))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)

    def test_build_rejects_output_inside_the_source_tree(self):
        output = SKILL_ROOT / "dist" / "recursive-plugin-output"
        self.assertFalse(output.exists())
        result = self.run_builder("--output", str(output))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the source repository", result.stderr)
        self.assertFalse(output.exists())

    def test_build_is_an_exact_whitelist_with_canonical_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "plugin"
            self.build(output)
            policy = self.load_policy()
            expected = {item["destination"] for item in policy["files"]}
            actual = {
                path.relative_to(output).as_posix()
                for path in output.rglob("*")
                if path.is_file()
            }
            self.assertEqual(actual, expected)
            packaged_skill = output / "skills" / "bertopic-tuning" / "SKILL.md"
            self.assertEqual(packaged_skill.read_bytes(), (SKILL_ROOT / "SKILL.md").read_bytes())
            self.assertNotIn("scripts/tests/test_plugin_packaging.py", actual)
            self.assertNotIn("README.md", actual)

    def test_manifest_and_brand_assets_are_complete(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "plugin"
            self.build(output)
            manifest = json.loads(
                (output / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["name"], "bertopic-tuning")
            self.assertEqual(manifest["version"], "1.0.0")
            self.assertEqual(manifest["skills"], "./skills/")
            referenced_assets = {
                manifest["interface"]["composerIcon"],
                manifest["interface"]["logo"],
                *manifest["interface"]["screenshots"],
            }
            for relative in referenced_assets:
                packaged = output / relative.removeprefix("./")
                source = SKILL_ROOT / relative.removeprefix("./")
                self.assertTrue(packaged.is_file(), relative)
                self.assertEqual(packaged.read_bytes(), source.read_bytes(), relative)

    def test_two_builds_have_identical_content_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first"
            second = root / "second"
            self.build(first)
            self.build(second)
            self.assertEqual(tree_digest(first), tree_digest(second))

    def test_clean_package_archive_contains_only_whitelisted_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "plugin"
            archive = root / "plugin.zip"
            self.build(output)
            with zipfile.ZipFile(archive, "w") as bundle:
                for path in sorted(item for item in output.rglob("*") if item.is_file()):
                    bundle.write(path, path.relative_to(output).as_posix())
            with zipfile.ZipFile(archive) as bundle:
                names = set(bundle.namelist())
            expected = {item["destination"] for item in self.load_policy()["files"]}
            self.assertEqual(names, expected)
            self.assertFalse(any(".git" in PurePosixPath(name).parts for name in names))
            self.assertFalse(any("__pycache__" in PurePosixPath(name).parts for name in names))

    def test_codex_home_runs_both_validator_commands_before_publish(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex_home = root / "codex-home"
            log = root / "validator-log.txt"
            skill_validator = (
                codex_home
                / "skills"
                / ".system"
                / "skill-creator"
                / "scripts"
                / "quick_validate.py"
            )
            plugin_validator = (
                codex_home
                / "skills"
                / ".system"
                / "plugin-creator"
                / "scripts"
                / "validate_plugin.py"
            )
            skill_validator.parent.mkdir(parents=True)
            plugin_validator.parent.mkdir(parents=True)
            skill_validator.write_text(
                "import pathlib,sys\n"
                f"log=pathlib.Path({str(log)!r})\n"
                "target=pathlib.Path(sys.argv[1])\n"
                "assert target.name == 'bertopic-tuning'\n"
                "assert (target/'SKILL.md').is_file()\n"
                "log.write_text('skill\\n', encoding='utf-8')\n",
                encoding="utf-8",
            )
            plugin_validator.write_text(
                "import pathlib,sys\n"
                f"log=pathlib.Path({str(log)!r})\n"
                "target=pathlib.Path(sys.argv[1])\n"
                "assert (target/'.codex-plugin'/'plugin.json').is_file()\n"
                "with log.open('a', encoding='utf-8') as handle: handle.write('plugin\\n')\n",
                encoding="utf-8",
            )
            output = root / "plugin"
            self.build(output, "--codex-home", str(codex_home))
            self.assertEqual(log.read_text(encoding="utf-8"), "skill\nplugin\n")

    def test_missing_official_validators_rejects_build_without_partial_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / "plugin"
            result = self.run_builder(
                "--output",
                str(output),
                "--codex-home",
                str(root / "missing-codex-home"),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("official validator", result.stderr)
            self.assertFalse(output.exists())

    def test_ci_builds_the_standalone_plugin_outside_the_checkout(self):
        workflow = (SKILL_ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("scripts/build_plugin.py", workflow)
        self.assertIn("runner.temp", workflow)

    def test_release_links_and_unreleased_notes_match_pre_release_state(self):
        readme = (SKILL_ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (SKILL_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertNotIn("releases/tag/v1.0.0", readme)
        self.assertIn("releases/latest", readme)
        for phrase in ("standalone plugin", "Codex UI", "brand assets"):
            self.assertIn(phrase, changelog)


if __name__ == "__main__":
    unittest.main()
