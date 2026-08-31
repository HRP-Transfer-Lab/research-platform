# Stage 12 review packet — Stage 5 complete study design — arms, components, contrasts and extraction status

- Packet: `stage5_complete`
- SHA-256: `55185952c5760c1c3fa1ece67f558811d8e2d2260ffa556cfc03374b9764faef`
- Scientific revision: `1785`
- Decisions: **107**
- Review units: **18**

> No item in this packet is approved by packet generation. Human review is required.

## rt-2026-001 — SPECTRA episodic-specificity training

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 1, "component_id": 1}`
- Stage 11 candidate: `87`
- Proposed value: `{"arm_id": 1, "component_id": 1, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `f9be5fd44042b64a98a4f1673637ddab8c4b20b621024650163866a8c2942429`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 1, "contrast_id": 1}`
- Stage 11 candidate: `113`
- Proposed value: `{"arm_id": 1, "contrast_coefficient": 1, "contrast_id": 1, "contrast_side": "focal", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `81913b838de9594e83a4bf743a40dc801eb6bff981bcc9ba7074c57c7296eafc`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 2, "contrast_id": 1}`
- Stage 11 candidate: `117`
- Proposed value: `{"arm_id": 2, "contrast_coefficient": -1, "contrast_id": 1, "contrast_side": "comparator", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `2fdbdffc518fe283dc525c01dbe4746c48c6ebe9cd1aee23f63e2c51250dbd75`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 1}`
- Stage 11 candidate: `58`
- Proposed value: `{"arm_description": null, "arm_id": 1, "arm_key": "spectra_training", "arm_label": "SPECTRA episodic-specificity training", "arm_role": "intervention", "assignment_structure": "parallel_group", "author_arm_label": "SPECTRA episodic-specificity training", "sample_json": {}, "study_id": 1}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `f8553c808baead11d578a8536b01357b04aa84b73c26c240c26e70265093dfdc`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 2}`
- Stage 11 candidate: `69`
- Proposed value: `{"arm_description": null, "arm_id": 2, "arm_key": "asso_active_control", "arm_label": "ASSO associative-memory active control", "arm_role": "active_control", "assignment_structure": "parallel_group", "author_arm_label": "ASSO associative word-picture recall training", "sample_json": {}, "study_id": 1}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `e0e7534381c980f9a4705568216de8f9ae39bd975abf5eff064180c0d7b0f9cf`

### `study_contrast`

- Surface mode: `ordinary`
- Key: `{"contrast_id": 1}`
- Stage 11 candidate: `105`
- Proposed value: `{"contrast_id": 1, "contrast_key": "spectra_vs_asso", "contrast_label": "SPECTRA vs ASSO active control", "contrast_type": "pairwise", "estimand_summary": null, "study_id": 1}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `3940fca9913cbf43e5f97b6c02f3110f0d779579795ebe4a1bba94e1a28961d3`

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 1}`
- Stage 11 candidate: `304`
- Proposed value: `{"arm_extraction_status": "partially_extracted", "study_id": 1}`
- Evidence basis: notes: Two-arm randomized active-control trial is explicit; per-arm sample counts were not extracted.
- Row snapshot: `481f692e7342a884035edf2c59a668d87ca4100f5af8aeab562af9cdc44e785e`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 1}`
- Stage 11 candidate: `322`
- Proposed value: `{"contrast_extraction_status": "partially_extracted", "study_id": 1}`
- Evidence basis: notes: Two-arm randomized active-control trial is explicit; per-arm sample counts were not extracted.
- Row snapshot: `481f692e7342a884035edf2c59a668d87ca4100f5af8aeab562af9cdc44e785e`

## rt-2026-010 — Serial dependence predicts generalization in perceptual learning

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 10}`
- Stage 11 candidate: `296`
- Proposed value: `{"arm_extraction_status": "not_yet_extracted", "study_id": 10}`
- Evidence basis: notes: Secondary analysis of perceptual-learning data; source conditions are not fully represented in the seed.
- Row snapshot: `ecb66ff07b0fc176e7904272bdec9a0bf3e215a7134be55561b5377eaefc4af3`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 10}`
- Stage 11 candidate: `314`
- Proposed value: `{"contrast_extraction_status": "not_yet_extracted", "study_id": 10}`
- Evidence basis: notes: Secondary analysis of perceptual-learning data; source conditions are not fully represented in the seed.
- Row snapshot: `ecb66ff07b0fc176e7904272bdec9a0bf3e215a7134be55561b5377eaefc4af3`

## rt-2026-011 — Neural mechanisms of error-driven learning in retrieval practice: confidence gates memory and metamemory networks

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 11}`
- Stage 11 candidate: `294`
- Proposed value: `{"arm_extraction_status": "not_yet_extracted", "study_id": 11}`
- Evidence basis: notes: Retrieval-practice mechanism experiment; condition structure is not sufficiently extracted in the seed.
- Row snapshot: `36e1c571ef6ccd00edc8d727a1c337e8a5222ed86eea403dcde5543eecf9b375`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 11}`
- Stage 11 candidate: `312`
- Proposed value: `{"contrast_extraction_status": "not_yet_extracted", "study_id": 11}`
- Evidence basis: notes: Retrieval-practice mechanism experiment; condition structure is not sufficiently extracted in the seed.
- Row snapshot: `36e1c571ef6ccd00edc8d727a1c337e8a5222ed86eea403dcde5543eecf9b375`

## rt-2026-012 — Stress drives the hippocampus to prioritize statistical prediction over episodic encoding

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 12}`
- Stage 11 candidate: `288`
- Proposed value: `{"arm_extraction_status": "not_yet_extracted", "study_id": 12}`
- Evidence basis: notes: Acute-stress mechanism experiment; stress/control condition structure is not sufficiently extracted in the seed.
- Row snapshot: `a81d3ee35c234dec5c7244edd7f7d67b18ef476c83675a81fc6cd38ab6c990c2`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 12}`
- Stage 11 candidate: `306`
- Proposed value: `{"contrast_extraction_status": "not_yet_extracted", "study_id": 12}`
- Evidence basis: notes: Acute-stress mechanism experiment; stress/control condition structure is not sufficiently extracted in the seed.
- Row snapshot: `a81d3ee35c234dec5c7244edd7f7d67b18ef476c83675a81fc6cd38ab6c990c2`

## rt-2026-013 — Immediate judgments of learning do not improve performance for educationally relevant materials: Evidence from key-term definitions, country outlines, and animal species

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 15, "contrast_id": 5}`
- Stage 11 candidate: `115`
- Proposed value: `{"arm_id": 15, "contrast_coefficient": 1, "contrast_id": 5, "contrast_side": "focal", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `c61dbba364d47653e5b6466d96e889c810b8ecd3ebe06c164bdd238ca95e6f81`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 16, "contrast_id": 5}`
- Stage 11 candidate: `116`
- Proposed value: `{"arm_id": 16, "contrast_coefficient": -1, "contrast_id": 5, "contrast_side": "comparator", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `0031493825887f6c64e8380866fdb7692e7787e321493488b08eeaf73da2aa7e`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 15}`
- Stage 11 candidate: `64`
- Proposed value: `{"arm_description": null, "arm_id": 15, "arm_key": "jol_during_study", "arm_label": "Immediate judgment-of-learning prompts", "arm_role": "experimental_condition", "assignment_structure": "unclear", "author_arm_label": "JOL during study", "sample_json": {}, "study_id": 13}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `7ea9aedaa4bfa3753a6c21755a0ec101a381b291e479ea29914b14cc42f91b5e`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 16}`
- Stage 11 candidate: `65`
- Proposed value: `{"arm_description": null, "arm_id": 16, "arm_key": "no_jol", "arm_label": "No JOL", "arm_role": "reference", "assignment_structure": "unclear", "author_arm_label": "no JOL", "sample_json": {}, "study_id": 13}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `bb9557f49a159021188884e37cd9287def5e0c7483a1876fd8d1d74329c3d90e`

### `study_contrast`

- Surface mode: `ordinary`
- Key: `{"contrast_id": 5}`
- Stage 11 candidate: `106`
- Proposed value: `{"contrast_id": 5, "contrast_key": "jol_vs_no_jol", "contrast_label": "JOL during study vs no JOL", "contrast_type": "pairwise", "estimand_summary": null, "study_id": 13}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `e5e2f9a68023d9e1d7dd4390f1fb219526a912ff63459059a4a283688c67992e`

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 13}`
- Stage 11 candidate: `287`
- Proposed value: `{"arm_extraction_status": "partially_extracted", "study_id": 13}`
- Evidence basis: notes: Across three controlled experiments the seed explicitly states JOL during study versus no JOL, but does not establish assignment structure for each experiment.
- Row snapshot: `ad23364c02acce90dfd4cbfb513e73dbd1ef67530d29af4396aa815c23f876f4`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 13}`
- Stage 11 candidate: `305`
- Proposed value: `{"contrast_extraction_status": "partially_extracted", "study_id": 13}`
- Evidence basis: notes: Across three controlled experiments the seed explicitly states JOL during study versus no JOL, but does not establish assignment structure for each experiment.
- Row snapshot: `ad23364c02acce90dfd4cbfb513e73dbd1ef67530d29af4396aa815c23f876f4`

## rt-2026-014 — mastery progression policy

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 18, "component_id": 10}`
- Stage 11 candidate: `92`
- Proposed value: `{"arm_id": 18, "component_id": 10, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `0868c958a2330210ee15c17d1538276f69646fc873d5bee118201a37c26bf69f`

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 19, "component_id": 9}`
- Stage 11 candidate: `93`
- Proposed value: `{"arm_id": 19, "component_id": 9, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `079f52000fb2e9d72a45b5221160f1a953f1423858ea7df17ed7742ff69fc88d`

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 20, "component_id": 10}`
- Stage 11 candidate: `95`
- Proposed value: `{"arm_id": 20, "component_id": 10, "membership_role": "shared", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `251628207a30243be99e771596e9683c53c0454d382dc1b958ad9a08844f32e0`

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 20, "component_id": 9}`
- Stage 11 candidate: `94`
- Proposed value: `{"arm_id": 20, "component_id": 9, "membership_role": "shared", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `e22125372b8c90b86cf61fe597b54e6030c2fd600dbf1933f567344eee5252f3`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 17}`
- Stage 11 candidate: `66`
- Proposed value: `{"arm_description": null, "arm_id": 17, "arm_key": "cal_nonmastery", "arm_label": "CAL-only + non-mastery progression", "arm_role": "reference", "assignment_structure": "factorial_cell", "author_arm_label": "CAL-only + non-mastery", "sample_json": {}, "study_id": 14}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `f29f826029638f562568e7d349d9fe884c77832605a82caf959f9d80c131efe5`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 18}`
- Stage 11 candidate: `67`
- Proposed value: `{"arm_description": null, "arm_id": 18, "arm_key": "cal_mastery", "arm_label": "CAL-only + mastery progression", "arm_role": "intervention", "assignment_structure": "factorial_cell", "author_arm_label": "CAL-only + mastery", "sample_json": {}, "study_id": 14}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `c1e2f601b6bad8b5de5d5656edfd481ca3ec9fe8e0718a4908908bff7e32dae2`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 19}`
- Stage 11 candidate: `68`
- Proposed value: `{"arm_description": null, "arm_id": 19, "arm_key": "ai_nonmastery", "arm_label": "AI tutoring + non-mastery progression", "arm_role": "intervention", "assignment_structure": "factorial_cell", "author_arm_label": "AI + non-mastery", "sample_json": {}, "study_id": 14}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `f66c01ae461e1433c44009d3111cefbcca203730b740d7859f1aa88281931dc2`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 20}`
- Stage 11 candidate: `70`
- Proposed value: `{"arm_description": null, "arm_id": 20, "arm_key": "ai_mastery", "arm_label": "AI tutoring + mastery progression", "arm_role": "intervention", "assignment_structure": "factorial_cell", "author_arm_label": "AI + mastery", "sample_json": {}, "study_id": 14}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `0532e380a92b87785e847231b0923a3a45578677fcd302d402decd7e787100ef`

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 14}`
- Stage 11 candidate: `289`
- Proposed value: `{"arm_extraction_status": "partially_extracted", "study_id": 14}`
- Evidence basis: notes: AI support x mastery yields four recoverable policy cells. Topic is an additional factorial dimension but is not expanded because its assignment structure is not sufficiently represented.
- Row snapshot: `86591ee4d1bce233a259dc24453fc021cc58904b90ab019d3515993a7c8173e5`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 14}`
- Stage 11 candidate: `307`
- Proposed value: `{"contrast_extraction_status": "not_yet_extracted", "study_id": 14}`
- Evidence basis: notes: AI support x mastery yields four recoverable policy cells. Topic is an additional factorial dimension but is not expanded because its assignment structure is not sufficiently represented.
- Row snapshot: `86591ee4d1bce233a259dc24453fc021cc58904b90ab019d3515993a7c8173e5`

## rt-2026-015 — integrate

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 22, "component_id": 11}`
- Stage 11 candidate: `96`
- Proposed value: `{"arm_id": 22, "component_id": 11, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `646f94058925d208824c3504b7fe715e065a9c2f94fe0fa246198a6c5e86ab89`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 21, "contrast_id": 6}`
- Stage 11 candidate: `118`
- Proposed value: `{"arm_id": 21, "contrast_coefficient": -1, "contrast_id": 6, "contrast_side": "comparator", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `3090104762cea5a4c0d715f2e21b20c71c4376f67b6b454734f04f64b0c5aa36`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 22, "contrast_id": 6}`
- Stage 11 candidate: `119`
- Proposed value: `{"arm_id": 22, "contrast_coefficient": 1, "contrast_id": 6, "contrast_side": "focal", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `1c12c8ef78e482d5ab95386a98460ed244f104d0640c3da61ea6c2c1c250e246`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 22, "contrast_id": 7}`
- Stage 11 candidate: `120`
- Proposed value: `{"arm_id": 22, "contrast_coefficient": 1, "contrast_id": 7, "contrast_side": "focal", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `58830bf4e989b57ff87f2fe741407ef0cbabfe8ecfdfb90a818c7a5b6a65eae9`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 23, "contrast_id": 7}`
- Stage 11 candidate: `121`
- Proposed value: `{"arm_id": 23, "contrast_coefficient": -1, "contrast_id": 7, "contrast_side": "comparator", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `84ea4a8c1f979fa8f7d56f92cf142f74389433492126514b6dcb1f45858d7f38`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 21}`
- Stage 11 candidate: `71`
- Proposed value: `{"arm_description": null, "arm_id": 21, "arm_key": "no_ai", "arm_label": "No AI", "arm_role": "reference", "assignment_structure": "cluster_group", "author_arm_label": "no AI", "sample_json": {}, "study_id": 15}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `6f300322bb35344f127a6d96efcd69af53c709c53cd14a5610cd1b0832a8507b`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 22}`
- Stage 11 candidate: `72`
- Proposed value: `{"arm_description": null, "arm_id": 22, "arm_key": "bounded_ai_reflection", "arm_label": "Bounded AI + compulsory reflection", "arm_role": "intervention", "assignment_structure": "cluster_group", "author_arm_label": "bounded AI + compulsory reflection", "sample_json": {}, "study_id": 15}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `03be918574a3a502ff9553e066b8b3c8d750ea1a62bf83e4f4008e6b9f8decb0`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 23}`
- Stage 11 candidate: `73`
- Proposed value: `{"arm_description": null, "arm_id": 23, "arm_key": "open_ai", "arm_label": "Open AI collaboration", "arm_role": "alternative_intervention", "assignment_structure": "cluster_group", "author_arm_label": "open AI collaboration", "sample_json": {}, "study_id": 15}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `c9da7f86209103e653bbbe6e2ae951b3d90961349f91cd1fe3ee61a89b76a74c`

### `study_contrast`

- Surface mode: `ordinary`
- Key: `{"contrast_id": 6}`
- Stage 11 candidate: `107`
- Proposed value: `{"contrast_id": 6, "contrast_key": "bounded_vs_no_ai", "contrast_label": "Bounded AI + reflection vs no AI", "contrast_type": "multiarm_pairwise", "estimand_summary": null, "study_id": 15}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `7d1a0d21e0f399e9b7933c6b304df4cb954f4b6c376deb3d6f7925f1d0df024c`

### `study_contrast`

- Surface mode: `ordinary`
- Key: `{"contrast_id": 7}`
- Stage 11 candidate: `108`
- Proposed value: `{"contrast_id": 7, "contrast_key": "bounded_vs_open_ai", "contrast_label": "Bounded AI + reflection vs open AI", "contrast_type": "multiarm_pairwise", "estimand_summary": null, "study_id": 15}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `5d43641ef7619e34d27eacb0acf00b750674fd75b91fcd6a22565fc43836e204`

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 15}`
- Stage 11 candidate: `300`
- Proposed value: `{"arm_extraction_status": "partially_extracted", "study_id": 15}`
- Evidence basis: notes: Three quasi-experimental classroom conditions are explicit; six intact classes support cluster-group representation but per-condition class counts are not extracted.
- Row snapshot: `2359a6c318673a1f572a4ee4f0795108961f66cb12d51eac0f29c0e75ff4b970`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 15}`
- Stage 11 candidate: `318`
- Proposed value: `{"contrast_extraction_status": "partially_extracted", "study_id": 15}`
- Evidence basis: notes: Three quasi-experimental classroom conditions are explicit; six intact classes support cluster-group representation but per-condition class counts are not extracted.
- Row snapshot: `2359a6c318673a1f572a4ee4f0795108961f66cb12d51eac0f29c0e75ff4b970`

## rt-2026-016 — redesign

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 25, "component_id": 12}`
- Stage 11 candidate: `97`
- Proposed value: `{"arm_id": 25, "component_id": 12, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `b3e01aea346d346555b85c194387cfd4c6ada735d88ee78b6d590c0037e47b97`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 24, "contrast_id": 8}`
- Stage 11 candidate: `122`
- Proposed value: `{"arm_id": 24, "contrast_coefficient": -1, "contrast_id": 8, "contrast_side": "comparator", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `a0c07c8b3924e801826270a103e64fc153a2ab2fb05f5630d71665e0a624d237`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 25, "contrast_id": 8}`
- Stage 11 candidate: `123`
- Proposed value: `{"arm_id": 25, "contrast_coefficient": 1, "contrast_id": 8, "contrast_side": "focal", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `e5bf81207a830d3b42e94c45bc809564cc62952c88c3c749d9091ea873188bcb`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 24}`
- Stage 11 candidate: `74`
- Proposed value: `{"arm_description": null, "arm_id": 24, "arm_key": "independent_completion", "arm_label": "Independent completion", "arm_role": "reference", "assignment_structure": "unclear", "author_arm_label": "independent completion", "sample_json": {}, "study_id": 16}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `0cf2a9da21dba637bb36aa81891869d7a8e24ee453f8ff3ea0c3e06704b924f2`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 25}`
- Stage 11 candidate: `75`
- Proposed value: `{"arm_description": null, "arm_id": 25, "arm_key": "ai_assisted_completion", "arm_label": "AI-assisted completion", "arm_role": "intervention", "assignment_structure": "unclear", "author_arm_label": "AI-assisted completion", "sample_json": {}, "study_id": 16}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `0c23e8b262b9c63fc86b52f1dc528408a292c31ec7d649c2b43b482aa071601d`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 26}`
- Stage 11 candidate: `76`
- Proposed value: `{"arm_description": null, "arm_id": 26, "arm_key": "completion_time_prediction", "arm_label": "Prediction of completion time", "arm_role": "measurement_condition", "assignment_structure": "unclear", "author_arm_label": "prediction of completion time", "sample_json": {}, "study_id": 16}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `0593bce5e6866509cde7d4deb5fe4691af8329385b577135daa8e510cffb6740`

### `study_contrast`

- Surface mode: `ordinary`
- Key: `{"contrast_id": 8}`
- Stage 11 candidate: `109`
- Proposed value: `{"contrast_id": 8, "contrast_key": "ai_vs_independent", "contrast_label": "AI-assisted vs independent completion", "contrast_type": "pairwise", "estimand_summary": null, "study_id": 16}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `fcf3b1a8446f685ee96396e35c0818e7d02f2ab639d041974836cb592dc36887`

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 16}`
- Stage 11 candidate: `290`
- Proposed value: `{"arm_extraction_status": "partially_extracted", "study_id": 16}`
- Evidence basis: notes: Independent completion, AI-assisted completion and prediction are explicit; prediction is represented as a measurement condition rather than an intervention arm.
- Row snapshot: `49fb49a05c22f3f7317b29edc051fad0873116e771438d438c2457ca0463d92d`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 16}`
- Stage 11 candidate: `308`
- Proposed value: `{"contrast_extraction_status": "partially_extracted", "study_id": 16}`
- Evidence basis: notes: Independent completion, AI-assisted completion and prediction are explicit; prediction is represented as a measurement condition rather than an intervention arm.
- Row snapshot: `49fb49a05c22f3f7317b29edc051fad0873116e771438d438c2457ca0463d92d`

## rt-2026-017 — redesign

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 27, "component_id": 13}`
- Stage 11 candidate: `98`
- Proposed value: `{"arm_id": 27, "component_id": 13, "membership_role": "shared", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `9b7e83b8d947bce4f4568340cf18f4a44bcade0b8924db912dfd57f07d06ed93`

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 28, "component_id": 13}`
- Stage 11 candidate: `99`
- Proposed value: `{"arm_id": 28, "component_id": 13, "membership_role": "shared", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `6b28e6aa9c05c95ff148937ca4dc4deefb594361fe5c151441ae98537bba3661`

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 29, "component_id": 13}`
- Stage 11 candidate: `100`
- Proposed value: `{"arm_id": 29, "component_id": 13, "membership_role": "shared", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `a6b89a9b4c7d72135e8479bb9e8f86507d12189bee319861e54dad699cf5a6f6`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 27}`
- Stage 11 candidate: `77`
- Proposed value: `{"arm_description": null, "arm_id": 27, "arm_key": "ai_planning", "arm_label": "AI support at planning", "arm_role": "experimental_condition", "assignment_structure": "parallel_group", "author_arm_label": "AI support at planning", "sample_json": {}, "study_id": 17}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `21bc030bcf32603ece5749c0ec50d8caee4ec7edd219a60b9807ba5de5f2a0a2`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 28}`
- Stage 11 candidate: `78`
- Proposed value: `{"arm_description": null, "arm_id": 28, "arm_key": "ai_drafting", "arm_label": "AI support at drafting", "arm_role": "experimental_condition", "assignment_structure": "parallel_group", "author_arm_label": "AI support at drafting", "sample_json": {}, "study_id": 17}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `be2f668b575b56a29bf9ad3f0a49a261db28a6122242c97942561550efee1222`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 29}`
- Stage 11 candidate: `79`
- Proposed value: `{"arm_description": null, "arm_id": 29, "arm_key": "ai_revision", "arm_label": "AI support at revision", "arm_role": "experimental_condition", "assignment_structure": "parallel_group", "author_arm_label": "AI support at revision", "sample_json": {}, "study_id": 17}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `fa16df6e9fd0e1c681fcb4cbfdd759833c987dce6ca271a8bf435acc5fe53240`

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 17}`
- Stage 11 candidate: `299`
- Proposed value: `{"arm_extraction_status": "partially_extracted", "study_id": 17}`
- Evidence basis: notes: Three between-subjects AI-support-stage conditions are explicit; no specific pairwise contrast is privileged by the seed.
- Row snapshot: `6c5f5044073e70da5e3203f40fc21d57718151fa55fa0a16ef80244bc6567bde`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 17}`
- Stage 11 candidate: `317`
- Proposed value: `{"contrast_extraction_status": "not_yet_extracted", "study_id": 17}`
- Evidence basis: notes: Three between-subjects AI-support-stage conditions are explicit; no specific pairwise contrast is privileged by the seed.
- Row snapshot: `6c5f5044073e70da5e3203f40fc21d57718151fa55fa0a16ef80244bc6567bde`

## rt-2026-018 — Not all cognitive offloading is equal: distinguishing dependent and autonomous offloading to generative AI

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 18}`
- Stage 11 candidate: `303`
- Proposed value: `{"arm_extraction_status": "not_applicable", "study_id": 18}`
- Evidence basis: notes: Three-wave observational survey models continuous offloading constructs rather than discrete assigned arms/groups in the seed.
- Row snapshot: `5d7bd03ea2d07877f9c8d045034c373725a23876d113654a3b49c717b82c120f`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 18}`
- Stage 11 candidate: `321`
- Proposed value: `{"contrast_extraction_status": "not_applicable", "study_id": 18}`
- Evidence basis: notes: Three-wave observational survey models continuous offloading constructs rather than discrete assigned arms/groups in the seed.
- Row snapshot: `5d7bd03ea2d07877f9c8d045034c373725a23876d113654a3b49c717b82c120f`

## rt-2026-002 — comprehensive executive-function training

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 3, "component_id": 2}`
- Stage 11 candidate: `101`
- Proposed value: `{"arm_id": 3, "component_id": 2, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `2e9693577a257919c1f763645bab2f8edb57116043a8eeb93523459800c742e9`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 3}`
- Stage 11 candidate: `80`
- Proposed value: `{"arm_description": null, "arm_id": 3, "arm_key": "executive_function_training", "arm_label": "Comprehensive executive-function training", "arm_role": "intervention", "assignment_structure": "parallel_group", "author_arm_label": "Comprehensive executive-function training", "sample_json": {}, "study_id": 2}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `dbbf2882358c3bba2330f6625068e0014a457227e32feb2050528cb6ddcaf332`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 4}`
- Stage 11 candidate: `81`
- Proposed value: `{"arm_description": null, "arm_id": 4, "arm_key": "behavioral_training", "arm_label": "Behavioral-training group", "arm_role": "alternative_intervention", "assignment_structure": "parallel_group", "author_arm_label": "Behavioral-training group", "sample_json": {}, "study_id": 2}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `0145b82e8b03bf68e730b9472d6a811672aaef1e6d1334d6883ca2ed4e731996`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 5}`
- Stage 11 candidate: `82`
- Proposed value: `{"arm_description": null, "arm_id": 5, "arm_key": "control", "arm_label": "Control group", "arm_role": "unclear", "assignment_structure": "parallel_group", "author_arm_label": "Control group", "sample_json": {}, "study_id": 2}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `deee9081583faa4e8cfa599878974037f2fe6765f487774f30cd6fc5de47eee8`

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 2}`
- Stage 11 candidate: `302`
- Proposed value: `{"arm_extraction_status": "partially_extracted", "study_id": 2}`
- Evidence basis: notes: Three-group design is explicit; the rapid-review seed does not specify the control sufficiently to assign a more specific role or safe contrast.
- Row snapshot: `a8943c2ef7604a303f11cb6f080d223c07b633a112b216fff69100c9decff11a`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 2}`
- Stage 11 candidate: `320`
- Proposed value: `{"contrast_extraction_status": "not_yet_extracted", "study_id": 2}`
- Evidence basis: notes: Three-group design is explicit; the rapid-review seed does not specify the control sufficiently to assign a more specific role or safe contrast.
- Row snapshot: `a8943c2ef7604a303f11cb6f080d223c07b633a112b216fff69100c9decff11a`

## rt-2026-003 — Promoting Working Memory and Numeracy Skills in Kindergarteners: Optimal Intervention Designs for Children Across Skill Levels

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 3}`
- Stage 11 candidate: `295`
- Proposed value: `{"arm_extraction_status": "not_applicable", "study_id": 3}`
- Evidence basis: notes: Secondary analysis integrates three separate randomized studies with varying controls; one synthetic arm set would misrepresent the analysis.
- Row snapshot: `71dac8433c97f5b18a7e6740ece3fc96919e48ddb31fbd8749702735d24e222c`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 3}`
- Stage 11 candidate: `313`
- Proposed value: `{"contrast_extraction_status": "not_applicable", "study_id": 3}`
- Evidence basis: notes: Secondary analysis integrates three separate randomized studies with varying controls; one synthetic arm set would misrepresent the analysis.
- Row snapshot: `71dac8433c97f5b18a7e6740ece3fc96919e48ddb31fbd8749702735d24e222c`

## rt-2026-004 — relational-frame training

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 6, "component_id": 4}`
- Stage 11 candidate: `102`
- Proposed value: `{"arm_id": 6, "component_id": 4, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `8a0921a6d6639ad81253fc2aacc18827c7f646ad57e3ee49bb5c921bb7595186`

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 7, "component_id": 4}`
- Stage 11 candidate: `103`
- Proposed value: `{"arm_id": 7, "component_id": 4, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `2578c76324920a8e992ac3b9da92f7167e16d8116e1ffbebe0e87e9e7ad9f001`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 6, "contrast_id": 2}`
- Stage 11 candidate: `124`
- Proposed value: `{"arm_id": 6, "contrast_coefficient": 1, "contrast_id": 2, "contrast_side": "focal", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `cac30090849f5a98c0a9344bf44c14a3c36a08e44b7a281676fd203886e98a73`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 7, "contrast_id": 3}`
- Stage 11 candidate: `125`
- Proposed value: `{"arm_id": 7, "contrast_coefficient": 1, "contrast_id": 3, "contrast_side": "focal", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `b0a5c577c420e2ad554e995eec70d240731957f001969f2482a87640df5eb5db`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 8, "contrast_id": 2}`
- Stage 11 candidate: `126`
- Proposed value: `{"arm_id": 8, "contrast_coefficient": -1, "contrast_id": 2, "contrast_side": "comparator", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `8d041afe049f39cc4d0526bd25dacd783d0ca952845f249b3c55f78e4a9f086c`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 8, "contrast_id": 3}`
- Stage 11 candidate: `127`
- Proposed value: `{"arm_id": 8, "contrast_coefficient": -1, "contrast_id": 3, "contrast_side": "comparator", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `d09ba023739faa337cf2b55fbf840e28e7c3d57ab58f7338314f981fafff2675`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 6}`
- Stage 11 candidate: `83`
- Proposed value: `{"arm_description": null, "arm_id": 6, "arm_key": "standard_relational_training", "arm_label": "Standard relational training", "arm_role": "intervention", "assignment_structure": "parallel_group", "author_arm_label": "standard relational training", "sample_json": {"randomized": 42}, "study_id": 4}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `169899fed0e3553ba95833464a6564332e079a3725b055e6e8915713f2db28d6`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 7}`
- Stage 11 candidate: `84`
- Proposed value: `{"arm_description": null, "arm_id": 7, "arm_key": "enhanced_multi_exemplar_training", "arm_label": "Enhanced multi-exemplar training", "arm_role": "intervention", "assignment_structure": "parallel_group", "author_arm_label": "enhanced multi-exemplar training", "sample_json": {"randomized": 38}, "study_id": 4}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `402101db1db471964133611fa10988bbbc53c2c8e337b89755568102d6dea62e`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 8}`
- Stage 11 candidate: `85`
- Proposed value: `{"arm_description": null, "arm_id": 8, "arm_key": "yoked_control", "arm_label": "Yoked control", "arm_role": "active_control", "assignment_structure": "parallel_group", "author_arm_label": "yoked control", "sample_json": {"randomized": 39}, "study_id": 4}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `11a1bfd16bb7db220f4ab77f28f7b44fd48ce1171e848e2f25cfd87dfdae4de8`

### `study_contrast`

- Surface mode: `ordinary`
- Key: `{"contrast_id": 2}`
- Stage 11 candidate: `110`
- Proposed value: `{"contrast_id": 2, "contrast_key": "standard_vs_yoked", "contrast_label": "Standard relational training vs yoked control", "contrast_type": "pairwise", "estimand_summary": null, "study_id": 4}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `99e02dea5c0e8ebb22632159e54533e14cef69bc6f4751c64f226c1da7003784`

### `study_contrast`

- Surface mode: `ordinary`
- Key: `{"contrast_id": 3}`
- Stage 11 candidate: `111`
- Proposed value: `{"contrast_id": 3, "contrast_key": "enhanced_vs_yoked", "contrast_label": "Enhanced multi-exemplar training vs yoked control", "contrast_type": "pairwise", "estimand_summary": null, "study_id": 4}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `e0df7a13a2671558b2da4e86752584aaec258fed0056c17b3011691f29fb2f06`

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 4}`
- Stage 11 candidate: `301`
- Proposed value: `{"arm_extraction_status": "partially_extracted", "study_id": 4}`
- Evidence basis: notes: Three randomized groups and per-group randomized counts are explicit. The same normalized relational-training component appears in two arms.
- Row snapshot: `f93ab39c275d5f4175d135c963a07bcb5f5146992d15a686169d6a6607f28cf2`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 4}`
- Stage 11 candidate: `319`
- Proposed value: `{"contrast_extraction_status": "partially_extracted", "study_id": 4}`
- Evidence basis: notes: Three randomized groups and per-group randomized counts are explicit. The same normalized relational-training component appears in two arms.
- Row snapshot: `f93ab39c275d5f4175d135c963a07bcb5f5146992d15a686169d6a6607f28cf2`

## rt-2026-005 — custom-developed cognitive games

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 9, "component_id": 5}`
- Stage 11 candidate: `104`
- Proposed value: `{"arm_id": 9, "component_id": 5, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `8a3669f0f55826aef668d7de9229adf75cea53b22a7f41b631310e06ce0805c8`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 10, "contrast_id": 4}`
- Stage 11 candidate: `114`
- Proposed value: `{"arm_id": 10, "contrast_coefficient": -1, "contrast_id": 4, "contrast_side": "comparator", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `edd63378c45a6813a8729d07c83c1a44f847c9fc7a23e893b31263bce24217fb`

### `contrast_arm_member`

- Surface mode: `ordinary`
- Key: `{"arm_id": 9, "contrast_id": 4}`
- Stage 11 candidate: `128`
- Proposed value: `{"arm_id": 9, "contrast_coefficient": 1, "contrast_id": 4, "contrast_side": "focal", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `da7e5bd329c6c7dab6b58ef5f0a29055754ed6133a2e1e7a4dd69944fe10f272`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 10}`
- Stage 11 candidate: `59`
- Proposed value: `{"arm_description": null, "arm_id": 10, "arm_key": "video_observation_active_control", "arm_label": "Perceptual-matched gameplay-video observation", "arm_role": "active_control", "assignment_structure": "parallel_group", "author_arm_label": "perceptual-matched gameplay-video observation", "sample_json": {}, "study_id": 5}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `57e375df938d1bd940de6684164fb7b5cf567646d79d1fc3da186476aec8d126`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 9}`
- Stage 11 candidate: `86`
- Proposed value: `{"arm_description": null, "arm_id": 9, "arm_key": "cognitive_game_training", "arm_label": "Custom-developed cognitive-game training", "arm_role": "intervention", "assignment_structure": "parallel_group", "author_arm_label": "custom-developed cognitive games", "sample_json": {}, "study_id": 5}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `904d9679592e826fac7232cd05ee2627c29e8c426787b3246c4e54b464ddf41b`

### `study_contrast`

- Surface mode: `ordinary`
- Key: `{"contrast_id": 4}`
- Stage 11 candidate: `112`
- Proposed value: `{"contrast_id": 4, "contrast_key": "training_vs_video_control", "contrast_label": "Cognitive-game training vs video-observation active control", "contrast_type": "pairwise", "estimand_summary": null, "study_id": 5}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `ad9dfb1de9099bd14bf87fcbad396f687f2fb86af6438460c03dd85b3adae92c`

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 5}`
- Stage 11 candidate: `293`
- Proposed value: `{"arm_extraction_status": "partially_extracted", "study_id": 5}`
- Evidence basis: notes: Randomized training-versus-active-control structure is explicit; no per-arm counts are inferred from total randomized N.
- Row snapshot: `a81361251c9157617f100373dba632ecfc54f6b2eecf436fe12594a824dd381a`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 5}`
- Stage 11 candidate: `311`
- Proposed value: `{"contrast_extraction_status": "partially_extracted", "study_id": 5}`
- Evidence basis: notes: Randomized training-versus-active-control structure is explicit; no per-arm counts are inferred from total randomized N.
- Row snapshot: `a81361251c9157617f100373dba632ecfc54f6b2eecf436fe12594a824dd381a`

## rt-2026-006 — Baduanjin

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 12, "component_id": 6}`
- Stage 11 candidate: `88`
- Proposed value: `{"arm_id": 12, "component_id": 6, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `4f3a733bf27b95714d657d41d64b048b020153734e100812a55d734885079c4a`

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 13, "component_id": 7}`
- Stage 11 candidate: `89`
- Proposed value: `{"arm_id": 13, "component_id": 7, "membership_role": "defining", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `934d98e8f6faf2af0cfbc726523a3a042230f20fb97487d2304b8c27cd4eee80`

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 14, "component_id": 6}`
- Stage 11 candidate: `90`
- Proposed value: `{"arm_id": 14, "component_id": 6, "membership_role": "shared", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `363fe58b62b6d28a11eafa61cfabcae7961b0ac682631cf40f368d3cdf67d2cc`

### `arm_component`

- Surface mode: `ordinary`
- Key: `{"arm_id": 14, "component_id": 7}`
- Stage 11 candidate: `91`
- Proposed value: `{"arm_id": 14, "component_id": 7, "membership_role": "shared", "rationale": null}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `5ee49ea484a775747ee6fa1d047b2b6386358a690dce8181fa532cb3c6a0fc88`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 11}`
- Stage 11 candidate: `60`
- Proposed value: `{"arm_description": null, "arm_id": 11, "arm_key": "control", "arm_label": "Control", "arm_role": "passive_control", "assignment_structure": "factorial_cell", "author_arm_label": "Control", "sample_json": {}, "study_id": 6}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `1f5ecb3a7be0d8c894cd6090301220875b28f2fe0420ff477f5342208ccac4ba`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 12}`
- Stage 11 candidate: `61`
- Proposed value: `{"arm_description": null, "arm_id": 12, "arm_key": "baduanjin_only", "arm_label": "Baduanjin only", "arm_role": "intervention", "assignment_structure": "factorial_cell", "author_arm_label": "Baduanjin-only", "sample_json": {}, "study_id": 6}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `62198cbaada2982398437110781ccd6a21c69252737921d505d54c125480488f`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 13}`
- Stage 11 candidate: `62`
- Proposed value: `{"arm_description": null, "arm_id": 13, "arm_key": "cognitive_training_only", "arm_label": "Cognitive training only", "arm_role": "intervention", "assignment_structure": "factorial_cell", "author_arm_label": "cognitive-training-only", "sample_json": {}, "study_id": 6}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `0c571f3af8bc64eaee1dc9f834d779efee5df125636e77a7bc458f86af0b2ad0`

### `study_arm`

- Surface mode: `ordinary`
- Key: `{"arm_id": 14}`
- Stage 11 candidate: `63`
- Proposed value: `{"arm_description": null, "arm_id": 14, "arm_key": "combined_baduanjin_cognitive", "arm_label": "Baduanjin + cognitive training", "arm_role": "intervention", "assignment_structure": "factorial_cell", "author_arm_label": "combined", "sample_json": {}, "study_id": 6}`
- Evidence basis: No separate evidence-basis text field; review the complete proposed row snapshot and linked source context.
- Row snapshot: `eaff2c11910f37ba1820f59b6c0bea6a0199b1e8f37ea29288dda49fbc188684`

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 6}`
- Stage 11 candidate: `298`
- Proposed value: `{"arm_extraction_status": "partially_extracted", "study_id": 6}`
- Evidence basis: notes: The 2x2 factorial cells are explicit, but the seed does not establish which factorial estimands should be privileged.
- Row snapshot: `4a5bbd85bcfb73f846edbd83bb52d1ddaf72628be25a9e386d5c1642ab71d78a`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 6}`
- Stage 11 candidate: `316`
- Proposed value: `{"contrast_extraction_status": "not_yet_extracted", "study_id": 6}`
- Evidence basis: notes: The 2x2 factorial cells are explicit, but the seed does not establish which factorial estimands should be privileged.
- Row snapshot: `4a5bbd85bcfb73f846edbd83bb52d1ddaf72628be25a9e386d5c1642ab71d78a`

## rt-2026-007 — Transcranial direct current stimulation combined with cognitive training for working memory in healthy adults: a systematic review and robust variance meta-analysis of trained and untrained outcomes

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 7}`
- Stage 11 candidate: `297`
- Proposed value: `{"arm_extraction_status": "not_applicable", "study_id": 7}`
- Evidence basis: notes: Systematic review/meta-analysis aggregates 23 randomized trials; source-level pooled descriptions are not one trial arm set.
- Row snapshot: `1d4e65ab96e034105229b1a4b4411125ed9bb0d541e151eb3625649b133f7744`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 7}`
- Stage 11 candidate: `315`
- Proposed value: `{"contrast_extraction_status": "not_applicable", "study_id": 7}`
- Evidence basis: notes: Systematic review/meta-analysis aggregates 23 randomized trials; source-level pooled descriptions are not one trial arm set.
- Row snapshot: `1d4e65ab96e034105229b1a4b4411125ed9bb0d541e151eb3625649b133f7744`

## rt-2026-008 — Psychometric Properties and Transfer Measures of Working Memory in Older Adults: A Scoping Review

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 8}`
- Stage 11 candidate: `291`
- Proposed value: `{"arm_extraction_status": "not_applicable", "study_id": 8}`
- Evidence basis: notes: Measurement-focused scoping review; no single experimental arm structure applies.
- Row snapshot: `b69dd072fb6f21aa0f6df027412e861d7ea3e4ea56d739640945c30c063b555a`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 8}`
- Stage 11 candidate: `309`
- Proposed value: `{"contrast_extraction_status": "not_applicable", "study_id": 8}`
- Evidence basis: notes: Measurement-focused scoping review; no single experimental arm structure applies.
- Row snapshot: `b69dd072fb6f21aa0f6df027412e861d7ea3e4ea56d739640945c30c063b555a`

## rt-2026-009 — An abstract relational map emerges in the human medial prefrontal cortex with consolidation

### `study_stage5_status` / arm

- Surface mode: `dimension`
- Key: `{"study_id": 9}`
- Stage 11 candidate: `292`
- Proposed value: `{"arm_extraction_status": "not_yet_extracted", "study_id": 9}`
- Evidence basis: notes: Mechanism study likely contains learning/scan conditions, but the rapid-review seed does not enumerate them sufficiently.
- Row snapshot: `438b4c3d33c3fa42075776d4ad4012557533937d34f142b3f6ffc26414019afa`

### `study_stage5_status` / contrast

- Surface mode: `dimension`
- Key: `{"study_id": 9}`
- Stage 11 candidate: `310`
- Proposed value: `{"contrast_extraction_status": "not_yet_extracted", "study_id": 9}`
- Evidence basis: notes: Mechanism study likely contains learning/scan conditions, but the rapid-review seed does not enumerate them sufficiently.
- Row snapshot: `438b4c3d33c3fa42075776d4ad4012557533937d34f142b3f6ffc26414019afa`
