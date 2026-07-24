# Corpus-Scale Theme Reconnaissance

## Assurance routing

Scale reconnaissance to the claim:

- `exploratory`: profile the corpus and read enough traceable original evidence
  to understand obvious themes, artifacts, and limitations; do not impose a
  universal pause or second approval before a requested baseline;
- `research`: create a concise theme map and limitations statement; require the
  full plan/ledger only when the claim depends on progressive coverage, and
  pause only for a scope-changing ambiguity;
- `publication_release`: use the complete census, ledger, holdout,
  residual-risk, preview, disposition, fingerprint, and explicit approval gate
  specified in the remainder of this reference.

The detailed full-corpus protocol below is therefore conditional, not a
universal prerequisite for every fit.

## Contents

- Assurance routing
- Purpose and boundary
- User-theme brief
- Reading-mode decision
- Full-corpus accounting
- Reading procedure
- Candidate-theme map
- Topic-count estimate
- Route-specific handling
- User preview and authorization gate
- Preview-versus-model audit
- Validation commands
- Red flags

## Purpose and boundary

For `publication_release`, run the complete corpus-scale reconnaissance after
fingerprinting and before any embedding, dimensionality reduction, clustering,
topic reduction, or BERTopic fit. For `research`, use the concise form unless a
progressive coverage claim activates the complete reading evidence. For
`exploratory`, perform compact inspection and proceed under the user's modeling
request. The purpose is to give the user an evidence-linked provisional map of
what the reviewed corpus evidence appears to contain without making the same
audit burden universal.

This stage is qualitative reconnaissance, not a topic model. Its estimate must be recorded as `pre_model_hypothesis_not_target_k`. It must not be copied into `nr_topics`, HDBSCAN parameters, a forced cluster count, or a model-selection target. Later modeling may confirm, merge, split, reject, or add themes.

The user's theme is the mainline for coverage and interpretation, not a closed label set. Use `coverage_and_interpretation_anchor` and keep `allow_emergent_themes: true`. Do not suppress recurring corpus evidence merely because it is outside the user's initial framing.

## User-theme brief

Before reading the corpus, restate the user's mainline in operational language:

- the central phenomenon, population, setting, and time frame;
- what should count as direct evidence for the mainline;
- adjacent evidence that can explain or qualify it;
- exclusions explicitly requested by the user;
- ambiguities that should be surfaced in the preview rather than silently resolved.

Store this in `theme-reconnaissance.json` under `user_theme`. Classify each candidate theme by its relation to the mainline:

- `mainline`: directly answers or instantiates the user's theme;
- `supporting`: mechanism, cause, consequence, actor, or subtheme needed to interpret the mainline;
- `contextual`: recurring background that frames the mainline without directly answering it;
- `emergent`: substantively recurring evidence not anticipated by the user's framing;
- `artifact`: template, boilerplate, source marker, duplicated campaign, reference list, or other non-substantive pattern;
- `uncertain`: evidence is insufficient to place the candidate reliably.

## Reading-mode decision

Copy `assets/corpus-reading-plan.json` and `assets/corpus-reading-ledger.csv` before semantic review. Estimate eligible unique-content tokens after exact-duplicate registration, reserve context for synthesis and audit, and record the available time. Choose:

- `direct_full_text` when every eligible canonical unit can be read in full inside the registered resource envelope;
- `progressive_extraction` when direct full-text reading is infeasible.

Do not use a universal size threshold. For progressive reading, follow `references/scalable-corpus-reading.md`: census every source unit, build traceable bounded representations, select through coverage-strata, user-anchor, lexical-novelty, probability-holdout and uncertainty-escalation channels, upgrade risky units to full text, and stop only under a registered holdout rule.

The mode controls what can be claimed. `progressive_extraction` supports an uncertainty-bounded preview; it never becomes complete full-text review merely because the census is complete.

## Full-corpus accounting

“Full corpus” first means complete and auditable census accounting of every source unit, not placing the whole corpus into one prompt. Keep census completion separate from semantic review depth:

```text
source_unit_count = eligible_unit_count + excluded_unit_count
profiled_source_unit_count = source_unit_count
reviewed_unit_count = full_text_reviewed_unit_count
                    + extracted_representation_reviewed_unit_count
eligible_unit_count = reviewed_unit_count
                    + duplicate_inherited_unit_count
                    + unreviewed_unit_count
                    + failed_unit_count
failed_unit_count = 0
```

Record the counts and exclusion basis in `theme-reconnaissance.json`, and reconcile them with exactly one ledger row per globally unique source `unit_id`. An exact duplicate may inherit only from an existing semantically reviewed canonical row. Set `accounting_complete: true` only when row, unique-ID and depth counts reconcile. Set `full_text_review_complete: true` only when extracted-representation, unreviewed and failed counts are all zero. Near duplicates cannot inherit review because small differences may change stance, actor, event, or theme.

Use stable unit IDs throughout. Preserve an audit link from every candidate theme to evidence IDs in `theme-candidate-audit.csv`; each evidence ID must resolve to a ledger row reviewed as `full_text` or `extracted_representation`. Do not claim complete full-text coverage from selected evidence, a search result, topic keyword list, lexical sketch, embedding neighborhood, generated summary, or beginning-of-file scan.

If a unit cannot be read or parsed, record it in `failed_unit_ids`, leave `accounting_complete: false`, and repair the failure before presenting a valid preview. Do not silently omit malformed, very long, non-Chinese, or inconvenient records.

## Reading procedure

Process the corpus lazily or in bounded batches while maintaining a cumulative codebook:

1. Freeze source order, stable IDs, fingerprint, route, and exclusions.
2. Profile every source unit and write its ledger row without loading the whole corpus into the prompt.
3. In `direct_full_text`, review every eligible canonical unit once; in `progressive_extraction`, execute every required selection channel and preserve the unreviewed denominator.
4. Assign one or more provisional candidate IDs only to semantically reviewed evidence and retain short notes plus raw locators.
5. After each batch, compare new evidence with the cumulative map; merge labels only when definitions and inclusion/exclusion rules agree.
6. Preserve unresolved boundaries and escalate novel, ambiguous, contradictory or context-sensitive evidence to full text.
7. Audit theme evidence across sources, times, groups, languages, document positions or parent documents so one dense source cannot define the map alone.
8. In progressive mode, freeze the audit-round map and mark the untouched audit rows `final_independent`. Their count must match the plan and they cannot support the frozen map. If they change the map, relabel released evidence `development_released`, expand reading and draw a fresh final holdout. Record `stop_with_residual_risk` only with zero new candidates and `material_change_detected: false`.
9. Separate substantive candidates from artifact candidates before estimating counts.

Do not use generated labels as evidence. The evidence is the linked corpus text and its distribution across independent units or parent documents. Labels are editable summaries.

## Candidate-theme map

Populate one row per candidate in `theme-candidate-audit.csv`. Use permanent provisional IDs such as `cand-main-...`; do not use bare sequential topic numbers as substantive identity. Each row must include:

- hierarchy level and optional parent candidate;
- route subset for mixed corpora;
- provisional label, definition, inclusion, and exclusion rules;
- theme type and relation to the user's mainline;
- independent support and evidence unit IDs;
- source or parent-document spread;
- duplicate or artifact risk;
- uncertainty and later user disposition;
- `prevalence_claimed: false` and `claim_scope: semantic_evidence_only` so adaptive evidence cannot be mistaken for a corpus prevalence estimate.

Candidate IDs in the coarse and fine estimates must resolve to rows in this table. Parent IDs must also resolve. Artifact candidates must be listed in `excluded_artifact_candidate_ids` and must not be counted in either substantive estimate.

Use the hierarchy to avoid a false single answer. A coarse candidate can organize several fine candidates; it is not automatically more correct. Report both when the research question plausibly supports multiple levels.

## Topic-count estimate

Provide a lower bound, point estimate, and upper bound at both coarse and fine granularity:

- lower bound: defensible merges after resolving obvious aliases and overlapping labels;
- point estimate: the current best reading of substantively distinct recurring themes;
- upper bound: plausible splits whose boundaries remain unresolved but evidence is not merely idiosyncratic;
- candidate ID list: exact members counted by the point estimate;
- basis: corpus evidence, hierarchy decisions, uncertainty, and independent support.

The point estimate must equal the number of listed candidate IDs, and bounds must satisfy `lower_bound <= point_estimate <= upper_bound`. Exclude artifacts and one-off fragments. Do not invent a numerical range from a preferred BERTopic output size, paper, library default, or desired visual neatness.

The estimate is a navigation hypothesis. The later study contract may use it to define questions for sensitivity analysis and missing-theme audit, but not to preselect a target K. BERTopic's density-based structure is allowed to disagree.

## Route-specific handling

### Network and short text

Review exact-duplicate groups through one canonical unit and record `duplicate_inherited_unit_count`. Inherited rows must match the canonical content hash, length and nonblank duplicate group. Preserve multiplicity only for a later, separately validated probability design. In progressive mode, rotate selection across source, time, language, group and duplicate-family strata; keep an independent probability holdout. Review every selected near duplicate independently or side by side because a changed qualifier, target, link, or emoji can alter meaning. Keep platform artifacts as explicit artifact candidates so the user can see what was excluded.

### Long documents

Account for every eligible parent document under `parent_document_coverage`. In direct mode, read natural sections or provisional semantic spans across every document. In progressive mode, census every section path, select across parent/source/time/type/length and within-document-position strata, and build traceable cards from distributed spans rather than head-only truncation. Escalate relevant sections or full documents when local spans cannot establish stance or theme boundaries. These reconnaissance spans remain reading aids and do not freeze the later `chunking_policy`.

### Mixed corpora

Complete both unit-level and parent-document accounting where applicable. Every ledger row uses the concrete `network-short` or `long-document` subset, both subsets must be present, and distinct profiled/reviewed long-document parent IDs must match the declared counts. In progressive mode, each subset independently requires semantic review, all five selection channels and a final-independent holdout. Mark `route_subset` on every candidate. Present shared candidates and route-specific candidates separately before proposing any aligned taxonomy.

## Publication/release preview and authorization gate

Present the reconnaissance before modeling in this order:

1. corpus fingerprint, route, reading mode and feasibility basis;
2. full-corpus census accounting versus full-text, extracted-representation, inherited and unreviewed semantic counts;
3. progressive selection channels, holdout result, stop evidence and residual risk when applicable;
4. user's mainline and how it governed interpretation;
5. coarse and fine count estimates with uncertainty;
6. candidate hierarchy and relation to the mainline;
7. emergent themes, excluded artifacts, and unresolved boundaries;
8. strongest counter-evidence and limitations;
9. the exact choices the user can accept, reject, merge, split, defer, or reframe.

Create `modeling-authorization.json` with `gate_status: awaiting_user_direction` and `modeling_may_start: false`, then stop. A completed direct plan records `reconnaissance_state: complete_for_preview`, `termination_basis: complete_full_text_review` and `resource_budget_exhausted: false`; a completed progressive plan uses `termination_basis: local_holdout_rule_satisfied`. Resource exhaustion is `interim`, never completed stop evidence. Do not create embeddings, fit a baseline, start structural candidates, or register a modeling run while the gate is waiting or under revision.

After the user responds, record every candidate disposition in `theme-candidate-audit.csv` and capture the instruction verbatim or faithfully in the authorization artifact. Modeling may start only when:

- `gate_status` is `approved_for_modeling`;
- `modeling_may_start` is `true`;
- `authorization_id`, user instruction, decision timestamp, and all resolved candidate IDs are present;
- the authorization's `pre_model_artifact_fingerprint` binds the current profile, reading plan, ledger, reconnaissance and disposed candidate map, and the reconnaissance ID matches;
- every candidate has a disposition;
- the authorization links the current `reading_plan_id` and `reading_mode`;
- `progressive_reading_risk_acknowledged` is true when the mode is `progressive_extraction`;
- the approval validator passes.

Link the same `authorization_id` and corpus fingerprint from every baseline, structural, representation, taxonomy, and mapping row in `experiment-registry.csv`; reject unknown run types. The study-contract route and research question must equal the approved reconnaissance. If the corpus fingerprint, route, research question, reading artifacts, user-theme mode, or resolved candidate map changes, return to reconnaissance or authorization as appropriate; never reuse a stale approval.

## Preview-versus-model audit

After candidate modeling, compare the selected taxonomy with the approved preview:

- preview candidates confirmed, merged, split, absent, or still unresolved;
- model-emergent themes not anticipated in the preview;
- user-mainline coverage and missing-theme evidence;
- artifact candidates that leaked into modeled topics;
- reasons for every material disagreement.

This audit evaluates discovery quality; it does not reward agreement for its own sake. A model that discovers grounded emergent themes may be better than one forced to reproduce the preview.

## Validation commands

Validate the completed preview before showing it to the user:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory>
```

After user approval, validate the modeling gate before any fit:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
```

The full study-bundle validator also requires an approved gate for modeling runs:

```text
python scripts/validate_study_bundle.py <study-bundle-directory>
```

## Red flags

- calling a selected set, generated summary or truncated scan complete full-text review;
- omitting unreviewed units from the semantic-review denominator;
- choosing progressive evidence from only frequent, early, mainline-matching or convenient records;
- using a progressive preview without an independent holdout and registered stop rule;
- approving progressive reading without explicit residual-risk acknowledgement;
- inheriting review across near duplicates;
- estimating one topic count without coarse/fine hierarchy or uncertainty;
- treating the user's theme as a closed vocabulary or mandatory cluster;
- counting platform, template, citation, or boilerplate artifacts as substantive themes;
- turning the preview estimate into `nr_topics` or target K;
- continuing to BERTopic before explicit user authorization;
- approving with unresolved candidate dispositions or a mismatched fingerprint;
- hiding preview-versus-model disagreements.
