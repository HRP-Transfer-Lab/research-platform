import { useEffect, useMemo, useState } from 'react'
import { Gauge, Pencil, Save } from 'lucide-react'
import { supabase } from './lib/supabase'

export type MaturityDefinition = {
  scale_version: string
  maturity_level: number
  code: string
  label: string
  short_label: string
  description: string
  cumulative_requirement: string
  color_token: string
}

export type MaturityAssessment = {
  maturity_assessment_id: number
  source_id: string | null
  synthesis_id: string | null
  claim_id: string | null
  scale_version: string
  maturity_level: number
  scope: 'record_contribution' | 'body_of_evidence'
  status: 'provisional_seed' | 'reviewed' | 'approved'
  basis: string
  assessed_on: string
  assessor: string | null
}

export function MaturityBadge({ level, label, colorToken, status }: { level: number; label: string; colorToken: string; status?: string | null }) {
  return (
    <span className={`eml-badge eml-${colorToken}`} title={status ? `${label} · ${status.replaceAll('_', ' ')}` : label}>
      <strong>EML{level}</strong>
      <span>{label}</span>
    </span>
  )
}

export function EvidenceMaturitySection({ sourceId, canEdit, onError }: { sourceId: string; canEdit: boolean; onError: (value: string | null) => void }) {
  const [definitions, setDefinitions] = useState<MaturityDefinition[]>([])
  const [assessment, setAssessment] = useState<MaturityAssessment | null>(null)
  const [editing, setEditing] = useState(false)
  const [level, setLevel] = useState(1)
  const [status, setStatus] = useState<MaturityAssessment['status']>('provisional_seed')
  const [basis, setBasis] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => { void load() }, [sourceId])

  async function load() {
    setLoading(true)
    const [defs, row] = await Promise.all([
      supabase
        .from('evidence_maturity_level_definition')
        .select('*')
        .eq('scale_version', 'hrp-eml-v1')
        .order('maturity_level'),
      supabase
        .from('evidence_maturity_assessment')
        .select('*')
        .eq('source_id', sourceId)
        .eq('scale_version', 'hrp-eml-v1')
        .maybeSingle(),
    ])
    const err = defs.error ?? row.error
    if (err) onError(err.message)
    const nextDefs = (defs.data ?? []) as MaturityDefinition[]
    const next = (row.data as MaturityAssessment | null) ?? null
    setDefinitions(nextDefs)
    setAssessment(next)
    const fallback = nextDefs.find((item) => item.maturity_level === 1) ?? nextDefs[0]
    setLevel(next?.maturity_level ?? fallback?.maturity_level ?? 1)
    setStatus(next?.status ?? 'provisional_seed')
    setBasis(next?.basis ?? '')
    setEditing(false)
    setLoading(false)
  }

  const definition = useMemo(
    () => definitions.find((item) => item.maturity_level === (assessment?.maturity_level ?? level)) ?? null,
    [definitions, assessment, level],
  )

  async function save() {
    const payload = {
      source_id: sourceId,
      scale_version: 'hrp-eml-v1',
      maturity_level: level,
      scope: 'record_contribution' as const,
      status,
      basis: basis.trim(),
      assessed_on: new Date().toISOString().slice(0, 10),
    }
    if (!payload.basis) {
      onError('Evidence maturity requires a written basis.')
      return
    }
    const response = assessment
      ? await supabase.from('evidence_maturity_assessment').update(payload).eq('maturity_assessment_id', assessment.maturity_assessment_id)
      : await supabase.from('evidence_maturity_assessment').insert(payload)
    if (response.error) onError(response.error.message)
    else await load()
  }

  return (
    <section className="detail-section maturity-section">
      <div className="section-heading">
        <div><Gauge size={17} /><h3>Evidence maturity</h3></div>
        {canEdit && <button className="text-button" onClick={() => setEditing((value) => !value)}><Pencil size={14} /> {editing ? 'Cancel' : 'Review EML'}</button>}
      </div>

      {loading ? <div className="empty-line">Loading maturity assessment…</div> : editing ? (
        <div className="edit-stack maturity-edit">
          <label className="field-label">HRP Evidence Maturity Level</label>
          <select className="select-input" value={level} onChange={(event) => setLevel(Number(event.target.value))}>
            {definitions.map((item) => <option key={item.maturity_level} value={item.maturity_level}>EML{item.maturity_level} · {item.label}</option>)}
          </select>
          {definitions.find((item) => item.maturity_level === level) && (
            <div className="maturity-definition-preview">
              <strong>{definitions.find((item) => item.maturity_level === level)?.description}</strong>
              <span>{definitions.find((item) => item.maturity_level === level)?.cumulative_requirement}</span>
            </div>
          )}
          <label className="field-label">Review status</label>
          <select className="select-input" value={status} onChange={(event) => setStatus(event.target.value as MaturityAssessment['status'])}>
            <option value="provisional_seed">Provisional seed</option>
            <option value="reviewed">Reviewed</option>
            <option value="approved">Approved</option>
          </select>
          <label className="field-label">Basis for this level</label>
          <textarea className="textarea" rows={5} value={basis} onChange={(event) => setBasis(event.target.value)} placeholder="State what this source contributes and why it does or does not satisfy the next cumulative level." />
          <button className="primary-button fit" onClick={save}><Save size={14} /> Save maturity assessment</button>
        </div>
      ) : assessment && definition ? (
        <div className="maturity-display">
          <div className="maturity-display-top">
            <MaturityBadge level={assessment.maturity_level} label={definition.label} colorToken={definition.color_token} status={assessment.status} />
            <span className={`maturity-review-status maturity-status-${assessment.status}`}>{assessment.status.replaceAll('_', ' ')}</span>
          </div>
          <p className="body-copy"><strong>{definition.description}</strong></p>
          <p className="small-copy">{assessment.basis}</p>
          <div className="maturity-boundary">
            <strong>Scope: source contribution.</strong> This level describes what this record contributes to an evidence pathway; it is not a body-level certainty rating and does not replace RoB/GRADE appraisal.
          </div>
        </div>
      ) : (
        <div className="empty-line">No EML assessment recorded. This does not mean the evidence is EML0.</div>
      )}
    </section>
  )
}
