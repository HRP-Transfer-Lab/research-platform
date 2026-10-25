# Assessment Evidence Architecture for the AI Era

## Purpose

Extend the UoE Knowledge Factory so assessment validity does not depend on a single polished product such as an essay or report.

The system should evaluate whether a student **possesses the target knowledge and competencies**, not merely whether those competencies appear in a submitted artefact.

This is especially important in an environment where generative AI can substantially improve the surface quality of written work and can therefore weaken the inference:

```text
high-quality submitted product
        ↓
student independently possesses the demonstrated competence
```

The platform should instead seek **converging evidence** across differently vulnerable assessment channels.

---

## 1. Design rationale

Current higher-education assessment faces two distinct problems:

1. widespread student use of generative AI in assessed work;
2. increasing difficulty inferring independent student competence from polished take-home products alone.

The architecture should therefore treat source-specific assessment as valuable but insufficient.

A student may be required to:

- distinguish claims made by specific core readings;
- compare papers that disagree;
- interpret a particular figure, table or methodological choice;
- identify a limitation discussed in the module rather than offer generic criticism;
- connect seminar cases to specific theoretical distinctions;
- use the course's conceptual vocabulary accurately.

This improves discrimination against generic answers, but it does not make assessment AI-proof because a capable model can also be given the readings.

Therefore:

> **Source specificity is one authentication layer, not the whole authentication strategy.**

---

## 2. Core construct: student competence

The system should distinguish evidence from three broad classes:

```text
                STUDENT COMPETENCE

          ┌──────────┼──────────┐
          ▼          ▼          ▼

       PRODUCT     PROCESS    PERFORMANCE

       essay/      drafts/      quiz
       report      decisions     viva
       project     reflection    application
                   AI log        transfer probe
```

A final essay or report may remain important, but should not automatically function as the sole evidence for a high-stakes competency.

---

## 3. Assessment Evidence Channels

For every learning outcome, competency or rubric subcriterion, the Assessment Designer should ask:

> **What evidence would convince us that this competence is actually possessed by the student rather than merely present in the submitted artefact?**

The system should support at least seven evidence channels.

### 3.1 Retrieval

Examples:

- low-stakes cumulative quizzes;
- short factual or conceptual retrieval;
- identify which author made a claim;
- distinguish construct from measure;
- classify a finding or method correctly.

Purpose:

Provide repeated evidence that core knowledge is retrievable by the student.

### 3.2 Explanation

Examples:

- short constructed response;
- explain a concept in simpler terms;
- explain why a conclusion follows;
- distinguish two closely related concepts.

Purpose:

Test whether the student can reconstruct meaning rather than merely recognise an answer.

### 3.3 Application

Examples:

- novel case;
- unseen scenario;
- new dataset;
- unfamiliar graph or figure;
- altered boundary condition.

Purpose:

Test whether the student can apply a concept beyond the original learning wrapper.

### 3.4 Process

Examples:

- initial interpretation of task;
- reading selection;
- argument outline;
- evidence map;
- draft;
- revision rationale;
- AI-use declaration;
- critique of AI output.

Purpose:

Make the development of the assessment visible and create evidence of student judgement over time.

### 3.5 Dialogue

Examples:

- viva-lite;
- short oral defence;
- unpredictable follow-up;
- explanation of a chosen citation;
- response to a changed assumption.

Purpose:

Authenticate ownership of central claims and reasoning.

### 3.6 Product

Examples:

- essay;
- report;
- project;
- presentation;
- portfolio;
- research output.

Purpose:

Assess integrated performance, communication and sustained argument.

### 3.7 AI Judgement

Examples:

- critique an AI-generated answer;
- identify unsupported claims;
- compare AI output against module readings;
- correct misleading evidence use;
- justify revisions;
- choose between competing AI-generated explanations.

Purpose:

Assess competence in human-AI collaboration rather than pretending AI use can always be excluded.

---

## 4. Dual-competence model

The platform should represent two distinct constructs.

### 4.1 Human-independent competence

What can the student do without AI support?

Examples:

- retrieve knowledge;
- explain concepts;
- reason through evidence;
- interpret findings;
- apply concepts to novel cases;
- defend a conclusion orally.

### 4.2 Human + AI competence

What can the student do when AI is explicitly available?

Examples:

- formulate useful queries/prompts;
- verify model output;
- identify unsupported claims;
- detect reasoning or evidence errors;
- compare model output with disciplinary sources;
- revise a weak AI answer;
- synthesise human and AI contributions responsibly.

These constructs must not be collapsed.

```text
                 COURSE COMPETENCE

          ┌────────────┴─────────────┐
          ▼                          ▼

INDEPENDENT COGNITION         AUGMENTED COGNITION

retrieval                     AI collaboration
conceptual explanation        verification
reasoning                     research strategy
novel transfer                error detection
oral defence                  synthesis with AI
```

A module may assess both, but should label them explicitly.

---

## 5. Authentication profiles

Each important competency should have an **authentication profile** showing the evidence channels through which it is assessed.

Example:

```text
Competency: Critical evaluation

Product / essay              ✓
Core-reading evidence        ✓
Process trail                ✓
Novel application            ✓
Dialogue / viva              ✓

Authentication confidence:
HIGH
```

Contrast:

```text
Competency: Critical evaluation

Product / essay              ✓
Everything else              ✗

Authentication confidence:
LOW — product only
```

The confidence label is not a psychometric estimate unless validated. Initially it should be a rule-based design flag.

The system should support thresholds such as:

- LOW — one evidence channel;
- MODERATE — two independent channels;
- HIGH — three or more channels spanning at least two of Product / Process / Performance.

Institutional partners may define their own rules.

---

## 6. Source-specific epistemic engagement

Assessment prompts should be able to target the reviewed module graph directly.

Examples:

- compare the claims of two named readings;
- identify which source supports a particular position;
- interpret a figure or methodological choice from a specified study;
- distinguish a source-specific limitation from a generic limitation;
- explain how a seminar case changes interpretation of a theory;
- use the module's canonical terminology.

Rubric subcriteria can explicitly reward this.

Example:

```text
Assessment:
Evaluate what lesion-method evidence can and cannot establish about cognitive architecture.

Subcriteria:
- accurate use of Fellows et al.;
- accurate representation of Chatterjee's criticism;
- comparison of their methodological positions;
- integration with Unit 3 concepts;
- justified conclusion about inferential limits.
```

This reduces the value of generic disciplinary prose.

---

## 7. Low-stakes retrieval and cumulative unit quizzes

The system should support auto-generated, graph-grounded unit quizzes.

Canonical workflow:

```text
unit readings
      ↓
reviewed knowledge graph
      ↓
question generator
      ↓
item validation
      ↓
student quiz
      ↓
feedback
      ↓
longitudinal knowledge-state record
```

Question types may include:

- author/claim identification;
- concept discrimination;
- construct versus measure;
- finding interpretation;
- evidence classification;
- short explanation;
- novel application;
- confidence rating.

Quizzes should generally be:

- frequent;
- low stakes;
- cumulative where appropriate;
- linked to explicit graph nodes;
- generated from validated item templates;
- reviewed for difficulty drift.

The platform should not assume that quiz performance alone establishes higher-order competence.

---

## 8. Viva-lite authentication

The system should support short, scalable oral verification.

Typical duration:

```text
5–8 minutes
```

Inputs:

```text
student submission
+
approved rubric
+
module graph
+
source readings
+
identified high-value claims
```

The Viva Agent should generate a small set of personalised probes such as:

- What is the central claim of your argument?
- Why did you use this study rather than the alternative?
- What evidence would weaken your conclusion?
- Explain this sentence from your submission in simpler terms.
- How would your answer change if condition X were different?
- Which reading most strongly disagrees with your position?

Viva questions should sample central competencies, not trivia.

The viva may function as:

- graded assessment;
- authentication hurdle;
- moderation evidence;
- targeted verification after an anomalous submission.

---

## 9. Processfolios

The system should support a processfolio model in which selected stages of assessment development are retained.

Possible process artefacts:

```text
assessment task issued
        ↓
initial interpretation
        ↓
reading selection
        ↓
argument outline
        ↓
evidence map
        ↓
draft
        ↓
AI interaction if permitted
        ↓
critique/revision
        ↓
final answer
```

The processfolio should not require exhaustive surveillance.

Its purpose is to capture meaningful decision points.

Possible uses:

- graded process component;
- pass/fail hurdle;
- viva evidence;
- formative feedback;
- authorship/authentication support.

---

## 10. AI-visible assessments

Some assessments should explicitly permit AI.

The target construct then changes from unaided production to **epistemic judgement over AI-supported work**.

Example pattern:

```text
AI produces one or more candidate answers
        ↓
student must:
identify errors
compare against readings
correct unsupported claims
select stronger evidence
rewrite weak sections
justify changes
```

Possible rubric subcriterion:

> **AI evaluative judgement:** identifies unsupported, misleading or incomplete AI-generated claims and corrects them using appropriate disciplinary evidence.

The platform should allow modules to classify assessments as:

- AI_PROHIBITED;
- AI_RESTRICTED;
- AI_DISCLOSED;
- AI_REQUIRED.

The exact institutional policy remains externally configurable.

---

## 11. Novel application and wrapper-transfer probes

The Assessment Designer should support changed-wrapper tasks.

Canonical progression:

```text
learned concept
     ↓
near application
     ↓
changed surface features
     ↓
boundary case
     ↓
explain why it does / does not apply
```

Examples:

- apply a learned bias to a new workplace decision;
- transfer a health-behaviour principle to an unfamiliar population;
- determine whether a theory predicts a new pattern;
- identify when a familiar construct does not apply.

These probes should be linked to explicit competency nodes such as:

- APPLY;
- GENERALISE;
- DISCRIMINATE_BOUNDARY;
- TRANSFER;
- JUSTIFY.

---

## 12. Data and figure interpretation

For empirically oriented modules, the system should generate equivalent variants of:

- graphs;
- tables;
- small datasets;
- unfamiliar experimental results;
- method descriptions.

Question types:

- What conclusion is justified?
- Which causal claim is not justified?
- What is the main confound?
- Which theory predicts this pattern?
- Which alternative explanation remains viable?

Variants must be checked for construct equivalence and difficulty.

---

## 13. Personalised parameterisation

The system should be able to generate different surface forms of the same competency target.

Example:

```text
same competency
+
different case
+
different data
+
different theory combination
```

This can reduce answer sharing and generic reuse.

However:

> Variant generation must not be treated as automatically equivalent.

The Assessment Critic should compare variants for:

- target construct;
- information load;
- reading burden;
- inferential complexity;
- ambiguity;
- expected response depth.

---

## 14. Short supervised synthesis tasks

The architecture should support short, open-book, controlled synthesis tasks.

Example:

```text
20–30 minutes
two source extracts
one novel result
400-word synthesis
AI unavailable
```

These provide evidence of human-independent synthesis.

They can complement rather than replace larger AI-permitted projects.

---

## 15. Oral presentation plus unpredictable follow-up

Students may use AI to help prepare a presentation.

Authentication then comes from follow-up questions such as:

- Why do you believe that?
- What alternative interpretation did you reject?
- Which reading would disagree?
- What changes if this assumption is removed?
- Which evidence is doing the most work in your conclusion?

The system should distinguish:

```text
prepared performance
from
responsive reasoning
```

---

## 16. Evidential reflection

Generic reflection should not be treated as strong authentication because AI can generate plausible reflective prose.

Reflection prompts should therefore be anchored to observable course evidence.

Example:

```text
What did you initially believe?
        ↓
What specific evidence changed it?
        ↓
Which reading caused that change?
        ↓
What did you get wrong in Quiz 3?
        ↓
How did your reasoning change?
        ↓
Demonstrate the revised reasoning on a new case.
```

This creates a traceable learning trajectory.

---

## 17. Assessment pattern template

A module may use a blended pattern such as:

```text
20% — cumulative retrieval/application quizzes

15% — short applied transfer task
      timed / open-book / no-AI

45% — substantive essay/report/project
      explicit AI policy
      core-reading specific

10% — process evidence
      outline / evidence map / decisions / AI-use record

10% — viva-lite
      brief authentication of central claims
```

These percentages are examples only.

The platform must not impose a single pattern.

Instead it should propose a portfolio based on:

- learning outcomes;
- target competencies;
- academic level;
- module content;
- institutional policy;
- workload constraints;
- desired authentication strength.

---

## 18. New graph objects

Add the following node or object types to the curriculum / assessment layer:

- assessment_evidence_channel;
- authentication_profile;
- viva;
- viva_question;
- processfolio;
- process_artifact;
- quiz;
- quiz_item;
- transfer_probe;
- ai_use_policy;
- ai_judgement_task;
- assessment_variant;
- supervision_condition;
- competence_mode.

Suggested competence modes:

- HUMAN_INDEPENDENT;
- HUMAN_AI_AUGMENTED.

Suggested evidence-channel values:

- RETRIEVAL;
- EXPLANATION;
- APPLICATION;
- PROCESS;
- DIALOGUE;
- PRODUCT;
- AI_JUDGEMENT.

---

## 19. Suggested relationships

```text
ASSESSMENT
  COLLECTS_EVIDENCE_VIA → EVIDENCE_CHANNEL

EVIDENCE_CHANNEL
  AUTHENTICATES → COMPETENCY

QUIZ_ITEM
  TESTS → KNOWLEDGE_NODE

TRANSFER_PROBE
  TESTS → COMPETENCY

VIVA_QUESTION
  AUTHENTICATES → CLAIM
  AUTHENTICATES → COMPETENCY

PROCESS_ARTIFACT
  EVIDENCES → DECISION

AI_JUDGEMENT_TASK
  MEASURES → HUMAN_AI_AUGMENTED_COMPETENCE

ASSESSMENT
  REQUIRES_AI_POLICY → AI_USE_POLICY

AUTHENTICATION_PROFILE
  SUMMARISES → COMPETENCY

ASSESSMENT_VARIANT
  INSTANTIATES → ASSESSMENT_TEMPLATE
```

---

## 20. New agent roles

### Assessment Evidence Designer

Responsibilities:

- choose complementary evidence channels for each competency;
- identify competencies vulnerable to product-only assessment;
- propose authentication profiles;
- balance learning value, staff workload and security.

### Quiz and Retrieval Agent

Responsibilities:

- generate graph-grounded retrieval/application items;
- maintain cumulative coverage;
- create distractors tied to known misconceptions;
- track item provenance.

### Viva Agent

Responsibilities:

- generate personalised oral probes from submissions;
- target central claims and competencies;
- avoid trivial or purely memory-based questioning;
- support lecturer-led or institution-approved delivery.

### Processfolio Agent

Responsibilities:

- define meaningful process checkpoints;
- capture student decisions without exhaustive surveillance;
- connect process artefacts to rubric subcriteria.

### Transfer Probe Agent

Responsibilities:

- generate changed-wrapper applications;
- test boundaries and generalisation;
- create structurally equivalent variants;
- flag uncertain difficulty equivalence.

### AI Judgement Assessment Agent

Responsibilities:

- generate AI-visible tasks;
- create flawed or competing candidate outputs;
- require evidence-based correction;
- assess verification and epistemic judgement.

### Assessment Authentication Critic

Responsibilities:

- detect product-only high-stakes competencies;
- identify over-reliance on reflection;
- detect duplicate evidence channels that are not genuinely independent;
- flag insufficient evidence of human-independent competence;
- flag insufficient evidence of human+AI competence where required.

---

## 21. Assessment-validity audit

For every high-value competency, the system should be able to produce:

```text
Competency
↓
where taught?
↓
where practised?
↓
where assessed?
↓
through which evidence channels?
↓
under what AI conditions?
↓
is independent competence sampled?
↓
is augmented competence sampled?
↓
authentication confidence
```

The system should flag:

- high-stakes competency assessed only through product;
- no evidence of human-independent performance;
- no evidence of AI judgement where AI use is a stated graduate competency;
- reflection with no linked observable evidence;
- assessment-specific reading requirements not represented in rubric;
- viva questions unrelated to assessed competencies;
- quiz coverage concentrated on low-level recall only;
- parameterised variants with likely difficulty drift.

---

## 22. Product position

This architecture moves the product beyond:

> AI-resistant assessment

towards:

> **assessment validity for the AI era**

The core proposition is:

> Every important competency should be supported by multiple, differently vulnerable forms of evidence.

This makes the platform capable of designing not only course content and rubrics, but defensible evidence architectures for what students actually know and can do.
