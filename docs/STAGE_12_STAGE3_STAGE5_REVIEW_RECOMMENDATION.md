# Stage 12 — Stage 3 residual and Stage 5 complete human-review recommendation

**Branch:** `evidence-registry-v1.1`  
**Scientific state revision reviewed:** `1785`  
**Scope:** local Evidence Registry v1.1 review closure only; no hosted release or CSI Gateway mutation.

## Recommendation

### Stage 3 residual extraction status

Packet: `stage3_extraction_status`  
Packet SHA-256: `03d1c719c6564f1bfbdc14ecf808ae7d10cd24c37dc5e23d71fe70a9aa43301a`  
Decisions: **17**  
Recommendation: **approve 17 / correct 0 / reject 0**.

The 13 `component_target_extraction_status` rows correctly remain `partially_extracted`: at least one target mapping has been reviewed for each component, but the Registry does not claim that every scientifically relevant target has been exhaustively extracted. The four `source_version_mechanism_status` rows likewise remain `partially_extracted`: reviewed mechanism assertions exist, without implying exhaustive mechanism extraction.

These are provenance/completeness decisions only. Approval should change the provenance authority to human review while preserving the scientific status values.

### Stage 5 complete study design

Packet: `stage5_complete`  
Packet SHA-256: `55185952c5760c1c3fa1ece67f558811d8e2d2260ffa556cfc03374b9764faef`  
Decisions: **107**  
Recommendation: **approve 107 / correct 0 / reject 0**.

The packet consists of 71 normalized structural decisions plus 36 study-level arm/contrast extraction-status decisions. The earlier 71-decision `stage5_design` packet is superseded for approval purposes by this complete 107-decision packet.

Scientific review found the following boundaries appropriate:

- explicit randomized, active-control, cluster-group and factorial condition structures are represented where recoverable from the seed;
- per-arm sample sizes are not inferred when absent;
- controls remain `unclear` where the seed does not justify a stronger role label;
- source-level systematic/scoping reviews are not converted into synthetic trial arms;
- secondary/mechanistic studies whose condition structures are insufficiently represented remain `not_yet_extracted` rather than being guessed;
- the kindergarten secondary analysis spanning multiple underlying randomized studies remains `not_applicable` to a single synthetic source-level arm set;
- the observational offloading study remains `not_applicable` to discrete assigned arms/contrasts because the seed represents continuous offloading constructs;
- the AI × mastery study is `partially_extracted`: four recoverable policy conditions are represented while the additional topic dimension is explicitly not reconstructed;
- no unprivileged factorial or pairwise contrast is fabricated where the seed does not support one;
- measurement-only conditions are represented as such and not treated as intervention arms.

## Governance boundary

Approval must:

1. revalidate the packet against the unchanged scientific-state revision and row snapshots;
2. require the exact packet SHA and stable scientific-decision SHA;
3. create Stage 11 human adjudication/authority for every accepted decision;
4. update only review/provenance fields in normalized state, preserving the reviewed scientific values;
5. abort the entire batch transaction on any row mismatch;
6. leave historical release `2026-08-23` and `csi-evidence-v1` unchanged.

No Registry release publication is authorised by this review recommendation.
