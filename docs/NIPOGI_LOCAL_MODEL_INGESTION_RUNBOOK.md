# NiPoGi Local Model Ingestion Runbook

**Status:** Stage 13 implementation runbook  
**Date:** 1 September 2026  
**Target host:** NiPoGi / `kastel-mini`  
**Assumed hardware:** 32 GB system memory, Ryzen-class CPU, no discrete NVIDIA GPU  
**Purpose:** Install and benchmark a local document-processing and model stack for scaling the HRP Transfer Evidence Registry from 18 sources towards 100–1,000 sources.

## 1. Operating principle

Use deterministic software for identity, access, hashing, parsing and schema validation. Use local language models for semantic extraction, classification, comparison and draft recommendation support.

```text
metadata APIs / source files
→ canonical identity and deduplication
→ acquisition + SHA-256
→ deterministic PDF parsing
→ section/chunk manifest
→ local structured extraction
→ automatic quality gates
→ machine-screened working corpus
→ CSI recommendation review
→ targeted scientific correction/promotion
```

Do not use the local model as an unstructured web browser or as an automatic scientific authority.

## 2. Initial model set

### Workhorse extraction model

```text
qwen3.5:9b
```

Use for:

- study-design and population extraction;
- intervention/component classification;
- outcome/timepoint extraction;
- transfer-route and CSI tag candidates;
- evidence-span selection;
- missingness detection;
- first-pass quality/RoB signalling evidence;
- draft proposition and recommendation support.

### Embedding model

```text
qwen3-embedding:0.6b
```

Use for:

- chunk indexing;
- semantic source retrieval;
- similar-study retrieval;
- evidence-query expansion;
- candidate duplicate detection support.

### Optional second-pass model

Do not download initially unless the 9B calibration shows a material gap.

Candidate:

```text
qwen3:30b
```

This is a larger local model for disagreement resolution and difficult extractions. It should be invoked selectively, not on every paper.

## 3. Install Ollama

Check whether it is already installed:

```bash
ollama --version
```

If the command is not found:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Enable and start the service:

```bash
sudo systemctl enable --now ollama
sudo systemctl status ollama --no-pager
```

## 4. Pull the initial models

```bash
ollama pull qwen3.5:9b
ollama pull qwen3-embedding:0.6b
ollama list
```

Expected approximate model storage:

```text
qwen3.5:9b             ~6.6 GB
qwen3-embedding:0.6b   ~0.6 GB
```

## 5. Smoke-test the model API

```bash
curl -s http://localhost:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3.5:9b",
    "stream": false,
    "messages": [
      {"role": "user", "content": "Return only JSON with keys status and purpose. status must be ok; purpose must be evidence extraction."}
    ],
    "format": {
      "type": "object",
      "properties": {
        "status": {"type": "string"},
        "purpose": {"type": "string"}
      },
      "required": ["status", "purpose"]
    },
    "options": {
      "temperature": 0,
      "seed": 42,
      "num_ctx": 8192
    }
  }' | python3 -m json.tool
```

Check the loaded model and context allocation:

```bash
ollama ps
```

## 6. Python environment

Create a separate environment outside the repository source tree:

```bash
python3 -m venv "$HOME/hrp-lab/venvs/evidence-ingestion"
source "$HOME/hrp-lab/venvs/evidence-ingestion/bin/activate"
python -m pip install --upgrade pip wheel
python -m pip install ollama pydantic httpx tenacity orjson
```

Later parser/index dependencies should be pinned in a repository requirements or lock file after the first benchmark.

## 7. Document parsing cascade

### Fast baseline

Use existing command-line tools for every PDF:

```bash
pdfinfo paper.pdf
pdftotext -layout paper.pdf paper.txt
```

These provide a quick integrity and text-coverage check.

### Academic-paper structure

Use a local GROBID CPU container when structured sections, references and citation metadata are required:

```bash
docker run --rm --init --ulimit core=0 \
  -p 8070:8070 \
  grobid/grobid:0.9.1-crf
```

### Layout/table fallback

Use Docling for papers whose layout, tables, formulas or reading order are not adequately represented by the fast/GROBID path. Install it only after the baseline environment is working:

```bash
source "$HOME/hrp-lab/venvs/evidence-ingestion/bin/activate"
python -m pip install docling
```

OCR should be used only for genuinely scanned documents and must be flagged in parse provenance.

## 8. Local corpus layout

```text
$HOME/hrp-lab/source-corpus/
  <source-id>/
    original/
      paper.pdf
      supplement.pdf
      protocol.pdf
    parsed/
      paper.txt
      paper.tei.xml
      paper.docling.json
      paper.md
    manifests/
      acquisition.json
      parse.json
      chunks.jsonl
      extraction.json
      validation.json
```

The Registry stores hashes, provenance and locators. Licensed source bytes remain outside Git.

## 9. Structured-output rule

Every extraction call must use a versioned JSON schema and validate the response with Pydantic or equivalent.

Every material value should include:

```text
value
status: extracted | inferred | not_reported | unresolved
source_anchor
verbatim_support_or_span
model_confidence
model_name
model_digest
prompt_version
schema_version
```

Use `temperature=0` for extraction and classification. Preserve raw model output for debugging, but admit only validated structured output to the candidate layer.

## 10. Chunking rule

Do not send an entire long paper repeatedly.

Create section-aware chunks with:

```text
source_version_id
page_start/page_end
section_path
chunk_index
text_sha256
parser_version
```

Recommended initial target:

```text
1,000–2,500 tokens per chunk
small overlap only where section continuity requires it
```

Retrieve the relevant sections before each field extraction. Methods, results, appendices, protocols and registration materials should remain separately addressable.

## 11. Two-pass extraction

### Pass A — field extraction

Run the workhorse model on retrieved sections and return schema-constrained candidates with anchors.

### Pass B — verification

Use one or more of:

- repeat extraction with a different prompt view;
- deterministic parser/metadata comparison;
- contradiction and missingness check;
- optional larger-model review;
- targeted human exception review.

Only fields passing the automatic gate become machine-screened.

## 12. First calibration benchmark

Use the existing 18-source Registry as the ontology/reference set, with special full-text quality cases such as the completed `rt-2026-001`, `rt-2026-002`, `rt-2026-006` and `rt-2026-014` appraisal work where source material is available.

Measure:

```text
JSON/schema pass rate
source-anchor validity
study-design accuracy
population extraction accuracy
intervention route accuracy
outcome/timepoint accuracy
missingness accuracy
unsupported-assertion rate
field-level agreement with reviewed Registry values
runtime and memory per paper
```

Do not tune and score on exactly the same fields. Preserve a small held-out set and rotate held-out sources while the corpus is small.

## 13. Acceptance gates for the first 100-source run

Minimum initial targets should be set empirically after the calibration run, but the pipeline must at least require:

- near-perfect schema validity after retry;
- no admission of unanchored decision-relevant fields;
- zero silent overwrite of human authority;
- explicit unresolved/missing states;
- reproducible model/prompt/schema provenance;
- a bounded unsupported-assertion rate;
- automatic exception routing;
- stable throughput and recoverable failures.

## 14. When to add the larger model

Pull the optional second-pass model only when the 9B benchmark shows that it materially improves one or more of:

- source-anchor correctness;
- complex design extraction;
- contradiction detection;
- route or mechanism classification;
- recommendation correction rate.

Then:

```bash
ollama pull qwen3:30b
```

Because it is approximately 19 GB, run it at a conservative context length and one job at a time on a 32 GB host.

## 15. Resource controls

Initial worker settings:

```text
qwen3.5:9b extraction concurrency: 1
embedding batch size: small, then benchmark upward
PDF parser concurrency: 1–2
second-pass 30B concurrency: 1
context: retrieve sections; do not default to maximum context
```

Log:

```text
wall-clock time
prompt/evaluation token counts
peak memory if available
retry count
failure reason
```

## 16. Security and governance

- Bind Ollama to localhost unless an authenticated network boundary is deliberately configured.
- Do not place publisher credentials, cookies or institutional tokens in prompts or manifests.
- Do not copy licensed PDFs into Git.
- Do not allow a local model to create human-reviewed or release-approved provenance.
- Do not send CSI person/session data into the scientific Registry.
- Use recommendation review and sanitised correction signals for feedback.

## 17. Immediate implementation sequence

```text
1. Install Ollama.
2. Pull qwen3.5:9b and qwen3-embedding:0.6b.
3. Verify structured JSON output.
4. Create the ingestion Python environment.
5. Build a one-paper parser/extractor for rt-2026-014.
6. Compare extraction to the reviewed rt-014 Registry state.
7. Generalise to a 10-paper calibration batch.
8. Add automatic admission/exception gates.
9. Add Evidence Operations Dashboard views.
10. Ingest the first focused 50–100-source corpus.
```
