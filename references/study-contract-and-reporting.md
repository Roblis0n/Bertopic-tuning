# Study Contract and Reporting

## Contents

- Contract-before-modeling rule
- Corpus-scale reconnaissance and authorization
- Study-contract fields
- Corpus fingerprint
- Experiment registry
- Topic catalog and human audit
- Layered research visualization
- Decision report
- Reproducibility bundle
- Completion audit

## Contract-before-modeling rule

Create the study contract after the user has reviewed the corpus-scale reconnaissance and its reading limits, and before fitting candidates. The contract prevents silent changes in analysis unit, reading mode, metric depth, threshold source, validation sample or selection priority after results are visible.

Copy templates from `assets/` into a study-specific output directory. Preserve the templates in plain CSV/JSON/Markdown; do not add decorative formatting that obscures machine readability.

## Corpus-scale reconnaissance and authorization

Before the study contract is frozen, complete and show these five artifacts to the user:

- `corpus-reading-plan.json`: direct/progressive mode, feasibility basis, extraction, selection, escalation, stopping, holdout and residual risk;
- `corpus-reading-ledger.csv`: exactly one row per unique source unit with content hash/length, duplicate identity, review depth, holdout role, registered artifact, bounded locator and extraction hash;
- `theme-reconnaissance.json`: corpus fingerprint, user-theme anchor, full-corpus census accounting, semantic-review depth, parent-document accounting when applicable, coarse/fine estimates, uncertainty, artifact exclusions and counter-evidence;
- `theme-candidate-audit.csv`: evidence-linked candidate hierarchy, relation to the user's mainline and one disposition per candidate after review;
- `modeling-authorization.json`: explicit gate state, user instruction, resolved candidate IDs, decision timestamp and the fingerprint binding all approved pre-model artifacts.

The user theme mode is `coverage_and_interpretation_anchor`, with emergent themes open. The estimate is `pre_model_hypothesis_not_target_k`; it is not a forced BERTopic topic count. Census accounting must reconcile profiled, full-text-reviewed, extracted-representation-reviewed, exact-duplicate-inherited, unreviewed, excluded and failed units. Long and mixed routes require analogous parent-document accounting. Only `direct_full_text` with zero extracted, unreviewed and failed units is complete full-text review.

Set `gate_status: awaiting_user_direction` and `modeling_may_start: false` while the preview is with the user. Modeling begins only after the user direction is recorded, every candidate has a disposition, the gate becomes `approved_for_modeling`, and this command succeeds:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
```

For `progressive_extraction`, approval additionally requires `progressive_reading_risk_acknowledged: true` after the user sees the semantic-review denominator, final-independent holdout and residual risk. The approved `authorization_id` and corpus fingerprint must appear in each modeling row of `experiment-registry.csv`, whose `run_type` must be one of the registered types. A changed corpus fingerprint, route, research question, reading plan/ledger, user-theme policy or resolved candidate map invalidates stale authorization through `pre_model_artifact_fingerprint`. See `references/corpus-theme-reconnaissance.md` and `references/scalable-corpus-reading.md` for the complete method.

## Study-contract fields

Complete `study-contract.json`.

Keep `pre_model_reconnaissance.required` and `user_authorization_required` true. Its five artifact paths must point to the approved files and its `authorization_id` must exactly match `modeling-authorization.json`. `user_theme_mode` must remain `coverage_and_interpretation_anchor`, and `allow_emergent_themes` must remain true unless the user explicitly changes the analytical scope and the authorization is renewed.

### Identity and scope

- `study_id`: stable descriptive identifier;
- `research_question`: the substantive question, not “run BERTopic”;
- `inferential_scope`: exploratory discovery, descriptive comparison, measurement construction or another declared use;
- `route`: `network-short`, `long-document` or `mixed`;
- `analysis_unit`: post, enriched post, paragraph, semantic chunk or another defined unit;
- `population_and_sampling`: target population, collection and exclusions.

### Diversity construct

- `diversity_definition`: include lexical, semantic, coverage and stability; add interpretability when scholarly claims depend on it;
- `minimum_meaningful_theme`: define the smallest theme worth retaining, its support unit and evidence source;
- `granularity_scope`: matched topic-count band or declared hierarchy level;
- `selection_policy`: `pareto`;
- `outlier_role`: `diagnostic_guardrail_only`.

### Calibration

For every metric threshold or floor, record:

- decision it supports;
- labeled/historical/null/sensitivity evidence source;
- calibration dataset and split;
- loss or minimum practical effect;
- uncertainty estimate;
- reviewer and date;
- artifact containing the calculation.

Do not place an unreferenced number in the contract. A value from a paper is not local calibration.

### Validation design

- independent resampling unit;
- source/account/thread/time/document grouping rules;
- seed and resample design justified by desired precision;
- human-audit sampling plan;
- reference-codebook or missing-theme protocol;
- time or domain holdout when deployment includes drift;
- negative controls and leakage checks.

### Route-specific fields

For `network-short`, record:

- duplicate/reshare grouping;
- context-enrichment policy;
- account/thread/source/time grouping;
- platform artifact policy.

For `long-document`, record:

- `chunking_policy` and its calibration artifact;
- `parent_document_id_field`;
- tokenizer/context-limit evidence;
- overlap accounting;
- discovery-sampling/document-weighting policy;
- `aggregation_policy` from chunks to documents;
- hierarchy levels being evaluated.

For `mixed`, define `route_subsets` and whether taxonomies remain separate or are aligned. Because a mixed corpus contains a long-document subset, it also requires `chunking_policy`, `parent_document_id_field`, `aggregation_policy`, overlap/tokenizer evidence and document-level resampling in `validation_groups`.

### Optional lexicon policy

When synonym, stopword or custom-term resources are enabled, complete `lexicon_policy` with:

- `apply_to: lexical_text`;
- the expected `lexicon-manifest.json` path;
- a model-result candidate-generation rule;
- a locally justified iteration stop rule;
- `assignment_invariant_required: true`;
- the human review and adjudication policy.

Applying the same resources to embedding text is outside this policy and requires a structural candidate.

### Visualization policy

Keep `visualization_policy.required: true` in the reusable study contract. Its artifact links must be exactly:

- `visualization-contract.json`;
- generated `visualization-plan.json`;
- completed `visualization-manifest.json`.

Retain the layer order `structure`, `representation`, `taxonomy`, `governance`; require shared document coordinates; and keep `topic_minus_one_visible: true`. The validation command is:

```text
python scripts/validate_visualization_bundle.py <study-bundle-directory>
```

The policy defines research and artifact completeness. It does not prescribe a plotting library, topic count, display threshold, or manuscript figure number.

## Corpus fingerprint

Create `corpus-profile.json` or an equivalent immutable record containing:

- source file hashes and row/document counts;
- text and metadata schema;
- length distribution under the real tokenizer;
- languages and normalization;
- missing/empty text;
- exact and near-duplicate groups;
- source/account/thread/time/document group counts;
- preprocessing and segmentation configuration hash;
- software and model revisions used for profiling.

When the analysis unit changes, create a new corpus fingerprint.

## Experiment registry

Use `experiment-registry.csv`. One row equals one candidate run. Record failed runs as well as successful ones.

Required content includes:

- candidate and parent snapshot IDs;
- approved `authorization_id` matching `modeling-authorization.json`;
- corpus fingerprint and analysis unit;
- run type: exactly one of baseline, structural, representation, taxonomy or mapping;
- exact embedding model/revision and embedding cache ID;
- complete UMAP/HDBSCAN/BERTopic configuration as canonical JSON;
- vectorizer/c-TF-IDF/representation configuration;
- random seed and resample/group identifiers;
- software/runtime versions;
- start/end status, warnings and artifact locations;
- pre-registered hypothesis for the change;
- rejection or promotion decision.

First compare controlled subsystem changes; combine them only after identifying which mechanism improved the scorecard.

## Candidate metrics

Use `candidate-metrics.csv`. Each candidate must link to its full resampling artifact and include:

- topic count and hierarchy level;
- TD/IRBO settings and values;
- semantic nearest-neighbor summary;
- coverage method and result;
- stability method and result;
- coherence and labelability;
- source/group leakage evidence;
- outlier fraction as diagnostic;
- uncertainty interval or distribution link;
- constraint failures;
- Pareto status.

Do not leave missing values blank without a reason. Use `not_applicable`, `not_measured` or an artifact link in an accompanying field where the template is extended.

## Topic catalog

Use `topic-catalog.csv`. For every non-retired topic record:

- structure snapshot and permanent `topic_uid`;
- local BERTopic ID;
- label and definition;
- inclusion and exclusion rules;
- size in both units and independent support groups/documents;
- representative, random and boundary evidence links;
- nearest topic and separate lexical/semantic evidence;
- parent topic/hierarchy level when applicable;
- status and lineage packet.

Do not interpret a topic from keywords alone.

## Human audit

Use `human-topic-audit.csv` and sample representative, random and boundary units. Include reviewer ID, blind condition and adjudication status. Score or code:

- topic relevance;
- internal coherence;
- distinctiveness from the nearest topic;
- label/definition fit;
- inclusion/exclusion decision;
- missing-theme observation;
- source or platform artifact;
- comments and evidence location.

Report inter-reviewer agreement appropriate to the scale. Do not discard disagreements; adjudicate and preserve them.

## Selected-model decision

Use `selected-model.json`. Record:

- selected candidate ID;
- eligible Pareto frontier;
- constraints and calibration sources;
- uncertainty and empirical ties;
- chosen operating granularity;
- substantive reason for the selection;
- alternatives rejected and why;
- human review decision;
- release/snapshot identifiers.

If no candidate clears the floors, select none and retain the current snapshot. A scheduled iteration does not require a new model.

## Layered research visualization

Create the figure artifacts after candidate selection and before the release decision. Copy `assets/visualization-contract.json`, map the study's real generic fields, and register frozen source paths plus hashes for assignments, topic terms, coordinates, relation matrices, hierarchy, colors and governance diagnostics.

Generate `visualization-plan.json` with `scripts/build_visualization_plan.py`. Missing core inputs must remain visible as `blocked_missing_inputs`; they cannot be removed from the plan. Render all ready core, route and enabled conditional figures, then populate `visualization-manifest.json`.

The minimum core covers:

- structure: interactive/static document map and intertopic map;
- representation: c-TF-IDF topic-term bars and term-score decline;
- taxonomy: similarity heatmap and hierarchy from one relation artifact;
- governance: prevalence including Topic `-1`, Pareto candidates, stability, outlier diagnostics and coverage/leakage.

`network-short` adds the short-text duplicate/source/template artifact audit. `long-document` adds the parent-document topic profile. `mixed` adds both. Time, group, geography, lineage and document-distribution figures require explicit module activation and source artifacts.

Every required figure retains self-contained HTML, SVG or PDF, PNG, figure-specific source data, caption, alt text, render parameters and SHA-256 values. See `references/research-grade-visualization.md`.

## Decision report

Complete `decision-report.md` in this order:

1. outcome and selected route;
2. research question and corpus fingerprint;
3. corpus-scale reconnaissance, reading mode/limits, user-theme mainline and authorization decision;
4. preview-versus-model confirmation, merge, split, absence and emergence audit;
5. analysis-unit decision;
6. paper-derived mechanisms and local tests;
7. structural, representation and taxonomy experiments;
8. diversity scorecard and matched-granularity comparison;
9. Pareto frontier and selection rationale;
10. layered research figure inventory, relation bases, Topic `-1`, route/conditional figures and visualization validation;
11. human audit and missing themes;
12. stability and uncertainty;
13. outlier composition as diagnostic;
14. lineage and release decision;
15. limitations, counter-evidence and reproducibility instructions.

Lead with the result, not a chronological tool diary.

## Reproducibility bundle

The minimum bundle contains:

```text
corpus-profile.json
theme-reconnaissance.json
theme-candidate-audit.csv
modeling-authorization.json
study-contract.json
experiment-registry.csv
candidate-metrics.csv
selected-model.json
topic-catalog.csv
topic-lineage.csv
human-topic-audit.csv
topic-pair-audit.csv
missing-theme-audit.csv
evidence-log.csv
visualization-contract.json
visualization-plan.json
visualization-manifest.json
decision-report.md
```

Also retain when permitted:

- preprocessing and segmentation code/configuration;
- embedding cache manifest, not necessarily proprietary vectors;
- trained model or exact reconstruction procedure;
- assignment and probability/distance tables;
- representative/random/boundary unit exports;
- seed/resample alignment results;
- the figure HTML/vector/PNG exports, source data, captions and alt text registered in `visualization-manifest.json`;
- environment lock or package report;
- human/LLM prompts and raw audit outputs;
- previous production snapshot and rollback instructions.

When lexical resources are enabled, also retain:

- `lexicon-manifest.json` and its editable source tables;
- `lexicon-candidate-audit.csv`;
- `lexicon-lineage.csv`;
- `representation-iteration.csv`;
- the before/after topic and assignment exports used by the comparison tool.

If the corpus cannot be shared, release an ethical, privacy-preserving replication package containing schemas, hashes, preprocessing rules, topic-term information, aggregate metrics and synthetic/test fixtures where possible.

## Completion audit

Run:

```text
python scripts/validate_theme_reconnaissance.py <bundle-directory> --require-approval
python scripts/validate_study_bundle.py <bundle-directory>
python scripts/validate_visualization_bundle.py <bundle-directory>
```

Then verify manually:

- every explicit research requirement maps to an artifact;
- full-corpus census and parent-document accounting pass, semantic-review depth and residual risk are disclosed, the user direction is recorded, and all modeling runs link the approved authorization ID;
- preview-versus-model disagreements and emergent themes are reported rather than hidden;
- all candidate comparisons use the same evaluation data and granularity rule;
- every threshold has a local calibration source;
- no paper parameter was copied as a default;
- representation-only changes are labeled correctly;
- enabled lexicon resources have no unresolved conflicts, all candidates have dispositions and assignment fingerprints match;
- all core and route-required figures are rendered, enabled metadata figures are complete, disabled ones are recorded as not applicable, and the visualization validator passes;
- document HTML/vector/PNG share frozen coordinates, heatmap/hierarchy share one declared relation basis, and Topic `-1` is visible in document, prevalence and outlier reporting;
- nearest-topic pairs and missing themes were audited;
- long-text bootstrap uses parent documents;
- network-text bootstrap respects duplicate/source dependence;
- every old/new topic has a lineage disposition;
- counter-evidence and failed candidates remain visible;
- save/reload or reconstruction reproduces the selected result.

Do not claim completion from a successful model fit alone.
