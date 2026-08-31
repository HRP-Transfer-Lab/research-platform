import { useEffect, useMemo, useState } from 'react'
import { Check, Plus, RefreshCw, Save, ShieldCheck, X } from 'lucide-react'
import { supabase } from './lib/supabase'
import { DetailSection, EditInput, EmptyLine } from './WorkbenchUi'
import { humanize, type EvidenceSource, type RegistryData } from './workbench'

type Framework = {
  framework_key: string
  label: string
  framework_family: string
  subject_kind: string
  version_label: string | null
  description: string
  active: boolean
}

type StudyQualityStatus = {
  study_id: number
  assessment_status: string
  mapping_source: string
  review_status: string
  notes: string | null
}

type ResultRobStatus = {
  outcome_id: number
  assessment_status: string
  mapping_source: string
  review_status: string
  notes: string | null
}

type StudyAssessment = {
  study_quality_assessment_id: number
  study_id: number
  assessment_key: string
  assessment_kind: string
  framework_key: string
  framework_version: string | null
  overall_judgement: string | null
  assessment_status: string
  notes: string | null
  assessor: string | null
  assessed_on: string | null
  mapping_source: string
  review_status: string
}

type ResultAssessment = {
  result_rob_assessment_id: number
  outcome_id: number
  contrast_id: number | null
  effect_estimate_id: number | null
  assessment_key: string
  framework_key: string
  framework_version: string | null
  estimand_or_result_scope: string | null
  overall_judgement: string | null
  assessment_status: string
  notes: string | null
  assessor: string | null
  assessed_on: string | null
  mapping_source: string
  review_status: string
}

type DomainJudgement = {
  assessment_domain_judgement_id: number
  study_quality_assessment_id: number | null
  result_rob_assessment_id: number | null
  domain_key: string
  domain_label: string
  judgement: string
  supporting_text: string | null
  notes: string | null
  order_index: number | null
  mapping_source: string
  review_status: string
}

type Contrast = { contrast_id: number; contrast_label: string; contrast_type: string }
type Effect = { effect_estimate_id: number; outcome_id: number; contrast_id: number | null; estimate_scope: string; metric: string; estimate_value: number }

const subjectStatusOptions = ['not_yet_assessed', 'assessment_in_progress', 'partially_assessed', 'reviewed_complete', 'not_applicable']
const assessmentStatusOptions = ['assessment_in_progress', 'partially_assessed', 'reviewed_complete', 'insufficient_information', 'not_applicable']
const studyKinds = ['methodological_quality', 'reporting_completeness', 'review_methodology', 'measurement_quality', 'other']

function ReviewPills({ source, status }: { source: string; status: string }) {
  return <span className="detail-meta-row"><span className="status-pill">{humanize(source)}</span><span className="status-pill">{humanize(status)}</span></span>
}

function ReviewButtons({ onApprove, onReject }: { onApprove: () => void; onReject: () => void }) {
  return <span className="detail-meta-row"><button className="icon-button mini" title="Approve" onClick={onApprove}><Check size={13} /></button><button className="icon-button mini" title="Reject" onClick={onReject}><X size={13} /></button></span>
}

function frameworksForStudyKind(frameworks: Framework[], kind: string) {
  const allowed: Record<string, string[]> = {
    methodological_quality: ['study_methodological_quality', 'custom'],
    reporting_completeness: ['study_reporting_completeness', 'custom'],
    review_methodology: ['study_review_methodology', 'custom'],
    measurement_quality: ['study_measurement_quality', 'custom'],
    other: ['custom'],
  }
  return frameworks.filter((item) => allowed[kind]?.includes(item.subject_kind) && item.active)
}

function DomainRows({
  domains,
  canEdit,
  onReview,
}: {
  domains: DomainJudgement[]
  canEdit: boolean
  onReview: (row: DomainJudgement, status: 'approved' | 'rejected') => Promise<void>
}) {
  if (!domains.length) return <p className="small-copy">No domain-level judgements recorded.</p>
  return <div className="stack-list">{domains.map((row) => <div className="record-note" key={row.assessment_domain_judgement_id}>
    <strong>{row.domain_label}</strong> · {row.judgement} <ReviewPills source={row.mapping_source} status={row.review_status} />
    {row.supporting_text && <p className="small-copy">{row.supporting_text}</p>}
    {canEdit && <ReviewButtons onApprove={() => void onReview(row, 'approved')} onReject={() => void onReview(row, 'rejected')} />}
  </div>)}</div>
}

export function Stage7QualityReview({
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
  const outcomes = data.outcomes.filter((item) => item.study_id === study?.study_id)
  const outcomeIds = useMemo(() => outcomes.map((item) => item.outcome_id), [outcomes])

  const [loading, setLoading] = useState(false)
  const [frameworks, setFrameworks] = useState<Framework[]>([])
  const [studyStatus, setStudyStatus] = useState<StudyQualityStatus | null>(null)
  const [resultStatuses, setResultStatuses] = useState<ResultRobStatus[]>([])
  const [studyAssessments, setStudyAssessments] = useState<StudyAssessment[]>([])
  const [resultAssessments, setResultAssessments] = useState<ResultAssessment[]>([])
  const [domains, setDomains] = useState<DomainJudgement[]>([])
  const [contrasts, setContrasts] = useState<Contrast[]>([])
  const [effects, setEffects] = useState<Effect[]>([])
  const [showStudyForm, setShowStudyForm] = useState(false)
  const [resultFormOutcome, setResultFormOutcome] = useState<number | null>(null)

  useEffect(() => { void load() }, [source.source_id, study?.study_id, outcomeIds.join(',')])

  async function load() {
    if (!study) {
      setStudyStatus(null); setResultStatuses([]); setStudyAssessments([]); setResultAssessments([]); setDomains([]); setContrasts([]); setEffects([])
      return
    }
    setLoading(true)
    onError(null)

    const baseQueries = await Promise.all([
      supabase.from('assessment_framework_definition').select('*').order('framework_key'),
      supabase.from('study_quality_status').select('*').eq('study_id', study.study_id).maybeSingle(),
      supabase.from('study_quality_assessment').select('*').eq('study_id', study.study_id).order('study_quality_assessment_id'),
      supabase.from('study_contrast').select('contrast_id,contrast_label,contrast_type').eq('study_id', study.study_id).order('contrast_id'),
    ])
    const firstError = baseQueries.find((result) => result.error)?.error
    if (firstError) { onError(firstError.message); setLoading(false); return }

    const [frameworkRows, statusRow, studyAssessmentRows, contrastRows] = baseQueries
    const resultQueries = outcomeIds.length ? await Promise.all([
      supabase.from('result_rob_status').select('*').in('outcome_id', outcomeIds).order('outcome_id'),
      supabase.from('result_risk_of_bias_assessment').select('*').in('outcome_id', outcomeIds).order('result_rob_assessment_id'),
      supabase.from('effect_estimate').select('effect_estimate_id,outcome_id,contrast_id,estimate_scope,metric,estimate_value').in('outcome_id', outcomeIds).order('effect_estimate_id'),
    ]) : []
    const resultError = resultQueries.find((result) => result.error)?.error
    if (resultError) { onError(resultError.message); setLoading(false); return }

    const resultAssessmentRows = resultQueries[1]
    const studyIds = ((studyAssessmentRows.data ?? []) as StudyAssessment[]).map((item) => item.study_quality_assessment_id)
    const robIds = resultAssessmentRows ? ((resultAssessmentRows.data ?? []) as ResultAssessment[]).map((item) => item.result_rob_assessment_id) : []
    const domainFilters: string[] = []
    if (studyIds.length) domainFilters.push(`study_quality_assessment_id.in.(${studyIds.join(',')})`)
    if (robIds.length) domainFilters.push(`result_rob_assessment_id.in.(${robIds.join(',')})`)
    let domainRows: { data: any[] | null; error: any } = { data: [], error: null }
    if (domainFilters.length) domainRows = await supabase.from('assessment_domain_judgement').select('*').or(domainFilters.join(',')).order('order_index')
    if (domainRows.error) { onError(domainRows.error.message); setLoading(false); return }

    setFrameworks((frameworkRows.data ?? []) as Framework[])
    setStudyStatus((statusRow.data ?? null) as StudyQualityStatus | null)
    setStudyAssessments((studyAssessmentRows.data ?? []) as StudyAssessment[])
    setContrasts((contrastRows.data ?? []) as Contrast[])
    setResultStatuses(resultQueries[0] ? (resultQueries[0].data ?? []) as ResultRobStatus[] : [])
    setResultAssessments(resultAssessmentRows ? (resultAssessmentRows.data ?? []) as ResultAssessment[] : [])
    setEffects(resultQueries[2] ? (resultQueries[2].data ?? []) as Effect[] : [])
    setDomains((domainRows.data ?? []) as DomainJudgement[])
    setLoading(false)
  }

  async function updateStudyStatus(status: string) {
    if (!study) return
    const { error } = await supabase.from('study_quality_status').update({ assessment_status: status, mapping_source: 'human_review', review_status: 'approved', updated_at: new Date().toISOString() }).eq('study_id', study.study_id)
    if (error) onError(error.message); else await load()
  }

  async function updateResultStatus(outcomeId: number, status: string) {
    const { error } = await supabase.from('result_rob_status').update({ assessment_status: status, mapping_source: 'human_review', review_status: 'approved', updated_at: new Date().toISOString() }).eq('outcome_id', outcomeId)
    if (error) onError(error.message); else await load()
  }

  async function reviewStudyAssessment(id: number, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('study_quality_assessment').update({ mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }).eq('study_quality_assessment_id', id)
    if (error) onError(error.message); else await load()
  }

  async function reviewResultAssessment(id: number, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('result_risk_of_bias_assessment').update({ mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }).eq('result_rob_assessment_id', id)
    if (error) onError(error.message); else await load()
  }

  async function reviewDomain(row: DomainJudgement, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('assessment_domain_judgement').update({ mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }).eq('assessment_domain_judgement_id', row.assessment_domain_judgement_id)
    if (error) onError(error.message); else await load()
  }

  const frameworkByKey = useMemo(() => new Map(frameworks.map((item) => [item.framework_key, item])), [frameworks])
  const contrastById = useMemo(() => new Map(contrasts.map((item) => [item.contrast_id, item])), [contrasts])
  const effectById = useMemo(() => new Map(effects.map((item) => [item.effect_estimate_id, item])), [effects])

  return <DetailSection title="Quality & risk of bias" icon={<ShieldCheck size={17} />}>
    <div className="record-note">Stage 7 separates study/report appraisal from result-specific risk of bias. Reporting completeness is not RoB. GRADE/body certainty is deliberately deferred to Stage 8 and is not available as a source, study or result write option.</div>
    {loading && <div className="small-copy" style={{ marginTop: 12 }}><RefreshCw className="spin" size={14} /> Loading Stage 7 quality architecture…</div>}
    {!study && <EmptyLine>No normalized study row.</EmptyLine>}

    {study && studyStatus && <div style={{ marginTop: 16 }}>
      <div className="product-head"><strong>Study / report quality status</strong><ReviewPills source={studyStatus.mapping_source} status={studyStatus.review_status} /></div>
      <div className="product-meta"><span>{humanize(studyStatus.assessment_status)}</span></div>
      {canEdit && <label><span className="field-label">Assessment state</span><select className="select-input" value={studyStatus.assessment_status} onChange={(e) => void updateStudyStatus(e.target.value)}>{subjectStatusOptions.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label>}
    </div>}

    {study && <div style={{ marginTop: 18 }}>
      <div className="product-head"><span className="field-label">Study / report assessments ({studyAssessments.length})</span>{canEdit && <button className="text-button" onClick={() => setShowStudyForm((value) => !value)}><Plus size={14} /> Add typed assessment</button>}</div>
      {showStudyForm && <StudyAssessmentForm studyId={study.study_id} frameworks={frameworks} onDone={async () => { setShowStudyForm(false); await load() }} onError={onError} />}
      <div className="stack-list">{studyAssessments.length ? studyAssessments.map((item) => {
        const framework = frameworkByKey.get(item.framework_key)
        const itemDomains = domains.filter((row) => row.study_quality_assessment_id === item.study_quality_assessment_id)
        return <div className="product-card" key={item.study_quality_assessment_id}>
          <div className="product-head"><div><strong>{framework?.label ?? item.framework_key}</strong><span className="match-pill">{humanize(item.assessment_kind)}</span></div><ReviewPills source={item.mapping_source} status={item.review_status} /></div>
          <div className="product-meta"><span>{humanize(item.assessment_status)}</span><span>{item.framework_version || framework?.version_label || 'Version not recorded'}</span></div>
          <p><strong>Overall judgement:</strong> {item.overall_judgement || 'Not yet recorded'}</p>
          {item.notes && <p className="small-copy">{item.notes}</p>}
          <DomainRows domains={itemDomains} canEdit={canEdit} onReview={reviewDomain} />
          {canEdit && <ReviewButtons onApprove={() => void reviewStudyAssessment(item.study_quality_assessment_id, 'approved')} onReject={() => void reviewStudyAssessment(item.study_quality_assessment_id, 'rejected')} />}
        </div>
      }) : <EmptyLine>No typed study/report assessment recorded.</EmptyLine>}</div>
    </div>}

    {study && <div style={{ marginTop: 22 }}>
      <span className="field-label">Result-specific risk of bias</span>
      <div className="stack-list">{outcomes.map((outcome) => {
        const status = resultStatuses.find((item) => item.outcome_id === outcome.outcome_id)
        const rows = resultAssessments.filter((item) => item.outcome_id === outcome.outcome_id)
        return <div className="product-card" key={outcome.outcome_id}>
          <div className="product-head"><strong>{outcome.outcome_name}</strong>{status && <ReviewPills source={status.mapping_source} status={status.review_status} />}</div>
          {status && <div className="product-meta"><span>{humanize(status.assessment_status)}</span></div>}
          {canEdit && status && <div className="two-fields"><label><span className="field-label">RoB assessment state</span><select className="select-input" value={status.assessment_status} onChange={(e) => void updateResultStatus(outcome.outcome_id, e.target.value)}>{subjectStatusOptions.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><button className="text-button fit" onClick={() => setResultFormOutcome(resultFormOutcome === outcome.outcome_id ? null : outcome.outcome_id)}><Plus size={14} /> Add result RoB</button></div>}
          {resultFormOutcome === outcome.outcome_id && <ResultAssessmentForm outcomeId={outcome.outcome_id} frameworks={frameworks} contrasts={contrasts} effects={effects.filter((item) => item.outcome_id === outcome.outcome_id && item.estimate_scope !== 'source_level_synthesis')} onDone={async () => { setResultFormOutcome(null); await load() }} onError={onError} />}
          {rows.length ? rows.map((item) => {
            const framework = frameworkByKey.get(item.framework_key)
            const contrast = item.contrast_id ? contrastById.get(item.contrast_id) : null
            const effect = item.effect_estimate_id ? effectById.get(item.effect_estimate_id) : null
            const itemDomains = domains.filter((row) => row.result_rob_assessment_id === item.result_rob_assessment_id)
            return <div className="record-note" key={item.result_rob_assessment_id}>
              <div className="product-head"><div><strong>{framework?.label ?? item.framework_key}</strong><span className="match-pill">{humanize(item.assessment_status)}</span></div><ReviewPills source={item.mapping_source} status={item.review_status} /></div>
              <p className="small-copy">Contrast: {contrast?.contrast_label ?? 'Not linked'} · Effect: {effect ? `${effect.metric} ${effect.estimate_value}` : 'Not linked'}</p>
              {item.estimand_or_result_scope && <p>{item.estimand_or_result_scope}</p>}
              <p><strong>Overall judgement:</strong> {item.overall_judgement || 'Not yet recorded'}</p>
              <DomainRows domains={itemDomains} canEdit={canEdit} onReview={reviewDomain} />
              {canEdit && <ReviewButtons onApprove={() => void reviewResultAssessment(item.result_rob_assessment_id, 'approved')} onReject={() => void reviewResultAssessment(item.result_rob_assessment_id, 'rejected')} />}
            </div>
          }) : <p className="small-copy">No result-specific RoB assessment recorded.</p>}
        </div>
      })}</div>
    </div>}

    <div className="record-note" style={{ marginTop: 18 }}><strong>Body certainty / GRADE:</strong> deferred to Stage 8, where it will attach to evidence propositions or synthesis outcomes rather than to this source or study.</div>
  </DetailSection>
}

function StudyAssessmentForm({ studyId, frameworks, onDone, onError }: { studyId: number; frameworks: Framework[]; onDone: () => Promise<void>; onError: (value: string | null) => void }) {
  const [kind, setKind] = useState('reporting_completeness')
  const available = frameworksForStudyKind(frameworks, kind)
  const [frameworkKey, setFrameworkKey] = useState('consort')
  const [overallJudgement, setOverallJudgement] = useState('')
  const [assessmentStatus, setAssessmentStatus] = useState('assessment_in_progress')
  const [notes, setNotes] = useState('')
  const [assessor, setAssessor] = useState('')

  useEffect(() => {
    if (!available.some((item) => item.framework_key === frameworkKey)) setFrameworkKey(available[0]?.framework_key ?? 'custom')
  }, [kind, frameworks.length])

  async function save() {
    const key = `${kind}_${frameworkKey}_${Date.now()}`
    const { error } = await supabase.from('study_quality_assessment').insert({
      study_id: studyId, assessment_key: key, assessment_kind: kind, framework_key: frameworkKey,
      overall_judgement: overallJudgement || null, assessment_status: assessmentStatus, notes: notes || null,
      assessor: assessor || null, assessed_on: new Date().toISOString().slice(0, 10), mapping_source: 'human_review', review_status: 'proposed',
    })
    if (error) onError(error.message); else await onDone()
  }

  return <div className="quality-form">
    <div className="two-fields"><label><span className="field-label">Assessment kind</span><select className="select-input" value={kind} onChange={(e) => setKind(e.target.value)}>{studyKinds.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><label><span className="field-label">Framework</span><select className="select-input" value={frameworkKey} onChange={(e) => setFrameworkKey(e.target.value)}>{available.map((item) => <option key={item.framework_key} value={item.framework_key}>{item.label}</option>)}</select></label></div>
    <div className="two-fields"><EditInput label="Overall judgement" value={overallJudgement} onChange={setOverallJudgement} /><EditInput label="Assessor" value={assessor} onChange={setAssessor} /></div>
    <label><span className="field-label">Assessment status</span><select className="select-input" value={assessmentStatus} onChange={(e) => setAssessmentStatus(e.target.value)}>{assessmentStatusOptions.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label>
    <label className="field-label">Notes</label><textarea className="textarea" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
    <button className="primary-button fit" onClick={() => void save()}><Save size={14} /> Save typed assessment</button>
  </div>
}

function ResultAssessmentForm({ outcomeId, frameworks, contrasts, effects, onDone, onError }: { outcomeId: number; frameworks: Framework[]; contrasts: Contrast[]; effects: Effect[]; onDone: () => Promise<void>; onError: (value: string | null) => void }) {
  const available = frameworks.filter((item) => ['result_risk_of_bias', 'custom'].includes(item.subject_kind) && item.active)
  const [frameworkKey, setFrameworkKey] = useState(available.find((item) => item.framework_key === 'rob2')?.framework_key ?? available[0]?.framework_key ?? 'custom')
  const [contrastId, setContrastId] = useState('')
  const [effectId, setEffectId] = useState('')
  const [scope, setScope] = useState('')
  const [overallJudgement, setOverallJudgement] = useState('')
  const [assessmentStatus, setAssessmentStatus] = useState('assessment_in_progress')
  const [notes, setNotes] = useState('')
  const [assessor, setAssessor] = useState('')

  async function save() {
    const key = `${frameworkKey}_${Date.now()}`
    const selectedEffect = effectId ? effects.find((item) => item.effect_estimate_id === Number(effectId)) : null
    const selectedContrast = selectedEffect?.contrast_id ?? (contrastId ? Number(contrastId) : null)
    const { error } = await supabase.from('result_risk_of_bias_assessment').insert({
      outcome_id: outcomeId, contrast_id: selectedContrast, effect_estimate_id: effectId ? Number(effectId) : null,
      assessment_key: key, framework_key: frameworkKey, estimand_or_result_scope: scope || null,
      overall_judgement: overallJudgement || null, assessment_status: assessmentStatus, notes: notes || null,
      assessor: assessor || null, assessed_on: new Date().toISOString().slice(0, 10), mapping_source: 'human_review', review_status: 'proposed',
    })
    if (error) onError(error.message); else await onDone()
  }

  return <div className="quality-form">
    <div className="two-fields"><label><span className="field-label">RoB framework</span><select className="select-input" value={frameworkKey} onChange={(e) => setFrameworkKey(e.target.value)}>{available.map((item) => <option key={item.framework_key} value={item.framework_key}>{item.label}</option>)}</select></label><label><span className="field-label">Stage 5 contrast</span><select className="select-input" value={contrastId} onChange={(e) => setContrastId(e.target.value)}><option value="">Not linked / not yet extracted</option>{contrasts.map((item) => <option key={item.contrast_id} value={item.contrast_id}>{item.contrast_label}</option>)}</select></label></div>
    <label><span className="field-label">Stage 6 effect estimate</span><select className="select-input" value={effectId} onChange={(e) => setEffectId(e.target.value)}><option value="">Not linked</option>{effects.map((item) => <option key={item.effect_estimate_id} value={item.effect_estimate_id}>{item.metric}: {item.estimate_value}</option>)}</select></label>
    <EditInput label="Estimand / result scope" value={scope} onChange={setScope} />
    <div className="two-fields"><EditInput label="Overall judgement" value={overallJudgement} onChange={setOverallJudgement} /><EditInput label="Assessor" value={assessor} onChange={setAssessor} /></div>
    <label><span className="field-label">Assessment status</span><select className="select-input" value={assessmentStatus} onChange={(e) => setAssessmentStatus(e.target.value)}>{assessmentStatusOptions.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label>
    <label className="field-label">Notes</label><textarea className="textarea" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
    <button className="primary-button fit" onClick={() => void save()}><Save size={14} /> Save result RoB assessment</button>
  </div>
}
