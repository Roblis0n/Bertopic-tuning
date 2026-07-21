---
name: bertopic-tuning
description: Use when a user requests BERTopic tuning, 主题建模调参, topic-diversity optimization, synonym or stopword management, custom/domain dictionaries, lexical representation iteration, short web or social-text modeling, long-document topic discovery, model comparison, topic stability, topic lineage, new-corpus updates, Chinese-corpus analysis, or academically reproducible BERTopic reporting.
---

# BERTopic Tuning

## Core principle

Optimize **effective thematic diversity**, not raw topic count, simple Topic Diversity, or outlier rate. Treat diversity as a vector of lexical distinctiveness, semantic distinctiveness, theme coverage, stability, and human interpretability. Keep coherence as a floor and outlier behavior as a diagnostic guardrail.

Translate papers into mechanisms and testable hypotheses. Never copy a paper's hyperparameters, thresholds, sample sizes, or metric weights into a new corpus unless reproducing that paper.

## Non-negotiable rules

1. Route the corpus before proposing a model.
2. Derive numerical choices from the research question, corpus profile, smallest meaningful theme, tokenizer/model limits, validation labels, historical distributions, or a pre-registered sensitivity design.
3. Separate four layers: structure, representation, taxonomy, and governance.
4. Do not claim that `update_topics()`, MMR, or label generation changed the clusters.
5. Do not force long multi-topic documents into one input unit.
6. Do not use random chunk-level resampling when chunks share a parent document.
7. Do not select a model with one scalar metric. Use explicit constraints plus a Pareto frontier.
8. Do not optimize away `-1`. Inspect it for missing themes, source artifacts and genuine noise after evaluating the taxonomy.
9. Compare diversity at matched topic counts, a declared topic-count band, or equivalent hierarchy levels.
10. Preserve raw text, corpus fingerprints, failed candidates, representative units, audit decisions and topic lineage.
11. Do not invent operational numbers. This includes fixed/default grids, ratios around a substantive support value, universal seed/resample/reviewer/sample counts, similarity cutoffs, topic-count bands and metric weights. If target-corpus evidence is unavailable, record `pending_local_calibration` and specify the estimand, calibration data, candidate-generation rule and stop rule.
12. Do not turn named models from papers, leaderboards or examples into a mandatory shortlist. Generate candidates from the task, language, context length, license, deployment and compute requirements; verify current availability when it matters.
13. Do not fit a baseline or any BERTopic candidate before a complete full-corpus theme reconnaissance has been shown to the user and `modeling-authorization.json` records `approved_for_modeling`.

## Route the corpus

Choose from content structure, not source label alone.

| Route | Observable condition | Required reference |
|---|---|---|
| `network-short` | Units are short, sparse, conversational, platform-shaped, highly duplicated or context-dependent | Read `references/network-short-text.md` completely |
| `long-document` | Units can contain several themes, exceed useful embedding context, or require section-to-document interpretation | Read `references/long-document.md` completely |
| `mixed` | The corpus contains both conditions | Partition by analysis unit, apply both routes, then align taxonomies only if the research question requires a shared space |

A long online article follows the long-document route. A concise formal response may follow the short-text route. If one corpus contains coherent natural sections, prefer the long-document route even when total length is moderate.

Always read:

- `references/corpus-theme-reconnaissance.md` for the mandatory pre-model preview and authorization gate;
- `references/diversity-evaluation.md` for metrics, calibration and selection;
- `references/study-contract-and-reporting.md` for artifacts and reporting;
- `references/academic-evidence.md` before making literature-backed claims.

Read when needed:

- `references/iteration-and-lineage.md` for new data, retraining, merge/split or temporal comparison;
- `references/bertopic-implementation.md` when implementing or reviewing Python/BERTopic code;
- `references/lexicon-management-and-iteration.md` when adding synonyms, stopwords, custom/domain terms or iterating lexical representation from model results;
- `references/web-research-protocol.md` when a decision depends on current papers, package/API behavior, encoder availability, a cited source, or an evidence gap.

## Required workflow

Track and finish this sequence. The full-corpus reconnaissance gate is the required intentional pause: show the preview, stop for user direction, and resume only after explicit modeling authorization. Outside that gate, do not stop after a parameter suggestion when the available data and tools permit execution.

### 1. Inspect and fingerprint

- Inspect the corpus, schema, current model, embeddings, topic exports and prior experiments.
- Preserve raw text and create separate embedding, lexical and display views.
- Record corpus size, length distribution, duplicate groups, languages, sources, dates, parent-document structure and missing fields.
- Hash the data snapshot and preprocessing configuration.
- State whether BERTopic's hard primary assignment is compatible with the research claim. If mixed membership or covariate inference is essential, retain BERTopic for discovery only and add a suitable robustness model.

### 2. Conduct full-corpus theme reconnaissance and pause

- Copy `assets/theme-reconnaissance.json`, `theme-candidate-audit.csv` and `modeling-authorization.json` into the study workspace.
- Restate the user's theme as a `coverage_and_interpretation_anchor`; keep emergent themes open unless the user explicitly changes the analytical scope.
- Account for every source unit. Directly review each eligible unit or inherit interpretation only from a verified exact duplicate. A sample, truncated scan or near-duplicate inheritance is not full-corpus coverage.
- For long or mixed corpora, cover every eligible parent document using provisional reading sections without freezing the later chunking policy.
- Produce an evidence-linked candidate hierarchy; classify each candidate as `mainline`, `supporting`, `contextual`, `emergent`, `artifact` or `uncertain`; and report artifact exclusions, unresolved boundaries, and coarse/fine lower-point-upper topic-count estimates.
- Label the count estimate `pre_model_hypothesis_not_target_k`. Never turn it into a forced BERTopic topic count or clustering target.
- Present the preview, set `gate_status: awaiting_user_direction` and `modeling_may_start: false`, then stop before embeddings or model fitting.

Validate the preview:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory>
```

After the user accepts, rejects, merges, splits, defers or reframes candidates, record every disposition and the user's instruction. Resume only when this passes:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
```

Read `references/corpus-theme-reconnaissance.md` for the accounting equations, route-specific review method, reporting order and invalidation rules.

### 3. Create the study contract

Copy `assets/study-contract.json` into the analysis workspace and complete it before fitting candidates. Define:

- research question and inferential scope;
- route and analysis unit;
- smallest substantively meaningful theme and its evidence basis;
- diversity dimensions and coherence/labelability floors;
- group-aware validation and bootstrap units;
- calibration method for every threshold;
- operational topic-count band or hierarchy level;
- model-selection policy (`pareto`);
- outlier role (`diagnostic_guardrail_only`).

Retain the mandatory `pre_model_reconnaissance` policy, link the approved reconnaissance and authorization artifacts, and store the approval's `authorization_id`. If the corpus fingerprint, route, research question or resolved preview changes, invalidate the old authorization before fitting.

If a value cannot yet be justified, record `pending_local_calibration` plus the calibration experiment that will estimate it. Do not replace it with a paper's number, a conventional default, a fixed multiplier of a local quantity or an invented pilot grid.

When academic claims, current software behavior or model availability matter, run the conditional search protocol before freezing the contract. Log verified sources, mechanisms, transfer conditions and limitations in `evidence-log.csv`.

### 4. Establish an auditable baseline

- Cache embeddings so structural candidates use identical vectors when the encoder is fixed.
- Fit a transparent baseline and export assignments, probabilities when available, topic words, representative/random/boundary units and topic embeddings.
- Keep the evaluation corpus and sampling rules fixed across candidates.
- Register every candidate, including failures, in `experiment-registry.csv`, and link its approved `authorization_id`.

### 5. Run the structural loop

Change assignments only through structural experiments:

1. Generate embedding candidates from corpus and operating requirements, then compare them on domain same-topic, confusing-different and clearly-different pairs.
2. Vary UMAP hypotheses from local-niche preservation to global-structure preservation; generate numerical candidates from the empirical neighbor graph and unresolved regions of the sensitivity curve.
3. Anchor HDBSCAN minimum support to the declared smallest meaningful theme. Use an adaptive pilot: add a candidate only where theme survival, fragmentation or merging remains unresolved, and stop when the pre-registered decision boundary or uncertainty target is resolved. Do not expand the anchor into a fixed ratio grid.
4. Perturb `min_samples` independently from `min_cluster_size`, again using an explicit candidate-generation and stopping rule rather than a reusable grid.
5. Compare `eom` and `leaf` as granularity hypotheses, not defaults.
6. Run seed and group-aware resample checks on finalists; determine repetitions from the target precision, stability plateau and compute stop rule rather than a universal count.

Keep representation fixed during this loop so structural effects remain identifiable.

### 6. Run the representation loop

Freeze assignments, then compare tokenization, domain dictionaries, phrase vocabulary, document-frequency pruning, c-TF-IDF variants, frequent-term suppression, MMR/KeyBERTInspired and grounded labels. Use `update_topics()` for this layer. Recompute representation metrics, but retain the structural scorecard unchanged.

For user-managed lexical resources:

1. Copy `assets/lexicon-config.json`, `synonyms.csv`, `stopwords.csv` and `custom-terms.csv` into the study workspace.
2. Record the tokenizer name and revision, keep source tables inside the lexicon bundle directory, then compile and validate them with `scripts/build_lexicon_bundle.py`; do not apply a bundle containing conflicts.
3. Apply custom phrase protection, tokenization, synonym canonicalization and stopword filtering to `lexical_text` only.
4. Refresh the representation with `update_topics()` and prove that unit assignments plus permanent and local topic IDs did not change.
5. Run `scripts/evaluate_representation_update.py`, review every generated lexicon candidate, and record accepted, rejected or deferred decisions.
6. Create a new content-addressed lexicon and representation snapshot only after the audit. Do not use generic `v1`/`v2` names.

Treat custom terms as tokenizer/domain-phrase instructions. Do not pass them as a closed `CountVectorizer(vocabulary=...)` allowlist unless the study explicitly requires and validates a closed vocabulary as a separate analytical policy.

### 7. Run the taxonomy loop

- Generate nearest-topic pairs from representative-unit topic embeddings and ranked-word overlap.
- Audit the most similar pairs before merging.
- Prefer post-hoc, evidence-backed agglomeration over coarsening the entire clustering merely to reduce topic count.
- Split a broad topic only when subthemes are distinct, recur across resamples and admit non-overlapping inclusion/exclusion rules.
- Evaluate diversity and coherence again at each intended hierarchy level.

### 8. Evaluate and select

Create one scorecard per candidate using `references/diversity-evaluation.md`. Include TD as a descriptive screen, rank-aware lexical overlap, nearest-topic semantic similarity, theme coverage, stability, coherence and labelability floors, group leakage checks, and outlier fraction as a reported guardrail.

Run:

```text
python scripts/evaluate_diversity.py --input <topics.json> --output <scorecard.json> --top-k <registered-k> --rbo-p <registered-p> [--semantic-redundancy-threshold <calibrated-value>] [--lexicon-manifest <frozen-manifest.json>]
```

Select non-dominated candidates with declared objectives and constraints:

```text
python scripts/select_pareto.py --input <candidate-metrics.csv> --output <pareto.json> --maximize <metric> --maximize <metric> --constraint <metric>=<calibrated-floor>
```

Inspect every finalist's representative, random and boundary units. Record why the chosen Pareto point fits the research purpose; do not automatically choose the model with the most topics.

### 9. Iterate without losing history

- Distinguish representation refresh, structural refit, taxonomy edit and new-data mapping.
- Keep lexicon bundle lineage separate from topic lineage. A synonym, stopword or custom-term edit creates a representation candidate, not a new structural model.
- Freeze permanent `topic_uid` values outside BERTopic's local integer IDs.
- Use a frozen reference encoder or shared anchor units when embedding spaces change.
- Calibrate alignment thresholds locally and run:

```text
python scripts/align_snapshots.py --old <old-topics.json> --new <new-topics.json> --thresholds <calibrated-thresholds.json> [--keyword-rbo-p <registered-p-when-keyword-gate-is-used>] [--lexicon-manifest <frozen-manifest.json>] --output <alignment.json>
```

- Treat one-to-many and many-to-one results as split/merge candidates requiring evidence and human review.
- For temporal analysis, prefer one global taxonomy plus topics-over-time. Do not compare independently fitted period-specific topic numbers.

### 10. Complete the research bundle

Populate all core templates in `assets/`: corpus profile, theme reconnaissance, theme-candidate audit, modeling authorization, study contract, experiment registry, candidate metrics, selected-model decision, topic catalog, unit audit, nearest-topic pair audit, missing-theme audit, lineage, evidence log and decision report. When lexical resources are enabled, also populate the lexicon source, candidate-audit, representation-iteration and lexicon-lineage artifacts.

Validate before claiming completion:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
python scripts/validate_study_bundle.py <study-bundle-directory>
python -m unittest discover -s scripts/tests -v
```

Fix every validation error. A header-only template, uncited decision, uncalibrated threshold or missing lineage decision is incomplete.

## Output contract

Lead with the selected route and substantive model decision. Report:

1. the approved pre-model reconnaissance, full-corpus coverage accounting, user direction and authorization ID;
2. preview-versus-model confirmations, merges, splits, absences and emergent themes;
3. what changed and which layer changed;
4. which diversity dimensions improved, deteriorated or remain uncertain;
5. whether comparisons used matched granularity;
6. which thresholds were locally calibrated and how;
7. strongest counter-evidence and failure modes;
8. topic merges, splits, new themes and retirements;
9. lexicon bundle changes, frozen-assignment evidence and unresolved term decisions when enabled;
10. reproducible artifact paths and validation results.

Do not present paper-derived numbers as universal recommendations. Do not describe a representation-only refresh as a new structural model. Do not claim that low outlier rate proves high-quality topic diversity.
