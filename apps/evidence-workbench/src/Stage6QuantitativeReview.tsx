import { useEffect, useMemo, useState } from 'react'
import { Activity, Check, Pencil, RefreshCw, Save, X } from 'lucide-react'
import { supabase } from './lib/supabase'
import { DetailSection, EditInput, EmptyLine } from './WorkbenchUi'
import { humanize, type EvidenceSource, type RegistryData } from './workbench'

type Stage6Status = {
  outcome_id: number
  quantitative_extraction_status: string
  mapping_source: string
  review_status: string
  notes: string | null
}

type EffectEstimate = {
  effect_estimate_id: number
  outcome_id: number
  contrast_id: number | null
  estimate_key: string
  estimate_scope: string
  estimate_type: string
  metric: string
  estimate_value: number
  standard_error: number | null
  ci_level: number | null
  ci_lower: number | null
  ci_upper: number | null
  p_value: number | null
  n_analysed: number | null
  adjustment_status: string
  model_specification: string | null
  time_or_model_label: string | null
  unit: string | null
  scale_direction: string
  source_reported: boolean
  rationale: string | null
  mapping_source: string
  review_status: string
}

type ArmOutcomeSummary = {
  arm_outcome_summary_id: number
  outcome_id: number
  arm_id: number
  summary_key: string
  n_analysed: number | null
  mean: number | null
  sd: number | null
  se: number | null
  proportion: number | null
  count: number | null
  change_mean: number | null
  change_sd: number | null
  unit: string | null
  source_reported: boolean
  rationale: string | null
  mapping_source: string
  review_status: string
}

type Contrast = { contrast_id: number; contrast_label: string; contrast_type: string }
type Arm = { arm_id: number; arm_label: string }

const extractionStatuses = [
  'not_yet_extracted', 'partially_extracted', 'reviewed_complete',
  'reviewed_no_quantitative_estimate', 'not_reported', 'not_applicable',
]
const estimateScopes = ['study_contrast', 'within_group', 'single_group', 'association', 'measurement', 'source_level_synthesis', 'other']
const estimateTypes = [
  'raw_mean', 'raw_proportion', 'change_score', 'mean_difference',
  'standardised_mean_difference', 'odds_ratio', 'risk_ratio', 'hazard_ratio',
  'correlation', 'regression_coefficient', 'rate_ratio', 'other',
]
const adjustmentStatuses = ['unadjusted', 'adjusted', 'partially_adjusted', 'not_applicable', 'unclear']
const scaleDirections = ['higher_is_better', 'higher_is_worse', 'neutral_or_metric_defined', 'unclear']

function ReviewPills({ source, status }: { source: string; status: string }) {
  return <span className="detail-meta-row"><span className="status-pill">{humanize(source)}</span><span className="status-pill">{humanize(status)}</span></span>
}

function ReviewButtons({ onApprove, onReject }: { onApprove: () => void; onReject: () => void }) {
  return <span className="detail-meta-row"><button className="icon-button mini" title="Approve" onClick={onApprove}><Check size={13} /></button><button className="icon-button mini" title="Reject" onClick={onReject}><X size={13} /></button></span>
}

function numericOrNull(value: string): number | null {
  if (!value.trim()) return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
}

function formatCi(item: EffectEstimate) {
  if (item.ci_lower == null || item.ci_upper == null) return 'Not extracted'
  const level = item.ci_level == null ? 'level unknown' : `${Math.round(item.ci_level * 100)}% CI`
  return `${item.ci_lower} to ${item.ci_upper} (${level})`
}

function EffectCard({
  item,
  contrasts,
  canEdit,
  onRefresh,
  onError,
}: {
  item: EffectEstimate
  contrasts: Contrast[]
  canEdit: boolean
  onRefresh: () => Promise<void>
  onError: (value: string | null) => void
}) {
  const [edit, setEdit] = useState(false)
  const [form, setForm] = useState({
    estimate_scope: item.estimate_scope,
    contrast_id: item.contrast_id?.toString() ?? '',
    estimate_type: item.estimate_type,
    metric: item.metric,
    estimate_value: String(item.estimate_value),
    standard_error: item.standard_error?.toString() ?? '',
    ci_level: item.ci_level?.toString() ?? '',
    ci_lower: item.ci_lower?.toString() ?? '',
    ci_upper: item.ci_upper?.toString() ?? '',
    p_value: item.p_value?.toString() ?? '',
    n_analysed: item.n_analysed?.toString() ?? '',
    adjustment_status: item.adjustment_status,
    model_specification: item.model_specification ?? '',
    time_or_model_label: item.time_or_model_label ?? '',
    unit: item.unit ?? '',
    scale_direction: item.scale_direction,
    source_reported: item.source_reported,
  })

  useEffect(() => {
    setForm({
      estimate_scope: item.estimate_scope,
      contrast_id: item.contrast_id?.toString() ?? '',
      estimate_type: item.estimate_type,
      metric: item.metric,
      estimate_value: String(item.estimate_value),
      standard_error: item.standard_error?.toString() ?? '',
      ci_level: item.ci_level?.toString() ?? '',
      ci_lower: item.ci_lower?.toString() ?? '',
      ci_upper: item.ci_upper?.toString() ?? '',
      p_value: item.p_value?.toString() ?? '',
      n_analysed: item.n_analysed?.toString() ?? '',
      adjustment_status: item.adjustment_status,
      model_specification: item.model_specification ?? '',
      time_or_model_label: item.time_or_model_label ?? '',
      unit: item.unit ?? '',
      scale_direction: item.scale_direction,
      source_reported: item.source_reported,
    })
  }, [item.effect_estimate_id, item.review_status])

  async function review(reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('effect_estimate').update({
      mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString(),
    }).eq('effect_estimate_id', item.effect_estimate_id)
    if (error) onError(error.message); else await onRefresh()
  }

  async function save() {
    const estimateValue = numericOrNull(form.estimate_value)
    if (estimateValue == null) {
      onError('Effect estimate value must be numeric.')
      return
    }
    const contrastId = form.estimate_scope === 'study_contrast' ? numericOrNull(form.contrast_id) : null
    if (form.estimate_scope === 'study_contrast' && contrastId == null) {
      onError('Study-contrast estimates require a Stage 5 contrast.')
      return
    }
    const payload = {
      estimate_scope: form.estimate_scope,
      contrast_id: contrastId,
      estimate_type: form.estimate_type,
      metric: form.metric,
      estimate_value: estimateValue,
      standard_error: numericOrNull(form.standard_error),
      ci_level: numericOrNull(form.ci_level),
      ci_lower: numericOrNull(form.ci_lower),
      ci_upper: numericOrNull(form.ci_upper),
      p_value: numericOrNull(form.p_value),
      n_analysed: numericOrNull(form.n_analysed),
      adjustment_status: form.adjustment_status,
      model_specification: form.model_specification || null,
      time_or_model_label: form.time_or_model_label || null,
      unit: form.unit || null,
      scale_direction: form.scale_direction,
      source_reported: form.source_reported,
      mapping_source: 'human_review',
      review_status: 'approved',
      updated_at: new Date().toISOString(),
    }
    const { error } = await supabase.from('effect_estimate').update(payload).eq('effect_estimate_id', item.effect_estimate_id)
    if (error) onError(error.message)
    else { setEdit(false); await onRefresh() }
  }

  const contrast = contrasts.find((value) => value.contrast_id === item.contrast_id)
  return <div className="product-card">
    <div className="product-head">
      <div><strong>{item.metric}: {item.estimate_value}</strong><span className="match-pill">{humanize(item.estimate_type)}</span></div>
      <ReviewPills source={item.mapping_source} status={item.review_status} />
    </div>
    {edit ? <div className="edit-stack subedit">
      <div className="two-fields">
        <label><span className="field-label">Estimate scope</span><select className="select-input" value={form.estimate_scope} onChange={(e) => setForm({ ...form, estimate_scope: e.target.value, contrast_id: e.target.value === 'study_contrast' ? form.contrast_id : '' })}>{estimateScopes.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label>
        <label><span className="field-label">Estimate type</span><select className="select-input" value={form.estimate_type} onChange={(e) => setForm({ ...form, estimate_type: e.target.value })}>{estimateTypes.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label>
      </div>
      {form.estimate_scope === 'study_contrast' && <label><span className="field-label">Stage 5 contrast</span><select className="select-input" value={form.contrast_id} onChange={(e) => setForm({ ...form, contrast_id: e.target.value })}><option value="">Select contrast</option>{contrasts.map((value) => <option key={value.contrast_id} value={value.contrast_id}>{value.contrast_label}</option>)}</select></label>}
      <div className="two-fields"><EditInput label="Metric" value={form.metric} onChange={(value) => setForm({ ...form, metric: value })} /><EditInput label="Estimate" type="number" value={form.estimate_value} onChange={(value) => setForm({ ...form, estimate_value: value })} /></div>
      <div className="triple-fields"><EditInput label="SE" type="number" value={form.standard_error} onChange={(value) => setForm({ ...form, standard_error: value })} /><EditInput label="CI lower" type="number" value={form.ci_lower} onChange={(value) => setForm({ ...form, ci_lower: value })} /><EditInput label="CI upper" type="number" value={form.ci_upper} onChange={(value) => setForm({ ...form, ci_upper: value })} /></div>
      <div className="triple-fields"><EditInput label="CI level (0–1)" type="number" value={form.ci_level} onChange={(value) => setForm({ ...form, ci_level: value })} /><EditInput label="p value" type="number" value={form.p_value} onChange={(value) => setForm({ ...form, p_value: value })} /><EditInput label="Analysed N" type="number" value={form.n_analysed} onChange={(value) => setForm({ ...form, n_analysed: value })} /></div>
      <div className="two-fields"><label><span className="field-label">Adjustment</span><select className="select-input" value={form.adjustment_status} onChange={(e) => setForm({ ...form, adjustment_status: e.target.value })}>{adjustmentStatuses.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><label><span className="field-label">Scale direction</span><select className="select-input" value={form.scale_direction} onChange={(e) => setForm({ ...form, scale_direction: e.target.value })}>{scaleDirections.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label></div>
      <EditInput label="Model / adjustment specification" value={form.model_specification} onChange={(value) => setForm({ ...form, model_specification: value })} />
      <div className="two-fields"><EditInput label="Time / model label" value={form.time_or_model_label} onChange={(value) => setForm({ ...form, time_or_model_label: value })} /><EditInput label="Unit" value={form.unit} onChange={(value) => setForm({ ...form, unit: value })} /></div>
      <label className="field-label"><input type="checkbox" checked={form.source_reported} onChange={(e) => setForm({ ...form, source_reported: e.target.checked })} /> Source-reported estimate</label>
      <div className="edit-actions"><button className="primary-button fit" onClick={() => void save()}><Save size={14} /> Save reviewed estimate</button><button className="secondary-button fit" onClick={() => setEdit(false)}>Cancel</button></div>
    </div> : <>
      <div className="product-meta"><span>{humanize(item.estimate_scope)}</span><span>{humanize(item.adjustment_status)}</span><span>{humanize(item.scale_direction)}</span></div>
      <p className="small-copy">CI: {formatCi(item)} · SE: {item.standard_error ?? 'not extracted'} · p: {item.p_value ?? 'not extracted'} · analysed N: {item.n_analysed ?? 'not extracted'}</p>
      <p className="small-copy">Contrast: {contrast?.contrast_label ?? (item.contrast_id == null ? 'Not applicable / not linked' : `Contrast ${item.contrast_id}`)}</p>
      {item.model_specification && <p>{item.model_specification}</p>}
      {item.rationale && <p className="small-copy">{item.rationale}</p>}
      {canEdit && <div className="edit-actions"><button className="text-button" onClick={() => setEdit(true)}><Pencil size={14} /> Correct estimate</button><ReviewButtons onApprove={() => void review('approved')} onReject={() => void review('rejected')} /></div>}
    </>}
  </div>
}

export function Stage6QuantitativeReview({
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
  const [statuses, setStatuses] = useState<Stage6Status[]>([])
  const [effects, setEffects] = useState<EffectEstimate[]>([])
  const [summaries, setSummaries] = useState<ArmOutcomeSummary[]>([])
  const [contrasts, setContrasts] = useState<Contrast[]>([])
  const [arms, setArms] = useState<Arm[]>([])

  const armById = useMemo(() => new Map(arms.map((item) => [item.arm_id, item.arm_label])), [arms])

  useEffect(() => { void load() }, [source.source_id, study?.study_id, outcomeIds.join(',')])

  async function load() {
    if (!study || !outcomeIds.length) {
      setStatuses([]); setEffects([]); setSummaries([]); setContrasts([]); setArms([])
      return
    }
    setLoading(true)
    onError(null)
    const [statusRows, effectRows, summaryRows, contrastRows, armRows] = await Promise.all([
      supabase.from('outcome_stage6_status').select('*').in('outcome_id', outcomeIds).order('outcome_id'),
      supabase.from('effect_estimate').select('*').in('outcome_id', outcomeIds).order('effect_estimate_id'),
      supabase.from('arm_outcome_summary').select('*').in('outcome_id', outcomeIds).order('arm_outcome_summary_id'),
      supabase.from('study_contrast').select('contrast_id,contrast_label,contrast_type').eq('study_id', study.study_id).order('contrast_id'),
      supabase.from('study_arm').select('arm_id,arm_label').eq('study_id', study.study_id).order('arm_id'),
    ])
    const firstError = [statusRows, effectRows, summaryRows, contrastRows, armRows].find((result) => result.error)?.error
    if (firstError) onError(firstError.message)
    else {
      setStatuses((statusRows.data ?? []) as Stage6Status[])
      setEffects((effectRows.data ?? []) as EffectEstimate[])
      setSummaries((summaryRows.data ?? []) as ArmOutcomeSummary[])
      setContrasts((contrastRows.data ?? []) as Contrast[])
      setArms((armRows.data ?? []) as Arm[])
    }
    setLoading(false)
  }

  async function reviewStatus(outcomeId: number, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('outcome_stage6_status').update({ mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }).eq('outcome_id', outcomeId)
    if (error) onError(error.message); else await load()
  }

  async function correctStatus(outcomeId: number, value: string) {
    const { error } = await supabase.from('outcome_stage6_status').update({ quantitative_extraction_status: value, mapping_source: 'human_review', review_status: 'approved', updated_at: new Date().toISOString() }).eq('outcome_id', outcomeId)
    if (error) onError(error.message); else await load()
  }

  async function reviewSummary(summaryId: number, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('arm_outcome_summary').update({ mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }).eq('arm_outcome_summary_id', summaryId)
    if (error) onError(error.message); else await load()
  }

  return <DetailSection title="Quantitative effects & uncertainty" icon={<Activity size={17} />}>
    <div className="record-note">Stage 6 makes quantitative estimates first-class records. Absence of an extracted number is not a null effect. Comparative estimates link to Stage 5 contrasts when applicable; pooled synthesis estimates may remain unlinked until Stage 8.</div>
    {loading && <div className="small-copy" style={{ marginTop: 12 }}><RefreshCw className="spin" size={14} /> Loading Stage 6 quantitative structure…</div>}
    {!study && <EmptyLine>No normalized study row.</EmptyLine>}
    {study && outcomes.length === 0 && <EmptyLine>No normalized outcome rows.</EmptyLine>}

    {outcomes.map((outcome) => {
      const status = statuses.find((item) => item.outcome_id === outcome.outcome_id)
      const outcomeEffects = effects.filter((item) => item.outcome_id === outcome.outcome_id)
      const outcomeSummaries = summaries.filter((item) => item.outcome_id === outcome.outcome_id)
      return <div className="product-card" key={outcome.outcome_id} style={{ marginTop: 14 }}>
        <div className="product-head"><strong>{outcome.outcome_name}</strong>{status && <ReviewPills source={status.mapping_source} status={status.review_status} />}</div>
        {status ? <>
          <div className="product-meta"><span>{humanize(status.quantitative_extraction_status)}</span><span>{outcomeEffects.length} effect estimate(s)</span><span>{outcomeSummaries.length} arm summary row(s)</span></div>
          {status.notes && <p className="small-copy">{status.notes}</p>}
          {canEdit && <div className="edit-actions"><label><span className="field-label">Extraction status</span><select className="select-input" value={status.quantitative_extraction_status} onChange={(e) => void correctStatus(outcome.outcome_id, e.target.value)}>{extractionStatuses.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><ReviewButtons onApprove={() => void reviewStatus(outcome.outcome_id, 'approved')} onReject={() => void reviewStatus(outcome.outcome_id, 'rejected')} /></div>}
        </> : <EmptyLine>No Stage 6 extraction-status row.</EmptyLine>}

        {outcomeEffects.length > 0 && <div className="stack-list" style={{ marginTop: 12 }}>{outcomeEffects.map((item) => <EffectCard key={item.effect_estimate_id} item={item} contrasts={contrasts} canEdit={canEdit} onRefresh={load} onError={onError} />)}</div>}

        {outcomeSummaries.length > 0 && <div style={{ marginTop: 12 }}><span className="field-label">Raw arm/group summaries</span><div className="stack-list">{outcomeSummaries.map((item) => <div className="record-note" key={item.arm_outcome_summary_id}><strong>{armById.get(item.arm_id) ?? `Arm ${item.arm_id}`}</strong> · {item.summary_key} · N {item.n_analysed ?? 'not extracted'} · mean {item.mean ?? '—'} · SD {item.sd ?? '—'} · proportion {item.proportion ?? '—'} <ReviewPills source={item.mapping_source} status={item.review_status} />{canEdit && <ReviewButtons onApprove={() => void reviewSummary(item.arm_outcome_summary_id, 'approved')} onReject={() => void reviewSummary(item.arm_outcome_summary_id, 'rejected')} />}</div>)}</div></div>}
      </div>
    })}
  </DetailSection>
}
