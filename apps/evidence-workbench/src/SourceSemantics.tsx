import { useEffect, useMemo, useState } from 'react'
import { Activity, Plus, Trash2 } from 'lucide-react'
import { supabase } from './lib/supabase'
import { ControllerPill, DetailSection, EvidenceRolePill, EmptyLine, RoutePill } from './WorkbenchUi'
import { controllerOverlayOptions, evidenceRoleOptions, humanize, primaryClassification, type EvidenceSource, type RegistryData } from './workbench'

export function SourceSemantics({ source, data, canEdit, onRefresh, onError }: { source: EvidenceSource; data: RegistryData; canEdit: boolean; onRefresh: () => Promise<void>; onError: (value: string | null) => void }) {
  const roles = useMemo(
    () => data.evidenceRoles.filter((item) => item.source_id === source.source_id),
    [data.evidenceRoles, source.source_id],
  )
  const overlays = useMemo(
    () => data.controllerOverlays.filter((item) => item.source_id === source.source_id),
    [data.controllerOverlays, source.source_id],
  )
  const study = data.studies.find((item) => item.source_id === source.source_id)
  const routes = Array.from(new Set(data.components.filter((item) => item.study_id === study?.study_id).map((item) => item.route)))

  const [roleChoice, setRoleChoice] = useState(evidenceRoleOptions[0])
  const [overlayChoice, setOverlayChoice] = useState(controllerOverlayOptions[0])
  const [roleRationale, setRoleRationale] = useState('')
  const [overlayRationale, setOverlayRationale] = useState('')

  useEffect(() => {
    setRoleChoice(roles.find((item) => item.primary_role)?.evidence_role ?? evidenceRoleOptions[0])
    setOverlayChoice(controllerOverlayOptions[0])
    setRoleRationale('')
    setOverlayRationale('')
  }, [source.source_id])

  async function setPrimaryRole() {
    const demote = await supabase.from('source_evidence_role').update({ primary_role: false }).eq('source_id', source.source_id)
    if (demote.error) return onError(demote.error.message)
    const { error } = await supabase.from('source_evidence_role').upsert({
      source_id: source.source_id,
      evidence_role: roleChoice,
      primary_role: true,
      rationale: roleRationale || 'Human-reviewed Workbench classification.',
      mapping_source: 'human_review',
      updated_at: new Date().toISOString(),
    }, { onConflict: 'source_id,evidence_role' })
    if (error) onError(error.message)
    else await onRefresh()
  }

  async function addSecondaryRole() {
    const { error } = await supabase.from('source_evidence_role').upsert({
      source_id: source.source_id,
      evidence_role: roleChoice,
      primary_role: false,
      rationale: roleRationale || 'Human-reviewed secondary evidence role.',
      mapping_source: 'human_review',
      updated_at: new Date().toISOString(),
    }, { onConflict: 'source_id,evidence_role' })
    if (error) onError(error.message)
    else await onRefresh()
  }

  async function removeRole(role: string) {
    const row = roles.find((item) => item.evidence_role === role)
    if (row?.primary_role) {
      onError('Set another primary evidence role before removing the current primary role.')
      return
    }
    const { error } = await supabase.from('source_evidence_role').delete().eq('source_id', source.source_id).eq('evidence_role', role)
    if (error) onError(error.message)
    else await onRefresh()
  }

  async function addOverlay() {
    const { error } = await supabase.from('source_controller_overlay').insert({
      source_id: source.source_id,
      component_id: null,
      controller_overlay: overlayChoice,
      rationale: overlayRationale || 'Human-reviewed Workbench controller/overlay classification.',
      mapping_source: 'human_review',
    })
    if (error) onError(error.message)
    else await onRefresh()
  }

  async function removeOverlay(id: number) {
    const { error } = await supabase.from('source_controller_overlay').delete().eq('source_controller_overlay_id', id)
    if (error) onError(error.message)
    else await onRefresh()
  }

  return (
    <DetailSection title="Route, evidence role & controller semantics" icon={<Activity size={17} />}>
      <div className="record-note">Route answers what an intervention changes. Evidence role answers what this source contributes. Controller/overlay describes cross-cutting supervision or scaffolding. The historical classification remains visible for audit compatibility but is not canonical route authority.</div>

      <div className="info-grid" style={{ marginTop: 12 }}>
        <div className="info-item"><span>Historical classification</span><strong>{humanize(primaryClassification(source))}</strong></div>
        <div className="info-item"><span>Canonical intervention route(s)</span><div className="detail-meta-row">{routes.length ? routes.map((route) => <RoutePill key={route} route={route} />) : <span>None — non-intervention evidence is valid.</span>}</div></div>
      </div>

      <div style={{ marginTop: 14 }}>
        <span className="field-label">Evidence roles</span>
        <div className="stack-list">
          {roles.length ? roles.map((item) => (
            <div className="product-card" key={item.evidence_role}>
              <div className="product-head">
                <div><EvidenceRolePill role={item.evidence_role} />{item.primary_role && <span className="status-pill">Primary</span>}<span className="status-pill">{humanize(item.mapping_source)}</span></div>
                {canEdit && !item.primary_role && <button className="icon-button mini" title="Remove evidence role" onClick={() => removeRole(item.evidence_role)}><Trash2 size={13} /></button>}
              </div>
              {item.rationale && <p className="small-copy">{item.rationale}</p>}
            </div>
          )) : <EmptyLine>No canonical evidence role recorded.</EmptyLine>}
        </div>
      </div>

      {canEdit && (
        <div className="edit-stack subedit" style={{ marginTop: 10 }}>
          <label><span className="field-label">Evidence role</span><select className="select-input" value={roleChoice} onChange={(event) => setRoleChoice(event.target.value)}>{evidenceRoleOptions.map((item) => <option key={item} value={item}>{humanize(item)}</option>)}</select></label>
          <label><span className="field-label">Reviewer rationale</span><input className="text-input" value={roleRationale} onChange={(event) => setRoleRationale(event.target.value)} placeholder="Why does this source contribute this role?" /></label>
          <div className="edit-actions"><button className="primary-button fit" onClick={setPrimaryRole}>Set primary role</button><button className="secondary-button fit" onClick={addSecondaryRole}><Plus size={13} /> Add secondary role</button></div>
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <span className="field-label">Controller / overlay</span>
        <div className="stack-list">
          {overlays.length ? overlays.map((item) => (
            <div className="product-card" key={item.source_controller_overlay_id}>
              <div className="product-head"><div><ControllerPill controller={item.controller_overlay} /><span className="status-pill">{humanize(item.mapping_source)}</span></div>{canEdit && <button className="icon-button mini" title="Remove controller/overlay" onClick={() => removeOverlay(item.source_controller_overlay_id)}><Trash2 size={13} /></button>}</div>
              {item.rationale && <p className="small-copy">{item.rationale}</p>}
            </div>
          )) : <EmptyLine>No controller/overlay recorded. Absence is represented by no linked value.</EmptyLine>}
        </div>
      </div>

      {canEdit && (
        <div className="edit-stack subedit" style={{ marginTop: 10 }}>
          <label><span className="field-label">Controller / overlay</span><select className="select-input" value={overlayChoice} onChange={(event) => setOverlayChoice(event.target.value)}>{controllerOverlayOptions.map((item) => <option key={item} value={item}>{humanize(item)}</option>)}</select></label>
          <label><span className="field-label">Reviewer rationale</span><input className="text-input" value={overlayRationale} onChange={(event) => setOverlayRationale(event.target.value)} placeholder="Why is this controller/overlay present?" /></label>
          <button className="secondary-button fit" onClick={addOverlay}><Plus size={13} /> Add controller / overlay</button>
        </div>
      )}
    </DetailSection>
  )
}
