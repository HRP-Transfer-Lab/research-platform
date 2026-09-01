# Stage 12 — Stage 6 quantitative review recommendation

## Scope

Reviewed the committed `stage6_quantitative` packet at scientific revision `2553`.

- packet SHA-256: `7ccc2d15a1adefa62ab86a2445604ec00a958f0a8d2a49bce0af650ab11b4c1d`
- review units: 38
- decisions: 39
- surface: 38 quantitative-extraction status decisions + 1 effect-estimate decision

## Recommendation

- approve: **39**
- correct: **0**
- reject: **0**

## Scientific review notes

1. Thirty-seven outcomes are conservatively `not_yet_extracted`; this does not imply a null effect, no quantitative reporting, or non-applicability.
2. The `overall post-training working memory` outcome for `rt-2026-007` is correctly `partially_extracted`, because one pooled quantitative estimate is available while detailed synthesis/model information remains incomplete.
3. The historical estimate is faithfully preserved as Hedges' g = 0.191 with CI 0.062–0.320. The source record does not state the CI level, so `ci_level = null` is correct rather than assuming 95%.
4. `estimate_scope = source_level_synthesis` is appropriate because `rt-2026-007` is a systematic review and robust-variance meta-analysis rather than one Stage 5 trial contrast.
5. `contrast_id = null` is scientifically and structurally correct. Creating a Stage 5 contrast would fabricate a trial-level estimand that is not represented by this pooled synthesis.
6. `estimate_type = standardised_mean_difference`, `metric = Hedges_g`, `estimate_value = 0.191`, and the reported CI bounds match the immutable release seed.
7. `source_reported = true`, `adjustment_status = not_applicable`, and the neutral/metric-defined scale direction are conservative given the available seed.
8. Formal proposition/synthesis-outcome linkage is correctly deferred to Stage 8 rather than being inferred during Stage 6 review.
9. Mechanism, measurement and observational outcomes remain `not_yet_extracted` rather than `not_applicable`, preserving the possibility of later extracting their quantitative statistics.
10. No arm summaries, p-values, standard errors, sample sizes, model details or confidence levels are invented where the seed does not support them.

## Governance decision

The packet is suitable for governed human approval as-is. Approval should change review/provenance authority only and must not alter normalized scientific values, the historical `2026-08-23` release, or `csi-evidence-v1` Gateway state.
