# NiPoGi Local Model Ingestion Runbook

**Status:** Stage 13 active implementation runbook  
**Updated:** 2 September 2026  
**Target host:** NiPoGi / `kastel-mini`  
**Observed runtime:** Ollama on CPU for Qwen 3.5 models  
**Purpose:** Scale the HRP Transfer Evidence Registry from the 18-source calibration set towards 100–1,000 machine-screened studies while preserving evidence provenance, targeted human review and CSI recommendation governance.

## 1. Operating rule

Use deterministic software for source identity, acquisition, hashing, parsing, schema checks and release bookkeeping. Use local language models for semantic extraction, classification, comparison and candidate generation.

```text
metadata APIs / source files
→ canonical identity and deduplication
→ acquisition + SHA-256
→ deterministic PDF parsing
→ section/page retrieval
→ local schema-constrained extraction
→ source-anchor validation
→ model agreement / exception routing
→ machine-screened working corpus
→ CSI recommendation review
→ targeted scientific correction or promotion
```

A local model may create a candidate. It may not create human authority, silently overwrite a reviewed value, publish a formal scientific claim or make a consequential CSI decision.

## 2. Measured NiPoGi model benchmark

The first CPU benchmark used an approximately 150-word generation task at an 8,192-token context.

| Model | Wall time | Prompt tokens/s | Output tokens/s |
|---|---:|---:|---:|
| `qwen3.5:4b` | 32.72 s | 30.55 | 9.32 |
| `qwen3.5:9b` | 50.89 s | 16.54 | 5.86 |

Derived result:

```text
4B end-to-end speed-up over 9B: 1.555×
4B wall-time reduction:            35.7%
4B prompt-processing speed-up:     1.847×
4B output-generation speed-up:     1.590×
```

This establishes `qwen3.5:4b` as the **provisional first-pass candidate on speed only**. Scientific adequacy depends on field accuracy, missingness behaviour, source-anchor validity and unsupported-assertion rates.

The machine-readable decision is stored in:

```text
components/evidence-registry/config/stage13_nipogi_model_cascade.v1.json
```

## 3. Current model cascade

### Tier 0 — deterministic

Use ordinary software for:

- DOI and identifier normalisation;
- source-version resolution and deduplication;
- access status;
- file hashing and page count;
- PDF-to-text conversion;
- schema and taxonomy validation;
- numerical and cross-field consistency checks.

### Tier 1 — routine local extraction

```text
qwen3.5:4b
```

Provisional uses:

- schema-constrained study and population extraction;
- intervention, mechanism, route and outcome candidates;
- evidence-span selection;
- explicit missingness;
- first-pass classification.

It becomes the routine workhorse only if it reaches the stricter calibration threshold across several source types.

### Tier 2 — selective local verification

```text
qwen3.5:9b
```

Invoke when one or more of these applies:

```text
schema failure after retry
low field confidence
weak or invalid source anchor
deterministic cross-check disagreement
4B/9B disagreement
novel study design or taxonomy class
decision-relevant field
single-source recommendation dependence
recommendation correction
targeted QA sample
```

Do not run 9B on every field by default unless calibration shows that the 4B model is inadequate without universal verification.

### Retrieval model

```text
qwen3-embedding:0.6b
```

Use after the core extraction calibration for:

- section and chunk retrieval;
- similar-study retrieval;
- duplicate-candidate support;
- evidence-query expansion.

### Larger model

```text
qwen3:30b
```

Do not download yet. Add it only if measured improvements in difficult extraction, contradiction detection or recommendation-level error justify the memory and latency cost.

## 4. Installed service checks

```bash
ollama --version
systemctl is-active ollama
curl -s http://127.0.0.1:11434/api/tags | python3 -m json.tool
ollama list
```

The API should remain bound to localhost unless an authenticated network boundary is deliberately configured.

## 5. First scientific calibration: `rt-2026-014`

The first real calibration uses the registered 73-page `ai26-1552.pdf` and ten fields from its reviewed Registry appraisal.

Tracked calibration assets:

```text
components/evidence-registry/config/
  stage13_calibration_rt014.v1.json

components/evidence-registry/scripts/
  stage13_calibrate_local_extraction.py
```

The script:

1. verifies the 73-page PDF;
2. calculates its SHA-256;
3. parses it using `pdftotext -layout`;
4. retrieves high-relevance pages within an input-character budget;
5. sends the same anchored JSON extraction task to 4B and 9B;
6. validates structure;
7. verifies that each short supporting quotation occurs on the stated physical PDF page;
8. compares ten values with the reviewed calibration record;
9. writes local parse, extraction and validation manifests; and
10. leaves PostgreSQL, scientific authority, the historical release and CSI Gateway untouched.

Run:

```bash
python3 -u components/evidence-registry/scripts/stage13_calibrate_local_extraction.py \
  --pdf "$HOME/hrp-lab/source-corpus/rt-2026-014/ai26-1552.pdf"
```

No Python packages beyond the standard library are required for this first runner. `pdfinfo` and `pdftotext` are required from `poppler-utils`.

Outputs are written outside Git:

```text
$HOME/hrp-lab/source-corpus/rt-2026-014/
  parsed/
    ai26-1552.layout.txt
  manifests/stage13-local-calibration/
    parse-manifest.json
    qwen3.5_4b.json
    qwen3.5_9b.json
    summary.json
```

## 6. Calibration interpretation

Minimum compact calibration pass:

```text
schema valid
field accuracy ≥ 8/10
anchor validity ≥ 80%
```

Stricter single-source workhorse-candidate signal:

```text
schema valid
field accuracy ≥ 9/10
anchor validity ≥ 90%
```

Even a 10/10 result on `rt-014` does not authorise a general extraction model. Promotion requires a multi-source set containing different study designs, publication layouts, intervention types and missingness patterns.

Interpret results as follows:

### 4B passes the stricter threshold and approximates 9B

Use 4B for routine first-pass extraction. Route only flagged fields and sampled cases to 9B.

### 4B passes the minimum threshold but 9B is materially better

Use 4B to prefill straightforward fields and 9B for decision-relevant fields until the prompt/retrieval pipeline improves.

### 9B offers no material scientific gain

Retain it only for targeted disagreement and novelty cases rather than paying its latency on every source.

### Both models fail

Do not jump immediately to a 30B model. First inspect:

```text
retrieved pages
context truncation
schema design
prompt ambiguity
PDF parse quality
field ontology
quote-anchor normalisation
```

Fix the production line, rerun the affected cohort and resample.

The runner may exit with code `2` and print `REVIEW` if neither model reaches the minimum compact threshold. That is a calibration finding, not a Registry or database failure.

## 7. Parsing cascade

### Fast born-digital baseline

```bash
pdfinfo paper.pdf
pdftotext -layout paper.pdf paper.txt
```

### Academic structure

Use local GROBID when structured sections, bibliography and citation metadata are required.

### Layout and table fallback

Use Docling only where the fast/GROBID route does not preserve required layout, tables, equations or reading order.

### OCR

Use OCR only for genuinely scanned documents. Label OCR provenance separately and treat low OCR quality as an exception signal.

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

Current `rt-014` has its PDF directly under the source directory; the calibration runner supports that path. Licensed PDF bytes and parsed full text must remain outside Git.

## 9. Structured extraction contract

Every material extracted field should retain:

```text
value
status: extracted | inferred | not_reported | unresolved
physical PDF page or section anchor
short supporting source span
model confidence
model name and digest
prompt version
extraction schema version
parser version
source hash
```

Use temperature zero for extraction and classification. Preserve raw model output for debugging, but admit only validated structured output to the candidate layer.

## 10. Scaling sequence

### 18 → 100

```text
rt-014 single-paper calibration
→ 10-paper mixed-design calibration
→ automatic admission and exception gates
→ Evidence Operations Dashboard
→ focused 50–100-source ingestion
```

Measure:

```text
schema pass rate
source-anchor validity
field precision / recall / F1
controlled-vocabulary accuracy
missingness accuracy
unsupported-assertion rate
4B/9B disagreement
runtime and failures per source
recommendation acceptance/correction/abstention
```

### 100 → 300

Add:

- embedding-based section retrieval;
- model-cohort comparison;
- internal working evidence retrieval for CSI pilots;
- recommendation-level review and correction;
- proposition/synthesis families;
- outcome-linked feedback.

### 300 → 1,000

Add:

- continuous discovery and acquisition;
- scheduled parser/model cohorts;
- risk-weighted sampling;
- demand-led source prioritisation;
- batch promotion rather than paper-by-paper approval;
- system-learning dashboards.

## 11. Human review budget

Routine source-level human review is capped at:

```text
ceiling(10% of eligible machine-screened studies)
```

Allocate approximately:

```text
5% stratified random sample
5% targeted risk / novelty / recommendation-feedback sample
```

If the sample reveals a systematic defect:

```text
quarantine affected cohort
→ correct parser/prompt/model/schema/rule
→ rerun cohort
→ draw a fresh sample
```

Do not turn the remaining 90% into a universal manual backlog.

Human authority is concentrated on:

- CSI recommendations;
- exceptions implicated in mis-recommendations;
- promoted propositions, syntheses and public claims;
- consequential uses;
- the bounded 10% quality sample.

## 12. CSI integration boundary

The existing approved CSI Evidence Gateway remains release-pinned and read-only. Machine-screened evidence should enter a separately labelled authenticated working index for internal pilots; it must not masquerade as approved evidence.

CSI recommendations should expose:

```text
evidence bundle fingerprint
release-approved / human-reviewed / machine-screened composition
source/card IDs
material anchors
required caveats
excluded low-confidence fields
model and rule versions
abstention rationale
```

Recommendation review then provides:

```text
approve
correct
reject
defer
abstain
```

A sanitised source/field correction signal may return to the Registry. Raw person, employee, client, organisation or workflow-session data must not.

## 13. Immediate next actions

```text
1. Run the rt-014 4B/9B scientific extraction calibration.
2. Inspect field errors and invalid anchors.
3. Freeze or revise the first-pass/verification cascade.
4. Generalise the runner to a 10-paper mixed-design batch.
5. Add automatic machine-screening and quarantine records.
6. Add the Evidence Operations Dashboard.
7. Ingest the first focused 50–100-source corpus.
```
