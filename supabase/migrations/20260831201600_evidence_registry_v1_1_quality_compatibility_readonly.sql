-- Stage 7 governance hardening: the historical source-linked quality table is
-- compatibility/audit metadata only. The typed Stage 7 tables are the v1.1
-- scientific write surface. Service-side historical preservation is unchanged.

revoke insert, update, delete on table public.quality_assessment from authenticated;

comment on table public.quality_assessment is
'Historical compatibility/audit surface. Stage 7 v1.1 scientific authority uses study_quality_assessment and result_risk_of_bias_assessment. Authenticated Workbench users have no write privilege here; GRADE/body certainty is deferred to Stage 8.';
