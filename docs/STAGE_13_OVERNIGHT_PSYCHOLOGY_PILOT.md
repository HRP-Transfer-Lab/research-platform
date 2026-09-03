# Stage 13 Overnight Psychology Intervention Pilot

**Status:** Ready for local smoke test and overnight candidate run  
**Date:** 3 September 2026  
**Branch:** `stage13-scaled-ingestion`

## Objective

Use the NiPoGi to discover and locally classify **50–100 additional psychology intervention and intervention-relevant papers** without creating scientific authority or requiring paper-by-paper human approval.

The overnight vertical slice is:

```text
versioned psychology query portfolio
→ Europe PMC core metadata + abstracts
→ DOI/PMID/title deduplication
→ exclusion of the 18-source seed
→ balanced candidate selection
→ Qwen 3.5 4B structured abstract screening
→ parser-owned title/abstract evidence-unit references
→ ranked full-text screening queue
```

This is a candidate-generation and abstract-screening run. It is not full-text scientific appraisal.

## Why this provider for the first overnight run

Europe PMC provides a public literature-search API with core publication metadata, abstracts and available full-text links. This allows the first run to operate without a separate commercial search service or OpenAlex key.

OpenAlex can be added as a second discovery provider after a key is configured. The first run does not need it.

## Search scope

The versioned configuration searches ten evidence families:

```text
cognitive training and transfer
attention and cognitive-control interventions
reasoning and problem-solving interventions
metacognition and learning-strategy interventions
self-regulation and implementation interventions
stress/emotion regulation and cognitive performance
digital psychological and behavioural interventions
human–AI cognition and learning interventions
workplace cognitive/workflow interventions
behaviour-change and functional interventions
```

Default date range:

```text
2021-01-01 to 2026-09-03
```

Default targets:

```text
140 balanced discovery candidates
100 local abstract classifications
```

## Classification contract

For every title/abstract candidate, the local model returns:

```text
screening decision: include / maybe / exclude
paper role
design family
intervention family
candidate Transfer Route(s)
capacity / coupling / niche / mixed relevance
population, intervention and comparator summary
outcome family
transfer signals
full-text priority
missing information required from full text
abstract-only confidence
screening rationale
```

The model cites immutable title/abstract evidence-unit IDs rather than inventing quotations or page numbers.

## Governance boundary

The run must always report:

```text
REGISTRY_MUTATED|0
SCIENTIFIC_STATE_MUTATED|0
HISTORICAL_RELEASE_MUTATED|0
CSI_GATEWAY_MUTATED|0
MACHINE_SCREENED_STATUS_CREATED|0
HUMAN_AUTHORITY_CREATED|0
```

An `include` classification means only:

> This candidate is sufficiently relevant to prioritise for full-text acquisition and screening.

It does not mean:

```text
efficacy established
quality or RoB approved
transfer established
certainty established
CSI recommendation authorised
source admitted to an approved release
```

## Resumability

Each candidate is checkpointed independently under:

```text
<run-dir>/classification/items/
```

Rerunning the same command with the same `--run-dir` reuses valid completed classifications and continues from the next unresolved candidate.

Do not use `--force-classification` unless intentionally invalidating all existing local classifications for that run.

## Outputs

```text
<run-dir>/discovery.json
<run-dir>/run-state.json
<run-dir>/overnight.log
<run-dir>/pid

<run-dir>/classification/items/*.json
<run-dir>/classification/classified-candidates.jsonl
<run-dir>/classification/ranked-candidates.csv
<run-dir>/classification/selected-for-fulltext-screening.json
<run-dir>/classification/summary.json
```

The ranked CSV is the easiest initial review surface. The selected JSON becomes the input for the next OA-resolution and full-text acquisition phase.

## Smoke test

```bash
SMOKE_DIR="$HOME/hrp-lab/source-corpus/_overnight/smoke-$(date +%Y%m%d-%H%M%S)"

python3 -u \
  components/evidence-registry/scripts/stage13_run_overnight_psychology_pilot.py \
  --email admin@iqmindware.com \
  --run-dir "$SMOKE_DIR" \
  --target-candidates 15 \
  --max-items 3
```

A successful smoke test should classify three candidates and create the summary, ranked CSV and selected manifest.

## Overnight launch

```bash
RUN_DIR="$HOME/hrp-lab/source-corpus/_overnight/psychology-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"

nohup systemd-inhibit \
  --what=sleep \
  --why="HRP Stage 13 overnight psychology evidence pilot" \
  python3 -u \
  components/evidence-registry/scripts/stage13_run_overnight_psychology_pilot.py \
  --email admin@iqmindware.com \
  --run-dir "$RUN_DIR" \
  --target-candidates 140 \
  --max-items 100 \
  > "$RUN_DIR/overnight.log" 2>&1 &

echo $! | tee "$RUN_DIR/pid"
echo "RUN_DIR=$RUN_DIR"
```

## Monitor

```bash
tail -f "$RUN_DIR/overnight.log"
```

In another terminal:

```bash
ps -p "$(cat "$RUN_DIR/pid")" -o pid,etime,cmd
ollama ps
```

Exit `tail -f` with `Ctrl-C`; this does not stop the pipeline.

## Resume after interruption

```bash
nohup systemd-inhibit \
  --what=sleep \
  --why="Resume HRP Stage 13 overnight psychology evidence pilot" \
  python3 -u \
  components/evidence-registry/scripts/stage13_run_overnight_psychology_pilot.py \
  --email admin@iqmindware.com \
  --run-dir "$RUN_DIR" \
  --target-candidates 140 \
  --max-items 100 \
  > "$RUN_DIR/overnight-resume.log" 2>&1 &

echo $! | tee "$RUN_DIR/pid"
```

## Next-morning gate

Review:

```text
classification/summary.json
classification/ranked-candidates.csv
classification/selected-for-fulltext-screening.json
```

Then:

```text
selected candidates
→ OA resolution and lawful PDF acquisition
→ parse-quality gate
→ source-kind-aware full-text extraction
→ automatic support/consistency checks
→ machine screen or quarantine
→ risk-weighted QA sample (maximum routine 10%)
→ working evidence index
→ CSI recommendation evidence bundles
```

Human authority remains concentrated at recommendation review, promoted propositions/syntheses/claims, consequential uses, exception cases and bounded quality assurance—not universal paper approval.
