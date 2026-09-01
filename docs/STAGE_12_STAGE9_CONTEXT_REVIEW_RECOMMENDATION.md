# Stage 12 — Stage 9 population/context review recommendation

## Scope

Reviewed the committed original `stage9_context` packet at scientific revision `2631`.

- original packet SHA-256: `af21c00c7e71c1271a24625c1b02f858e25c17cca23b883a7cdfc4e1917dc3bc`
- review units: 18
- original decisions: 121
- surface: study population/context terms and facet statuses plus component delivery-context terms/statuses

## Recommendation

- approve as scientific values: **119**
- correct: **1**
- reject: **1**

The original 121-decision packet must not be batch-approved as-is. It is retained as an audit artefact. After the governed correction below, the 119 remaining valid decisions should be regenerated in a new `stage9_context_corrected` packet bound to the new scientific-state revision.

## Required correction — rt-2026-015 geography

The original candidate includes:

- `study_population_context_term`: `pc_geo_china`, relationship `entire_sample`
- corresponding `study_population_context_status`: geography = `candidate_mapped`

The evidence basis is only that the population is described as **Chinese undergraduates**. This supports population/education/role descriptions but does not establish the geographic location of the study. Stage 9's own principles require geography to be explicit and forbid inference from indirect descriptors.

Governed resolution:

1. **Reject** the `pc_geo_china` term candidate and remove the normalized candidate term.
2. **Correct** the study-15 geography status to `not_yet_extracted`, with `mapping_source='human_review'` and `review_status='approved'`.
3. Remove the unsupported geography mapping from the Stage 9 replay manifest and make explicit that population nationality/ethnicity does not establish study geography.

## Scientific review notes for the remaining 119 decisions

1. Life-stage mappings are conservative and use `entire_sample` versus `includes_subgroup` appropriately; mixed young/older samples are not collapsed into one life stage.
2. Role and education facets remain distinct. University, middle-school and kindergarten contexts are mapped only where the reviewed seed explicitly establishes them.
3. Health-condition context is restricted to explicitly described healthy/nonclinical, learning-difficulties or comparable reviewed population descriptions; unmapped health facets remain unextracted.
4. Baseline cognitive status is used separately from health context, e.g. cognitively normal older adults.
5. Study setting is scoped independently from participant role and delivery context. Online, laboratory, school, university-classroom, community, controlled-research and evidence-synthesis settings are used only where supported by the reviewed seed.
6. Component delivery context is represented separately and only for the four explicit delivery mappings: guided cognitive training; researcher-facilitated tablet games; tablet-game delivery; and structured matching-to-sample task training.
7. No context-fit assessment is inferred from these descriptors.
8. Unmapped facets remain `not_yet_extracted`; absence of a mapped term is not interpreted as absence of that characteristic.

## Governance decision

Following the two-decision geography correction, the remaining 119 decisions are suitable for governed human approval as-is. Approval must change review/provenance authority only and must not alter normalized scientific values, the historical `2026-08-23` release, or `csi-evidence-v1` Gateway state.
