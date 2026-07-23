# BERTopic Tuning

A diversity-first Codex skill for academically defensible BERTopic tuning, evaluation, layered research-grade visualization, and continuous model iteration across **short network texts** and **long documents**.

The central objective is **effective thematic diversity**: distinct, well-covered, stable, and interpretable themes at a substantively meaningful granularity. Raw topic count and outlier rate are reported, but neither is treated as the optimization target.

## What this repository provides

- Separate modeling routes for short, noisy network text and multi-theme long documents.
- A mandatory corpus-scale theme reconnaissance with full source accounting, direct full-text review for manageable corpora, and audited progressive extraction/reading for large or multi-file corpora.
- An explicit user-direction gate: the skill reports its provisional map, pauses, and fits BERTopic only after recorded authorization.
- A multi-dimensional diversity framework covering lexical distinctiveness, semantic distinctiveness, theme coverage, stability, and human interpretability.
- A clear separation between structural clustering, topic representation, taxonomy editing, and model governance.
- Corpus-derived tuning decisions instead of universal parameter grids copied from papers or examples.
- Pareto-based model selection with explicit quality constraints.
- A four-layer research figure system covering structure, representation, taxonomy, and governance, with the required BERTopic views paired with publication and audit artifacts.
- Topic alignment and lineage tracking across corpus or model updates.
- User-managed synonym, stopword and custom/domain-term bundles with frozen-assignment representation iteration.
- Portable command-line tools, study templates, tests, and research-oriented reporting guidance.
- An academic evidence map and a protocol for verifying current papers, software behavior, and model availability.

## Modeling routes

Route the corpus by its observable structure, not merely by its source.

| Route | Use it when | Main modeling unit | Main diversity risk |
|---|---|---|---|
| `network-short` | Texts are short, sparse, conversational, duplicated, platform-shaped, or context-dependent | One meaningful post, comment, message, or reconstructed conversational unit | Artificial micro-topics caused by templates, sources, slang, duplicates, or missing context |
| `long-document` | Documents contain several themes, exceed useful encoder context, or require section-to-document interpretation | Semantically coherent segments linked to a permanent parent-document ID | One-vector compression, dominant-section bias, and invalid chunk-level resampling |
| `mixed` | Both conditions occur in one corpus | Partitioned units, modeled by route | A shared taxonomy that hides route-specific themes |

### Short network text

The short-text route emphasizes:

- duplicate and near-duplicate groups;
- source, account, thread, repost, and temporal context;
- platform artifacts, boilerplate, hashtags, URLs, emoji, slang, and domain phrases;
- embedding comparisons built from same-theme, confusing-different, and clearly-different text pairs;
- group-aware validation so duplicate families or related messages cannot leak across samples;
- explicit auditing of small clusters to distinguish genuine niche themes from source or template artifacts.

See [references/network-short-text.md](references/network-short-text.md) for the complete route.

### Long documents

The long-document route emphasizes:

- segmentation by natural sections, paragraphs, discourse boundaries, or other meaningful units;
- preservation of `parent_document_id`, segment order, section name, and source metadata;
- chunk-level topic discovery with document-level aggregation or multi-topic profiles;
- parent-document bootstrap and validation rather than random chunk resampling;
- interpretation at both segment and document levels;
- hierarchical analysis when broad document themes contain recurring subthemes.

See [references/long-document.md](references/long-document.md) for the complete route.

## Diversity-first evaluation

No single metric defines a good topic model. Candidate models are evaluated as a vector:

| Dimension | Question | Typical evidence |
|---|---|---|
| Lexical distinctiveness | Do topics use meaningfully different ranked vocabularies? | Topic Diversity plus rank-aware overlap such as RBO |
| Semantic distinctiveness | Are nearby topics genuinely different in meaning? | Nearest-topic similarity, representative-unit comparison, redundancy audits |
| Theme coverage | Are known or emerging themes represented without systematic omissions? | Validation labels, missing-theme audits, source and subgroup coverage |
| Stability | Do important themes survive seeds, group-aware resamples, and new data? | Assignment, taxonomy, and theme-survival comparisons |
| Human interpretability | Can reviewers label and distinguish topics consistently? | Representative, random, and boundary-unit audits |

Coherence and labelability act as quality floors. Topic count is compared only at matched counts, within a declared count band, or at equivalent hierarchy levels. The outlier fraction is a **diagnostic guardrail** used to investigate missing themes, artifacts, and genuine noise—not a score to minimize blindly.

For metric definitions and calibration rules, see [references/diversity-evaluation.md](references/diversity-evaluation.md).

## Layered research-grade visualization

The skill converts a selected snapshot into an auditable figure bundle instead of stopping at default BERTopic HTML. The mandatory core catalog contains:

| Layer | Core figures |
|---|---|
| Structure | Interactive/static document map from one frozen coordinate artifact; intertopic map with a declared relation basis |
| Representation | Per-topic c-TF-IDF bars; ranked c-TF-IDF term-score decline |
| Taxonomy | Topic similarity heatmap and hierarchy from one registered relation artifact |
| Governance | Topic prevalence including `-1`; candidate Pareto frontier; topic stability; outlier composition; coverage/leakage audit |

Seven baseline views remain explicit: `visualize_barchart.html`, `visualize_documents.html`, a publication document datamap, `visualize_topics.html`, `visualize_heatmap.html`, `visualize_hierarchy.html`, and a c-TF-IDF term-score-decline figure. The reusable contract does not hard-code corpus fields, language, topic count, or manuscript figure numbering.

Every required figure has self-contained HTML, SVG or PDF, PNG, figure-specific source data, a caption, alternative text, render parameters, and SHA-256 evidence. Interactive and static document maps share the same coordinates; heatmap and hierarchy share the same topic relation space; lexical and semantic geometries are labeled explicitly; Topic `-1` remains visible in document, prevalence, and outlier reporting.

Route-specific and metadata-specific figures are activated from the study contract:

- short-text artifact audits for `network-short`;
- parent-document topic profiles for `long-document`;
- both for `mixed`;
- time, group, geography, lineage, and document-distribution figures only when their fields and source artifacts are registered.

See [references/research-grade-visualization.md](references/research-grade-visualization.md) for the complete method.

## Installation

### Project-scoped installation

From the root of the project where you want to use the skill:

```powershell
New-Item -ItemType Directory -Force .agents\skills | Out-Null
git clone https://github.com/Roblis0n/Bertopic-tuning.git .agents\skills\bertopic-tuning
```

For macOS or Linux:

```bash
mkdir -p .agents/skills
git clone https://github.com/Roblis0n/Bertopic-tuning.git .agents/skills/bertopic-tuning
```

Restart or reload Codex if the skill is not discovered immediately.

### Update an existing installation

```powershell
git -C .agents\skills\bertopic-tuning pull --ff-only
```

## Using the skill

Invoke it explicitly with `$bertopic-tuning` and provide the corpus location, research question, user-theme mainline, and any existing model outputs. The skill first accounts for every source unit and estimates whether complete unique-content reading fits the available context and time. It then uses either direct full-text review or audited progressive extraction, reports the semantic-review denominator, residual risk, provisional theme map and count range, and pauses for your direction before modeling. Exhausting the resource budget before the registered stopping rule is satisfied produces an `interim` incomplete reconnaissance, not an approvable `stop_with_residual_risk` preview.

Example for short network text:

```text
Use $bertopic-tuning to design and execute a diversity-first BERTopic study for
Chinese social-media posts. First inspect the full corpus and show me coarse and
fine candidate themes centered on my research mainline. Wait for my direction,
then compare structural candidates and select a Pareto-optimal model.
```

Example for long documents:

```text
Use $bertopic-tuning to model a collection of long policy documents. Design a
section-aware segmentation strategy, preserve parent-document links, evaluate
topic diversity at matched granularity, and produce a reproducible topic-lineage
plan for future corpus updates.
```

中文调用示例：

```text
使用 $bertopic-tuning 分析这批长文本。先全量核算语料并保留父文档关系；若全文
阅读超出时间或上下文预算，改用可审计的分层提取、风险升级全文和独立留出复核。
先告诉我实际语义阅读覆盖、残余风险及粗细粒度主题预估，等我确认后再建模；最后
共同评估主题覆盖、稳定性和可解释性。
```

## End-to-end workflow

1. **Inspect and fingerprint** the corpus, metadata, duplicates, languages, lengths, sources, dates, parent-document structure and per-unit content SHA-256.
2. **Choose and execute the reading mode**: reconcile a full source census with unique ledger IDs; use direct full text when feasible or progressive extraction with registered artifacts, bounded hashed spans, five selection channels and a final-independent probability holdout. Mixed corpora must satisfy these requirements separately in both route subsets. Then report semantic-review depth, residual risk and evidence-linked coarse/fine estimates.
3. **Pause for user direction** and record candidate dispositions plus explicit authorization bound to the current pre-model artifact fingerprint; no embeddings or model fitting occur while the gate is waiting.
4. **Create a study contract** defining the research claim, modeling route, meaningful theme size, evaluation dimensions, calibration rules, and stopping criteria.
5. **Fit an auditable baseline** with cached embeddings and fixed evaluation samples.
6. **Tune structure** through testable hypotheses about the encoder, UMAP, HDBSCAN, granularity, seeds, and resamples.
7. **Tune representation** while assignments remain fixed: tokenization, phrases, user-managed lexicon bundles, c-TF-IDF variants, frequent-term suppression, MMR, and grounded labels.
8. **Audit the taxonomy** before any merge or split, using nearest-topic pairs and representative evidence.
9. **Select on a Pareto frontier** under explicit coherence, coverage, stability, and labelability constraints.
10. **Build the layered research visualization** from a deterministic contract and plan, then validate the rendered HTML/vector/PNG/source/caption/alt-text manifest.
11. **Track iteration and lineage** with permanent topic UIDs and calibrated snapshot alignment.
12. **Complete and validate the study bundle** so every decision, failure, threshold, topic change, and research figure remains reproducible.

The detailed operating procedure is in [SKILL.md](SKILL.md).

## Included command-line tools

The portable command-line tools use only the Python standard library. The reconnaissance validator checks artifacts and the pause gate; it does not call an LLM provider or claim to read a corpus by itself. The optional `build_count_vectorizer()` adapter imports scikit-learn only inside the user's modeling environment. The repository does not impose a BERTopic version, encoder, tokenizer or universal tuning grid.

| Tool | Purpose |
|---|---|
| `scripts/validate_theme_reconnaissance.py` | Verifies unique ledger IDs, content hash/length and canonical duplicate identity, registered bounded extraction spans, per-route mixed coverage/channels/holdouts, parent accounting, semantic-review depth, prevalence firewall, structured stopping state, pre-model artifact binding, and the authorization gate |
| `scripts/evaluate_diversity.py` | Calculates topic-level lexical and semantic diversity diagnostics from a portable topic catalog |
| `scripts/select_pareto.py` | Filters candidates by explicit constraints and returns the non-dominated model set |
| `scripts/align_snapshots.py` | Aligns old and new topic snapshots using locally calibrated semantic, keyword, and document evidence |
| `scripts/validate_study_bundle.py` | Checks whether the required research artifacts and decisions are complete |
| `scripts/build_lexicon_bundle.py` | Validates editable synonym, stopword and custom-term tables and compiles a content-addressed manifest |
| `scripts/evaluate_representation_update.py` | Proves assignments stayed frozen and compares surface/concept lexical evidence before and after a lexicon refresh |
| `scripts/build_visualization_plan.py` | Generates the deterministic core, route, and metadata-conditional figure registry from a generic visualization contract |
| `scripts/validate_visualization_bundle.py` | Verifies the contract-plan-manifest chain, shared geometry, declared relation bases, Topic `-1`, offline HTML, vector/PNG signatures, source data, captions, alt text, safe paths, and hashes |

### Evaluate diversity

Input topics use a portable JSON structure:

```json
{
  "topics": [
    {
      "topic_id": "T-health",
      "keywords": ["vaccination", "immunity", "public health"],
      "embedding": [0.81, 0.12, 0.44],
      "size": 120
    }
  ]
}
```

Run:

```bash
python scripts/evaluate_diversity.py \
  --input topics.json \
  --output diversity-scorecard.json \
  --top-k <registered-keyword-depth> \
  --rbo-p <registered-rank-persistence>
```

Add `--semantic-redundancy-threshold` only when that threshold has been calibrated from the target study.

### Select Pareto-optimal candidates

```bash
python scripts/select_pareto.py \
  --input candidate-metrics.csv \
  --output pareto.json \
  --maximize irbo \
  --maximize semantic_diversity \
  --maximize coverage \
  --maximize stability \
  --constraint "coherence>=<calibrated-floor>"
```

Objectives and constraints must come from the study contract. Outlier fraction can be reported or constrained when substantively justified, but it should not silently dominate selection.

### Align model snapshots

```bash
python scripts/align_snapshots.py \
  --old old-topics.json \
  --new new-topics.json \
  --thresholds calibrated-thresholds.json \
  --output alignment.json
```

One-to-many and many-to-one matches are split and merge candidates requiring evidence and review; they are not automatic lineage decisions.

### Validate the pre-model theme preview

Copy `corpus-reading-plan.json`, `corpus-reading-ledger.csv`, `theme-reconnaissance.json`, `theme-candidate-audit.csv`, `modeling-authorization.json` and `corpus-profile.json` from `assets/` into the study bundle. After reconciling the source census and completing the registered direct or progressive reading procedure, validate the preview before showing it to the user:

```bash
python scripts/validate_theme_reconnaissance.py <study-bundle-directory>
```

Leave the gate at `awaiting_user_direction` while the user reviews the candidate map, semantic-review denominator and residual risk. A completed plan must be `complete_for_preview`, use the appropriate full-text or local-holdout termination basis, and record `resource_budget_exhausted: false`; resource exhaustion produces only an interim result. Candidate rows remain `prevalence_claimed: false` with `claim_scope: semantic_evidence_only`. After recording all accept, reject, merge, split, defer or reframe instructions—and `progressive_reading_risk_acknowledged: true` for progressive reading—record a fresh `pre_model_artifact_fingerprint` over the approved profile, plan, ledger, reconnaissance and candidate map, then require approval before any modeling process begins:

```bash
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
```

The coarse/fine estimate is explicitly `pre_model_hypothesis_not_target_k`; it supports later coverage and missing-theme checks but never forces BERTopic's topic count. See [references/corpus-theme-reconnaissance.md](references/corpus-theme-reconnaissance.md).

### Validate a completed study bundle

```bash
python scripts/validate_study_bundle.py <study-bundle-directory>
```

### Plan and validate the research figures

Copy `visualization-contract.json` and `visualization-manifest.json` from `assets/`. Register the selected snapshot, generic field map, frozen input artifacts, document projection, topic relation spaces, conditional modules and output policy. Build the figure plan:

```bash
python scripts/build_visualization_plan.py \
  --contract study/visualization-contract.json \
  --output study/visualization-plan.json
```

The plan preserves missing core figures as `blocked_missing_inputs`. Require a complete input registry before rendering:

```bash
python scripts/build_visualization_plan.py \
  --contract study/visualization-contract.json \
  --output study/visualization-plan.json \
  --require-ready
```

After producing all six output forms per ready figure and populating the manifest, run:

```bash
python scripts/validate_visualization_bundle.py study
```

The planner and validator use only the Python standard library. Rendering remains in the fitted BERTopic/Plotly environment and follows [references/research-grade-visualization.md](references/research-grade-visualization.md).

### Compile and iterate user lexicons

Copy `lexicon-config.json`, `synonyms.csv`, `stopwords.csv` and `custom-terms.csv` from `assets/`, edit ordinary UTF-8 CSV/JSON files, then compile them:

```bash
python scripts/build_lexicon_bundle.py \
  --config study/lexicon-config.json \
  --output study/lexicon-manifest.json
```

Fill the tokenizer `name` and `revision` before compiling, and keep all three CSV source tables inside the study's lexicon directory. The compiler rejects unidentified tokenizers, paths that escape the bundle, conflicts, cycles, and incomplete active-row evidence; the study-bundle validator rejects stale or tampered manifests.

Apply the compiled bundle to the lexical tokenizer and refresh topics with BERTopic's `update_topics()`. Then prove that assignments stayed unchanged and generate the next review queue:

```bash
python scripts/evaluate_representation_update.py \
  --before-topics study/baseline-topics.json \
  --after-topics study/candidate-topics.json \
  --before-assignments study/baseline-assignments.csv \
  --after-assignments study/candidate-assignments.csv \
  --lexicon-manifest study/lexicon-manifest.json \
  --top-k <registered-keyword-depth> \
  --rbo-p <registered-rank-persistence> \
  --output study/representation-comparison.json \
  --candidate-output study/lexicon-candidate-audit.csv
```

Custom terms protect tokenizer phrases; they are not passed as a closed `CountVectorizer(vocabulary=...)` allowlist. Review every generated candidate before changing a source table. See [references/lexicon-management-and-iteration.md](references/lexicon-management-and-iteration.md).

Assignment exports use `unit_id` plus `topic_uid` (preferred) or `topic_id`. The evaluator rejects changed assignments, changed permanent or local topic IDs, and assignment IDs absent from the topic catalog; `-1` remains the permitted outlier assignment.

## Study templates

The `assets/` directory contains reusable artifacts for a reproducible study:

- `corpus-profile.json`
- `corpus-reading-plan.json`
- `corpus-reading-ledger.csv`
- `theme-reconnaissance.json`
- `theme-candidate-audit.csv`
- `modeling-authorization.json`
- `study-contract.json`
- `experiment-registry.csv`
- `candidate-metrics.csv`
- `selected-model.json`
- `topic-catalog.csv`
- `human-topic-audit.csv`
- `topic-pair-audit.csv`
- `missing-theme-audit.csv`
- `topic-lineage.csv`
- `evidence-log.csv`
- `decision-report.md`
- `visualization-contract.json`, generated `visualization-plan.json`, and `visualization-manifest.json`
- `lexicon-config.json`, `synonyms.csv`, `stopwords.csv`, `custom-terms.csv`
- `lexicon-candidate-audit.csv`, `lexicon-lineage.csv`, `representation-iteration.csv`

Copy these templates into the analysis workspace and complete them with corpus-specific evidence. A header-only template or an unexplained threshold is not a finished artifact.

## Continuous model iteration

The skill distinguishes four kinds of change:

- **Representation refresh:** labels or keywords change while assignments stay fixed.
- **Structural refit:** embeddings or clustering change topic membership.
- **Taxonomy edit:** reviewed topics are merged, split, renamed, or retired.
- **New-data mapping:** new units are mapped into a frozen reference taxonomy before deciding whether retraining is necessary.

A synonym, stopword or custom-term edit is a representation refresh when it affects `lexical_text` only. Each compiled bundle receives a content-derived ID and separate lexicon lineage. If the edit touches embedding text or changes assignments, it becomes a structural refit candidate.

Permanent `topic_uid` values are kept separate from BERTopic's local integer IDs. Each update records continuations, new topics, retirements, merges, splits, unresolved mappings, and the evidence behind those decisions. See [references/iteration-and-lineage.md](references/iteration-and-lineage.md).

## Academic evidence and reproducibility

The repository translates literature into mechanisms and testable hypotheses; it does not copy numerical settings from unrelated corpora. Use:

- [references/corpus-theme-reconnaissance.md](references/corpus-theme-reconnaissance.md) for the corpus-scale preview, count estimation, and authorization gate;
- [references/scalable-corpus-reading.md](references/scalable-corpus-reading.md) for large/multi-file extraction, adaptive selection, full-text escalation, holdout auditing and residual-risk reporting;
- [references/academic-evidence.md](references/academic-evidence.md) for the evidence map and source-to-decision boundaries;
- [references/web-research-protocol.md](references/web-research-protocol.md) when claims depend on current papers, APIs, package behavior, or model availability;
- [references/study-contract-and-reporting.md](references/study-contract-and-reporting.md) for required artifacts and reporting standards;
- [references/research-grade-visualization.md](references/research-grade-visualization.md) for the layered core/conditional figure system and artifact contract;
- [references/bertopic-implementation.md](references/bertopic-implementation.md) when implementing or reviewing BERTopic code.

## Repository structure

```text
bertopic-tuning/
├── SKILL.md
├── README.md
├── LICENSE
├── agents/
│   └── openai.yaml
├── assets/
│   └── reusable study and audit templates
├── references/
│   ├── corpus-theme-reconnaissance.md
│   ├── scalable-corpus-reading.md
│   ├── network-short-text.md
│   ├── long-document.md
│   ├── diversity-evaluation.md
│   ├── research-grade-visualization.md
│   ├── lexicon-management-and-iteration.md
│   ├── iteration-and-lineage.md
│   └── research, implementation, and reporting guidance
└── scripts/
    ├── validate_theme_reconnaissance.py
    ├── evaluate_diversity.py
    ├── build_lexicon_bundle.py
    ├── evaluate_representation_update.py
    ├── select_pareto.py
    ├── align_snapshots.py
    ├── build_visualization_plan.py
    ├── validate_visualization_bundle.py
    ├── validate_study_bundle.py
    └── tests/
```

## Validation

Run the complete test suite from the repository root:

```bash
python -m unittest discover -s scripts/tests -v
```

The suite covers pre-model reconnaissance and authorization, diversity evaluation, Pareto selection, snapshot alignment, lexicon iteration, deterministic visualization planning, rendered artifact validation, and completed study-bundle validation.

## Scope

This repository is a research and decision framework plus portable evaluation and visualization-governance tooling. It estimates a provisional coarse/fine theme range from audited target-corpus evidence and asks for user direction before modeling. For large corpora it reports the exact semantic-review denominator and residual risk instead of pretending that selected evidence is complete full-text coverage. It defines a generic layered figure contract but does not install or pin a plotting stack. It intentionally does not prescribe one embedding model, one target topic count, one HDBSCAN setting, one reading sample size, one manuscript figure order, or one universal threshold. Final choices must be generated and justified from the target corpus, research question, validation design, user authorization, and compute constraints.

## License

Released under the [MIT License](LICENSE). You may use, modify, and distribute the repository provided that the copyright and license notice are retained.
