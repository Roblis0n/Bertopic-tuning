# Lexicon Management and Representation Iteration

## Contents

- Scope and invariants
- Editable resources
- Compilation and conflict rules
- Token-processing order
- BERTopic integration
- Model-result feedback
- Evaluation and release
- Route-specific checks
- Commands and required outputs

## Scope and invariants

Use this workflow for user-maintained synonym maps, stopword lists and custom or domain-term dictionaries. These resources normally change the lexical representation only.

Keep these views separate:

| View | Lexicon action |
|---|---|
| raw text | never modify |
| embedding text | never modify in a representation refresh |
| lexical text | apply the compiled bundle |
| display text | preserve the readable original |

A completed representation refresh must prove:

- `assignments_unchanged=true` for every stable unit ID;
- the set of local and permanent topic IDs is unchanged;
- the embedding cache and structural scorecard are unchanged;
- only lexical, keyword and label evidence is recomputed.

If a synonym or normalization rule is applied to embedding text, stop this workflow and register a structural candidate. If assignments change, reject the representation refresh and route the candidate to the structural loop.

## Editable resources

Copy these files from `assets/` into the study bundle:

- `lexicon-config.json` declares lexical-only scope, normalization, tokenizer identity and source tables;
- `synonyms.csv` maps one surface variant to one canonical term;
- `stopwords.csv` contains terms proposed for exclusion from topic representation;
- `custom-terms.csv` protects domain entities and multi-character or multi-token phrases;
- `lexicon-candidate-audit.csv` records model-derived candidates and human dispositions;
- `lexicon-lineage.csv` records changes between immutable bundles;
- `representation-iteration.csv` records each frozen-assignment comparison.

Use status values `active`, `proposed`, `rejected` or `retired` in editable source tables. Only `active` rows enter the compiled bundle. Every active row requires a source and reason.

Do not maintain one mutable “latest” list. Compile content-addressed bundles and record `parent_bundle_id`. Never name bundles `v1`, `v2`, `final` or `latest`.

## Compilation and conflict rules

Run the compiler before applying any resource:

```text
python scripts/build_lexicon_bundle.py --config <study>/lexicon-config.json --output <study>/lexicon-manifest.json
```

The compiler:

- reads UTF-8 or UTF-8-with-BOM CSV files;
- requires a non-empty tokenizer name and revision in `lexicon-config.json`;
- rejects absolute paths and source tables outside the lexicon bundle directory;
- canonicalizes row order for a deterministic content hash;
- resolves synonym chains to one final canonical term;
- rejects synonym cycles;
- rejects a variant mapped to more than one canonical term;
- rejects empty active terms and incomplete evidence fields;
- rejects a term that is both a stopword and a protected custom term;
- rejects stopwords that conflict with active synonym variants or canonical terms;
- records raw source-file hashes separately from the canonical bundle hash.

Do not silently choose one side of a conflict. Correct the editable tables and compile again.
Every tokenizer, evaluator and alignment entry point rejects a manifest that is unidentified or contains unresolved conflicts.

## Token-processing order

Use this exact positive recipe:

```text
phrase protection -> tokenization -> synonym canonicalization -> stopword filtering
```

Why the order matters:

- phrase protection prevents a domain expression from being fragmented before review;
- tokenization remains replaceable and corpus-specific;
- synonym canonicalization consolidates validated surface variants;
- stopword filtering evaluates the canonical token rather than leaving a hidden alias behind.

Protect custom terms and synonym variants with longest-match-first scanning. Use a tested language tokenizer for the remaining text. Preserve the canonical-to-display mapping so topic reports remain readable.

## BERTopic integration

Load the compiled bundle and create the lexical tokenizer:

```python
import json
from pathlib import Path

from lexicon_tools import build_count_vectorizer

manifest = json.loads(Path("lexicon-manifest.json").read_text(encoding="utf-8"))
vectorizer = build_count_vectorizer(
    manifest,
    base_tokenizer=domain_tokenizer,
    ngram_range=registered_ngram_range,
    min_df=locally_calibrated_min_df,
)
topic_model.update_topics(lexical_texts, vectorizer_model=vectorizer)
```

Use the same stable-unit order and the assignments exported before the refresh. Export assignments again immediately afterward and compare them byte-for-value through the provided evaluator.
Assignment CSV files require `unit_id` plus `topic_uid` (preferred) or `topic_id`; the chosen topic identifier must match a permanent or local identifier in the topic JSON. The outlier ID `-1` is permitted. When both permanent and local identifiers are exported, both sets must remain unchanged.

Custom terms are phrase and tokenizer instructions, not a closed vocabulary. Do not pass them to `CountVectorizer(vocabulary=...)` by default: a fixed allowlist removes every unlisted corpus term and disables corpus-learned vocabulary filtering. A study that genuinely requires a closed vocabulary must register it as a separate analytical policy and evaluate coverage loss.

## Model-result feedback

Treat model output as evidence for candidates, not as authority to mutate the tables automatically.

Generate review candidates from:

- a term appearing in ranked keywords across several topics;
- an active synonym variant remaining after refresh;
- an active custom term failing to appear as a complete representation term;
- representative, random or boundary units showing false canonicalization;
- source or platform markers dominating several topics;
- a proposed stopword removing a rare but substantive theme distinction.

The evaluator lists every cross-topic diagnostic without applying a universal cutoff. It also reports unresolved variants and missing protected terms. Review context before changing status to `accepted`, `rejected` or `deferred`.

For a synonym candidate, require evidence that the terms are substitutable in the target corpus. Do not merge polysemous terms merely because their embeddings are close.

For a stopword candidate, inspect source, time, subgroup and rare-theme distributions. A frequent word can still define the research question.

For a custom-term candidate, verify that phrase protection improves readable topic terms without creating artificial keyword duplication.

## Evaluation and release

Run:

```text
python scripts/evaluate_representation_update.py \
  --before-topics <baseline-topics.json> \
  --after-topics <candidate-topics.json> \
  --before-assignments <baseline-assignments.csv> \
  --after-assignments <candidate-assignments.csv> \
  --lexicon-manifest <lexicon-manifest.json> \
  --top-k <registered-k> \
  --rbo-p <registered-p> \
  --output <representation-comparison.json> \
  --candidate-output <lexicon-candidate-audit.csv>
```

Compare:

- surface TD and IRBO;
- concept-normalized TD and IRBO under one frozen audit map;
- stopword leakage before and after;
- residual synonym variants;
- protected-term recovery;
- ranked keyword changes by topic;
- representative, random and boundary-unit label fit.

Do not claim that semantic theme coverage or clustering stability improved merely because the keywords improved. Carry the frozen structural scorecard forward unchanged.

Select among eligible representation candidates with explicit constraints and a Pareto frontier. Reject a candidate when assignments changed, topic identity changed, label fit fell below its local floor, a substantive term was suppressed, or unresolved conflicts remain.

Stop iterating when the registered decision is resolved: every candidate has a disposition, required labelability and coverage checks pass, and further locally generated candidates do not resolve remaining uncertainty. Do not prescribe a universal iteration count.

## Route-specific checks

### Network-short

- audit hashtags, aliases, usernames, templates, platform markers and slang;
- inspect terms by duplicate, account, thread, source and time groups;
- do not stoplist a campaign term when diffusion is the research object;
- verify synonym mappings across community-specific meanings.

### Long-document

- protect domain phrases in chunk bodies without repeating headings into lexical text;
- audit custom-term support across independent parent documents, not raw chunk counts;
- verify that a stopword does not erase a secondary theme found in only a few sections;
- retain section and original-offset evidence for every disputed candidate.

## Required outputs

- compiled `lexicon-manifest.json` with no conflicts;
- baseline and candidate assignment exports with one matching fingerprint;
- surface and concept-normalized comparison scorecards;
- adjudicated `lexicon-candidate-audit.csv`;
- `representation-iteration.csv` with the release decision;
- `lexicon-lineage.csv` linking the parent and selected bundle;
- experiment-registry entry identifying the representation snapshot;
- decision-report section describing improvements, deterioration, counter-evidence and rollback.
