# Stage 13 — Scaled Evidence Ingestion and Recommendation-Level Governance

**Status:** Adopted architecture decision  
**Date:** 1 September 2026  
**Branch:** `stage13-scaled-ingestion`  
**Scope:** HRP Transfer Evidence Registry, Evidence Workbench, CSI Evidence Gateway and downstream CSI recommendation review

## 1. Decision

The 18-source seed established the ontology, candidate/authority boundary, review packet, release and Gateway machinery. It is a calibration set, not the intended operating pattern for every later paper.

At the 100–1,000-source scale:

> **Human approval is not a prerequisite for admitting every source, extraction or classification into the internal working corpus.**

Human authority is concentrated at four points:

1. **recommendation review** — where CSI converts evidence into an intervention option or bounded experiment;
2. **exception review** — where a source, field or classification is uncertain, contradictory or implicated in a mis-recommendation;
3. **promotion review** — where evidence is promoted into a public claim, approved synthesis, formal release or higher-stakes use;
4. **sampled quality assurance** — a risk-weighted audit sample used to estimate and improve machine performance.

This is a just-in-time governance model:

```text
AUTOMATE THE CORPUS
→ REVIEW THE DECISION
→ TRACE ANY ERROR BACK TO ITS EVIDENCE
→ CORRECT THE SOURCE OR RULE
→ IMPROVE THE NEXT DECISION
```

## 2. Evidence states

The pipeline must keep the following states distinct.

| State | Meaning | Human approval required to enter state? | Permitted use |
|---|---|---:|---|
| `discovered` | Candidate source identity/metadata found | No | Deduplication and acquisition queue |
| `acquired` | Full text or another source artifact registered and hashed | No | Parsing and provenance |
| `parsed` | Machine-readable text/structure created with quality metadata | No | Extraction input |
| `agent_extracted` | One or more model-generated field candidates stored with anchors and provenance | No | Validation and model comparison |
| `machine_screened` | Candidate passed automatic admission gates | No | Internal retrieval and draft/bounded CSI recommendation support |
| `human_reviewed` | Selected fields/source have durable human authority | Yes | Stronger recommendation support and promotion eligibility |
| `release_approved` | Included in a governed immutable evidence release or approved synthesis/claim | Yes | Public/production evidence contract and higher-assurance uses |

`machine_screened` is not a synonym for scientifically authoritative, peer reviewed, low risk of bias, high certainty or proven efficacy. It means only that the record passed the specified machine-quality gates and can be used under an explicit provisional-use policy.

## 3. Automatic admission gate

A source may enter the machine-screened working corpus without per-paper human approval only when all mandatory gates pass.

### 3.1 Identity and acquisition

- canonical identity resolved or a collision is explicitly flagged;
- DOI/PMID/arXiv/repository identifiers normalised where available;
- source artifact hash, media type, size and storage locator recorded;
- access/licence metadata recorded without credentials;
- duplicate and source-version checks passed.

### 3.2 Parse quality

- parser and parser version recorded;
- page/section structure available at the level required by the extraction;
- text coverage and corruption checks passed;
- tables/figures required for a claimed result are either parsed or marked unresolved;
- OCR-derived text is labelled separately from born-digital text.

### 3.3 Extraction quality

- output validates against the versioned extraction schema;
- every material extracted field carries a source anchor: page, section, table, figure or exact text span;
- unsupported fields are `null`/unknown rather than invented;
- controlled vocabulary values pass taxonomy checks;
- internal cross-field consistency checks pass;
- model, prompt, context, parameters and code versions are recorded.

### 3.4 Confidence and agreement

At least one of the following must apply for decision-relevant fields:

- two independent extraction passes agree;
- a model pass agrees with a deterministic rule or parser-derived value;
- a calibrated field-specific confidence threshold is passed;
- the field is retained but explicitly marked `needs_review` and excluded from recommendation ranking.

A single unanchored model assertion never passes the automatic gate.

## 4. Evidence-use policy

The existing approved CSI Evidence Gateway remains the high-assurance publication boundary.

### 4.1 Approved Gateway — unchanged

`csi-evidence-v1` remains:

- read-only;
- release-pinned;
- approved-release-only;
- free of person/session data;
- suitable for public and production CSI evidence provenance.

### 4.2 Internal Working Evidence Index — new

A separate authenticated working surface should expose machine-screened records for internal pilots and recommendation development. It must not silently masquerade as the approved Gateway.

Each working evidence card must include:

```text
source_version_id
review_tier
field_provenance
parse_quality
model_agreement
field_confidence
known_missingness
usage_policy
required_caveats
extraction_run_id
```

CSI evidence requests should state one of:

```text
approved_only
approved_plus_machine_screened
machine_screened_for_research_only
```

The resulting recommendation must report the composition of its evidence bundle.

Example:

```text
Evidence basis
- 4 release-approved cards
- 7 machine-screened cards
- 1 low-confidence field excluded
- no approved body-level synthesis available
```

## 5. Recommendation-level human authority

The primary scalable human-review object is the **CSI recommendation packet**, not the individual paper.

A recommendation packet should contain:

```text
recommendation_id
CSI vertical and version
valued goal / functional target
pressure point
competing constraint hypotheses
recommended route and protocol
alternative routes
bounded test / action
expected outcome
contradicting outcome
protected constraints
evidence query
bundle fingerprint
source/card IDs
review-tier composition
material evidence excerpts and anchors
model/rule versions
uncertainty and abstention rationale
```

The reviewer actions are:

```text
approve
correct
reject
defer
abstain
```

A review decision authorises or corrects that recommendation in that context. It does not automatically confer universal scientific authority on every source in the bundle.

## 6. When source-level human review is triggered

Source or field review becomes mandatory when any of the following applies:

1. a reviewer reports that a recommendation was wrong because evidence was mis-extracted or misclassified;
2. the recommendation depends materially on one machine-screened source;
3. local models disagree on a decision-relevant field;
4. parse quality, source anchoring or extraction confidence is below threshold;
5. the study design or intervention is outside the calibrated ontology/model range;
6. the recommendation concerns a health, employment, educational progression, safeguarding or other consequential decision;
7. the evidence is being promoted into an approved claim, synthesis, formal release or external publication;
8. the source is selected in a stratified random quality-assurance sample;
9. repeated recommendation feedback suggests systematic error for a model, taxonomy class or source family.

This converts human review from a universal queue into a targeted exception-and-promotion queue.

## 7. Recommendation feedback loop

Recommendation review and follow-up should generate structured feedback categories.

```text
correct_as_presented
partly_correct
wrong_route
wrong_protocol
wrong_constraint_locus
population_mismatch
context_mismatch
overstated_evidence
understated_evidence
missing_better_evidence
source_misclassified
source_mis_extracted
unsupported_inference
should_have_abstained
unnecessary_abstention
implementation_burden_missed
harm_or_tradeoff_missed
```

The CSI operational system stores the complete recommendation-review record. The scientific Registry does **not** receive personal, employee, client, workflow-session or other operational data.

Only a sanitised scientific correction signal may cross back into the Registry, containing the minimum required fields, for example:

```text
source_version_id
field_path
issue_type
current_candidate_value
suggested_candidate_value
evidence_anchor
reviewer_rationale
frequency/severity summary
originating model/rule versions
```

That signal enters as a new candidate or review-priority item. It never silently overwrites a reviewed value.

## 8. Risk-tiered recommendation governance

| Recommendation tier | Example | Evidence allowed | Human review timing |
|---|---|---|---|
| `R0_research` | internal retrieval, ontology testing, model evaluation | machine-screened | sampled/post hoc |
| `R1_bounded_low_risk` | reversible self-directed option or small organisational experiment | approved + machine-screened with caveats | sampled, exception-triggered, or reviewer-on-demand |
| `R2_sensitive` | health-adjacent, material organisational change, vulnerable population | approved evidence preferred; machine-screened only if visibly provisional | human review before action |
| `R3_consequential` | clinical, employment, eligibility, safeguarding or irreversible decision | approved evidence/claims only where applicable | authorised human decision required; CSI remains decision support |

No tier permits autonomous consequential action.

## 9. Quality assurance at scale

Human review should estimate system performance rather than merely create a growing approval backlog.

For each ingestion/model version, use:

- a fixed calibration set;
- a fresh held-out sample;
- a stratified random audit sample;
- all low-confidence/disagreement cases;
- all sources implicated in recommendation corrections;
- periodic rechecks after parser, prompt, model or taxonomy changes.

Track field-level metrics rather than one vague accuracy score:

```text
schema pass rate
identity/deduplication precision
evidence-anchor validity
field precision/recall/F1
controlled-vocabulary accuracy
unsupported-assertion rate
missingness accuracy
recommendation acceptance rate
recommendation correction rate
abstention calibration
error rate by route, population, design and model version
```

## 10. Dashboard architecture

### 10.1 Evidence Operations Dashboard — Evidence Workbench

Show:

- discovered/acquired/parsed/extracted/machine-screened/human-reviewed/release-approved counts;
- acquisition status, access blocks and retry queue;
- parser/model throughput and failures;
- extraction-schema pass rate;
- model disagreement and low-confidence queue;
- sources used most often in CSI recommendations;
- sources implicated in recommendation corrections;
- promotion and sampled-QA queues.

### 10.2 Recommendation Review Dashboard — CSI Surface

Show:

- pending, sampled and escalated recommendations;
- pressure point and competing hypotheses;
- primary and alternative routes;
- evidence-bundle composition and anchors;
- uncertainty, caveats and reason for escalation;
- approve/correct/reject/defer/abstain actions;
- feedback taxonomy;
- scheduled outcome re-check.

### 10.3 System Learning Dashboard

Show:

- recommendation acceptance/correction/abstention rates;
- error categories by route and model version;
- source/taxonomy fields most often corrected;
- recommendation outcomes after follow-up;
- candidate rule, prompt and model improvements;
- promoted authoritative evidence and claims.

## 11. Scaling milestones

### 18 → 100: calibration and economics

- build the local acquisition, parsing, extraction and embedding pipeline;
- benchmark local extraction against the existing calibration records;
- ingest a focused 50–100-source domain corpus;
- deploy the Evidence Operations Dashboard;
- implement recommendation packet fingerprints and reviewer feedback;
- estimate papers/day, failure rate and human minutes per recommendation.

### 100 → 300: retrieval and recommendation calibration

- add working evidence retrieval to internal CSI pilots;
- implement model disagreement/exception routing;
- run recommendation-level review and outcome feedback;
- create the first reviewed proposition/synthesis families;
- measure whether corrections propagate to improved later recommendations.

### 300 → 1,000: portfolio scale

- schedule continuous discovery/acquisition;
- maintain parser/model version cohorts;
- use risk-weighted sampled QA rather than universal paper approval;
- prioritise evidence by CSI demand, novelty, uncertainty and potential decision impact;
- promote only high-value source groups and syntheses into approved releases.

## 12. Non-negotiable boundaries

- Machine-screened evidence is never relabelled as human-approved.
- Recommendation approval does not automatically approve every source in its bundle.
- CSI user/person/session data does not enter the scientific Registry.
- Scientific corrections return through a sanitised candidate pathway.
- Public claims, formal syntheses and immutable releases retain explicit human authority.
- Consequential decisions retain authorised human ownership.
- The system must be able to abstain.

## 13. Compact operating rule

> **Do not require Mark to authorise 100–1,000 papers. Automate well-anchored evidence records, review the intervention decision, inspect the sources that actually matter or fail, and feed those corrections back into the evidence and recommendation system.**
