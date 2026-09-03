# Stage 13 Health / Clinical-Adjacent Psychology Scope Gate

**Status:** Active for the three-domain overnight pilot  
**Date:** 3 September 2026  
**Branch:** `stage13-scaled-ingestion`

## Decision

The `health_clinical_adjacent` CSI evidence domain is restricted to **psychology-related intervention evidence**.

A paper qualifies only when its intervention content or principal intervention mechanism is explicitly one or more of:

```text
psychological
cognitive
behavioural
motivational
self-regulatory
psychosocial
neuropsychological
```

A paper does not qualify merely because it concerns:

```text
a medical condition or patient group
a healthcare pathway or service
occupational therapy in general
physical rehabilitation
adherence or participation
functioning or disability
quality of life or wellbeing
a digital health service
```

These contexts and outcomes may be relevant only when the intervention itself has an explicit psychology-related component.

## Explicit negative example

The following title is a regression-test exclusion:

> Occupational Therapy Services Provided to Adults Diagnosed With Kidney Disease: A Scoping Review

It is a general health/rehabilitation service review unless the title or abstract identifies a central psychological, cognitive, behavioural, motivational, self-regulatory, psychosocial or neuropsychological intervention component.

## Positive examples

```text
Cognitive behavioural therapy for chronic primary pain
Motivational interviewing for health-behaviour adherence
Cognitive rehabilitation after traumatic brain injury
Mindfulness-based stress management in cancer survivorship
Digital psychological self-management for persistent symptoms
Behavioural activation for depression
```

## Two-gate architecture

### Gate 1 — before Ollama

```text
raw discovery candidates
→ query-origin inspection
→ title/abstract psychology centrality test
→ exclude failed health-only candidates
→ remove failed health query hits from cross-domain candidates
→ balanced strict discovery manifest
```

This prevents general medical papers from consuming local-model classification time where possible.

### Gate 2 — after Ollama

```text
raw three-domain classifications
→ re-evaluate every health-domain assignment
→ retain explicit psychology-related health evidence
→ remove unsupported health labels where another domain remains
→ exclude unsupported health-only classifications
→ rebuild strict ranked CSV and full-text portfolio
```

The raw model outputs remain preserved for audit. Only the strict outputs are used as the full-text acquisition hand-off.

## Files

```text
components/evidence-registry/config/
  stage13_health_psychology_scope_policy.v1.json

components/evidence-registry/scripts/
  stage13_health_psychology_scope.py
  stage13_enforce_psychology_health_classifications.py
  stage13_run_overnight_three_domain_pilot.py
  test_stage13_health_psychology_scope.py
```

## Required terminal indicators

The strict discovery stage reports:

```text
candidate_excluded_before_llm|...
OLLAMA_CALLS|0
STAGE 13 HEALTH PSYCHOLOGY SCOPE GATE|PASS
```

The final enforcement stage reports:

```text
health_scope_violations|0
STAGE 13 PSYCHOLOGY-ONLY HEALTH ENFORCEMENT|PASS
```

The final run reports:

```text
HEALTH_SCOPE|PSYCHOLOGY_RELATED_ONLY
REGISTRY_MUTATED|0
SCIENTIFIC_STATE_MUTATED|0
HISTORICAL_RELEASE_MUTATED|0
CSI_GATEWAY_MUTATED|0
MACHINE_SCREENED_STATUS_CREATED|0
HUMAN_AUTHORITY_CREATED|0
```

## Governance interpretation

This is still abstract-level candidate screening. Passing the scope gate means only that the paper is sufficiently psychology-related to enter the full-text acquisition queue. It does not establish efficacy, methodological quality, risk of bias, certainty, transfer, clinical effectiveness or recommendation authority.

Health and clinical-adjacent recommendations remain subject to the stronger evidence, claims and authorised-human boundaries of the later CSI recommendation layer.
