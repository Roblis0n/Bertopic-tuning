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
5. **Tune representation** while assignments remain fixed: tokenization, phrases, c-TF-IDF variants, frequent-term suppression, MMR, and grounded labels.
6. **Audit the taxonomy** before any merge or split, using nearest-topic pairs and representative evidence.
7. **Select on a Pareto frontier** under explicit coherence, coverage, stability, and labelability constraints.
8. **Track iteration and lineage** with permanent topic UIDs and calibrated snapshot alignment.
9. **Complete and validate the study bundle** so every decision, failure, threshold, and topic change remains reproducible.

The detailed operating procedure is in [SKILL.md](SKILL.md).

## Included command-line tools

The helper scripts use only the Python standard library. They evaluate exported model artifacts; they do not impose a BERTopic version, encoder, or universal tuning grid.

| Tool | Purpose |
|---|---|
| `scripts/evaluate_diversity.py` | Calculates topic-level lexical and semantic diversity diagnostics from a portable topic catalog |
| `scripts/select_pareto.py` | Filters candidates by explicit constraints and returns the non-dominated model set |
| `scripts/align_snapshots.py` | Aligns old and new topic snapshots using locally calibrated semantic, keyword, and document evidence |
| `scripts/validate_study_bundle.py` | Checks whether the required research artifacts and decisions are complete |

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

Copy these templates into the analysis workspace and complete them with corpus-specific evidence. A header-only template or an unexplained threshold is not a finished artifact.

## Continuous model iteration

The skill distinguishes four kinds of change:

- **Representation refresh:** labels or keywords change while assignments stay fixed.
- **Structural refit:** embeddings or clustering change topic membership.
- **Taxonomy edit:** reviewed topics are merged, split, renamed, or retired.
- **New-data mapping:** new units are mapped into a frozen reference taxonomy before deciding whether retraining is necessary.

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
├── agents/
│   └── openai.yaml
├── assets/
│   └── reusable study and audit templates
├── references/
│   ├── network-short-text.md
│   ├── long-document.md
│   ├── diversity-evaluation.md
│   ├── iteration-and-lineage.md
│   └── research, implementation, and reporting guidance
└── scripts/
    ├── evaluate_diversity.py
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

## Scope

This repository is a research and decision framework plus portable evaluation tooling. It intentionally does not prescribe one embedding model, one topic count, one HDBSCAN setting, or one universal threshold. Those choices must be generated and justified from the target corpus, research question, validation design, and compute constraints.

## License

Released under the [MIT License](LICENSE). You may use, modify, and distribute the repository provided that the copyright and license notice are retained.
