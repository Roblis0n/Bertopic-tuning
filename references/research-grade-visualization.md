# Research-Grade BERTopic Visualization

## Assurance routing

- `exploratory`: figures are optional and never block model selection.
- `research`: only figures explicitly enabled as decision-relevant are required;
  other figures are optional or not applicable.
- `publication_release`: retain the complete core, route, conditional, export,
  caption, alt-text, source-data, and hash requirements below.

Whenever any figure is produced, keep its integrity rules: registered inputs,
Topic `-1` treatment, shared coordinates or relation basis where applicable,
and honest interpretation limits. Assurance changes whether a figure is
required, not whether a produced figure may be misleading.

## Contents

1. [Assurance routing](#assurance-routing)
2. [Purpose](#purpose)
3. [Four-layer question map](#four-layer-question-map)
4. [Freeze the visualization contract](#freeze-the-visualization-contract)
5. [Build and inspect the plan](#build-and-inspect-the-plan)
6. [Mandatory core figures](#mandatory-core-figures)
7. [Render the seven baseline views](#render-the-seven-baseline-views)
8. [Render governance figures](#render-governance-figures)
9. [Activate route and metadata figures](#activate-route-and-metadata-figures)
10. [Preserve cross-figure consistency](#preserve-cross-figure-consistency)
11. [Export and manifest contract](#export-and-manifest-contract)
12. [Caption and interpretation contract](#caption-and-interpretation-contract)
13. [Validate the bundle](#validate-the-bundle)
14. [Common failures](#common-failures)

## Purpose

Use visualization to answer registered research questions, diagnose the selected model, and expose uncertainty. Do not treat a default BERTopic HTML export as a complete research figure package.

Separate four layers:

- **structure**: where documents and topics lie in frozen embedding/relation spaces;
- **representation**: which c-TF-IDF terms describe each topic;
- **taxonomy**: which topics are close and how evidence supports a hierarchy;
- **governance**: why the selected snapshot is defensible under coverage, stability, leakage, outlier, and model-selection evidence.

The visualization stage does not alter assignments. A new projection changes a display artifact, not the fitted clusters. A new c-TF-IDF bar chart changes neither the structure nor the taxonomy.

## Four-layer question map

| Layer | Required question | Main figures | Main interpretation limit |
|---|---|---|---|
| Structure | Where are modeled units and topics in the registered spaces? | `document-map`, `topic-map` | Two-dimensional distance is descriptive and projection-dependent |
| Representation | Which terms carry topic-specific lexical evidence? | `topic-term-barchart`, `ctfidf-term-score-decline` | c-TF-IDF is lexical evidence, not semantic separation or coherence |
| Taxonomy | Which topics are near, and what coarser hierarchy is defensible? | `topic-similarity-heatmap`, `topic-hierarchy` | The result depends on the declared relation basis and linkage |
| Governance | Is the selected snapshot robust, covered, non-leaky, and substantively usable? | prevalence, Pareto, stability, outlier, coverage/leakage | No one figure or weighted score establishes model quality |

Read this reference after model selection and before reporting or publication export.

## Freeze the visualization contract

Copy `assets/visualization-contract.json` into the study bundle. Fill it from the selected snapshot and source artifacts; do not infer case-specific column names.

Required identity:

- `study_id`, `snapshot_id`, and `route`;
- generic `field_map` entries for the actual unit ID, local topic ID, permanent topic UID, and label;
- `parent_document_id` for `long-document` and `mixed`;
- optional time, group, latitude, and longitude mappings only when they have a registered analytical role.

Register every input under `data_artifacts` as a relative path and a SHA-256 value. Core inputs include:

- topic terms and topic catalog;
- unit-topic assignments;
- frozen document and topic coordinates plus their projection parameters;
- one topic similarity matrix and one hierarchy/linkage artifact;
- one frozen topic-color map;
- candidate, stability, outlier, and coverage/leakage diagnostics.

Set `relation_spaces.topic_map.basis` and `relation_spaces.taxonomy.basis` explicitly:

- `semantic_topic_embeddings` when the space comes from registered topic embeddings;
- `document_topic_centroids` when it comes from registered document-embedding centroids;
- `ctfidf_lexical` when it comes from c-TF-IDF.

Never label `ctfidf_lexical` as semantic. Record how topic embeddings or centroids were constructed.

Keep `outlier_topic_id: "-1"`. The keys `topic_minus_one` in captions and `include_topic_minus_one` in manifest policies make its treatment auditable.

Retain the export policy:

```json
{
  "self_contained_html": true,
  "static_vector": true,
  "static_raster_png": true,
  "source_data": true,
  "caption": true,
  "alt_text": true,
  "sha256": true,
  "static_title_location": "caption",
  "colorblind_safe": true
}
```

Choose displayed topic sets, keyword depth, label length, opacity, point size, raster resolution, time bins, normalization, and annotation density from the target study. Register those choices and their calibration evidence. Do not copy native library defaults as research justification.

## Build and inspect the plan

Generate the deterministic plan:

```text
python scripts/build_visualization_plan.py --contract <study-bundle-directory>/visualization-contract.json --output <study-bundle-directory>/visualization-plan.json
```

The plan always lists every core figure. `blocked_missing_inputs` means the evidence must be produced; it is not permission to omit the figure. Route and metadata figures remain visible as either `ready` or `not_applicable`.

Before rendering, require readiness:

```text
python scripts/build_visualization_plan.py --contract <study-bundle-directory>/visualization-contract.json --output <study-bundle-directory>/visualization-plan.json --require-ready
```

Do not edit the generated plan by hand. Change the contract or source artifacts, then regenerate it.

## Mandatory core figures

The selected snapshot requires eleven conceptual figures:

| Figure ID | Layer | Research use |
|---|---|---|
| `topic-term-barchart` | representation | Compare ranked c-TF-IDF evidence within and across topics |
| `document-map` | structure | Inspect unit placement, boundaries, and Topic `-1` in one frozen projection |
| `topic-map` | structure | Inspect global topic relations in the declared space |
| `topic-similarity-heatmap` | taxonomy | Audit all topic-pair similarities in one matrix |
| `topic-hierarchy` | taxonomy | Inspect defensible coarser groupings from the same taxonomy relation |
| `ctfidf-term-score-decline` | representation | Inspect how quickly additional ranked terms lose topic-specific value |
| `topic-prevalence` | governance | Report topic count/share at the declared unit, including Topic `-1` |
| `candidate-pareto` | governance | Show non-dominated candidates and constraint failures without a composite score |
| `topic-stability` | governance | Show topic survival/alignment uncertainty across registered perturbations |
| `outlier-diagnostics` | governance | Explain the composition and nearest-topic evidence of Topic `-1` |
| `coverage-leakage-audit` | governance | Show missing-theme coverage and source/group leakage |

Do not collapse these into one dashboard screenshot. A dashboard may index them, but each figure keeps its own source data, caption, alt text, and manifest record.

## Render the seven baseline views

The following seven views are mandatory. Their example output names are stable and generic; manuscript figure numbers are assigned only when assembling a paper.

### 1. Topic-term bars

Required HTML: `visualize_barchart.html`.

Use the fitted model's `visualize_barchart` method or an equivalent plot built from the frozen `topic_terms` artifact. Use the registered topic set and keyword depth. Keep scores comparable within the selected representation snapshot and state whether displayed terms are surface or concept-normalized.

This is a c-TF-IDF representation figure. Do not claim it proves semantic distinctiveness.

### 2. Interactive document map

Required HTML: `visualize_documents.html`.

Compute or load document embeddings once, reduce them once, save the coordinates as `document_coordinates`, and pass those frozen reduced embeddings to `visualize_documents`. Preserve a stable unit ID in the figure-specific source data. Hover text must obey the study's privacy policy; use titles or redacted display text when raw documents are sensitive.

Do not cluster the two-dimensional coordinates.

### 3. Static publication datamap

Required raster example: `figure_bertopic_datamap.png`; also export SVG or PDF.

Use `visualize_document_datamap` or an equivalent publication renderer with the exact `document_coordinates` used by `visualize_documents`. Keep Topic `-1` visible as its own neutral but legible class. Use the same topic-color artifact and the same unit-topic assignments.

The static map and interactive map are two outputs of one conceptual `document-map`; disagreement in point coordinates, assignments, colors, or snapshot ID invalidates the bundle.

### 4. Intertopic map

Required HTML: `visualize_topics.html`.

Use `visualize_topics` or an equivalent topic-coordinate renderer. Set the representation choice from `relation_spaces.topic_map.basis` instead of accepting an unexamined default:

- semantic/topic-embedding basis: do not call the map lexical;
- `ctfidf_lexical`: set the native c-TF-IDF option and call the geometry lexical.

Bubble size may represent topic prevalence only when the source and denominator are explicit.

### 5. Similarity heatmap

Required HTML: `visualize_heatmap.html`.

Use `visualize_heatmap` or an equivalent heatmap from the registered `topic_similarity` matrix. Set the native c-TF-IDF switch from the taxonomy relation basis. Keep the complete selected topic set unless a declared secondary detail panel is being rendered. If reordered, export the row/column order in the source data.

Do not infer merge decisions from color alone. Link high-similarity pairs to `topic-pair-audit.csv`.

### 6. Topic hierarchy

Required HTML: `visualize_hierarchy.html`.

Use `visualize_hierarchy` or an equivalent dendrogram from the same topic set, `topic_similarity` artifact, basis, distance transform, and linkage registered for the heatmap. When passing a precomputed hierarchy, preserve its parent/child IDs in `topic_hierarchy`.

A dendrogram is a candidate taxonomy. It does not prove that every merge is substantively valid.

### 7. c-TF-IDF score decline

Required raster example: `figure_ctfidf_term_score_decline.png`; also export HTML and SVG or PDF.

Use `visualize_term_rank` or an equivalent rank plot from `topic_terms`. If scores are log-transformed, name the transformation on the axis and in the caption. Retain the raw score in the figure source data.

Interpret a sharp early drop as concentrated lexical representation, not automatically as a better topic. Flat or crossing profiles are audit prompts for keyword depth and term redundancy.

The current official BERTopic plotting reference documents these native methods:

- [documents and DataMapPlot](https://maartengr.github.io/BERTopic/getting_started/visualization/visualize_documents.html);
- [topic map](https://maartengr.github.io/BERTopic/api/plotting/topics.html);
- [topic-term bar chart](https://maartengr.github.io/BERTopic/api/plotting/barchart.html);
- [similarity heatmap](https://maartengr.github.io/BERTopic/api/plotting/heatmap.html);
- [topic hierarchy](https://maartengr.github.io/BERTopic/api/plotting/hierarchy.html);
- [term-score decline](https://maartengr.github.io/BERTopic/api/plotting/term.html).

Verify the installed BERTopic version before calling version-sensitive arguments. Record the package and plotting-library revisions in the experiment registry.

## Render governance figures

### Topic prevalence

Plot both count and share, or provide linked panels. State the denominator and analysis unit. Include Topic `-1`; do not hide it to make the model appear cleaner. For long documents, distinguish segment prevalence from parent-document prevalence.

### Candidate Pareto

Build from `candidate-metrics.csv` and the exact objective/constraint declaration used by `select_pareto.py`.

- mark ineligible candidates and their failed constraints;
- distinguish dominated and frontier candidates;
- identify the selected operating point only after the substantive decision;
- do not collapse lexical, semantic, coverage, stability, coherence, labelability, leakage, and outlier evidence into a weighted total.

Use facets or linked panels when more than two objectives matter.

### Topic stability

Align topics by permanent `topic_uid` before plotting. Show survival, match uncertainty, or distribution across the registered seeds, group-aware resamples, and snapshots. Do not compare unrelated local integer topic IDs.

### Outlier diagnostics

Build from Topic `-1` units, nearest-topic evidence, source/duplicate groups, and human audit. Separate:

- missing-theme candidates;
- source, template, or duplicate artifacts;
- boundary cases;
- genuinely irrelevant/noisy content.

Outlier fraction remains a guardrail, not an objective to minimize.

### Coverage and leakage

Combine `missing-theme-audit.csv`, group/source coverage diagnostics, and candidate metrics at matched granularity. Show reference themes or validation groups that are covered, partial, missing, or source-confounded. Do not treat purposive pre-model reconnaissance as prevalence evidence.

## Activate route and metadata figures

### Route figures

`network-short` and `mixed` require `short-text-artifact-audit`. Visualize duplicate-family, source/account/thread, template, hashtag/URL, and platform-token concentration by topic. Keep near duplicates independent unless the registered duplicate policy says otherwise.

`long-document` and `mixed` require `parent-document-topic-profile`. Show how segment topics contribute to each parent document or document class. Preserve parent ID, section/order evidence, aggregation rule, and Topic `-1`. Do not replace a multi-topic profile with one hard document label.

### Metadata figures

Enable a module only when its field mapping, source artifact, research question, denominator, and validation design are registered.

| Module | Figure | Activation rule |
|---|---|---|
| `time` | `topics-over-time` | A time field and frozen-taxonomy time-topic artifact exist |
| `group` | `topics-by-group` | A substantive group field and group-topic artifact exist |
| `geography` | `topic-geography` | Geographic mappings and geographic topic artifact exist |
| `lineage` | `topic-lineage` | Aligned snapshots and reviewed lineage evidence exist |
| `document_distribution` | `document-topic-distribution` | Validated per-document topic distributions exist |

Use one global taxonomy for time/group comparison unless the research design explicitly models separate taxonomies and aligns them. The official BERTopic API supports topics-over-time, topics-per-class, and document probability distributions, but its numerical display cutoffs are not universal research settings.

## Preserve cross-figure consistency

Freeze and hash:

- unit-topic assignments;
- topic catalog and permanent UIDs;
- document coordinates and projection parameters;
- topic coordinates and projection parameters;
- taxonomy similarity matrix, topic order, distance transform, and hierarchy linkage;
- topic-color map;
- representation snapshot and topic terms;
- candidate and diagnostic tables.

Use the same topic UID, label, and color in every figure. A label refresh may change displayed text only when the manifest links the new representation snapshot and retains the same assignments.

The heatmap and hierarchy must share one taxonomy relation artifact and basis. The document HTML, vector, and PNG must share one coordinate artifact. The static publication title belongs in the caption, not as a large title inside the plotting area.

## Export and manifest contract

Every required figure has six outputs:

1. `interactive_html`: complete offline HTML with Plotly or other runtime embedded; no CDN script or stylesheet;
2. `static_vector`: SVG or PDF generated from the plotting source, not traced from a screenshot;
3. `static_raster`: PNG generated from the same source;
4. `source_data`: figure-specific CSV, TSV, JSON, Parquet, Arrow, or Feather;
5. `caption`: Markdown or text;
6. `alt_text`: concise accessible description.

Use plain backgrounds, legible text, restrained grid lines, colorblind-safe colors, direct labels where feasible, and one stable topic-color map. Do not encode a claim by color alone. Retain shape, labels, or panel structure for accessibility.

After rendering, copy `assets/visualization-manifest.json` and populate one record per ready figure. Each record contains:

- the exact planned identity, layer, inputs, basis, coordinate/relation/color links, and outlier policy;
- `status: rendered`;
- research question, interpretation, and limitations;
- a nonempty render-parameter record;
- `title_location: caption`;
- paths and SHA-256 values for all six outputs;
- `self_contained: true` on the HTML output.

Do not put absolute local paths or credentials in a public bundle.

## Caption and interpretation contract

Write each caption so it stands alone:

1. what the marks, axes, color, size, and ordering represent;
2. analysis unit and denominator;
3. selected snapshot and hierarchy level;
4. relation basis and projection/linkage method when applicable;
5. Topic `-1` treatment;
6. transformation or normalization;
7. principal finding without causal overstatement;
8. main limitation;
9. source-data artifact.

Alternative text describes the main visual relationship and important exceptions; it does not repeat every label.

Do not say:

- “topics are objectively far apart” from a 2D projection;
- “the model is coherent” from term bars;
- “the hierarchy proves the right topic count” from a dendrogram;
- “low outlier rate proves quality”;
- “the selected model is best” when it is one Pareto operating point.

## Validate the bundle

Run:

```text
python scripts/validate_visualization_bundle.py <study-bundle-directory>
```

The validator rebuilds the plan, verifies all registered inputs and outputs, checks file signatures and hashes, rejects unsafe paths and external HTML dependencies, and enforces the cross-figure invariants.

Fix every error before claiming a complete research bundle. A PNG alone, a screenshot, an HTML file linked to a CDN, a figure without source data, a stale plan, or a missing governance figure is incomplete.

## Common failures

| Failure | Why it is invalid | Required correction |
|---|---|---|
| Only BERTopic's default HTML files are delivered | Model governance and publication reproducibility are missing | Complete the plan and all six output forms |
| Static and interactive document maps differ | They no longer describe the same projection | Re-render both from the frozen coordinate artifact |
| Topic map is called semantic without a declared basis | c-TF-IDF and embedding geometry answer different questions | Register and label the actual basis |
| Heatmap and hierarchy use different topic sets or distance bases | Their taxonomy claims cannot be compared | Rebuild both from one registered relation artifact |
| Topic `-1` is hidden | Missing themes and artifacts are concealed | Show it in document, prevalence, and outlier figures |
| Candidate metrics are collapsed into one score | Trade-offs and constraints disappear | Use a Pareto/constraint view |
| Time or group chart uses separately refitted topic numbers | Topic identities are not comparable | Use a frozen global taxonomy or reviewed lineage alignment |
| Figure numbers are hard-coded in the reusable skill | Paper ordering becomes case-specific | Assign figure numbers only during manuscript assembly |
| A screenshot is treated as a publication export | Vector source, data, parameters, and accessibility are lost | Export from the plotting source and retain the manifest |
