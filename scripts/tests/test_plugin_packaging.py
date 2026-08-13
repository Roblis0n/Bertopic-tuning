import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path, PurePosixPath


SKILL_ROOT = Path(__file__).resolve().parents[2]
BUILDER = SKILL_ROOT / "scripts" / "build_plugin.py"
POLICY = SKILL_ROOT / ".codex-plugin" / "package-policy.json"
PLUGIN_NAME = "bertopic-tuning"


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
    def run_builder(
        self,
        *arguments: str,
        builder: Path = BUILDER,
        cwd: Path = SKILL_ROOT,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update({
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_VALUE_0": "*",
        })
        return subprocess.run(
            [sys.executable, "-X", "utf8", "-B", str(builder), *arguments],
            cwd=cwd,
            env=environment,
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

    def git(self, cwd: Path, *arguments: str, input_text: str | None = None) -> str:
        environment = os.environ.copy()
        environment.update({
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_VALUE_0": "*",
        })
        result = subprocess.run(
            ["git", *arguments],
            cwd=cwd,
            env=environment,
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def make_index_repo(self, root: Path) -> Path:
        source = root / "source"
        policy = self.load_policy()
        relative_files = {
            Path(item["source"])
            for item in policy["files"]
        } | {
            Path(".codex-plugin/package-policy.json"),
            Path("scripts/build_plugin.py"),
        }
        contract = Path("scripts/validate_plugin_contract.py")
        if (SKILL_ROOT / contract).is_file():
            relative_files.add(contract)
        for relative in relative_files:
            destination = source / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SKILL_ROOT / relative, destination)
        self.git(source, "init", "-q")
        # Tests create and discard repositories rapidly. Disable detached Git
        # maintenance so no background writer can race TemporaryDirectory
        # cleanup after a commit returns.
        self.git(source, "config", "maintenance.auto", "false")
        self.git(source, "config", "gc.auto", "0")
        self.git(source, "add", "-A")
        return source

    def build_from_index_repo(
        self,
        source: Path,
        output: Path,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        return self.run_builder(
            "--output",
            str(output),
            *arguments,
            builder=source / "scripts" / "build_plugin.py",
            cwd=source,
        )

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
            output = Path(temp_dir) / PLUGIN_NAME
            output.mkdir()
            result = self.run_builder("--output", str(output))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)

    def test_build_rejects_output_inside_the_source_tree(self):
        output = SKILL_ROOT / "dist" / PLUGIN_NAME
        self.assertFalse(output.exists())
        result = self.run_builder("--output", str(output))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the source repository", result.stderr)
        self.assertFalse(output.exists())

    def test_build_rejects_output_with_a_noncanonical_folder_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "bertopic-tuning-plugin"
            result = self.run_builder("--output", str(output))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must be named bertopic-tuning", result.stderr)
            self.assertFalse(output.exists())

    def test_build_is_an_exact_whitelist_with_canonical_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / PLUGIN_NAME
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
            output = Path(temp_dir) / PLUGIN_NAME
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

    def test_two_builds_have_identical_tree_and_archive_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first = root / "first" / PLUGIN_NAME
            second = root / "second" / PLUGIN_NAME
            first_archive = root / "first" / f"{PLUGIN_NAME}.zip"
            second_archive = root / "second" / f"{PLUGIN_NAME}.zip"
            self.build(first, "--archive", str(first_archive))
            self.build(second, "--archive", str(second_archive))
            self.assertEqual(tree_digest(first), tree_digest(second))
            self.assertEqual(
                hashlib.sha256(first_archive.read_bytes()).digest(),
                hashlib.sha256(second_archive.read_bytes()).digest(),
            )
            first_metadata = {
                path.relative_to(first).as_posix(): (
                    stat.S_IMODE(path.stat().st_mode),
                    path.stat().st_mtime_ns,
                )
                for path in first.rglob("*")
            }
            second_metadata = {
                path.relative_to(second).as_posix(): (
                    stat.S_IMODE(path.stat().st_mode),
                    path.stat().st_mtime_ns,
                )
                for path in second.rglob("*")
            }
            self.assertEqual(first_metadata, second_metadata)

    def test_clean_package_archive_contains_only_whitelisted_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / PLUGIN_NAME
            archive = root / f"{PLUGIN_NAME}.zip"
            self.build(output, "--archive", str(archive))
            with zipfile.ZipFile(archive) as bundle:
                names = set(bundle.namelist())
            expected = {item["destination"] for item in self.load_policy()["files"]}
            self.assertEqual(names, expected)
            self.assertFalse(any(".git" in PurePosixPath(name).parts for name in names))
            self.assertFalse(any("__pycache__" in PurePosixPath(name).parts for name in names))

    def test_build_reads_policy_and_source_bytes_only_from_git_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.make_index_repo(root)
            indexed_skill = (source / "SKILL.md").read_bytes()
            with (source / "SKILL.md").open("ab") as handle:
                handle.write(b"\nPRIVATE_UNCOMMITTED_SENTINEL\n")
            secret = source / "private-secret.txt"
            secret.write_text("PRIVATE_POLICY_SENTINEL", encoding="utf-8")
            policy_path = source / ".codex-plugin" / "package-policy.json"
            dirty_policy = json.loads(policy_path.read_text(encoding="utf-8"))
            dirty_policy["files"].append({
                "source": "private-secret.txt",
                "destination": "skills/bertopic-tuning/assets/private-secret.txt",
            })
            policy_path.write_text(json.dumps(dirty_policy), encoding="utf-8")

            output = root / "out" / PLUGIN_NAME
            result = self.build_from_index_repo(source, output)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(
                (output / "skills" / PLUGIN_NAME / "SKILL.md").read_bytes(),
                indexed_skill,
            )
            self.assertFalse(
                (output / "skills" / PLUGIN_NAME / "assets" / "private-secret.txt").exists()
            )

    def test_build_rejects_windows_absolute_destination_without_writing_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.make_index_repo(root)
            escaped = root / "escaped.txt"
            policy_path = source / ".codex-plugin" / "package-policy.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy["files"][0]["destination"] = str(escaped)
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            self.git(source, "add", ".codex-plugin/package-policy.json")

            output = root / "out" / PLUGIN_NAME
            result = self.build_from_index_repo(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("safe POSIX relative path", result.stderr)
            self.assertFalse(escaped.exists())
            self.assertFalse(output.exists())

    def test_build_rejects_symlink_mode_in_git_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.make_index_repo(root)
            object_id = self.git(source, "hash-object", "-w", "--stdin", input_text="README.md").strip()
            self.git(source, "update-index", "--cacheinfo", f"120000,{object_id},SKILL.md")

            output = root / "out" / PLUGIN_NAME
            result = self.build_from_index_repo(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr)
            self.assertFalse(output.exists())

    def test_index_fixture_disables_background_git_maintenance(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = self.make_index_repo(Path(temp_dir))

            self.assertEqual(
                self.git(source, "config", "--get", "maintenance.auto").strip(),
                "false",
            )
            self.assertEqual(
                self.git(source, "config", "--get", "gc.auto").strip(),
                "0",
            )

    def test_build_rejects_unmerged_git_index_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.make_index_repo(root)
            self.git(source, "config", "user.name", "Packaging Test")
            self.git(source, "config", "user.email", "packaging@example.invalid")
            self.git(source, "commit", "-q", "-m", "base")
            base_branch = self.git(source, "branch", "--show-current").strip()
            self.git(source, "switch", "-q", "-c", "other")
            (source / "SKILL.md").write_text("other branch\n", encoding="utf-8")
            self.git(source, "add", "SKILL.md")
            self.git(source, "commit", "-q", "-m", "other")
            self.git(source, "switch", "-q", base_branch)
            (source / "SKILL.md").write_text("base branch\n", encoding="utf-8")
            self.git(source, "add", "SKILL.md")
            self.git(source, "commit", "-q", "-m", "base change")
            merge = subprocess.run(
                ["git", "merge", "other"],
                cwd=source,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertNotEqual(merge.returncode, 0)
            self.assertIn("SKILL.md", self.git(source, "ls-files", "--unmerged"))

            output = root / "out" / PLUGIN_NAME
            result = self.build_from_index_repo(source, output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unmerged", result.stderr)
            self.assertFalse(output.exists())

    def test_archive_preserves_executable_mode_from_git_index(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.make_index_repo(root)
            self.git(source, "update-index", "--chmod=+x", "SKILL.md")
            output = root / "out" / PLUGIN_NAME
            archive = root / "out" / f"{PLUGIN_NAME}.zip"
            result = self.build_from_index_repo(
                source,
                output,
                "--archive",
                str(archive),
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            with zipfile.ZipFile(archive) as bundle:
                info = bundle.getinfo(f"skills/{PLUGIN_NAME}/SKILL.md")
            self.assertEqual((info.external_attr >> 16) & 0o777, 0o755)

    def test_git_source_archive_preserves_indexed_license_bytes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source"
            source.mkdir()
            shutil.copyfile(SKILL_ROOT / "LICENSE", source / "LICENSE")
            shutil.copyfile(SKILL_ROOT / ".gitattributes", source / ".gitattributes")
            self.git(source, "init", "-q")
            self.git(source, "config", "user.name", "Packaging Test")
            self.git(source, "config", "user.email", "packaging@example.invalid")
            self.git(source, "add", "LICENSE", ".gitattributes")
            indexed = subprocess.run(
                ["git", "show", ":LICENSE"],
                cwd=source,
                capture_output=True,
                check=True,
            ).stdout
            self.git(source, "commit", "-q", "-m", "archive fixture")
            archive_path = root / "source.zip"
            result = subprocess.run(
                [
                    "git",
                    "archive",
                    "--format=zip",
                    f"--output={archive_path}",
                    "HEAD",
                    "LICENSE",
                ],
                cwd=source,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            with zipfile.ZipFile(archive_path) as bundle:
                exported = bundle.read("LICENSE")
        self.assertEqual(exported, indexed)

    def test_vendored_contract_rejects_unsupported_manifest_field(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = self.make_index_repo(root)
            manifest_path = source / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["unsupported_release_field"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.git(source, "add", ".codex-plugin/plugin.json")

            output = root / "out" / PLUGIN_NAME
            archive = root / "out" / f"{PLUGIN_NAME}.zip"
            result = self.build_from_index_repo(
                source,
                output,
                "--archive",
                str(archive),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported_release_field", result.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(archive.exists())

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
            output = root / PLUGIN_NAME
            self.build(output, "--codex-home", str(codex_home))
            self.assertEqual(log.read_text(encoding="utf-8"), "skill\nplugin\n")

    def test_available_official_validators_accept_the_real_package(self):
        codex_home = os.environ.get("CODEX_HOME")
        if not codex_home:
            self.skipTest("CODEX_HOME is not configured")
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / PLUGIN_NAME
            result = self.run_builder(
                "--output",
                str(output),
                "--codex-home",
                codex_home,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertIn("Plugin validation passed", result.stdout)

    def test_vendored_and_official_contracts_reject_an_unsupported_field(self):
        codex_home = os.environ.get("CODEX_HOME")
        if not codex_home:
            self.skipTest("CODEX_HOME is not configured")
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / PLUGIN_NAME
            self.build(output)
            manifest_path = output / ".codex-plugin" / "plugin.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["unsupported_release_field"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            validators = (
                SKILL_ROOT / "scripts" / "validate_plugin_contract.py",
                Path(codex_home)
                / "skills"
                / ".system"
                / "plugin-creator"
                / "scripts"
                / "validate_plugin.py",
            )
            for validator in validators:
                result = subprocess.run(
                    [sys.executable, "-X", "utf8", "-B", str(validator), str(output)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0, validator)
                self.assertIn("unsupported_release_field", result.stdout, validator)

    def test_missing_official_validators_rejects_build_without_partial_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output = root / PLUGIN_NAME
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
        self.assertIn("/bertopic-tuning", workflow)
        self.assertIn("/bertopic-tuning.zip", workflow)
        self.assertNotIn("bertopic-tuning-plugin", workflow)

    def test_release_links_and_changelog_match_v1_release(self):
        readme = (SKILL_ROOT / "README.md").read_text(encoding="utf-8")
        changelog = (SKILL_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("releases/latest", readme)
        self.assertIn("/bertopic-tuning --archive", readme)
        self.assertIn("## [1.0.0] - 2026-08-13", changelog)
        self.assertIn(
            "[1.0.0]: https://github.com/Roblis0n/Bertopic-tuning/releases/tag/v1.0.0",
            changelog,
        )
        self.assertNotIn("The GitHub tag and release have not been published", changelog)
        self.assertIn("203+ standard-library", changelog)
        for phrase in ("standalone plugin", "Codex UI", "brand assets"):
            self.assertIn(phrase, changelog)


if __name__ == "__main__":
    unittest.main()
