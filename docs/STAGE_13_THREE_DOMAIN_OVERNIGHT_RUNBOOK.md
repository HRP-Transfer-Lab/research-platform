# Stage 13 Three-Domain Overnight Evidence Runbook

**Status:** Ready for NiPoGi smoke test and candidate-only overnight run  
**Date:** 3 September 2026  
**Branch:** `stage13-scaled-ingestion`

## 1. Tonight's attainable gate

The NiPoGi can now search for and locally classify up to 100 additional **title/abstract candidates** across three CSI domains:

```text
PERFORMANCE / WORK
cognitive performance
motivation and engagement
workplace wellbeing and resilience
workflow, interruption and decision systems
human–AI work

PERSONAL
self-directed cognitive performance
learning and study
reasoning and decision-making
habits, goals and self-regulation
personal wellbeing, resilience and cognitive ageing

HEALTH / CLINICAL-ADJACENT
psychological and behavioural support
cognitive rehabilitation
symptom self-management and functioning
adherence and participation
digital and cognitive-affective interventions
```

This run creates a ranked evidence-acquisition portfolio. It does **not** yet perform full-text scientific extraction or admit 100 papers to the Evidence Registry.

## 2. Search balance

The versioned configuration contains 15 interleaved query families:

```text
5 performance/work
5 personal
5 health/clinical-adjacent
```

Default run targets:

```text
180 deduplicated discovery candidates
100 local abstract classifications
approximately 34 / 33 / 33 query-origin balance
75 domain-balanced candidates for full-text acquisition
minimum 20 assigned candidates per domain in the full run
```

Papers may receive more than one semantic CSI-domain label. Query origin is retained as a retrieval clue but does not determine the model classification.

## 3. Domain-aware classification

Each locally classified candidate contains the existing intervention-intelligence fields plus:

```text
primary_csi_domain
csi_domains
application_targets
health_scope
```

Allowed primary domains:

```text
performance_work
personal
health_clinical_adjacent
cross_domain
not_applicable
```

The health scope distinguishes:

```text
non_health
health_clinical_adjacent
clinical_intervention_research
not_applicable
```

A clinical research paper may be discovered and prioritised, but abstract classification does not authorise clinical advice, treatment claims or autonomous recommendations.

## 4. Governance boundary

The overnight command must report:

```text
PDF_DOWNLOADS|0
REGISTRY_MUTATED|0
SCIENTIFIC_STATE_MUTATED|0
HISTORICAL_RELEASE_MUTATED|0
CSI_GATEWAY_MUTATED|0
MACHINE_SCREENED_STATUS_CREATED|0
HUMAN_AUTHORITY_CREATED|0
```

The result is a candidate queue for lawful full-text acquisition and subsequent evidence processing.

It does not establish:

```text
efficacy
quality or risk of bias
certainty
far transfer
clinical effectiveness
recommendation authority
release approval
```

## 5. Synchronise

```bash
git status --short
git fetch origin stage13-scaled-ingestion
git merge --ff-only origin/stage13-scaled-ingestion
git rev-parse --short HEAD
```

## 6. Compile and test

```bash
python3 -m py_compile \
  components/evidence-registry/scripts/stage13_discover_psychology_interventions.py \
  components/evidence-registry/scripts/stage13_classify_psychology_candidates.py \
  components/evidence-registry/scripts/stage13_classify_csi_domain_candidates.py \
  components/evidence-registry/scripts/stage13_run_overnight_three_domain_pilot.py \
  components/evidence-registry/scripts/test_stage13_overnight_psychology_pilot.py \
  components/evidence-registry/scripts/test_stage13_three_domain_pilot.py
```

```bash
python3 components/evidence-registry/scripts/test_stage13_overnight_psychology_pilot.py
python3 components/evidence-registry/scripts/test_stage13_three_domain_pilot.py
```

## 7. Three-item smoke test

The discovery configuration is interleaved by domain, so the first three balanced candidates should originate from one query in each domain when all three searches return eligible abstracts.

```bash
SMOKE_DIR="$HOME/hrp-lab/source-corpus/_overnight/three-domain-smoke-$(date +%Y%m%d-%H%M%S)"

python3 -u \
  components/evidence-registry/scripts/stage13_run_overnight_three_domain_pilot.py \
  --email admin@iqmindware.com \
  --run-dir "$SMOKE_DIR" \
  --target-candidates 15 \
  --max-items 3
```

A successful smoke test should finish with:

```text
classified_candidates|3
classification_failures|0
semantic_domain_coverage|performance_work|...
semantic_domain_coverage|personal|...
semantic_domain_coverage|health_clinical_adjacent|...
domain_gate_pass|1
STAGE 13 THREE-DOMAIN ABSTRACT CLASSIFICATION|PASS
STAGE 13 THREE-DOMAIN OVERNIGHT PILOT|PASS
```

The model may classify a query-origin candidate outside its originating domain when the abstract supports that decision. If the three-item gate is `PARTIAL`, inspect the classifications before launching the full run; do not force domain labels merely to satisfy a quota.

## 8. Overnight launch

```bash
RUN_DIR="$HOME/hrp-lab/source-corpus/_overnight/three-domain-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"

nohup systemd-inhibit \
  --what=sleep \
  --why="HRP Stage 13 three-domain evidence pilot" \
  python3 -u \
  components/evidence-registry/scripts/stage13_run_overnight_three_domain_pilot.py \
  --email admin@iqmindware.com \
  --run-dir "$RUN_DIR" \
  --target-candidates 180 \
  --max-items 100 \
  > "$RUN_DIR/overnight.log" 2>&1 &

echo $! | tee "$RUN_DIR/pid"
printf 'RUN_DIR=%s\n' "$RUN_DIR" | tee "$HOME/hrp-lab/source-corpus/_overnight/latest-three-domain-run.env"
```

## 9. Monitor without interrupting

```bash
tail -f "$RUN_DIR/overnight.log"
```

In a second terminal:

```bash
ps -p "$(cat "$RUN_DIR/pid")" -o pid,etime,cmd
ollama ps
```

Use `Ctrl-C` to leave `tail -f`; the background process continues.

## 10. Resume the same run

Set `RUN_DIR` to the printed directory or recover it with:

```bash
source "$HOME/hrp-lab/source-corpus/_overnight/latest-three-domain-run.env"
```

Then:

```bash
nohup systemd-inhibit \
  --what=sleep \
  --why="Resume HRP Stage 13 three-domain evidence pilot" \
  python3 -u \
  components/evidence-registry/scripts/stage13_run_overnight_three_domain_pilot.py \
  --email admin@iqmindware.com \
  --run-dir "$RUN_DIR" \
  --target-candidates 180 \
  --max-items 100 \
  > "$RUN_DIR/overnight-resume.log" 2>&1 &

echo $! | tee "$RUN_DIR/pid"
```

Valid completed candidate records are reused automatically.

## 11. Outputs to inspect next morning

```text
$RUN_DIR/run-state.json
$RUN_DIR/discovery.json
$RUN_DIR/classification/summary.json
$RUN_DIR/classification/ranked-candidates.csv
$RUN_DIR/classification/domain-balanced-fulltext-portfolio.json
$RUN_DIR/classification/items/*.json
```

The domain-balanced portfolio is the hand-off to the next acquisition stage.

## 12. Scaling sequence after the overnight run

```text
100 abstract-classified candidates
→ inspect domain balance and error sample
→ resolve lawful OA locations for the balanced portfolio
→ acquire a first full-text tranche
→ parse-quality and canonicalisation gates
→ source-kind-aware full-text extraction
→ deterministic and 4B agreement checks
→ 9B only for disagreement/high-impact exceptions
→ screen or quarantine
→ maximum 10% routine study-level human QA
→ working evidence index
→ CSI evidence bundles and recommendation review
```

The eight current full-text papers remain the mixed-source engineering set. The overnight run expands the candidate funnel; it does not bypass the mixed-source validation gate.
