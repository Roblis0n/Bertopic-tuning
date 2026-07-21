# Network and Short-Text Route

## Contents

- Research threat model
- Corpus construction
- Text views and Chinese handling
- Context enrichment
- Structural experiments
- Diversity-preserving taxonomy
- Validation and iteration
- Required outputs

## Research threat model

Use this route for posts, comments, short answers, captions, headlines and other units whose meaning is sparse or platform-dependent. The main risks are not merely short length:

- identical templates, reposts and campaigns masquerade as repeated themes;
- usernames, URLs, hashtags, platform markers or source communities become topics;
- abbreviations, emoji and aliases split one concept into several surface forms;
- a message depends on a parent post, thread, image caption or event context;
- random post-level validation leaks near duplicates, authors or threads;
- rare but real themes disappear when global structure is favored;
- small local clusters create apparent diversity through semantic fragmentation.

Treat these as falsifiable failure modes. Record which ones are present in the corpus profile.

## Corpus construction

### Preserve four identifiers

Retain at least:

- stable unit ID;
- near-duplicate/reshare group ID;
- account, thread, source or community ID when available;
- event time or collection batch.

Use these fields for leakage-safe splitting and bootstrap. Never overwrite raw text.

### Separate diffusion from content discovery

Collapse exact and near duplicates for topic discovery, but preserve multiplicity as metadata for later prevalence or diffusion analysis. Otherwise a coordinated campaign or platform template can dominate the taxonomy and inflate apparent support.

Do not automatically collapse:

- repeated language that is itself the research object;
- quotations whose surrounding commentary changes the substantive meaning;
- identical messages posted in analytically distinct populations when population comparison is central.

Record the deduplication rule and provide sensitivity results with and without duplicate weighting.

## Text views and Chinese handling

Maintain separate views:

| View | Purpose | Treatment |
|---|---|---|
| raw | audit and quotation | immutable |
| embedding | semantic clustering | natural text with minimal normalization and justified context |
| lexical | c-TF-IDF and topic words | segmentation, domain dictionary, platform stop terms, phrase handling |
| display | human audit | readable original with source metadata |

For Chinese corpora:

- use contextual/subword embeddings on natural text unless a selected encoder requires another format;
- use a tested tokenizer or segmenter only for lexical representation;
- protect domain entities and multi-character phrases with a domain dictionary;
- normalize traditional/simplified forms only when the research question does not require their distinction;
- normalize aliases and abbreviations through an auditable mapping rather than destructive replacement;
- retain semantically meaningful emoji by converting them to stable textual descriptions;
- treat hashtags as both a full phrase and, when useful, a segmented phrase;
- exclude account handles, URLs and platform boilerplate from c-TF-IDF unless they are substantive variables.

Test whether source or platform markers predict topics. High predictability is evidence of leakage, not thematic diversity.

## Context enrichment

Enrich a unit only when it is semantically underspecified. Candidate context can include:

- title or parent-post text;
- quoted text clearly distinguished from author commentary;
- thread turn immediately required to resolve pronouns or ellipsis;
- event or media caption available to the original reader.

Create two fields: `unit_text` and `context_text`. Mark boundaries explicitly in the embedding string. Do not indiscriminately concatenate all posts by an account, day or thread: that can average several themes and manufacture source-based clusters.

Evaluate enrichment on an annotated set containing:

- same theme with different slang;
- similar vocabulary but different themes;
- context-dependent short units;
- context-independent controls.

Adopt enrichment only if it improves these distinctions without increasing source leakage.

## Structural experiments

### Select embeddings by domain discrimination

Construct a validation set of unit pairs or triplets:

1. clearly same theme despite lexical variation;
2. confusingly similar language but substantively different themes;
3. clearly different themes;
4. rare-theme examples;
5. platform/source counterexamples.

Generate the encoder candidate pool from the corpus language, domain distinctions, context behavior, license, deployment and compute constraints. Compare the resulting current candidates on neighborhood retrieval, ranking and documented errors. A named model in a paper, benchmark or example can supply a mechanism to test, not a mandatory shortlist. Do not select an encoder from a general leaderboard alone. Record exact model revision, pooling, instruction/prefix and truncation behavior.

### Treat UMAP as a locality hypothesis

Construct candidates that represent:

- stronger local-neighborhood preservation for niche themes;
- a balanced neighborhood scale;
- stronger global-structure preservation.

Choose actual values from the corpus neighbor graph and sensitivity results. Inspect whether nearest-neighbor identities and rare-theme retrieval change before fitting HDBSCAN. Do not use a two-dimensional display projection for production clustering.

### Anchor HDBSCAN to substantive support

Define the smallest meaningful theme in terms of independent evidence units, such as unique authors, threads, sources or dates—not repeated posts. Treat that support as a substantive anchor, not a numerical recipe. Start with a diagnostic pilot, inspect where genuine themes disappear or duplicate fragments emerge, and add the next candidate only in unresolved regions of the support-sensitivity curve. Stop when the pre-registered decision boundary, uncertainty target or compute rule is reached. Do not emit a fixed multiplier grid around the anchor.

Perturb `min_samples` separately to distinguish density conservatism from topic granularity. Compare `leaf` and `eom` as competing hypotheses:

- `leaf` may preserve niche themes but can fragment synonyms;
- `eom` may yield broader stable regions but absorb smaller themes.

Judge them by effective diversity and rare-theme survival, not by which yields fewer outliers.

### Keep experimental stages identifiable

Hold representation constant while changing embedding/UMAP/HDBSCAN. Cache embeddings. Use a screening design first and run expensive seed/group-bootstrap evaluation only on non-dominated structural candidates. Derive repetition counts from the precision or stability decision being estimated, not a conventional count.

## Diversity-preserving representation and taxonomy

After freezing assignments:

- compare phrase vocabulary, domain stop terms and frequent-term suppression;
- use MMR or KeyBERTInspired to reduce within-topic keyword redundancy;
- inspect whether keyword changes merely cosmetically raise TD;
- export representative, random and boundary units for every topic.

Generate nearest-topic pairs with both lexical overlap and representative-unit semantic similarity. Audit false splits caused by aliases, hashtags, entities, events or community-specific language.

Prefer a moderately fine candidate followed by audited post-hoc agglomeration when it preserves distinct rare themes better than global coarsening. Do not force a target topic count unless the downstream ontology requires it; if it does, document the loss of diversity at that operating point.

## Validation

### Resampling unit

Bootstrap and split by the highest leakage unit available:

- near-duplicate group;
- account or source;
- conversation/thread;
- event/time block.

Use more than one scheme when each represents a real deployment shift. Random post-level resampling alone is insufficient.

### Short-text scorecard

Emphasize:

- IRBO and semantic nearest-topic redundancy;
- rare-theme survival across seeds and group resamples;
- coverage of a stratified human codebook or missing-theme audit;
- topic-source/account predictability;
- representative versus random/boundary unit agreement;
- time-holdout novelty and drift;
- human ability to write distinct inclusion/exclusion rules.

Report outlier fraction and its composition. Investigate whether outliers contain a stable missing theme, but never reward a candidate simply for assigning more units.

## New data and iteration

Use the frozen taxonomy to map new units first. Maintain a novelty pool containing low-confidence, semantically distant or repeatedly unrepresented material. Trigger a shadow structural refit when the pool contains locally calibrated evidence of stable new themes, when existing themes become semantically redundant, or when group-aware stability degrades—not merely because a calendar interval elapsed.

Fit one global taxonomy for temporal prevalence and use topic-over-time representations. Independently fitted period models confound substantive change with stochastic relabeling.

When merging a new batch model with an existing model, calibrate topic-similarity decisions using known retained, changed and genuinely new themes. Never inherit the library's default similarity threshold as an academic decision rule.

## Required outputs

- duplicate and source-leakage audit;
- context-enrichment decision and validation evidence;
- embedding discrimination results;
- structural candidate registry;
- rare-theme survival table;
- nearest-topic semantic/lexical audit;
- time/source/account-stratified scorecard;
- novelty-pool summary and snapshot lineage.

## Red flags

- hashtags, usernames or platform boilerplate dominate topic labels;
- the same campaign is counted as many independent supporting documents;
- all short units receive indiscriminate author/thread aggregation;
- a high TD score is accepted without semantic pair inspection;
- `leaf` is praised only because it creates more topics;
- outlier reduction is treated as the optimization target;
- period-specific topic IDs are compared directly.
