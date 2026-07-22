# Full-Corpus Theme Reconnaissance and User Authorization Design

> 2026-07-22 amendment: “full corpus” now means a reconciled census of every source unit, not mandatory full-text semantic reading of every unique unit. The current design supports `direct_full_text` for feasible corpora and audited `progressive_extraction` for large or multi-file corpora. The latter must disclose full-text, extracted-representation and unreviewed counts; use five independent selection channels plus a probability holdout; and obtain explicit residual-risk acknowledgement before modeling. Current contracts live in `SKILL.md`, `references/corpus-theme-reconnaissance.md` and `references/scalable-corpus-reading.md`.

## Outcome

Add a mandatory governance stage between corpus fingerprinting and BERTopic fitting. Codex must census the full eligible source frame, choose a budget-grounded reading mode, disclose semantic-review depth and residual risk, produce an evidence-linked estimate of topic quantity and theme types around the user's research mainline, report the result, and stop in `awaiting_user_direction`. No baseline, structural, representation, taxonomy, or mapping run may begin until a recorded user instruction changes the gate to `approved_for_modeling`.

The user's theme is a coverage and interpretation anchor by default. It must not become a hard target topic count or silently seed the clustering structure. The reconnaissance must preserve recurring emergent themes outside the mainline. Seed-guided BERTopic remains an optional, explicitly authorized structural candidate that must be compared with an unguided candidate.

## Existing gap

The current project already requires corpus profiling, a study contract, missing-theme auditing, and matched-granularity comparison. It does not currently require:

- a content-level review that accounts for every eligible unit before modeling;
- an explicit coarse/fine topic-count estimate grounded in candidate themes;
- a recorded distinction between mainline, supporting, contextual, emergent, artifact, and uncertain material;
- a user-facing pause before any model fitting;
- a machine-checkable authorization linking subsequent experiments to the approved reconnaissance.

Consequently, the proposed feature belongs primarily to the governance layer. It supplies coverage anchors for later structural and taxonomy evaluation, but it does not itself change assignments or claim to be a fitted topic model.

## Approaches considered

### 1. Instructions only

Add a paragraph to `SKILL.md` telling Codex to read the corpus and ask the user before modeling.

This is small, but it cannot prove full coverage, preserve evidence, or prevent a later run from bypassing the pause. It is insufficient for this project’s reproducibility standard.

### 2. Audited reconnaissance plus authorization gate — selected

Add three study artifacts, one reference workflow, a standard-library validator, and integration with the existing study-bundle validator. This makes the behavior reproducible without coupling the project to a specific LLM vendor or adding a premature BERTopic fitting pipeline.

### 3. Provider-specific automated LLM reconnaissance engine

Add an API-driven batch summarizer and theme synthesizer. This could automate execution, but it would introduce provider credentials, privacy policy, prompt/version drift, cost controls, and context-window behavior. Those concerns are outside the current portable, standard-library tooling boundary. The project should first establish the artifact and gate contracts; an automated engine can implement those contracts in a separate future feature.

## Workflow

1. **Fingerprint and route.** Preserve raw text, determine `network-short`, `long-document`, or `mixed`, assign stable unit and parent-document identifiers, and register exact-duplicate groups.
2. **Create a reconnaissance brief.** Record the user's research question, mainline theme, inclusion/exclusion intent, `coverage_and_interpretation_anchor` mode, and permission for emergent-theme discovery.
3. **Account for the full corpus and choose reading mode.** Write one ledger row per source unit. Use `direct_full_text` when every eligible canonical unit fits the registered resource envelope; otherwise use `progressive_extraction`, select evidence through coverage-strata, user-anchor, lexical-novelty, probability-holdout and uncertainty-escalation channels, and upgrade risky evidence to full text. Exact duplicates may inherit from a reviewed canonical unit; unreviewed units remain explicit.
4. **Synthesize an evidence-linked hierarchy.** Produce candidate coarse themes and fine subthemes. Each candidate retains definitions, inclusion/exclusion rules, route subset, independent support, evidence unit IDs, source/parent spread, artifact risk, and its relation to the user mainline.
5. **Estimate topic quantity.** For both coarse and fine levels, report a lower bound, evidence-backed point estimate, and upper bound. The lower bound reflects defensible merges, the point estimate reflects the current candidate map, and the upper bound reflects unresolved defensible splits. Artifact candidates are excluded and uncertain candidates are listed separately.
6. **Report and pause.** Present the mainline themes first, followed by supporting/contextual themes, recurrent emergent themes, uncertain boundaries, and artifacts. Set the gate to `awaiting_user_direction` and `modeling_may_start=false`.
7. **Record user direction.** Translate the user's instruction into candidate dispositions and an authorization record. Valid dispositions are `accepted`, `rejected`, `merge_requested`, `split_requested`, and `deferred`.
8. **Authorize modeling.** Only a complete, fingerprint-matched record with `gate_status=approved_for_modeling` and `modeling_may_start=true` permits the study contract to be frozen and modeling runs to begin.
9. **Evaluate rather than force.** Later candidates are evaluated for preview-theme coverage, fragmentation, merging, unexpected themes, and missing themes. The preview count remains a hypothesis and never becomes an unexamined BERTopic target.

## Full-corpus semantics

“Full corpus” means full census accounting, not one prompt containing the entire dataset and not necessarily complete full-text semantic reading.

- `source_unit_count` covers all ingested rows/documents before registered exclusions.
- `eligible_unit_count` excludes only documented empty, invalid, or out-of-scope units.
- `reviewed_unit_count` equals full-text-reviewed plus extracted-representation-reviewed units.
- `duplicate_inherited_unit_count` counts exact duplicates whose semantic review is inherited from a registered representative.
- `unreviewed_unit_count` counts censused eligible units not semantically reviewed under progressive extraction.
- `failed_unit_count` counts eligible units that could not be read or processed.
- Accounting is complete only when `reviewed_unit_count + duplicate_inherited_unit_count + unreviewed_unit_count == eligible_unit_count` and `failed_unit_count == 0`. Complete full-text review additionally requires both extracted-representation and unreviewed counts to equal zero.

Near duplicates do not inherit review automatically because their semantic differences may be substantive. For long documents, every eligible parent document and every reconnaissance segment must be accounted for. A provisional natural-section or paragraph segmentation may support reconnaissance; it does not freeze the later modeling chunk policy.

## Artifact contracts

### `theme-reconnaissance.json`

This is the machine-readable reconnaissance summary. It contains:

- schema version, stable `reconnaissance_id`, creation time, route, and corpus fingerprint;
- the research question, user-mainline policy and `reading_plan_id`;
- census counts, semantic-review depth and route-specific parent-document accounting;
- coarse and fine topic-count estimates with bounds, candidate IDs, and evidence basis;
- unresolved boundaries, excluded artifact candidate IDs, and strongest counter-evidence;
- a fixed statement that the result is a pre-model hypothesis rather than a target topic count or fitted model.

### `theme-candidate-audit.csv`

One row equals one proposed theme node. Required columns are:

```text
reconnaissance_id,candidate_theme_id,parent_candidate_theme_id,hierarchy_level,route_subset,provisional_label,theme_type,relation_to_user_mainline,definition,inclusion,exclusion,independent_support,evidence_unit_ids,source_or_parent_spread,duplicate_or_artifact_risk,uncertainty,user_disposition,user_instruction
```

`relation_to_user_mainline` uses `mainline`, `supporting`, `contextual`, `emergent`, `artifact`, or `uncertain`. `theme_type` remains corpus-derived rather than being restricted to a universal ontology.

### `modeling-authorization.json`

This is the pause gate. It contains:

- stable `authorization_id`;
- the approved `reconnaissance_id` and corpus fingerprint;
- the approved `reading_plan_id`, reading mode and progressive-risk acknowledgement;
- `gate_status`;
- `modeling_may_start`;
- user-theme mode and emergent-theme policy;
- the user's instruction, all resolved candidate IDs, and decision timestamp.

Valid gate states are:

- `awaiting_user_direction`: a complete preview can be reported; modeling is forbidden;
- `revision_requested`: reconnaissance must be revised; modeling is forbidden;
- `approved_for_modeling`: candidate dispositions are complete and modeling is allowed;
- `stop`: the study stops; modeling is forbidden.

### Existing artifact extensions

- `corpus-reading-plan.json` records feasibility, census fields, extraction cards, selection channels, escalation, holdout stopping evidence and residual risk.
- `corpus-reading-ledger.csv` records one source unit per row with review depth and traceable source locator.
- `study-contract.json` gains `pre_model_reconnaissance`, which points to the reading plan, ledger, reconnaissance, candidate audit and authorization artifacts and states that user authorization is mandatory.
- `experiment-registry.csv` gains `authorization_id`, linking every modeling run to the approved gate.
- `decision-report.md` gains a pre-model reconnaissance section and a preview-versus-model comparison.

## Validation design

Create `scripts/validate_theme_reconnaissance.py` with a reusable function and CLI:

The reusable public signature is `validate_theme_reconnaissance(root: Path, *, require_approval: bool = False) -> dict[str, Any]`.

The result includes `valid`, `errors`, `warnings`, `reconnaissance_id`, `authorization_id`, and `gate_status`.

The validator must reject:

- missing or malformed artifacts;
- blank or duplicate candidate IDs;
- mismatched corpus fingerprints or reconnaissance IDs;
- negative or arithmetically inconsistent coverage counts;
- a census/accounting claim with failed units or a full-text claim with extracted/unreviewed units;
- missing/mismatched reading plans or ledgers, unsupported progressive selection channels, an incomplete holdout stop rule, or candidate evidence linked to unreviewed units;
- topic estimates whose bounds are unordered or whose candidate IDs do not exist;
- unknown hierarchy, mainline-relation, gate-state, or disposition values;
- approval without a non-empty user instruction, timestamp, all candidate dispositions, exact resolved-ID coverage, or progressive-risk acknowledgement when applicable;
- any `modeling_may_start=true` state other than `approved_for_modeling`.

The standalone validator accepts a valid `awaiting_user_direction` bundle so it can be checked before showing the preview. Its `--require-approval` flag rejects that state. `validate_study_bundle.py` always invokes the approval-required path and rejects experiment-registry rows with absent or mismatched authorization IDs.

## Route-specific behavior

### Network-short

Register exact duplicates and census all units. In progressive mode, select across duplicate families, account/thread/source/time/language strata, lexical novelty, user-anchor evidence and an independent probability holdout. Preserve repost, hashtag, URL, emoji, near-duplicate differences and template evidence. Themes supported only by one duplicate family or source are flagged for artifact review instead of being counted automatically.

### Long-document

Census every parent document and section path. In direct mode, read every parent through traceable natural sections. In progressive mode, select distributed spans across source/time/type/length and within-document position, then escalate sections or documents whose stance or boundary cannot be resolved. Count independent parent-document support rather than raw segment support. The reconnaissance segmentation remains provisional until the later chunk-policy audit.

### Mixed

Maintain separate coverage ledgers and candidate maps for each route subset. Align them only when the user's research question requires a shared taxonomy.

## User-facing report order

1. corpus route and coverage statement;
2. estimated coarse and fine topic ranges;
3. user-mainline themes and subthemes;
4. supporting and contextual themes;
5. recurrent emergent themes outside the requested mainline;
6. uncertain merge/split boundaries;
7. source, template, duplicate, or noise artifacts;
8. exact statement that modeling is paused and the next action requires user direction.

## Error behavior

- Incomplete census accounting produces an invalid preview with named failures. Progressive semantic review may remain partial only when its denominator, holdout evidence and residual risk are explicit; it cannot be described as complete full-text review.
- A changed corpus fingerprint invalidates the previous authorization and requires a new reconnaissance or an explicitly audited delta process.
- A user request to force a topic count is recorded as an operating constraint, then evaluated against coverage loss; it does not overwrite the empirical preview.
- A user request to seed the model creates a separate structural candidate and preserves an unguided comparator.
- User silence leaves the gate at `awaiting_user_direction`; no fitting occurs.

## Test strategy

Tests cover reading-plan/ledger schemas, direct and progressive modes, full-accounting arithmetic, semantic-review evidence links, required selection channels, holdout and risk acknowledgement, long-document parent accounting, ID and fingerprint linkage, count-bound ordering, candidate-ID references, every gate transition, experiment-registry authorization linkage, CLI exit codes, fixture validation, and privacy-safe package contents.

The full existing test suite, skill validator, completed study-bundle validator, standalone pre-model validator, and extracted-package test suite must all pass before completion is claimed.

## Scope boundary

This feature does not add a provider-specific LLM client, install BERTopic, fit models, choose an encoder, or define universal topic-count or reading-sample heuristics. It defines and enforces full source accounting, budget-grounded semantic reading and permission to proceed.
