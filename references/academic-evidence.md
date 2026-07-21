# Academic Evidence Base

## Contents

- Evidence-transfer rule
- Core BERTopic evidence
- Diversity and evaluation evidence
- Short-text evidence
- Long-document evidence
- Stability and optimization evidence
- Official implementation references
- Citation integrity protocol

## Evidence-transfer rule

Use every source through this chain:

```text
claim -> mechanism -> transfer conditions -> local test -> result -> limitation
```

Transfer a methodological idea only when its mechanism fits the new corpus. Do not transfer:

- a paper's optimal UMAP/HDBSCAN values;
- its similarity or merge threshold;
- its chunk length;
- its number of seeds, resamples or human examples;
- its topic-count range;
- a weighted metric formula;
- its reported improvement as an expected effect.

Those values depend on corpus size, language, encoder geometry, theme prevalence, preprocessing and research purpose. Record paper-derived ideas in `evidence-log.csv` with a scope limitation and the local experiment used to test them.

Do not disguise transfer as a scaled recipe such as fixed multiples of a locally defined support value, a standard encoder shortlist, or a conventional reviewer count. Extract why a paper varied a component, what failure it was intended to reveal, what evidence resolved the choice and when the search stopped. Rebuild those decision rules on the target corpus.

## Core BERTopic evidence

### Grootendorst (2022), BERTopic

- Source: [arXiv 2203.05794](https://arxiv.org/abs/2203.05794); [full HTML](https://ar5iv.labs.arxiv.org/html/2203.05794)
- Status: preprint; original BERTopic methods paper.
- Transferable ideas:
  - modular separation of embedding, reduction, clustering and c-TF-IDF representation;
  - different preprocessing can serve embedding and lexical representation;
  - topic words can be updated independently from clustering;
  - a standard fit gives one primary topic per input unit, so analysis-unit design matters.
- Do not transfer: dataset-specific parameter choices or the use of simple TD/NPMI as sufficient validation.
- Local test: separate structural and representation experiments; compare analysis units; add semantic, coverage, stability and human validation.

### Janssens, Bogaert and Van den Poel (2025)

- Source: [Ghent University record and article](https://biblio.ugent.be/publication/01KBA5N45SY9KNX60813ASKBAR); [author-hosted PDF](https://biblio.ugent.be/publication/01KBA5N45SY9KNX60813ASKBAR/file/01KBYFV31HFRY99MGEKKNQNSDW.pdf)
- Status: peer-reviewed IEEE Access article.
- Evidence: across Trump tweets, COVID tweets and Yelp reviews, indirect post-hoc reduction using c-TF-IDF agglomeration generally preserved or improved lexical diversity better than obtaining fewer topics solely through coarser clustering; LLM-assisted reduction could help but cost and evaluation remained issues.
- Transferable idea: preserve a fine candidate first, then compare audited post-hoc aggregation with global coarsening.
- Limitations: three web/social-review datasets, limited human evaluation and formal statistical testing; results are not a universal merge rule.
- Local test: compare matched topic-count solutions produced by direct coarsening and post-hoc hierarchy, using semantic distinctiveness, coverage, stability and human audit.

## Diversity and evaluation evidence

### Dieng, Ruiz and Blei (2020)

- Source: [Transactions of the ACL](https://aclanthology.org/2020.tacl-1.29/)
- Status: peer-reviewed.
- Transferable idea: quantify uniqueness of top words across topics and combine quality dimensions rather than coherence alone.
- Limitation: simple Topic Diversity is lexical, topic-count-sensitive and can reward fragmentation.
- Local test: retain TD only as a screen and add IRBO plus semantic nearest-topic analysis.

### Tan and D'Souza (2025)

- Source: [International Journal on Digital Libraries](https://link.springer.com/article/10.1007/s00799-025-00429-5)
- Status: peer-reviewed version of record.
- Evidence: lexical diversity measures had only modest association with LLM-rated semantic diversity in their comparison; their reported IRBO/semantic association was not strong enough to treat the metrics as substitutes. BERTopic could combine high coherence with repetition or missing-theme errors in some settings.
- Transferable idea: evaluate lexical and semantic diversity separately and audit missing themes.
- Limitations: English corpora, LLM-judge dependence, and limited repeated fitting for configurations.
- Local test: human-calibrate semantic pair judgments and repeat structural fits.

### Hoyle et al. (2021)

- Source: [NeurIPS paper](https://papers.nips.cc/paper_files/paper/2021/hash/0f83556a305d789b1d71815e8ea4f4b0-Abstract.html)
- Status: peer-reviewed.
- Transferable idea: automated coherence can rank models differently from human interpretability.
- Local test: use coherence as a floor and conduct representative/random/boundary human audit.

### Lim and Lauw (2024)

- Source: [Computational Linguistics](https://aclanthology.org/2024.cl-3.3/)
- Status: peer-reviewed.
- Transferable idea: evaluation validity is corpus-dependent; correlations with human judgments vary by setting.
- Local test: calibrate metrics on the target corpus and report disagreement between metrics and reviewers.

### Stammbach et al. (2023)

- Source: [EMNLP paper](https://aclanthology.org/2023.emnlp-main.581/)
- Status: peer-reviewed.
- Transferable idea: LLM topic ratings can align better with human judgments than some lexical metrics.
- Limitation: result depends on prompt, model, task framing and human reference.
- Local test: freeze and validate the LLM rubric against independent human ratings before scaling it.

### Chang et al. (2009), Reading Tea Leaves

- Source: [NeurIPS paper](https://proceedings.neurips.cc/paper/2009/hash/f92586a25bb3145facd64ab20fd554ff-Abstract.html)
- Status: peer-reviewed.
- Transferable idea: better probabilistic fit does not guarantee human-interpretable topics.
- Local test: retain human word/document intrusion or equivalent distinguishability tasks.

## Short-text evidence

### de Groot et al. (2022)

- Source: [arXiv 2212.08459](https://arxiv.org/abs/2212.08459)
- Status: preprint.
- Evidence: BERTopic performed competitively on very short open-ended responses and a benchmark corpus under lexical diversity/coherence measures.
- Transferable idea: contextual embeddings plus document clustering can address sparse short-text co-occurrence better than bag-of-words alone in some corpora.
- Limitations: simple lexical diversity, selected datasets and preprint status.
- Local test: compare domain encoders and include a short-text baseline under the same human/semantic evaluation.

### Feng et al. (2025), BERTopic_Teen

- Source: [Frontiers in Public Health](https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2025.1608241/full); [PubMed record](https://pubmed.ncbi.nlm.nih.gov/40873978/)
- Status: peer-reviewed.
- Evidence: a domain Twitter study combined frequent-term suppression, representation diversification and dimensionality search and reported very high lexical TD.
- Transferable ideas: suppress generic domain terms, separate representation quality from structure, and search reduction choices.
- Limitation: one health domain; near-ceiling TD illustrates why TD alone cannot validate semantic diversity.
- Local test: semantic nearest-topic and human pair audit after representation changes.

### Short-text robustness comparators

- Biterm Topic Model: [Yan et al. (2013)](https://xiaohuiyan.github.io/paper/BTM-WWW13.pdf). Idea: model corpus-level biterm co-occurrence for sparse short text; use as a robustness comparator when co-occurrence is substantively meaningful.
- Neural topic modeling for short texts: [Wu et al. (2020), EMNLP](https://aclanthology.org/2020.emnlp-main.138/). Idea: compare whether a dedicated short-text topic model recovers themes BERTopic misses.

Do not add these comparators mechanically. Add one when the scholarly claim needs evidence that findings are not an artifact of BERTopic's embedding-clustering design.

## Long-document evidence

### Yu et al. (2023)

- Source: [EMNLP paper](https://aclanthology.org/2023.emnlp-main.341/)
- Status: peer-reviewed; not a BERTopic-specific study.
- Transferable idea: detect semantic topic boundaries when natural document boundaries are unreliable, and evaluate segmentation directly.
- Limitation: segmentation benchmarks and objectives differ from every target corpus.
- Local test: compare natural, semantic and fixed-window policies on boundary judgments and theme recovery; do not copy window sizes.

### BERTopic distribution limitation

- Source: [official topic-distribution documentation](https://maartengr.github.io/BERTopic/getting_started/distribution/distribution.html)
- Transferable idea: sliding windows can approximate multiple topic distributions within a document.
- Limitation: approximate inference does not repair a taxonomy trained on semantically averaged or truncated whole documents.
- Local test: train on defensible chunks and compare aggregate document-theme recovery.

## Stability and optimization evidence

### Greene, O'Callaghan and Cunningham (2014)

- Source: [arXiv 1404.4606](https://arxiv.org/abs/1404.4606)
- Status: preprint.
- Transferable idea: too few topics can be broad and too many can be small/redundant; perturbation stability helps diagnose granularity.
- Local test: seed, group-bootstrap and nearby-decision perturbations with topic alignment.

### Terragni et al. (2021), OCTIS

- Source: [EACL demonstrations](https://aclanthology.org/2021.eacl-demos.31/)
- Status: peer-reviewed demo paper.
- Transferable idea: register comparable pipelines, optimize multiple metrics and retain experiment metadata.
- Local test: use explicit constraints and a Pareto frontier instead of one weighted score.

## Official implementation references

Use official documentation for current API behavior; verify the installed BERTopic version before implementation:

- [parameter tuning](https://maartengr.github.io/BERTopic/getting_started/parameter%20tuning/parametertuning.html)
- [best practices](https://maartengr.github.io/BERTopic/getting_started/best_practices/best_practices.html)
- [vectorizers and update_topics](https://maartengr.github.io/BERTopic/getting_started/vectorizers/vectorizers.html)
- [c-TF-IDF](https://maartengr.github.io/BERTopic/getting_started/ctfidf/ctfidf.html)
- [representation and MMR](https://maartengr.github.io/BERTopic/getting_started/representation/representation.html)
- [topic reduction](https://maartengr.github.io/BERTopic/getting_started/topicreduction/topicreduction.html)
- [hierarchical topics](https://maartengr.github.io/BERTopic/getting_started/hierarchicaltopics/hierarchicaltopics.html)
- [model merging](https://maartengr.github.io/BERTopic/getting_started/merge/merge.html)
- [online learning](https://maartengr.github.io/BERTopic/getting_started/online/online.html)

Documentation explains API behavior, not scholarly validity. Do not treat a library default as an evidence-backed research threshold.

## Citation integrity protocol

Before citing a source in a new report:

1. open the publisher, proceedings, repository or official documentation page;
2. verify title, authors, year, venue, DOI/version and access date;
3. check for correction, expression of concern, retraction or superseding version;
4. read the methods/limitations supporting the exact claim;
5. record evidence type: peer-reviewed, proceedings, preprint or documentation;
6. state dataset/language/domain limits;
7. log the transferable mechanism and local validation—not a copied parameter.

Use `assets/evidence-log.csv`. If a paper cannot be verified, do not use it to justify a decision.
