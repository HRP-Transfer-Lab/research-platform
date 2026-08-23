create table public.evidence_maturity_level_definition (
  scale_version text not null,
  maturity_level smallint not null check (maturity_level between 0 and 7),
  code text not null,
  label text not null,
  short_label text not null,
  description text not null,
  cumulative_requirement text not null,
  color_token text not null,
  primary key (scale_version, maturity_level),
  unique (scale_version, code)
);

comment on table public.evidence_maturity_level_definition is 'HRP Evidence Maturity Level definitions. Maturity is a cumulative stage of evidence development and must not be treated as a substitute for risk-of-bias or GRADE certainty.';

insert into public.evidence_maturity_level_definition (
  scale_version, maturity_level, code, label, short_label, description, cumulative_requirement, color_token
) values
('hrp-eml-v1',0,'EML0','Rationale only','Rationale','A theoretical, mechanistic or logic-model rationale exists, but the target proposition has not been directly supported by empirical evidence.','No direct empirical support for the target proposition.','neutral'),
('hrp-eml-v1',1,'EML1','Mechanism / paradigm support','Mechanism','Relevant mechanisms, constructs, measurement findings or adjacent paradigms have empirical support, but the target intervention-outcome proposition has not yet received a credible direct demonstration.','Empirical mechanism, construct, measurement or adjacent-paradigm support.','blue'),
('hrp-eml-v1',2,'EML2','Initial direct demonstration','Direct demo','At least one credible direct study demonstrates the target intervention, mapping or activity-system effect under defined conditions.','At least one credible direct empirical test of the target proposition.','indigo'),
('hrp-eml-v1',3,'EML3','Replicated efficacy','Replicated','The direct effect has been reproduced across at least two rigorous studies with a consistent direction, preferably including independent replication.','EML2 plus convergent direct replication across at least two rigorous studies; independence is preferred and must be recorded.','teal'),
('hrp-eml-v1',4,'EML4','Convergent body','Synthesis','A systematic synthesis or equivalent multi-study body supports the proposition with no unresolved pattern that makes the overall direction misleading.','EML3 plus reviewed multi-study synthesis; body-level quality/certainty remains separately appraised.','emerald'),
('hrp-eml-v1',5,'EML5','Transfer & durability','Transfer','A replicated/convergent body also demonstrates portability beyond the practised format and/or durability after delay for the target claim.','EML4 plus credible cumulative transfer/delayed evidence. A single far-transfer study cannot by itself satisfy EML5.','green'),
('hrp-eml-v1',6,'EML6','Real-world effectiveness','Effectiveness','The intervention or system has demonstrated useful outcomes in authentic or routine settings with appropriate fidelity and practical functional outcomes.','EML5 plus effectiveness evidence in real-world/routine conditions relevant to the claim.','lime'),
('hrp-eml-v1',7,'EML7','Generalised / scale-ready','Scale-ready','Evidence supports generalisation or scaled use across relevant settings/populations, with implementation, boundary conditions, fidelity and important harms/cost considerations sufficiently characterised for scaled decision-making.','EML6 plus multi-context generalisation and implementation/scale evidence.','gold');

create table public.evidence_maturity_assessment (
  maturity_assessment_id bigserial primary key,
  source_id text references public.evidence_source(source_id) on delete cascade,
  synthesis_id text references public.evidence_synthesis(synthesis_id) on delete cascade,
  claim_id text references public.approved_claim(claim_id) on delete cascade,
  scale_version text not null default 'hrp-eml-v1',
  maturity_level smallint not null,
  scope text not null check (scope in ('record_contribution','body_of_evidence')),
  status text not null check (status in ('provisional_seed','reviewed','approved')),
  basis text not null,
  assessed_on date not null default current_date,
  assessor text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint evidence_maturity_exactly_one_subject check (num_nonnulls(source_id, synthesis_id, claim_id) = 1),
  constraint evidence_maturity_level_fk foreign key (scale_version, maturity_level)
    references public.evidence_maturity_level_definition(scale_version, maturity_level)
);

create unique index evidence_maturity_source_unique
  on public.evidence_maturity_assessment(source_id, scale_version)
  where source_id is not null;
create unique index evidence_maturity_synthesis_unique
  on public.evidence_maturity_assessment(synthesis_id, scale_version)
  where synthesis_id is not null;
create unique index evidence_maturity_claim_unique
  on public.evidence_maturity_assessment(claim_id, scale_version)
  where claim_id is not null;
create index evidence_maturity_level_idx on public.evidence_maturity_assessment(scale_version, maturity_level);
create index evidence_maturity_source_idx on public.evidence_maturity_assessment(source_id) where source_id is not null;
create index evidence_maturity_synthesis_idx on public.evidence_maturity_assessment(synthesis_id) where synthesis_id is not null;
create index evidence_maturity_claim_idx on public.evidence_maturity_assessment(claim_id) where claim_id is not null;

comment on table public.evidence_maturity_assessment is 'Ordinal evidence-maturity assessment. Source ratings describe a record contribution; synthesis/claim ratings may describe a body of evidence. Quality/certainty remains separate in quality_assessment/GRADE.';

insert into public.evidence_maturity_assessment (
  source_id, scale_version, maturity_level, scope, status, basis, assessor
) values
('rt-2026-001','hrp-eml-v1',2,'record_contribution','provisional_seed','Direct randomized training study with separate-measure transfer evidence; currently a single reviewed direct study in this Registry release.','seed-mapping-2026-08-23'),
('rt-2026-002','hrp-eml-v1',2,'record_contribution','provisional_seed','Direct randomized longitudinal training study with separate and delayed outcomes; source-level contribution remains an initial direct demonstration until replicated body review is completed.','seed-mapping-2026-08-23'),
('rt-2026-003','hrp-eml-v1',2,'record_contribution','provisional_seed','Direct intervention evidence drawn from randomized studies; this Registry record is treated as a direct demonstration contribution rather than an approved body-level synthesis.','seed-mapping-2026-08-23'),
('rt-2026-004','hrp-eml-v1',2,'record_contribution','provisional_seed','Direct randomized relational-training demonstration with changed-format evidence; independent replication/body synthesis not yet approved in the Registry.','seed-mapping-2026-08-23'),
('rt-2026-005','hrp-eml-v1',2,'record_contribution','provisional_seed','Direct randomized training demonstration across younger and older adults with follow-up; body-level replication/synthesis not yet approved here.','seed-mapping-2026-08-23'),
('rt-2026-006','hrp-eml-v1',2,'record_contribution','provisional_seed','Direct factorial intervention trial combining condition and training loci; treated as an initial direct demonstration contribution.','seed-mapping-2026-08-23'),
('rt-2026-007','hrp-eml-v1',4,'record_contribution','provisional_seed','Systematic review/meta-analysis synthesising multiple randomized studies. This is a synthesis-stage contribution, but no HRP body-level claim or GRADE certainty assessment has yet been approved.','seed-mapping-2026-08-23'),
('rt-2026-008','hrp-eml-v1',1,'record_contribution','provisional_seed','Scoping review of measurement/transfer properties informs measurement architecture rather than directly demonstrating an intervention-outcome claim.','seed-mapping-2026-08-23'),
('rt-2026-009','hrp-eml-v1',1,'record_contribution','provisional_seed','Mechanistic relational-structure study informs the plausibility/design of reasoning interventions but is not a direct intervention-efficacy demonstration.','seed-mapping-2026-08-23'),
('rt-2026-010','hrp-eml-v1',1,'record_contribution','provisional_seed','Mechanism/training-design evidence on perceptual generalisation; not a direct demonstration of the CSI intervention claim.','seed-mapping-2026-08-23'),
('rt-2026-011','hrp-eml-v1',1,'record_contribution','provisional_seed','Mechanistic error-driven learning/metamemory evidence informs controller design but does not directly demonstrate the target intervention outcome.','seed-mapping-2026-08-23'),
('rt-2026-012','hrp-eml-v1',1,'record_contribution','provisional_seed','Acute-stress mechanism evidence informs Regulate hypotheses but is not direct evidence that a CSI regulation intervention improves the target outcome.','seed-mapping-2026-08-23'),
('rt-2026-013','hrp-eml-v1',1,'record_contribution','provisional_seed','Controlled negative metacognitive-prompt evidence informs strategy design and boundaries but is not a direct demonstration of a CSI intervention effect.','seed-mapping-2026-08-23'),
('rt-2026-014','hrp-eml-v1',2,'record_contribution','provisional_seed','Large randomized field experiment directly tests AI support/progression effects in an authentic educational activity system.','seed-mapping-2026-08-23'),
('rt-2026-015','hrp-eml-v1',2,'record_contribution','provisional_seed','Direct quasi-experimental classroom demonstration of bounded AI plus reflection with independent no-AI outcomes; replication/body synthesis not yet approved.','seed-mapping-2026-08-23'),
('rt-2026-016','hrp-eml-v1',2,'record_contribution','provisional_seed','Preregistered behavioral experiment directly demonstrates human-AI offloading/speedup effects under defined task conditions.','seed-mapping-2026-08-23'),
('rt-2026-017','hrp-eml-v1',2,'record_contribution','provisional_seed','Direct experiment on AI support stage and ownership in writing; source-level direct demonstration only.','seed-mapping-2026-08-23'),
('rt-2026-018','hrp-eml-v1',1,'record_contribution','provisional_seed','Observational longitudinal taxonomy of autonomous/dependent offloading informs mechanism/activity-system hypotheses but is not a direct intervention test.','seed-mapping-2026-08-23');

alter table public.evidence_maturity_level_definition enable row level security;
alter table public.evidence_maturity_assessment enable row level security;

revoke all on public.evidence_maturity_level_definition from anon;
revoke all on public.evidence_maturity_assessment from anon;
grant select on public.evidence_maturity_level_definition to authenticated, service_role;
grant select, insert, update, delete on public.evidence_maturity_assessment to authenticated, service_role;
grant usage, select on sequence public.evidence_maturity_assessment_maturity_assessment_id_seq to authenticated, service_role;

create policy evidence_maturity_definition_workbench_read
on public.evidence_maturity_level_definition for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy evidence_maturity_assessment_workbench_read
on public.evidence_maturity_assessment for select to authenticated
using ((select private.has_workbench_role(array['viewer','editor','owner']::text[])));
create policy evidence_maturity_assessment_workbench_insert
on public.evidence_maturity_assessment for insert to authenticated
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy evidence_maturity_assessment_workbench_update
on public.evidence_maturity_assessment for update to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])))
with check ((select private.has_workbench_role(array['editor','owner']::text[])));
create policy evidence_maturity_assessment_workbench_delete
on public.evidence_maturity_assessment for delete to authenticated
using ((select private.has_workbench_role(array['editor','owner']::text[])));

create trigger audit_evidence_maturity_assessment
after insert or update or delete on public.evidence_maturity_assessment
for each row execute function private.audit_workbench_change();

alter table public.csi_gateway_evidence_card
  add column maturity_scale_version text,
  add column maturity_level smallint,
  add column maturity_label text,
  add column maturity_short_label text,
  add column maturity_scope text,
  add column maturity_status text,
  add column maturity_basis text,
  add column maturity_color_token text;

alter table public.csi_gateway_claim
  add column maturity_scale_version text,
  add column maturity_level smallint,
  add column maturity_label text,
  add column maturity_short_label text,
  add column maturity_scope text,
  add column maturity_status text,
  add column maturity_basis text,
  add column maturity_color_token text;

update public.csi_gateway_evidence_card card
set maturity_scale_version = ema.scale_version,
    maturity_level = ema.maturity_level,
    maturity_label = d.label,
    maturity_short_label = d.short_label,
    maturity_scope = ema.scope,
    maturity_status = ema.status,
    maturity_basis = ema.basis,
    maturity_color_token = d.color_token
from public.evidence_maturity_assessment ema
join public.evidence_maturity_level_definition d
  on d.scale_version = ema.scale_version and d.maturity_level = ema.maturity_level
where ema.source_id = card.card_id
  and ema.scale_version = 'hrp-eml-v1';

create index csi_gateway_evidence_maturity_idx
  on public.csi_gateway_evidence_card(maturity_scale_version, maturity_level);

create or replace view public.v_csi_gateway_evidence_v1 with (security_invoker=true) as
select card_id, evidence_release_id, contract_version, evidence_class,
       primary_classification, secondary_component, title, authors,
       publication_year, publication_date, venue, source_kind, peer_review_status,
       doi, pmid, arxiv_id, source_url, study_design, study_setting,
       population_summary, population_tags, route_classes, topic_tags,
       functional_domains, evidence_rungs, transfer_axes, product_ids,
       component_summaries, outcome_summaries, product_relevance, route_rationale,
       claim_level, approved_claim_ids, required_caveats, published_at,
       maturity_scale_version, maturity_level, maturity_label, maturity_short_label,
       maturity_scope, maturity_status, maturity_basis, maturity_color_token
from public.csi_gateway_evidence_card where status='published';

create or replace view public.v_csi_gateway_claim_v1 with (security_invoker=true) as
select claim_id, evidence_release_id, contract_version, product, route_scope,
       population_scope, claim_text, required_caveat, certainty_judgement,
       claim_version, source_synthesis_id, published_at,
       maturity_scale_version, maturity_level, maturity_label, maturity_short_label,
       maturity_scope, maturity_status, maturity_basis, maturity_color_token
from public.csi_gateway_claim where status='published';

update public.csi_gateway_contract
set query_contract = jsonb_set(
      jsonb_set(query_contract, '{filters,maturity_level}', '"eq|gte|lte"'::jsonb, true),
      '{maturity_scale}',
      jsonb_build_object(
        'scale_version','hrp-eml-v1',
        'meaning','cumulative evidence maturity; not risk-of-bias or GRADE certainty',
        'levels', jsonb_build_array('EML0','EML1','EML2','EML3','EML4','EML5','EML6','EML7')
      ),
      true
    )
where contract_version='csi-evidence-v1';
