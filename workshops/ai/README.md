# HRP Transfer Lab — AI Workshops

**Status:** workshop development workspace. Teaching plans here are proposals until starter code, materials, evaluation sets and delivery are validated.

This folder collects practical, inspectable workshops on language models, RAG, tools, agent design, computational modelling and adaptive human–AI systems.

## New participant: first steps on a Mac

Start with **[Mac setup and first uploads (Alex / beginner guide)](./ALEX_MAC_GETTING_STARTED.md)**. It covers the four essential prerequisites, a local Cloudflare Hello World check, and the first three synthetic documents to upload to AI Search. No Python, Docker or live IQMindware credentials are required for the initial setup.

**[Starter data](./starter-data/01_demo_catalogue.md):** three small, public, fictional knowledge-base files for the first RAG activity. Never confuse their invented product prices or refund terms with the real business.

## Workshop catalogue

| Workshop | Scope | Status |
| --- | --- | --- |
| [Into the Matrix — Build, Deploy and Understand Your First AI Agent](./INTO_THE_MATRIX_AGENTIC_AI_WORKSHOP.md) | Six-stage hands-on course: LLM → RAG → tools → bounded agent → web deployment → evaluation | Curriculum v0.1, proposed |
| Building AI Systems That Think With You | Inspectable computational decision and knowledge models (Bayesian models, causal graphs, tests) | Potential follow-on; not yet specified |
| Adaptive Human–AI Systems | Agent–niche feedback, G-loop ideas, human capability, limits and validation | Potential follow-on; not yet specified |

## Working principles

- Build something functional at each stage and expose observable tool/state traces rather than a chat interface alone.
- Distinguish language generation, retrieval and tool-based agency.
- Teach grounded claims, testable evaluation, permissions and failure handling before promising autonomy.
- Separate conceptual G-loop teaching examples from the canonical computational G-loop, which requires separate specification, implementation and evaluation.
- Do not expose production credentials, customer data or private evidence to workshop learners.

## Reference example

The first workshop uses the **IQMindware AI Guide** architecture as a reusable teaching demonstration. Participants can substitute a different approved domain corpus without adopting the IQMindware product or business context. The underlying AI Guide plan lives in the private `Mindware-Lab/trident-g-platform` repository and is not redistributed here.

## Next step

Produce instructor-tested starter templates and an inspectable agent trace, then pilot the six-stage format with a small group before making commercial or educational efficacy claims.
