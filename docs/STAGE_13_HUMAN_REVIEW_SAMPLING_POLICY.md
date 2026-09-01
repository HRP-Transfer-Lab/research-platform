# Stage 13 — Human Review Sampling Policy

**Status:** Adopted policy  
**Date:** 1 September 2026  
**Policy ID:** `stage13-study-review-sampling-v1`  
**Applies to:** machine-screened evidence batches intended for the 100–1,000-study working corpus

## 1. Decision

Routine human review must not become a paper-by-paper release gate.

For each machine-screened study batch:

```text
maximum human study-review budget
= ceiling(10% of eligible studies)
```

Examples:

```text
100 studies  → no more than 10 study reviews
300 studies  → no more than 30 study reviews
1,000 studies → no more than 100 study reviews
```

The remaining studies may enter the internal machine-screened working corpus when the automatic admission gates pass.

## 2. Review-budget allocation

The 10% study-review budget should combine representativeness with risk detection:

```text
50% stratified random sample
50% targeted risk/novelty sample
```

The exact split may be changed in a later version, but the total may not exceed 10% without an explicit one-off owner decision for a defined validation study.

### Stratified random half

Sample across important strata such as:

```text
study design
evidence class
intervention route
source kind
peer-review status
population/context family
parser version
model/prompt version
```

### Targeted half

Prioritise studies with:

```text
low field confidence
model disagreement
weak source anchoring
novel study design or taxonomy class
high recommendation usage
single-source recommendation dependence
prior recommendation correction
new parser/model/prompt cohort
```

## 3. What happens outside the 10% budget

A source that fails a machine gate is not automatically added to an unlimited human backlog.

Instead, the system should do one of the following:

```text
exclude the affected field from recommendation ranking
quarantine the source or model cohort
rerun parsing/extraction with a corrected pipeline
reduce its evidence-use tier
require CSI recommendation-level review when it materially affects a decision
withhold a public claim or authoritative synthesis
```

This preserves the review ceiling by fixing systematic pipeline problems rather than manually rescuing every record.

## 4. Release semantics

Two release concepts must remain distinct.

### Machine-screened working release

May contain the full automatically admitted batch. It must report:

```text
review_tier = machine_screened
sampling_policy_id
eligible_study_count
human_reviewed_study_count
human_review_rate
strata covered
sample error metrics
parser/model/prompt cohorts
known limitations
```

It must not be described as a human-approved evidence release merely because 10% was audited.

### Human-authoritative claim or synthesis release

Human authority attaches to the proposition, synthesis, claim or recommendation being approved. Only the reviewed evidence needed to justify that object should be promoted.

If the available reviewed evidence is insufficient, the claim is withheld or qualified. The default response is not to review the other 90% of the corpus.

## 5. Recommendation-level authority

The principal human-authority surface remains the CSI recommendation packet.

The reviewer may:

```text
approve
correct
reject
defer
abstain
```

A mis-recommendation should generate structured feedback. When the error appears to originate in a source extraction or classification, a sanitised correction signal is returned to the Registry and receives priority within a later targeted review sample.

An urgent faulty source may be suspended from recommendation use immediately without waiting for a complete human appraisal.

## 6. Batch acceptance rule

The human sample estimates whether the automatic pipeline is performing adequately.

If the sampled error rate exceeds a prespecified threshold:

```text
fail or quarantine the affected batch/stratum
→ correct parser, prompt, model, schema or rule
→ rerun the affected cohort
→ draw a new sample within the next review budget
```

Do not expand the same batch into universal manual review.

## 7. Dashboard requirements

The Evidence Operations Dashboard must show:

```text
eligible studies
10% review budget
reviews selected
reviews completed
random versus targeted allocation
sample coverage by stratum
sample error metrics
quarantined cohorts
machine-screened studies admitted
studies suspended from recommendation use
```

The CSI Recommendation Review Dashboard must show which evidence cards were:

```text
release-approved
human-reviewed
machine-screened
excluded or suspended
```

## 8. Compact rule

> **Review no more than 10% of studies as the routine quality sample. Use that sample to validate the machine pipeline; use human authority mainly at the recommendation, proposition and exception level; quarantine and repair failing cohorts rather than creating a 1,000-paper approval queue.**
