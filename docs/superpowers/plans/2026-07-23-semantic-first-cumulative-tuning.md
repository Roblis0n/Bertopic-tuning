# Semantic-First Cumulative BERTopic Tuning Improvement Plan

> **Execution note:** This plan was implemented task-by-task with `superpowers:executing-plans`, test-driven development, and skill-behavior pressure fixtures. The active runtime prohibited subagents, so the planned fresh-agent pressure runs were replaced by deterministic instruction-contract replay over the same hidden-target scenarios. The user later explicitly requested GitHub publication, so the validated public changes are committed and pushed after local completion; `HANDOFF.md` remains private and no ZIP is created.

**Goal:** Replace the current audit-heavy, metric-led, uniformly strict workflow with a semantic-first BERTopic workflow that tunes one parameter family at a time, carries one explicit champion forward, performs a bounded interaction confirmation at the end, and scales audit requirements to the intended use.

**Architecture:** Add an assurance-level policy that separates exploratory tuning, research-grade comparison, and publication/release. Algorithmic metrics become triage signals; a consolidated semantic review built from original texts becomes the authority for topic identity and boundary decisions. A cumulative tuning trace records each stage’s champion, challengers, semantic judgment, promotion or rollback, while the existing strict bundle remains available only for publication/release.

**Tech Stack:** Markdown skill/reference documentation, UTF-8 JSON/CSV templates, Python 3 standard library, `unittest`, existing BERTopic portable evaluation scripts, existing Codex skill validator. No new LLM API or plotting dependency. Git/GitHub is used only for the user-authorized final publication after validation; no ZIP is created.

## 中文执行摘要

本计划把 skill 的工作重心从“把审计材料填全”改为“真正理解主题并逐步改善一个主模型”：

- 用 `exploratory`、`research`、`publication_release` 三种保障级别控制审计强度，完整账本、哈希、谱系和全套图件不再对所有任务强制。
- 算法只负责发现可疑主题和相似主题对；Codex 或人工必须阅读原文，判断主题对象、含义、立场、边界、上下位关系和伪主题风险。
- 建立唯一的当前优胜模型（champion）。分析单位、embedding、UMAP、HDBSCAN、表示和分类体系按阶段逐项推进；每一步只保留有语义证据支持的改动，失败就回退。
- 主流程结束后，只针对已发现的参数交互做有边界的联合复核，不做全参数笛卡尔网格。
- 把原有分散的人类主题审计和主题对审计整合为 `semantic-review.json`，新增 `tuning-trace.json` 记录优胜模型链；同时加强校验器，使其检查真实决策一致性，而不只是文件和表头存在。
- 全部改动先写失败测试，再实现；最终使用探索、研究、出版三套资料包分别验证。

## Approved design basis

The user has already approved these design decisions in the 2026-07-23 conversation:

1. Reduce audit content that does not directly affect a modeling decision.
2. Make interpretation of original texts—not cosine similarity, TD, IRBO, or keyword overlap—the basis for distinguishing topic meanings.
3. Use algorithmic similarity only to identify topics and topic pairs that need semantic review.
4. Tune cumulatively: retain the accepted improvement, use it as the next stage’s baseline, and roll back rejected changes.
5. Change one parameter family at a time along the main path.
6. Because UMAP, HDBSCAN, embeddings, and analysis units can interact, finish with a small, evidence-triggered interaction confirmation rather than a full combinatorial grid.
7. Generate the full audit and visualization bundle only for final publication/release work.

This file is the single implementation plan for that approved direction. Do not create parallel `v1`, `v2`, `final`, or `latest` plans.

## Global constraints

- Preserve the skill name `bertopic-tuning` and the existing `network-short`, `long-document`, and `mixed` routes.
- Preserve raw text, stable unit IDs, parent-document IDs, duplicate/source groups, and the distinction between structure, representation, taxonomy, and governance.
- Never treat lexical overlap, embedding similarity, 2D distance, coherence, topic count, or Topic `-1` rate as a semantic verdict.
- Never automatically merge, split, label, promote, or reject a topic solely from an algorithmic threshold.
- Allow provisional defaults only in `exploratory` mode, record their provenance, mark them `exploratory_only`, and prohibit them from justifying a research/publication claim.
- Require locally calibrated thresholds only when a threshold supports a research or publication decision.
- Carry one explicit champion through the main tuning path. Every challenger must identify its champion parent and the single parameter family it changes.
- Permit multi-family changes only in the final `interaction_confirmation` stage, with a recorded diagnostic trigger and a bounded candidate rule.
- Keep group-safe resampling as a permanent validity rule: short-text dependence groups stay together; long-document chunks stay with their parent document.
- Do not add a new mandatory artifact unless it replaces multiple existing obligations or makes an existing decision executable.
- Do not install or call an external LLM service. Codex or a named human reviewer reads the registered original/display texts and records the semantic decision.
- Do not weaken the existing full publication/release evidence chain; make it conditional instead of universal.
- Existing study bundles without `assurance_level` must retain legacy strict behavior and emit a migration warning rather than silently becoming less strict.
- 仅在全部验收通过后执行用户明确授权的 Git/GitHub 发布；不得生成 ZIP，`HANDOFF.md` 只保留在本地且不得暂存、提交或推送。

---

## Target workflow

```text
route corpus
→ establish baseline champion
→ analysis-unit/context stage
→ embedding stage
→ UMAP stage
→ HDBSCAN minimum-support stage
→ HDBSCAN density-conservatism stage
→ HDBSCAN selection-method stage
→ representation stage with frozen assignments
→ taxonomy stage
→ bounded interaction confirmation
→ finalist stability/coverage checks
→ final semantic decision and assurance-level delivery
```

At every main-path stage:

```text
current champion
→ generate challengers that change one parameter family
→ calculate algorithmic diagnostics
→ build an original-text semantic review queue for plausible challengers
→ judge meaning, coverage, boundaries, and artifacts
→ promote one challenger or retain the champion
→ carry only the resulting champion to the next stage
```

## Assurance levels

| Level | Intended use | Modeling gate | Required semantic work | Required artifacts | Visualization |
|---|---|---|---|---|---|
| `exploratory` | smoke test, feasibility check, early tuning, rapid baseline | The explicit modeling request is sufficient authorization | Review the stage champion and only algorithmically or substantively risky topic pairs | Compact contract/profile, experiment registry, candidate metrics, tuning trace, semantic review, decision report | Optional |
| `research` | defensible model comparison and substantive analysis | Record the user’s modeling request; pause only when reconnaissance exposes a scope-changing ambiguity | Review every promoted stage winner and all finalists; check missing themes and grouped stability on finalists | Exploratory artifacts plus selected model, topic catalog, concise reconnaissance, missing-theme and stability evidence | Decision-relevant figures only |
| `publication_release` | journal submission, public release, production taxonomy | Preserve the current explicit reconnaissance preview and approval gate | Full topic, pair, coverage, outlier, lineage, and reviewer audit | Current complete research bundle plus tuning trace and consolidated semantic review | Full layered bundle and all required export forms |

The skill should infer the level from the requested outcome:

- “试跑、探索、先看看、技术验证、快速调参” → `exploratory`;
- “研究、比较模型、形成可信主题、论文分析但尚未交付” → `research`;
- “投稿、发表、公开、发布、生产使用、最终研究资料包” → `publication_release`.

Ask the user only when the requested outcome genuinely spans two levels and the difference changes an external claim or release obligation.

## File map

### Create

- `references/semantic-review-and-cumulative-tuning.md` — canonical meaning-first review and cumulative champion method.
- `assets/semantic-review.json` — one consolidated topic-card, pair-decision, coverage-decision, and unresolved-issue artifact.
- `assets/tuning-trace.json` — cumulative stage/champion history and bounded interaction confirmation.
- `scripts/workflow_policy.py` — assurance-level artifact and gate policy.
- `scripts/build_semantic_review_queue.py` — deterministic evidence queue builder; never emits a semantic verdict.
- `scripts/validate_tuning_trace.py` — stage order, single-family change, champion chain, promotion, rollback, and interaction-boundary validator.
- `scripts/tests/test_semantic_cumulative_workflow.py` — mode, semantic queue, cumulative tuning, selection, and integration tests.
- `scripts/tests/fixtures/skill-behavior-scenarios.json` — pressure scenarios for RED/GREEN skill testing.
- `scripts/tests/fixtures/skill-behavior-baseline.json` — verbatim baseline failures captured before editing the skill.
- `scripts/tests/fixtures/skill-behavior-green.json` — deterministic post-rewrite behavior evidence under the same pressure scenarios; records the runtime no-subagent limitation.

### Modify

- `SKILL.md` — replace the universal strict workflow with assurance routing and the semantic-first cumulative loop.
- `README.md` — explain the three assurance levels, cumulative champion path, semantic authority, and conditional deliverables.
- `agents/openai.yaml` — make semantic interpretation and cumulative tuning discoverable without encoding the workflow as a shortcut.
- `assets/study-contract.json` — add assurance level, claim scope, authorization basis, semantic-review policy, and cumulative tuning policy.
- `assets/experiment-registry.csv` — add stage and champion-parent identity without duplicating the tuning trace.
- `assets/candidate-metrics.csv` — add stage, champion comparison, semantic eligibility, boundary clarity, and unresolved-meaning status.
- `assets/selected-model.json` — bind the final choice to the champion chain and final semantic review.
- `assets/decision-report.md` — lead with semantic findings and stage promotions; render sections conditionally by assurance level.
- `assets/modeling-authorization.json` — support `user_request` authorization for non-release work while retaining explicit approval for publication/release.
- `references/corpus-theme-reconnaissance.md` — make the heavy ledger/approval gate conditional by assurance level.
- `references/diversity-evaluation.md` — demote algorithmic metrics to triage and make original-text meaning judgments primary.
- `references/study-contract-and-reporting.md` — define mode-specific artifact sets and remove universal bundle obligations.
- `references/bertopic-implementation.md` — implement the champion loop and enforce one-family diffs.
- `references/network-short-text.md` — integrate source-diverse semantic review and cumulative tuning.
- `references/long-document.md` — make analysis-unit selection the first cumulative stage and preserve parent-document evidence.
- `references/research-grade-visualization.md` — require the complete figure system only for publication/release.
- `references/iteration-and-lineage.md` — connect promoted champions and taxonomy decisions to later snapshot lineage.
- `scripts/evaluate_diversity.py` — label its outputs as diagnostic triage and expose review triggers without decisions.
- `scripts/select_pareto.py` — support categorical semantic eligibility and champion-relative deltas; never auto-promote.
- `scripts/validate_theme_reconnaissance.py` — retain strict validation while adding explicit assurance-aware entry points.
- `scripts/validate_study_bundle.py` — validate mode-specific artifacts, consolidated semantic review, and cumulative trace.
- `scripts/build_visualization_plan.py` — activate mandatory figures from assurance level instead of universally.
- `scripts/validate_visualization_bundle.py` — keep strict checks for required figures while accepting non-required modes.
- `scripts/tests/test_tools.py` — cover template, policy, selection, legacy migration, and study-bundle integration.
- `scripts/tests/test_theme_reconnaissance.py` — cover exploratory/research/publication gate behavior without weakening strict publication checks.
- `scripts/tests/test_visualization_bundle.py` — cover assurance-aware figure requirements.
- `HANDOFF.md` — record the final local design, behavior, tests, and private maintenance boundary after implementation succeeds.

### Keep but make conditionally required

- `human-topic-audit.csv` and `topic-pair-audit.csv` remain compatible publication exports, but `semantic-review.json` becomes the canonical semantic decision artifact.
- `corpus-reading-plan.json`, `corpus-reading-ledger.csv`, and the full span/hash machinery remain required for publication/release and for research claims that depend on progressive extraction coverage; they are not required for ordinary exploratory tuning.
- The full visualization contract/plan/manifest remains intact for publication/release.

---

### Task 1: Establish RED behavior tests before editing the skill

**Files:**

- Create: `scripts/tests/fixtures/skill-behavior-scenarios.json`
- Create: `scripts/tests/fixtures/skill-behavior-baseline.json`
- Do not modify: `SKILL.md` or any implementation file during the RED-capture portion of this task.

**Interfaces:**

- Scenario fields: `scenario_id`, `request`, `available_artifacts`, `pressures`, `failure_conditions`, `desired_behavior`.
- Baseline fields: `scenario_id`, `agent_output`, `observed_failures`, `verbatim_rationalizations`.

- [x] **Step 1: Write five pressure scenarios**

Create the scenario fixture with these exact behavioral targets:

```json
[
  {
    "scenario_id": "exploratory-baseline-must-run",
    "request": "用这批短文本快速试跑 BERTopic，先得到一个能继续调参的基线，不做投稿交付。",
    "pressures": ["limited-time", "no-validation-labels", "user-requested-modeling"],
    "failure_conditions": [
      "blocks all fitting until a full reconnaissance bundle and second approval exist",
      "invents calibrated thresholds",
      "claims publication-grade validity"
    ],
    "desired_behavior": "Select exploratory assurance, record provisional settings, fit a baseline, and limit claims."
  },
  {
    "scenario_id": "high-cosine-different-meaning",
    "request": "两个主题都谈补贴：一个是申请门槛，一个是领取后的使用限制。判断是否合并。",
    "pressures": ["cosine-similarity-is-high", "keywords-overlap", "deadline"],
    "failure_conditions": [
      "merges from similarity alone",
      "does not read original evidence",
      "cannot state the object and boundary difference"
    ],
    "desired_behavior": "Use similarity only to queue review; read original texts; classify the relationship from meaning."
  },
  {
    "scenario_id": "different-words-same-meaning",
    "request": "两个主题关键词几乎不重合，但原文可能都在说资格审核。判断是否重复。",
    "pressures": ["irbo-looks-good", "surface-vocabulary-differs", "many-topics"],
    "failure_conditions": [
      "accepts distinctness from IRBO alone",
      "does not compare original-text definitions"
    ],
    "desired_behavior": "Read evidence, write inclusion/exclusion rules, and flag a merge candidate if meanings coincide."
  },
  {
    "scenario_id": "cumulative-champion-path",
    "request": "从现有基线开始逐步调 embedding、UMAP 和 HDBSCAN，每一步保留有效改动。",
    "pressures": ["many-possible-combinations", "compute-cost", "need-progress"],
    "failure_conditions": [
      "launches a broad Cartesian grid",
      "loses the current champion",
      "changes several parameter families without an interaction-stage reason"
    ],
    "desired_behavior": "Create a champion chain, change one family per stage, promote or roll back, then run bounded interaction confirmation."
  },
  {
    "scenario_id": "publication-stays-strict",
    "request": "把最终 BERTopic 结果整理成可投稿、可复现、可公开的研究资料包。",
    "pressures": ["publication-deadline", "many-artifacts", "temptation-to-skip"],
    "failure_conditions": [
      "uses exploratory shortcuts",
      "omits semantic evidence or lineage",
      "omits required publication figures"
    ],
    "desired_behavior": "Select publication_release and preserve the full strict release gate."
  }
]
```

- [x] **Step 2: Run each scenario without the revised skill**

The runtime in which this plan was executed explicitly prohibited subagents. Use a deterministic static replay of the pre-rewrite instructions instead, give the evaluator only the scenario request and available artifacts, and record the limitation in `capture_method`. Do not reveal desired behavior to the RED evaluator.

- [x] **Step 3: Record the RED failures verbatim**

Write `skill-behavior-baseline.json`. For each scenario, retain the exact blocking behavior, metric-first conclusion, non-cumulative search, or audit rationalization. Do not summarize away the wording that the revised skill must correct.

- [x] **Step 4: Verify that the baseline exhibits the target failures**

Expected RED result:

- exploratory work is blocked or overloaded;
- at least one semantic scenario lets algorithmic similarity/diversity dominate;
- cumulative tuning is not expressed as a champion chain;
- publication strictness is already preserved.

If a scenario does not expose a failure, revise that scenario before changing `SKILL.md`.

---

### Task 2: Add assurance-level policy and mode-aware contracts

**Files:**

- Create: `scripts/workflow_policy.py`
- Modify: `assets/study-contract.json`
- Modify: `assets/modeling-authorization.json`
- Modify: `scripts/validate_study_bundle.py`
- Modify: `scripts/validate_theme_reconnaissance.py`
- Test: `scripts/tests/test_semantic_cumulative_workflow.py`
- Test: `scripts/tests/test_theme_reconnaissance.py`

**Interfaces:**

```python
ASSURANCE_LEVELS: tuple[str, ...] = (
    "exploratory",
    "research",
    "publication_release",
)

def required_artifacts(
    assurance_level: str,
    *,
    progressive_coverage_claim: bool,
    visualization_enabled: bool,
) -> set[str]: ...

def validate_assurance_contract(contract: dict[str, Any]) -> list[str]: ...

def requires_explicit_preview_approval(contract: dict[str, Any]) -> bool: ...
```

- [x] **Step 1: Write failing assurance-policy tests**

Add tests that assert:

```python
def test_exploratory_mode_does_not_require_publication_bundle(self):
    required = required_artifacts(
        "exploratory",
        progressive_coverage_claim=False,
        visualization_enabled=False,
    )
    self.assertIn("tuning-trace.json", required)
    self.assertIn("semantic-review.json", required)
    self.assertNotIn("corpus-reading-ledger.csv", required)
    self.assertNotIn("visualization-manifest.json", required)

def test_publication_release_retains_full_gate(self):
    required = required_artifacts(
        "publication_release",
        progressive_coverage_claim=True,
        visualization_enabled=True,
    )
    self.assertIn("modeling-authorization.json", required)
    self.assertIn("corpus-reading-ledger.csv", required)
    self.assertIn("visualization-manifest.json", required)
```

Also assert:

- `exploratory` requires `claim_scope == "exploratory_only"`;
- provisional defaults require `provisional_defaults_used: true` and a nonblank provenance record;
- research/publication decisions reject provisional defaults as final evidence;
- publication requires `authorization_basis == "explicit_preview_approval"`;
- missing `assurance_level` invokes legacy strict requirements with a warning;
- unknown assurance levels fail.

- [x] **Step 2: Run the assurance tests and observe RED**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.AssurancePolicyTests -v
```

Expected: import failure for `workflow_policy` or missing assurance fields.

- [x] **Step 3: Implement the assurance policy**

Define these minimum artifact sets:

```python
EXPLORATORY_REQUIRED = {
    "study-contract.json",
    "corpus-profile.json",
    "experiment-registry.csv",
    "candidate-metrics.csv",
    "tuning-trace.json",
    "semantic-review.json",
    "decision-report.md",
}

RESEARCH_ADDITIONAL = {
    "selected-model.json",
    "topic-catalog.csv",
    "theme-reconnaissance.json",
    "missing-theme-audit.csv",
}

PUBLICATION_ADDITIONAL = {
    "corpus-reading-plan.json",
    "corpus-reading-ledger.csv",
    "theme-candidate-audit.csv",
    "modeling-authorization.json",
    "topic-lineage.csv",
    "human-topic-audit.csv",
    "topic-pair-audit.csv",
    "evidence-log.csv",
    "visualization-contract.json",
    "visualization-plan.json",
    "visualization-manifest.json",
}
```

Research adds the full reading plan/ledger only when `progressive_coverage_claim` is true. Publication always uses the current full strict set, including compatibility audit exports.

- [x] **Step 4: Update the study and authorization templates**

Add:

```json
{
  "assurance_level": "",
  "claim_scope": "",
  "authorization_basis": "",
  "provisional_defaults": {
    "used": false,
    "provenance": [],
    "permitted_for_final_selection": false
  },
  "semantic_review_policy": {
    "algorithmic_metrics_role": "triage_only",
    "original_text_required": true,
    "review_stage_winners": true,
    "review_all_finalists": true
  },
  "cumulative_tuning_policy": {
    "one_parameter_family_per_main_stage": true,
    "carry_forward_champion": true,
    "rollback_rejected_change": true,
    "bounded_interaction_confirmation": true
  }
}
```

Allow `authorization_basis` values:

- `user_request`;
- `explicit_preview_approval`;
- `external_release_approval`.

- [x] **Step 5: Make reconnaissance validation conditional without weakening strict validation**

Keep the existing strict `validate_theme_reconnaissance(..., require_approval=True)` behavior unchanged for publication. Add an assurance-aware wrapper:

```python
def validate_reconnaissance_for_level(
    root: Path,
    assurance_level: str,
    *,
    progressive_coverage_claim: bool,
) -> dict[str, Any]:
    ...
```

Behavior:

- exploratory: reconnaissance is optional and never blocks a requested baseline;
- research: require concise `theme-reconnaissance.json`; require full ledger only for progressive coverage claims;
- publication: call the existing strict validator and require explicit approval.

- [x] **Step 6: Run mode tests**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.AssurancePolicyTests scripts.tests.test_theme_reconnaissance -v
```

Expected: all assurance tests pass and all existing strict publication reconnaissance tests remain green.

---

### Task 3: Create consolidated, original-text semantic review

**Files:**

- Create: `assets/semantic-review.json`
- Create: `scripts/build_semantic_review_queue.py`
- Modify: `references/diversity-evaluation.md`
- Modify: `assets/candidate-metrics.csv`
- Test: `scripts/tests/test_semantic_cumulative_workflow.py`

**Interfaces:**

```python
RELATIONSHIPS: tuple[str, ...] = (
    "distinct",
    "overlapping",
    "parent_child",
    "merge_candidate",
    "split_signal",
    "artifact",
    "uncertain",
)

def build_review_queue(
    topic_payload: dict[str, Any],
    unit_rows: list[dict[str, Any]],
    assignment_rows: list[dict[str, Any]],
    diversity_scorecard: dict[str, Any],
    *,
    candidate_id: str,
    route: str,
) -> dict[str, Any]: ...

def validate_semantic_review(
    review: dict[str, Any],
    *,
    required_topic_uids: set[str],
    required_pair_ids: set[tuple[str, str]],
) -> list[str]: ...
```

- [x] **Step 1: Write failing semantic-queue tests**

Use fixtures containing:

- a high-cosine pair that discusses “申请资格门槛” versus “领取后的使用限制”;
- a low-overlap pair that uses different vocabulary for the same “资格审核” meaning;
- one template/source artifact topic;
- Topic `-1` units containing a possible missing theme.

Assert:

```python
queue = build_review_queue(
    topic_payload,
    units,
    assignments,
    scorecard,
    candidate_id="candidate-semantic-test",
    route="network-short",
)

pair = next(
    item for item in queue["pair_reviews"]
    if {item["topic_uid_a"], item["topic_uid_b"]} == {"topic-a", "topic-b"}
)
self.assertEqual(pair["algorithmic_signal_role"], "review_trigger_only")
self.assertNotIn("relationship", pair)
self.assertGreater(len(pair["evidence_units"]), 0)
self.assertIn("display_text", pair["evidence_units"][0])
```

The queue builder must never emit `merge`, `split`, `same_topic`, or a substantive label.

- [x] **Step 2: Run semantic tests and observe RED**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.SemanticReviewTests -v
```

Expected: missing module/template failure.

- [x] **Step 3: Implement the semantic review template**

Use one artifact with this structure:

```json
{
  "study_id": "",
  "candidate_id": "",
  "review_scope": "stage_winner",
  "reviewer": {
    "type": "codex",
    "id": "",
    "blind_to_candidate_metrics": true
  },
  "topic_cards": [
    {
      "topic_uid": "",
      "evidence_unit_ids": [],
      "meaning": {
        "object": "",
        "claim_action_or_function": "",
        "context": "",
        "stance_or_perspective": ""
      },
      "label": "",
      "definition": "",
      "inclusion_rules": [],
      "exclusion_rules": [],
      "boundary_clarity": "clear",
      "artifact_status": "substantive",
      "counter_evidence": ""
    }
  ],
  "pair_decisions": [
    {
      "topic_uid_a": "",
      "topic_uid_b": "",
      "evidence_unit_ids": [],
      "relationship": "distinct",
      "meaning_difference": "",
      "decision_reason": "",
      "unresolved": false
    }
  ],
  "coverage_decisions": [],
  "unresolved_issues": []
}
```

Allowed `boundary_clarity`: `clear`, `mixed`, `uncertain`.
Allowed `artifact_status`: `substantive`, `artifact`, `uncertain`.

- [x] **Step 4: Implement evidence queue construction**

The builder must:

- resolve every evidence ID to an existing unit;
- include original/display text and source or parent ID;
- combine representative, random, boundary, source/parent-diverse, nearest-pair, and Topic `-1` evidence already exported by the model;
- keep algorithmic values under `algorithmic_signals`;
- use semantic and lexical nearest-pair outputs only to order review;
- never infer a decision;
- fail if a requested evidence ID is missing;
- keep all chunks from a long document linked to the parent ID.

Do not add a universal sample count. The candidate export or study contract supplies the evidence IDs and semantic stop rule.

- [x] **Step 5: Change candidate metrics from semantic-score authority to semantic eligibility**

Extend `candidate-metrics.csv` with:

```text
stage_id,champion_parent_id,semantic_review_status,meaning_distinctiveness,boundary_clarity,theme_coverage_judgment,artifact_risk,unresolved_semantic_decisions,comparison_to_champion
```

Allowed categorical values:

- `semantic_review_status`: `not_required`, `pending`, `pass`, `fail`, `uncertain`;
- `meaning_distinctiveness`: `improved`, `unchanged`, `worse`, `uncertain`;
- `comparison_to_champion`: `promote`, `retain`, `defer`.

- [x] **Step 6: Rewrite the evaluation reference**

Make this decision order explicit:

```text
algorithmic diagnostics
→ original-text semantic review
→ semantic eligibility
→ quantitative trade-off comparison
→ champion promotion or retention
```

State that cosine, IRBO, TD, coherence, and clustering confidence are review triggers or supporting evidence, not topic-identity decisions.

- [x] **Step 7: Run semantic tests**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.SemanticReviewTests -v
```

Expected: all semantic queue and review-schema tests pass.

---

### Task 4: Implement the cumulative champion trace

**Files:**

- Create: `assets/tuning-trace.json`
- Create: `scripts/validate_tuning_trace.py`
- Modify: `assets/experiment-registry.csv`
- Modify: `assets/selected-model.json`
- Test: `scripts/tests/test_semantic_cumulative_workflow.py`

**Interfaces:**

```python
MAIN_STAGE_ORDER: tuple[str, ...] = (
    "analysis_unit",
    "embedding",
    "umap",
    "hdbscan_min_cluster_size",
    "hdbscan_min_samples",
    "hdbscan_selection_method",
    "representation",
    "taxonomy",
)

def validate_tuning_trace(
    trace: dict[str, Any],
    registry_rows: list[dict[str, str]],
    *,
    assurance_level: str,
) -> dict[str, Any]: ...
```

Return:

```python
{
    "valid": bool,
    "errors": list[str],
    "warnings": list[str],
    "current_champion_id": str,
    "completed_stages": list[str],
}
```

- [x] **Step 1: Write failing champion-chain tests**

Add a valid chain:

```text
baseline-a
→ embedding-b promoted
→ umap-c rejected, champion remains embedding-b
→ hdbscan-d promoted
→ representation-e promoted with identical assignments
```

Assert:

```python
result = validate_tuning_trace(trace, registry, assurance_level="research")
self.assertTrue(result["valid"], result["errors"])
self.assertEqual(result["current_champion_id"], "representation-e")
```

Add failures for:

- stage `umap` starting from a candidate other than the current champion;
- a main-stage candidate changing UMAP and HDBSCAN together;
- a rejected candidate becoming `champion_after`;
- a promoted candidate lacking a passed semantic review;
- representation promotion with changed assignment fingerprint;
- skipped stage without a reason;
- multiple promoted candidates in one stage;
- interaction confirmation without a diagnostic trigger;
- interaction confirmation expanding into an unrestricted grid.

- [x] **Step 2: Run champion tests and observe RED**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.CumulativeTuningTests -v
```

Expected: missing validator/template failure.

- [x] **Step 3: Implement the tuning-trace template**

Use:

```json
{
  "study_id": "",
  "assurance_level": "",
  "baseline_candidate_id": "",
  "current_champion_id": "",
  "stages": [
    {
      "stage_id": "embedding",
      "status": "pending",
      "champion_before": "",
      "candidate_ids": [],
      "changed_parameter_family": "embedding",
      "semantic_review_artifact": "",
      "metric_artifacts": [],
      "decision": "retain",
      "promoted_candidate_id": "",
      "champion_after": "",
      "decision_reason": "",
      "skip_reason": ""
    }
  ],
  "interaction_confirmation": {
    "required": false,
    "diagnostic_triggers": [],
    "allowed_parameter_families": [],
    "candidate_generation_rule": "",
    "candidate_ids": [],
    "semantic_review_artifact": "",
    "decision": "retain",
    "promoted_candidate_id": "",
    "decision_reason": ""
  }
}
```

- [x] **Step 4: Extend the experiment registry**

Add:

```text
stage_id,champion_parent_id,changed_parameter_family,config_diff_artifact
```

Retain the full model configurations. Ignore candidate identity, seeds, resample IDs, timestamps, status, and artifact paths when checking a one-family scientific diff.

- [x] **Step 5: Implement stage-specific diff validation**

Allow these scientific changes:

| Stage | Allowed scientific change |
|---|---|
| `analysis_unit` | analysis-unit/segmentation configuration and resulting corpus fingerprint |
| `embedding` | embedding model/revision/instruction/pooling/truncation only |
| `umap` | UMAP configuration only |
| `hdbscan_min_cluster_size` | `min_cluster_size` only |
| `hdbscan_min_samples` | `min_samples` only |
| `hdbscan_selection_method` | `cluster_selection_method` only |
| `representation` | vectorizer/c-TF-IDF/representation/lexicon snapshot only; assignments must match |
| `taxonomy` | taxonomy snapshot and reviewed merge/split mapping only |

The interaction stage may change multiple named families only when each is listed in `allowed_parameter_families`, each trigger is nonblank, and the candidate-generation rule is bounded by an unresolved diagnostic rather than a Cartesian grid.

- [x] **Step 6: Enforce semantic promotion**

For research/publication:

- promoted candidates require `semantic_review_status == "pass"`;
- `meaning_distinctiveness == "worse"` prohibits promotion;
- unresolved semantic decisions prohibit final promotion;
- numerical improvement alone cannot promote;
- an empirical tie retains the simpler current champion unless semantic evidence supports change.

Exploratory mode may promote with a compact semantic review, but the resulting decision remains `exploratory_only`.

- [x] **Step 7: Run champion tests**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.CumulativeTuningTests -v
```

Expected: all champion-chain, rollback, single-family, and interaction-boundary tests pass.

---

### Task 5: Reframe algorithmic evaluation and Pareto selection

**Files:**

- Modify: `scripts/evaluate_diversity.py`
- Modify: `scripts/select_pareto.py`
- Modify: `references/diversity-evaluation.md`
- Modify: `assets/candidate-metrics.csv`
- Test: `scripts/tests/test_tools.py`
- Test: `scripts/tests/test_semantic_cumulative_workflow.py`

**Interfaces:**

```python
def compare_to_champion(
    rows: list[dict[str, Any]],
    *,
    champion_id: str,
    objectives: dict[str, str],
    id_field: str = "candidate_id",
) -> dict[str, dict[str, float]]: ...

def parse_required_field(specification: str) -> tuple[str, str]: ...
```

CLI additions:

```text
--require-field semantic_review_status=pass
--champion-id <candidate-id>
```

- [x] **Step 1: Write failing semantic-eligibility tests**

Add candidates where:

- candidate A has the best TD/IRBO/cosine metrics but semantic review fails;
- candidate B has slightly weaker algorithmic metrics but clear topic meanings and coverage;
- candidate C is algorithmically tied with the champion and has no semantic improvement.

Assert:

```python
result = select_pareto(
    rows,
    objectives={"irbo": "max", "stability": "max"},
    constraints=["coherence>=0.5"],
    required_fields={"semantic_review_status": "pass"},
)
self.assertNotIn("candidate-a", result["frontier_ids"])
self.assertIn("candidate-b", result["frontier_ids"])
```

Assert that candidate C does not automatically replace the champion.

- [x] **Step 2: Run selection tests and observe RED**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_tools.ParetoSelectionTests scripts.tests.test_semantic_cumulative_workflow.SemanticSelectionTests -v
```

Expected: missing categorical filter/champion comparison failure.

- [x] **Step 3: Label diversity output as triage**

Add to every `evaluate_diversity.py` scorecard:

```json
{
  "decision_role": "diagnostic_triage_only",
  "semantic_verdict_produced": false,
  "requires_original_text_review": true
}
```

Retain TD, IRBO, semantic nearest-neighbor summaries, effective topic count, and top suspicious pairs. Do not rename them as human meaning scores.

- [x] **Step 4: Add categorical eligibility filtering**

Extend `select_pareto()` with:

```python
required_fields: dict[str, str] | None = None
```

Candidates that fail an exact categorical requirement go to `ineligible_ids` with a clear reason. Keep numeric constraints and Pareto dominance unchanged.

- [x] **Step 5: Add champion-relative deltas**

When `champion_id` is supplied, output per-candidate objective deltas without turning them into a weighted score:

```json
{
  "champion_id": "candidate-current",
  "deltas_from_champion": {
    "candidate-challenger": {
      "irbo": 0.02,
      "stability": -0.01
    }
  },
  "promotion_decision_produced": false
}
```

- [x] **Step 6: Update the selection method**

Specify:

```text
semantic eligibility
→ locally justified hard constraints
→ Pareto or champion-relative quantitative comparison
→ original-text promotion decision
```

Pareto is required only when multiple eligible research/publication candidates remain. A single candidate or a representation refresh may use champion-relative comparison without fabricating a frontier.

- [x] **Step 7: Run metric and selection tests**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_tools.DiversityEvaluationTests scripts.tests.test_tools.ParetoSelectionTests scripts.tests.test_semantic_cumulative_workflow.SemanticSelectionTests -v
```

Expected: all legacy calculations remain correct; semantic failure excludes a candidate; no automatic promotion occurs.

---

### Task 6: Make parameter iteration explicitly cumulative in the implementation guide

**Files:**

- Modify: `references/bertopic-implementation.md`
- Create: `references/semantic-review-and-cumulative-tuning.md`
- Modify: `SKILL.md`
- Modify: `assets/decision-report.md`
- Test: `scripts/tests/test_semantic_cumulative_workflow.py`

**Interfaces:**

The new reference must define this positive recipe:

```text
load current champion
→ generate one-family challengers
→ fit/reuse compatible cached components
→ calculate diagnostics
→ build semantic queue
→ review original text
→ promote exactly one challenger or retain champion
→ record rollback point
```

- [x] **Step 1: Write failing documentation behavior tests**

Assert that the skill/reference contain:

- all main stage IDs in order;
- “current champion” and “champion parent”;
- one parameter family per main stage;
- rollback of rejected changes;
- semantic review before promotion;
- bounded interaction confirmation;
- an explicit prohibition on Cartesian-grid interaction search;
- no rule that forces a fixed number of candidates, seeds, or samples.

- [x] **Step 2: Run documentation tests and observe RED**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.DocumentationIntegrationTests -v
```

Expected: missing reference and missing cumulative-stage language.

- [x] **Step 3: Write the cumulative tuning reference**

Cover:

1. champion identity and immutable baseline;
2. stage order and legal skips;
3. candidate generation from unresolved evidence;
4. compatible cache reuse;
5. algorithmic triage;
6. original-text semantic review;
7. promote/retain/defer rules;
8. representation assignment invariants;
9. bounded interaction confirmation;
10. finalist grouped stability and coverage;
11. rollback and release.

Keep the actual meaning judgment separate from the algorithmic metric section.

- [x] **Step 4: Add champion-oriented implementation pseudocode**

Document:

```python
champion = baseline
for stage in main_stages:
    challengers = generate_stage_candidates(champion, stage, unresolved_evidence)
    diagnostics = evaluate_against_champion(champion, challengers)
    review_queue = build_semantic_review_queue(champion, challengers, diagnostics)
    semantic_decision = review_original_text(review_queue)
    champion = promote_or_retain(champion, challengers, semantic_decision)

champion = confirm_bounded_interactions(champion, unresolved_interactions)
```

Clarify that `review_original_text()` is a Codex/human reasoning step, not an embedding function.

- [x] **Step 5: Rewrite the decision report around stage decisions**

Lead with:

- final champion and assurance level;
- stage-by-stage promotions and rollbacks;
- semantic meaning changes;
- topics retained, merged, split, or flagged uncertain;
- final interaction confirmation;
- finalist stability and coverage;
- only then supporting numerical metrics.

Hide publication-only sections in exploratory/research reports instead of leaving empty headings.

- [x] **Step 6: Run documentation tests**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.DocumentationIntegrationTests -v
```

Expected: all cumulative and semantic-first documentation assertions pass.

---

### Task 7: Integrate route-specific meaning review and finalist validation

**Files:**

- Modify: `references/network-short-text.md`
- Modify: `references/long-document.md`
- Modify: `references/corpus-theme-reconnaissance.md`
- Modify: `scripts/build_semantic_review_queue.py`
- Test: `scripts/tests/test_semantic_cumulative_workflow.py`

**Interfaces:**

```python
def validate_route_evidence(
    queue: dict[str, Any],
    *,
    route: str,
) -> list[str]: ...
```

- [x] **Step 1: Write failing route tests**

For `network-short`, require semantic evidence to span the registered duplicate/source/account/thread groups when available.

For `long-document`, require:

- a parent ID for every reviewed chunk;
- evidence from more than one parent when the topic claims cross-document support;
- the analysis-unit stage before embedding/UMAP/HDBSCAN stages;
- document-level grouped finalist stability.

For `mixed`, require both route subsets and route-specific evidence handling.

- [x] **Step 2: Run route tests and observe RED**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.RouteSemanticTests -v
```

Expected: current queue/reference behavior does not enforce route-specific semantic evidence.

- [x] **Step 3: Implement short-text evidence diversity**

The semantic queue should expose duplicate/source/account/thread/time identifiers. It should warn—not manufacture a semantic conclusion—when all evidence for a topic comes from one dependent group.

Keep duplicate collapse and source-leakage guards, but reserve expensive grouped resampling for stage finalists in `research` and `publication_release`.

- [x] **Step 4: Implement long-document evidence integrity**

Make `analysis_unit` the first structural stage. Require each semantic topic card to link chunks back to parent documents and original offsets. Distinguish:

- many chunks from one document;
- support across independent documents;
- primary versus secondary document themes.

Final stability resamples by parent document.

- [x] **Step 5: Reduce reconnaissance burden by level**

Document:

- exploratory: profile and inspect enough original evidence to understand obvious themes and artifacts; no universal pause;
- research: concise theme map and limitations; pause only on a scope-changing ambiguity;
- publication: current complete census, ledger, holdout, residual-risk, and approval process.

- [x] **Step 6: Run route tests**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.RouteSemanticTests -v
```

Expected: all route-specific evidence and stage-order tests pass.

---

### Task 8: Scale visualization and reporting obligations by assurance level

**Files:**

- Modify: `assets/study-contract.json`
- Modify: `references/research-grade-visualization.md`
- Modify: `scripts/build_visualization_plan.py`
- Modify: `scripts/validate_visualization_bundle.py`
- Modify: `scripts/tests/test_visualization_bundle.py`

**Interfaces:**

```python
def figure_requirement(
    figure_id: str,
    *,
    assurance_level: str,
    enabled_modules: set[str],
) -> str: ...
```

Return one of:

- `required`;
- `optional`;
- `not_applicable`.

- [x] **Step 1: Write failing assurance-aware visualization tests**

Assert:

- exploratory can complete without visualization artifacts;
- research can enable only decision-relevant figures;
- publication requires the existing core and route figures plus all export forms;
- Topic `-1`, shared coordinates, and shared taxonomy relation remain mandatory whenever the corresponding figure is produced;
- a publication bundle cannot downgrade a required figure to optional.

- [x] **Step 2: Run visualization tests and observe RED**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_visualization_bundle -v
```

Expected: new assurance-aware tests fail while existing strict tests still pass.

- [x] **Step 3: Implement assurance-aware planning**

Use:

- exploratory: all figures optional;
- research: figures explicitly enabled by the contract are required; others optional/not applicable;
- publication: preserve the current eleven core, route, and enabled conditional requirements.

Do not weaken figure-integrity validation for any produced figure.

- [x] **Step 4: Update the visualization reference**

Separate:

- tuning diagnostics;
- research interpretation figures;
- publication/release artifact bundle.

Remove language that makes full HTML/vector/PNG/source/caption/alt-text/hash exports mandatory before a model is selected.

- [x] **Step 5: Run visualization tests**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_visualization_bundle -v
```

Expected: assurance-aware and legacy strict visualization tests all pass.

---

### Task 9: Make study-bundle validation check decisions, not just file presence

**Files:**

- Modify: `scripts/validate_study_bundle.py`
- Modify: `assets/selected-model.json`
- Modify: `assets/decision-report.md`
- Modify: `scripts/tests/test_tools.py`
- Test: `scripts/tests/test_semantic_cumulative_workflow.py`

**Interfaces:**

```python
def validate_semantic_selection_links(
    selected_model: dict[str, Any],
    tuning_trace: dict[str, Any],
    semantic_review: dict[str, Any],
    candidate_rows: list[dict[str, str]],
) -> list[str]: ...
```

- [x] **Step 1: Write failing decision-integrity tests**

Reject bundles where:

- the selected model is not the final tuning-trace champion;
- a promoted stage lacks a linked semantic review;
- selected-model claims a Pareto frontier that does not match the actual selection output;
- candidate metrics are blank or nonnumeric where used as objectives/constraints;
- the selected model has unresolved semantic decisions;
- a research/publication model uses provisional exploratory defaults as final justification;
- decision-report assurance level disagrees with the contract.

- [x] **Step 2: Run decision-integrity tests and observe RED**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.DecisionIntegrityTests -v
```

Expected: current validator accepts at least some inconsistent bundles.

- [x] **Step 3: Validate the champion and semantic chain**

Require:

```text
selected-model.candidate_id
== tuning-trace.current_champion_id
== final champion_after
```

For research/publication, require all promoted stage reviews and all finalist topic cards to resolve to registered semantic-review evidence.

- [x] **Step 4: Validate actual metric values used in selection**

For every objective or constraint named by the selection artifact:

- field exists;
- value is nonblank, numeric, and finite;
- uncertainty artifact is present when the contract says uncertainty is required;
- categorical semantic eligibility passes.

- [x] **Step 5: Validate Pareto claims**

Recompute the declared frontier from `candidate-metrics.csv` with the exact objectives, constraints, and categorical requirements. Reject a mismatched `eligible_pareto_frontier`.

Do not require Pareto when fewer than two eligible candidates remain.

- [x] **Step 6: Run decision-integrity tests**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.DecisionIntegrityTests scripts.tests.test_tools.StudyBundleValidationTests -v
```

Expected: inconsistent decisions fail; existing valid strict fixture and new assurance fixtures pass.

---

### Task 10: Rewrite the skill around degrees of freedom

**Files:**

- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `agents/openai.yaml`
- Modify: `references/study-contract-and-reporting.md`
- Modify: `references/iteration-and-lineage.md`
- Test: `scripts/tests/test_tools.py`
- Test: `scripts/tests/test_semantic_cumulative_workflow.py`

**Interfaces:**

The revised `SKILL.md` must use this top-level order:

1. Core principle: understand meanings, improve one champion, scale evidence to the claim.
2. Choose assurance level.
3. Route the corpus.
4. Establish baseline champion.
5. Run cumulative stages.
6. Use algorithms for triage and original texts for decisions.
7. Confirm bounded interactions.
8. Validate finalists.
9. Deliver artifacts required by the assurance level.

- [x] **Step 1: Write documentation shape tests**

Assert:

- assurance routing appears before artifact instructions;
- `semantic-review-and-cumulative-tuning.md` is always read for model comparison/tuning;
- original text is explicitly authoritative for topic meaning;
- metric outputs are explicitly triage-only;
- the cumulative stage order is present;
- full reconnaissance approval is conditional, not universal;
- full visualization export is publication-only;
- no copied universal parameter, threshold, sample, seed, or reviewer count appears;
- structure/representation/taxonomy distinctions remain.

- [x] **Step 2: Run documentation tests and observe RED**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.DocumentationIntegrationTests scripts.tests.test_tools.SkillInstructionTests -v
```

Expected: current universal gate and visualization rules fail the new tests.

- [x] **Step 3: Rewrite `SKILL.md` using positive recipes**

Replace large universal prohibition blocks with observable condition rules:

- if exploratory, use the compact path;
- if research, require semantic stage-winner/finalist evidence;
- if publication/release, activate the full strict bundle;
- if one main-stage candidate changes several families, move it to interaction confirmation or reject it;
- if algorithmic and semantic evidence disagree, retain the champion and resolve the meaning uncertainty;
- if a representation update changes assignments, reclassify it as structural.

Keep non-negotiable scientific invariants concise.

- [x] **Step 4: Apply progressive disclosure**

Keep `SKILL.md` focused on routing and the executable loop. Move detailed schemas, pair-taxonomy categories, stage diff rules, and evidence examples to `references/semantic-review-and-cumulative-tuning.md`.

Avoid repeating the same rule in `README.md`, `SKILL.md`, and multiple references.

- [x] **Step 5: Update discovery metadata**

Ensure `agents/openai.yaml` signals:

- semantic topic interpretation;
- cumulative parameter tuning;
- model comparison;
- assurance-aware research reporting.

Do not encode enough workflow detail in the default prompt for an agent to skip `SKILL.md`.

- [x] **Step 6: Update public documentation**

README must clearly say:

- what is automatic;
- what requires Codex/human reading;
- how the champion path works;
- which artifacts each assurance level requires;
- when the full publication bundle is activated.

- [x] **Step 7: Run documentation tests**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow.DocumentationIntegrationTests scripts.tests.test_tools.SkillInstructionTests -v
```

Expected: all documentation and discovery tests pass.

---

### Task 11: Forward-test the revised skill under pressure

**Files:**

- Read: `scripts/tests/fixtures/skill-behavior-scenarios.json`
- Read: `scripts/tests/fixtures/skill-behavior-baseline.json`
- Create: `scripts/tests/fixtures/skill-behavior-green.json`
- Modify only if failures are found: `SKILL.md` or directly relevant reference.

**Interfaces:**

- Use the exact same scenario requests from Task 1.
- Re-evaluate the exact scenarios against the revised instruction contract without leaking the desired behavior into the evaluated rules.
- Because the active runtime prohibits subagents, record `deterministic_instruction_contract_due_to_runtime_no_subagents` as the capture method rather than claiming a fresh-agent run.

- [x] **Step 1: Run GREEN scenarios**

For each scenario, capture:

- assurance level selected;
- whether modeling is unnecessarily blocked;
- whether original text is read before a semantic decision;
- whether the current champion is preserved;
- whether only one parameter family changes on the main path;
- whether publication remains strict.

- [x] **Step 2: Compare with baseline failures**

Pass criteria:

- exploratory baseline proceeds without a second approval ritual;
- high-cosine distinct meanings are not automatically merged;
- low-overlap same meanings are not automatically accepted as distinct;
- tuning is expressed as a champion chain with rollback;
- interaction confirmation is bounded and evidence-triggered;
- publication retains full evidence requirements.

- [x] **Step 3: Capture new rationalizations**

If an agent still violates the design, record the exact wording. Fix only the rule or positive recipe that permits that rationalization.

- [x] **Step 4: Re-run affected scenarios**

Continue RED-GREEN-REFACTOR until the same scenarios pass without leaking expected answers.

- [x] **Step 5: Run a counter-scenario**

Give a request where the user explicitly asks for a journal-ready public bundle. Confirm that the revised skill does not use exploratory shortcuts merely because they are faster.

---

### Task 12: Complete fixtures, regression tests, and local handoff

**Files:**

- Modify: `scripts/tests/fixtures/lexicon-study-bundle/**`
- Create: `scripts/tests/fixtures/exploratory-study-bundle/**`
- Create: `scripts/tests/fixtures/research-study-bundle/**`
- Modify: `scripts/tests/test_tools.py`
- Modify: `scripts/tests/test_theme_reconnaissance.py`
- Modify: `scripts/tests/test_visualization_bundle.py`
- Modify: `HANDOFF.md`

**Interfaces:**

- Exploratory fixture: compact artifacts, provisional claim scope, no visualization.
- Research fixture: cumulative trace, semantic review, concise reconnaissance, finalist stability/coverage evidence.
- Publication fixture: legacy strict/full bundle plus new trace/review artifacts.

- [x] **Step 1: Build an exploratory fixture**

It must pass without:

- corpus reading ledger;
- explicit preview approval;
- visualization manifest;
- full lineage.

It must fail if it claims research/publication validity.

- [x] **Step 2: Build a research fixture**

It must include:

- valid champion chain;
- semantic reviews for promoted winners and finalists;
- selected-model link;
- missing-theme and grouped finalist stability evidence;
- no mandatory full publication visualization bundle.

- [x] **Step 3: Upgrade the strict fixture**

Add `assurance_level: publication_release`, tuning trace, and consolidated semantic review while preserving all existing strict artifacts and validation behavior.

- [x] **Step 4: Run focused tests**

Run:

```powershell
python -X utf8 -B -m unittest scripts.tests.test_semantic_cumulative_workflow -v
python -X utf8 -B -m unittest scripts.tests.test_theme_reconnaissance -v
python -X utf8 -B -m unittest scripts.tests.test_tools -v
python -X utf8 -B -m unittest scripts.tests.test_visualization_bundle -v
```

Expected: all focused suites pass.

- [x] **Step 5: Run the complete suite**

Run:

```powershell
python -X utf8 -B -m unittest discover -s scripts/tests -v
```

Expected: all tests pass with no traceback or unexpected warning.

- [x] **Step 6: Validate the skill**

Run:

```powershell
python -X utf8 -B 'D:\Codex work\.codex\skills\.system\skill-creator\scripts\quick_validate.py' 'F:\Skill\Codex\.agents\skills\bertopic-tuning'
```

Expected:

```text
Skill is valid!
```

- [x] **Step 7: Validate all three assurance fixtures**

Run:

```powershell
python -X utf8 -B scripts/validate_study_bundle.py scripts/tests/fixtures/exploratory-study-bundle
python -X utf8 -B scripts/validate_study_bundle.py scripts/tests/fixtures/research-study-bundle
python -X utf8 -B scripts/validate_study_bundle.py scripts/tests/fixtures/lexicon-study-bundle
```

Expected: each reports `"valid": true`; only documented migration warnings are permitted.

- [x] **Step 8: Update the private handoff**

Record:

- the new assurance levels;
- the semantic-review authority rule;
- the cumulative champion stage order;
- the bounded interaction rule;
- the mode-specific artifact sets;
- actual test and validator outputs;
- the user-authorized GitHub publication record and the fact that no ZIP was created;
- confirmation that `HANDOFF.md` remained ignored, untracked, unstaged, and unpublished.

Do not copy private handoff content into public files.

---

## Acceptance Criteria

The improvement is complete only when all of the following are true:

1. An exploratory modeling request can produce a baseline without a publication-style authorization pause.
2. Exploratory defaults are visibly provisional and cannot justify research/publication selection.
3. Algorithmic metrics never produce a semantic merge, split, label, or promotion verdict.
4. Every promoted research/publication stage winner has an original-text semantic review.
5. The main tuning path carries one champion and changes one parameter family per stage.
6. Rejected changes roll back cleanly and cannot become the next stage’s parent.
7. Multi-family experiments occur only in a bounded, evidence-triggered final interaction stage.
8. Representation changes still require identical assignments and topic identities.
9. Short-text dependence groups and long-document parent groups remain protected.
10. Pareto selection is used only when multiple eligible candidates remain and is subordinate to semantic eligibility.
11. Study-bundle validation recomputes selection consistency instead of checking only that files and headers exist.
12. Full reconnaissance, lineage, visualization exports, hashes, and compatibility audit tables are mandatory only for publication/release or an explicitly matching research claim.
13. The five skill pressure scenarios pass with the revised skill and fail meaningfully under the baseline.
14. All unit tests, skill validation, and three assurance-level fixture validations pass.
15. No duplicate plan, ZIP, or public handoff file is created; Git/GitHub publication occurs only under the user's explicit final instruction.

## Explicit non-goals

- Do not build a GUI.
- Do not add an external LLM API.
- Do not prescribe one embedding model, tokenizer, UMAP/HDBSCAN setting, topic count, seed count, resample count, reviewer count, or sample size.
- Do not automate substantive topic meaning from embeddings.
- Do not remove the publication/release audit system.
- Do not turn the cumulative path into an exhaustive grid.
- Do not combine unrelated performance optimization, deployment, or package-management work with this change.

## Plan self-review checklist

- [x] Every approved design decision maps to at least one implementation task.
- [x] Every new script has a failing test before implementation.
- [x] Skill edits have RED baseline scenarios before documentation changes.
- [x] Exploratory flexibility cannot leak into publication/release.
- [x] Semantic review authority is explicit and evidence-linked.
- [x] The champion chain, rollback, and interaction boundaries are machine-validated.
- [x] No task contains a fixed universal modeling number.
- [x] Git/GitHub appears only as the user-authorized final publication step; no ZIP or public handoff is permitted.
- [x] No placeholder marker, deferred-work wording, or ambiguous duplicate-version name remains.
