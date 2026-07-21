# Full-Corpus Theme Reconnaissance

## Contents

- Purpose and boundary
- User-theme brief
- Full-corpus accounting
- Reading procedure
- Candidate-theme map
- Topic-count estimate
- Route-specific handling
- User preview and authorization gate
- Preview-versus-model audit
- Validation commands
- Red flags

## Purpose and boundary

Run a full-corpus theme reconnaissance after fingerprinting and before any embedding, dimensionality reduction, clustering, topic reduction, or BERTopic fit. Its purpose is to give the user an evidence-linked provisional map of what the corpus appears to contain, estimate a defensible coarse and fine topic-count range, and obtain explicit direction for the modeling study.

This stage is qualitative reconnaissance, not a topic model. Its estimate must be recorded as `pre_model_hypothesis_not_target_k`. It must not be copied into `nr_topics`, HDBSCAN parameters, a forced cluster count, or a model-selection target. Later modeling may confirm, merge, split, reject, or add themes.

The user's theme is the mainline for coverage and interpretation, not a closed label set. Use `coverage_and_interpretation_anchor` and keep `allow_emergent_themes: true`. Do not suppress recurring corpus evidence merely because it is outside the user's initial framing.

## User-theme brief

Before reading the corpus, restate the user's mainline in operational language:

- the central phenomenon, population, setting, and time frame;
- what should count as direct evidence for the mainline;
- adjacent evidence that can explain or qualify it;
- exclusions explicitly requested by the user;
- ambiguities that should be surfaced in the preview rather than silently resolved.

Store this in `theme-reconnaissance.json` under `user_theme`. Classify each candidate theme by its relation to the mainline:

- `mainline`: directly answers or instantiates the user's theme;
- `supporting`: mechanism, cause, consequence, actor, or subtheme needed to interpret the mainline;
- `contextual`: recurring background that frames the mainline without directly answering it;
- `emergent`: substantively recurring evidence not anticipated by the user's framing;
- `artifact`: template, boilerplate, source marker, duplicated campaign, reference list, or other non-substantive pattern;
- `uncertain`: evidence is insufficient to place the candidate reliably.

## Full-corpus accounting

“Full corpus” means complete and auditable accounting of every source unit, not placing the whole corpus into one prompt. The reconnaissance is complete only when these equations hold:

```text
source_unit_count = eligible_unit_count + excluded_unit_count
eligible_unit_count = reviewed_unit_count
                    + duplicate_inherited_unit_count
                    + failed_unit_count
failed_unit_count = 0
```

Record the counts and exclusion basis in `theme-reconnaissance.json`. Every eligible unit must therefore be directly reviewed or be an exact duplicate whose interpretation is inherited from a reviewed canonical unit. Near duplicates cannot inherit review because small differences may change stance, actor, event, or theme.

Use stable unit IDs throughout. Preserve an audit link from every candidate theme to evidence IDs in `theme-candidate-audit.csv`. Do not claim full coverage from a sample, search result, topic keyword list, embedding neighborhood, or beginning-of-file scan.

If a unit cannot be read or parsed, record it in `failed_unit_ids`, leave `coverage_complete: false`, and repair the failure before presenting the reconnaissance as complete. Do not silently omit malformed, very long, non-Chinese, or inconvenient records.

## Reading procedure

Process the corpus in bounded batches while maintaining a cumulative codebook:

1. Freeze source order, stable IDs, fingerprint, route, and exclusions.
2. Review every eligible canonical unit once; inherit only verified exact duplicates.
3. Assign one or more provisional candidate IDs and retain short evidence notes.
4. After each batch, compare new evidence with the cumulative map; merge labels only when definitions and inclusion/exclusion rules agree.
5. Preserve unresolved boundaries instead of forcing a premature decision.
6. Audit theme coverage across sources, times, groups, or parent documents so one dense source cannot define the map alone.
7. Separate substantive candidates from artifact candidates before estimating counts.

Do not use generated labels as evidence. The evidence is the linked corpus text and its distribution across independent units or parent documents. Labels are editable summaries.

## Candidate-theme map

Populate one row per candidate in `theme-candidate-audit.csv`. Use permanent provisional IDs such as `cand-main-...`; do not use bare sequential topic numbers as substantive identity. Each row must include:

- hierarchy level and optional parent candidate;
- route subset for mixed corpora;
- provisional label, definition, inclusion, and exclusion rules;
- theme type and relation to the user's mainline;
- independent support and evidence unit IDs;
- source or parent-document spread;
- duplicate or artifact risk;
- uncertainty and later user disposition.

Candidate IDs in the coarse and fine estimates must resolve to rows in this table. Parent IDs must also resolve. Artifact candidates must be listed in `excluded_artifact_candidate_ids` and must not be counted in either substantive estimate.

Use the hierarchy to avoid a false single answer. A coarse candidate can organize several fine candidates; it is not automatically more correct. Report both when the research question plausibly supports multiple levels.

## Topic-count estimate

Provide a lower bound, point estimate, and upper bound at both coarse and fine granularity:

- lower bound: defensible merges after resolving obvious aliases and overlapping labels;
- point estimate: the current best reading of substantively distinct recurring themes;
- upper bound: plausible splits whose boundaries remain unresolved but evidence is not merely idiosyncratic;
- candidate ID list: exact members counted by the point estimate;
- basis: corpus evidence, hierarchy decisions, uncertainty, and independent support.

The point estimate must equal the number of listed candidate IDs, and bounds must satisfy `lower_bound <= point_estimate <= upper_bound`. Exclude artifacts and one-off fragments. Do not invent a numerical range from a preferred BERTopic output size, paper, library default, or desired visual neatness.

The estimate is a navigation hypothesis. The later study contract may use it to define questions for sensitivity analysis and missing-theme audit, but not to preselect a target K. BERTopic's density-based structure is allowed to disagree.

## Route-specific handling

### Network and short text

Review exact-duplicate groups through a canonical unit and record `duplicate_inherited_unit_count`. Preserve multiplicity for prevalence analysis. Review every near duplicate independently or in a side-by-side group because a changed qualifier, target, link, or emoji can alter meaning. Keep platform artifacts as explicit artifact candidates so the user can see what was excluded.

### Long documents

Account for every eligible parent document under `parent_document_coverage`. Read natural sections or provisional semantic spans across the entire document, including appendices or references unless explicitly excluded. These reconnaissance spans are reading aids; they do not freeze the later `chunking_policy`. The final analysis unit remains a study-contract decision calibrated against encoder limits and thematic boundaries.

### Mixed corpora

Complete both unit-level and parent-document accounting where applicable. Mark `route_subset` on every candidate. Present shared candidates and route-specific candidates separately before proposing any aligned taxonomy.

## User preview and authorization gate

Present the reconnaissance before modeling in this order:

1. corpus fingerprint, route, and coverage accounting;
2. user's mainline and how it governed interpretation;
3. coarse and fine count estimates with uncertainty;
4. candidate hierarchy and relation to the mainline;
5. emergent themes, excluded artifacts, and unresolved boundaries;
6. strongest counter-evidence and limitations;
7. the exact choices the user can accept, reject, merge, split, defer, or reframe.

Create `modeling-authorization.json` with `gate_status: awaiting_user_direction` and `modeling_may_start: false`, then stop. This is an intentional workflow pause. Do not create embeddings, fit a baseline, start structural candidates, or register a modeling run while the gate is waiting or under revision.

After the user responds, record every candidate disposition in `theme-candidate-audit.csv` and capture the instruction verbatim or faithfully in the authorization artifact. Modeling may start only when:

- `gate_status` is `approved_for_modeling`;
- `modeling_may_start` is `true`;
- `authorization_id`, user instruction, decision timestamp, and all resolved candidate IDs are present;
- the authorization fingerprint and reconnaissance ID match the approved artifacts;
- every candidate has a disposition;
- the approval validator passes.

Link the same `authorization_id` from every baseline, structural, representation, taxonomy, and mapping row in `experiment-registry.csv`. If the corpus fingerprint, route, research question, user-theme mode, or resolved candidate map changes, return to reconnaissance or authorization as appropriate; never reuse a stale approval.

## Preview-versus-model audit

After candidate modeling, compare the selected taxonomy with the approved preview:

- preview candidates confirmed, merged, split, absent, or still unresolved;
- model-emergent themes not anticipated in the preview;
- user-mainline coverage and missing-theme evidence;
- artifact candidates that leaked into modeled topics;
- reasons for every material disagreement.

This audit evaluates discovery quality; it does not reward agreement for its own sake. A model that discovers grounded emergent themes may be better than one forced to reproduce the preview.

## Validation commands

Validate the completed preview before showing it to the user:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory>
```

After user approval, validate the modeling gate before any fit:

```text
python scripts/validate_theme_reconnaissance.py <study-bundle-directory> --require-approval
```

The full study-bundle validator also requires an approved gate for modeling runs:

```text
python scripts/validate_study_bundle.py <study-bundle-directory>
```

## Red flags

- calling a sample or truncated scan “full-corpus”;
- inheriting review across near duplicates;
- estimating one topic count without coarse/fine hierarchy or uncertainty;
- treating the user's theme as a closed vocabulary or mandatory cluster;
- counting platform, template, citation, or boilerplate artifacts as substantive themes;
- turning the preview estimate into `nr_topics` or target K;
- continuing to BERTopic before explicit user authorization;
- approving with unresolved candidate dispositions or a mismatched fingerprint;
- hiding preview-versus-model disagreements.
