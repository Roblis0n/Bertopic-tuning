# Study Contract and Reporting

## Contents

- Contract-before-modeling rule
- Study-contract fields
- Corpus fingerprint
- Experiment registry
- Topic catalog and human audit
- Decision report
- Reproducibility bundle
- Completion audit

## Contract-before-modeling rule

Create the study contract before fitting candidates. The contract prevents silent changes in analysis unit, metric depth, threshold source, validation sample or selection priority after results are visible.

Copy templates from `assets/` into a study-specific output directory. Preserve the templates in plain CSV/JSON/Markdown; do not add decorative formatting that obscures machine readability.

## Study-contract fields

Complete `study-contract.json`.

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

For `mixed`, define `route_subsets` and whether taxonomies remain separate or are aligned.

### Optional lexicon policy

When synonym, stopword or custom-term resources are enabled, complete `lexicon_policy` with:

- `apply_to: lexical_text`;
- the expected `lexicon-manifest.json` path;
- a model-result candidate-generation rule;
- a locally justified iteration stop rule;
- `assignment_invariant_required: true`;
- the human review and adjudication policy.

Applying the same resources to embedding text is outside this policy and requires a structural candidate.

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
- corpus fingerprint and analysis unit;
- run type: baseline, structural, representation, taxonomy or mapping;
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

## Decision report

Complete `decision-report.md` in this order:

1. outcome and selected route;
2. research question and corpus fingerprint;
3. analysis-unit decision;
4. paper-derived mechanisms and local tests;
5. structural, representation and taxonomy experiments;
6. diversity scorecard and matched-granularity comparison;
7. Pareto frontier and selection rationale;
8. human audit and missing themes;
9. stability and uncertainty;
10. outlier composition as diagnostic;
11. lineage and release decision;
12. limitations, counter-evidence and reproducibility instructions.

Lead with the result, not a chronological tool diary.

## Reproducibility bundle

The minimum bundle contains:

```text
study-contract.json
corpus-profile.json
experiment-registry.csv
candidate-metrics.csv
selected-model.json
topic-catalog.csv
topic-lineage.csv
human-topic-audit.csv
topic-pair-audit.csv
missing-theme-audit.csv
evidence-log.csv
decision-report.md
```

Also retain when permitted:

- preprocessing and segmentation code/configuration;
- embedding cache manifest, not necessarily proprietary vectors;
- trained model or exact reconstruction procedure;
- assignment and probability/distance tables;
- representative/random/boundary unit exports;
- seed/resample alignment results;
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
python scripts/validate_study_bundle.py <bundle-directory>
```

Then verify manually:

- every explicit research requirement maps to an artifact;
- all candidate comparisons use the same evaluation data and granularity rule;
- every threshold has a local calibration source;
- no paper parameter was copied as a default;
- representation-only changes are labeled correctly;
- enabled lexicon resources have no unresolved conflicts, all candidates have dispositions and assignment fingerprints match;
- nearest-topic pairs and missing themes were audited;
- long-text bootstrap uses parent documents;
- network-text bootstrap respects duplicate/source dependence;
- every old/new topic has a lineage disposition;
- counter-evidence and failed candidates remain visible;
- save/reload or reconstruction reproduces the selected result.

Do not claim completion from a successful model fit alone.
