import { useEffect, useMemo, useState } from 'react'
import { CheckCircle2, FileCheck2, GitCommitHorizontal, LockKeyhole, Plus, RefreshCw, Rocket, ShieldCheck } from 'lucide-react'
import { supabase } from './lib/supabase'
import { humanize } from './workbench'

type ReleaseBuild = {
  release_build_id: string
  target_release_id: string
  build_status: string
  selection_policy: string
  schema_version: string
  taxonomy_version: string
  gateway_contract_version: string
  source_review_document: string
  source_review_section: string | null
  requested_at: string
  prepared_at: string | null
  validated_at: string | null
  prepared_revision: number | null
  validated_revision: number | null
  scientific_state_sha256: string | null
  export_manifest_sha256: string | null
  git_commit_sha: string | null
  approved_at: string | null
  published_at: string | null
  notes: string | null
}

type BuildMember = {
  release_build_id: string
  source_version_id: string
  release_record_id: string
  release_position: number
  source_state_sha256: string | null
}

function shortHash(value: string | null) {
  return value ? `${value.slice(0, 12)}…` : 'Not recorded'
}

export function Stage11ReleaseBuildCockpit({
  isOwner,
  onRegistryRefresh,
  onError,
}: {
  isOwner: boolean
  onRegistryRefresh: () => Promise<void>
  onError: (value: string | null) => void
}) {
  const [loading, setLoading] = useState(false)
  const [builds, setBuilds] = useState<ReleaseBuild[]>([])
  const [members, setMembers] = useState<BuildMember[]>([])
  const [targetRelease, setTargetRelease] = useState('')
  const [busyId, setBusyId] = useState<string | null>(null)

  useEffect(() => { void load() }, [])

  async function load() {
    setLoading(true)
    const [buildRows, memberRows] = await Promise.all([
      supabase.from('evidence_release_build').select('*').order('requested_at', { ascending: false }),
      supabase.from('release_build_source_version').select('release_build_id,source_version_id,release_record_id,release_position,source_state_sha256').order('release_position'),
    ])
    const error = buildRows.error ?? memberRows.error
    if (error) onError(error.message)
    else {
      setBuilds((buildRows.data ?? []) as ReleaseBuild[])
      setMembers((memberRows.data ?? []) as BuildMember[])
    }
    setLoading(false)
  }

  const membersByBuild = useMemo(() => {
    const map = new Map<string, BuildMember[]>()
    for (const member of members) {
      const rows = map.get(member.release_build_id) ?? []
      rows.push(member)
      map.set(member.release_build_id, rows)
    }
    return map
  }, [members])

  async function createBuild() {
    const target = targetRelease.trim()
    if (!target) return
    const safe = target.replace(/[^a-zA-Z0-9._-]+/g, '-').replace(/^-+|-+$/g, '') || 'release'
    const buildId = `erb-${safe}-${Date.now()}`
    setBusyId(buildId)
    onError(null)
    const { error } = await supabase.rpc('create_evidence_release_build', {
      p_release_build_id: buildId,
      p_target_release_id: target,
      p_schema_version: 'registry-v1.1',
      p_taxonomy_version: 'iqm-route-v0.2',
      p_gateway_contract_version: 'csi-evidence-v1',
      p_source_review_document: 'docs/EVIDENCE_REGISTRY_V1_1_IMPLEMENTATION_PLAN.md',
      p_source_review_section: 'Stage 12 release review',
      p_notes: 'Release build created from Evidence Workbench Stage 11 cockpit.',
    })
    if (error) onError(error.message)
    else {
      setTargetRelease('')
      await load()
    }
    setBusyId(null)
  }

  async function runBuildAction(buildId: string, fn: 'prepare_evidence_release_build' | 'approve_evidence_release_build' | 'publish_evidence_release_build') {
    setBusyId(buildId)
    onError(null)
    if (fn === 'publish_evidence_release_build') {
      const ok = window.confirm('Publish this approved build as an immutable evidence release? This is intentionally separate from CSI Gateway publication.')
      if (!ok) { setBusyId(null); return }
    }
    const { error } = await supabase.rpc(fn, { p_release_build_id: buildId })
    if (error) onError(error.message)
    else {
      await load()
      await onRegistryRefresh()
    }
    setBusyId(null)
  }

  return <section style={{ marginTop: 28 }}>
    <div className="page-heading with-action">
      <div>
        <div className="eyebrow">STAGE 11 AUTHORITY</div>
        <h2>Release-build cockpit</h2>
        <p>New releases move through prepare → deterministic validation/export → owner approval → immutable publication. Saving a release-status field is no longer a publication path.</p>
      </div>
      <button className="secondary-button" onClick={() => void load()} disabled={loading}><RefreshCw size={15} className={loading ? 'spin' : ''} /> Refresh</button>
    </div>

    {isOwner && <div className="add-member-card" style={{ marginBottom: 18 }}>
      <h3>Create draft release build</h3>
      <p>This creates governance state only. Preparation pins the latest reviewed source version for each canonical source; validation/export remains a deterministic backend step.</p>
      <label><span className="field-label">Target release ID</span><input className="text-input" value={targetRelease} onChange={(e) => setTargetRelease(e.target.value)} placeholder="e.g. 2026-09-v1.1" /></label>
      <button className="primary-button" disabled={!targetRelease.trim() || busyId !== null} onClick={() => void createBuild()}><Plus size={15} /> Create build</button>
    </div>}

    <div className="release-grid">{builds.map((build) => {
      const buildMembers = membersByBuild.get(build.release_build_id) ?? []
      const hashesComplete = buildMembers.length > 0 && buildMembers.every((row) => row.source_state_sha256)
      return <div className="release-card" key={build.release_build_id}>
        <div className="release-card-head">
          <div><span className="release-id">{build.target_release_id}</span><span className="status-pill">{humanize(build.build_status)}</span></div>
          {build.build_status === 'published' ? <Rocket size={22} /> : <ShieldCheck size={22} />}
        </div>
        <div className="product-meta"><span className="mono">{build.release_build_id}</span></div>
        <div className="release-stats">
          <div><strong>{buildMembers.length}</strong><span>pinned versions</span></div>
          <div><strong>{build.validated_revision ?? build.prepared_revision ?? '—'}</strong><span>state revision</span></div>
          <div><strong>{build.gateway_contract_version}</strong><span>gateway contract</span></div>
        </div>
        <div className="release-source">
          <strong>Deterministic authority</strong>
          <span>Scientific state: <code>{shortHash(build.scientific_state_sha256)}</code></span>
          <span>Manifest: <code>{shortHash(build.export_manifest_sha256)}</code></span>
          <span>Source hashes: {hashesComplete ? 'complete' : buildMembers.length ? 'pending validation/export' : 'not prepared'}</span>
          <span>Git export: <code>{build.git_commit_sha || 'Not recorded'}</code></span>
        </div>
        {build.notes && <p>{build.notes}</p>}
        <div className="detail-meta-row">
          {build.prepared_at && <span className="status-pill"><FileCheck2 size={12} /> Prepared</span>}
          {build.validated_at && <span className="status-pill"><CheckCircle2 size={12} /> Validated</span>}
          {build.approved_at && <span className="status-pill"><LockKeyhole size={12} /> Owner approved</span>}
          {build.git_commit_sha && <span className="status-pill"><GitCommitHorizontal size={12} /> Export recorded</span>}
        </div>
        {isOwner && <div className="detail-meta-row" style={{ marginTop: 12 }}>
          {build.build_status === 'draft' && <button className="secondary-button" disabled={busyId !== null} onClick={() => void runBuildAction(build.release_build_id, 'prepare_evidence_release_build')}>Prepare</button>}
          {build.build_status === 'validated' && <button className="primary-button" disabled={busyId !== null} onClick={() => void runBuildAction(build.release_build_id, 'approve_evidence_release_build')}>Approve build</button>}
          {build.build_status === 'approved' && <button className="primary-button" disabled={busyId !== null} onClick={() => void runBuildAction(build.release_build_id, 'publish_evidence_release_build')}>Publish immutable release</button>}
          {build.build_status === 'prepared' && <span className="small-copy">Run deterministic backend validation/export before owner approval.</span>}
        </div>}
      </div>
    })}</div>
    {!loading && builds.length === 0 && <div className="empty-state">No governed release builds yet. The historical 2026-08-23 seed remains an immutable compatibility release.</div>}
  </section>
}
