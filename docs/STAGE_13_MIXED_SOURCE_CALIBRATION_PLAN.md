# Stage 13 — Mixed-Source Calibration and First Scaling Gate

**Status:** Active implementation plan  
**Date:** 2 September 2026  
**Precondition:** `rt-2026-014` V4 same-source hybrid extraction calibration passed 10/10 with parser-owned spans  
**Purpose:** Move from a successful one-paper engineering calibration to a diverse calibration set and then a first 50–100-study machine-screened corpus.

## 1. What the V4 result establishes

The `rt-2026-014` V4 result establishes that the following architecture can work on the calibration paper:

```text
born-digital PDF
→ deterministic page-preserving parse
→ parser-owned evidence spans
→ task-sized retrieval
→ Qwen 3.5 4B semantic extraction
→ deterministic identifier and main-table count extraction
→ schema, anchor and semantic-support validation
```

Observed checkpoint:

```text
semantic fields             7/7
explicit deterministic      3/3
hybrid fields              10/10
span references            10/10
supported fields           10/10
schema                       pass
Registry/release/Gateway mutations 0
```

This is a same-source engineering pass. It is not evidence that arbitrary publications, layouts or study designs can yet be processed safely.

## 2. Next gate: mixed-source calibration

Target an initial **10-source calibration set** where lawful full text is available.

The set should be heterogeneous across:

```text
review bucket
study design
source kind
peer-review status
intervention versus mechanism versus human–AI evidence
PDF layout and table style
presence/absence of registration
presence/absence of participant-flow tables
presence/absence of numeric effect estimates
explicit missing fields
```

Preferred bucket coverage:

```text
3–4 direct-intervention sources
3 measurement/mechanism sources
3–4 human–AI activity-system sources
```

This is a one-off model/pipeline calibration set. It does not change the routine Stage 13 rule that no more than 10% of eligible machine-screened studies should receive source-level human QA.

## 3. Source acquisition sequence

```text
existing release records
→ read-only acquisition-state check
→ Unpaywall DOI lookup
→ Europe PMC DOI/PMID lookup
→ direct open-access candidate manifest
→ validate candidate identity, version and licence
→ download selected lawful full texts
→ SHA-256, page count and local-corpus registration
→ parse-quality check
→ mixed-source calibration
```

The discovery utility is:

```text
components/evidence-registry/scripts/stage13_discover_open_access.py
```

It performs no downloads and no Registry mutations.

## 4. Calibration labels and human workload

Do not require a full RoB appraisal for every calibration source.

Use three levels of reference labels:

### A. Deterministic reference fields

Examples:

```text
DOI/PMID/registration identifier
publication year
page count
sample counts tied to clearly identified main tables or flow text
intervention-arm labels
timepoint labels
```

These can be verified by ordinary software plus targeted inspection.

### B. Existing reviewed Registry fields

Use fields already represented in the approved 18-source seed, while recording whether the label came from full-text review, public metadata or rapid route review.

### C. Targeted human gold fields

Create a bounded gold set for decision-relevant semantic fields such as:

```text
study design
randomisation unit
analysis approach
intervention route
outcome family
transfer rung
population/context fit
explicitly unreported information
```

The calibration objective is to estimate field-level performance, not to create complete scientific authority for all ten papers.

## 5. Required metrics

Measure separately:

```text
schema validity
identifier accuracy
sample/arm/timepoint accuracy
semantic field precision/recall/F1
missingness accuracy
span-reference validity
semantic-support validity
unsupported-assertion rate
4B/9B disagreement
parse failure rate
runtime per source
retry rate
manual correction minutes
```

A single aggregate accuracy score is insufficient.

## 6. Promotion rule

The 4B-first pipeline may proceed to the first 50–100-source run only when:

```text
schema validity is near-perfect after bounded retry;
all admitted decision-relevant fields have valid parser-owned anchors;
unsupported assertions are below the prespecified ceiling;
missingness is represented explicitly;
no reviewed value can be silently overwritten;
error rates are acceptable within each tested stratum;
failures route to quarantine, exclusion or selective 9B review;
model/parser/prompt/schema provenance is reproducible.
```

A weak stratum is quarantined and repaired. It does not trigger manual review of the entire corpus.

## 7. First 50–100-source corpus

After mixed-source calibration:

```text
continuous metadata discovery
→ lawful full-text acquisition where available
→ parse and extraction workers
→ automatic admission or quarantine
→ machine-screened working evidence index
→ 5% stratified random QA
→ 5% targeted risk/feedback QA
→ recommendation-level review in CSI
```

Human authority remains concentrated on:

```text
CSI recommendations
promoted propositions/syntheses/public claims
consequential uses
sources implicated in mis-recommendations
bounded sampled QA
```

## 8. Dashboard work in parallel

The Evidence Operations Dashboard can be developed while mixed-source calibration proceeds. Its first vertical slice should show:

```text
source funnel: discovered → acquired → parsed → extracted → screened
access blocks and retries
parser/model cohorts
schema/anchor/support pass rates
quarantined records and reasons
10% review budget and allocation
throughput and latency
sources used in recommendations
sources implicated in corrections
```

The dashboard must distinguish:

```text
machine_screened
human_reviewed
release_approved
```

and must not imply that a machine-screened record has human scientific authority.

## 9. CSI integration gate

The existing approved Gateway remains unchanged for high-assurance release-pinned evidence.

A separately labelled authenticated working index may later expose machine-screened cards to internal CSI pilots. Every recommendation must preserve:

```text
evidence-use mode
bundle fingerprint
source/card IDs
review-tier composition
material evidence anchors
excluded low-confidence fields
model/rule versions
required caveats
abstention rationale
```

Recommendation approval authorises the recommendation in context; it does not automatically approve every paper in the evidence bundle.

## 10. Immediate sequence

```text
1. Record the rt-014 V4 calibration checkpoint.
2. Discover lawful OA candidates across the 18-source seed.
3. Select a heterogeneous 6–10-source set from available full texts.
4. Acquire, hash and register those source documents.
5. Generalise the parser/extractor from source-specific calibration profiles to reusable field families.
6. Run mixed-source calibration and estimate field-level error.
7. Add automatic screening/quarantine persistence.
8. Build the Evidence Operations Dashboard vertical slice.
9. Process the first 50–100 sources.
10. Connect the working evidence index to internal CSI recommendation review.
```
