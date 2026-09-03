# Stage 13 — Mixed-Source Parse-Quality Gate

**Status:** Implemented local calibration gate  
**Purpose:** Determine which verified full-text PDFs can safely enter local structured extraction and which must be quarantined for parser fallback, inspection or reacquisition.

## Boundary

This gate is operational and local-manifest-only.

It does **not**:

- call Ollama;
- create extraction candidates;
- create `machine_screened`, `human_reviewed` or `release_approved` status;
- alter scientific authority;
- alter the immutable historical release;
- alter the approved CSI Gateway.

## Input

The script reads one latest verified `local_corpus` full-text artifact for each source whose acquisition status is `fulltext_verified`.

It therefore processes registered source documents rather than scanning arbitrary local files.

## Checks

For every selected PDF it verifies:

```text
registered SHA-256 == observed SHA-256
registered page count == pdfinfo page count
pdftotext physical pages == pdfinfo page count
parsed opening text matches DOI or title
text coverage is adequate
replacement/control-character damage is bounded
parser-owned spans can be generated
```

## Routes

```text
PASS
→ technically eligible for local extraction calibration

REVIEW
→ quarantine; inspect identity, OCR need or parser fallback

FAIL
→ quarantine; repair, reacquire or resolve integrity mismatch
```

A parse pass means only that the source is technically usable for extraction calibration. It is not a scientific appraisal.

## Files

Policy:

```text
components/evidence-registry/config/stage13_parse_quality_policy.v1.json
```

Runner:

```text
components/evidence-registry/scripts/stage13_parse_quality_batch.py
```

Tests:

```text
components/evidence-registry/scripts/test_stage13_parse_quality_batch.py
```

Local per-source outputs:

```text
$HOME/hrp-lab/source-corpus/<source-id>/parsed/<pdf-stem>.layout.txt
$HOME/hrp-lab/source-corpus/<source-id>/manifests/stage13-parse-quality/spans.jsonl
$HOME/hrp-lab/source-corpus/<source-id>/manifests/stage13-parse-quality/parse-quality.json
```

Batch output:

```text
$HOME/hrp-lab/source-corpus/_parsing/stage13-parse-quality-batch-<timestamp>.json
```

## Run

```bash
python3 -m py_compile \
  components/evidence-registry/scripts/stage13_parse_quality_batch.py \
  components/evidence-registry/scripts/test_stage13_parse_quality_batch.py

python3 \
  components/evidence-registry/scripts/test_stage13_parse_quality_batch.py

python3 -u \
  components/evidence-registry/scripts/stage13_parse_quality_batch.py
```

The expected current selection after recovery of `rt-2026-009` is eight verified local full texts.

## Next gate

```text
parse-quality batch
→ source-kind-aware field-family extraction
→ mixed-source 4B calibration
→ selective 9B disagreement review
→ screen-or-quarantine persistence
→ Evidence Operations Dashboard
```
