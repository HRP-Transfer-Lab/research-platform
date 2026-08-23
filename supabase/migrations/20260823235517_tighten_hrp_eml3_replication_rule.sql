update public.evidence_maturity_level_definition
set label = 'Replicated direct evidence',
    short_label = 'Replicated',
    description = 'The direct effect has been reproduced across at least two rigorous direct studies with a consistent direction, including at least one genuine replication designed to reproduce the effect.',
    cumulative_requirement = 'EML2 plus at least one genuine replication: preferably an independent-team replication, or a prospectively registered or multisite replication explicitly designed to reproduce the effect. Repeated exploratory demonstrations from the same development programme do not by themselves satisfy EML3.'
where scale_version = 'hrp-eml-v1' and maturity_level = 3;
