# HRP Research Factory — M1b Grounded Agno Source Review v0.1

**Date:** 13 November 2026. **Status:** implementation for review; validation pending.
**Dependencies:** M0 and M1a are merged into research-platform/main.
**First paper:** TG-COMP-001 — Homeostatic Adaptive Intelligence.

## 1. Purpose and scientific boundary

M1a supplied bibliographic metadata and candidate DOIs, but did not read original sources. M1b adds explicitly authorised **local original-source text**, SHA-256 content pins and three bounded Agno roles:

1. **A02 Evidence Librarian:** selects source IDs from the already scoped corpus and lists coverage gaps.
2. **A03 Source Verifier:** proposes short verbatim quotations linked to claim/source IDs; deterministic Python rejects any quote that is not an exact source substring.
3. **A04 Competing-Theory Analyst:** receives **only accepted exact quotes**, produces bounded rival explanations and unresolved objections.

These are three actual Agno agent definitions using structured Pydantic outputs and *no tools*. Python policy gates run between the roles. Source passages are untrusted data; agent instructions explicitly forbid following instructions inside a document.

**An exact quotation is NOT a verified scientific interpretation.** The human reviewer must independently check original article identity, context, methods, conclusions, competing sources and the relationship between passages and claims. No agent can approve public claims or publications.

## 2. Files and ownership

New in components/research-factory/src/hrp_research_factory/:

- source_packets.py — local text ingestion, content hashes, scope/exposure controls and quote matching.
- open_access.py — fixed-host, opt-in Europe PMC OA DOI importer.
- grounded_agents.py — Agno A02/A03/A04 constructors and structured output.
- source_review.py — model-optional sequential source reading and independent quote gate.

New tests: test_source_review.py, test_open_access.py, test_grounded_agno_constructor.py. A fictional offline demo is scripts/demo_source_review.py. No changes are made to canonical theory, frozen M-series experiments or the Evidence Registry.

## 3. Run the offline demonstration

From components/research-factory/:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
python scripts/demo_source_review.py
```

This generates a local source-audit packet using clearly labelled FICTIONAL text, no model credentials, no live sources and no scientific claims. All outputs go to Git-ignored runs/.

## 4. Import a real open-access source, locally

The importer requires a single exact DOI candidate, a uniquely matching non-retracted Europe PMC hit with isOpenAccess=Y and inEPMC=Y, and JATS XML whose own DOI matches. It disallows HTTP redirects and truncates text to a bounded source extract.

```bash
export HRP_ALLOW_PUBLIC_FULLTEXT_LOOKUP=YES
hrp-factory import-open-access configs/TG-COMP-001.json \
  --candidates configs/TG-COMP-001-evidence-candidates.json \
  --source-id SRC-004 --out runs/oa-src-004
```

The source is stored as a checksum-pinned UTF-8 file and a source-bundle.json manifest. Even open-access sources are marked **restricted_local** and **hosted_approved=false** until article-specific rights and exposure are reviewed. If no eligible OA full text exists, the importer fails rather than invents a substitute. No external API is called unless the exact permission variable equals YES.

Alternatively, supply your own authorised TXT/Markdown files with a source-bundle.json containing: schema_version=hrp-local-source-bundle-v0.1, paper_id, and sources[] entries with source_id, DOI, title, file basename, SHA-256, access_basis, data_tier and hosted_approved. These are validated against the TG-COMP-001 DOI candidate list. Only regular files in the manifest directory are permitted; no symlinks, path traversal or oversized extracts.

## 5. Perform a local source inventory without an LLM

```bash
hrp-factory source-review configs/TG-COMP-001.json \
  --candidates configs/TG-COMP-001-evidence-candidates.json \
  --source-bundle runs/oa-src-004/source-bundle.json --out runs
```

This creates a source inventory and pending human-review packet. Source content is not copied into GitHub or a public database.

## 6. Run the three Agno agents (explicit opt-in)

First verify which models actually exist with ollama list. Install the Agno extras, then use a loopback local Ollama model:

```bash
python -m pip install -e '.[agents,dev]'
ollama list
export HRP_ALLOW_MODEL_CALLS=YES
export OLLAMA_HOST=http://127.0.0.1:11434
hrp-factory source-review configs/TG-COMP-001.json \
  --candidates configs/TG-COMP-001-evidence-candidates.json \
  --source-bundle runs/oa-src-004/source-bundle.json \
  --run-agents --provider ollama --model YOUR_INSTALLED_MODEL --out runs
```

Hosted OpenAI model calls are additionally restricted: HRP_ALLOW_SOURCE_TEXT_TO_HOSTED=YES, an API key, an eligible approved-public contract, and every source explicitly marked approved_public and hosted_approved=true under an open-access basis. The importer does not automatically grant these rights, and source privacy can never be overridden through a model prompt.

## 7. Generated packet and checks

```text
runs/TG-COMP-001/<run-id>/
  run_manifest.json
  review_packet.md
  source_review/
    source_manifest.json   # sources and hashes, no full text
    quote_audit.json       # exact matches/rejections, short quotes only
    rival_analysis.json    # model interpretations, unverified
    run_provenance.json    # model/provider and review flags
    REVIEW.md              # human review checklist
```

A03 quotes that are not exact matches are rejected and withheld from A04. A04 cannot invent passage IDs or link a quote to an unrelated claim. If no exact quote survives, the rival-analysis model stage is skipped. The evidence gate remains insufficient / human review pending in all cases.

## 8. Acceptance checklist

- [x] Bounded checksum-pinned local source import and access-tier controls.
- [x] Optional fixed-host Europe PMC OA import with rights notes.
- [x] A02/A03/A04 structured Agno constructors.
- [x] Deterministic quote gate and fabricated/misattributed citation refusal.
- [x] Offline fictional demo and tests for source mutation, malformed quotes and blocked hosting.
- [ ] Validate M1b tests and real Agno SDK construction in GitHub CI.
- [ ] Run one authorised real source and a confirmed installed local model.
- [ ] Independently check original article identity, full context, methods and limitations.
- [ ] Integrate Zotero/OSF and any other authorised primary-text sources.
- [ ] Expand claim-level reviewer evidence, contradictions, correction/retraction handling.
- [ ] PI approves original-source review before model freeze or publication claims.

**Scope limit:** M1b is a functioning source-grounded agent workflow, not full M1 scientific verification. Source identity and semantic support are not established by an LLM. No journal or preprint submission is enabled.

## 9. Documentation references

- Agno structured outputs: https://docs.agno.com/input-output/structured-output/agent
- Agno workflows: https://docs.agno.com/workflows/overview
- Europe PMC API: https://dev.europepmc.org/RestfulWebService
- Earlier evidence bridge: M1_RESEARCH_FACTORY_EVIDENCE_BRIDGE_V0_1.md
- Agent assignment: RESEARCH_FACTORY_REPOSITORY_AND_AGENT_ASSIGNMENT_PLAN_V0_2.md
