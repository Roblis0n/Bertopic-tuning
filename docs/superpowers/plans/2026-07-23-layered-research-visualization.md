# Layered Research-Grade BERTopic Visualization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a corpus-agnostic, four-layer BERTopic visualization contract that plans and validates seven baseline views plus governance and conditional research figures.

**Architecture:** A deterministic standard-library planner converts a generic visualization contract into a complete figure registry; a separate validator checks the frozen contract-plan-manifest chain and rendered artifacts. BERTopic/Plotly rendering stays in the user's modeling environment, while the skill reference maps native methods and custom diagnostic plots to the audited registry.

**Tech Stack:** Markdown skill/reference documentation, UTF-8 JSON templates, Python 3 standard library, `unittest`, existing Codex skill validator, local Git and GitHub HTTPS remote.

## Global Constraints

- Complete the feature in one implementation; do not create duplicate `v1`, `v2`, `final`, or `latest` files.
- Do not hard-code any single case study, language-specific labels, manuscript figure numbers, topic counts, or case-specific metadata fields.
- Preserve the existing `network-short`, `long-document`, and `mixed` routes.
- Keep command-line governance tools on the Python standard library.
- Do not introduce universal topic counts, display thresholds, sample sizes, metric weights, or copied paper parameters.
- Keep structure, representation, taxonomy, and governance visually and semantically separate.
- Include Topic `-1` explicitly in document, prevalence, and outlier reporting.
- Use one frozen document-coordinate artifact for interactive and static document maps.
- Declare whether every topic relation is lexical c-TF-IDF or semantic/topic-embedding based.
- Require self-contained HTML, vector, PNG, source data, caption, alt text, and SHA-256 evidence for each required figure.
- Keep `HANDOFF.md` private and unstaged.

---

## File map

### Create

- `scripts/build_visualization_plan.py` — deterministic figure planner.
- `scripts/validate_visualization_bundle.py` — rendered-bundle validator.
- `scripts/tests/test_visualization_bundle.py` — planner, validator, CLI, and documentation tests.
- `assets/visualization-contract.json` — generic configurable contract template.
- `assets/visualization-manifest.json` — rendered artifact manifest template.
- `references/research-grade-visualization.md` — complete plotting and interpretation workflow.
- `docs/superpowers/specs/2026-07-23-layered-research-visualization-design.md` — approved architecture and boundaries.
- `docs/superpowers/plans/2026-07-23-layered-research-visualization.md` — this executable plan.

### Modify

- `SKILL.md` — require the visualization stage and reference.
- `README.md` — document figures, tools, templates, workflow, validation, and scope.
- `agents/openai.yaml` — make research-grade visualization discoverable.
- `assets/study-contract.json` — link the visualization policy without embedding case fields.
- `assets/decision-report.md` — add the layered-visualization evidence section.
- `references/study-contract-and-reporting.md` — register visualization artifacts in the research bundle.
- `references/network-short-text.md` — require the route artifact audit.
- `references/long-document.md` — require the parent-document profile.
- `scripts/validate_study_bundle.py` — validate the visualization policy links when present and require them in the reusable study contract.
- `scripts/tests/test_tools.py` — cover policy/template integration without duplicating the standalone artifact tests.
- `HANDOFF.md` — private maintenance snapshot after measured verification and publication.

## Task 1: Define behavior with failing tests

**Files:**

- Create: `scripts/tests/test_visualization_bundle.py`
- Modify: `scripts/tests/test_tools.py`

**Interfaces:**

- Imports to define: `build_plan`, `CORE_FIGURE_IDS`, `validate_visualization_bundle`.
- Fixture helper: `write_complete_visualization_bundle(root: Path, *, route: str, enabled_modules: set[str]) -> None`.

- [ ] **Step 1: Write planner contract tests**

Add tests that import the missing planner and assert:

```python
plan = build_plan(make_contract(root, route="mixed"))
self.assertEqual(
    [figure["figure_id"] for figure in plan["figures"] if figure["requirement"] == "core"],
    list(CORE_FIGURE_IDS),
)
self.assertIn("topic-term-barchart", CORE_FIGURE_IDS)
self.assertIn("document-map", CORE_FIGURE_IDS)
self.assertIn("topic-map", CORE_FIGURE_IDS)
self.assertIn("topic-similarity-heatmap", CORE_FIGURE_IDS)
self.assertIn("topic-hierarchy", CORE_FIGURE_IDS)
self.assertIn("ctfidf-term-score-decline", CORE_FIGURE_IDS)
```

Also assert that a custom `field_map` survives unchanged, missing core inputs produce `blocked_missing_inputs`, `mixed` activates both route figures, and enabled time/group/geography/lineage/distribution modules activate only their own figures.

- [ ] **Step 2: Write artifact validation tests**

The temporary complete bundle writes valid HTML, SVG, a one-pixel PNG, CSV, Markdown, and text artifacts with real SHA-256 values. Assert:

```python
audit = validate_visualization_bundle(root)
self.assertTrue(audit["valid"], audit["errors"])
```

Add exact negative mutations for missing required figure, stale plan, changed snapshot, changed file hash, `../` path traversal, remote `<script src="https://...">`, invalid PNG signature, relation-basis mismatch, taxonomy relation mismatch, missing Topic `-1` policy, and `title_location != "caption"`.

- [ ] **Step 3: Write CLI tests**

Run the missing planner with `--require-ready` against an incomplete contract and assert a non-zero exit plus a written plan. Run the missing validator against the complete temporary bundle and assert zero plus machine-readable `"valid": true`.

- [ ] **Step 4: Write documentation integration tests**

Assert that `SKILL.md`, `README.md`, `references/research-grade-visualization.md`, `assets/visualization-contract.json`, `assets/visualization-manifest.json`, and `agents/openai.yaml` exist and contain the semantic IDs, all seven supplied filenames/method names, the four layers, `topic_minus_one`, `self_contained_html`, and both CLI names.

- [ ] **Step 5: Run the new module and observe RED**

Run:

```powershell
python -B -m unittest scripts.tests.test_visualization_bundle -v
```

Expected: import failure because `build_visualization_plan.py` and `validate_visualization_bundle.py` do not yet exist.

## Task 2: Implement the deterministic visualization planner

**Files:**

- Create: `scripts/build_visualization_plan.py`
- Test: `scripts/tests/test_visualization_bundle.py`

**Interfaces:**

- `CORE_FIGURE_IDS: tuple[str, ...]`
- `build_plan(contract: dict[str, Any]) -> dict[str, Any]`
- `validate_contract(contract: dict[str, Any]) -> list[str]`
- CLI: `--contract PATH --output PATH [--require-ready]`

- [ ] **Step 1: Implement the semantic figure registry**

Define eleven immutable core records with figure ID, layer, question, required input IDs, basis source, outlier policy, required outputs, and activation reason. Define route and conditional records separately. Use the preferred output stems only as generic suggestions; do not enforce manuscript numbers.

- [ ] **Step 2: Implement contract validation**

Require study/snapshot/route identity, generic unit/topic fields, artifact mapping, projection and relation spaces, explicit outlier identity, and the exact research export policy. An enabled conditional module must register its required field mapping and source artifact.

- [ ] **Step 3: Implement deterministic plan construction**

Canonicalize JSON with sorted keys, derive `contract_sha256` and `plan_id`, emit core figures in registry order, activate route/metadata figures, preserve disabled modules as `not_applicable`, list missing input IDs, and summarize ready/blocked/not-applicable counts. Do not include a clock time.

- [ ] **Step 4: Implement the CLI**

Always write the plan when JSON is parseable. Return non-zero for contract errors, and also for required blocked figures when `--require-ready` is set.

- [ ] **Step 5: Run planner tests**

Run:

```powershell
python -B -m unittest scripts.tests.test_visualization_bundle.VisualizationPlanTests scripts.tests.test_visualization_bundle.VisualizationCliTests.test_require_ready_rejects_blocked_plan -v
```

Expected: all selected tests pass.

## Task 3: Implement the rendered visualization bundle validator

**Files:**

- Create: `scripts/validate_visualization_bundle.py`
- Test: `scripts/tests/test_visualization_bundle.py`

**Interfaces:**

- `validate_visualization_bundle(root: Path) -> dict[str, Any]`
- CLI: `BUNDLE [--output PATH]`

- [ ] **Step 1: Implement safe artifact reading**

Resolve every path relative to the bundle, reject absolute/path-traversal targets, read bytes once, validate `sha256:<64 hex>`, and compare the recorded digest with the actual bytes.

- [ ] **Step 2: Enforce the contract-plan chain**

Load the three root JSON files, rebuild the plan with `build_plan`, and reject any stale or manually edited controlled plan. Reject contract errors and any required figure whose plan state is blocked.

- [ ] **Step 3: Validate figure records and formats**

Require each ready planned figure once. Enforce identity, layer, inputs, basis, projection/relation/color links, outlier policy, question, interpretation, limitations, render parameters, `title_location: caption`, and output keys:

```python
REQUIRED_OUTPUTS = (
    "interactive_html",
    "static_vector",
    "static_raster",
    "source_data",
    "caption",
    "alt_text",
)
```

Check `<html`, `<svg` or `%PDF-`, PNG magic bytes, allowed source-data extensions, nonblank captions/alt text, and unique output paths.

- [ ] **Step 4: Enforce cross-figure research invariants**

Require the document map's three visual forms to link one frozen projection; require the heatmap and hierarchy to link the same taxonomy relation artifact and basis; require explicit Topic `-1` display in document map, prevalence, and outlier diagnostics; reject external script/stylesheet resources in self-contained HTML.

- [ ] **Step 5: Run validator tests**

Run:

```powershell
python -B -m unittest scripts.tests.test_visualization_bundle.VisualizationBundleTests -v
```

Expected: valid bundle passes and every named mutation fails for its specific reason.

## Task 4: Add templates and the complete plotting reference

**Files:**

- Create: `assets/visualization-contract.json`
- Create: `assets/visualization-manifest.json`
- Create: `references/research-grade-visualization.md`

**Interfaces:**

- Contract keys consumed by `build_plan`.
- Manifest keys consumed by `validate_visualization_bundle`.

- [ ] **Step 1: Add the generic contract template**

Include all core artifact IDs, generic field-map slots, document projection, topic/taxonomy relation spaces, conditional modules, Topic `-1`, and exact export-policy booleans. Leave corpus-specific values blank and use `pending_local_calibration` only for genuinely uncalibrated rendering choices.

- [ ] **Step 2: Add the manifest template**

Include root identity fields and one commented-by-structure example record without comments (valid JSON). The template must remain generic and invalid as a claimed completed bundle until populated.

- [ ] **Step 3: Write the reference workflow**

Cover, in order:

1. the four-layer question map;
2. prepare/freeze contract and input artifacts;
3. build/inspect the plan;
4. render the seven baseline views;
5. render governance figures;
6. activate route/metadata figures;
7. preserve coordinate/relation/color consistency;
8. export HTML/vector/PNG/source/caption/alt;
9. write captions and limitations;
10. validate the bundle;
11. route-specific requirements;
12. common failures and interpretation limits.

Map native BERTopic methods without copying their numerical defaults. State that `visualize_topics` can be lexical or embedding-based, heatmap/hierarchy must declare `use_ctfidf`, and `visualize_documents` plus `visualize_document_datamap` must receive the same reduced embeddings.

- [ ] **Step 4: Run documentation/template tests**

Run:

```powershell
python -B -m unittest scripts.tests.test_visualization_bundle.VisualizationDocumentationTests -v
```

Expected: all required files, figures, methods, layers, policies, and commands are present.

## Task 5: Integrate visualization into the public skill and study contract

**Files:**

- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `agents/openai.yaml`
- Modify: `assets/study-contract.json`
- Modify: `assets/decision-report.md`
- Modify: `references/study-contract-and-reporting.md`
- Modify: `references/network-short-text.md`
- Modify: `references/long-document.md`
- Modify: `scripts/validate_study_bundle.py`
- Modify: `scripts/tests/test_tools.py`

**Interfaces:**

- `study-contract.json.visualization_policy`
- `validate_visualization_policy(contract: dict[str, Any]) -> list[str]`

- [ ] **Step 1: Add the failing study-policy test**

Require the reusable study contract to contain:

```json
{
  "visualization_policy": {
    "required": true,
    "contract_artifact": "visualization-contract.json",
    "plan_artifact": "visualization-plan.json",
    "manifest_artifact": "visualization-manifest.json",
    "validation_command": "python scripts/validate_visualization_bundle.py <study-bundle-directory>",
    "layer_model": ["structure", "representation", "taxonomy", "governance"],
    "shared_document_coordinates_required": true,
    "topic_minus_one_visible": true
  }
}
```

Test that the reusable contract passes and missing/wrong fields fail through `validate_visualization_policy`.

- [ ] **Step 2: Integrate `SKILL.md`**

Always-read `references/research-grade-visualization.md`. Insert a required visualization stage after model selection and before iteration/report completion. Require the generated plan, all ready core/route/conditional figures, shared coordinates, explicit relation basis, Topic `-1`, artifact forms, and validation command. Renumber subsequent stages once.

- [ ] **Step 3: Integrate public documentation and metadata**

Add the layered figure system to README features, workflow, CLI tools, templates, references, repository tree, validation, and scope. Update the Chinese default prompt to request a “分层研究级图谱及可复现图件清单” without case-specific wording.

- [ ] **Step 4: Integrate study reporting**

Add the visualization policy to `assets/study-contract.json`; add a decision-report section linking the contract, plan, manifest, figure questions, missing/conditional figures, basis, outlier evidence, and validation output. Register all artifacts and completion checks in `references/study-contract-and-reporting.md`.

- [ ] **Step 5: Integrate route requirements**

In the short-text reference require duplicate/source/template artifact visualization. In the long-document reference require parent-document topic profiles. Both must use registered source artifacts and preserve the main taxonomy.

- [ ] **Step 6: Add policy validation**

Implement `validate_visualization_policy` in `validate_study_bundle.py`, call it when a contract is loaded, and test exact policy failures. Keep rendered-file validation in the standalone visualization validator so the existing completed study fixture remains focused and portable.

- [ ] **Step 7: Run integration tests**

Run:

```powershell
python -B -m unittest scripts.tests.test_visualization_bundle.VisualizationDocumentationTests scripts.tests.test_tools.SkillInstructionTests scripts.tests.test_tools.StudyBundleValidationTests -v
```

Expected: all selected tests pass.

## Task 6: Verify, self-review, and publish

**Files:**

- Modify after measured results: `HANDOFF.md`
- Publish public changed files through the existing GitHub remote.

- [ ] **Step 1: Run the complete test suite**

Run:

```powershell
python -B -m unittest discover -s scripts/tests -v
```

Expected: every test passes; record the actual count.

- [ ] **Step 2: Run the skill validator**

Run:

```powershell
python -X utf8 -B "D:\Codex work\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "F:\Skill\Codex\.agents\skills\bertopic-tuning"
```

Expected: `Skill is valid!`.

- [ ] **Step 3: Exercise both new CLIs**

Create a temporary complete visualization fixture through the tested helper or a dedicated test invocation. Run the planner with `--require-ready`, then the standalone validator. Expected: zero exit and `"valid": true`.

- [ ] **Step 4: Self-review against the design**

Confirm all seven baseline views, eleven core figures, route/conditional activation, generic fields, explicit lexical/semantic basis, Topic `-1`, shared coordinates, six output forms, path/hash checks, and no external dependency are covered by code plus tests.

- [ ] **Step 5: Inspect intended changes**

Run local status and diff checks. Verify no cache, bytecode, private `HANDOFF.md`, case-specific dataset, local source figure, or generated archive is staged.

- [ ] **Step 6: Update the private handoff**

Record the final files, measured test count, validator results, commit ID, push target, and remaining boundaries. Keep it ignored and unstaged.

- [ ] **Step 7: Commit and push**

Stage only intended public files, commit once with a descriptive message, and push the current feature commit to the GitHub remote's `main` branch after verifying the remote has not advanced.
