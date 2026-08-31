# Stage 12 — Stage 4 outcome-distance review recommendation

**Status:** REVIEWED — APPROVAL RECOMMENDED  
**Branch:** `evidence-registry-v1.1`

## Scope

Human review of the 38 Stage 4 outcome-distance decisions for the immutable 18-source seed corpus.

The first generated `stage4_distance` packet was intentionally not approved because its Stage 11 candidate payload bound `distance_status` but did not explicitly include the single-valued `outcome_distance` field. The shared review-surface generator was corrected in commit `f6d1123b034939e1581aab2a0623233e60325d98` so regenerated distance candidates bind both `outcome_distance` and `distance_status`.

## Scientific boundary applied

The Stage 4 rules were preserved throughout review:

- outcome distance is orthogonal to time;
- `separate_measure` does not imply vertical transfer;
- `delayed` does not determine distance;
- `applied` may support `real_life_function` distance without establishing niche transfer;
- mechanism, measurement and observational evidence is not forced into intervention outcome-distance semantics;
- ambiguous legacy rungs remain unresolved rather than coerced.

## Review result

For the corrected, value-binding packet:

```text
approve: 38
correct: 0
reject: 0
```

Notable conservative decisions include:

- ambiguous `practice_or_nearest_transfer` / `practice_or_separate_measure` rows remain `not_yet_extracted`;
- measurement-review, mechanism and longitudinal-observational rows remain `not_applicable` where intervention distance is not scientifically meaningful;
- changed-format analogical/perceptual outcomes are kept distinct from transfer-axis approval;
- applied learning, writing and human-AI task outcomes may be `real_life_function` while transfer remains a separate question;
- delayed follow-up changes time semantics only and does not itself change distance.

No scientific-value correction is recommended.

## Approval boundary

Approval should occur only against a regenerated packet whose candidate payload visibly contains both:

```text
outcome_distance
distance_status
```

and whose packet/scientific-decision hashes validate against the current scientific revision.

The historical `2026-08-23` release and `csi-evidence-v1` Gateway remain unchanged.
