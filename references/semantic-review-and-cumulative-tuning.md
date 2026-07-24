# Semantic Review and Cumulative Tuning

Use this reference for every BERTopic model comparison or tuning task.
Algorithms organize evidence; Codex or a named human reviewer reads original
text and decides meaning. Carry one current champion through controlled stages.

## Contents

1. Decision boundary
2. Champion identities
3. Main-stage order
4. One-family scientific differences
5. Stage recipe
6. Semantic evidence queue
7. Topic and pair decisions
8. Promotion and rollback
9. Bounded interaction confirmation
10. Route-specific evidence
11. Finalist validation
12. Artifact links

## 1. Decision boundary

Algorithmic diagnostics may:

- rank topics and pairs for reading;
- expose instability, overlap, outliers, leakage, or missing-theme risk;
- compare eligible candidates under declared constraints;
- identify an unresolved parameter interaction.

They may not decide that two topics have the same meaning, assign a substantive
label, merge or split a topic, classify a topic as an artifact, or promote a
challenger. Original text is authoritative.

Use this order:

```text
diagnostic signals
→ traceable original-text queue
→ semantic topic and pair decisions
→ semantic eligibility
→ quantitative trade-off comparison
→ promote, retain, or defer
```

## 2. Champion identities

Record one immutable `baseline_candidate_id` and one mutable
`current_champion_id`. Every main-stage challenger records:

- `stage_id`;
- `champion_parent_id`;
- `changed_parameter_family`;
- complete scientific configuration;
- configuration-diff artifact;
- diagnostic artifacts;
- semantic-review status.

The champion parent is always the champion at the start of that stage. A
rejected or deferred challenger cannot appear as the next stage’s parent.

## 3. Main-stage order

Use this order unless a stage has a recorded evidence-based `skip_reason`:

1. `analysis_unit`
2. `embedding`
3. `umap`
4. `hdbscan_min_cluster_size`
5. `hdbscan_min_samples`
6. `hdbscan_selection_method`
7. `representation`
8. `taxonomy`

`analysis_unit` comes first because changing segmentation changes the modeled
corpus. `representation` comes after structural stages and requires identical
assignments. `taxonomy` changes only reviewed topic relations.

## 4. One-family scientific differences

Ignore candidate IDs, timestamps, seeds, resample IDs, statuses, and artifact
paths when checking a scientific difference.

| Stage | Permitted scientific difference |
|---|---|
| `analysis_unit` | analysis-unit or segmentation configuration and its corpus fingerprint |
| `embedding` | encoder, revision, instruction, pooling, or truncation |
| `umap` | UMAP configuration |
| `hdbscan_min_cluster_size` | `min_cluster_size` |
| `hdbscan_min_samples` | `min_samples` |
| `hdbscan_selection_method` | `cluster_selection_method` |
| `representation` | vectorizer, c-TF-IDF, representation method, or lexicon snapshot; assignment fingerprint must match |
| `taxonomy` | reviewed taxonomy snapshot and merge/split mapping |

If a main-stage challenger changes more than one family, reject it or move the
hypothesis to `interaction_confirmation`.

## 5. Stage recipe

```python
champion = baseline
for stage in main_stages:
    challengers = generate_stage_candidates(
        champion,
        stage,
        unresolved_evidence,
    )
    diagnostics = evaluate_against_champion(champion, challengers)
    review_queue = build_semantic_review_queue(
        champion,
        challengers,
        diagnostics,
    )
    semantic_decision = review_original_text(review_queue)
    champion = promote_or_retain(
        champion,
        challengers,
        semantic_decision,
    )

champion = confirm_bounded_interactions(
    champion,
    unresolved_interactions,
)
```

`review_original_text()` is a Codex/human reasoning step, not an embedding
function. Candidate generation follows unresolved evidence and a stop rule; it
does not use a universal count.

Reuse only scientifically compatible caches:

- reuse embeddings when the encoder and input unit are unchanged;
- reuse neighbor graphs only when their inputs and relevant settings match;
- reuse assignments for representation comparisons;
- never reuse a cache merely because the filename matches.

## 6. Semantic evidence queue

Build the queue with `scripts/build_semantic_review_queue.py`. Resolve every
evidence ID to a registered unit and include its original/display text.

For each topic, combine already registered:

- representative evidence;
- random evidence;
- boundary evidence;
- source- or parent-diverse evidence;
- nearest-pair evidence;
- Topic `-1` or missing-theme evidence.

Keep cosine, RBO, lexical overlap, confidence, and distances inside
`algorithmic_signals`. The queue builder must set their role to
`review_trigger_only` and must not include a `relationship` verdict.

Do not impose a universal sample count. The study contract supplies evidence
IDs, target precision, and the semantic stop rule.

## 7. Topic and pair decisions

For every topic card, read the evidence and record:

- substantive object;
- claim, action, or function;
- context;
- stance or perspective;
- concise label and definition;
- inclusion and exclusion rules;
- counter-evidence;
- `boundary_clarity`: `clear`, `mixed`, or `uncertain`;
- `artifact_status`: `substantive`, `artifact`, or `uncertain`.

For each queued pair, compare both sides before selecting:

- `distinct`;
- `overlapping`;
- `parent_child`;
- `merge_candidate`;
- `split_signal`;
- `artifact`;
- `uncertain`.

High similarity is compatible with distinct meanings, such as application
eligibility versus post-receipt usage restrictions. Low word overlap is
compatible with the same meaning, such as different descriptions of
qualification review.

## 8. Promotion and rollback

For `research` and `publication_release`, promote only when:

- semantic review status is `pass`;
- meaning distinctiveness is not `worse`;
- no unresolved semantic decision remains;
- locally justified hard constraints pass;
- the change answers the stage hypothesis.

For `exploratory`, a compact review may support a provisional promotion, but the
result remains `exploratory_only`.

Use `promote` to set the challenger as `champion_after`. Use `retain` or `defer`
to keep `champion_after` equal to `champion_before`. The latter is the rollback:
later stages start from the retained champion, not from the rejected
configuration.

Pareto selection is optional when fewer than two eligible candidates remain.
When used, it describes trade-offs and never produces the promotion decision.

## 9. Bounded interaction confirmation

Run `interaction_confirmation` only after the main path and only when a
diagnostic names a plausible interaction.

Record:

- nonblank `diagnostic_triggers`;
- named `allowed_parameter_families`;
- a bounded `candidate_generation_rule`;
- candidate IDs;
- semantic-review artifact;
- promote/retain/defer decision;
- rollback reason.

The rule must answer the unresolved diagnostic. Never use a Cartesian grid,
full grid, exhaustive sweep, or all combinations. Preserve the pre-interaction
champion unless original-text evidence supports promotion.

## 10. Route-specific evidence

For `network-short`, expose duplicate, source, account, thread, and time groups
when registered. Warn when all semantic evidence comes from one dependence
group. Keep dependent units together in finalist resampling.

For `long-document`, link every reviewed chunk to its parent document and
offsets. Distinguish many chunks from one parent from support across independent
parents. Run the `analysis_unit` stage before embedding and resample finalists
by parent document.

For `mixed`, retain both route subsets and apply both evidence rules before
aligning taxonomies.

## 11. Finalist validation

On the final champion and any remaining eligible finalist:

- re-read unclear and counter-evidence units;
- inspect Topic `-1` for missing themes and artifacts;
- evaluate grouped stability at the correct dependence unit;
- check reference-theme coverage without treating purposive evidence as
  prevalence;
- compare at matched topic counts or equivalent hierarchy levels;
- record the strongest contradictory result and unresolved limitation.

## 12. Artifact links

- `assets/tuning-trace.json` records the champion chain.
- `assets/semantic-review.json` records meaning decisions.
- `experiment-registry.csv` stores complete candidate configurations and
  champion parentage.
- `candidate-metrics.csv` stores diagnostics and semantic eligibility.
- `selected-model.json` binds the final choice to the trace and review.

Validate:

```text
python scripts/validate_tuning_trace.py <tuning-trace.json> <experiment-registry.csv>
python scripts/validate_study_bundle.py <study-bundle-directory>
```
