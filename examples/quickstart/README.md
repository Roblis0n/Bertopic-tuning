# Semantic review queue quickstart

This offline example builds a traceable review queue from a small, real
semantic-review test fixture. It does not fit a model, download an embedding,
or make a semantic judgment. The scorecard only determines which original
texts must be read together.

## Run it

From this directory:

```text
python ../../scripts/build_semantic_review_queue.py \
  --topics inputs/topics.json \
  --units inputs/units.csv \
  --assignments inputs/assignments.csv \
  --scorecard inputs/scorecard.json \
  --candidate-id candidate-semantic-test \
  --route network-short \
  --output output/semantic-review-queue.json
```

The command writes `output/semantic-review-queue.json`. Its output is
deterministic for these inputs. To check the fresh output against the committed
result, run:

```text
python -X utf8 -c "from pathlib import Path; import sys; sys.exit(Path('output/semantic-review-queue.json').read_bytes() != Path('expected/semantic-review-queue.json').read_bytes())"
```

An exit status of `0` means the files are byte-identical.

## What to inspect

`expected/semantic-review-queue.json` contains three topic review cards, two
diagnostic-triggered pair queues, and one Topic `-1` coverage review. It keeps
the original Chinese text and records `semantic_verdict_produced: false`:
reviewers must still determine topic meaning, boundaries, artifacts, and any
relationship between the queued topics.

The four input files are copied from the semantic queue's existing test
fixture, split only into the command-line file formats the script requires.
