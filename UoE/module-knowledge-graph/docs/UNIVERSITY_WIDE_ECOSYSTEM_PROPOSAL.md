# Proposal: University-Wide AI Module Engineering and Course Intelligence Ecosystem

## Executive Summary

Universities are rapidly adopting generative AI, but most current uses remain fragmented: individual lecturers use AI to draft teaching materials, students use general-purpose models for study support, and institutions experiment separately with assessment design, curriculum mapping, quality assurance and learning analytics.

This proposal outlines a different approach: a **university-wide AI-assisted module engineering and course intelligence ecosystem** built around academically governed knowledge, competency and curriculum graphs.

The system would create a structured semantic layer between institutional academic content and AI.

Rather than asking an AI model independently to generate seminars, assessments, marking rubrics, lecture material or student explanations, the platform first establishes a reviewed representation of:

- what students are expected to know;
- what competencies they are expected to develop;
- how these develop across units and modules;
- which readings, theories and evidence support them;
- where they are taught and practised;
- how they are assessed;
- how assessment criteria and subcriteria operationalise them.

AI agents then generate candidate educational artefacts from this common framework, while academics remain responsible for checking, editing and approving the resulting content.

The intended result is not autonomous replacement of lecturers. It is an **academic production and intelligence infrastructure** that reduces repetitive workload while improving curriculum coherence, traceability and quality assurance.

---

# 1. The Problem

University courses contain many interdependent components:

- programme outcomes;
- module specifications;
- learning outcomes;
- weekly or unit-level content;
- required and recommended readings;
- lecturecasts;
- seminars and workshops;
- formative activities;
- assessments;
- marking rubrics;
- grading criteria;
- feedback;
- accreditation and institutional standards.

These components are often created and maintained separately.

This produces several recurring problems.

### Fragmented course design

Teaching materials, assessments and marking rubrics can evolve independently over time.

### Weak constructive alignment

Students may be assessed on competencies they have had limited opportunity to practise, while material receiving substantial teaching time may receive little assessment weight.

### Hidden prerequisites

Later units frequently depend on knowledge that may not have been clearly established earlier in the course.

### Inconsistent assessment rubrics

Broad university marking criteria often need to be interpreted differently for different assignments. This work is commonly performed manually by individual lecturers.

### High academic production costs

Creating or revising seminars, lecturecasts, formative exercises, assessments and rubrics is time-intensive.

### Uncontrolled use of generative AI

Generic AI can produce plausible educational material but may introduce knowledge that is not part of the approved module, conflate constructs and measures, obscure the evidential basis of claims, or create inconsistent versions of course content.

The proposed system addresses these problems by establishing a common academic knowledge and competency layer before content is generated.

---

# 2. Proposed Solution

The proposed ecosystem is an **AI-assisted University Module Engineering and Course Intelligence Platform**.

Its central architecture is:

```text
OFFICIAL STANDARDS
        ↓
PROGRAMME OUTCOMES
        ↓
MODULE OUTCOMES
        ↓
COMPETENCY GRAPH
        ↓
KNOWLEDGE GRAPH
        ↓
CURRICULUM GRAPH
        ↓
TEACHING + ASSESSMENT + RUBRIC + GRADING
        ↓
STUDENT LEARNING AND PERFORMANCE
```

Each layer remains explicitly connected to the others.

AI agents operate around this structure, but the reviewed academic graph remains the authoritative representation.

---

# 3. Four Interconnected Academic Layers

## 3.1 Standards Layer

The standards layer records the external and institutional requirements relevant to a course.

Possible sources include:

- national subject benchmark statements;
- institutional academic regulations;
- programme-level learning outcomes;
- credit and level descriptors;
- accreditation requirements;
- assessment policies;
- academic integrity requirements.

These provide constraints rather than content generation prompts.

---

## 3.2 Knowledge Graph

The knowledge graph represents what students are expected to understand.

Typical node types include:

- concepts;
- constructs;
- theories;
- mechanisms;
- claims;
- studies;
- methods;
- measures;
- findings;
- limitations;
- debates.

Relationships might include:

```text
THEORY → EXPLAINS → CONSTRUCT
STUDY → TESTS → CLAIM
FINDING → SUPPORTS → CLAIM
FINDING → CHALLENGES → CLAIM
CONSTRUCT → MEASURED_BY → MEASURE
THEORY → CONTRASTS_WITH → THEORY
```

Every substantive relationship can retain provenance back to the original course source.

---

## 3.3 Competency Graph

The competency graph represents what students are expected to be able to do with that knowledge.

Examples include:

- explain;
- apply;
- compare;
- analyse;
- interpret;
- evaluate;
- synthesise;
- construct arguments;
- evaluate evidence;
- reason methodologically;
- communicate academically.

This allows the system to distinguish knowledge acquisition from higher-order academic performance.

---

## 3.4 Curriculum Graph

The curriculum graph connects the knowledge and competencies to the actual educational experience.

Objects include:

- programme;
- module;
- unit;
- reading;
- lecturecast;
- seminar;
- workshop;
- formative activity;
- assessment;
- assessment criterion;
- rubric subcriterion.

For example:

```text
UNIT
  TEACHES → CONCEPT

SEMINAR
  PRACTISES → COMPETENCY

LECTURECAST
  EXPLAINS → THEORY

ASSESSMENT
  ASSESSES → COMPETENCY

RUBRIC SUBCRITERION
  MEASURES → COMPETENCY
```

This creates an auditable model of constructive alignment.

---

# 4. Academic Knowledge Provenance

A key design principle is the distinction between source knowledge, synthesis and pedagogy.

The system uses three epistemic levels.

### E1 — Source Explicit

The relationship or claim is explicitly stated in approved course material.

### E2 — Source-Grounded Synthesis

The relationship results from integrating evidence across approved materials.

### E3 — Pedagogical Organisation

The relationship is introduced by the academic or AI system to organise teaching, for example identifying a prerequisite relationship not explicitly stated in the readings.

This allows lecturers and reviewers to ask:

- Where did this claim come from?
- Which reading supports it?
- Is it directly stated or synthesised?
- Is this a scientific claim or a pedagogical decision?
- Has an academic approved it?

---

# 5. AI Agent Ecosystem

The platform could use coordinated specialist AI agents rather than one general-purpose model.

## Academic Knowledge Agents

### Ingest and Structure Agent

Processes approved readings and course documents while preserving:

- document;
- section;
- page;
- passage;
- citation;
- source metadata.

### Knowledge Extraction Agent

Identifies candidate:

- concepts;
- theories;
- claims;
- methods;
- evidence;
- findings;
- limitations.

### Semantic Reconciliation Agent

Identifies:

- synonymous terminology;
- overlapping concepts;
- competing theories;
- cross-reading relationships;
- possible contradictions.

### Graph Critic Agent

Checks for:

- unsupported claims;
- over-generalisation;
- mistaken causal inference;
- construct/measure confusion;
- duplicate concepts;
- missing limitations;
- false consensus across conflicting readings.

---

# 6. AI Teaching Design Agents

Once an academic knowledge graph has been reviewed, teaching artefacts can be generated from it.

## Unit Content Builder

Creates or revises weekly/unit teaching material.

It can generate:

- structured explanations;
- key concepts;
- worked examples;
- evidence summaries;
- critical debates;
- formative exercises;
- retrieval questions.

The content is constrained by the approved course graph.

## Lecturecast Builder

Creates asynchronous teaching scripts and visual plans.

A typical structure might be:

```text
orientation
→ prerequisite activation
→ core concept/model
→ evidence/example
→ comparison or limitation
→ application
→ retrieval summary
```

Production notes can identify where diagrams, tables or animations would be useful.

## Seminar and Workshop Builder

Creates active learning rather than simply reproducing asynchronous content.

A standard pattern might be:

```text
activate prior knowledge
→ retrieve
→ apply
→ compare
→ evaluate evidence
→ practise assessment-relevant skill
→ exit check
```

Each activity can be explicitly linked to the knowledge or competency being practised.

## Formative Activity Builder

Possible outputs include:

- retrieval exercises;
- short applications;
- concept sorting;
- evidence appraisal;
- data interpretation;
- theory comparisons;
- argument maps;
- reflective exercises;
- methodological critique.

---

# 7. Assessment Intelligence

## Assessment Designer

The Assessment Designer works backwards from:

- learning outcomes;
- knowledge domains;
- competencies;
- level requirements;
- existing teaching.

It can propose assessments that sample appropriate combinations of knowledge and academic skill.

A central validation question becomes:

> Has the student been taught and given an opportunity to practise what this assessment requires?

## Assessment-Specific Rubric Generator

Many universities use broad marking criteria across multiple assessment types.

The proposed system retains those institutional criteria while generating assessment-specific subcriteria.

For example:

### Critical Analysis — 25%

Possible assessment-specific subcriteria:

1. Evaluates relevant theoretical claims.
2. Compares plausible alternative explanations.
3. Evaluates the quality and limitations of evidence.
4. Produces a justified synthesis or conclusion.

A different assignment can generate different subcriteria while retaining the same institutional criterion and weighting.

This creates:

```text
INSTITUTIONAL CRITERION
        ↓
MODULE INTERPRETATION
        ↓
ASSESSMENT-SPECIFIC SUBCRITERIA
        ↓
OBSERVABLE PERFORMANCE
```

---

# 8. AI-Assisted Grading

The same architecture can support marking.

A grading workflow could be:

```text
student submission
        ↓
assessment instructions
        ↓
approved rubric
        ↓
assessment-specific subcriteria
        ↓
relevant module knowledge/skills
        ↓
independent subcriterion judgements
        ↓
weighted criterion scores
        ↓
provisional grade
        ↓
cohort calibration where authorised
        ↓
academic review
```

The system could generate:

- criterion-level feedback;
- strengths;
- areas for improvement;
- personalised concluding feedback;
- evidence supporting each grading judgement.

The academic remains responsible for final approval where required.

---

# 9. Cohort Calibration and Norming

Where an institution uses grading calibration, this should remain separate from initial marking.

The system should first judge each submission independently against the approved rubric.

Only afterwards should cohort-level checks be applied.

This prevents circular reasoning such as:

> “The desired class average is 65, therefore this submission should receive approximately 65.”

Instead:

```text
independent assessment
→ provisional scores
→ cohort distribution review
→ calibration
→ final marks
```

This preserves both consistency and transparency.

---

# 10. Nine Core Course Intelligence Views

Each reviewed module graph can generate multiple views.

| View | Function |
|---|---|
| Core-concept tree | Shows essential conceptual structure |
| Prerequisite graph | Shows what needs to be understood first |
| Theory map | Shows relationships between theoretical accounts |
| Evidence graph | Links claims, studies, findings and limitations |
| Construct map | Distinguishes constructs, operationalisations and measures |
| Debate map | Represents disagreement and competing explanations |
| Assessment map | Connects outcomes, knowledge, competency and grading |
| Reading map | Shows what each reading contributes |
| Student revision map | Provides a compressed study architecture |

The important point is that these are different projections of the **same reviewed course model**.

---

# 11. Programme-Level Curriculum Intelligence

Once multiple modules have been modelled, the platform can operate at programme level.

It can identify:

### Prerequisite gaps

A later module assumes knowledge that has not clearly been established.

### Duplication

Several modules spend significant time covering essentially the same material.

### Curriculum gaps

Important programme competencies receive little teaching.

### Assessment imbalance

A competency is repeatedly assessed while another receives very little assessment.

### Progression problems

Students may repeatedly demonstrate the same level of performance rather than moving from:

```text
describe
→ explain
→ apply
→ analyse
→ evaluate
→ synthesise
```

### Evidence imbalance

A programme may teach a theoretical perspective extensively without exposing students adequately to competing evidence.

---

# 12. Quality-Assurance Dashboard

A university-wide deployment could provide programme leaders and quality teams with dashboards showing:

- learning-outcome coverage;
- assessment coverage;
- curriculum progression;
- prerequisite dependencies;
- competency development;
- rubric alignment;
- formative-to-summative preparation;
- reading/evidence coverage;
- duplicated content;
- unresolved graph inconsistencies.

This creates a continuously inspectable curriculum rather than a collection of disconnected module documents.

---

# 13. Human-in-the-Loop Academic Governance

The system is designed around an explicit principle:

> **AI proposes; academics govern.**

A typical workflow is:

```text
AI produces candidate artefact
        ↓
automated provenance/alignment check
        ↓
academic reviewer
        ↓
approve / edit / reject / regenerate
        ↓
canonical course artefact
```

Academics remain responsible for:

- learning outcomes;
- substantive course knowledge;
- assessment standards;
- rubric approval;
- teaching accuracy;
- final consequential academic decisions.

This transforms the lecturer from primary manual content producer into **academic architect, reviewer and subject expert**.

---

# 14. University Roles

Different stakeholders could interact with different parts of the platform.

## Lecturer

- builds units;
- reviews AI teaching content;
- creates seminars;
- develops assessments;
- creates rubrics;
- grades work.

## Module Leader

- oversees module coherence;
- monitors unit progression;
- reviews assessment coverage.

## Programme Director

- monitors curriculum-level progression;
- identifies duplication and gaps;
- reviews programme learning outcomes.

## Quality Team

- examines constructive alignment;
- tracks standards and consistency;
- supports validation and periodic review.

## External Examiner

Potentially receives structured evidence showing:

- what was taught;
- how it was assessed;
- how marking criteria operationalised programme expectations.

## Student

Receives only approved student-facing representations, such as:

- revision maps;
- concept explanations;
- evidence maps;
- practice activities;
- formative tutoring.

---

# 15. Privacy and Copyright

The platform should support multiple deployment models.

## Local or On-Premise Processing

Licensed textbooks, papers and other copyrighted teaching resources remain inside the university environment.

AI processing can occur locally.

Derived graph structures can then be stored without redistributing the original source material.

## Private Cloud

Universities may choose a controlled cloud environment with contractual restrictions and institutional authentication.

## Hybrid Architecture

Low-sensitivity tasks can use external AI while sensitive or copyrighted materials remain locally processed.

The architecture should avoid requiring the university to transfer all course material to a third-party general-purpose AI provider.

---

# 16. Model Independence

The platform should not depend on a single AI provider.

Different models may perform:

- embeddings;
- extraction;
- reasoning;
- critique;
- drafting.

Models can therefore be replaced as capabilities, cost, policy and institutional requirements evolve.

The durable assets are:

- university knowledge graphs;
- competency maps;
- curriculum graphs;
- approved artefacts;
- rubrics;
- provenance;
- academic decisions.

These remain institution-owned.

---

# 17. Commercial Product Structure

A university-wide ecosystem could be offered in layers.

## Course Intelligence

For lecturers and module leaders.

Includes:

- module knowledge graph;
- teaching design;
- seminar generation;
- lecturecast generation;
- assessment design;
- rubric design.

## Assessment Intelligence

Includes:

- assessment construction;
- competency mapping;
- assessment-specific rubrics;
- grading assistance;
- moderation and calibration tools.

## Curriculum Intelligence

For programme and institutional teams.

Includes:

- programme graphs;
- constructive-alignment analysis;
- progression;
- duplication/gap analysis;
- standards mapping.

## Student Learning Layer

Built only on academically approved course knowledge.

Includes:

- course-specific tutoring;
- revision maps;
- formative assessment;
- adaptive remediation;
- evidence-grounded explanations.

---

# 18. Proposed Pilot

A practical pilot could start with three psychology modules:

- Introduction to Cognitive Psychology;
- Biological Psychology;
- Health Psychology.

### Phase 1

Build knowledge graphs for selected units.

Evaluate:

- concept extraction;
- evidence mapping;
- provenance;
- lecturer correction requirements.

### Phase 2

Generate:

- unit content;
- seminars;
- lecturecasts;
- formative activities.

Compare with existing lecturer-created materials.

### Phase 3

Generate assessment-specific rubrics and compare them with existing lecturer-developed rubrics.

### Phase 4

Run grading assistance on previously marked anonymised work.

Compare:

- marks;
- criterion-level judgements;
- feedback quality;
- consistency;
- academic review burden.

### Phase 5

Build programme-level curriculum intelligence and identify structural issues across the three modules.

---

# 19. Pilot Evaluation

Important metrics include:

### Academic accuracy

How often are extracted concepts, claims and relations correct?

### Provenance accuracy

Can substantive outputs reliably trace back to approved materials?

### Academic review burden

How much human correction is required?

### Time saving

How much staff time is saved in:

- module design;
- seminar preparation;
- assessment design;
- rubric development;
- marking?

### Constructive alignment

Does the system identify genuine misalignment between outcomes, teaching and assessment?

### Inter-rater reliability

Does AI-assisted marking improve or reduce consistency?

### Staff acceptance

Do academics feel that the system augments rather than undermines academic authority?

### Student outcomes

Later pilots could assess:

- engagement;
- understanding;
- assessment performance;
- retention.

---

# 20. Long-Term Opportunity

The longer-term opportunity is not simply another educational chatbot.

It is a **university semantic and pedagogical infrastructure layer**.

The institution progressively builds a structured representation of:

```text
what it teaches
        ↓
why it teaches it
        ↓
how students learn it
        ↓
how students practise it
        ↓
how it is assessed
        ↓
how standards are applied
        ↓
what students ultimately achieve
```

This creates an institutional asset that becomes more valuable as additional modules and programmes are represented.

AI models may change repeatedly.

The university's structured academic knowledge does not.

---

# 21. Proposed Design Principle

The system can be summarised in one sentence:

> **Create one academically governed representation of what students should know and be able to do, then use AI to help build, teach, assess and improve the curriculum around it.**

The goal is not automated education.

The goal is **AI-augmented academic production with human-controlled standards, evidence and judgement**.
