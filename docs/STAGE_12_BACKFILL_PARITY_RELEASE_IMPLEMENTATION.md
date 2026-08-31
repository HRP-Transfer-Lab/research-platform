# Evidence Registry v1.1 — Stage 12 Backfill, Parity and First v1.1 Release

**Status:** IN PROGRESS  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`

## Goal

Complete and review the 18-source v1.1 backfill, prove parity with the historical seed/Gateway boundary, and publish the first immutable v1.1 evidence release through the governed Stage 11 release-build path.

Stage 12 is the final gate before controlled corpus expansion.

The governing rule is:

> A new v1.1 release must contain reviewed normalized scientific state, not merely the historical raw seed records decorated with a new release ID.

---

## 1. Non-negotiable safety boundary

Stage 12 must not:

- mutate release `2026-08-23`;
- alter `csi-evidence-v1` without a deliberate version decision;
- promote agent candidates without human review;
- fabricate quality/RoB/GRADE/EML/harms/Bridge evidence;
- publish a release until deterministic export, parity and human-approval gates pass.

Publication is an explicit final operation, not a side effect of successful validation.

---

## 2. Stage 12 has four distinct jobs

```text
A. BACKFILL COMPLETENESS
What normalized v1.1 scientific state exists for the 18 sources?

B. HUMAN REVIEW CLOSURE
Which candidate mappings are accepted/rejected/corrected versus still proposed?

C. RELEASE REPRESENTATION + PARITY
Does the deterministic export contain the reviewed Stage 1–10 state and preserve historical/Gateway invariants?

D. GOVERNED PUBLICATION
Can a human owner approve and publish the first immutable v1.1 release through Stage 11?
```

These should not be collapsed into one “publish” step.

---

## 3. Backfill inventory

Audit all 18 sources across the verified architecture:

- Stage 1 route/evidence-role semantics;
- Stage 2 canonical source/version identity;
- Stage 3 application family, target and mechanism;
- Stage 4 outcome distance/time/transfer/role/Bridge dimensions;
- Stage 5 arms/components/contrasts;
- Stage 6 effect estimates;
- Stage 7 study quality and result RoB status;
- Stage 8 propositions/synthesis/body certainty/body EML;
- Stage 9 population/context/delivery mappings;
- Stage 10 harms/participation/implementation/support/boundaries;
- Stage 11 provenance/adjudication/authority state.

Explicit missingness remains valid scientific state.

---

## 4. Human-review closure

The deterministic seed backfills created in Stages 3–10 intentionally remain `agent_candidate / proposed` unless reviewed.

Stage 12 must classify every publication-relevant candidate into one of:

```text
approved
rejected
corrected / superseded
intentionally deferred from v1.1 release
```

The final release must not silently treat `proposed` as approved.

For large candidate sets, use a governed batch-review workflow only when the reviewer is explicitly shown the candidate set, evidence basis and proposed action. Batch review is a human operation, not agent self-approval.

---

## 5. Quality/RoB boundary

Stage 12 should perform initial formal appraisal on priority direct-intervention evidence where practical, but must not create superficial scores merely to make the release look complete.

Acceptable v1.1 state includes explicit:

```text
not_yet_assessed
insufficient_information
not_applicable
```

where appropriate.

GRADE remains body/outcome-level only.

---

## 6. Proposition/synthesis proof

Create at least one bounded test proposition/synthesis workflow only where the current 18-source evidence genuinely supports it.

This test should prove the architecture:

```text
proposition
→ contributing evidence
→ synthesis
→ synthesis outcome
→ body certainty status
→ body EML status
```

It must not create an inflated public claim merely to populate Stage 8.

A zero-public-claim v1.1 release remains legitimate if body-level claim maturity is insufficient.

---

## 7. Canonical v1.1 release export

The Stage 11 deterministic exporter must be extended/confirmed to serialize reviewed normalized scientific state relevant to a release.

At minimum the release snapshot should represent or hash-govern:

```text
source_version identity
source evidence roles/controllers
application-family mappings
target/mechanism mappings
study design + arm/contrast structure
outcome classifications
effect estimates
quality/RoB assessments or explicit statuses
population/context mappings
harms/implementation/support/boundary observations
proposition/synthesis objects if included
source-contribution EML
active Stage 11 field authorities
```

The exported representation may be normalized JSON rather than reproducing every database table literally, but it must be scientifically lossless for the approved v1.1 release state.

---

## 8. Historical parity

The historical seed remains the comparison anchor.

Verify:

```text
historical release: 2026-08-23 unchanged
historical source set: 18 reconstructable
historical source-version memberships: 18 unchanged
historical record-contribution EML: 18 unchanged
historical EML distribution: 1:7 / 2:10 / 4:1
historical Gateway cards: 18
historical Gateway claims: 0
historical Gateway contract: csi-evidence-v1
```

A new v1.1 release may contain more structured scientific information; parity means no accidental loss or semantic corruption of the historical boundary.

---

## 9. Gateway compatibility

Before publication verify that current CSI consumers continue to see the existing historical Gateway release exactly as before.

Publishing the first v1.1 Registry release does not automatically require publishing a new CSI Gateway release.

Preferred Stage 12 sequence:

```text
publish immutable Registry v1.1 release
→ verify it
→ decide separately whether/when to project it into a new Gateway publication
```

This prevents Registry release validation from silently changing downstream product behaviour.

---

## 10. Release identity

Do not guess the first v1.1 release ID during implementation.

The release ID should be selected only after:

- final backfill review is complete;
- export representation is fixed;
- deterministic hashes are stable;
- intended publication date/version semantics are clear.

The target release must not collide with `2026-08-23`.

---

## 11. Stage 12 audit before mutation

The first Stage 12 operation is read-only.

It should report:

1. historical release/Gateway parity baseline;
2. source/version identity counts;
3. proposed/approved/rejected counts across Stage 3–10 candidate tables;
4. quality/RoB assessment completeness;
5. Stage 8 proposition/synthesis counts;
6. Stage 11 authority counts;
7. existing draft/release builds;
8. whether current release serialization includes normalized v1.1 state;
9. publication blockers.

No review or publication action should occur until this audit is understood.

---

## 12. Publication blockers

A Stage 12 audit should treat the following as blockers unless explicitly resolved:

- unresolved publication-relevant agent candidates;
- deterministic export omits reviewed normalized scientific state;
- release build contains unreviewed source versions;
- release hashes are unstable;
- scientific state drifts after validation;
- historical parity regression;
- Gateway regression;
- Workbench build failure;
- Supabase advisor error;
- proposed body-level claims without sufficient reviewed evidence.

---

## 13. Final publication sequence

Only after all blockers are cleared:

```text
1. create release build
2. prepare / pin source versions
3. export canonical normalized scientific state
4. run full validators + parity suite
5. record deterministic state + manifest hashes
6. inspect release diff/manifest
7. human owner approves release build
8. human owner publishes release build
9. verify immutable evidence_release + memberships
10. commit immutable export/manifest to Git
11. rerun release hash verification from Git snapshot
12. leave CSI Gateway publication unchanged unless separately approved
```

---

## 14. Stage 12 exit criteria

Stage 12 is VERIFIED only when:

1. the 18-source v1.1 backfill is represented without loss;
2. publication-relevant candidate mappings have explicit human decisions or documented deferral;
3. explicit missingness is retained rather than fabricated completion;
4. initial quality/RoB state is represented honestly;
5. at least one bounded proposition/synthesis workflow has been proven if scientifically justified;
6. deterministic release export contains reviewed normalized Stage 1–11 scientific state;
7. unchanged state exports byte-identically with reproducible hashes;
8. the historical `2026-08-23` release remains unchanged;
9. `csi-evidence-v1` historical consumers remain reproducible;
10. a human owner approves and publishes the first immutable v1.1 Registry release;
11. the release export/manifest is committed as an immutable Git snapshot;
12. full validators, Workbench build and advisor gates pass after publication.

Only after Stage 12 verification may the Registry expand systematically from the 18-source seed toward hundreds or thousands of sources.
