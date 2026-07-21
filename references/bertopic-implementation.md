# BERTopic Implementation Guide

## Contents

- Environment and version checks
- Config-driven pipeline
- Text-view separation
- Structural versus representation operations
- Long-document implementation
- Topic exports for evaluation
- Memory and reproducibility
- API verification checklist

## Environment and version checks

Before writing code, inspect the installed versions and current official documentation. BERTopic APIs and serialization behavior can change.

Typical dependencies are:

- `bertopic`;
- the selected embedding backend, often `sentence-transformers`;
- `umap-learn`;
- `hdbscan` or an explicitly chosen alternative clusterer;
- `scikit-learn`;
- a Chinese tokenizer/segmenter only when required for lexical representation.

Record exact package, encoder and tokenizer revisions. Do not silently install or upgrade packages in an established research environment.

## Config-driven pipeline

Keep every numerical choice in the study configuration. Do not embed paper values in code.

```python
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP


def build_topic_model(cfg, embedding_model, tokenizer=None, representation_model=None):
    vectorizer_kwargs = dict(cfg["vectorizer"])
    if tokenizer is not None:
        vectorizer_kwargs.update(tokenizer=tokenizer, token_pattern=None)

    return BERTopic(
        embedding_model=embedding_model,
        umap_model=UMAP(**cfg["umap"]),
        hdbscan_model=HDBSCAN(**cfg["hdbscan"]),
        vectorizer_model=CountVectorizer(**vectorizer_kwargs),
        representation_model=representation_model,
        **cfg["bertopic"],
    )
```

Generate `cfg` from the study contract and candidate registry. Canonically serialize it as JSON so two candidates can be diffed.

## Text-view separation

Maintain parallel arrays keyed by stable unit ID:

- `raw_text`: immutable evidence;
- `embedding_text`: minimally normalized natural text plus justified context;
- `lexical_text`: tokenized/normalized text used by CountVectorizer;
- `display_text`: reviewer-facing text;
- group and parent-document metadata.

BERTopic usually receives one text array for fitting and topic representation. When embedding and lexical views differ:

1. precompute embeddings from `embedding_text`;
2. fit the structural candidate with those embeddings and a declared lexical view;
3. freeze assignments;
4. call `update_topics()` with the intended lexical view and vectorizer for representation experiments;
5. verify that assignments are unchanged.

Do not aggressively remove stopwords or punctuation from embedding text unless the encoder validation supports it.

## Precompute and reuse embeddings

Precompute embeddings for fair structural comparisons and cost control. Store:

- unit order and stable IDs;
- corpus fingerprint;
- encoder name/revision;
- instruction or prefix;
- tokenizer/truncation configuration;
- normalization and pooling;
- vector shape, dtype and file hash.

Never reuse an embedding cache when preprocessing, context enrichment, unit segmentation or encoder settings changed.

## Structural operations

These operations can change document assignments:

- changing embedding text or encoder;
- changing UMAP;
- changing HDBSCAN/clusterer;
- changing the analysis unit;
- fitting on a changed corpus;
- structural `reduce_topics()` or merge actions that alter canonical topic mapping.

For controlled experiments:

- fix the embedding cache while comparing UMAP/HDBSCAN;
- fix representation while comparing structure;
- set and record random state where supported;
- export local assignments before any reduction;
- run finalist seeds and group-aware resamples;
- keep the full candidate registry.

Do not cluster a two-dimensional visualization embedding.

## Representation operations

These operations ordinarily leave assignments unchanged:

- `update_topics()`;
- CountVectorizer vocabulary/tokenization changes applied after fit;
- c-TF-IDF variants;
- `KeyBERTInspired`, MMR or other representation models;
- topic labels and descriptions.

After a representation update, assert equality of unit-to-local-topic assignments and permanent ID mapping. Recompute lexical/label metrics only; retain structural metrics from the frozen assignment.

For Chinese vectorization:

- pass a tested tokenizer callable with `token_pattern=None`;
- keep domain phrases intact;
- fit stop terms and frequency pruning on the modeling corpus only;
- preserve a mapping from normalized terms to display forms;
- audit whether generic policy/platform words dominate c-TF-IDF.

## c-TF-IDF and topic representation

Treat BM25 weighting, frequent-word reduction, n-grams and MMR as hypotheses. Compare them on label fit, within-topic keyword redundancy and stability. They are not substitutes for structural diversity evaluation.

LLM labels must be grounded in exported representative/random/boundary units. Record model, prompt, input IDs and raw output. Do not use an attractive label as evidence that the cluster is coherent.

## Long-document implementation

Fit the model on calibrated chunks from all parent documents. Preserve parent IDs and offsets in a separate table aligned with chunk order.

After fitting/mapping:

1. retain chunk-level local topic, probability/distance and evidence span;
2. correct weights for overlap;
3. aggregate topic evidence by parent document;
4. export section-to-topic evidence;
5. compute parent-level theme distributions and missing content;
6. evaluate with parent-document bootstrap.

`approximate_distribution()` can estimate token-window topic distributions for mapped text. Validate its window/stride against the chunk policy and do not use it to justify whole-document training.

Use `hierarchical_topics()` or an explicit c-TF-IDF/semantic agglomeration to create parent candidates. Audit the tree cut; do not accept a hierarchy merely because the function returned one.

## New data and iteration APIs

- `transform()`: map new units where the fitted components support prediction; retain unknown/boundary evidence.
- `topics_over_time()`: describe representation/prevalence change under a stable global taxonomy.
- `merge_models()`: combine topic models through topic similarity; calibrate similarity decisions locally and revalidate.
- `partial_fit()`: requires incrementally compatible components; using it changes assumptions when density clustering is replaced.
- `reduce_topics()`: creates a taxonomy change; preserve the pre-reduction catalog and evaluate matched granularity.

Read the current official pages linked in `academic-evidence.md` before calling these APIs.

## Topic exports for diversity evaluation

Create a portable JSON file for `scripts/evaluate_diversity.py`:

```json
{
  "topics": [
    {
      "topic_id": "permanent-or-snapshot-topic-id",
      "keywords": ["ranked", "topic", "terms"],
      "embedding": [0.0, 0.0],
      "size": 0
    }
  ]
}
```

Compute `embedding` from representative-unit embeddings under a declared reference encoder. Do not assume BERTopic's stored topic embedding always represents the same construct across model configurations.

For alignment exports, add:

- `topic_uid`;
- `keywords`;
- `anchor_unit_ids` or `representative_unit_ids` when comparable;
- reference-encoder topic embedding.

## Probability and memory decisions

Full document-by-topic probability calculations can be expensive. Decide from the research need:

- use hard assignments plus boundary evidence when complete distributions are unnecessary;
- calculate probabilities for audit/finalists rather than every screening candidate when valid;
- batch long-document inference;
- record whether probabilities are exact, approximate or unavailable;
- never compare confidence measures produced by incompatible clusterers as if identical.

Computational shortcuts must not change which scholarly claims are made without documentation.

## Persistence and reproducibility

Save or record:

- BERTopic model and supported serialization mode;
- external embedding model identifier/files;
- preprocessing and segmentation code/config;
- vectorizer vocabulary and tokenizer revision;
- topic catalogs before and after reduction;
- unit assignments and permanent-ID mapping;
- environment/package report;
- fixed regression units and expected outputs.

Reload the saved model in a clean process and reproduce the fixed regression outputs before release. If exact stochastic reproduction is not supported, document the tolerance and artifact used to verify equivalence.

## API verification checklist

- installed BERTopic version recorded;
- current official signature checked for every non-basic method;
- custom clusterer supports prediction/partial fit required by deployment;
- `prediction_data` or equivalent configured only when required;
- probability semantics documented;
- encoder context limit measured with its tokenizer;
- saved model reload tested;
- structural and representation changes labeled correctly;
- no library default is presented as an academic threshold.
