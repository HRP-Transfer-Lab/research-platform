# INTO THE MATRIX — Build, Deploy and Understand Your First AI Agent

**Working title:** Into the Matrix: From Using AI to Engineering AI Systems  
**Version:** 0.2 | **Prepared:** 13 October 2026  
**Status:** WORKSHOP CONCEPT / CURRICULUM PLAN — not yet built, tested or delivered  
**Owner:** HRP Transfer Lab  
**Reference implementation:** IQMindware AI Guide (Cloudflare, Gemma, RAG)  
**Primary audience:** professionals, entrepreneurs, researchers, educators and capable beginners  
**Delivery format:** one practical day or two half-days, with optional follow-on workshops  
**Default Mac pilot environment:** Claude Code + Terminal (see [Alex's Mac setup](./ALEX_MAC_GETTING_STARTED.md)); no VS Code needed

> **Central promise:** Go from talking to AI to understanding and building AI agents. Construct a working system, give it knowledge and tools, deploy it to the web, and learn how to inspect and control what it does.

## 1. Educational rationale: getting "inside the matrix"

The aim is not another prompt-writing course or a black-box automation demonstration. Participants learn how conversational AI becomes an *application* by assembling and inspecting its components: model inference, retrieval, structured data, tool calls, a bounded control loop, feedback and deployment.

The key educational shift is from treating AI as an opaque conversational oracle to understanding it as a designed system whose representations, information sources, permissions and actions are available for inspection and criticism.

**Learning outcomes.** By the end of the core workshop participants should be able to:

1. Explain the differences between a basic LLM, a RAG assistant and a tool-using agent.
2. Run an LLM from an application rather than only through a hosted chat interface.
3. Connect a curated document collection to retrieval and distinguish retrieved evidence from model-generated language.
4. Define and call a simple, bounded tool; inspect its arguments, results and potential failure.
5. Implement or modify a short observe → choose → act → inspect → continue/stop loop with explicit limits.
6. Publish a minimal web interface and explain its backend/data flow, costs and safeguards.
7. Test grounding, hallucinations, tool choice and failure recovery, rather than inferring intelligence from fluent output.

**Pedagogical rule:** every module produces a visible, working increment, and participants inspect both the user-facing response *and the behind-the-scenes sequence*.

### How the Mac pilot is built: Claude Code + Terminal

**Claude Code is the development assistant, not the target agent.** Participants use Claude Code to inspect local project files, propose/edit code and run project commands *with human approval*. The application they build remains a separate Cloudflare Worker using Gemma, RAG and bounded tools. Account access and charges for Claude Code are independent of Cloudflare model and infrastructure usage.

The instructor should demonstrate the distinction explicitly:

```text
PERSON → CLAUDE CODE (coding agent) → proposes/edits/tests local project
                                           │
                                           ▼
                                     HUMAN REVIEW
                                           │
                                           ▼
                                    CLOUDFlARE WORKER
                                  (Gemma + RAG + tools)
```

Course procedure: first review proposed actions, then authorise a small edit or local command, inspect the result and trace, and explain how it changed the system. No automatic public deployment, production-account access, live customer data, unrestricted command execution or unapproved paid calls. The coding agent may make mistakes: participants need to verify its output and understand the operating boundary.

For the beginner setup, follow [Alex's Claude Code Mac guide](./ALEX_MAC_GETTING_STARTED.md). Node.js is needed for the Cloudflare tooling, but not to run the native Claude Code installer. Claude Code requires an eligible paid subscription or billed Console account; a free Claude chat account alone is insufficient. The Cloudflare skills plugin is optional and can be introduced later when account permissions are understood.

The curriculum remains *conceptually tool-independent*, so equivalent coding assistants may be substituted in future editions; this version's **default practical implementation is Claude Code + Terminal**.

## 2. The progression: six build stages

| Stage | What participants construct | Essential concept | Tangible checkpoint |
| --- | --- | --- | --- |
| **1. Enter the Matrix** | A Gemma-powered chat interface | An LLM generates responses; it is not automatically an agent | Ask a question and inspect the request, model output and latency |
| **2. Give it Knowledge** | RAG over a small reviewed knowledge collection | Retrieval, grounding, provenance, limits and stale information | Display retrieved passages and source links alongside the answer |
| **3. Give it Tools** | A read-only lookup, e.g. approved product availability | Structured function/tool calls versus unconstrained text | Inspect the chosen tool, input arguments, returned data and response |
| **4. Give it Agency** | A bounded tool-selection and clarification loop | Goals, uncertainty, permitted actions, state and stopping rules | Observe why it asked, searched, used a tool or stopped |
| **5. Connect it to Reality** | A deployed Cloudflare web application | APIs, execution boundaries, public access and operations | Share a working demo URL (or local preview if account access is unavailable) |
| **6. Test the Agent** | A small evaluation suite and iterative repair | Reliability, safety, adversarial cases and human oversight | Compare performance before/after a change using the same test set |

**Important distinction:** a RAG chatbot or scripted questionnaire is *not by itself an autonomous agent*. The agentic increment is the bounded ability to choose amongst authorised operations, inspect outcomes and decide whether more work is needed. An agent is not necessarily more accurate than a simpler RAG system.

### Running demonstration

Use a fictional or publicly approved **IQMindware cognitive-training product adviser** as the demonstration project. Participants can substitute a consultancy, teaching resource, shop or research archive using the same starter template.

Example input:

> "I struggle to remember information when I'm learning. What should I do?"

Progressively compare:

- **A — Basic LLM:** a generic explanation, without retrieval or verified product information.
- **B — RAG chatbot:** retrieves source-grounded material about memory, attention, study strategies and evidence limits, with citations.
- **C — Bounded agent:** decides whether a clarifying question, source retrieval or a read-only availability lookup is needed before offering proportionate options and uncertainties.

The lesson is not that C is always best. Participants should be able to identify conditions where A or B is faster, safer or more reliable.

## 3. Inspectable agent: the teaching centrepiece

Do not deliver a workshop whose only output is a polished chat window. The interface should include an optional **inspection panel** with a chronological trace:

```text
USER INPUT
   ↓
WORKING STATE (goal, explicit uncertainties, permitted tools)
   ↓
NEXT-STEP CHOICE (answer / clarify / retrieve / look up)
   ↓
TOOL REQUEST (name + validated arguments, if any)
   ↓
OBSERVATION (retrieved passages / structured result / error)
   ↓
UPDATED WORKING STATE (what changed? what remains unknown?)
   ↓
ANSWER OR CONTINUE (budget, safety, stop condition)
```

Show **observable** state and runtime records, not invented access to a model's hidden internal reasoning. A useful trace includes short action labels, tool names, JSON-like inputs and outputs, source IDs, confidence/uncertainty annotations where justified, and reasons for stopping expressed as system rules. Avoid presenting a fabricated "chain of thought".

The structure should be approachable: editable cards for the goal, known facts, unanswered questions, chosen action, observation and next step. If a tool fails or retrieved data conflict, participants can see the error rather than being shown an implausibly seamless answer.

## 4. G-loop and agent–niche adaptation: distinctive scientific layer

HRP Transfer Lab's distinctive contribution is to connect agent engineering with **model construction, testing, environmental feedback and learning**.

For teaching, introduce a *G-loop-inspired* interaction:

```text
Clarify problem
 → construct a provisional working representation
 → identify uncertainty / competing interpretations
 → select a permitted information-gathering action
 → observe evidence / user response
 → revise the representation
 → evaluate whether the goal is sufficiently served
 → continue, stop or hand over
```

For the memory example, plausible interpretations might include working-memory demands, ineffective retrieval practice, distractions or ordinary information retention problems. The system asks a discriminating question or consults approved evidence **without diagnosing or inferring cognitive impairment**.

This workshop loop is **not** an implementation or validation of the canonical Kastel/Trident-G computational G-loop, adaptive control policies, latent-state estimation or near-criticality hypotheses. Those are higher-level concepts that may motivate later technical work; they should be labelled as such.

The deeper discussion is **agent–niche coupling**: actions can alter the environment (a visitor's understanding, a database entry in an authorised sandbox, a user's workflow) and subsequent observations can alter the agent's behaviour. Participants should distinguish immediate information use from genuine learning across episodes, and a changed website response from demonstrated cognitive transfer.

## 5. Suggested one-day timetable

Indicative teaching time: **about 6–6.5 hours plus breaks**. This is a draft, not an externally validated learning design.

| Time allocation | Block | Exercise |
| --- | --- | --- |
| 40 min | Orientation + Stage 1 | Run first model call, inspect response and latency |
| 55 min | Stage 2 | Add small knowledge base; compare sourced/unsourced claims |
| 50 min | Stage 3 | Add deterministic, read-only database/tool lookup |
| 75 min | Stage 4 | Build and inspect a bounded agent loop with stop rules |
| 50 min | Stage 5 | Connect frontend and deploy to a preview web endpoint |
| 65 min | Stage 6 + reflection | Red-team, evaluate, repair and compare systems A/B/C |
| 25 min | Demonstrations and next steps | Show traces, trade-offs and potential real-world applications |

Alternatively split the first three stages and last three stages over **two half-days**, assigning preparation and evaluation exercises between sessions.

### Demonstration challenges

1. An answerable question with a clear source.
2. A question for which the corpus has **no** evidence: correct outcome is uncertainty or hand-off.
3. A stale or conflicting product price: the structured authoritative source must take precedence.
4. A vague goal ("improve my memory"): test whether a brief clarification helps.
5. A prompt injection hidden inside retrieved text: retrieval content must not grant new permissions.
6. A tool failure or time-out: no fabricated success, and a helpful fallback.
7. A question requesting clinical diagnosis: refuse diagnosis and provide suitable general information and signposting.

Participants should record successes, failures and what changed after a fix. Even a simple fixed question set is more informative than evaluating only the best-looking demo.

## 6. Technical workshop stack

Proposed reference architecture (verify live model/service availability, quotas and prices when preparing the course):

```text
Browser (chat interface + inspector)
  └─ Cloudflare Pages / Worker endpoint
       ├─ Workers AI: Gemma model candidate
       ├─ Cloudflare AI Search: reviewed RAG materials
       ├─ Read-only tool: approved product/resource lookup
       ├─ Bounded controller: allowed tools, state, turn/action/time/budget caps
       └─ Structured trace + fallback
  Optional later: D1 for structured facts; R2 for approved documents
```

**Use managed inference** so learners need ordinary laptops rather than GPUs. Keep API credentials server-side and issue development-only access where possible. GitHub provides versioning; JavaScript/TypeScript is a practical first implementation language. A Python companion notebook can be offered for computational modellers.

**Prerequisites:** a laptop/browser, basic familiarity with files and web applications, starter code, and a ready-made sandbox environment. No neural-network mathematics is required; the instructor should not expect novices to build retrieval or agent orchestration entirely from scratch during a single day.

**Instructor preparation:** pre-test Claude Code installation/login and approval prompts on a supported Mac, plus all Cloudflare accounts/permissions; provide seeded knowledge data, starter repositories or templates, example traces, a functioning fallback demonstration and separate Claude/Cloudflare cost caps. Where self-service Cloudflare account creation is a barrier, provide a preconfigured instructor-hosted sandbox with isolated learner credentials and quotas.

**Security and privacy:** no live customer data; no unrestricted external actions; no access to production accounts; do not log identifiable conversations by default; enforce rate limits and budgets; avoid account linking, payments or public autonomous messaging. Approve any public deployment explicitly and remove or constrain demo endpoints after the course.

## 7. Workshop deliverables and assessment

Each participant or pair should leave with:

- A basic LLM endpoint and interface.
- A small documented RAG corpus and at least one source-grounded answer.
- A functioning read-only tool with validated arguments.
- A bounded agent loop with explicit stop/hand-off policy.
- An inspectable event/action trace.
- A deployed preview URL **or** a reproducible local demonstration.
- A short evaluation record comparing A/B/C and identifying at least one failure and mitigation.

A compact rubric can score **conceptual understanding**, **functioning integration**, **grounding and integrity**, **safe tool control**, and **inspection/evaluation quality**. The aim is understanding and competence, not an impressive-looking but opaque demo.

## 8. Audience adaptations and commercial pathway

**Entrepreneurs / professionals:** customise the assistant to a small business knowledge base, sales FAQ or service information. Focus on deterministic business facts and safe customer hand-off.

**Students / academics:** use a research archive or teaching resource; focus on provenance, competing explanations, retrieval quality and evaluating overclaims.

**Organisations:** use a simulated policy/workflow assistant; emphasise human approval, permissions, audit trails and consequences for team workflows. This can lead into later Synergy Work Intelligence (SWI) discussions, but the workshop must not imply a production-ready HR agent.

Possible series:

1. **Build Your First AI Agent** — basic model, RAG, tools, loop, web deployment.
2. **Building AI Systems That Think With You** — externalised and inspectable Bayesian models, causal graphs, decision trees and computational representations; connection to educational computational-modelling articles.
3. **Adaptive Human–AI Systems** — agent–niche feedback, goals and constraints, policy learning, G-loop architecture, changed-condition evaluation and distinctions between short-term assistance and retained human skill.

**Workshop 1 should stand on its own** and should not require buying an IQMindware product. Later workshops may connect to Trident-G research, computational modelling and evidence-based augmentation, with theoretical and empirical status clearly labelled.

## 9. Open decisions and next build tasks

### Open decisions

- Is the intended audience primarily beginners, technically confident entrepreneurs or postgraduate researchers?
- One full day, two half-days or a modular online course?
- Public workshop brand: "Into the Matrix" as a working title, with trademark/marketing review before commercial launch.
- Individual Cloudflare accounts, pre-provisioned teaching sandbox or local-first alternatives?
- Which parts of the IQMindware knowledge base can be openly redistributed as a teaching dataset?
- What costs, instructor-to-student support ratio and accessibility accommodations are viable?

### Next implementation tasks

1. Extract a *non-sensitive workshop starter* from the IQMindware AI Guide architecture (no credentials or internal private documents).
2. Build three frozen demonstration baselines (A, B, C) with the same test prompts.
3. Add the visual inspector and an exportable trace format.
4. Assemble a 30–50-item graded evaluation set, including grounded and adversarial cases.
5. Run a small internal pilot to establish feasible timings, friction points and learning outcomes.
6. Prepare facilitator notes, installation checklist, participant handout, task rubric and a reproducible fallback exercise.

## 10. Provenance and scope

This document adapts the discussion **"Into the Matrix: Build, Deploy and Understand Your First AI Agent"** (13 October 2026) into an HRP Transfer Lab workshop plan. The IQMindware customer chatbot is the **reference example**, not the project owner or the only permissible use case.

Companion internal architecture (may require separate repository access):

- `Mindware-Lab/trident-g-platform/products/trident-g-iq/docs/iqmindware-ai-guide/IQM_AI_GUIDE_CLOUDFLARE_GEMMA_RAG_PLAN_v0.1.md`
- `Mindware-Lab/trident-g-platform/docs/hrp-lab-g-loop-agent/kastel-stack-v1/KASTEL_G_LOOP_v1.md`
- `Mindware-Lab/trident-g-platform/kastel-stack/application/COUPLED_ADAPTATION_SPEC.md`

This is a **curriculum proposal, not a completed workshop or endorsed educational outcome**. It changes no application runtime, model deployment, website, user data or training research protocols.
