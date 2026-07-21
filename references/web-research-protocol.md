# Conditional Web Research Protocol

## Trigger online research

Search the web when any of these conditions applies:

- the user requests recent/current literature or explicit verification;
- a paper, dataset, package page, model card or documentation page is cited but not locally available;
- BERTopic, UMAP, HDBSCAN, sentence-transformers or another API/version may have changed;
- selecting currently available embedding or segmentation models;
- making a formal scholarly claim that needs a traceable source;
- the bundled evidence base does not cover the corpus language, domain, text type or method;
- checking correction, retraction, superseding version or publication status;
- designing a robustness comparator or locating validated human-evaluation instruments.

Do not browse merely to calculate local metrics, inspect the user's artifacts, reproduce a frozen run, or repeat a source that has already been verified for the same claim and version.

If network access is unavailable, continue with local evidence and clearly mark the literature review as not refreshed. Do not claim current completeness.

## Source priority

Use sources in this order:

1. peer-reviewed paper at the publisher or proceedings site;
2. official preprint repository or author/institution repository;
3. official BERTopic/package documentation and release notes;
4. official model card, dataset card or repository;
5. citation index or database record for discovery;
6. secondary discussion only to locate primary evidence, not to support the final claim.

For technical claims, rely on official documentation or source repositories. For scientific claims, rely on the paper itself. Do not cite search-result snippets.

## Search by decision, not by broad topic

Form queries around the decision being made. Example query families:

### Diversity and evaluation

```text
BERTopic semantic topic diversity human evaluation
topic model IRBO semantic diversity nearest topic similarity
topic model stability bootstrap topic alignment
BERTopic topic reduction diversity agglomerative c-TF-IDF
```

### Network/short text

```text
BERTopic short text social media topic diversity evaluation
short text topic model semantic clustering stability
Chinese social media BERTopic human validation
topic model source leakage duplicate posts bootstrap
```

### Long documents

```text
BERTopic long document semantic segmentation chunk topic modeling
long document topic segmentation theme coverage evaluation
document-level bootstrap chunk topic model
hierarchical topic modeling long documents human evaluation
```

### Iteration and lineage

```text
BERTopic model merge topic alignment temporal stability
dynamic topic model topic lineage merge split evaluation
BERTopic online learning partial_fit current documentation
topic taxonomy versioning permanent topic IDs
```

Add the target language/domain and exclude irrelevant meanings of “topic diversity” when necessary.

## Search workflow

1. Define the exact decision and evidence needed.
2. Search multiple scholarly indexes/search engines when exhaustive coverage matters.
3. Open primary sources and read methods, results and limitations—not only abstracts.
4. Follow backward references for foundational methods and forward citations for replications or criticism.
5. Verify publication status, DOI/version, correction/retraction state and access date.
6. Extract the mechanism, population/corpus, evaluation design, result and limitation.
7. Identify whether the source supports a principle, comparator, metric or implementation fact.
8. Design a local test; never convert a reported optimum into a default.
9. Record the source and transfer decision in `evidence-log.csv`.
10. Cite the primary source next to the claim in the decision report.

## Evidence extraction record

For each source record:

- full citation and stable URL/DOI;
- evidence status: peer-reviewed, proceedings, preprint, documentation, model card;
- corpus size, language, domain and analysis unit;
- model comparison and evaluation design;
- key result relevant to the decision;
- uncertainty/statistical evidence if reported;
- limitations and conflicts of interest when relevant;
- correction/retraction/version check;
- transferable mechanism;
- non-transferable parameters;
- local validation experiment;
- access date.

## Database-specific use

When conducting a formal review, preserve exact queries, databases, dates, result counts, duplicates and screening decisions. Use a PRISMA-like log when claims of comprehensive or systematic coverage are made.

For an ordinary modeling decision, a targeted evidence update is sufficient, but still search for counter-evidence and at least one independent source when the claim materially affects the pipeline.

## Current implementation checks

Before coding version-sensitive BERTopic behavior:

- open the official page for the installed/current release;
- inspect the installed function signature or local package source;
- confirm whether custom UMAP/clusterer components support `transform()` or `partial_fit()`;
- confirm persistence/serialization requirements;
- verify encoder context length and prompt/prefix from the official model card;
- record the checked versions and URLs.
- verify current `CountVectorizer` tokenizer, stop-word and fixed-vocabulary semantics before changing the lexicon adapter.

Package documentation supports what an API does, not whether that operation is scientifically valid for the corpus.

## Literature-to-experiment rule

For each paper-derived idea, write:

```text
paper claim:
mechanism:
transfer conditions:
target-corpus risk:
local comparison:
success/failure evidence:
decision:
```

Reject any entry that contains only “the paper used parameter X, therefore use X.”

## Search stopping rule

Stop targeted searching when:

- the decision has primary-source support and credible counter-evidence has been checked;
- additional results repeat the same mechanism without changing transfer conditions;
- current API/model facts are verified from official sources;
- remaining uncertainty is local and must be resolved empirically.

Do not substitute more searching for running the target-corpus validation experiment.
