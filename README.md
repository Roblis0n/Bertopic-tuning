# BERTopic Tuning

[![CI](https://github.com/Roblis0n/Bertopic-tuning/actions/workflows/validate.yml/badge.svg)](https://github.com/Roblis0n/Bertopic-tuning/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/Roblis0n/Bertopic-tuning?display_name=tag&sort=semver)](https://github.com/Roblis0n/Bertopic-tuning/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Turn short text, long documents, or mixed corpora into an auditable BERTopic
champion whose topic meanings are grounded in original-text review.

Unlike metric-only tuning, this Codex skill uses similarity, diversity,
coherence, stability, and Topic `-1` diagnostics only to decide what deserves
reading; a recorded semantic review decides topic identity, boundaries, and
whether one controlled challenger replaces the current champion.

## Install

Requirements: [Codex with skills support](https://developers.openai.com/codex/skills/),
Git, and Python 3 for the bundled offline tools. Choose one scope below. Each
command works unchanged in PowerShell, Command Prompt, and POSIX shells.

Install for your user account so the skill is available in every repository:

```text
python -c "import pathlib, subprocess; p=pathlib.Path.home()/'.agents'/'skills'/'bertopic-tuning'; p.parent.mkdir(parents=True, exist_ok=True); subprocess.run(['git','clone','https://github.com/Roblis0n/Bertopic-tuning.git',str(p)], check=True)"
```

Or install only in the current repository:

```text
python -c "import pathlib, subprocess; p=pathlib.Path('.agents/skills/bertopic-tuning'); p.parent.mkdir(parents=True, exist_ok=True); subprocess.run(['git','clone','https://github.com/Roblis0n/Bertopic-tuning.git',str(p)], check=True)"
```

Codex detects skill changes automatically; restart it only if the skill does
not appear.

The cloned repository root is the installable skill source, not a standalone
plugin root. To build the standalone plugin and deterministic release archive,
choose new output paths outside this repository:

```text
python -X utf8 -B scripts/build_plugin.py --output <outside-repository-path>/bertopic-tuning --archive <outside-repository-path>/bertopic-tuning.zip --codex-home <codex-home-path>
```

The builder reads the policy and every source file from the Git index, copies
only the explicit whitelist, and projects the indexed root `SKILL.md`
byte-for-byte into `skills/bertopic-tuning/SKILL.md`. It rejects unmerged or
symlink index entries, unsafe paths, existing targets, incorrect plugin names,
and destinations inside the source tree. The vendored plugin contract always
runs. `--codex-home` additionally runs both official Codex validators before
publishing either output; CI exercises the vendored contract and deterministic
directory/ZIP build on Linux and Windows.

## Invoke

Copy this prompt and replace the angle-bracketed values:

```text
Use $bertopic-tuning to analyze <corpus-path> for <research-question> at the <exploratory|research|publication_release> assurance level. Preserve stable unit and parent-document IDs, choose the route from the corpus structure, read the required original-text evidence, tune one cumulative champion one parameter family at a time, and deliver the required semantic-review, tuning-trace, and study-bundle artifacts with limitations.
```

## Verify it offline

The [executable quickstart](examples/quickstart/README.md) runs without BERTopic,
an embedding download, or network access. From `examples/quickstart`, its build
command writes a deterministic review queue:

```text
python ../../scripts/build_semantic_review_queue.py --topics inputs/topics.json --units inputs/units.csv --assignments inputs/assignments.csv --scorecard inputs/scorecard.json --candidate-id candidate-semantic-test --route network-short --output output/semantic-review-queue.json
```

Verified committed-fixture result:

```text
topic review cards: 3
diagnostic-triggered pair reviews: 2
Topic -1 coverage reviews: 1
semantic verdict produced: false
fresh output vs. committed expected output: byte-identical
```

That final `false` is deliberate: the tool constructs evidence for review; it
does not pretend an algorithm has understood the topics. Follow the quickstart
for the clean-run and byte-comparison commands.

## Modeling contract

The skill now answers three questions in order:

1. How strong a claim will this result support?
2. What do the topics mean when their original texts are read?
3. Does one controlled change improve the current champion?

It does not treat cosine similarity, lexical overlap, coherence, topic count,
Topic Diversity, or Topic `-1` rate as a substitute for understanding meaning.

### What changes by design

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
python scripts/build_semantic_review_queue.py --topics <topics.json> --units <units.csv> --assignments <assignments.csv> --scorecard <scorecard.json> --candidate-id <candidate-id> --route <network-short|long-document|mixed> --output <semantic-review-queue.json>
```

Evaluate diagnostic diversity:

```text
python scripts/evaluate_diversity.py --input <topics.json> --output <scorecard.json> --top-k <registered-k> --rbo-p <registered-p>
```

Compare eligible candidates:

```text
python scripts/select_pareto.py --input <candidate-metrics.csv> --output <pareto.json> --require-field semantic_review_status=pass --champion-id <candidate-id> --maximize <registered-objective>
```

When lexical resources are enabled, compile and validate the registered bundle:

```text
python scripts/build_lexicon_bundle.py --config <lexicon-config.json> --output <lexicon-manifest.json>
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

## Limitations

- This repository supplies a Codex workflow, portable validators, and artifact
  templates; it is not an automatic BERTopic fitting package. The quickstart
  demonstrates semantic-review queue construction, not model fitting.
- Topic identity, boundaries, labels, merges, splits, artifacts, and promotion
  still require review of registered original text. Numerical diagnostics
  cannot establish semantic correctness.
- The skill does not install or pin BERTopic, embeddings, tokenizers, or a
  modeling stack, and it does not provide universal thresholds or parameter
  grids. Those choices must be justified in the target corpus environment.
- Bounded reading can end with documented residual risk or an `interim`
  result. Publication/release claims require the stricter approval and bundle
  checks; validator success establishes contract integrity, not scientific
  truth.

## Companion project

Use [Research Project Builder](https://github.com/Roblis0n/research-project-builder)
as the upstream companion for research framing and project design before
BERTopic modeling. The projects remain separate so neither duplicates the
other's workflow.

## References

Always read:

- [`references/semantic-review-and-cumulative-tuning.md`](references/semantic-review-and-cumulative-tuning.md);
- the selected route reference:
  [`network-short-text.md`](references/network-short-text.md),
  [`long-document.md`](references/long-document.md), or both for `mixed`;
- [`references/diversity-evaluation.md`](references/diversity-evaluation.md);
- [`references/study-contract-and-reporting.md`](references/study-contract-and-reporting.md).

Read
[`references/publication-release-workflow.md`](references/publication-release-workflow.md)
only for `publication_release`.

## Validation

Run:

```text
python -X utf8 -B -m unittest discover -s scripts/tests -v
```

The test suite covers legacy strict behavior, all three assurance levels,
semantic queues, champion chains, selection integrity, route evidence,
visualization integrity, lexicon iteration, reconnaissance, and documentation
contracts. See the [changelog](CHANGELOG.md) for the complete release record.
