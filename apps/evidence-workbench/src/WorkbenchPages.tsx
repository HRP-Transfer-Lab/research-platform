import { useState } from 'react'
import { Archive, FileSearch, Plus, RefreshCw, Upload } from 'lucide-react'
import { supabase } from './lib/supabase'
import { humanize, type AuditRow, type RegistryData, type Release, type ResearchCandidate, type Role, type WorkbenchMember } from './workbench'
import { EditInput } from './WorkbenchUi'

export function ReleasesPage({ data, isOwner, onRefresh, onError }: { data: RegistryData; isOwner: boolean; onRefresh: () => Promise<void>; onError: (v: string | null) => void }) {
  async function changeStatus(release: Release, status: string) {
    const { error } = await supabase.from('evidence_release').update({ status }).eq('release_id', release.release_id)
    if (error) onError(error.message); else await onRefresh()
  }
  return <main className="wide-page"><div className="page-heading"><div className="eyebrow">VERSIONED EVIDENCE</div><h2>Evidence releases</h2><p>Production consumers should use approved, reproducible releases rather than draft literature records.</p></div><div className="release-grid">{data.releases.map((release) => { const count = data.sources.filter((s) => s.release_id === release.release_id).length; return <div className="release-card" key={release.release_id}><div className="release-card-head"><div><span className="release-id">{release.release_id}</span><span className="status-pill">{humanize(release.status)}</span></div><Archive size={22} /></div><div className="release-stats"><div><strong>{count}</strong><span>sources</span></div><div><strong>{release.schema_version}</strong><span>schema</span></div><div><strong>{release.taxonomy_version}</strong><span>taxonomy</span></div></div><p>{release.notes}</p><div className="release-source"><strong>Review source</strong><span>{release.source_review_document}</span><span>{release.source_review_section}</span></div>{isOwner && <label className="owner-status"><span className="field-label">Owner release status</span><select className="select-input" value={release.status} onChange={(e) => changeStatus(release, e.target.value)}><option value="draft">Draft</option><option value="approved_seed">Approved seed</option><option value="approved_release">Approved release</option><option value="retired">Retired</option></select></label>}</div>})}</div></main>
}

export function AuditPage({ rows, onRefresh }: { rows: AuditRow[]; onRefresh: () => void }) {
  return <main className="wide-page"><div className="page-heading with-action"><div><div className="eyebrow">PROVENANCE</div><h2>Workbench audit trail</h2><p>Latest browser-side mutations to scientific records and access roles.</p></div><button className="secondary-button" onClick={onRefresh}><RefreshCw size={15} /> Refresh</button></div><div className="audit-table"><div className="audit-header"><span>Time</span><span>Action</span><span>Table</span><span>Record</span><span>Actor</span></div>{rows.map((row) => { const record = row.after_row ?? row.before_row ?? {}; const identity = record.source_id ?? record.study_id ?? record.outcome_id ?? record.component_id ?? record.product_relevance_id ?? record.release_id ?? record.user_id ?? '—'; return <div className="audit-row" key={row.audit_id}><span>{new Date(row.occurred_at).toLocaleString()}</span><span><span className={`action-pill action-${row.action.toLowerCase()}`}>{row.action}</span></span><span>{humanize(row.table_name)}</span><span className="mono">{String(identity)}</span><span className="mono small-mono">{row.actor_user_id ?? 'service/admin'}</span></div>})}{rows.length === 0 && <div className="empty-state">No Workbench mutations recorded yet.</div>}</div></main>
}

export function AccessPage({ rows, currentUserId, onRefresh, onError }: { rows: WorkbenchMember[]; currentUserId: string; onRefresh: () => Promise<void>; onError: (v: string | null) => void }) {
  const [uid, setUid] = useState('')
  const [role, setRole] = useState<Role>('viewer')
  const [name, setName] = useState('')
  async function add() {
    const { error } = await supabase.from('workbench_member').insert({ user_id: uid.trim(), role, display_name: name.trim() || null, created_by: currentUserId })
    if (error) onError(error.message); else { setUid(''); setName(''); await onRefresh() }
  }
  async function change(userId: string, nextRole: Role, active: boolean) {
    const { error } = await supabase.from('workbench_member').update({ role: nextRole, active }).eq('user_id', userId)
    if (error) onError(error.message); else await onRefresh()
  }
  return <main className="wide-page"><div className="page-heading"><div className="eyebrow">OWNER CONTROL</div><h2>Workbench access</h2><p>Membership is explicit. Authentication without a row here cannot read Registry tables.</p></div><div className="access-layout"><section className="member-list"><h3>Members</h3>{rows.map((m) => <div className="member-row" key={m.user_id}><div className="member-avatar">{(m.display_name || 'R')[0].toUpperCase()}</div><div className="member-copy"><strong>{m.display_name || 'Reviewer'}</strong><code>{m.user_id}</code></div><select className="select-input compact-select" value={m.role} onChange={(e) => change(m.user_id, e.target.value as Role, m.active)}><option value="viewer">Viewer</option><option value="editor">Editor</option><option value="owner">Owner</option></select><label className="active-check"><input type="checkbox" checked={m.active} onChange={(e) => change(m.user_id, m.role, e.target.checked)} /> Active</label></div>)}</section><section className="add-member-card"><h3>Add member</h3><p>The person signs in once and sends you their Supabase user ID. No email address is required in this role table.</p><EditInput label="User UUID" value={uid} onChange={setUid} /><EditInput label="Display name (optional)" value={name} onChange={setName} /><label className="field-label">Role</label><select className="select-input" value={role} onChange={(e) => setRole(e.target.value as Role)}><option value="viewer">Viewer — read evidence</option><option value="editor">Editor — review/edit evidence</option><option value="owner">Owner — releases, claims & access</option></select><button className="primary-button full" disabled={!uid.trim()} onClick={add}><Plus size={15} /> Add member</button></section></div></main>
}


export function DiscoveryPage({
  rows,
  canEdit,
  currentUserId,
  onRefresh,
  onError,
}: {
  rows: ResearchCandidate[]
  canEdit: boolean
  currentUserId: string
  onRefresh: () => Promise<void>
  onError: (v: string | null) => void
}) {
  async function importQueue(file: File) {
    try {
      const parsed = JSON.parse(await file.text())
      const candidates = Array.isArray(parsed?.candidates) ? parsed.candidates : []
      if (!candidates.length) {
        onError('No candidates found in this scout queue file.')
        return
      }
      const payload = candidates.map((item: any) => ({
        candidate_id: item.candidate_id,
        source: item.source,
        title: item.title,
        identifiers: item.identifiers ?? {},
        published_raw: item.published ?? null,
        venue: item.venue ?? null,
        source_url: item.url ?? null,
        topic_family: item.topic_family,
        consumers: item.consumers ?? [],
        relevance_terms: item.relevance_terms ?? [],
        discovery_status: 'discovered_unscreened',
        claim_status: 'no_public_claim',
        exclusion_reason: null,
        raw_candidate: item,
        last_seen_at: new Date().toISOString(),
      }))
      const { error } = await supabase.from('research_candidate').upsert(payload, { onConflict: 'candidate_id' })
      if (error) onError(error.message)
      else await onRefresh()
    } catch (error) {
      onError(error instanceof Error ? error.message : String(error))
    }
  }

  async function setStatus(candidate: ResearchCandidate, discovery_status: ResearchCandidate['discovery_status']) {
    const payload: any = {
      discovery_status,
      screened_at: discovery_status === 'discovered_unscreened' ? null : new Date().toISOString(),
      screened_by: discovery_status === 'discovered_unscreened' ? null : currentUserId,
    }
    const { error } = await supabase.from('research_candidate').update(payload).eq('candidate_id', candidate.candidate_id)
    if (error) onError(error.message)
    else await onRefresh()
  }

  return <main className="wide-page">
    <div className="page-heading with-action">
      <div>
        <div className="eyebrow">DISCOVERY · NOT YET EVIDENCE</div>
        <h2>Research discovery inbox</h2>
        <p>Scout candidates stay outside the Evidence Registry until they are screened, extracted, human-verified, appraised and released.</p>
      </div>
      {canEdit && <label className="secondary-button">
        <Upload size={15} /> Import scout queue
        <input type="file" accept="application/json,.json" hidden onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) void importQueue(file)
          event.currentTarget.value = ''
        }} />
      </label>}
    </div>
    <div className="release-grid">
      {rows.map((candidate) => <article className="release-card" key={candidate.candidate_id}>
        <div className="release-card-head">
          <div><span className="release-id">{candidate.source}</span><span className="status-pill">{humanize(candidate.discovery_status)}</span></div>
          <FileSearch size={22} />
        </div>
        <h3>{candidate.title}</h3>
        <p>{candidate.venue ?? humanize(candidate.topic_family)}</p>
        <div className="release-source">
          <strong>{humanize(candidate.topic_family)}</strong>
          <span>{candidate.relevance_terms.join(', ') || 'No relevance terms recorded'}</span>
          <span>Consumers: {candidate.consumers.join(', ') || 'Not assigned'}</span>
        </div>
        {candidate.source_url && <p><a href={candidate.source_url} target="_blank" rel="noreferrer">Open source ↗</a></p>}
        <div className="record-note"><strong>Claim boundary:</strong> discovery metadata only — no public claim.</div>
        {canEdit && <label className="owner-status">
          <span className="field-label">Screening decision</span>
          <select className="select-input" value={candidate.discovery_status} onChange={(event) => void setStatus(candidate, event.target.value as ResearchCandidate['discovery_status'])}>
            <option value="discovered_unscreened">Unscreened</option>
            <option value="screening">Screening</option>
            <option value="include_for_review">Include for review</option>
            <option value="exclude">Exclude</option>
            <option value="duplicate">Duplicate</option>
          </select>
        </label>}
      </article>)}
      {rows.length === 0 && <div className="empty-state">No discovery candidates imported yet.</div>}
    </div>
  </main>
}
