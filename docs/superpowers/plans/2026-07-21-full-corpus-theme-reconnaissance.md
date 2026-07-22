# Full-Corpus Theme Reconnaissance Implementation Plan

> Historical implementation plan. The 2026-07-22 scalable-reading amendment supersedes tasks that require direct full-text review of every eligible unique unit. Follow the current `SKILL.md`, `references/corpus-theme-reconnaissance.md`, `references/scalable-corpus-reading.md`, templates and validators for active behavior.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an auditable, full-corpus theme reconnaissance stage that estimates coarse and fine topic structures around the user's research mainline, reports them before modeling, and blocks all modeling until explicit user authorization is recorded.

**Architecture:** The feature is a governance layer, not a new clustering algorithm. Three portable artifacts record full-corpus coverage, candidate themes, and user authorization; a standard-library validator checks them independently, and the existing study-bundle validator enforces the authorization ID on every modeling run. Skill instructions and route references define how Codex performs batched full-corpus reading without treating the preview topic count as a target K.

**Tech Stack:** Markdown skill instructions, UTF-8 JSON/CSV templates, Python 3 standard library, `unittest`, existing Codex skill validator and ZIP packaging workflow.

## Global Constraints

- Do not run Git commands or create commits; this workspace is maintained without Git operations for this task.
- Do not create `v1`, `v2`, `final`, `latest`, or other duplicate-version files.
- The default user-theme mode is exactly `coverage_and_interpretation_anchor`.
- The preview must allow recurrent emergent themes outside the user's mainline.
- A preview topic count is a corpus-grounded hypothesis, never a forced BERTopic topic count.
- Do not add provider-specific LLM clients, external dependencies, BERTopic fitting code, or universal topic-count thresholds.
- Every eligible unit must be content-reviewed or linked to an exact-duplicate representative; near duplicates cannot inherit review automatically.
- No baseline, structural, representation, taxonomy, or mapping run may start while the gate is not `approved_for_modeling`.
- `HANDOFF.md` remains local-only and must not enter the portable package.
- All CSV/JSON artifacts remain plain and machine-readable without decorative formatting.

---

## File map

### Create

- `assets/theme-reconnaissance.json` — machine-readable preview, coverage ledger, and coarse/fine topic estimate.
- `assets/theme-candidate-audit.csv` — one evidence-linked row per candidate theme.
- `assets/modeling-authorization.json` — explicit pause/approval gate.
- `references/corpus-theme-reconnaissance.md` — complete operating method for full-corpus review and user handoff.
- `scripts/validate_theme_reconnaissance.py` — reusable validator and command-line entry point.
- `scripts/tests/test_theme_reconnaissance.py` — focused validator tests.
- `scripts/tests/fixtures/theme-reconnaissance-awaiting/` — complete preview that is valid before approval.

### Modify

- `SKILL.md` — insert reconnaissance and user authorization before the study contract and baseline.
- `README.md` — document the new workflow, artifacts, command, and scope.
- `agents/openai.yaml` — make preview-and-pause behavior discoverable in the default prompt.
- `assets/study-contract.json` — add mandatory `pre_model_reconnaissance` policy.
- `assets/experiment-registry.csv` — add `authorization_id`.
- `assets/decision-report.md` — add preview and preview-versus-model reporting sections.
- `references/network-short-text.md` — define duplicate-aware full review.
- `references/long-document.md` — define parent-document and provisional-segment full review.
- `references/study-contract-and-reporting.md` — register artifacts and authorization linkage.
- `references/bertopic-implementation.md` — add the pre-fit authorization guard.
- `scripts/validate_study_bundle.py` — require approved reconnaissance and linked registry rows.
- `scripts/tests/test_tools.py` — test templates, documentation integration, and final-bundle enforcement.
- `scripts/tests/fixtures/lexicon-study-bundle/*` — migrate the completed fixture to the new required gate.
- `HANDOFF.md` — record the completed feature, exact test results, package size, and hash while preserving privacy rules.
- `F:\Skill\Codex\bertopic-tuning.skill.zip` — rebuild the single portable package after all source validation passes.

---

### Task 1: Add the three artifact contracts

**Files:**

- Create: `assets/theme-reconnaissance.json`
- Create: `assets/theme-candidate-audit.csv`
- Create: `assets/modeling-authorization.json`
- Modify: `assets/study-contract.json`
- Modify: `assets/experiment-registry.csv`
- Modify: `assets/decision-report.md`
- Test: `scripts/tests/test_tools.py`

**Interfaces:**

- Consumes: the existing corpus fingerprint, route, research question, and stable unit IDs.
- Produces: artifact schemas consumed by `validate_theme_reconnaissance(root, require_approval=False)` and an `authorization_id` consumed by the experiment registry.

- [ ] **Step 1: Write the failing asset-schema test**

Add this method to `SkillInstructionTests` in `scripts/tests/test_tools.py`:

```python
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
    self.assertIn("coarse", reconnaissance["topic_count_estimate"])
    self.assertIn("fine", reconnaissance["topic_count_estimate"])

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
        "user_disposition",
        "user_instruction",
    }
    self.assertTrue(required.issubset(header), required.difference(header))

    authorization = json.loads(
        (asset_root / "modeling-authorization.json").read_text(encoding="utf-8")
    )
    self.assertEqual(authorization["gate_status"], "awaiting_user_direction")
    self.assertFalse(authorization["modeling_may_start"])
    self.assertEqual(
        authorization["user_theme_mode"],
        "coverage_and_interpretation_anchor",
    )

    contract = json.loads(
        (asset_root / "study-contract.json").read_text(encoding="utf-8")
    )
    policy = contract["pre_model_reconnaissance"]
    self.assertTrue(policy["required"])
    self.assertTrue(policy["user_authorization_required"])
    self.assertEqual(policy["authorization_artifact"], "modeling-authorization.json")

    with (asset_root / "experiment-registry.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as handle:
        registry_header = set(next(csv.reader(handle)))
    self.assertIn("authorization_id", registry_header)
```

- [ ] **Step 2: Run the focused test and confirm the intended failure**

Run:

```powershell
python -B -m unittest scripts.tests.test_tools.SkillInstructionTests.test_theme_reconnaissance_assets_have_auditable_schemas -v
```

Expected: `ERROR` or `FAIL` naming the missing reconnaissance assets.

- [ ] **Step 3: Create `assets/theme-reconnaissance.json`**

Use this exact template with LF line endings:

```json
{
  "schema_version": 1,
  "reconnaissance_id": "",
  "corpus_fingerprint": "",
  "route": "",
  "created_at": "",
  "research_question": "",
  "user_theme": {
    "mainline": "",
    "mode": "coverage_and_interpretation_anchor",
    "allow_emergent_themes": true,
    "inclusion_intent": "",
    "exclusion_intent": ""
  },
  "coverage": {
    "source_unit_count": null,
    "eligible_unit_count": null,
    "reviewed_unit_count": null,
    "duplicate_inherited_unit_count": null,
    "excluded_unit_count": null,
    "failed_unit_count": null,
    "coverage_complete": false,
    "failed_unit_ids": [],
    "exclusion_basis": ""
  },
  "parent_document_coverage": {
    "applicable": false,
    "eligible_parent_document_count": null,
    "reviewed_parent_document_count": null,
    "failed_parent_document_count": null,
    "coverage_complete": false
  },
  "topic_count_estimate": {
    "interpretation": "pre_model_hypothesis_not_target_k",
    "coarse": {
      "lower_bound": null,
      "point_estimate": null,
      "upper_bound": null,
      "candidate_theme_ids": [],
      "basis": ""
    },
    "fine": {
      "lower_bound": null,
      "point_estimate": null,
      "upper_bound": null,
      "candidate_theme_ids": [],
      "basis": ""
    }
  },
  "unresolved_boundaries": [],
  "excluded_artifact_candidate_ids": [],
  "strongest_counter_evidence": ""
}
```

- [ ] **Step 4: Create `assets/theme-candidate-audit.csv`**

Use this exact header and no data rows:

```csv
reconnaissance_id,candidate_theme_id,parent_candidate_theme_id,hierarchy_level,route_subset,provisional_label,theme_type,relation_to_user_mainline,definition,inclusion,exclusion,independent_support,evidence_unit_ids,source_or_parent_spread,duplicate_or_artifact_risk,uncertainty,user_disposition,user_instruction
```

- [ ] **Step 5: Create `assets/modeling-authorization.json`**

Use this exact template:

```json
{
  "schema_version": 1,
  "authorization_id": "",
  "reconnaissance_id": "",
  "corpus_fingerprint": "",
  "gate_status": "awaiting_user_direction",
  "modeling_may_start": false,
  "user_theme_mode": "coverage_and_interpretation_anchor",
  "allow_emergent_themes": true,
  "user_instruction": "",
  "resolved_candidate_theme_ids": [],
  "decision_recorded_at": ""
}
```

- [ ] **Step 6: Extend the existing templates**

Add this object to `assets/study-contract.json` immediately before `lexicon_policy`:

```json
"pre_model_reconnaissance": {
  "required": true,
  "user_theme_mode": "coverage_and_interpretation_anchor",
  "allow_emergent_themes": true,
  "reconnaissance_artifact": "theme-reconnaissance.json",
  "candidate_audit_artifact": "theme-candidate-audit.csv",
  "authorization_artifact": "modeling-authorization.json",
  "user_authorization_required": true
},
```

Insert `authorization_id` after `parent_snapshot_id` in `assets/experiment-registry.csv`.

Insert this section in `assets/decision-report.md` after “Analysis-unit decision”:

```markdown
## Full-corpus theme reconnaissance and user direction

Report the coverage ledger, coarse and fine topic-count estimates, user-mainline themes, supporting/contextual themes, recurrent emergent themes, uncertain boundaries and artifacts. Link `theme-reconnaissance.json`, `theme-candidate-audit.csv` and the approved `modeling-authorization.json`. State the user instruction and confirm that modeling began only after approval.

## Preview-versus-model comparison

Compare the selected model with the approved preview: covered candidate themes, missing themes, unexpected themes, merges, splits and preview assumptions rejected by model or human evidence. Do not treat the preview count as a target K.
```

- [ ] **Step 7: Run the focused test and verify success**

Run the same command from Step 2.

Expected: `PASS`.

---

### Task 2: Implement the standalone reconnaissance validator

**Files:**

- Create: `scripts/validate_theme_reconnaissance.py`
- Create: `scripts/tests/test_theme_reconnaissance.py`
- Create: `scripts/tests/fixtures/theme-reconnaissance-awaiting/corpus-profile.json`
- Create: `scripts/tests/fixtures/theme-reconnaissance-awaiting/theme-reconnaissance.json`
- Create: `scripts/tests/fixtures/theme-reconnaissance-awaiting/theme-candidate-audit.csv`
- Create: `scripts/tests/fixtures/theme-reconnaissance-awaiting/modeling-authorization.json`

**Interfaces:**

- Consumes: a directory containing `corpus-profile.json` and the three new artifacts.
- Produces: `validate_theme_reconnaissance(root: Path, *, require_approval: bool = False) -> dict[str, Any]` and a CLI with optional `--require-approval` and `--output`.

- [ ] **Step 1: Write the valid-awaiting and incomplete-coverage tests**

Create `scripts/tests/test_theme_reconnaissance.py` with a helper that writes one valid two-theme fixture and these initial tests:

```python
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


def write_preview(root: Path, *, gate_status: str = "awaiting_user_direction") -> None:
    fingerprint = "sha256:corpus-test"
    reconnaissance_id = "recon-20260721-a1"
    candidate_ids = ["PRE-C-001", "PRE-F-001"]
    approved = gate_status == "approved_for_modeling"

    (root / "corpus-profile.json").write_text(
        json.dumps({"corpus_fingerprint": fingerprint, "unit_count": 12}),
        encoding="utf-8",
    )
    reconnaissance = {
        "schema_version": 1,
        "reconnaissance_id": reconnaissance_id,
        "corpus_fingerprint": fingerprint,
        "route": "network-short",
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
            "applicable": False,
            "eligible_parent_document_count": None,
            "reviewed_parent_document_count": None,
            "failed_parent_document_count": None,
            "coverage_complete": False,
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
            "network-short",
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
            "network-short",
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


class ThemeReconnaissanceValidationTests(unittest.TestCase):
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
            self.assertTrue(any("approved_for_modeling" in e for e in result["errors"]))

    def test_incomplete_coverage_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_preview(root)
            path = root / "theme-reconnaissance.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["coverage"]["failed_unit_count"] = 1
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = validate_theme_reconnaissance(root)
            self.assertFalse(result["valid"])
            self.assertTrue(any("eligible_unit_count" in e for e in result["errors"]))
            self.assertTrue(any("failed_unit_count" in e for e in result["errors"]))
```

- [ ] **Step 2: Run the new test module and confirm import failure**

Run:

```powershell
python -B -m unittest scripts.tests.test_theme_reconnaissance -v
```

Expected: `ERROR` with `ModuleNotFoundError: No module named 'validate_theme_reconnaissance'`.

- [ ] **Step 3: Implement the validator core**

Create `scripts/validate_theme_reconnaissance.py` with these public constants and functions:

```python
#!/usr/bin/env python3
"""Validate full-corpus theme reconnaissance and the user modeling gate."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = {
    "corpus-profile.json",
    "theme-reconnaissance.json",
    "theme-candidate-audit.csv",
    "modeling-authorization.json",
}

CANDIDATE_FIELDS = {
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
}

RELATIONS = {"mainline", "supporting", "contextual", "emergent", "artifact", "uncertain"}
HIERARCHY_LEVELS = {"coarse", "fine"}
GATE_STATES = {"awaiting_user_direction", "revision_requested", "approved_for_modeling", "stop"}
DISPOSITIONS = {"accepted", "rejected", "merge_requested", "split_requested", "deferred"}
ROUTES = {"network-short", "long-document", "mixed"}


def _read_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"Cannot read valid JSON from {path.name}: {exc}")
        return None


def _read_candidates(path: Path, errors: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return list(reader.fieldnames or []), list(reader)
    except (OSError, csv.Error) as exc:
        errors.append(f"Cannot read CSV {path.name}: {exc}")
        return [], []


def _count(value: Any, field: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        errors.append(f"{field} must be a non-negative integer")
        return None
    return value


def validate_theme_reconnaissance(
    root: Path,
    *,
    require_approval: bool = False,
) -> dict[str, Any]:
    root = Path(root)
    errors: list[str] = []
    warnings: list[str] = []
    result: dict[str, Any] = {
        "valid": False,
        "errors": errors,
        "warnings": warnings,
        "reconnaissance_id": "",
        "authorization_id": "",
        "gate_status": "",
    }
    if not root.is_dir():
        errors.append(f"Reconnaissance directory does not exist: {root}")
        return result

    for name in sorted(REQUIRED_FILES):
        if not (root / name).is_file():
            errors.append(f"Missing required file: {name}")
    if errors:
        return result

    profile = _read_json(root / "corpus-profile.json", errors)
    reconnaissance = _read_json(root / "theme-reconnaissance.json", errors)
    authorization = _read_json(root / "modeling-authorization.json", errors)
    header, candidates = _read_candidates(root / "theme-candidate-audit.csv", errors)
    if not all(isinstance(item, dict) for item in (profile, reconnaissance, authorization)):
        return result

    missing_columns = sorted(CANDIDATE_FIELDS.difference(header))
    errors.extend(f"theme-candidate-audit.csv lacks required column: {field}" for field in missing_columns)
    if not candidates:
        errors.append("theme-candidate-audit.csv must contain at least one candidate theme")

    fingerprint = str(reconnaissance.get("corpus_fingerprint", "")).strip()
    reconnaissance_id = str(reconnaissance.get("reconnaissance_id", "")).strip()
    authorization_id = str(authorization.get("authorization_id", "")).strip()
    gate_status = str(authorization.get("gate_status", "")).strip()
    result.update(
        reconnaissance_id=reconnaissance_id,
        authorization_id=authorization_id,
        gate_status=gate_status,
    )
    if reconnaissance.get("schema_version") != 1:
        errors.append("theme-reconnaissance.json schema_version must be 1")
    if authorization.get("schema_version") != 1:
        errors.append("modeling-authorization.json schema_version must be 1")
    if not fingerprint:
        errors.append("theme-reconnaissance.json must contain corpus_fingerprint")
    if not reconnaissance_id:
        errors.append("theme-reconnaissance.json must contain reconnaissance_id")
    if not str(reconnaissance.get("created_at", "")).strip():
        errors.append("theme-reconnaissance.json created_at must not be blank")
    if not str(reconnaissance.get("research_question", "")).strip():
        errors.append("theme-reconnaissance.json research_question must not be blank")
    for source, value in (
        ("corpus-profile.json", profile.get("corpus_fingerprint")),
        ("modeling-authorization.json", authorization.get("corpus_fingerprint")),
    ):
        if str(value or "").strip() != fingerprint:
            errors.append(f"{source} corpus_fingerprint does not match theme-reconnaissance.json")
    if str(authorization.get("reconnaissance_id", "")).strip() != reconnaissance_id:
        errors.append("modeling-authorization.json reconnaissance_id does not match")

    route = str(reconnaissance.get("route", "")).strip()
    if route not in ROUTES:
        errors.append("theme-reconnaissance.json route must be network-short, long-document, or mixed")
    user_theme = reconnaissance.get("user_theme")
    if not isinstance(user_theme, dict):
        errors.append("theme-reconnaissance.json user_theme must be an object")
    else:
        if not str(user_theme.get("mainline", "")).strip():
            errors.append("user_theme.mainline must not be blank")
        if user_theme.get("mode") != "coverage_and_interpretation_anchor":
            errors.append("user_theme.mode must be coverage_and_interpretation_anchor")
        if user_theme.get("allow_emergent_themes") is not True:
            errors.append("user_theme.allow_emergent_themes must be true")

    coverage = reconnaissance.get("coverage")
    if not isinstance(coverage, dict):
        errors.append("theme-reconnaissance.json coverage must be an object")
    else:
        source = _count(coverage.get("source_unit_count"), "coverage.source_unit_count", errors)
        eligible = _count(coverage.get("eligible_unit_count"), "coverage.eligible_unit_count", errors)
        reviewed = _count(coverage.get("reviewed_unit_count"), "coverage.reviewed_unit_count", errors)
        inherited = _count(
            coverage.get("duplicate_inherited_unit_count"),
            "coverage.duplicate_inherited_unit_count",
            errors,
        )
        excluded = _count(coverage.get("excluded_unit_count"), "coverage.excluded_unit_count", errors)
        failed = _count(coverage.get("failed_unit_count"), "coverage.failed_unit_count", errors)
        if None not in (source, eligible, reviewed, inherited, excluded, failed):
            profile_unit_count = _count(
                profile.get("unit_count"),
                "corpus-profile.json unit_count",
                errors,
            )
            if profile_unit_count is not None and source != profile_unit_count:
                errors.append("coverage.source_unit_count must match corpus-profile.json unit_count")
            if source != eligible + excluded:
                errors.append("coverage.source_unit_count must equal eligible_unit_count + excluded_unit_count")
            if eligible != reviewed + inherited + failed:
                errors.append(
                    "coverage.eligible_unit_count must equal reviewed_unit_count + duplicate_inherited_unit_count + failed_unit_count"
                )
            if failed != 0:
                errors.append("coverage.failed_unit_count must be zero before full-corpus coverage is claimed")
            if coverage.get("coverage_complete") is not True:
                errors.append("coverage.coverage_complete must be true")

    parent = reconnaissance.get("parent_document_coverage")
    if route in {"long-document", "mixed"}:
        if not isinstance(parent, dict) or parent.get("applicable") is not True:
            errors.append("Long-document and mixed routes require applicable parent_document_coverage")
        else:
            eligible_parent = _count(
                parent.get("eligible_parent_document_count"),
                "parent_document_coverage.eligible_parent_document_count",
                errors,
            )
            reviewed_parent = _count(
                parent.get("reviewed_parent_document_count"),
                "parent_document_coverage.reviewed_parent_document_count",
                errors,
            )
            failed_parent = _count(
                parent.get("failed_parent_document_count"),
                "parent_document_coverage.failed_parent_document_count",
                errors,
            )
            if None not in (eligible_parent, reviewed_parent, failed_parent):
                if eligible_parent != reviewed_parent + failed_parent:
                    errors.append("parent-document counts are inconsistent")
                if failed_parent != 0 or parent.get("coverage_complete") is not True:
                    errors.append("parent-document coverage must be complete with zero failures")

    candidate_ids: list[str] = []
    for index, row in enumerate(candidates, start=2):
        prefix = f"theme-candidate-audit.csv row {index}"
        candidate_id = str(row.get("candidate_theme_id", "")).strip()
        if not candidate_id:
            errors.append(f"{prefix} lacks candidate_theme_id")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix} duplicates candidate_theme_id {candidate_id}")
        else:
            candidate_ids.append(candidate_id)
        if str(row.get("reconnaissance_id", "")).strip() != reconnaissance_id:
            errors.append(f"{prefix} reconnaissance_id does not match")
        if str(row.get("hierarchy_level", "")).strip() not in HIERARCHY_LEVELS:
            errors.append(f"{prefix} hierarchy_level must be coarse or fine")
        if str(row.get("relation_to_user_mainline", "")).strip() not in RELATIONS:
            errors.append(f"{prefix} has an invalid relation_to_user_mainline")
        for field in (
            "route_subset",
            "provisional_label",
            "theme_type",
            "definition",
            "inclusion",
            "exclusion",
            "independent_support",
            "evidence_unit_ids",
            "source_or_parent_spread",
            "duplicate_or_artifact_risk",
            "uncertainty",
        ):
            if not str(row.get(field, "")).strip():
                errors.append(f"{prefix} lacks {field}")

    candidate_id_set = set(candidate_ids)
    candidate_levels = {
        str(row.get("candidate_theme_id", "")).strip(): str(
            row.get("hierarchy_level", "")
        ).strip()
        for row in candidates
        if str(row.get("candidate_theme_id", "")).strip()
    }
    for index, row in enumerate(candidates, start=2):
        parent_id = str(row.get("parent_candidate_theme_id", "")).strip()
        candidate_id = str(row.get("candidate_theme_id", "")).strip()
        if parent_id and parent_id not in candidate_id_set:
            errors.append(
                f"theme-candidate-audit.csv row {index} references unknown parent_candidate_theme_id"
            )
        if parent_id and parent_id == candidate_id:
            errors.append(
                f"theme-candidate-audit.csv row {index} cannot be its own parent"
            )

    estimate = reconnaissance.get("topic_count_estimate")
    if not isinstance(estimate, dict):
        errors.append("theme-reconnaissance.json topic_count_estimate must be an object")
    else:
        if estimate.get("interpretation") != "pre_model_hypothesis_not_target_k":
            errors.append("topic_count_estimate.interpretation must be pre_model_hypothesis_not_target_k")
        for level in ("coarse", "fine"):
            item = estimate.get(level)
            if not isinstance(item, dict):
                errors.append(f"topic_count_estimate.{level} must be an object")
                continue
            lower = _count(item.get("lower_bound"), f"topic_count_estimate.{level}.lower_bound", errors)
            point = _count(item.get("point_estimate"), f"topic_count_estimate.{level}.point_estimate", errors)
            upper = _count(item.get("upper_bound"), f"topic_count_estimate.{level}.upper_bound", errors)
            if None not in (lower, point, upper) and not lower <= point <= upper:
                errors.append(f"topic_count_estimate.{level} must satisfy lower_bound <= point_estimate <= upper_bound")
            ids = item.get("candidate_theme_ids")
            if not isinstance(ids, list) or not ids:
                errors.append(f"topic_count_estimate.{level}.candidate_theme_ids must be a non-empty list")
            else:
                unknown = sorted(set(map(str, ids)).difference(candidate_ids))
                if unknown:
                    errors.append(f"topic_count_estimate.{level} references unknown candidate IDs: {unknown}")
                wrong_level = sorted(
                    candidate_id
                    for candidate_id in map(str, ids)
                    if candidate_levels.get(candidate_id) != level
                )
                if wrong_level:
                    errors.append(
                        f"topic_count_estimate.{level} references candidates from another hierarchy level: {wrong_level}"
                    )
                if point is not None and point != len(set(map(str, ids))):
                    errors.append(
                        f"topic_count_estimate.{level}.point_estimate must equal the number of listed candidate_theme_ids"
                    )
            if not str(item.get("basis", "")).strip():
                errors.append(f"topic_count_estimate.{level}.basis must not be blank")

    excluded_artifacts = reconnaissance.get("excluded_artifact_candidate_ids")
    if not isinstance(excluded_artifacts, list):
        errors.append("excluded_artifact_candidate_ids must be a list")
    else:
        unknown_artifacts = sorted(set(map(str, excluded_artifacts)).difference(candidate_ids))
        if unknown_artifacts:
            errors.append(
                f"excluded_artifact_candidate_ids contains unknown candidate IDs: {unknown_artifacts}"
            )

    if gate_status not in GATE_STATES:
        errors.append("modeling-authorization.json has an invalid gate_status")
    may_start = authorization.get("modeling_may_start")
    if not isinstance(may_start, bool):
        errors.append("modeling_may_start must be a boolean")
    elif may_start != (gate_status == "approved_for_modeling"):
        errors.append("modeling_may_start must be true only for approved_for_modeling")
    if authorization.get("user_theme_mode") != "coverage_and_interpretation_anchor":
        errors.append("modeling-authorization.json user_theme_mode must be coverage_and_interpretation_anchor")
    if authorization.get("allow_emergent_themes") is not True:
        errors.append("modeling-authorization.json allow_emergent_themes must be true")

    if gate_status == "approved_for_modeling":
        if not authorization_id:
            errors.append("approved modeling requires authorization_id")
        if not str(authorization.get("user_instruction", "")).strip():
            errors.append("approved modeling requires user_instruction")
        if not str(authorization.get("decision_recorded_at", "")).strip():
            errors.append("approved modeling requires decision_recorded_at")
        resolved = authorization.get("resolved_candidate_theme_ids")
        if not isinstance(resolved, list) or set(map(str, resolved)) != set(candidate_ids):
            errors.append("resolved_candidate_theme_ids must match every candidate theme exactly")
        for index, row in enumerate(candidates, start=2):
            disposition = str(row.get("user_disposition", "")).strip()
            if disposition not in DISPOSITIONS:
                errors.append(f"theme-candidate-audit.csv row {index} requires a valid user_disposition")
            if not str(row.get("user_instruction", "")).strip():
                errors.append(f"theme-candidate-audit.csv row {index} requires user_instruction")
    if require_approval and gate_status != "approved_for_modeling":
        errors.append("gate_status must be approved_for_modeling before modeling")

    result["valid"] = not errors
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate full-corpus theme reconnaissance")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--require-approval", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = validate_theme_reconnaissance(
        args.bundle,
        require_approval=args.require_approval,
    )
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote reconnaissance audit: {args.output}")
    else:
        print(rendered)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the initial tests and verify success**

Run:

```powershell
python -B -m unittest scripts.tests.test_theme_reconnaissance -v
```

Expected: the three initial tests pass.

- [ ] **Step 5: Add gate, identity, range, parent-document, and CLI tests**

Add tests that make these exact assertions:

```python
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
        path = root / "modeling-authorization.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["corpus_fingerprint"] = "sha256:other"
        path.write_text(json.dumps(payload), encoding="utf-8")
        result = validate_theme_reconnaissance(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("corpus_fingerprint" in e for e in result["errors"]))

def test_unordered_topic_range_is_rejected(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_preview(root)
        path = root / "theme-reconnaissance.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["topic_count_estimate"]["fine"].update(
            lower_bound=3, point_estimate=2, upper_bound=1
        )
        path.write_text(json.dumps(payload), encoding="utf-8")
        result = validate_theme_reconnaissance(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("lower_bound <= point_estimate" in e for e in result["errors"]))

def test_long_document_route_requires_complete_parent_coverage(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_preview(root)
        path = root / "theme-reconnaissance.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["route"] = "long-document"
        path.write_text(json.dumps(payload), encoding="utf-8")
        result = validate_theme_reconnaissance(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("parent_document_coverage" in e for e in result["errors"]))

def test_cli_returns_zero_for_valid_waiting_preview(self):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_preview(root)
        completed = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS_DIR / "validate_theme_reconnaissance.py"), str(root)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["valid"])
```

Also add one approval test that removes a candidate disposition and asserts the validator rejects it, and one test that sets `modeling_may_start=true` while awaiting and asserts rejection.

- [ ] **Step 6: Run the complete validator test module**

Run:

```powershell
python -B -m unittest scripts.tests.test_theme_reconnaissance -v
```

Expected: every reconnaissance validation test passes.

- [ ] **Step 7: Materialize the reusable awaiting fixture**

Create `scripts/tests/fixtures/theme-reconnaissance-awaiting/` with the same content produced when the test helper `write_preview` receives `gate_status="awaiting_user_direction"`. Run:

```powershell
python -B scripts/validate_theme_reconnaissance.py scripts/tests/fixtures/theme-reconnaissance-awaiting
```

Expected: JSON output contains `"valid": true` and `"gate_status": "awaiting_user_direction"`.

Then run:

```powershell
python -B scripts/validate_theme_reconnaissance.py scripts/tests/fixtures/theme-reconnaissance-awaiting --require-approval
```

Expected: non-zero exit and an error stating that `gate_status` must be `approved_for_modeling`.

---

### Task 3: Enforce the authorization gate in completed study bundles

**Files:**

- Modify: `scripts/validate_study_bundle.py`
- Modify: `scripts/tests/test_tools.py`
- Modify: `scripts/tests/fixtures/lexicon-study-bundle/study-contract.json`
- Modify: `scripts/tests/fixtures/lexicon-study-bundle/experiment-registry.csv`
- Create: `scripts/tests/fixtures/lexicon-study-bundle/theme-reconnaissance.json`
- Create: `scripts/tests/fixtures/lexicon-study-bundle/theme-candidate-audit.csv`
- Create: `scripts/tests/fixtures/lexicon-study-bundle/modeling-authorization.json`

**Interfaces:**

- Consumes: `validate_theme_reconnaissance(root, require_approval=True)` and its returned `authorization_id`.
- Produces: a completed study bundle that is invalid unless every modeling registry row links to the approved authorization.

- [ ] **Step 1: Write the failing completed-bundle gate test**

Import the new validator in `scripts/tests/test_tools.py`, migrate `test_complete_bundle_passes` to write approved reconnaissance artifacts, and add:

```python
def test_modeling_registry_rejects_missing_or_mismatched_authorization(self):
    fixture = Path(__file__).resolve().parent / "fixtures" / "lexicon-study-bundle"
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for source in fixture.iterdir():
            if source.is_file():
                (root / source.name).write_bytes(source.read_bytes())
        registry = root / "experiment-registry.csv"
        rows = list(csv.DictReader(registry.open("r", encoding="utf-8-sig", newline="")))
        fieldnames = list(rows[0])
        rows[0]["authorization_id"] = "auth-wrong"
        with registry.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        result = validate_bundle(root)
        self.assertFalse(result["valid"])
        self.assertTrue(any("authorization_id" in e for e in result["errors"]))
```

- [ ] **Step 2: Run the gate test and confirm failure**

Run:

```powershell
python -B -m unittest scripts.tests.test_tools.StudyBundleValidationTests.test_modeling_registry_rejects_missing_or_mismatched_authorization -v
```

Expected: failure because `validate_study_bundle.py` does not yet enforce the new ID.

- [ ] **Step 3: Integrate the standalone validator**

Modify `scripts/validate_study_bundle.py` as follows:

```python
from validate_theme_reconnaissance import validate_theme_reconnaissance
```

Add the new files to `REQUIRED_FILES`:

```python
"theme-reconnaissance.json",
"theme-candidate-audit.csv",
"modeling-authorization.json",
```

Add `pre_model_reconnaissance` to `CONTRACT_FIELDS` and `authorization_id` to the required fields for `experiment-registry.csv`.

After all tables are read, add this exact enforcement block:

```python
reconnaissance_audit = validate_theme_reconnaissance(root, require_approval=True)
errors.extend(
    f"Theme reconnaissance: {item}" for item in reconnaissance_audit["errors"]
)
approved_authorization_id = str(
    reconnaissance_audit.get("authorization_id", "")
).strip()
modeling_run_types = {"baseline", "structural", "representation", "taxonomy", "mapping"}
for index, row in enumerate(tables.get("experiment-registry.csv", []), start=2):
    run_type = str(row.get("run_type", "")).strip().casefold()
    if run_type not in modeling_run_types:
        continue
    row_authorization_id = str(row.get("authorization_id", "")).strip()
    if not row_authorization_id:
        errors.append(
            f"experiment-registry.csv row {index} modeling run lacks authorization_id"
        )
    elif row_authorization_id != approved_authorization_id:
        errors.append(
            f"experiment-registry.csv row {index} authorization_id does not match the approved reconnaissance"
        )
```

Validate the contract policy with these exact conditions:

```python
policy = contract.get("pre_model_reconnaissance")
if not isinstance(policy, dict):
    errors.append("study-contract.json pre_model_reconnaissance must be an object")
else:
    expected = {
        "required": True,
        "user_theme_mode": "coverage_and_interpretation_anchor",
        "allow_emergent_themes": True,
        "reconnaissance_artifact": "theme-reconnaissance.json",
        "candidate_audit_artifact": "theme-candidate-audit.csv",
        "authorization_artifact": "modeling-authorization.json",
        "user_authorization_required": True,
    }
    for field, value in expected.items():
        if policy.get(field) != value:
            errors.append(
                f"pre_model_reconnaissance.{field} must be {value!r}"
            )
```

- [ ] **Step 4: Migrate both completed fixtures**

Update the dynamically created bundle in `test_complete_bundle_passes` and the persistent `lexicon-study-bundle` fixture with:

- the exact policy from Task 1;
- a complete approved reconnaissance whose fingerprint matches `corpus-profile.json`;
- fully disposed candidate rows;
- an approval record with `gate_status=approved_for_modeling`;
- the matching `authorization_id` in every registry modeling row.

The fixture topic estimate must be derived from its candidate rows and satisfy `lower_bound <= point_estimate <= upper_bound`; do not use an unrelated decorative range.

- [ ] **Step 5: Run focused completed-bundle tests**

Run:

```powershell
python -B -m unittest scripts.tests.test_tools.StudyBundleValidationTests.test_complete_bundle_passes scripts.tests.test_tools.StudyBundleValidationTests.test_complete_lexicon_enabled_fixture_passes scripts.tests.test_tools.StudyBundleValidationTests.test_modeling_registry_rejects_missing_or_mismatched_authorization -v
```

Expected: all three tests pass.

- [ ] **Step 6: Validate the persistent completed fixture through the CLI**

Run:

```powershell
python -X utf8 -B scripts/validate_study_bundle.py scripts/tests/fixtures/lexicon-study-bundle
```

Expected: JSON output contains `"valid": true` and no errors.

---

### Task 4: Document the full-corpus operating method and pause behavior

**Files:**

- Create: `references/corpus-theme-reconnaissance.md`
- Modify: `SKILL.md`
- Modify: `references/network-short-text.md`
- Modify: `references/long-document.md`
- Modify: `references/study-contract-and-reporting.md`
- Modify: `references/bertopic-implementation.md`
- Modify: `README.md`
- Modify: `agents/openai.yaml`
- Modify: `HANDOFF.md`
- Test: `scripts/tests/test_tools.py`

**Interfaces:**

- Consumes: the artifact and validator names fixed in Tasks 1–3.
- Produces: one unambiguous agent workflow from corpus receipt through user authorization and later preview-versus-model evaluation.

- [ ] **Step 1: Write the failing integration test**

Add this test to `SkillInstructionTests`:

```python
def test_full_corpus_reconnaissance_is_integrated_and_guarded(self):
    skill_root = Path(__file__).resolve().parents[2]
    required_text = {
        "SKILL.md": "awaiting_user_direction",
        "references/corpus-theme-reconnaissance.md": "coverage_and_interpretation_anchor",
        "references/network-short-text.md": "duplicate_inherited_unit_count",
        "references/long-document.md": "parent_document_coverage",
        "references/study-contract-and-reporting.md": "modeling-authorization.json",
        "references/bertopic-implementation.md": "approved_for_modeling",
        "README.md": "validate_theme_reconnaissance.py",
        "agents/openai.yaml": "全量主题预侦察",
    }
    for relative, needle in required_text.items():
        path = skill_root / relative
        self.assertTrue(path.is_file(), relative)
        self.assertIn(needle, path.read_text(encoding="utf-8"), relative)

    skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    reconnaissance_position = skill_text.index("awaiting_user_direction")
    baseline_position = skill_text.index("Establish an auditable baseline")
    self.assertLess(reconnaissance_position, baseline_position)
    self.assertIn("pre_model_hypothesis_not_target_k", skill_text)
```

- [ ] **Step 2: Run the integration test and confirm failure**

Run:

```powershell
python -B -m unittest scripts.tests.test_tools.SkillInstructionTests.test_full_corpus_reconnaissance_is_integrated_and_guarded -v
```

Expected: failure naming the missing reference and missing workflow terms.

- [ ] **Step 3: Write `references/corpus-theme-reconnaissance.md`**

Use the approved design specification as the source of truth and include these sections in order:

1. purpose and non-model status;
2. user-theme brief and `coverage_and_interpretation_anchor` default;
3. full-accounting equations;
4. batch reading with stable IDs and evidence retention;
5. candidate hierarchy and topic-count range derivation;
6. route-specific rules for `network-short`, `long-document`, and `mixed`;
7. user-facing report order;
8. `awaiting_user_direction` pause behavior;
9. candidate dispositions and approval transition;
10. later preview-versus-model coverage audit;
11. commands and required outputs;
12. red flags.

Include these exact equations and prohibitions:

```text
source_unit_count = eligible_unit_count + excluded_unit_count
eligible_unit_count = reviewed_unit_count + duplicate_inherited_unit_count + failed_unit_count
full coverage requires failed_unit_count = 0
```

```text
The point estimate is the current evidence-linked candidate map.
The lower bound reflects defensible merges.
The upper bound reflects unresolved defensible splits.
None of these values is a forced BERTopic topic count.
```

- [ ] **Step 4: Insert the stage into `SKILL.md`**

Make `references/corpus-theme-reconnaissance.md` an always-read reference. Add a non-negotiable rule forbidding model fitting before approved authorization. Insert a new required workflow step after “Inspect and fingerprint” and before “Create the study contract” that requires:

- full eligible-corpus accounting;
- evidence-linked coarse/fine estimates;
- mainline/supporting/contextual/emergent/artifact/uncertain classification;
- reporting to the user;
- `gate_status=awaiting_user_direction` and an immediate pause;
- explicit approval before the contract is frozen or baseline fit begins.

Renumber every subsequent workflow heading and internal cross-reference once; do not retain duplicate old/new numbering. Add the three artifacts and standalone validation command to the research-bundle and output sections:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory>
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
```

- [ ] **Step 5: Add route-specific and implementation rules**

In `references/network-short-text.md`, state that only exact duplicates may use `duplicate_inherited_unit_count`, while near duplicates remain independently reviewed. Require source/account/thread/time evidence for candidate themes.

In `references/long-document.md`, require `parent_document_coverage`, traceable provisional segments, section paths, and offsets. State that reconnaissance segmentation does not freeze the later chunk policy.

In `references/study-contract-and-reporting.md`, define all three artifacts, the contract policy, registry authorization link, preview-versus-model reporting, and reproducibility-bundle membership.

In `references/bertopic-implementation.md`, place this guard immediately before model construction or fitting:

```python
audit = validate_theme_reconnaissance(study_root, require_approval=True)
if not audit["valid"]:
    raise ValueError("Modeling is blocked until theme reconnaissance is approved")
authorization_id = audit["authorization_id"]
```

State that every experiment registry row must carry `authorization_id`.

- [ ] **Step 6: Update public and local project documentation**

Update `README.md` in the feature list, end-to-end workflow, included tools, study templates, repository tree, validation section, and scope. Explain that the tool validates the pause gate but does not perform provider-specific LLM calls.

Update `agents/openai.yaml` so the Chinese default prompt requires “全量主题预侦察、先汇报预估、等待用户指示后再建模”.

Update `HANDOFF.md` with the new feature boundary, files, validation commands, test baseline after actual execution, and package snapshot after rebuilding. Preserve every existing privacy prohibition and never copy private handoff content into public files.

- [ ] **Step 7: Run the integration and identity tests**

Run:

```powershell
python -B -m unittest scripts.tests.test_tools.SkillInstructionTests -v
```

Expected: all skill instruction tests pass, including identity, parameter-transfer firewall, lexicon integration, and full-corpus reconnaissance integration.

---

### Task 5: Add regression cases for every forbidden transition

**Files:**

- Modify: `scripts/tests/test_theme_reconnaissance.py`
- Modify: `scripts/tests/test_tools.py`

**Interfaces:**

- Consumes: final validator behavior from Tasks 2–3.
- Produces: regression coverage that prevents silent relaxation of full coverage or the user gate.

- [ ] **Step 1: Add focused negative tests**

Add one test for each of these mutations of the valid helper fixture:

- duplicate candidate ID;
- candidate row with a mismatched reconnaissance ID;
- unknown candidate ID in a topic estimate;
- point estimate that differs from the number of listed candidate IDs;
- candidate with an unknown or self-referential parent ID;
- source-unit count that differs from `corpus-profile.json`;
- blank research question or creation timestamp;
- blank evidence unit IDs;
- `allow_emergent_themes=false`;
- `revision_requested` with `modeling_may_start=true`;
- approval without a decision timestamp;
- approval whose resolved candidate IDs omit one row;
- approval whose candidate disposition is blank;
- long-document parent counts that do not balance;
- corpus fingerprint changed after approval;
- completed study registry row missing `authorization_id`;
- completed study registry row linked to a different approval.

Each test must assert both `valid is False` and a specific error substring naming the violated field. Do not assert only that “some error occurred.”

- [ ] **Step 2: Run the reconnaissance and study-bundle test classes**

Run:

```powershell
python -B -m unittest scripts.tests.test_theme_reconnaissance scripts.tests.test_tools.StudyBundleValidationTests -v
```

Expected: all tests pass.

- [ ] **Step 3: Check deterministic text formats**

Extend `test_hashed_text_resources_use_stable_line_endings` to include:

```python
"assets/theme-reconnaissance.json",
"assets/theme-candidate-audit.csv",
"assets/modeling-authorization.json",
```

Run:

```powershell
python -B -m unittest scripts.tests.test_tools.SkillInstructionTests.test_hashed_text_resources_use_stable_line_endings -v
```

Expected: `PASS`; none of the new hashed resources contains CRLF.

---

### Task 6: Run complete verification and rebuild the single portable package

**Files:**

- Modify after measured results: `HANDOFF.md`
- Replace after validation: `F:\Skill\Codex\bertopic-tuning.skill.zip`

**Interfaces:**

- Consumes: all source, tests, templates, and documentation from Tasks 1–5.
- Produces: one validated project tree, one validated portable package, and an updated private maintenance snapshot.

- [ ] **Step 1: Run every project test**

Run:

```powershell
python -B -m unittest discover -s scripts/tests -v
```

Expected: all tests pass. Record the actual `Ran N tests` value; do not preserve the old count if it changed.

- [ ] **Step 2: Run the Codex skill validator**

Run:

```powershell
python -X utf8 -B 'D:\Codex work\.codex\skills\.system\skill-creator\scripts\quick_validate.py' 'F:\Skill\Codex\.agents\skills\bertopic-tuning'
```

Expected: `Skill is valid!`.

- [ ] **Step 3: Run both governance validators**

Run:

```powershell
python -X utf8 -B scripts/validate_theme_reconnaissance.py scripts/tests/fixtures/theme-reconnaissance-awaiting
python -X utf8 -B scripts/validate_study_bundle.py scripts/tests/fixtures/lexicon-study-bundle
```

Expected: both commands return zero and output `"valid": true`.

Also run the negative approval check:

```powershell
python -X utf8 -B scripts/validate_theme_reconnaissance.py scripts/tests/fixtures/theme-reconnaissance-awaiting --require-approval
```

Expected: non-zero exit caused only by the intentional `awaiting_user_direction` state.

- [ ] **Step 4: Build the package from the permitted roots only**

Create the archive from exactly these entries:

```text
SKILL.md
agents/
references/
scripts/
assets/
```

Build to a temporary ZIP under the writable workspace, inspect and extract it, run the full test suite and skill validator against the extracted root, then replace `F:\Skill\Codex\bertopic-tuning.skill.zip` only after all extracted-package checks pass. The archive must not contain `HANDOFF.md`, `README.md`, `LICENSE`, `.git`, caches, compiled bytecode, or the planning documents.

- [ ] **Step 5: Run the package privacy and content audit**

Use PowerShell’s `System.IO.Compression.ZipFile` reader to assert:

- exactly one root-level `SKILL.md` exists;
- the three new assets exist;
- `references/corpus-theme-reconnaissance.md` exists;
- `scripts/validate_theme_reconnaissance.py` exists;
- no entry matches `(^|/)HANDOFF\.md$`;
- no entry contains `.git`, `__pycache__`, `.pyc`, `README.md`, or `LICENSE`.

Expected: all required entries are present and all forbidden-entry queries return no rows.

- [ ] **Step 6: Record the measured handoff snapshot**

Calculate the final package byte size and SHA-256, then update `HANDOFF.md` with:

- the actual test count and `OK` result;
- the standalone reconnaissance validation result;
- the completed study-bundle validation result;
- the skill validation result;
- the package byte size and SHA-256;
- the added files and workflow boundary;
- explicit confirmation that `HANDOFF.md` was not packaged or published.

- [ ] **Step 7: Final self-review against the design**

Verify each design requirement maps to a passing test or inspected artifact:

- full eligible-unit accounting;
- exact-duplicate-only inherited review;
- long-document parent coverage;
- coarse/fine evidence-linked ranges;
- user mainline plus open emergent themes;
- report-before-model pause;
- explicit candidate dispositions;
- approved authorization before modeling;
- authorization linkage in experiment registry;
- preview-versus-model reporting;
- no provider-specific dependency or forced K;
- one portable package with no private handoff material.

Completion requires every item above. A passing model fit is neither required nor sufficient for this feature.
