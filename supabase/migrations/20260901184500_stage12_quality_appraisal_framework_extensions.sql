-- HRP Transfer Evidence Registry v1.1
-- Stage 12 quality/RoB appraisal framework extensions.
--
-- Additive framework vocabulary only. No study/result judgement is created.
-- Historical release 2026-08-23 and csi-evidence-v1 remain unchanged.

insert into public.assessment_framework_definition (
  framework_key,
  label,
  framework_family,
  subject_kind,
  version_label,
  publisher_or_owner,
  description,
  active
) values
  (
    'robins_e',
    'ROBINS-E',
    'risk_of_bias',
    'result_risk_of_bias',
    '2024-03-24',
    'Risk of Bias tools / University of Bristol collaborators',
    'Risk-of-bias framework for a specific non-randomized exposure result. Registered for exposure studies; do not substitute ROBINS-I for exposure questions.',
    true
  ),
  (
    'prisma_scr',
    'PRISMA-ScR',
    'reporting',
    'study_reporting_completeness',
    '2018',
    'PRISMA Group',
    'Reporting guideline for scoping reviews. Reporting completeness is not methodological quality or risk of bias.',
    true
  )
on conflict (framework_key) do update set
  label=excluded.label,
  framework_family=excluded.framework_family,
  subject_kind=excluded.subject_kind,
  version_label=excluded.version_label,
  publisher_or_owner=excluded.publisher_or_owner,
  description=excluded.description,
  active=excluded.active;

-- Version-lock the external framework vocabulary used by the v1.1 appraisal protocol.
-- The assessment row itself still stores framework_version explicitly.
update public.assessment_framework_definition
set version_label='2019-08-22'
where framework_key='rob2';

update public.assessment_framework_definition
set version_label='2016'
where framework_key='robins_i';

update public.assessment_framework_definition
set version_label='2017'
where framework_key='amstar2';

update public.assessment_framework_definition
set version_label='2025'
where framework_key='consort';

update public.assessment_framework_definition
set version_label='2020'
where framework_key='prisma';

update public.assessment_framework_definition
set version_label='2018'
where framework_key='cosmin';

comment on table public.assessment_framework_definition is
'Controlled appraisal framework vocabulary. Framework applicability and all scientific judgements remain human-review gated; version labels identify the appraisal baseline and do not auto-assign a framework to a study/result.';
