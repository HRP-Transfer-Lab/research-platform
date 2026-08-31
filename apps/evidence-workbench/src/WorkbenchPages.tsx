import { useState } from 'react'
import { Activity, Archive, Plus, RefreshCw } from 'lucide-react'
import { supabase } from './lib/supabase'
import { Stage11ReleaseBuildCockpit } from './Stage11ReleaseBuildCockpit'
import { humanize, type AuditRow, type RegistryData, type Role, type WorkbenchMember } from './workbench'
import { EditInput } from './WorkbenchUi'

export function ReleasesPage({ data, isOwner, onRefresh, onError }: { data: RegistryData; isOwner: boolean; onRefresh: () => Promise<void>; onError: (v: string | null) => void }) {
  return <main className="wide-page">
    <div className="page-heading">
      <div className="eyebrow">VERSIONED EVIDENCE</div>
      <h2>Evidence releases</h2>
      <p>Approved releases are immutable publication states. New releases are created through the governed Stage 11 release-build workflow below rather than by editing a status field.</p>
    </div>
    <div className="release-grid">{data.releases.map((release) => {
      const count = data.sources.filter((s) => s.release_id === release.release_id).length
      return <div className="release-card" key={release.release_id}>
        <div className="release-card-head"><div><span className="release-id">{release.release_id}</span><span className="status-pill">{humanize(release.status)}</span></div><Archive size={22} /></div>
        <div className="release-stats"><div><strong>{count}</strong><span>legacy/source rows</span></div><div><strong>{release.schema_version}</strong><span>schema</span></div><div><strong>{release.taxonomy_version}</strong><span>taxonomy</span></div></div>
        <p>{release.notes}</p>
        <div className="release-source"><strong>Review source</strong><span>{release.source_review_document}</span><span>{release.source_review_section}</span></div>
        <div className="record-note">Release status is read-only here. Approval/publication authority now lives in the governed release-build state machine.</div>
      </div>
    })}</div>
    <Stage11ReleaseBuildCockpit isOwner={isOwner} onRegistryRefresh={onRefresh} onError={onError} />
  </main>
}

export function AuditPage({ rows, onRefresh }: { rows: AuditRow[]; onRefresh: () => void }) {
  return <main className="wide-page"><div className="page-heading with-action"><div><div className="eyebrow">PROVENANCE</div><h2>Workbench audit trail</h2><p>Latest browser-side mutations to scientific records and access roles.</p></div><button className="secondary-button" onClick={onRefresh}><RefreshCw size={15} /> Refresh</button></div><div className="audit-table"><div className="audit-header"><span>Time</span><span>Action</span><span>Table</span><span>Record</span><span>Actor</span></div>{rows.map((row) => { const record = row.after_row ?? row.before_row ?? {}; const identity = record.source_id ?? record.study_id ?? record.outcome_id ?? record.component_id ?? record.product_relevance_id ?? record.release_id ?? record.release_build_id ?? record.field_candidate_id ?? record.authority_id ?? record.user_id ?? '—'; return <div className="audit-row" key={row.audit_id}><span>{new Date(row.occurred_at).toLocaleString()}</span><span><span className={`action-pill action-${row.action.toLowerCase()}`}>{row.action}</span></span><span>{humanize(row.table_name)}</span><span className="mono">{String(identity)}</span><span className="mono small-mono">{row.actor_user_id ?? 'service/admin'}</span></div>})}{rows.length === 0 && <div className="empty-state">No Workbench mutations recorded yet.</div>}</div></main>
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
