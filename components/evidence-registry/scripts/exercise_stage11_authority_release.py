#!/usr/bin/env python3
"""Exercise Stage 11 correction durability and deterministic release-build authority locally.

The exercise is deliberately non-publishing:
- provenance/adjudication tests run inside a rolled-back transaction;
- release approval/publication runs inside a rolled-back transaction;
- the temporary validated build is cancelled/deleted at the end.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import uuid
from pathlib import Path

DEFAULT_CONTAINER = "supabase_db_research-platform"
REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_REVIEWER = "11111111-1111-1111-1111-111111111111"


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=check, capture_output=capture)


def psql(container: str, sql: str, *, check: bool = True) -> str:
    cmd = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres", "-A", "-t", "-F", "|"]
    result = run(cmd, input_text=sql, capture=True, check=check)
    return result.stdout.strip()


def sql_text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def dollar_json(value: object) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if "$stage11$" in text:
        raise ValueError("unexpected dollar-quote marker in JSON")
    return "$stage11$" + text + "$stage11$::jsonb"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def exercise_provenance(container: str) -> None:
    sql = f"""
begin;
do $$
declare
  run1 bigint;
  run2 bigint;
  cand1 bigint;
  cand2 bigint;
  adj1 bigint;
  adj2 bigint;
  auth_value jsonb;
  auth_count integer;
begin
  insert into public.scientific_processing_run(
    run_kind,actor_kind,run_status,completed_at,provider,tool_name,tool_version,model_name,model_version,
    prompt_version,extraction_schema_version,taxonomy_version,code_commit_sha,parameters_json,notes
  ) values (
    'pre_extraction','agent','completed',now(),'stage11-local-test','synthetic-extractor','1',
    'synthetic-model','1','prompt-v1','stage11-test-schema','iqm-route-v0.2','0000000','{{}}'::jsonb,
    'Transactional Stage 11 correction-durability test; rolled back.'
  ) returning processing_run_id into run1;

  insert into public.scientific_field_candidate(
    processing_run_id,subject_kind,subject_key,field_path,candidate_value_json,source_basis,confidence
  ) values (
    run1,'source_version','{{"source_version_id":"sv-rt-2026-015-v1"}}'::jsonb,'stage11.test.field',
    '{{"value":"agent-a"}}'::jsonb,'Synthetic local Stage 11 test candidate A',0.80
  ) returning field_candidate_id into cand1;

  adj1 := private.apply_scientific_adjudication_core(
    cand1,'{TEST_REVIEWER}'::uuid,'correct','{{"value":"human-reviewed"}}'::jsonb,
    'Reviewer corrects the synthetic candidate.'
  );

  select authoritative_value_json into auth_value
  from public.scientific_field_authority
  where subject_kind='source_version'
    and subject_key='{{"source_version_id":"sv-rt-2026-015-v1"}}'::jsonb
    and field_path='stage11.test.field' and active=true;

  if auth_value is distinct from '{{"value":"human-reviewed"}}'::jsonb then
    raise exception 'Human correction did not establish authority: %', auth_value;
  end if;

  insert into public.scientific_processing_run(
    run_kind,actor_kind,run_status,completed_at,provider,tool_name,tool_version,model_name,model_version,
    prompt_version,extraction_schema_version,taxonomy_version,code_commit_sha,parameters_json,notes
  ) values (
    're_extraction','agent','completed',now(),'stage11-local-test','synthetic-extractor','2',
    'synthetic-model','2','prompt-v2','stage11-test-schema','iqm-route-v0.2','0000001','{{}}'::jsonb,
    'Transactional Stage 11 reprocessing test; rolled back.'
  ) returning processing_run_id into run2;

  insert into public.scientific_field_candidate(
    processing_run_id,subject_kind,subject_key,field_path,candidate_value_json,source_basis,confidence,supersedes_candidate_id
  ) values (
    run2,'source_version','{{"source_version_id":"sv-rt-2026-015-v1"}}'::jsonb,'stage11.test.field',
    '{{"value":"agent-b"}}'::jsonb,'Synthetic local Stage 11 later candidate B',0.95,cand1
  ) returning field_candidate_id into cand2;

  select count(*),max(authoritative_value_json) into auth_count,auth_value
  from public.scientific_field_authority
  where subject_kind='source_version'
    and subject_key='{{"source_version_id":"sv-rt-2026-015-v1"}}'::jsonb
    and field_path='stage11.test.field' and active=true;

  if auth_count<>1 or auth_value is distinct from '{{"value":"human-reviewed"}}'::jsonb then
    raise exception 'Later agent candidate overwrote active human authority';
  end if;

  if (select candidate_status from public.scientific_field_candidate where field_candidate_id=cand2) <> 'proposed' then
    raise exception 'Later machine candidate should remain proposed';
  end if;

  adj2 := private.apply_scientific_adjudication_core(
    cand2,'{TEST_REVIEWER}'::uuid,'reject',null,'Later machine candidate rejected; human authority remains.'
  );

  select authoritative_value_json into auth_value
  from public.scientific_field_authority
  where subject_kind='source_version'
    and subject_key='{{"source_version_id":"sv-rt-2026-015-v1"}}'::jsonb
    and field_path='stage11.test.field' and active=true;

  if auth_value is distinct from '{{"value":"human-reviewed"}}'::jsonb then
    raise exception 'Rejected reprocessing candidate altered human authority';
  end if;

  raise notice 'STAGE11_PROVENANCE_TRANSACTION_PASS candidate1=%, adjudication1=%, candidate2=%, adjudication2=%',cand1,adj1,cand2,adj2;
end $$;
rollback;
"""
    psql(container, sql)


def fetch_build_payload(container: str, build_id: str) -> tuple[dict, dict, bytes, bytes]:
    meta_raw = psql(container, f"""
select jsonb_build_object(
  'release_build_id',release_build_id,
  'target_release_id',target_release_id,
  'schema_version',schema_version,
  'taxonomy_version',taxonomy_version,
  'gateway_contract_version',gateway_contract_version,
  'prepared_revision',prepared_revision
)::text
from public.evidence_release_build where release_build_id={sql_text(build_id)};
""")
    if not meta_raw:
        raise RuntimeError("temporary release build missing")
    meta = json.loads(meta_raw)

    members_raw = psql(container, f"""
select coalesce(jsonb_agg(x order by (x->>'release_position')::int),'[]'::jsonb)::text
from (
  select jsonb_build_object(
    'release_record_id',rb.release_record_id,
    'release_position',rb.release_position,
    'source_version',jsonb_build_object(
      'source_version_id',sv.source_version_id,
      'canonical_source_id',sv.canonical_source_id,
      'version_number',sv.version_number,
      'version_status',sv.version_status,
      'title',sv.title,
      'authors',sv.authors,
      'publication_year',sv.publication_year,
      'publication_date',sv.publication_date,
      'venue',sv.venue,
      'source_kind',sv.source_kind,
      'peer_review_status',sv.peer_review_status,
      'doi',sv.doi,
      'pmid',sv.pmid,
      'arxiv_id',sv.arxiv_id,
      'source_url',sv.source_url,
      'review_status',sv.review_status,
      'method_extraction_status',sv.method_extraction_status,
      'route_rationale',sv.route_rationale,
      'raw_record',sv.raw_record,
      'supersedes_source_version_id',sv.supersedes_source_version_id
    )
  ) as x
  from public.release_build_source_version rb
  join public.source_version sv on sv.source_version_id=rb.source_version_id
  where rb.release_build_id={sql_text(build_id)}
) q;
""")
    members = json.loads(members_raw)

    authority_raw = psql(container, """
select coalesce(jsonb_agg(x order by x::text),'[]'::jsonb)::text
from (
  select jsonb_build_object(
    'subject_kind',subject_kind,
    'subject_key',subject_key,
    'field_path',field_path,
    'authoritative_value_json',authoritative_value_json,
    'authority_kind',authority_kind,
    'approved_by',approved_by,
    'approved_at',approved_at
  ) as x
  from public.scientific_field_authority
  where active=true
) q;
""")
    authorities = json.loads(authority_raw)

    source_manifest: list[dict] = []
    state_sources: list[dict] = []
    for member in members:
        source_obj = member["source_version"]
        source_hash = sha256(canonical_bytes(source_obj))
        source_manifest.append({
            "source_version_id": source_obj["source_version_id"],
            "release_record_id": member["release_record_id"],
            "release_position": member["release_position"],
            "source_state_sha256": source_hash,
        })
        state_sources.append(source_obj)

    scientific_state = {
        "schema_version": meta["schema_version"],
        "taxonomy_version": meta["taxonomy_version"],
        "gateway_contract_version": meta["gateway_contract_version"],
        "scientific_state_revision": meta["prepared_revision"],
        "source_versions": state_sources,
        "active_field_authorities": authorities,
    }
    state_bytes = canonical_bytes(scientific_state)
    state_hash = sha256(state_bytes)

    manifest = {
        "release_build_id": meta["release_build_id"],
        "target_release_id": meta["target_release_id"],
        "schema_version": meta["schema_version"],
        "taxonomy_version": meta["taxonomy_version"],
        "gateway_contract_version": meta["gateway_contract_version"],
        "scientific_state_revision": meta["prepared_revision"],
        "scientific_state_sha256": state_hash,
        "sources": source_manifest,
    }
    manifest_bytes = canonical_bytes(manifest)
    manifest_hash = sha256(manifest_bytes)
    manifest["export_manifest_sha256"] = manifest_hash
    final_manifest_bytes = canonical_bytes(manifest)

    # Hash refers to manifest content before self-hash insertion; this avoids recursive hashing.
    return scientific_state, manifest, state_bytes, final_manifest_bytes


def expect_direct_release_write_blocked(container: str, role: str, release_id: str) -> None:
    sql = f"""
begin;
set local role {role};
insert into public.evidence_release(
 release_id,released_on,schema_version,taxonomy_version,source_review_document,status
) values ({sql_text(release_id)},current_date,'x','x','stage11-direct-write-test','draft');
rollback;
"""
    cmd = ["docker", "exec", "-i", container, "psql", "-v", "ON_ERROR_STOP=1", "-U", "postgres", "-d", "postgres"]
    result = run(cmd, input_text=sql, capture=True, check=False)
    if result.returncode == 0:
        raise RuntimeError(f"direct evidence_release write unexpectedly succeeded as {role}")


def exercise_release(container: str) -> None:
    token = uuid.uuid4().hex[:12]
    build_id = f"stage11-local-{token}"
    target_release = f"stage11-local-release-{token}"
    git_sha = run(["git", "rev-parse", "HEAD"], capture=True, check=True).stdout.strip()

    psql(container, f"""
select private.stage11_create_release_build_core(
 {sql_text(build_id)},{sql_text(target_release)},'registry-v1.1','iqm-route-v0.2','csi-evidence-v1',
 'docs/STAGE_11_PROVENANCE_RELEASE_AUTHORITY_IMPLEMENTATION.md','local deterministic Stage 11 exercise',
 '{TEST_REVIEWER}'::uuid,'Temporary local verification build; never published.'
);
select private.stage11_prepare_release_build_core({sql_text(build_id)});
""")

    state1, manifest1, state_bytes1, manifest_bytes1 = fetch_build_payload(container, build_id)
    state2, manifest2, state_bytes2, manifest_bytes2 = fetch_build_payload(container, build_id)
    if state_bytes1 != state_bytes2 or manifest_bytes1 != manifest_bytes2:
        raise RuntimeError("unchanged prepared build did not export byte-identically twice")

    state_hash = sha256(state_bytes1)
    # Manifest SHA is over canonical manifest without the self-hash field.
    manifest_without_self = dict(manifest1)
    manifest_hash_recorded = manifest_without_self.pop("export_manifest_sha256")
    manifest_hash = sha256(canonical_bytes(manifest_without_self))
    if manifest_hash != manifest_hash_recorded:
        raise RuntimeError("manifest self-hash convention is inconsistent")

    validation_report = {
        "stage": 11,
        "local_exercise": True,
        "deterministic_repeat": True,
        "source_count": len(manifest1["sources"]),
        "scientific_state_revision": manifest1["scientific_state_revision"],
    }
    psql(container, f"""
select private.stage11_record_release_validation_core(
 {sql_text(build_id)},{sql_text(state_hash)},{sql_text(manifest_hash)},
 {dollar_json(manifest_without_self)},{dollar_json(validation_report)},{sql_text(git_sha)},null
);
""")

    validated = psql(container, f"""
select build_status||'|'||scientific_state_sha256||'|'||export_manifest_sha256||'|'||
       (select count(*)::text from public.release_build_source_version rb where rb.release_build_id=b.release_build_id)
from public.evidence_release_build b where release_build_id={sql_text(build_id)};
""")
    expected_prefix = f"validated|{state_hash}|{manifest_hash}|"
    if not validated.startswith(expected_prefix):
        raise RuntimeError(f"validated build state mismatch: {validated}")
    member_count = int(validated.rsplit("|", 1)[1])
    if member_count != 18:
        raise RuntimeError(f"expected 18 pinned source versions; got {member_count}")

    expect_direct_release_write_blocked(container, "authenticated", f"blocked-auth-{token}")
    expect_direct_release_write_blocked(container, "service_role", f"blocked-service-{token}")

    # Drift invalidation is tested inside a transaction and rolled back.
    psql(container, f"""
begin;
do $$
declare drift_blocked boolean := false;
begin
  update public.canonical_source
  set preferred_title=preferred_title
  where canonical_source_id=(select min(canonical_source_id) from public.canonical_source);
  begin
    perform private.assert_stage11_build_current({sql_text(build_id)});
  exception when others then
    if position('Scientific state drift' in sqlerrm)>0 then drift_blocked := true; else raise; end if;
  end;
  if not drift_blocked then raise exception 'Expected scientific-state drift guard to fire'; end if;
end $$;
rollback;
""")

    # Approval + publication authority path is exercised transactionally and rolled back.
    psql(container, f"""
begin;
select private.stage11_approve_release_build_core({sql_text(build_id)},'{TEST_REVIEWER}'::uuid);
select private.stage11_publish_release_build_core({sql_text(build_id)},'{TEST_REVIEWER}'::uuid);
do $$
declare n integer;
begin
  if not exists(select 1 from public.evidence_release where release_id={sql_text(target_release)} and status='approved_release') then
    raise exception 'Governed transactional publication did not create approved release';
  end if;
  select count(*) into n from public.release_source_version where release_id={sql_text(target_release)};
  if n<>18 then raise exception 'Governed transactional publication expected 18 memberships, got %',n; end if;
end $$;
rollback;
""")

    # The transactional publication must not persist.
    if psql(container, f"select count(*) from public.evidence_release where release_id={sql_text(target_release)};") != "0":
        raise RuntimeError("transactional Stage 11 test publication persisted unexpectedly")

    # Clean the temporary validated build using the controlled GUC; cascade cleanup sees the same session GUC.
    psql(container, f"""
select set_config('hrp.stage11_controlled_write','on',false);
update public.evidence_release_build set build_status='cancelled',updated_at=now() where release_build_id={sql_text(build_id)};
delete from public.evidence_release_build where release_build_id={sql_text(build_id)};
""")
    if psql(container, f"select count(*) from public.evidence_release_build where release_build_id={sql_text(build_id)};") != "0":
        raise RuntimeError("temporary Stage 11 release build cleanup failed")

    print(
        "STAGE 11 RELEASE EXERCISE PASS: "
        f"sources={member_count}; state_sha256={state_hash}; manifest_sha256={manifest_hash}; "
        "repeat_export=byte_identical; drift_guard=PASS; transactional_publish=PASS; direct_auth/service_write=BLOCKED"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--container", default=DEFAULT_CONTAINER)
    args = ap.parse_args()
    running = run(["docker", "inspect", "-f", "{{.State.Running}}", args.container], capture=True).stdout.strip()
    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running")

    exercise_provenance(args.container)
    print("STAGE 11 PROVENANCE EXERCISE PASS: human correction survives later agent candidate and rejection")
    exercise_release(args.container)
    print("STAGE 11 AUTHORITY/RELEASE EXERCISE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
