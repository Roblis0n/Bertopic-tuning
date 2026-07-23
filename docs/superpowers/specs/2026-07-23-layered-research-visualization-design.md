# Layered Research-Grade BERTopic Visualization Design

## Outcome

Add a corpus-agnostic visualization stage to `bertopic-tuning` that turns a selected BERTopic snapshot into an auditable research figure system. The system separates structure, representation, taxonomy, and governance; includes all seven views supplied by the user; adds the diagnostic figures needed to defend model selection; activates metadata- and route-specific figures only when their prerequisites exist; and validates the final HTML/vector/PNG/source-data/caption/alt-text bundle.

The feature does not hard-code any single case study, language-specific labels, topic counts, field names, figure numbers, or local parameter values. Existing filenames may be retained in an individual study manifest, but the reusable skill works through semantic figure IDs and configurable field mappings.

## Existing gap

The project already separates structural, representation, taxonomy, and governance decisions, but it has no corresponding visualization contract. Consequently:

- BERTopic's built-in figures can be exported without a declared analytical question;
- lexical c-TF-IDF geometry can be mistaken for semantic geometry;
- interactive document plots and static publication maps can silently use different coordinates;
- Topic `-1` can disappear from prevalence and document-space reporting;
- model-selection, stability, coverage, leakage, and outlier evidence can remain outside the visual record;
- metadata-specific figures can be created merely because a column exists, without a registered inferential purpose;
- screenshots can replace reproducible vector/raster exports;
- captions, alternative text, source tables, render parameters, and hashes are not enforced.

This is a governance and reporting gap, not a request for a new BERTopic fitting engine.

## Selected architecture

Use three machine-readable artifacts and two standard-library tools:

1. `visualization-contract.json` declares the selected study/snapshot, generic field map, frozen data artifacts, document projection, topic relation spaces, conditional modules, outlier identity, and export policy.
2. `visualization-plan.json` is generated deterministically from that contract. It lists every core, route-specific, and metadata-conditional figure, its layer, research question, required inputs, relation basis, outlier policy, required output forms, and readiness state.
3. `visualization-manifest.json` records the rendered figures, interpretations, limitations, parameters, input links, and content hashes.
4. `scripts/build_visualization_plan.py` creates the deterministic plan without importing BERTopic, Plotly, Matplotlib, pandas, NumPy, or scikit-learn.
5. `scripts/validate_visualization_bundle.py` verifies the contract-plan-manifest chain, required figures, shared geometry, declared lexical/semantic basis, Topic `-1` visibility, self-contained HTML, vector/raster signatures, source data, captions, alt text, safe relative paths, and SHA-256 hashes.

Actual rendering remains in the user's fitted BERTopic environment. This preserves the repository's standard-library portability and avoids coupling the skill to one BERTopic/Plotly release. The reference workflow maps the plan to native BERTopic plotting calls and custom governance plots.

## Four visualization layers

### Structure

These figures answer where documents and topics lie in the fitted representation space.

- `document-map`: interactive document map plus publication datamap from one frozen document-coordinate artifact.
- `topic-map`: intertopic map with an explicit semantic or lexical relation basis.

The 2D projection is descriptive. It must not be reused as clustering input or treated as evidence that visual distance equals a calibrated inferential effect.

### Representation

These figures answer which terms represent each topic and how quickly term evidence declines.

- `topic-term-barchart`: per-topic c-TF-IDF bars, corresponding to `visualize_barchart.html`.
- `ctfidf-term-score-decline`: ranked c-TF-IDF decline, corresponding to the reference static term-score plot and BERTopic's term-rank view.

Both figures are lexical. They do not establish semantic separation or topic coherence by themselves.

### Taxonomy

These figures answer which topics are near each other and how a coarser hierarchy could be formed.

- `topic-similarity-heatmap`: the complete registered topic relation matrix.
- `topic-hierarchy`: hierarchy derived from the same registered taxonomy relation artifact.

The heatmap and hierarchy must use the same topic set, ordering map, relation basis, and frozen snapshot. If c-TF-IDF is used, label the relation lexical. If topic embeddings are used, state exactly how they were formed.

### Governance

These figures answer whether the selected model is defensible.

- `topic-prevalence`: topic counts/shares with Topic `-1` shown explicitly.
- `candidate-pareto`: candidate trade-offs and constraint failures without a weighted composite score.
- `topic-stability`: topic survival/alignment uncertainty across registered seeds, group-aware resamples, or snapshots.
- `outlier-diagnostics`: composition and nearest-topic evidence for Topic `-1`.
- `coverage-leakage-audit`: theme coverage and source/group leakage evidence at matched granularity.

## Mandatory core figure catalog

The planner always emits the following eleven conceptual figures. Missing inputs block readiness; they never cause a required figure to disappear.

| Figure ID | Layer | Required source artifacts | Required baseline view |
|---|---|---|---|
| `topic-term-barchart` | representation | `topic_terms`, `topic_catalog`, `topic_color_map` | `visualize_barchart.html` |
| `document-map` | structure | `document_topics`, `document_coordinates`, `topic_catalog`, `topic_color_map` | `visualize_documents.html` and publication datamap PNG |
| `topic-map` | structure | `topic_coordinates`, `topic_catalog`, `topic_color_map` | `visualize_topics.html` |
| `topic-similarity-heatmap` | taxonomy | `topic_similarity`, `topic_catalog`, `topic_color_map` | `visualize_heatmap.html` |
| `topic-hierarchy` | taxonomy | `topic_similarity`, `topic_hierarchy`, `topic_catalog`, `topic_color_map` | `visualize_hierarchy.html` |
| `ctfidf-term-score-decline` | representation | `topic_terms`, `topic_catalog`, `topic_color_map` | publication term-score-decline PNG |
| `topic-prevalence` | governance | `document_topics`, `topic_catalog`, `topic_color_map` | count/share figure including Topic `-1` |
| `candidate-pareto` | governance | `candidate_metrics` | constraint-aware Pareto figure |
| `topic-stability` | governance | `stability_metrics`, `topic_catalog`, `topic_color_map` | uncertainty/survival figure |
| `outlier-diagnostics` | governance | `document_topics`, `outlier_diagnostics`, `topic_color_map` | Topic `-1` composition figure |
| `coverage-leakage-audit` | governance | `candidate_metrics`, `coverage_diagnostics` | coverage/leakage figure |

Each conceptual figure requires:

- self-contained interactive HTML;
- one vector export (`.svg` or `.pdf`);
- one PNG export;
- one figure-specific source-data artifact;
- a caption file;
- an alternative-text file;
- content hashes for every input and output.

The seven baseline files remain explicit requirements through this catalog, but generic output stems do not freeze manuscript figure numbering.

## Route-specific figures

Route predicates are deterministic:

- `network-short` activates `short-text-artifact-audit`, driven by duplicate/source/template artifact evidence.
- `long-document` activates `parent-document-topic-profile`, driven by parent-document aggregation evidence.
- `mixed` activates both route-specific figures.

An activated route figure is required. If its source artifact is missing, the plan records `blocked_missing_inputs`.

## Metadata-conditional figures

The contract may enable:

- `topics-over-time` when a time field and time-topic artifact are registered;
- `topics-by-group` when a substantively relevant group field and group-topic artifact are registered;
- `topic-geography` when a geographic field mapping and geographic artifact are registered;
- `topic-lineage` when aligned snapshots and lineage evidence are registered;
- `document-topic-distribution` when a validated document-topic distribution artifact exists.

The planner records disabled modules as `not_applicable`. Enabling a module without its field/artifact produces a contract error or a blocked figure; it does not silently fall back to a decorative chart.

## Contract rules

`visualization-contract.json` contains:

- `study_id`, `snapshot_id`, and `route`;
- `field_map` with generic names for unit, local topic, permanent topic, label, optional parent/time/group/geographic fields;
- `data_artifacts`, keyed by semantic artifact ID and containing a safe relative path plus `sha256:<64 hex>`;
- `document_projection` with basis, artifact ID, method, parameter artifact, and recorded seed/determinism statement;
- `relation_spaces.topic_map` and `relation_spaces.taxonomy`, each with basis and source artifact ID;
- `conditional_modules`;
- `outlier_topic_id`;
- an export policy requiring self-contained HTML, vector, PNG, source data, captions, alt text, hashes, and static titles in captions.

No field name is inferred from a case study. No threshold, sample size, topic count, number of displayed terms, color choice, or label length is universal. Rendering parameters are copied from the registered local study or left `pending_local_calibration` with an estimand and stopping rule.

## Plan rules

`build_visualization_plan.py`:

- canonicalizes and hashes the contract;
- creates a stable `plan_id`;
- validates contract identity, route, field mapping, export policy, relation spaces, and conditional prerequisites;
- emits every core figure in a fixed semantic order;
- emits route and conditional figures from observable predicates;
- sets each figure to `ready`, `blocked_missing_inputs`, or `not_applicable`;
- records missing artifacts instead of omitting figures;
- records the exact relation basis, coordinate artifact, relation artifact, outlier policy, color-map artifact, required outputs, and activation reason;
- supports `--require-ready` to fail when any required figure remains blocked.

The generated plan is deterministic and contains no timestamp.

## Manifest and bundle validation rules

`validate_visualization_bundle.py`:

1. loads the three JSON artifacts;
2. rebuilds the expected plan from the contract and rejects stale or edited plans;
3. rejects a completed bundle containing contract errors or blocked required figures;
4. checks study, snapshot, plan, layer, input, relation, coordinate, color, and outlier links;
5. requires every ready core/route/conditional figure exactly once;
6. verifies every referenced input artifact and output path stays inside the bundle;
7. verifies SHA-256 hashes against file bytes;
8. verifies HTML, SVG/PDF, and PNG signatures;
9. rejects remote script and stylesheet dependencies in files marked self-contained;
10. verifies nonblank figure-specific source data, caption, alt text, question, interpretation, limitations, and render-parameter record;
11. requires `title_location: caption`;
12. requires Topic `-1` to be explicit in the document map, prevalence, and outlier figures;
13. requires the document map's HTML/vector/PNG to share one coordinate artifact;
14. requires the heatmap and hierarchy to share the taxonomy relation artifact and basis;
15. returns a machine-readable audit and a non-zero CLI exit when invalid.

## BERTopic method mapping

The reference workflow maps:

- `topic-term-barchart` to `visualize_barchart`;
- `document-map` to `visualize_documents` and `visualize_document_datamap`, passing the same frozen reduced embeddings;
- `topic-map` to `visualize_topics`, with `use_ctfidf` chosen from the registered relation basis;
- `topic-similarity-heatmap` to `visualize_heatmap`;
- `topic-hierarchy` to `visualize_hierarchy`;
- `ctfidf-term-score-decline` to `visualize_term_rank`.

Native outputs are not sufficient by themselves. The workflow must also export source data, preserve Topic `-1` where required, create publication companions, and render the governance figures from the project's candidate/audit artifacts.

## Error behavior

- A missing core input blocks the core figure; it is not waived.
- A missing route-specific input blocks completion for that route.
- A disabled metadata module is valid and remains visible as `not_applicable` in the plan.
- An enabled metadata module with missing fields or data is invalid.
- A lexical relation labeled semantic is invalid because the manifest must match the contract basis.
- A stale coordinate or topic-relation hash invalidates the bundle.
- A PNG screenshot without the registered source data and companion vector remains incomplete.
- An external Plotly CDN reference invalidates an artifact declared self-contained.
- A path outside the study bundle invalidates the manifest.

## Test strategy

Tests use only the Python standard library and temporary directories. They cover:

- all eleven core figures and all seven baseline views;
- custom non-case-specific field names;
- missing-input visibility;
- route and metadata activation;
- deterministic plan IDs and CLI readiness failure;
- valid complete bundle validation;
- missing required figures;
- stale plans and mismatched snapshot IDs;
- hash tampering and path traversal;
- external HTML dependencies;
- invalid PNG/vector signatures;
- lexical/semantic relation mismatch;
- heatmap/hierarchy relation consistency;
- Topic `-1` visibility;
- static-title location;
- skill/reference/README integration.

The full existing test suite, skill validator, plan CLI, and visualization-bundle validator must pass before publication.

## Scope boundary

This feature defines, plans, and audits research-grade BERTopic visualization. It does not install visualization dependencies, fit BERTopic, choose a universal topic count, invent display thresholds, infer a case-specific schema, or claim that a two-dimensional plot validates the model.
