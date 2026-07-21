# Long-Document Route

## Contents

- Research threat model
- Analysis-unit design
- Chunking calibration
- Corpus-wide modeling
- Document aggregation
- Hierarchical taxonomy
- Validation and iteration
- Required outputs

## Research threat model

Use this route for reports, articles, policies, interviews, books, legal texts and other documents that can contain several substantive themes or exceed useful encoder context. Primary risks are:

- one full-document embedding averages several themes;
- truncation makes the beginning of the document dominate;
- headings, boilerplate or reference sections create artificial topics;
- long documents contribute more chunks and dominate clustering/prevalence;
- overlapping windows duplicate evidence and inflate support;
- chunk-level resampling leaks the same parent document across samples;
- a one-topic document assignment hides secondary themes;
- broad parent topics and fine child topics are evaluated as if they had the same granularity.

The principal tuning decision is the analysis unit. Do not begin with HDBSCAN parameters.

## Analysis-unit design

Use the sequence **segment first, model second, aggregate last**.

Prefer boundaries in this order:

1. section or subsection headings;
2. coherent paragraphs;
3. sentence groups separated by detected semantic change;
4. fixed token windows only when structural and semantic boundaries are unavailable.

Preserve:

- `document_id` and immutable raw text;
- section path and heading text;
- `chunk_id`;
- original character/token offsets;
- chunk type, such as prose, list, table, citation or appendix;
- overlap span, if any;
- embedding, lexical and display text views.

Never let a chunk lose its parent-document link.

## Chunking calibration

Do not copy a chunk length from another paper. Build candidate segmentation policies from:

- the selected encoder's tokenizer and documented context limit;
- natural section/paragraph length distribution;
- a human-labeled set of semantic boundary decisions;
- within-chunk cohesion and between-adjacent-chunk separation;
- retention of known secondary themes;
- computational constraints documented separately from scientific quality.

Evaluate at least these policy families when applicable:

- natural paragraph/section boundaries;
- merge-short/split-long structural segments;
- semantic boundary detection;
- fixed windows as a fallback comparator.

Prefix headings to the embedding view when they disambiguate the chunk, but avoid repeating headings in the lexical view if they would dominate c-TF-IDF. Keep the original heading as metadata.

Use overlap only when a coherent segment must be forcibly split. Record overlapping spans and remove or down-weight duplicated evidence during aggregation and prevalence estimation.

### Chunk-policy audit

For each candidate policy, inspect:

- truncation rate under the real tokenizer;
- proportion of chunks judged internally multi-topic;
- proportion missing required local context;
- boundary agreement with human judgments;
- recovery of themes listed in headings, abstracts or an independent codebook;
- duplicate evidence introduced by overlap;
- number of chunks contributed by each parent document.

Select chunking jointly with the research question, before structural topic tuning.

## Corpus-wide modeling

Fit one BERTopic model over chunks from the corpus, not one model per document. Separate discovery and mapping:

1. Construct a discovery sample that represents documents, sections, time periods and sources without allowing very long documents to dominate.
2. Fit and select the taxonomy on that sample or the full corpus when feasible.
3. Map all chunks to the frozen taxonomy.
4. Aggregate mapped evidence back to documents.

If sampling chunks for discovery, give each parent document a declared sampling budget or weight. Sample across its section structure rather than taking only the beginning or a purely random concentration.

Apply the structural experiment rules from `SKILL.md`:

- compare embeddings on domain same/different chunk pairs;
- vary locality hypotheses rather than copying UMAP grids;
- anchor minimum theme support to independent parent documents as well as chunks;
- perturb clustering conservatism separately from minimum cluster size;
- preserve fine themes before audited hierarchy construction.

A theme supported by many chunks from one document is not equivalent to a theme supported across many independent documents. Report both supports.

## Document aggregation

For document (d), chunk (c), and topic (t), aggregate a chunk distribution (p(t\mid c)) using non-duplicated evidence weights:

\[
p(t\mid d)=\frac{\sum_{c\in d} w_c p(t\mid c)}{\sum_{c\in d} w_c}
\]

Derive (w_c) from non-overlapping valid tokens, characters or another justified evidence unit. If only hard chunk assignments exist, aggregate weighted indicators and state that uncertainty within chunks is unavailable.

Provide each document with:

- primary and secondary themes;
- weighted theme proportions;
- contributing sections and original offsets;
- strongest evidence chunks;
- boundary/uncertain chunks;
- content not represented by the taxonomy.

Compute effective document theme count, (\exp(H(p(t\mid d)))), only as a diagnostic. Do not maximize it: a fragmented model can inflate it.

`approximate_distribution()` can create a sliding-window approximation for mapped documents. Treat it as an inference aid, not a substitute for selecting defensible training units. Validate its window policy against the same chunk-boundary audit.

## Representation and hierarchical taxonomy

Use the chunk body for c-TF-IDF, with domain phrase handling and lexical normalization. Use heading context for semantic interpretation when justified.

Maintain at least two declared levels when the research purpose needs both:

- fine chunk themes for retrieval and evidence tracing;
- parent themes formed by audited semantic/c-TF-IDF hierarchy for synthesis.

Evaluate each level separately. A parent-level model may be coherent but broad; a child-level model may be distinct but locally fragmented. Never average metrics across levels without reporting each one.

Merge only when:

- semantic and lexical evidence indicate redundancy;
- representative, random and boundary chunks cannot support separate definitions;
- parent-document distributions do not reveal a meaningful distinction;
- the merge remains stable under document-level resampling.

Split only when a broad topic contains recurring subthemes across independent documents and each child has a defensible inclusion/exclusion rule.

## Validation

### Resample by parent document

Every random split, bootstrap and perturbation must keep all chunks from one parent document together. If documents are nested in authors, institutions or series, add grouped sensitivity analyses at those levels.

### Long-document scorecard

Emphasize:

- corpus-level lexical and semantic inter-topic distinctiveness;
- document-weighted theme coverage;
- recovery of themes from headings, abstracts or independent annotations;
- missing-theme audit on sampled documents;
- topic survival under document-level resampling;
- parent-document diversity of support for every theme;
- evidence traceability from theme to chunk to original offset;
- agreement between representative, random and boundary chunks;
- distinctiveness at both parent and child hierarchy levels.

Do not let average coverage hide documents whose secondary themes disappear. Report distributions and stratify by document length, source, time and structure.

### Human audit

For each topic, sample:

- representative chunks;
- random assigned chunks;
- boundary or second-choice chunks;
- chunks from several parent documents;
- the most similar neighboring topic.

Ask reviewers to write a definition, inclusion rule, exclusion rule and nearest-topic distinction. Audit sampled documents against headings/abstracts or an independent summary to locate missing themes.

## New data and iteration

Map new documents using the identical chunking and aggregation policy. A chunk-policy change is a structural data change and requires a new corpus fingerprint plus back-comparison.

Maintain:

- the original assignment under the release used at ingestion;
- the canonical assignment under the current taxonomy;
- parent-document aggregation under each relevant snapshot;
- topic lineage and chunk-policy lineage.

Trigger a shadow refit when new documents contain validated missing themes, existing topics become semantically redundant, chunk-level stability degrades at the document level, or the original segmentation policy no longer represents the source format. Do not use outlier rate alone.

Use a global taxonomy for time comparison and apply topics-over-time or document-level prevalence aggregation. Independent yearly models cannot be compared by local topic number.

## Required outputs

- chunking-policy comparison and tokenizer-limit audit;
- chunk table with parent IDs and offsets;
- document-contribution balance audit;
- chunk-level topic catalog;
- parent-theme hierarchy and level-specific metrics;
- document-topic distribution with evidence links;
- document-level bootstrap stability;
- missing-theme audit;
- snapshot and chunk-policy lineage.

## Red flags

- full reports are embedded as single units despite multiple themes;
- chunk size comes from a paper rather than local boundary validation;
- headings are repeated into c-TF-IDF and dominate every topic;
- overlap is counted twice;
- long documents contribute unbounded discovery weight;
- chunks are randomly split across train and validation;
- topic popularity is raw chunk count;
- parent and child topics share one diversity score;
- `approximate_distribution()` is treated as a cure for poor training units.
