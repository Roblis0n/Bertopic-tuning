# Scalable Corpus Extraction and Reading

## Contents

- Purpose and governing distinction
- Choose the reading mode
- Freeze the source frame
- Build bounded reading representations
- Select evidence through independent channels
- Run the adaptive reading loop
- Audit an independent holdout
- Record the ledger and accounting
- Handle each corpus route
- Build candidate themes without overstating coverage
- Authorize modeling
- Common mistakes and red flags

## Purpose and governing distinction

Use this protocol when direct semantic review of every eligible unique-content unit would exceed the registered time or context budget. Reduce prompt load without pretending that a selected subset is complete full-text coverage.

Keep three claims separate:

| Claim | Required evidence |
|---|---|
| Full-corpus census | Every source unit has a stable ID, parse status, fingerprint, route, metadata profile and ledger row |
| Semantic review coverage | The ledger identifies which units were read as full text, read through an extracted representation, inherited from an exact duplicate, or not semantically reviewed |
| Complete full-text review | Every eligible canonical unit was read in full; extracted cards and unreviewed units both equal zero |

`progressive_extraction` may support a transparent pre-model preview and user authorization. It may not be described as complete full-text review, proof that no rare theme exists, or a census estimate of theme prevalence.

## Choose the reading mode

Estimate the token load of eligible unique content after exact-duplicate registration. Reserve context for the cumulative codebook, contradiction review, candidate synthesis, reporting and audit. Record the available time separately.

Choose:

- `direct_full_text` when every eligible canonical unit can be read without truncation inside the registered resource envelope;
- `progressive_extraction` when full-text reading is infeasible, or when completing it would crowd out synthesis and audit.

Do not use a universal row-count, token-count or sampling threshold. Record the target-corpus estimate, usable budget, time budget, feasibility decision and reason in `corpus-reading-plan.json`.

Do not silently switch modes. A changed mode changes the evidence claim and invalidates an authorization that points to the old reading plan.

## Freeze the source frame

Before semantic reading:

1. Freeze source order, stable unit and parent IDs, route subsets, corpus fingerprint and exclusions.
2. Scan inputs lazily or in bounded batches. Do not paste whole tables, folders or documents into one prompt.
3. Record schema, text fields, source, time, language, group keys, content length, parse status and raw-text locator for every source unit.
4. Register SHA-256 for every unit. An exact duplicate may inherit only when its nonblank `duplicate_group_id`, `content_sha256` and `content_length` all equal one semantically reviewed canonical row; one content hash maps to one canonical. Keep multiplicity for any later, separately designed probability study.
5. Mark near duplicates for comparison; never inherit their interpretation automatically.
6. Preserve raw text outside the prompt and store only stable locators in the ledger.

The census layer may use deterministic parsing, hashing, counts, lexical sketches and metadata summaries. These are selection aids, not candidate-theme evidence until a human or agent actually reads the linked text or reading representation.

## Build bounded reading representations

Create a compact, traceable unit card for selection and first-pass review. Register every source/card artifact in `extraction.registered_artifacts` as an in-bundle `artifact_path` and verified whole-file `artifact_sha256`; do not impose one universal card length.

Include, when available:

- stable unit and parent IDs;
- source, time, language, group and length strata;
- title, heading path or conversational context;
- traceable text spans with raw offsets or record locators;
- registered `extraction_artifact`, scheme-qualified `extraction_locator`, bounded `span_start`/`span_end`, and `extraction_sha256` that matches the exact reviewed bytes in the registered file;
- user-anchor matches and nearby context;
- locally unusual or rare lexical spans;
- duplicate and artifact indicators;
- extraction warnings and omitted-material description.

For short text, use the complete text when it is already compact. For long documents, distribute spans across natural sections and document positions; include late sections, conclusions, limitations, appendices and contradictory passages when they are eligible. Never treat a title, abstract, first page or head-only excerpt as a whole-document representation.

Generated summaries may aid navigation, but they must retain links to source spans and may not be the sole evidence for a candidate theme whose boundary, stance or rarity matters.

For `full_text`, the registered span must start at zero, end at `content_length`, and use the same SHA-256 as the content. For `extracted_representation`, the span must be nonempty and remain within the registered content boundary; its extraction hash identifies the exact card or span that was read. A nonempty string such as `x` is not a locator.

## Select evidence through independent channels

In `progressive_extraction`, maintain all five channels. One unit may enter through several channels.

| Channel | Purpose |
|---|---|
| `coverage_strata` | Rotate across route, source, time, language, group, length and document-position strata so dense sources cannot dominate |
| `user_anchor` | Retrieve direct, adjacent, contradictory and negative evidence around the user's research mainline |
| `lexical_novelty` | Surface rare terms, new phrases, low-frequency combinations, temporal bursts and tail patterns without declaring them themes |
| `probability_holdout` | Preserve a probability-selected audit set that was not used to build the candidate map |
| `uncertainty_escalation` | Add units that challenge definitions, merges, splits, artifacts, stance or source-specific interpretations |

Define strata only from available target-corpus fields. Collapse unusably sparse intersections transparently, but never drop a route, language, source or period merely because it is inconvenient.

Do not choose a fixed universal sample size. Generate the next batch from unresolved coverage cells, novel evidence and candidate uncertainty. Record the generation rule before reading each extension.

## Run the adaptive reading loop

1. Read an initial rotation across every observable coverage stratum and the user-anchor queue.
2. Assign provisional candidate IDs, evidence notes and inclusion/exclusion rules only to reviewed material.
3. Compare each batch with the cumulative candidate hierarchy.
4. Add lexical-novelty and contradiction queues; inspect rare or disconfirming units before adding more common examples.
5. Escalate a unit from extracted representation to full text when stance, boundary, novelty, sensitivity, internal contradiction or omitted context could change interpretation.
6. Recompute uncovered strata and unresolved candidate boundaries.
7. Continue until the registered stopping rule is satisfied, then open the untouched probability holdout.

Treat incremental candidate yield as one diagnostic, not an automatic saturation claim. A declining yield in convenience-selected material does not establish coverage.

## Audit an independent holdout

Keep the probability holdout unavailable to candidate construction until the provisional map and definitions are frozen for that audit round.

Use it to test:

- discovery of new candidate themes;
- changed inclusion or exclusion rules;
- candidate merges or splits;
- missed artifacts or source-specific meanings;
- under-covered languages, periods, groups or document positions.

If the holdout materially changes the map under the registered decision rule, set the decision to `expand_reading`, add evidence through the relevant channels and repeat with a fresh holdout. Stop only when the local rule is satisfied and record `stop_with_residual_risk` plus the evidence and remaining uncertainty.

Use `holdout_role` to keep audit state explicit:

- `none`: ordinary development or coverage evidence;
- `development_released`: a previous holdout that changed the map, was released into development, and is no longer independent;
- `final_independent`: the untouched holdout used for the current stopping decision.

Before release, fingerprint the frozen `theme-candidate-audit.csv` and the sorted final-holdout unit frame. Record them as `stopping.candidate_map_freeze_sha256` and `stopping.holdout_sampling_frame_sha256`, assign a nonblank `holdout_audit_round_id`, and repeat all three values on every `final_independent` ledger row. `stopping.holdout_unit_count` must equal the number of those rows, and row-level new-theme/material-change outcomes must reconcile with the stopping record. Mixed corpora require a final-independent holdout and all five channels inside each concrete route subset, not merely in the corpus-wide union. Holdout rows may record observations in `review_notes`, but they cannot carry candidate IDs, use adaptive candidate-selection channels, or appear in the frozen candidate map's `evidence_unit_ids`. If they produce any new candidate or another material map change, record `material_change_detected: true`, expand reading, release evidence only as `development_released`, and draw a fresh final holdout. `stop_with_residual_risk` requires `new_candidate_theme_count: 0` and `material_change_detected: false`.

A completed preview must record `reconnaissance_state: complete_for_preview` and `resource_budget_exhausted: false`. Direct review uses `termination_basis: complete_full_text_review`; progressive review uses `termination_basis: local_holdout_rule_satisfied`. The free-text estimand, rule and evidence cannot cite time, token, quota, deadline or budget exhaustion as their basis.

If the registered time, token or review budget is exhausted first, record `reconnaissance_state: interim` and `resource_budget_exhausted: true`, report an incomplete reconnaissance, and leave modeling disabled. Do not use resource exhaustion as stopping evidence, relabel it `stop_with_residual_risk`, or seek modeling authorization.

Do not recycle a holdout into development evidence and continue calling it independent.

## Record the ledger and accounting

Create exactly one `corpus-reading-ledger.csv` row per globally unique source `unit_id`. Validate uniqueness with a disk-backed index or an equivalent external-memory method rather than loading millions of IDs into prompt context. Keep content hash/length, duplicate group/canonical, selection/holdout, review depth, registered artifact, locator, span bounds, extraction hash and final-holdout binding fields in the same auditable row. The validator opens each registered artifact, verifies its whole-file hash, checks span bounds and hashes the exact reviewed bytes. An `exact_duplicate_inherited` row must pass the hash/group/length checks and point to an existing canonical row whose depth is `full_text` or `extracted_representation`. Use exactly one `review_depth`:

| Review depth | Meaning |
|---|---|
| `full_text` | Eligible canonical content was read in full |
| `extracted_representation` | A traceable bounded card or set of source spans was read |
| `not_semantically_reviewed` | Unit was censused but not read semantically |
| `exact_duplicate_inherited` | Interpretation points to a reviewed exact-content canonical unit |
| `excluded` | Unit was excluded under the recorded rule |
| `failed` | Unit could not be parsed or read; repair before presenting a valid preview |

Maintain these equations:

```text
source_unit_count = eligible_unit_count + excluded_unit_count
profiled_source_unit_count = source_unit_count
reviewed_unit_count = full_text_reviewed_unit_count
                    + extracted_representation_reviewed_unit_count
eligible_unit_count = reviewed_unit_count
                    + duplicate_inherited_unit_count
                    + unreviewed_unit_count
                    + failed_unit_count
failed_unit_count = 0
```

Set `accounting_complete: true` only when the census, row count, unique ID count and depth counts reconcile. Set `full_text_review_complete: true` only when extracted, unreviewed and failed counts are all zero. Apply the analogous accounting to parent documents for long and mixed routes. Long-document ledger rows must retain `parent_document_id`; declared profiled and semantically reviewed parent counts must equal the corresponding distinct parent IDs derived from the long-document ledger subset.

Candidate `evidence_unit_ids` may point only to `full_text` or `extracted_representation` rows. Use the reviewed canonical unit rather than an inherited duplicate as evidence.

## Handle each corpus route

### Network-short

- Read compact selected texts in full when possible.
- Preserve account, thread, community, source, repost, time, hashtag, URL and emoji context in cards.
- Place near-duplicate differences, coordinated slogans, templates and temporal bursts into uncertainty or artifact queues.
- Keep a probability holdout across duplicate families and analytic groups, not isolated rows that leak the same event or campaign.

### Long-document

- Census every parent document and its natural section paths without freezing later modeling chunks.
- Stratify by source, time, type, length and within-document position.
- Build cards from distributed traceable spans, not head-only truncation.
- Escalate the entire relevant section or document when local spans cannot establish stance or boundary.
- Measure independent support by parent document, not raw span count.

### Mixed

- Use `network-short` or `long-document` as the concrete `route_subset` on every ledger row; never write `mixed` as a row subset, and require both subsets to be present.
- Maintain separate depth, parent, channel and holdout summaries by route subset within the same artifacts.
- Run semantic review, every required channel and an independent final holdout in each route subset.
- Report shared and route-specific candidates separately before any taxonomy alignment.

## Build candidate themes without overstating coverage

Base candidate definitions on reviewed evidence only. Report source-frame distribution from the census separately from theme evidence distribution in the selected review set.

For every preview, state:

- reading mode and feasibility basis;
- census counts and semantic-review counts by depth;
- selection channels and strata;
- full-text escalations;
- holdout result and stopping decision;
- residual risks, including themes without lexical cues and unreviewed subgroups;
- that coarse/fine counts remain `pre_model_hypothesis_not_target_k`.

Every candidate row must state `prevalence_claimed: false` and `claim_scope: semantic_evidence_only`. Numeric percentages or unqualified prevalence/frequency/proportion claims are rejected. If prevalence is later needed, create a separate probability study with validated frame coverage, inclusion probabilities and weights; the adaptive reconnaissance gate does not authorize it.

## Authorize modeling

Show `corpus-reading-plan.json` and the reconciled coverage summary with the theme preview. Leave `progressive_reading_risk_acknowledged: false` while awaiting user direction.

For `progressive_extraction`, modeling may start only after the user sees the semantic-review denominator, holdout evidence and residual risk, then the authorization records `progressive_reading_risk_acknowledged: true`. This acknowledgement permits modeling under the declared uncertainty; it does not convert partial review into complete full-text coverage.

After candidate dispositions are recorded, calculate `pre_model_artifact_fingerprint` over `corpus-profile.json`, `corpus-reading-plan.json`, `corpus-reading-ledger.csv`, `theme-reconnaissance.json` and `theme-candidate-audit.csv`, and store it in `modeling-authorization.json`. Recompute and renew authorization after any change to those files; matching IDs alone are insufficient.

## Common mistakes and red flags

- using a fixed row threshold or universal sample size;
- loading an entire large file into the prompt instead of streaming fields and locators;
- calling a metadata scan or lexical sketch semantic review;
- calling selected evidence “full-corpus reading”;
- omitting `not_semantically_reviewed` units from the denominator;
- selecting only frequent, early, mainline-matching or easy-to-parse material;
- using one source, language or period to define the candidate map;
- treating generated summaries as source evidence without traceable spans;
- opening the holdout before freezing the audit-round map;
- stopping at apparent saturation without a registered estimand and decision rule;
- writing budget exhaustion into a nominally satisfied stopping rule;
- using an unregistered artifact, unbounded locator or unverifiable extraction hash;
- inheriting an exact duplicate from a different content hash or duplicate group;
- satisfying mixed-route channels only in one subset;
- asserting prevalence from adaptive candidate evidence;
- approving progressive reading without explicit residual-risk acknowledgement;
- interpreting a progressive preview as proof that an absent or rare theme does not exist.
