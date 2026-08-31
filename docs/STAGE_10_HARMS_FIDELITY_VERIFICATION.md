# Evidence Registry v1.1 — Stage 10 Verification

**Status:** VERIFIED  
**Date:** 31 August 2026  
**Branch:** `evidence-registry-v1.1`  
**Verified implementation tip:** `17f25ba4db70577cd092ba8cc3dcff09da82bbdb`

## Scope

Stage 10 adds governed architecture for:

- harms and adverse-performance observations;
- harms-reporting completeness;
- participation flow;
- implementation and delivery observations;
- fidelity/adherence assessment subjects;
- support and prompt dependence;
- autonomy / unsupported testing;
- scientific boundary conditions;
- implementation burden and cost/resource fields.

The governing scientific separations are:

```text
harm outcome
!= harms-reporting completeness
!= participation flow
!= fidelity / adherence
!= support dependence
!= Bridge evidence
!= implementation burden / cost
!= boundary condition
!= RoB / study quality
!= GRADE
!= EML
```

## Migrations

- `20260831224500_evidence_registry_v1_1_harms_fidelity_implementation.sql`
- `20260831224600_tighten_stage10_harm_reporting_guards.sql`

The second migration enforces the critical missingness rule that `reviewed_no_harm_observed` is only valid after an explicitly systematic, human-approved harms assessment. It also prevents `event_count=0` from being used without explicit systematic assessment.

## Stage 10 scientific objects

The architecture provides:

- `harm_type_definition`
- `study_harms_status`
- `harm_observation`
- `study_participation_observation`
- `component_implementation_status`
- `component_implementation_observation`
- `component_reporting_assessment`
- `support_dependence_observation`
- `boundary_condition_observation`

TIDieR/component reporting therefore has a legitimate component-level subject without being conflated with study quality or result-level RoB.

## Conservative seed boundary

The immutable 18-source seed produces:

```text
harm types: 8
studies: 18
harms-status rows: 18
harm observations: 1
participation observations: 8
components: 13
implementation-status rows: 130
implementation observations: 4
support-dependence observations: 1
boundary observations: 3
component-reporting assessments: 0
```

The single candidate harm observation is:

```text
rt-2026-013
performance_tradeoff
memory test performance
```

It represents the explicit finding that immediate JOL prompting was null overall and could worsen difficult learning. It is not promoted into a general safety conclusion.

The seed deliberately retains:

```text
17 / 18 harms statuses = not_yet_extracted
0 reviewed-no-harm conclusions
0 fabricated zero-event harm observations
0 harm-withdrawal conclusions
0 fidelity observations
0 adherence observations
0 implementation-burden observations
0 cost/resource observations
0 TIDieR assessments
```

Unknown seriousness and harm-related withdrawal remain `NULL` rather than being encoded as false.

## Participation-flow boundary

The following reviewed sample-flow facts are represented independently of adherence:

- rt-2026-001: 54 randomised; 51 analysed
- rt-2026-006: 162 randomised; 138 completed
- rt-2026-009: 23 enrolled; 22 second-scan/follow-up assessed
- rt-2026-015: 180 entered; 168 completed

These facts do not imply non-adherence, withdrawal due to harm, or reasons for attrition.

## Implementation evidence

Four conservative implementation observations are retained:

- rt-2026-001 — guided cognitive training
- rt-2026-003 — researcher-facilitated tablet games
- rt-2026-004 — structured matching-to-sample training
- rt-2026-015 — explicit bounded-AI/open-AI/no-AI procedure structure and independent no-AI follow-up

No provider, fidelity, adherence, tailoring, burden or cost judgement is inferred where the reviewed seed does not establish it.

## Support dependence and Bridge boundary

rt-2026-015 records an explicit supervised no-AI outcome:

```text
support_type: ai_assistance
support_presence: absent
support_requirement: absent_at_test
autonomy_status: unsupported_demonstrated
```

This shows performance without AI at that test but does not establish spontaneous cue recovery or prompt fading.

Stage 10 therefore does not automatically create Stage 4 Bridge evidence.

Verified boundary observations are retained for:

- rt-2026-015 — independence/prompt-fading not demonstrated;
- rt-2026-016 — subjective effort and objective speed dissociate;
- rt-2026-018 — dependent versus autonomous offloading association is observational, not causal.

## Human approval boundary

All seed-derived Stage 10 scientific mappings remain:

```text
mapping_source = agent_candidate
review_status = proposed
```

No agent candidate is self-promoted to approved scientific evidence.

The Workbench allows explicit human review of candidate observations while deliberately avoiding a casual one-click `no harm` control.

## Workbench

Implemented:

- `apps/evidence-workbench/src/Stage10HarmsImplementationReview.tsx`
- integrated into `SourceDetailWithMaturity.tsx`

The reviewer visibly separates:

- harms assessment state;
- harm observations;
- participation flow;
- component implementation;
- reporting/fidelity assessments;
- support dependence;
- scientific boundary conditions.

## Deterministic replay

The Stage 1–10 local wrapper is:

`components/evidence-registry/scripts/bootstrap_local_registry_v1_1.py`

A clean replay completed successfully through:

```text
LOCAL REGISTRY V1.1 STAGES 1-10 PASS
```

The final verification sequence also passed:

- clean local Supabase reset/migration replay;
- Stage 1–10 deterministic bootstrap;
- Stage 10 manifest validation;
- Stage 10 database validation;
- Evidence Workbench production build;
- local Supabase advisor gate with `--fail-on error`.

## Compatibility

Stage 10 does not mutate:

- immutable evidence release `2026-08-23`;
- source-level record-contribution EML;
- Stage 4 harm-role classifications;
- Stage 4 Bridge evidence;
- Stage 7 RoB/quality boundaries;
- Stage 8 GRADE/body-EML authority;
- `csi-evidence-v1`.

## Verification decision

**Stage 10 is VERIFIED.**

The Registry can now structurally represent the harms, fidelity, support-dependence, autonomy and implementation information required for higher evidence-maturity reasoning without interpreting missing evidence as favourable evidence.

The next implementation stage is:

**Stage 11 — extraction/adjudication provenance and deterministic review → release authority.**
