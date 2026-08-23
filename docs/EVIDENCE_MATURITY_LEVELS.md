# HRP Evidence Maturity Level (EML) v1

**Status:** operational scientific framework v1  
**Scale version:** `hrp-eml-v1`  
**Purpose:** provide one simple ordinal signal for how far an evidence proposition has progressed from rationale to replicated, transferable, real-world and scalable support.

## Why a new maturity scale is needed

No single established psychology, cognitive-science or social-science framework cleanly spans all of the following in one ordinal scale:

```text
mechanistic / theoretical rationale
→ adjacent paradigm or mechanism evidence
→ first direct demonstration
→ replication
→ multi-study synthesis
→ transfer / durability
→ real-world effectiveness
→ generalisation / scale-up
```

The HRP scale therefore **derives its stages transparently from established standards**, rather than presenting itself as an external consensus standard.

Important anchors:

- Society for Prevention Research standards for efficacy, effectiveness, replication and scale-up: Gottfredson et al. (2015), *Prevention Science*, https://doi.org/10.1007/s11121-015-0555-x
- Chambless & Hollon (1998) on possibly efficacious versus established efficacy and the importance of independent replication: https://pubmed.ncbi.nlm.nih.gov/9489259/
- NIH Stage Model for Behavioral Intervention Development: https://www.nia.nih.gov/research/dbsr/nih-stage-model-behavioral-intervention-development
- Society of Clinical Psychology / Tolin et al. treatment-evidence criteria: https://societyofclinicalpsychology.org/resources/psychological-treatments/
- GRADE certainty-of-evidence methods for a body of evidence: https://training.cochrane.org/handbook/current/chapter-14
- ESSA evidence tiers: https://ies.ed.gov/sites/default/files/ies/document/2024/10/ESSA%20Tiers%20of%20Evidence.pdf
- Oxford Centre for Evidence-Based Medicine Levels of Evidence: https://www.cebm.ox.ac.uk/files/levels-of-evidence/cebm-levels-of-evidence-2-1.pdf

## EML is maturity, not methodological quality

EML answers:

> **How far has this proposition progressed through the evidence-development pathway?**

It does **not** answer:

> How trustworthy is this particular study?

or:

> How certain are we that the body-level effect estimate is correct?

Those remain separate:

```text
EVIDENCE MATURITY (EML)
progress through rationale → demonstration → replication → transfer → effectiveness

+

STUDY QUALITY / RISK OF BIAS
RoB 2 / ROBINS-I / reporting and other design-specific appraisal

+

BODY-LEVEL CERTAINTY
GRADE or another justified synthesis-level certainty framework

=

DECISION SUPPORT
```

A high EML does not rescue a low-quality evidence body. Conversely, a rigorous mechanistic study may be high quality while remaining EML1 for an intervention claim.

## The scale

| Level | Label | Meaning |
| --- | --- | --- |
| **EML0** | Rationale only | Theory, mechanism or logic-model rationale; no direct empirical support for the target proposition. |
| **EML1** | Mechanism / paradigm support | Empirical mechanism, construct, measurement or adjacent-paradigm support, but no credible direct demonstration of the target proposition. |
| **EML2** | Initial direct demonstration | At least one credible direct empirical test demonstrates the target intervention, mapping or activity-system effect under defined conditions. |
| **EML3** | Replicated efficacy | The direct effect has been reproduced across at least two rigorous studies with consistent direction; independent replication is preferred and must be recorded where present. |
| **EML4** | Convergent body | A systematic synthesis or equivalent reviewed multi-study body supports the proposition; body-level quality/certainty is still separately appraised. |
| **EML5** | Transfer & durability | The convergent body also demonstrates cumulative portability beyond the practised format and/or durability after delay for the target claim. |
| **EML6** | Real-world effectiveness | Useful outcomes are demonstrated under authentic/routine conditions with appropriate fidelity and functional outcomes. |
| **EML7** | Generalised / scale-ready | Evidence supports relevant multi-setting/population generalisation and implementation/scale decisions, with boundary conditions, fidelity, harms and important cost/implementation considerations sufficiently characterised. |

## Cumulative rule

EML is intentionally cumulative.

For example:

```text
one direct experiment
+ delayed follow-up
+ far-transfer outcome
```

does **not** automatically equal EML5.

If the proposition has not yet been replicated and synthesised, it remains EML2 while receiving separate transfer/delayed evidence tags.

This prevents a single exciting far-transfer result from appearing more mature than a replicated but narrower literature.

## Two scopes

### `record_contribution`

Used for an individual source.

It means:

> What maturity-stage contribution does this source make to the relevant proposition?

Examples:

- mechanistic fMRI study → often EML1 contribution;
- direct randomized intervention trial → often EML2 contribution;
- systematic review/meta-analysis → potentially EML4 contribution.

It does **not** mean the entire intervention or product has that maturity.

### `body_of_evidence`

Used for a reviewed synthesis or approved claim.

This is the preferred maturity signal for CSI recommendations once a body-level synthesis exists.

A production CSI should prefer:

```text
approved body-level EML
```

and only fall back to displaying matched source-contribution EMLs when no approved body-level claim exists.

## Review statuses

```text
provisional_seed
reviewed
approved
```

Initial automatic/seed mappings are never silently treated as approved scientific judgments.

## Visual system

The Workbench and CSI surfaces use ordinal EML badges with both text and colour. Colour is supplemental and must never be the only carrier of meaning.

```text
EML0  neutral
EML1  blue
EML2  indigo
EML3  teal
EML4  emerald
EML5  green
EML6  lime
EML7  gold
```

## CSI display rule

When a CSI recommendation has no approved body-level synthesis:

> **Evidence maturity:** body-level rating not yet available. Matched reviewed sources currently contribute at EML1–EML2.

Do not display the maximum matched study EML as though it were the certainty or maturity of the recommendation itself.

When an approved body-level claim later exists, CSI may display:

```text
EML5 · Transfer & durability
GRADE: Moderate certainty
```

with drill-down to supporting evidence and caveats.

## Current 2026-08-23 seed mapping

The first 18 Gateway cards are conservatively seeded as **provisional source contributions**:

- EML1: mechanism, measurement or observational/activity-system evidence without a direct intervention demonstration;
- EML2: direct intervention/activity-system demonstrations;
- EML4: the existing systematic review/meta-analysis contribution.

No EML3, EML5, EML6 or EML7 **body-level** rating is currently asserted. The Evidence Workbench should be used to review these provisional mappings and later create explicit synthesis/claim ratings.
