# BERTopic Tuning

A diversity-first Codex skill for academically defensible BERTopic tuning, evaluation, and continuous model iteration across **short network texts** and **long documents**.

The central objective is **effective thematic diversity**: distinct, well-covered, stable, and interpretable themes at a substantively meaningful granularity. Raw topic count and outlier rate are reported, but neither is treated as the optimization target.

## What this repository provides

- Separate modeling routes for short, noisy network text and multi-theme long documents.
- A multi-dimensional diversity framework covering lexical distinctiveness, semantic distinctiveness, theme coverage, stability, and human interpretability.
- A clear separation between structural clustering, topic representation, taxonomy editing, and model governance.
- Corpus-derived tuning decisions instead of universal parameter grids copied from papers or examples.
- Pareto-based model selection with explicit quality constraints.
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

Invoke it explicitly with `$bertopic-tuning` and provide the corpus location, research question, and any existing model outputs.

Example for short network text:

```text
Use $bertopic-tuning to design and execute a diversity-first BERTopic study for
Chinese social-media posts. Audit duplicates and platform artifacts, compare
structural candidates, and select a Pareto-optimal model without minimizing the
outlier fraction as the primary objective.
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
使用 $bertopic-tuning 分析这批长文本。先按语义结构切分并保留父文档关系，
再以词汇区分度、语义区分度、主题覆盖、稳定性和人工可解释性共同评估模型，
不要把降低离群率作为主要目标。
```

## End-to-end workflow

1. **Inspect and fingerprint** the corpus, metadata, duplicates, languages, lengths, sources, dates, and parent-document structure.
2. **Create a study contract** defining the research claim, modeling route, meaningful theme size, evaluation dimensions, calibration rules, and stopping criteria.
3. **Fit an auditable baseline** with cached embeddings and fixed evaluation samples.
4. **Tune structure** through testable hypotheses about the encoder, UMAP, HDBSCAN, granularity, seeds, and resamples.
5. **Tune representation** while assignments remain fixed: tokenization, phrases, user-managed lexicon bundles, c-TF-IDF variants, frequent-term suppression, MMR, and grounded labels.
6. **Audit the taxonomy** before any merge or split, using nearest-topic pairs and representative evidence.
7. **Select on a Pareto frontier** under explicit coherence, coverage, stability, and labelability constraints.
8. **Track iteration and lineage** with permanent topic UIDs and calibrated snapshot alignment.
9. **Complete and validate the study bundle** so every decision, failure, threshold, and topic change remains reproducible.

The detailed operating procedure is in [SKILL.md](SKILL.md).

## Included command-line tools

The portable command-line tools use only the Python standard library. The optional `build_count_vectorizer()` adapter imports scikit-learn only inside the user's modeling environment. The repository does not impose a BERTopic version, encoder, tokenizer or universal tuning grid.

| Tool | Purpose |
|---|---|
| `scripts/evaluate_diversity.py` | Calculates topic-level lexical and semantic diversity diagnostics from a portable topic catalog |
| `scripts/select_pareto.py` | Filters candidates by explicit constraints and returns the non-dominated model set |
| `scripts/align_snapshots.py` | Aligns old and new topic snapshots using locally calibrated semantic, keyword, and document evidence |
| `scripts/validate_study_bundle.py` | Checks whether the required research artifacts and decisions are complete |
| `scripts/build_lexicon_bundle.py` | Validates editable synonym, stopword and custom-term tables and compiles a content-addressed manifest |
| `scripts/evaluate_representation_update.py` | Proves assignments stayed frozen and compares surface/concept lexical evidence before and after a lexicon refresh |

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

### Validate a completed study bundle

```bash
python scripts/validate_study_bundle.py <study-bundle-directory>
```

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

- `study-contract.json`
- `corpus-profile.json`
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

- [references/academic-evidence.md](references/academic-evidence.md) for the evidence map and source-to-decision boundaries;
- [references/web-research-protocol.md](references/web-research-protocol.md) when claims depend on current papers, APIs, package behavior, or model availability;
- [references/study-contract-and-reporting.md](references/study-contract-and-reporting.md) for required artifacts and reporting standards;
- [references/bertopic-implementation.md](references/bertopic-implementation.md) when implementing or reviewing BERTopic code.

## Repository structure

```text
bertopic-tuning/
├── SKILL.md
├── README.md
├── HANDOFF.md
├── LICENSE
├── agents/
│   └── openai.yaml
├── assets/
│   └── reusable study and audit templates
├── references/
│   ├── network-short-text.md
│   ├── long-document.md
│   ├── diversity-evaluation.md
│   ├── lexicon-management-and-iteration.md
│   ├── iteration-and-lineage.md
│   └── research, implementation, and reporting guidance
└── scripts/
    ├── evaluate_diversity.py
    ├── build_lexicon_bundle.py
    ├── evaluate_representation_update.py
    ├── select_pareto.py
    ├── align_snapshots.py
    ├── validate_study_bundle.py
    └── tests/
```

## Validation

Run the complete test suite from the repository root:

```bash
python -m unittest discover -s scripts/tests -v
```

The current suite covers diversity evaluation, Pareto selection, snapshot alignment, and study-bundle validation.

## Maintainer handoff

To continue the project in a new Codex conversation, start with the current state, constraints, validation commands, and copy-ready opening prompt in [HANDOFF.md](HANDOFF.md).

## Scope

This repository is a research and decision framework plus portable evaluation tooling. It intentionally does not prescribe one embedding model, one topic count, one HDBSCAN setting, or one universal threshold. Those choices must be generated and justified from the target corpus, research question, validation design, and compute constraints.

## License

Released under the [MIT License](LICENSE). You may use, modify, and distribute the repository provided that the copyright and license notice are retained.
