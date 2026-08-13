# BERTopic Tuning GitHub Productization Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan.

**Goal:** Make BERTopic Tuning immediately understandable, installable,
verifiable, plugin-compatible, and release-ready without changing its modeling
semantics.

**Architecture:** Keep one canonical root skill, add public-facing repository
layers around it, and use the current standard-library validators as the
behavioral contract.

**Tech stack:** Markdown, YAML, JSON, Python standard library, GitHub Actions,
Codex skill/plugin manifests, PNG/SVG assets.

### Task 1: Build an executable quickstart

**Files:**
- Create: `examples/quickstart/README.md`
- Create: `examples/quickstart/inputs/*`
- Create: `examples/quickstart/expected/*`

1. Select the smallest existing semantic-review fixture that exercises real
   scripts without network access.
2. Copy only the necessary inputs into the public example.
3. Run the documented command and save a compact expected result.
4. Re-run from a clean output directory and confirm byte-stable output where
   the script promises determinism.

### Task 2: Rewrite the repository entry experience

**Files:**
- Modify: `README.md`
- Create: `CHANGELOG.md`

1. Add badges, one-sentence value, differentiator, verified output preview,
   exact installation commands, and an exact invocation prompt.
2. Link the executable quickstart and retain the assurance/modeling reference
   material below it.
3. Add a concise limitations section and a companion-project cross-link.
4. Record the complete public release in the changelog.

### Task 3: Add CI and community health

**Files:**
- Create: `.github/workflows/validate.yml`
- Create: `.github/CODE_OF_CONDUCT.md`
- Create: `.github/CONTRIBUTING.md`
- Create: `.github/SECURITY.md`
- Create: `.github/SUPPORT.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/pull_request_template.md`

1. Run the full suite on Ubuntu and Windows with Python UTF-8 enabled.
2. Use `actions/checkout@v6` and `actions/setup-python@v6`.
3. Add project-specific contribution, security, and issue guidance.
4. Run the workflow command locally once more.

### Task 4: Add Codex UI and plugin packaging

**Files:**
- Modify: `agents/openai.yaml`
- Create: `.codex-plugin/plugin.json`
- Create: `assets/icon-small.png`
- Create: `assets/icon-large.png`
- Create: `assets/social-preview.png`

1. Generate a text-free cluster/champion icon and a GitHub social preview.
2. Inspect the generated images at original resolution and reject text or
   composition errors.
3. Add concise UTF-8 UI metadata, brand color, icons, and exact default prompt.
4. Validate the skill folder and plugin root with the official validators.

### Task 5: Verify and publish

1. Run all 190 tests, example commands, link checks, skill validation, and
   plugin validation.
2. Review the complete diff and commit only repository-scoped files.
3. Push the productization branch, open a reviewable PR, wait for CI, and merge.
4. Set description, Topics, Discussions, and custom social preview.
5. Create and verify tag/release `v1.0.0`.
