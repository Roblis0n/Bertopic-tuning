# BERTopic Tuning

A semantic-first Codex skill for BERTopic modeling, topic interpretation, and
research delivery across short network text, long documents, and mixed corpora.

The skill now answers three questions in order:

1. How strong a claim will this result support?
2. What do the topics mean when their original texts are read?
3. Does one controlled change improve the current champion?

It does not treat cosine similarity, lexical overlap, coherence, topic count,
Topic Diversity, or Topic `-1` rate as a substitute for understanding meaning.

## What changed

- Audit intensity is selected by `exploratory`, `research`, or
  `publication_release` assurance.
- Algorithms create review queues; Codex or a named human reviewer reads
  original text and decides topic identity and boundaries.
- Tuning carries one current champion forward.
- Each main stage changes one parameter family.
- Rejected changes roll back automatically because the retained champion
  remains the next parent.
- Multi-family checks are confined to a final, evidence-triggered,
  bounded interaction confirmation.
- The full reconnaissance, lineage, and visualization bundle remains strict for
  publication/release instead of blocking every trial.

## Assurance levels

| Level | Intended use | Required result |
|---|---|---|
| `exploratory` | Smoke test, feasibility check, early tuning | Provisional baseline or champion, compact semantic review, limited claims |
| `research` | Defensible model comparison and substantive interpretation | Semantically reviewed stage winners/finalists, grouped stability and coverage evidence |
| `publication_release` | Submission, public release, production taxonomy | Full preview approval, audit, lineage, visualization, hashes, and reproducibility bundle |

An explicit modeling request authorizes exploratory and ordinary research work.
Publication/release retains the separate preview and approval gate.

Existing bundles without `assurance_level` remain legacy-strict until migrated.

## What is automatic

The included scripts can:

- resolve assurance-specific artifact requirements;
- compute lexical and semantic diagnostic scorecards;
- identify suspicious topics and topic pairs;
- build a traceable original-text review queue;
- filter semantically ineligible Pareto candidates;
- calculate objective deltas from the current champion;
- validate single-family candidate differences;
- validate promotion, retention, deferral, and rollback;
- enforce bounded interaction confirmation;
- plan and validate assurance-aware visualization bundles;
- validate final study-bundle links.

Automation never emits a substantive merge, split, label, artifact, or model
promotion verdict.

## What requires reading

Codex or a named human reviewer reads the original/display text and records:

- topic object, function, context, and perspective;
- definition, label, inclusion rules, and exclusion rules;
- counter-evidence and boundary clarity;
- pair relationships;
- missing-theme and artifact judgments;
- the reason a challenger should replace or not replace the champion.

The canonical decision artifact is `semantic-review.json`.

## Champion path

```text
baseline
→ analysis_unit
→ embedding
→ umap
→ hdbscan_min_cluster_size
→ hdbscan_min_samples
→ hdbscan_selection_method
→ representation
→ taxonomy
→ bounded interaction confirmation
```

At every main stage:

```text
current champion
→ one-family challengers
→ diagnostic triage
→ original-text semantic review
→ promote one, retain, or defer
→ next-stage champion
```

`tuning-trace.json` records the complete chain. Representation changes must
preserve assignment and topic-identity fingerprints.

## Main assets

| Artifact | Purpose |
|---|---|
| `assets/study-contract.json` | Assurance, claim, route, calibration, semantic, and tuning policy |
| `assets/tuning-trace.json` | Stage order, parentage, decisions, champion, and interactions |
| `assets/semantic-review.json` | Original-text topic, pair, and coverage decisions |
| `assets/experiment-registry.csv` | Complete candidate configurations and stage identity |
| `assets/candidate-metrics.csv` | Diagnostics, semantic eligibility, and champion comparison |
| `assets/selected-model.json` | Final champion and evidence links |
| `assets/decision-report.md` | Assurance-aware result narrative |

Compatibility audit tables remain available for publication/release.

## Core commands

Build a semantic review queue:

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

Evaluate diagnostic diversity:

```text
python scripts/evaluate_diversity.py \
  --input <topics.json> \
  --output <scorecard.json> \
  --top-k <registered-k> \
  --rbo-p <registered-p>
```

Compare eligible candidates:

```text
python scripts/select_pareto.py \
  --input <candidate-metrics.csv> \
  --output <pareto.json> \
  --require-field semantic_review_status=pass \
  --champion-id <candidate-id> \
  --maximize <registered-objective>
```

When lexical resources are enabled, compile and validate the registered bundle:

```text
python scripts/build_lexicon_bundle.py \
  --config <lexicon-config.json> \
  --output <lexicon-manifest.json>
python scripts/evaluate_representation_update.py <registered-arguments>
```

Validate the champion chain and study bundle:

```text
python scripts/validate_tuning_trace.py <tuning-trace.json> <experiment-registry.csv>
python scripts/validate_study_bundle.py <study-bundle-directory>
```

Publication/release also runs:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
python scripts/validate_visualization_bundle.py <study-bundle-directory>
```

## References

Always read:

- `references/semantic-review-and-cumulative-tuning.md`;
- the selected route reference;
- `references/diversity-evaluation.md`;
- `references/study-contract-and-reporting.md`.

Read `references/publication-release-workflow.md` only for
`publication_release`.

## Validation

Run:

```text
python -X utf8 -B -m unittest discover -s scripts/tests -v
```

The test suite covers legacy strict behavior, all three assurance levels,
semantic queues, champion chains, selection integrity, route evidence,
visualization integrity, lexicon iteration, reconnaissance, and documentation
contracts.
