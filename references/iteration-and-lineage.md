# Model Iteration and Topic Lineage

## Contents

- Snapshot model
- Four update classes
- Triggering shadow experiments
- New-data strategy
- Topic alignment
- Merge/split governance
- Temporal analysis
- Release and rollback

## Snapshot model

Treat an operational BERTopic system as linked immutable snapshots, not as one mutable object.

| Snapshot layer | Contents | Changes assignments? |
|---|---|---|
| data | corpus fingerprint, preprocessing, segmentation, metadata | potentially |
| structure | encoder, UMAP, clusterer, assignments/probabilities | yes |
| representation | vectorizer, c-TF-IDF, keywords, labels | no |
| taxonomy | hierarchy, audited merge/split decisions | changes canonical topic mapping |
| lineage | permanent IDs and old-to-new relationships | no; documents change history |

Give each snapshot a stable descriptive ID containing date/time or a content hash. Do not use ambiguous labels such as “final”, “latest”, or generic v1/v2.

Keep BERTopic's local integer topic ID separate from a permanent `topic_uid`. Never reuse a retired permanent ID for an unrelated theme.

## Four update classes

### Representation refresh

Use when assignments remain defensible but terms, labels or representative documents have drifted.

Allowed actions:

- `update_topics()` with a revised vectorizer/c-TF-IDF representation;
- keyword diversification;
- representative-document refresh;
- grounded label/definition updates.

Required proof:

- structural assignments and permanent IDs are unchanged;
- label/keyword relevance improves on held-out audit units;
- historical and current wording are both preserved when temporal interpretation matters.

Do not call this a structural retrain.

### Structural refit

Use when analysis units, embeddings, UMAP or clustering change. Recompute all structural, taxonomy, diversity, stability and human-audit evidence. Align to the production snapshot before release.

### Taxonomy edit

Use when the structural candidate is retained but selected topics require audited merge, split, parent assignment or retirement. Record the evidence and retain the pre-edit topic catalog.

### New-data mapping

Transform new data through the frozen preprocessing/segmentation and model where supported. Store release-specific assignment, confidence/distance evidence and unknown status. Mapping alone does not authorize a taxonomy change.

## Trigger shadow experiments from evidence

Start a shadow candidate when one or more locally calibrated signals indicate:

- stable themes are repeatedly missing from mapped new data;
- nearest-topic redundancy or human duplicate decisions increase;
- topic definitions no longer fit random/boundary units;
- seed or group-resample stability declines beyond historical uncertainty;
- source, language or time leakage emerges;
- the encoder or segmentation policy systematically confuses important distinctions;
- a broad topic contains recurring, independently supported subthemes;
- the study's research question or source format changes.

Outlier fraction, elapsed time or corpus growth can prompt inspection, but none alone proves the taxonomy requires replacement.

## New-data strategies

### Stable taxonomy is the priority

Prefer:

1. map new units to the frozen model;
2. inspect novelty and drift;
3. fit a batch shadow model on an appropriate historical-plus-new corpus;
4. align and audit topics;
5. release only after Pareto and lineage review.

This is usually easier to reproduce than continuous mutation.

### Batch model merging

`BERTopic.merge_models()` can combine models by topic-embedding similarity. Treat its similarity threshold as a decision parameter requiring local calibration with known retained, changed and genuinely new topics. After merging, recompute nearest-topic redundancy, coverage, stability and labels; merging is not itself validation.

Use one shared or frozen reference embedding space for alignment. If encoders differ, re-embed representative/anchor units with a reference encoder rather than comparing incompatible topic vectors.

### True online learning

Use `partial_fit()` only when streaming latency or memory requirements make batch fitting unsuitable. Verify that every pipeline component supports incremental updates, such as incremental reduction, online clustering and online vectorization. Document that changing from density clustering to an incremental clusterer changes the statistical object and may alter granularity, outlier semantics and stability.

Compare online and batch snapshots on the same audit set. Do not choose online learning solely because an API exists.

## Topic alignment

### Evidence channels

For each old/new pair, retain separate measurements:

- semantic similarity under a frozen reference encoder;
- ranked keyword overlap;
- overlap or transfer of shared anchor units;
- definition/inclusion/exclusion compatibility;
- source/time prevalence pattern as supporting evidence, not identity proof.

Avoid an arbitrary fixed weighted sum. Calibrate thresholds or decision rules with labeled continuity, split, merge and new-theme examples. If evidence channels disagree, mark the pair for review.

Run `scripts/align_snapshots.py` after creating a calibrated threshold file. The script produces one-to-one provisional matches and flags one-to-many/many-to-one structures; it does not make the human taxonomy decision.

### Event vocabulary

Use only these lineage states unless the study contract defines an extension:

- `retained`: same substantive theme and permanent ID;
- `drifted`: continuity exists, but definition or content shifted materially;
- `renamed`: representation changed without substantive identity change;
- `split`: one old theme maps to several defensible new themes;
- `merged`: several old themes map to one defensible new theme;
- `new`: no supported continuity and a validated theme appears;
- `retired`: no supported current continuation;
- `complex`: many-to-many relationship requiring adjudication.

### Identity policy

- Retain an ID only for supported substantive continuity.
- For a split, preserve the old node as historical and create new child IDs unless the governance contract explicitly permits one clear continuation.
- For a merge, preserve old nodes as historical and create a new merged ID unless one theme clearly absorbs only a minor representation variant.
- Record weights or shares only when they have a defensible denominator; do not force them to imply causal ancestry.
- Preserve human decisions and counter-evidence.

## Merge governance

Create a merge decision packet containing:

- semantic and lexical pair evidence;
- representative, random and boundary units from both topics;
- definitions and nearest-topic distinctions;
- independent-source/document support;
- effect on IRBO, semantic diversity, coverage, coherence and stability;
- effect at parent and child hierarchy levels;
- reviewer decision and reason.

Merge only after confirming that the distinction is not substantively useful. A high cosine score is a review trigger, not an automatic merge.

## Split governance

Create a split decision packet containing:

- internal multimodality evidence;
- proposed child definitions and exclusion rules;
- independent support across sources or parent documents;
- child survival under group-aware resampling;
- coverage of the former parent topic;
- nearest-child and nearest-external-topic comparisons;
- human audit and uncertainty.

Do not split solely because a topic is large. Size may reflect a genuinely broad dominant theme.

## Temporal analysis

Use one global topic structure when estimating changes in prevalence or representation over time. Apply `topics_over_time()` or an equivalent aggregation after fixing the taxonomy.

Distinguish:

- prevalence drift: how much a stable topic appears;
- representation drift: how its terms and examples change;
- structural drift: the taxonomy no longer represents content;
- data drift: source/language/collection changes.

Period-specific independent models can be used as exploratory challengers, but align them to the global taxonomy and never compare their local topic numbers directly.

## Release gate

Release only when:

- study bundle validation passes;
- selected candidate lies on the declared Pareto frontier or a documented exception is approved;
- uncertainty and counter-evidence are reported;
- every new topic has a permanent ID and definition;
- every old topic has a lineage disposition;
- merge/split candidates have human decisions;
- fixed regression units can be reproduced after save/reload;
- data, software, model and prompt revisions are recorded;
- previous snapshot and rollback instructions remain available.

Never overwrite historical document assignments. Store at least:

- assignment at ingestion/release time;
- canonical assignment under the current taxonomy;
- structure snapshot ID;
- representation snapshot ID;
- lineage snapshot ID;
- assignment probability/distance when available.

## Monitoring after release

Monitor theme coverage, nearest-topic redundancy, label fit, stability proxies, source leakage, novelty-pool composition and outlier composition. Compare each signal with its historical reference distribution and audit units. A monitoring alert starts investigation; it does not automatically mutate the model.

## Required lineage columns

Use `assets/topic-lineage.csv` and record:

- old and new snapshot IDs;
- old and new permanent topic IDs;
- event type;
- separate evidence channels;
- human decision and reason;
- effective date;
- links to decision packets.

Keep unmatched topics explicit. An empty lineage table is valid only for the initial snapshot.
