# Evidence Registry v1.1 — Stage 10 Harms, Fidelity, Dependence, Boundaries and Implementation

**Status:** IN PROGRESS  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`

## Goal

Represent safety, intervention delivery, support dependence, implementation burden and boundary conditions explicitly enough to support defensible EML5–EML7 decisions and later health-adjacent use.

The governing distinction is:

```text
BENEFIT / HARM RESULT
  !=
HARMS-ASSESSMENT COMPLETENESS
  !=
FIDELITY / ADHERENCE
  !=
SUPPORT / PROMPT DEPENDENCE
  !=
IMPLEMENTATION BURDEN / COST
  !=
BOUNDARY CONDITION
  !=
STUDY QUALITY / RoB
  !=
GRADE
  !=
EML
```

Stage 10 is additive. Existing free-text fields remain compatibility/source text.

---

## 1. Core scientific rules

### 1.1 No-reporting is not no-harm

The Registry must distinguish at least:

```text
not_yet_extracted
not_reported
not_systematically_assessed
systematically_assessed_no_harm_observed
harm_observed
not_applicable
```

A blank harms field must never mean `no harm`.

### 1.2 Harm is an outcome role, but adverse-event reporting is a separate evidence layer

Stage 4 already allows an outcome role of `harm`. Stage 10 adds the reporting/assessment architecture needed for adverse events and trade-offs that may not appear as ordinary efficacy outcomes.

Examples include:

```text
physical_adverse_event
psychological_worsening
performance_tradeoff
fatigue_or_burden
loss_of_autonomy_or_dependency
withdrawal_due_to_harm
serious_adverse_event
other_harm
```

### 1.3 Fidelity is not methodological quality

TIDieR-style reporting completeness, protocol fidelity, adherence and implementation integrity are not substitutes for RoB or study quality.

### 1.4 Prompt/support dependence is not Bridge success

A result obtained only while a prompt, coach, scaffold or AI assistant is present must remain distinguishable from unsupported deployment.

Support conditions should be representable as:

```text
continuous_scaffold
explicit_prompt
cue_triggered_support
human_coaching
AI_assistance
materials_or_tool_support
unsupported_or_autonomous
unclear
```

This layer complements, but does not replace, Stage 4 Bridge evidence.

### 1.5 Boundary conditions are evidence, not failure states

A result may be useful precisely because it identifies where an intervention does not generalise, where effects reverse, or where delivery requirements constrain portability.

---

## 2. Harms reporting status

Create a per-study harms-status object such as:

```text
study_harms_status
```

Minimum fields:

```text
study_id
extraction_status
assessment_mode
systematic_assessment nullable
notes
mapping_source
review_status
updated_at
```

Controlled `assessment_mode` should support:

```text
not_yet_extracted
not_reported
passive_or_incidental
systematic
unclear
not_applicable
```

The status object records the completeness/assessment context, not the substantive harm itself.

---

## 3. Harm / adverse-event observations

Create a typed child object such as:

```text
harm_observation
```

A harm observation may attach to:

```text
study
study arm nullable
outcome nullable
contrast nullable
```

Minimum fields:

```text
harm_observation_id
study_id
arm_id nullable
outcome_id nullable
contrast_id nullable
harm_type
harm_label
severity nullable
serious nullable
event_count nullable
participant_count nullable
withdrawal_due_to_harm nullable
systematically_assessed nullable
result_summary
evidence_basis
mapping_source
review_status
created_at
updated_at
```

Controlled severity should support at least:

```text
mild
moderate
severe
serious
unclear
not_applicable
```

`event_count = 0` is only valid when the record explicitly supports zero observed events under a defined assessment process.

---

## 4. Component implementation status

Create a per-component extraction-status object:

```text
component_implementation_status
```

Dimensions should be individually trackable rather than collapsed into one completeness flag:

```text
provider
materials_procedures
delivery_mode
fidelity
adherence
tailoring
modification
support_dependence
implementation_burden
cost_resources
```

Each dimension should support explicit missingness:

```text
not_yet_extracted
candidate_mapped
reviewed_mapped
reviewed_no_mapping
not_reported
not_applicable
```

---

## 5. Implementation observations

Create:

```text
component_implementation_observation
```

Minimum fields:

```text
implementation_observation_id
component_id
dimension
observation_kind
value_text nullable
value_numeric nullable
unit nullable
status_or_level nullable
evidence_basis
mapping_source
review_status
created_at
updated_at
```

This table can represent source-grounded facts such as:

```text
provider type
delivery channel
materials/procedures
fidelity percentage or qualitative level
adherence/completion
protocol modifications
tailoring
staff burden
participant burden
cost/resource requirements
```

The historical component fields remain visible as source text and can seed candidate observations only where their meaning is explicit.

---

## 6. Support / prompt dependence

Create a typed support-condition object, preferably result-aware:

```text
support_dependence_observation
```

Minimum fields:

```text
support_dependence_id
component_id nullable
outcome_id nullable
support_type
support_presence
support_requirement
autonomy_status nullable
evidence_basis
mapping_source
review_status
created_at
updated_at
```

Controlled support requirement:

```text
required
optional
removed_at_test
absent_at_test
unclear
not_applicable
```

Controlled autonomy status:

```text
scaffold_dependent
partially_independent
unsupported_demonstrated
autonomy_not_tested
unclear
```

This must not auto-assign Stage 4 Bridge evidence. A later human review may use the support-condition evidence when evaluating prompted, cue-triggered, changed-context, unprompted or delayed portability.

---

## 7. Boundary conditions

Create a generic but typed scientific boundary object:

```text
boundary_condition_observation
```

Minimum fields:

```text
boundary_condition_id
study_id
component_id nullable
outcome_id nullable
proposition_id nullable
boundary_dimension
boundary_direction
boundary_summary
evidence_basis
mapping_source
review_status
created_at
updated_at
```

Controlled boundary dimensions may include:

```text
population
context
baseline_state
dose_or_exposure
delivery
support_dependence
time_or_durability
transfer
performance_tradeoff
implementation
other
```

Stage 9 `context_fit_assessment` remains proposition-relative matching. Stage 10 boundary conditions record source-supported scientific limits or moderators; the two should not be merged.

---

## 8. Conservative seed boundary

Audit before any mapping:

```text
component.provider
component.delivery_mode
component.setting
component.tailoring
component.fidelity
component.prompt_status
component.protocol_json
study.sample_json
Stage 4 harm-role outcomes
outcome.result_summary / outcome_json
source.raw_record
```

The 18-source seed must not create a harm conclusion merely because harms are absent from the rapid review.

Expected principle:

```text
if explicit harms assessment is not present:
  harms status may remain not_yet_extracted or not_reported
  harm observations remain empty
```

Candidate implementation observations may be created only from explicit reviewed source fields.

---

## 9. Human approval boundary

AI may propose:

```text
candidate harms-reporting status
candidate harm type / severity
candidate fidelity/adherence extraction
candidate support-dependence interpretation
candidate implementation burden/cost extraction
candidate boundary condition
```

but all agent-generated scientific rows remain:

```text
mapping_source = agent_candidate
review_status = proposed
```

No agent candidate may self-promote to `approved`.

---

## 10. EML interaction

Stage 10 supplies structured evidence needed for higher EML decisions but does not automatically set EML.

### EML5

Transfer/durability evidence may be qualified by support dependence and boundary conditions.

### EML6

Real-world effectiveness requires authentic/routine context plus sufficient information on delivery/fidelity and practical functional outcomes.

### EML7

Scale-readiness requires implementation/generalisation evidence plus sufficiently characterised boundaries, fidelity, important harms and cost/resource considerations.

A high Stage 10 completeness state does not itself imply EML6/7.

---

## 11. Workbench requirements

For a selected source, show separately:

```text
HARMS REPORTING STATUS
HARM / ADVERSE-EVENT OBSERVATIONS

IMPLEMENTATION / FIDELITY
  provider
  delivery
  fidelity
  adherence
  tailoring/modifications
  burden/cost

SUPPORT / PROMPT DEPENDENCE
BOUNDARY CONDITIONS
```

The UI should visibly state:

```text
NOT REPORTED != NO HARM
FIDELITY != RoB
SUPPORT DEPENDENCE != BRIDGE SUCCESS
IMPLEMENTATION COMPLETENESS != EML
```

---

## 12. Validation targets

Minimum gates:

```text
orphan harm observations                         0
cross-study harm arm/outcome/contrast links      0
zero-event harm claims without assessment        0
harm rows inferred from blank source fields      0
non-delivery implementation subject leakage      0
invalid support-dependence subjects               0
agent candidates self-approved                    0
```

Regression gates:

```text
Stages 1–9 validators PASS
historical Registry validator PASS
CSI Gateway validator PASS
clean bootstrap PASS
Workbench build PASS
Supabase advisor gate PASS
```

The immutable `2026-08-23` release and `csi-evidence-v1` remain unchanged.

---

## 13. Implementation sequence

1. Audit current harm, fidelity, prompt, delivery, modification and burden/cost signals.
2. Lock harms-reporting missingness semantics.
3. Add study harms status + harm observation schema.
4. Add component implementation status + observation schema.
5. Add result/component support-dependence schema.
6. Add scientific boundary-condition schema.
7. Add integrity/human-approval guards, RLS and audit coverage.
8. Create conservative seed/status manifest and validator.
9. Apply only explicit candidate mappings supported by source fields.
10. Integrate deterministic replay into bootstrap.
11. Add Workbench reviewer.
12. Clean reset + full regression + build + advisors.
13. Record Stage 10 verification and mark the canonical tracker VERIFIED.

---

## Exit criteria

Stage 10 is VERIFIED only when:

- absence of harms reporting cannot be mistaken for evidence of no harm;
- harm observations have correct scientific subjects and explicit assessment context;
- fidelity/adherence/delivery/tailoring/modification/burden/cost are structurally representable;
- prompt/support dependence is distinct from Bridge success;
- boundary conditions are first-class scientific evidence;
- agent candidates remain human-review gated;
- higher EML decisions can query the structured Stage 10 evidence without Stage 10 auto-promoting EML;
- deterministic replay and Stages 1–9 regressions pass;
- the immutable `2026-08-23` release and `csi-evidence-v1` remain unchanged.