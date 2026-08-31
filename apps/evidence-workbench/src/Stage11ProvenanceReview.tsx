import { useEffect, useMemo, useState } from 'react'
import { Check, Fingerprint, Pencil, RefreshCw, X } from 'lucide-react'
import { supabase } from './lib/supabase'
import { DetailSection, EmptyLine } from './WorkbenchUi'
import { humanize, type EvidenceSource, type RegistryData } from './workbench'

type ProcessingRun = {
  processing_run_id: number
  run_kind: string
  actor_kind: string
  run_status: string
  provider: string | null
  tool_name: string | null
  tool_version: string | null
  model_name: string | null
  model_version: string | null
  prompt_version: string | null
  extraction_schema_version: string | null
  taxonomy_version: string | null
  code_commit_sha: string | null
  started_at: string
  completed_at: string | null
}

type FieldCandidate = {
  field_candidate_id: number
  processing_run_id: number
  subject_kind: string
  subject_key: unknown
  field_path: string
  candidate_value_json: unknown
  source_basis: string
  confidence: number | null
  candidate_status: string
  supersedes_candidate_id: number | null
  created_at: string
}

type Adjudication = {
  adjudication_id: number
  field_candidate_id: number
  reviewer_user_id: string
  review_decision: string
  reviewed_value_json: unknown
  rationale: string | null
  is_final: boolean
  reviewed_at: string
}

type Authority = {
  authority_id: number
  subject_kind: string
  subject_key: unknown
  field_path: string
  authoritative_value_json: unknown
  source_adjudication_id: number | null
  authority_kind: string
  approved_by: string | null
  approved_at: string
  active: boolean
}

function normalizeJson(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(normalizeJson)
  if (value && typeof value === 'object') {
    const record = value as Record<string, unknown>
    return Object.fromEntries(Object.keys(record).sort().map((key) => [key, normalizeJson(record[key])]))
  }
  return value
}

function stableJson(value: unknown) {
  return JSON.stringify(normalizeJson(value))
}

function prettyJson(value: unknown) {
  try { return JSON.stringify(value, null, 2) } catch { return String(value) }
}

export function Stage11ProvenanceReview({
  source,
  data,
  canEdit,
  onError,
}: {
  source: EvidenceSource
  data: RegistryData
  canEdit: boolean
  onError: (value: string | null) => void
}) {
  const study = data.studies.find((item) => item.source_id === source.source_id)
  const sourceComponents = data.components.filter((item) => item.study_id === study?.study_id)
  const sourceOutcomes = data.outcomes.filter((item) => item.study_id === study?.study_id)

  const [loading, setLoading] = useState(false)
  const [runs, setRuns] = useState<ProcessingRun[]>([])
  const [candidates, setCandidates] = useState<FieldCandidate[]>([])
  const [adjudications, setAdjudications] = useState<Adjudication[]>([])
  const [authorities, setAuthorities] = useState<Authority[]>([])

  useEffect(() => { void load() }, [source.source_id])

  async function load() {
    setLoading(true)
    onError(null)
    const [runRows, candidateRows, adjudicationRows, authorityRows] = await Promise.all([
      supabase.from('scientific_processing_run').select('*').order('started_at', { ascending: false }).limit(500),
      supabase.from('scientific_field_candidate').select('*').order('created_at', { ascending: false }).limit(500),
      supabase.from('scientific_field_adjudication').select('*').order('reviewed_at', { ascending: false }).limit(500),
      supabase.from('scientific_field_authority').select('*').eq('active', true).order('approved_at', { ascending: false }).limit(500),
    ])
    const error = runRows.error ?? candidateRows.error ?? adjudicationRows.error ?? authorityRows.error
    if (error) onError(error.message)
    else {
      setRuns((runRows.data ?? []) as ProcessingRun[])
      setCandidates((candidateRows.data ?? []) as FieldCandidate[])
      setAdjudications((adjudicationRows.data ?? []) as Adjudication[])
      setAuthorities((authorityRows.data ?? []) as Authority[])
    }
    setLoading(false)
  }

  const sourceTokens = useMemo(() => new Set([
    source.source_id,
    `sv-${source.source_id}-v1`,
    `cs-${source.source_id}`,
    ...sourceComponents.map((item) => item.component_name),
    ...sourceOutcomes.map((item) => item.outcome_name),
  ]), [source.source_id, sourceComponents, sourceOutcomes])

  function belongsToSource(key: unknown): boolean {
    if (typeof key === 'string') return sourceTokens.has(key) || key.includes(source.source_id)
    if (Array.isArray(key)) return key.some(belongsToSource)
    if (key && typeof key === 'object') return Object.values(key as Record<string, unknown>).some(belongsToSource)
    return false
  }

  const sourceCandidates = candidates.filter((row) => belongsToSource(row.subject_key))
  const sourceAuthorities = authorities.filter((row) => belongsToSource(row.subject_key))
  const runById = useMemo(() => new Map(runs.map((row) => [row.processing_run_id, row])), [runs])
  const adjudicationByCandidate = useMemo(() => {
    const map = new Map<number, Adjudication[]>()
    for (const row of adjudications) {
      const rows = map.get(row.field_candidate_id) ?? []
      rows.push(row)
      map.set(row.field_candidate_id, rows)
    }
    return map
  }, [adjudications])

  function authorityFor(candidate: FieldCandidate) {
    const key = stableJson(candidate.subject_key)
    return sourceAuthorities.find((row) => row.subject_kind === candidate.subject_kind && row.field_path === candidate.field_path && stableJson(row.subject_key) === key)
  }

  async function adjudicate(candidateId: number, decision: 'accept' | 'reject' | 'correct', reviewedValue?: unknown) {
    onError(null)
    const { error } = await supabase.rpc('adjudicate_scientific_field_candidate', {
      p_field_candidate_id: candidateId,
      p_review_decision: decision,
      p_reviewed_value_json: reviewedValue ?? null,
      p_rationale: decision === 'correct' ? 'Corrected in Evidence Workbench Stage 11 provenance review.' : `Candidate ${decision}ed in Evidence Workbench Stage 11 provenance review.`,
    })
    if (error) onError(error.message); else await load()
  }

  async function correct(candidate: FieldCandidate) {
    const raw = window.prompt('Enter the corrected value as valid JSON:', prettyJson(candidate.candidate_value_json))
    if (raw === null) return
    try {
      const value = JSON.parse(raw)
      await adjudicate(candidate.field_candidate_id, 'correct', value)
    } catch {
      onError('Corrected value must be valid JSON.')
    }
  }

  return <DetailSection title="Processing provenance & field authority" icon={<Fingerprint size={17} />}>
    <div className="record-note">Stage 11 separates machine proposals from human scientific authority. A later extraction run may generate a new candidate, but it cannot overwrite an active reviewed value. Candidate provenance records tool/model/prompt/schema identity; final authority is established only by human adjudication.</div>
    {loading && <div className="small-copy" style={{ marginTop: 12 }}><RefreshCw size={14} className="spin" /> Loading Stage 11 provenance…</div>}

    <div className="stack-list" style={{ marginTop: 14 }}>{sourceCandidates.length ? sourceCandidates.map((candidate) => {
      const run = runById.get(candidate.processing_run_id)
      const candidateAdjudications = adjudicationByCandidate.get(candidate.field_candidate_id) ?? []
      const authority = authorityFor(candidate)
      return <div className="product-card" key={candidate.field_candidate_id}>
        <div className="product-head">
          <div><strong>{humanize(candidate.subject_kind)} · {candidate.field_path}</strong><span className="match-pill">{humanize(candidate.candidate_status)}</span></div>
          <span className="status-pill">Candidate #{candidate.field_candidate_id}</span>
        </div>
        <div className="product-meta">
          <span>Confidence: {candidate.confidence === null ? 'Not supplied' : candidate.confidence.toFixed(2)}</span>
          <span>Run: {run ? `${humanize(run.run_kind)} / ${humanize(run.actor_kind)}` : candidate.processing_run_id}</span>
        </div>
        {run && <div className="record-note">
          <strong>Run provenance:</strong> {[run.provider, run.tool_name && `${run.tool_name}${run.tool_version ? ` ${run.tool_version}` : ''}`, run.model_name && `${run.model_name}${run.model_version ? ` ${run.model_version}` : ''}`].filter(Boolean).join(' · ') || 'No tool/model label'}<br />
          Prompt: {run.prompt_version || 'Not supplied'} · Extraction schema: {run.extraction_schema_version || 'Not supplied'} · Taxonomy: {run.taxonomy_version || 'Not supplied'} · Code: {run.code_commit_sha || 'Not supplied'}
        </div>}
        <p className="small-copy"><strong>Source basis:</strong> {candidate.source_basis}</p>
        <pre className="record-note" style={{ whiteSpace: 'pre-wrap' }}>{prettyJson(candidate.candidate_value_json)}</pre>
        {authority && <div className="record-note"><strong>Current authoritative value ({humanize(authority.authority_kind)}):</strong><pre style={{ whiteSpace: 'pre-wrap', marginBottom: 0 }}>{prettyJson(authority.authoritative_value_json)}</pre></div>}
        {candidateAdjudications.map((row) => <div className="small-copy" key={row.adjudication_id}><strong>{humanize(row.review_decision)}</strong> by {row.reviewer_user_id} · {new Date(row.reviewed_at).toLocaleString()}{row.rationale ? ` — ${row.rationale}` : ''}</div>)}
        {canEdit && candidate.candidate_status === 'proposed' && <div className="detail-meta-row" style={{ marginTop: 10 }}>
          <button className="icon-button mini" title="Accept candidate" onClick={() => void adjudicate(candidate.field_candidate_id, 'accept')}><Check size={13} /></button>
          <button className="icon-button mini" title="Correct candidate" onClick={() => void correct(candidate)}><Pencil size={13} /></button>
          <button className="icon-button mini" title="Reject candidate" onClick={() => void adjudicate(candidate.field_candidate_id, 'reject')}><X size={13} /></button>
        </div>}
      </div>
    }) : <EmptyLine>No first-class Stage 11 field candidates for this source. Historical seed classifications predate this ledger and are intentionally not back-filled with invented model/prompt metadata.</EmptyLine>}</div>

    {sourceAuthorities.length > 0 && <div style={{ marginTop: 18 }}>
      <span className="field-label">Active reviewed field authority</span>
      <div className="stack-list">{sourceAuthorities.map((row) => <div className="product-card" key={row.authority_id}>
        <div className="product-head"><strong>{humanize(row.subject_kind)} · {row.field_path}</strong><span className="status-pill">{humanize(row.authority_kind)}</span></div>
        <pre className="record-note" style={{ whiteSpace: 'pre-wrap' }}>{prettyJson(row.authoritative_value_json)}</pre>
        <div className="small-copy">Approved {new Date(row.approved_at).toLocaleString()} {row.approved_by ? `by ${row.approved_by}` : ''}</div>
      </div>)}</div>
    </div>}
  </DetailSection>
}
