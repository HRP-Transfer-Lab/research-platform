-- Hosted migration-history marker.
-- The remote database originally received a runtime fix here for JSON target-array
-- casts in private.import_evidence_record(jsonb). The corrected function definition
-- is folded into the preceding replayable migration in Git so a fresh database never
-- passes through the transient faulty definition.

-- No-op on fresh replay by design.
select 1;
