# Diversity Evaluation and Model Selection

## Contents

- Effective diversity construct
- Lexical metrics
- Semantic metrics
- Coverage and missing themes
- Stability
- Human and LLM audit
- Threshold calibration
- Pareto selection
- Failure diagnostics

## Effective diversity construct

Treat topic diversity as a construct with several measurements:

| Dimension | Question | Preferred evidence |
|---|---|---|
| lexical distinctiveness | Do topics repeat the same ranked terms? | TD plus IRBO/ranked overlap |
| semantic distinctiveness | Are nearest topics genuinely different concepts? | representative-unit topic embeddings and pair audit |
| within-topic representation | Do keywords convey different facets without becoming irrelevant? | semantic keyword redundancy and human label fit |
| theme coverage | Are important corpus themes missing? | reference-code recall or stratified missing-theme audit |
| stability | Do themes survive seeds, resamples and nearby analytical decisions? | aligned topic survival and assignment agreement |
| interpretability | Can a reviewer define and distinguish each theme? | representative/random/boundary unit audit |

Do not collapse these into a single score before inspection. A model can be lexically diverse but semantically redundant, semantically distinct but unstable, or coherent but incomplete.

## Lexical metrics

### Topic Diversity

At registered keyword depth (k):

\[
TD@k=\frac{|\bigcup_{i=1}^{K} W_i^{(k)}|}{Kk}
\]

Use TD as a descriptive screen only. It ignores rank, semantics and topic support. It can rise when one concept is fragmented into topics with different synonyms, and can saturate near one.

Register (k) before comparing candidates and require every topic to export that many valid terms. Compare models at matched (K), a declared topic-count band, or equivalent hierarchy levels.

### Rank-aware overlap

Use rank-biased overlap (RBO) for each topic pair and report inverse RBO (IRBO) as lexical diversity. Record the persistence parameter and keyword depth in the study contract. Report:

- mean or median pairwise IRBO;
- lowest IRBO / highest RBO topic pairs;
- nearest lexical neighbor for every topic;
- sensitivity to keyword depth.

Pairwise means can hide a few near-duplicate topics, so always inspect the upper tail of overlap.

## Semantic metrics

Create topic embeddings from representative-unit embeddings or a robust topic medoid/centroid. Keep the reference encoder fixed when comparing snapshots. Top-word embeddings alone can measure the representation rather than the underlying assigned content.

For topic (i), define nearest-topic similarity:

\[
s_i=\max_{j\ne i}\cos(e_i,e_j)
\]

Report:

- median, upper quantile and maximum of (s_i);
- (1-\operatorname{median}(s_i)) as a compact semantic-diversity summary;
- proportion of topic pairs above a locally calibrated redundancy threshold;
- the most similar pairs with representative/random/boundary evidence;
- distributions by topic size and hierarchy level.

Nearest-neighbor summaries are more diagnostic than the mean over all topic pairs, which is dominated by obviously unrelated pairs.

### Calibrating semantic redundancy

Create labeled topic pairs:

- duplicate concepts that should merge;
- related but defensibly distinct concepts;
- clearly distinct controls;
- rare and broad topic examples.

Estimate a threshold from the intended decision cost using held-out labels, precision-recall analysis or a documented empirical boundary. Do not reuse a cosine value from another encoder, language or corpus.

## Within-topic keyword diversity

MMR and similar representation methods reduce redundant keywords. Evaluate:

- keyword semantic duplication;
- label fit to representative and random units;
- intrusion of attractive but unsupported terms;
- stability of the keyword list across resamples.

This dimension improves topic communication. It does not prove structural topic diversity because assignments remain unchanged.

## Coverage and missing themes

### With a reference codebook

Map modeled topics to reference themes using a blinded alignment protocol. Report:

- reference-theme recall;
- precision of mapped topics;
- themes split across several topics;
- modeled topics absent from the codebook;
- performance for rare and subgroup-specific themes.

Do not force one-to-one alignment when the reference hierarchy differs from the model hierarchy.

### Without a reference codebook

Construct a stratified audit sample across source, time, length, group and low-confidence regions. Have reviewers identify substantive themes before seeing model labels, then measure which themes are represented.

For long documents, compare model themes with headings, abstracts, analyst summaries or independent annotations. For short texts, oversample rare events, communities and vocabulary variants.

Report missing-theme evidence separately from assignment coverage. A high assigned fraction can coexist with low substantive theme coverage.

## Stability

Use three forms of perturbation:

1. random seeds for stochastic components;
2. resampling at the independent evidence unit;
3. nearby defensible analytical choices, such as tokenization, segmentation or locality assumptions.

For long texts, resample parent documents. For network texts, resample duplicate/account/thread/time groups when these induce dependence.

Align topics across runs with representative-unit semantic similarity, ranked keyword similarity and shared-unit evidence. Report dimensions separately instead of assuming a universal weighted sum.

Report:

- topic survival frequency;
- matched semantic and lexical similarity distributions;
- retained/split/merged/unmatched events;
- assignment AMI/NMI or another declared agreement statistic on common units;
- document-topic distribution agreement for long texts;
- rare-theme survival;
- uncertainty intervals across resamples.

Calibrate “stable enough” from the intended use, human-coded anchors, historical reproducibility or a minimum effect requirement. Do not inherit a publication's threshold.

## Human and LLM audit

For every finalist, sample from each topic:

- representative units;
- random assigned units;
- boundary/low-margin units;
- units from distinct sources or parent documents;
- the nearest competing topic.

Require the reviewer to record:

- concise label;
- definition;
- inclusion rule;
- exclusion rule;
- nearest-topic distinction;
- relevance, internal coherence, distinctiveness and label fit;
- missing-theme observations.

Use independent review and adjudication when a scholarly claim requires inter-reviewer evidence. Do not prescribe a universal reviewer count; derive the design from the claim, reliability estimand, expected disagreement and feasible adjudication plan. A single exploratory reviewer cannot support an inter-reviewer reliability claim. Report agreement and adjudication. Sample size should follow the precision required for the claim, not a paper's example count.

An LLM can scale pairwise semantic or label audits, but first calibrate it against human ratings, freeze model/prompt, randomize label order where appropriate, retain raw responses and report sensitivity to prompt/model. LLM ratings are evidence, not ground truth.

## Outlier role

Record:

- overall outlier/unknown fraction;
- distribution by source, group, time and length;
- semantic composition of the unknown pool;
- stable missing-theme clusters within it;
- effect of any reassignment on diversity and labelability.

Use these as diagnostics and safety constraints. Do not maximize assigned fraction or minimize outliers as a primary objective. A density model may correctly leave boundary material unassigned; forced reassignment can blur themes and erase novelty.

## Threshold calibration hierarchy

For every numeric gate, record one of these evidence sources:

1. **decision-linked human labels**: preferred for semantic duplicate, coverage and labelability gates;
2. **historical reference distribution**: appropriate for drift and regression monitoring;
3. **empirical null or negative controls**: appropriate for similarity and stability diagnostics;
4. **measurement precision/minimum effect**: appropriate for sample size and practical improvement;
5. **sensitivity frontier**: appropriate when no single threshold is defensible.

If none applies, leave the result as exploratory and show the metric curve instead of inventing a cutoff.

## Pareto selection

Separate constraints from objectives.

Typical constraints, each locally justified, include:

- minimum coherence or human labelability;
- required reference-theme coverage;
- required reproducibility;
- operational topic-count/hierarchy scope;
- maximum tolerated source leakage;
- coverage/outlier guardrail.

Typical objectives include:

- maximize IRBO;
- maximize semantic distinctiveness;
- maximize theme coverage;
- maximize stability;
- minimize unresolved duplicate pairs;
- minimize maintenance cost only after scholarly quality is satisfied.

Do not assign arbitrary metric weights. Find the non-dominated frontier, inspect uncertainty intervals, then choose the point that best matches the research purpose. If confidence intervals overlap substantially, report candidates as empirically tied and prefer the simpler, more reproducible taxonomy only with an explicit rationale.

## Candidate comparison contract

Each row in `candidate-metrics.csv` must correspond to one registered candidate and include:

- topic count and hierarchy level;
- TD and IRBO settings/results;
- semantic nearest-neighbor result;
- coverage result and method;
- stability result and resampling unit;
- coherence and human labelability;
- outlier fraction as diagnostic;
- uncertainty or a link to the resampling result;
- status and rejection reason.

Run `scripts/evaluate_diversity.py` for portable lexical/semantic metrics and `scripts/select_pareto.py` for the declared frontier.

## Failure diagnostics

| Pattern | Likely cause | Next experiment |
|---|---|---|
| TD high, semantic diversity low | synonym/event fragmentation | audit nearest pairs; adjust locality or merge taxonomy |
| coherence high, coverage low | broad common themes dominate | inspect missing themes; protect rare support and revise units |
| diversity high, stability low | microcluster fragmentation | raise evidence support or favor reproducible hierarchy |
| labels diverse, assignments identical | representation-only cosmetic change | report as label improvement, not structural gain |
| coverage high, distinctiveness low | forced assignment or over-broad clusters | restore density boundaries; audit assigned fringe units |
| stable topics follow source/account | leakage or corpus confounding | group validation and artifact removal |
| long-document stability high only by chunk bootstrap | parent-document leakage | repeat bootstrap by parent document |
