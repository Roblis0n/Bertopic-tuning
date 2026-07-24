---
name: bertopic-tuning
description: Use when a user requests BERTopic tuning, 主题建模调参, topic-diversity evaluation, semantic topic interpretation, short-text or long-document topic modeling, model comparison, topic stability or lineage, synonyms, stopwords, custom/domain lexicons, research visualization, or reproducible BERTopic reporting.
---

# BERTopic Tuning

## Core principle

Understand topic meanings from original text, improve one current champion, and
scale evidence to the claim. Original text is authoritative for topic identity,
boundaries, labels, merges, splits, and promotion decisions. Algorithmic output
is diagnostic triage only: it decides what deserves reading, not what a topic
means.

Keep four layers separate:

- **structure** changes assignments through analysis units, embeddings, UMAP, or
  HDBSCAN;
- **representation** changes words and labels while assignments stay frozen;
- **taxonomy** records reviewed merges, splits, and hierarchy;
- **governance** records evidence, decisions, stability, lineage, and release
  obligations.

Optimize effective thematic diversity rather than raw topic count, Topic
Diversity alone, coherence alone, or a low Topic `-1` rate.

## Choose the assurance level

Choose the level from the requested outcome before collecting artifacts.

| Level | Use it when | Modeling authorization | Semantic review | Delivery |
|---|---|---|---|---|
| `exploratory` | The user asks to try, inspect feasibility, establish a baseline, or tune quickly without a research/release claim | The modeling request itself is sufficient | Read the current champion and risky topics/pairs; mark provisional choices `exploratory_only` | Compact contract, profile, registry, metrics, `tuning-trace.json`, `semantic-review.json`, decision report |
| `research` | The user needs a defensible comparison or substantive topic interpretation | Record the modeling request; pause only if reconnaissance reveals a scope-changing ambiguity | Read every promoted stage winner and all finalists; validate grouped stability and missing themes on finalists | Exploratory set plus selected model, topic catalog, concise reconnaissance, missing-theme evidence |
| `publication_release` | The result will be submitted, published, released, or used as a production taxonomy | Complete the preview and explicit approval gate | Complete topic, pair, coverage, outlier, lineage, and reviewer audit | Full reproducibility and visualization bundle |

If an existing contract has no `assurance_level`, treat it as legacy
`publication_release` and emit a migration warning. Never silently downgrade an
old bundle.

Provisional defaults are allowed only for exploratory work. Record their
provenance, keep `permitted_for_final_selection: false`, and never use them to
justify a research or publication result.

## Route the corpus

Choose from content structure, not the source label.

| Route | Observable condition | Read completely |
|---|---|---|
| `network-short` | Short, sparse, conversational, duplicated, platform-shaped, or context-dependent units | `references/network-short-text.md` |
| `long-document` | Units contain several themes, exceed useful context, or require section-to-document interpretation | `references/long-document.md` |
| `mixed` | Both conditions occur | Read both route references and preserve route-specific evidence |

For every modeling or comparison task, read
`references/semantic-review-and-cumulative-tuning.md` completely. Also read:

- `references/diversity-evaluation.md` for diagnostics and eligible comparison;
- `references/study-contract-and-reporting.md` for assurance-specific artifacts;
- `references/bertopic-implementation.md` when fitting or reviewing code.

Read conditionally:

- `references/corpus-theme-reconnaissance.md` for research reconnaissance and
  the complete publication preview;
- `references/research-grade-visualization.md` when figures are requested or
  required;
- `references/lexicon-management-and-iteration.md` for synonyms, stopwords,
  custom terms, or domain dictionaries;
- `references/iteration-and-lineage.md` for later snapshots or new corpora;
- `references/scalable-corpus-reading.md` for bounded extraction from corpora
  too large for direct reading;
- `references/academic-evidence.md` and `references/web-research-protocol.md`
  when claims depend on current papers, packages, or model availability.

## Establish the baseline champion

1. Preserve raw text, stable unit IDs, parent-document IDs, duplicate/source
   groups, and separate embedding, lexical, and display text.
2. Complete the evidence gate required by the assurance level:
   - exploratory: profile the corpus and inspect enough original evidence to
     identify obvious themes, artifacts, and limitations; do not impose a second approval ritual;
   - research: create a concise theme map; use a full reading ledger only when
     the claim depends on progressive coverage;
   - publication/release: follow
     `references/publication-release-workflow.md` and require explicit preview
     approval before fitting.
3. Copy `assets/study-contract.json`, select the assurance level, define the
   route, claim scope, analysis unit, smallest meaningful theme, grouping
   rules, calibration plan, and provisional-setting provenance.
4. Fit one transparent baseline when authorized. Export assignments,
   probabilities when available, topic words, representative/random/boundary
   units, topic embeddings, and Topic `-1` evidence.
5. Register it as `baseline_candidate_id` and `current_champion_id` in
   `tuning-trace.json`.

Do not invent operational numbers. Do not import parameters, thresholds,
candidate counts, seed counts, sample
sizes, reviewer counts, or metric weights from another paper or corpus. When
target-corpus evidence is unavailable, record `pending_local_calibration`, the unresolved estimand,
candidate-generation rule, calibration evidence, and stop rule.

## Run cumulative stages

Carry exactly one current champion through this main-stage order:

```text
analysis_unit
→ embedding
→ umap
→ hdbscan_min_cluster_size
→ hdbscan_min_samples
→ hdbscan_selection_method
→ representation
→ taxonomy
```

At each stage, change one parameter family:

1. Load the current champion.
2. Generate challengers from unresolved evidence.
3. Set every challenger’s `champion_parent_id` to that current champion.
4. Change only the stage’s parameter family.
5. Reuse compatible cached embeddings, neighbor graphs, or assignments.
6. Calculate algorithmic diagnostics.
7. Build the original-text review queue.
8. Read the evidence and record the semantic decision.
9. Promote exactly one eligible challenger, retain the champion, or defer.
10. Carry only `champion_after` into the next stage.

A rejected challenger never becomes the next champion parent. Record a
substantive `skip_reason` when evidence does not justify a stage experiment.

For `representation`, prove that assignment and topic-identity fingerprints are
unchanged. If assignments change, reclassify the candidate as structural.

Validate the chain:

```text
python scripts/validate_tuning_trace.py <tuning-trace.json> <experiment-registry.csv>
```

## Read original text before deciding meaning

Use `evaluate_diversity.py`, lexical overlap, semantic nearest neighbors,
confidence, Topic `-1`, and stability failures to create a review queue. Never
let them emit a merge, split, label, artifact classification, or promotion
verdict.

Build a portable queue:

```text
python scripts/build_semantic_review_queue.py \
  --topics <topics.json> \
  --units <units.csv> \
  --assignments <assignments.csv> \
  --scorecard <scorecard.json> \
  --candidate-id <candidate-id> \
  --route <network-short|long-document|mixed> \
  --output <semantic-review-queue.json>
```

For every topic card, read the registered original/display text and write:

- object;
- claim, action, or function;
- context;
- stance or perspective;
- definition and label;
- inclusion and exclusion rules;
- counter-evidence;
- boundary clarity and artifact status.

For every queued pair, compare both sides’ original evidence and choose only
after writing the meaning difference. Allowed relationships are `distinct`,
`overlapping`, `parent_child`, `merge_candidate`, `split_signal`, `artifact`,
and `uncertain`.

High cosine can still mean different objects, stages, or functions. Low lexical
overlap can still express the same meaning. When algorithmic and semantic
evidence disagree, retain the champion and resolve the meaning uncertainty.

## Compare eligible candidates

Apply this order:

```text
semantic eligibility
→ locally justified hard constraints
→ Pareto or champion-relative diagnostics
→ original-text promotion decision
```

Run Pareto only when several semantically eligible research/publication
candidates remain:

```text
python scripts/select_pareto.py \
  --input <candidate-metrics.csv> \
  --output <pareto.json> \
  --require-field semantic_review_status=pass \
  --champion-id <current-champion> \
  --maximize <registered-objective> \
  --constraint <registered-constraint>
```

Pareto output and champion deltas do not promote a model. Retain the simpler
champion in an empirical tie unless original-text evidence supports the change.

## Confirm bounded interactions

After the main path, inspect unresolved diagnostics for parameter interactions.
Run `interaction_confirmation` only when a named diagnostic trigger exists.

- Name the allowed parameter families.
- Generate candidates that answer the unresolved interaction.
- State a bounded candidate-generation and stop rule.
- Preserve the pre-interaction champion as the rollback point.
- Review original text again before promotion.

Never turn this step into a Cartesian grid, exhaustive sweep, or reusable
multi-family search.

## Validate finalists

- Recheck meaning, missing themes, artifacts, and Topic `-1`.
- Use group-safe resampling: short-text dependence groups stay together;
  long-document chunks stay with their parent document.
- For long documents, interpret chunk support at parent-document level and
  distinguish one-document repetition from cross-document support.
- Compare matched topic counts, declared bands, or equivalent hierarchy levels.
- Preserve the strongest counter-evidence and unresolved limitations.

## Deliver by assurance level

Always validate the study bundle:

```text
python scripts/validate_study_bundle.py <study-bundle-directory>
```

For publication/release, also validate the full reconnaissance and visualization
bundles:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
python scripts/validate_visualization_bundle.py <study-bundle-directory>
```

Lead the decision report with:

1. assurance level, route, and final champion;
2. stage promotions, retentions, deferrals, and rollbacks;
3. substantive meaning changes and unresolved boundaries;
4. bounded interaction result;
5. finalist stability, coverage, and counter-evidence;
6. supporting numerical diagnostics;
7. only the artifacts and figures required by the selected assurance level.

Do not leave empty publication-only headings in exploratory or research reports.
Do not describe a representation refresh as a structural model. Do not claim
that topic count, coherence, diversity, similarity, or outlier rate proves that
the topic meanings are correct.
