#!/usr/bin/env python3
"""Validate Evidence Registry v1.1 Stage 2 source identity/version invariants.

Local-only by default: queries the running local Supabase Postgres container via
`docker exec`. It does not link to or modify hosted Supabase projects.
"""

from __future__ import annotations

import argparse
import subprocess

DEFAULT_CONTAINER = "supabase_db_research-platform"
DEFAULT_RELEASE = "2026-08-23"
DEFAULT_EXPECTED = 18


def run(cmd: list[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=capture)


def psql(container: str, sql: str, *, tuples_only: bool = False) -> str:
    cmd = [
        "docker", "exec", "-i", container,
        "psql", "-v", "ON_ERROR_STOP=1",
        "-U", "postgres", "-d", "postgres",
    ]
    if tuples_only:
        cmd.extend(["-A", "-t", "-F", "|"])
    result = run(cmd, input_text=sql, capture=tuples_only)
    return result.stdout.strip() if tuples_only else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Registry v1.1 Stage 2 source identity/version invariants.")
    parser.add_argument("--container", default=DEFAULT_CONTAINER)
    parser.add_argument("--release", default=DEFAULT_RELEASE)
    parser.add_argument("--expected", type=int, default=DEFAULT_EXPECTED)
    args = parser.parse_args()

    try:
        running = run(
            ["docker", "inspect", "-f", "{{.State.Running}}", args.container],
            capture=True,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Local database container {args.container!r} is unavailable.") from exc

    if running != "true":
        raise SystemExit(f"Local database container {args.container!r} is not running.")

    q = lambda value: "'" + value.replace("'", "''") + "'"
    release = q(args.release)

    counts_sql = f"""
select
  (select count(*) from public.evidence_source where release_id={release}),
  (select count(*) from public.canonical_source),
  (select count(*) from public.source_version),
  (select count(*) from public.release_source_version where release_id={release}),
  (select count(*) from public.canonical_source_identity where identity_scheme='legacy_source_id'),
  (select count(*) from public.canonical_source_identity where identity_scheme='doi'),
  (select count(*) from public.canonical_source_identity where identity_scheme='pmid'),
  (select count(*) from public.canonical_source_identity where identity_scheme='arxiv'),
  (select count(*) from public.canonical_source_identity where identity_scheme='canonical_url');
"""
    counts = psql(args.container, counts_sql, tuples_only=True).split("|")
    if len(counts) != 9:
        raise SystemExit(f"STAGE 2 IDENTITY INVALID: unexpected count output {counts!r}")

    (
        evidence_sources,
        canonical_sources,
        source_versions,
        release_memberships,
        legacy_aliases,
        dois,
        pmids,
        arxiv_ids,
        urls,
    ) = map(int, counts)

    expected = args.expected
    errors: list[str] = []

    required_counts = {
        "evidence_sources": evidence_sources,
        "canonical_sources": canonical_sources,
        "source_versions": source_versions,
        "release_memberships": release_memberships,
        "legacy_source_aliases": legacy_aliases,
    }
    for name, value in required_counts.items():
        if value != expected:
            errors.append(f"{name}: expected {expected}, got {value}")

    integrity_sql = f"""
select
  (select count(*)
     from public.evidence_source es
    where es.release_id={release}
      and not exists (
        select 1 from public.canonical_source_identity csi
         where csi.identity_scheme='legacy_source_id'
           and csi.normalized_value=lower(es.source_id)
      )),

  (select count(*)
     from public.canonical_source cs
    where not exists (
      select 1 from public.source_version sv
       where sv.canonical_source_id=cs.canonical_source_id
    )),

  (select count(*)
     from public.canonical_source cs
     join public.source_version sv on sv.canonical_source_id=cs.canonical_source_id
    group by cs.canonical_source_id
   having count(*) <> 1),

  (select count(*)
     from public.source_version sv
    where sv.version_number <> 1
       or sv.source_version_id <> ('sv-' || replace(sv.canonical_source_id, 'cs-', '') || '-v1')),

  (select count(*)
     from public.release_source_version rsv
    where rsv.release_id={release}
      and rsv.release_record_id <> replace(replace(rsv.source_version_id, 'sv-', ''), '-v1', '')),

  (select count(*) from (
      select identity_scheme, normalized_value
      from public.canonical_source_identity
      group by identity_scheme, normalized_value
      having count(*) > 1
  ) d),

  (select count(*)
     from public.release_source_version rsv
     join public.source_version sv on sv.source_version_id=rsv.source_version_id
     join public.canonical_source_identity csi
       on csi.canonical_source_id=sv.canonical_source_id
      and csi.identity_scheme='legacy_source_id'
    where rsv.release_id={release}
      and csi.normalized_value <> lower(rsv.release_record_id));
"""
    raw_integrity = psql(args.container, integrity_sql, tuples_only=True).split("|")
    if len(raw_integrity) != 7:
        raise SystemExit(f"STAGE 2 IDENTITY INVALID: unexpected integrity output {raw_integrity!r}")

    labels = [
        "sources_without_canonical_identity",
        "canonical_sources_without_version",
        "canonical_sources_without_exactly_one_seed_version",
        "invalid_seed_version_identity",
        "invalid_release_record_mapping",
        "duplicate_external_identities",
        "release_membership_legacy_alias_mismatch",
    ]
    integrity = dict(zip(labels, map(int, raw_integrity)))
    errors.extend(f"{name}: {value} failures" for name, value in integrity.items() if value != 0)

    # Explicitly verify the two immutability guards without leaving any mutation.
    guard_sql = f"""
do $$
declare
  v_source_version_id text;
  v_release_record_id text;
begin
  select rsv.source_version_id, rsv.release_record_id
    into v_source_version_id, v_release_record_id
    from public.release_source_version rsv
   where rsv.release_id={release}
   order by rsv.release_record_id
   limit 1;

  if v_source_version_id is null then
    raise exception 'No Stage 2 release membership available for guard test';
  end if;

  begin
    update public.source_version
       set title = title
     where source_version_id = v_source_version_id;
    raise exception 'SOURCE_VERSION_GUARD_FAILED';
  exception
    when others then
      if sqlerrm = 'SOURCE_VERSION_GUARD_FAILED' then
        raise;
      end if;
      if position('pinned to an approved evidence release and is immutable' in sqlerrm) = 0 then
        raise;
      end if;
  end;

  begin
    update public.release_source_version
       set release_record_id = release_record_id
     where release_id={release}
       and source_version_id = v_source_version_id;
    raise exception 'RELEASE_MEMBERSHIP_GUARD_FAILED';
  exception
    when others then
      if sqlerrm = 'RELEASE_MEMBERSHIP_GUARD_FAILED' then
        raise;
      end if;
      if position('Release membership for approved release' in sqlerrm) = 0 then
        raise;
      end if;
  end;
end;
$$;
"""
    try:
        psql(args.container, guard_sql)
    except subprocess.CalledProcessError as exc:
        errors.append(f"immutability guard test failed: {exc}")

    if errors:
        print("STAGE 2 IDENTITY INVALID")
        for error in errors:
            print("-", error)
        return 1

    print(f"STAGE 2 IDENTITY VALID: {expected} canonical sources / {expected} source versions / {expected} release memberships")
    print(f"release={args.release}; legacy_aliases={legacy_aliases}; doi={dois}; pmid={pmids}; arxiv={arxiv_ids}; canonical_url={urls}")
    print("identity_integrity: all zero failures")
    print("immutability_guards: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
