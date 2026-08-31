import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Check, RefreshCw, X } from 'lucide-react'
import { supabase } from './lib/supabase'
import { DetailSection, EmptyLine } from './WorkbenchUi'
import { humanize, type EvidenceSource, type RegistryData } from './workbench'

type HarmStatus = {
  study_id: number
  extraction_status: string
  assessment_mode: string
  systematic_assessment: boolean | null
  notes: string | null
  mapping_source: string
  review_status: string
}

type HarmObservation = {
  harm_observation_id: number
  study_id: number
  outcome_id: number | null
  harm_type: string
  harm_label: string
  severity: string | null
  serious: boolean | null
  withdrawal_due_to_harm: boolean | null
  systematically_assessed: boolean | null
  result_summary: string
  evidence_basis: string
  mapping_source: string
  review_status: string
}

type ParticipationObservation = {
  participation_observation_id: number
  study_id: number
  flow_kind: string
  participant_count: number
  source_field: string | null
  evidence_basis: string
  mapping_source: string
  review_status: string
}

type ImplementationStatus = {
  component_id: number
  dimension: string
  extraction_status: string
  notes: string | null
  mapping_source: string
  review_status: string
}

type ImplementationObservation = {
  implementation_observation_id: number
  component_id: number
  dimension: string
  observation_kind: string
  value_text: string | null
  value_numeric: number | null
  unit: string | null
  status_or_level: string | null
  evidence_basis: string
  mapping_source: string
  review_status: string
}

type ReportingAssessment = {
  component_reporting_assessment_id: number
  component_id: number
  assessment_key: string
  framework_key: string
  framework_version: string | null
  overall_judgement: string | null
  assessment_status: string
  notes: string | null
  mapping_source: string
  review_status: string
}

type SupportObservation = {
  support_dependence_id: number
  study_id: number
  component_id: number | null
  outcome_id: number | null
  support_type: string
  support_presence: string
  support_requirement: string
  autonomy_status: string | null
  evidence_basis: string
  mapping_source: string
  review_status: string
}

type BoundaryObservation = {
  boundary_condition_id: number
  study_id: number
  component_id: number | null
  outcome_id: number | null
  proposition_id: number | null
  boundary_dimension: string
  boundary_direction: string
  boundary_summary: string
  evidence_basis: string
  mapping_source: string
  review_status: string
}

const implementationDimensions = [
  'provider',
  'materials_procedures',
  'delivery_mode',
  'fidelity',
  'adherence',
  'tailoring',
  'modification',
  'support_dependence',
  'implementation_burden',
  'cost_resources',
]

function ReviewPills({ source, status }: { source: string; status: string }) {
  return <span className="detail-meta-row"><span className="status-pill">{humanize(source)}</span><span className="status-pill">{humanize(status)}</span></span>
}

function ReviewButtons({ onApprove, onReject }: { onApprove: () => void; onReject: () => void }) {
  return <span className="detail-meta-row"><button className="icon-button mini" title="Approve" onClick={onApprove}><Check size={13} /></button><button className="icon-button mini" title="Reject" onClick={onReject}><X size={13} /></button></span>
}

function unknownBoolean(value: boolean | null) {
  if (value === null) return 'Unknown / not established'
  return value ? 'Yes' : 'No'
}

export function Stage10HarmsImplementationReview({
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
  const components = data.components.filter((item) => item.study_id === study?.study_id)
  const componentIds = useMemo(() => components.map((item) => item.component_id), [components])

  const [loading, setLoading] = useState(false)
  const [harmStatus, setHarmStatus] = useState<HarmStatus | null>(null)
  const [harms, setHarms] = useState<HarmObservation[]>([])
  const [participation, setParticipation] = useState<ParticipationObservation[]>([])
  const [implementationStatus, setImplementationStatus] = useState<ImplementationStatus[]>([])
  const [implementation, setImplementation] = useState<ImplementationObservation[]>([])
  const [reporting, setReporting] = useState<ReportingAssessment[]>([])
  const [support, setSupport] = useState<SupportObservation[]>([])
  const [boundaries, setBoundaries] = useState<BoundaryObservation[]>([])

  useEffect(() => { void load() }, [source.source_id, study?.study_id, componentIds.join(',')])

  async function load() {
    if (!study) {
      setHarmStatus(null); setHarms([]); setParticipation([]); setImplementationStatus([]); setImplementation([]); setReporting([]); setSupport([]); setBoundaries([])
      return
    }
    setLoading(true)
    onError(null)

    const studyQueries = await Promise.all([
      supabase.from('study_harms_status').select('*').eq('study_id', study.study_id).maybeSingle(),
      supabase.from('harm_observation').select('*').eq('study_id', study.study_id).order('harm_observation_id'),
      supabase.from('study_participation_observation').select('*').eq('study_id', study.study_id).order('participation_observation_id'),
      supabase.from('support_dependence_observation').select('*').eq('study_id', study.study_id).order('support_dependence_id'),
      supabase.from('boundary_condition_observation').select('*').eq('study_id', study.study_id).order('boundary_condition_id'),
    ])
    const studyError = studyQueries.find((result) => result.error)?.error
    if (studyError) { onError(studyError.message); setLoading(false); return }

    let statusRows: ImplementationStatus[] = []
    let observationRows: ImplementationObservation[] = []
    let reportingRows: ReportingAssessment[] = []
    if (componentIds.length) {
      const componentQueries = await Promise.all([
        supabase.from('component_implementation_status').select('*').in('component_id', componentIds).order('component_id').order('dimension'),
        supabase.from('component_implementation_observation').select('*').in('component_id', componentIds).order('implementation_observation_id'),
        supabase.from('component_reporting_assessment').select('*').in('component_id', componentIds).order('component_reporting_assessment_id'),
      ])
      const componentError = componentQueries.find((result) => result.error)?.error
      if (componentError) { onError(componentError.message); setLoading(false); return }
      statusRows = (componentQueries[0].data ?? []) as ImplementationStatus[]
      observationRows = (componentQueries[1].data ?? []) as ImplementationObservation[]
      reportingRows = (componentQueries[2].data ?? []) as ReportingAssessment[]
    }

    setHarmStatus((studyQueries[0].data ?? null) as HarmStatus | null)
    setHarms((studyQueries[1].data ?? []) as HarmObservation[])
    setParticipation((studyQueries[2].data ?? []) as ParticipationObservation[])
    setSupport((studyQueries[3].data ?? []) as SupportObservation[])
    setBoundaries((studyQueries[4].data ?? []) as BoundaryObservation[])
    setImplementationStatus(statusRows)
    setImplementation(observationRows)
    setReporting(reportingRows)
    setLoading(false)
  }

  async function reviewRow(table: string, idColumn: string, id: number, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from(table).update({
      mapping_source: 'human_review',
      review_status: reviewStatus,
      updated_at: new Date().toISOString(),
    }).eq(idColumn, id)
    if (error) { onError(error.message); return false }
    return true
  }

  async function reviewHarm(row: HarmObservation, reviewStatus: 'approved' | 'rejected') {
    if (await reviewRow('harm_observation', 'harm_observation_id', row.harm_observation_id, reviewStatus)) await load()
  }

  async function reviewParticipation(row: ParticipationObservation, reviewStatus: 'approved' | 'rejected') {
    if (await reviewRow('study_participation_observation', 'participation_observation_id', row.participation_observation_id, reviewStatus)) await load()
  }

  async function reviewImplementation(row: ImplementationObservation, reviewStatus: 'approved' | 'rejected') {
    if (!await reviewRow('component_implementation_observation', 'implementation_observation_id', row.implementation_observation_id, reviewStatus)) return
    if (reviewStatus === 'approved') {
      const { error } = await supabase.from('component_implementation_status').update({
        extraction_status: 'reviewed_mapped',
        mapping_source: 'human_review',
        review_status: 'approved',
        updated_at: new Date().toISOString(),
      }).eq('component_id', row.component_id).eq('dimension', row.dimension)
      if (error) { onError(error.message); return }
    }
    await load()
  }

  async function reviewSupport(row: SupportObservation, reviewStatus: 'approved' | 'rejected') {
    if (!await reviewRow('support_dependence_observation', 'support_dependence_id', row.support_dependence_id, reviewStatus)) return
    if (reviewStatus === 'approved' && row.component_id !== null) {
      const { error } = await supabase.from('component_implementation_status').update({
        extraction_status: 'reviewed_mapped',
        mapping_source: 'human_review',
        review_status: 'approved',
        updated_at: new Date().toISOString(),
      }).eq('component_id', row.component_id).eq('dimension', 'support_dependence')
      if (error) { onError(error.message); return }
    }
    await load()
  }

  async function reviewBoundary(row: BoundaryObservation, reviewStatus: 'approved' | 'rejected') {
    if (await reviewRow('boundary_condition_observation', 'boundary_condition_id', row.boundary_condition_id, reviewStatus)) await load()
  }

  const outcomeName = (outcomeId: number | null) => data.outcomes.find((item) => item.outcome_id === outcomeId)?.outcome_name ?? (outcomeId ? `Outcome ${outcomeId}` : null)
  const componentName = (componentId: number | null) => data.components.find((item) => item.component_id === componentId)?.component_name ?? (componentId ? `Component ${componentId}` : null)

  return <DetailSection title="Harms, fidelity & implementation" icon={<AlertTriangle size={17} />}>
    <div className="record-note">Stage 10 keeps harm outcomes, harms-reporting completeness, participation flow, fidelity/adherence, support dependence, implementation burden and scientific boundary conditions separate. No report of harm is not evidence of no harm. Participation loss is not automatically non-adherence or harm withdrawal. Support dependence does not itself establish or refute Stage 4 Bridge evidence.</div>
    {loading && <div className="small-copy" style={{ marginTop: 12 }}><RefreshCw className="spin" size={14} /> Loading Stage 10 harms/implementation architecture…</div>}
    {!study && <EmptyLine>No normalized study row.</EmptyLine>}

    {study && <div style={{ marginTop: 16 }}>
      <span className="field-label">Harms assessment state</span>
      {harmStatus ? <div className="product-card">
        <div className="product-head"><strong>{humanize(harmStatus.extraction_status)}</strong><ReviewPills source={harmStatus.mapping_source} status={harmStatus.review_status} /></div>
        <div className="product-meta"><span>Assessment mode: {humanize(harmStatus.assessment_mode)}</span><span>Systematic assessment: {unknownBoolean(harmStatus.systematic_assessment)}</span></div>
        {harmStatus.notes && <p className="small-copy">{harmStatus.notes}</p>}
        <div className="record-note">A reviewed “no harm observed” state is deliberately not offered as a casual control here; the database requires an explicitly systematic, human-approved harms assessment.</div>
      </div> : <EmptyLine>No harms-status row.</EmptyLine>}

      <div className="stack-list" style={{ marginTop: 10 }}>{harms.length ? harms.map((row) => <div className="product-card" key={row.harm_observation_id}>
        <div className="product-head"><strong>{humanize(row.harm_type)} · {row.harm_label}</strong><ReviewPills source={row.mapping_source} status={row.review_status} /></div>
        <div className="product-meta"><span>{outcomeName(row.outcome_id) || 'Study-level observation'}</span><span>Severity: {row.severity ? humanize(row.severity) : 'Unknown'}</span><span>Serious: {unknownBoolean(row.serious)}</span><span>Withdrawal due to harm: {unknownBoolean(row.withdrawal_due_to_harm)}</span></div>
        <p>{row.result_summary}</p><p className="small-copy">{row.evidence_basis}</p>
        {canEdit && row.review_status === 'proposed' && <ReviewButtons onApprove={() => void reviewHarm(row, 'approved')} onReject={() => void reviewHarm(row, 'rejected')} />}
      </div>) : <EmptyLine>No harm observation extracted. This does not mean no harm occurred.</EmptyLine>}</div>
    </div>}

    {study && <div style={{ marginTop: 22 }}>
      <span className="field-label">Participation flow</span>
      <div className="record-note">These are source-grounded sample-flow facts only. They are not automatically adherence, attrition cause, or withdrawal due to harm.</div>
      <div className="stack-list" style={{ marginTop: 10 }}>{participation.length ? participation.map((row) => <div className="product-card" key={row.participation_observation_id}>
        <div className="product-head"><strong>{humanize(row.flow_kind)} · {row.participant_count}</strong><ReviewPills source={row.mapping_source} status={row.review_status} /></div>
        <p className="small-copy">{row.evidence_basis}</p>
        {row.source_field && <div className="product-meta"><span>{row.source_field}</span></div>}
        {canEdit && row.review_status === 'proposed' && <ReviewButtons onApprove={() => void reviewParticipation(row, 'approved')} onReject={() => void reviewParticipation(row, 'rejected')} />}
      </div>) : <EmptyLine>No structured participation-flow fact extracted.</EmptyLine>}</div>
    </div>}

    {study && <div style={{ marginTop: 22 }}>
      <span className="field-label">Component implementation</span>
      <div className="stack-list">{components.length ? components.map((component) => {
        const statuses = implementationStatus.filter((item) => item.component_id === component.component_id)
        const observations = implementation.filter((item) => item.component_id === component.component_id)
        const assessments = reporting.filter((item) => item.component_id === component.component_id)
        return <div className="product-card" key={component.component_id}>
          <div className="product-head"><strong>{component.component_name}</strong></div>
          <div className="record-note">Retained source fields — provider: {component.provider || 'Not recorded'} · delivery: {component.delivery_mode || 'Not recorded'} · setting: {component.setting || 'Not recorded'} · fidelity: {component.fidelity || 'Not recorded'} · tailoring: {component.tailoring || 'Not recorded'}</div>
          <div className="product-meta" style={{ marginTop: 8 }}>{implementationDimensions.map((dimension) => {
            const status = statuses.find((item) => item.dimension === dimension)
            return <span key={dimension}>{humanize(dimension)}: {status ? humanize(status.extraction_status) : 'No status'}</span>
          })}</div>
          <div className="stack-list" style={{ marginTop: 10 }}>{observations.length ? observations.map((row) => <div className="record-note" key={row.implementation_observation_id}>
            <div className="product-head"><strong>{humanize(row.dimension)} · {humanize(row.observation_kind)}</strong><ReviewPills source={row.mapping_source} status={row.review_status} /></div>
            <p>{row.value_text ?? row.value_numeric ?? row.status_or_level ?? 'No value'}</p><p className="small-copy">{row.evidence_basis}</p>
            {canEdit && row.review_status === 'proposed' && <ReviewButtons onApprove={() => void reviewImplementation(row, 'approved')} onReject={() => void reviewImplementation(row, 'rejected')} />}
          </div>) : <EmptyLine>No structured implementation observation.</EmptyLine>}</div>
          <div style={{ marginTop: 10 }}>{assessments.length ? assessments.map((row) => <div className="record-note" key={row.component_reporting_assessment_id}><strong>{row.framework_key} · {humanize(row.assessment_status)}</strong><ReviewPills source={row.mapping_source} status={row.review_status} /></div>) : <div className="small-copy">No TIDieR/component-reporting assessment. Absence is explicit rather than interpreted as adequate reporting/fidelity.</div>}</div>
        </div>
      }) : <EmptyLine>No intervention components for this source.</EmptyLine>}</div>
    </div>}

    {study && <div style={{ marginTop: 22 }}>
      <span className="field-label">Support / autonomy evidence</span>
      <div className="record-note">Support state is result-aware. An unsupported test can demonstrate performance without the support at that test while still leaving spontaneous cue recovery, fading and broader autonomous deployment unestablished.</div>
      <div className="stack-list" style={{ marginTop: 10 }}>{support.length ? support.map((row) => <div className="product-card" key={row.support_dependence_id}>
        <div className="product-head"><strong>{humanize(row.support_type)} · {humanize(row.support_presence)}</strong><ReviewPills source={row.mapping_source} status={row.review_status} /></div>
        <div className="product-meta"><span>{componentName(row.component_id) || 'Study-level'}</span><span>{outcomeName(row.outcome_id) || 'No outcome link'}</span><span>Requirement: {humanize(row.support_requirement)}</span><span>Autonomy: {row.autonomy_status ? humanize(row.autonomy_status) : 'Unknown'}</span></div>
        <p className="small-copy">{row.evidence_basis}</p>
        {canEdit && row.review_status === 'proposed' && <ReviewButtons onApprove={() => void reviewSupport(row, 'approved')} onReject={() => void reviewSupport(row, 'rejected')} />}
      </div>) : <EmptyLine>No structured support-dependence observation.</EmptyLine>}</div>
    </div>}

    {study && <div style={{ marginTop: 22 }}>
      <span className="field-label">Scientific boundaries</span>
      <div className="record-note">Boundary observations record source-supported limits, dissociations or moderators. They are not Stage 9 context-fit scores, RoB, GRADE or EML.</div>
      <div className="stack-list" style={{ marginTop: 10 }}>{boundaries.length ? boundaries.map((row) => <div className="product-card" key={row.boundary_condition_id}>
        <div className="product-head"><strong>{humanize(row.boundary_dimension)} · {humanize(row.boundary_direction)}</strong><ReviewPills source={row.mapping_source} status={row.review_status} /></div>
        <p>{row.boundary_summary}</p><p className="small-copy">{row.evidence_basis}</p>
        <div className="product-meta"><span>{componentName(row.component_id) || 'Study-level'}</span>{outcomeName(row.outcome_id) && <span>{outcomeName(row.outcome_id)}</span>}</div>
        {canEdit && row.review_status === 'proposed' && <ReviewButtons onApprove={() => void reviewBoundary(row, 'approved')} onReject={() => void reviewBoundary(row, 'rejected')} />}
      </div>) : <EmptyLine>No structured boundary observation.</EmptyLine>}</div>
    </div>}
  </DetailSection>
}
