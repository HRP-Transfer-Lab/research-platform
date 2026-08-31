import { useEffect, useMemo, useState } from 'react'
import { Check, Layers3, Plus, RefreshCw, Save, X } from 'lucide-react'
import { supabase } from './lib/supabase'
import { DetailSection, EditInput, EmptyLine } from './WorkbenchUi'
import { humanize, type EvidenceSource, type RegistryData } from './workbench'

type Stage8Status = {
  scope_key: string
  curation_status: string
  mapping_source: string
  review_status: string
  notes: string | null
}

type Proposition = {
  proposition_id: number
  proposition_key: string
  label: string
  intervention_or_exposure: string
  comparator_scope: string | null
  population_scope: string
  context_scope: string | null
  target_or_outcome_scope: string
  timeframe_scope: string | null
  route_scope: string[]
  proposition_text: string
  status: string
  mapping_source: string
  review_status: string
}

type Contribution = {
  contribution_id: number
  proposition_id: number
  contribution_key: string
  source_id: string | null
  study_id: number | null
  outcome_id: number | null
  contrast_id: number | null
  effect_estimate_id: number | null
  contribution_role: string
  result_direction: string | null
  inclusion_status: string
  inclusion_reason: string | null
  mapping_source: string
  review_status: string
}

type BodySynthesis = {
  body_synthesis_id: number
  synthesis_key: string
  proposition_id: number
  title: string
  synthesis_kind: string
  method_summary: string
  search_or_selection_basis: string | null
  status: string
  version: string
  mapping_source: string
  review_status: string
}

type SynthesisOutcome = {
  synthesis_outcome_id: number
  body_synthesis_id: number
  proposition_id: number
  outcome_key: string
  outcome_label: string
  conclusion_direction: string
  conclusion_summary: string
  estimate_type: string | null
  metric: string | null
  pooled_estimate: number | null
  ci_level: number | null
  ci_lower: number | null
  ci_upper: number | null
  included_study_count: number | null
  included_result_count: number | null
  status: string
  mapping_source: string
  review_status: string
}

type Certainty = {
  body_certainty_assessment_id: number
  synthesis_outcome_id: number
  framework_key: string
  framework_version: string | null
  certainty_judgement: string
  assessment_status: string
  basis: string
  mapping_source: string
  review_status: string
}

type BodyMaturity = {
  body_maturity_assessment_id: number
  synthesis_outcome_id: number
  scale_version: string
  maturity_level: number
  assessment_status: string
  basis: string
  direct_study_count: number | null
  genuine_replication_count: number | null
  independent_replication_count: number | null
  replication_basis: string | null
  consistency_pattern: string | null
  unresolved_boundaries: string | null
  mapping_source: string
  review_status: string
}

type BodyClaim = {
  body_claim_id: number
  claim_key: string
  proposition_id: number
  synthesis_outcome_id: number
  product: string | null
  claim_text: string
  required_caveat: string | null
  population_scope: string
  context_scope: string | null
  route_scope: string[]
  certainty_summary: string | null
  status: string
  version: string
  mapping_source: string
  review_status: string
}

type Framework = { framework_key: string; label: string; subject_kind: string; active: boolean }
type MaturityDefinition = { maturity_level: number; code: string; label: string; short_label: string }
type Contrast = { contrast_id: number; contrast_label: string }
type Effect = { effect_estimate_id: number; outcome_id: number; contrast_id: number | null; estimate_scope: string; metric: string; estimate_value: number }

const curationStatuses = ['not_yet_curated', 'curation_in_progress', 'partially_curated', 'reviewed_complete']
const contributionRoles = ['direct_support', 'direct_null', 'direct_harm', 'boundary_condition', 'mechanism_support', 'measurement_support', 'implementation_support', 'synthesis_support', 'contradictory', 'contextual', 'other']
const directions = ['supportive', 'null', 'harmful', 'mixed', 'uncertain', 'not_applicable']
const synthesisKinds = ['systematic_review_meta_analysis', 'systematic_review_narrative', 'rapid_review', 'scoping_review', 'structured_internal_synthesis', 'living_synthesis', 'other']
const consistencyPatterns = ['consistent', 'mixed_but_convergent', 'mixed', 'contradictory', 'unclear', 'not_assessed']

function ReviewPills({ source, status }: { source: string; status: string }) {
  return <span className="detail-meta-row"><span className="status-pill">{humanize(source)}</span><span className="status-pill">{humanize(status)}</span></span>
}

function ReviewButtons({ onApprove, onReject, approveTitle = 'Approve' }: { onApprove: () => void; onReject: () => void; approveTitle?: string }) {
  return <span className="detail-meta-row"><button className="icon-button mini" title={approveTitle} onClick={onApprove}><Check size={13} /></button><button className="icon-button mini" title="Reject" onClick={onReject}><X size={13} /></button></span>
}

function num(value: string): number | null {
  if (!value.trim()) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function splitList(value: string) {
  return value.split(',').map((item) => item.trim()).filter(Boolean)
}

export function Stage8BodyEvidenceReview({ source, data, canEdit, onError }: { source: EvidenceSource; data: RegistryData; canEdit: boolean; onError: (value: string | null) => void }) {
  const study = data.studies.find((item) => item.source_id === source.source_id)
  const sourceOutcomes = data.outcomes.filter((item) => item.study_id === study?.study_id)

  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<Stage8Status | null>(null)
  const [propositions, setPropositions] = useState<Proposition[]>([])
  const [contributions, setContributions] = useState<Contribution[]>([])
  const [syntheses, setSyntheses] = useState<BodySynthesis[]>([])
  const [synthesisOutcomes, setSynthesisOutcomes] = useState<SynthesisOutcome[]>([])
  const [certainties, setCertainties] = useState<Certainty[]>([])
  const [maturities, setMaturities] = useState<BodyMaturity[]>([])
  const [claims, setClaims] = useState<BodyClaim[]>([])
  const [frameworks, setFrameworks] = useState<Framework[]>([])
  const [maturityDefinitions, setMaturityDefinitions] = useState<MaturityDefinition[]>([])
  const [contrasts, setContrasts] = useState<Contrast[]>([])
  const [effects, setEffects] = useState<Effect[]>([])
  const [showPropositionForm, setShowPropositionForm] = useState(false)
  const [contributionFormProposition, setContributionFormProposition] = useState<number | null>(null)
  const [synthesisFormProposition, setSynthesisFormProposition] = useState<number | null>(null)
  const [outcomeFormSynthesis, setOutcomeFormSynthesis] = useState<number | null>(null)
  const [certaintyFormOutcome, setCertaintyFormOutcome] = useState<number | null>(null)
  const [maturityFormOutcome, setMaturityFormOutcome] = useState<number | null>(null)
  const [claimFormOutcome, setClaimFormOutcome] = useState<number | null>(null)

  useEffect(() => { void load() }, [source.source_id, study?.study_id])

  async function load() {
    setLoading(true)
    onError(null)
    const [statusRow, sourceContributionRows, frameworkRows, maturityRows, contrastRows, effectRows] = await Promise.all([
      supabase.from('body_evidence_stage8_status').select('*').eq('scope_key', 'seed_body_curation').maybeSingle(),
      supabase.from('proposition_evidence_contribution').select('*').eq('source_id', source.source_id).order('contribution_id'),
      supabase.from('assessment_framework_definition').select('framework_key,label,subject_kind,active').order('framework_key'),
      supabase.from('evidence_maturity_level_definition').select('maturity_level,code,label,short_label').eq('scale_version', 'hrp-eml-v1').order('maturity_level'),
      study ? supabase.from('study_contrast').select('contrast_id,contrast_label').eq('study_id', study.study_id).order('contrast_id') : Promise.resolve({ data: [], error: null } as any),
      study ? supabase.from('effect_estimate').select('effect_estimate_id,outcome_id,contrast_id,estimate_scope,metric,estimate_value').in('outcome_id', sourceOutcomes.map((item) => item.outcome_id).length ? sourceOutcomes.map((item) => item.outcome_id) : [-1]).order('effect_estimate_id') : Promise.resolve({ data: [], error: null } as any),
    ])
    const firstError = [statusRow, sourceContributionRows, frameworkRows, maturityRows, contrastRows, effectRows].find((result) => result.error)?.error
    if (firstError) { onError(firstError.message); setLoading(false); return }

    const sourceContribs = (sourceContributionRows.data ?? []) as Contribution[]
    const propositionIds = [...new Set(sourceContribs.map((item) => item.proposition_id))]
    let propositionRows: any = { data: [], error: null }
    let allContributionRows: any = { data: [], error: null }
    let synthesisRows: any = { data: [], error: null }
    let outcomeRows: any = { data: [], error: null }
    let certaintyRows: any = { data: [], error: null }
    let bodyMaturityRows: any = { data: [], error: null }
    let claimRows: any = { data: [], error: null }

    if (propositionIds.length) {
      ;[propositionRows, allContributionRows, synthesisRows, claimRows] = await Promise.all([
        supabase.from('evidence_proposition').select('*').in('proposition_id', propositionIds).order('proposition_id'),
        supabase.from('proposition_evidence_contribution').select('*').in('proposition_id', propositionIds).order('contribution_id'),
        supabase.from('body_evidence_synthesis').select('*').in('proposition_id', propositionIds).order('body_synthesis_id'),
        supabase.from('body_approved_claim').select('*').in('proposition_id', propositionIds).order('body_claim_id'),
      ])
      const bodyError = [propositionRows, allContributionRows, synthesisRows, claimRows].find((result) => result.error)?.error
      if (bodyError) { onError(bodyError.message); setLoading(false); return }
      const synthesisIds = (synthesisRows.data ?? []).map((item: any) => item.body_synthesis_id)
      if (synthesisIds.length) {
        outcomeRows = await supabase.from('synthesis_outcome').select('*').in('body_synthesis_id', synthesisIds).order('synthesis_outcome_id')
        if (outcomeRows.error) { onError(outcomeRows.error.message); setLoading(false); return }
        const synthesisOutcomeIds = (outcomeRows.data ?? []).map((item: any) => item.synthesis_outcome_id)
        if (synthesisOutcomeIds.length) {
          ;[certaintyRows, bodyMaturityRows] = await Promise.all([
            supabase.from('body_certainty_assessment').select('*').in('synthesis_outcome_id', synthesisOutcomeIds).order('body_certainty_assessment_id'),
            supabase.from('body_maturity_assessment').select('*').in('synthesis_outcome_id', synthesisOutcomeIds).order('body_maturity_assessment_id'),
          ])
          const outcomeError = [certaintyRows, bodyMaturityRows].find((result) => result.error)?.error
          if (outcomeError) { onError(outcomeError.message); setLoading(false); return }
        }
      }
    }

    setStatus((statusRow.data ?? null) as Stage8Status | null)
    setPropositions((propositionRows.data ?? []) as Proposition[])
    setContributions((allContributionRows.data ?? sourceContribs) as Contribution[])
    setSyntheses((synthesisRows.data ?? []) as BodySynthesis[])
    setSynthesisOutcomes((outcomeRows.data ?? []) as SynthesisOutcome[])
    setCertainties((certaintyRows.data ?? []) as Certainty[])
    setMaturities((bodyMaturityRows.data ?? []) as BodyMaturity[])
    setClaims((claimRows.data ?? []) as BodyClaim[])
    setFrameworks((frameworkRows.data ?? []) as Framework[])
    setMaturityDefinitions((maturityRows.data ?? []) as MaturityDefinition[])
    setContrasts((contrastRows.data ?? []) as Contrast[])
    setEffects((effectRows.data ?? []) as Effect[])
    setLoading(false)
  }

  async function updateCurationStatus(value: string) {
    const { error } = await supabase.from('body_evidence_stage8_status').update({ curation_status: value, mapping_source: 'human_review', review_status: 'approved', updated_at: new Date().toISOString() }).eq('scope_key', 'seed_body_curation')
    if (error) onError(error.message); else await load()
  }

  async function reviewSimple(table: string, idField: string, id: number, reviewStatus: 'approved' | 'rejected', statusField?: string) {
    const payload: Record<string, any> = { mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }
    if (reviewStatus === 'approved' && statusField) payload[statusField] = 'approved'
    const { error } = await supabase.from(table).update(payload).eq(idField, id)
    if (error) onError(error.message); else await load()
  }

  async function reviewCertainty(id: number, reviewStatus: 'approved' | 'rejected') {
    const payload = reviewStatus === 'approved'
      ? { mapping_source: 'human_review', review_status: 'approved', assessment_status: 'reviewed_complete', updated_at: new Date().toISOString() }
      : { mapping_source: 'human_review', review_status: 'rejected', updated_at: new Date().toISOString() }
    const { error } = await supabase.from('body_certainty_assessment').update(payload).eq('body_certainty_assessment_id', id)
    if (error) onError(error.message); else await load()
  }

  async function reviewMaturity(id: number, reviewStatus: 'approved' | 'rejected') {
    const payload = reviewStatus === 'approved'
      ? { mapping_source: 'human_review', review_status: 'approved', assessment_status: 'approved', updated_at: new Date().toISOString() }
      : { mapping_source: 'human_review', review_status: 'rejected', updated_at: new Date().toISOString() }
    const { error } = await supabase.from('body_maturity_assessment').update(payload).eq('body_maturity_assessment_id', id)
    if (error) onError(error.message); else await load()
  }

  async function approveClaim(id: number) {
    const { error } = await supabase.from('body_approved_claim').update({ mapping_source: 'human_review', review_status: 'approved', status: 'approved_internal', updated_at: new Date().toISOString() }).eq('body_claim_id', id)
    if (error) onError(error.message); else await load()
  }

  const contributionSourceName = useMemo(() => new Map(data.sources.map((item) => [item.source_id, item.title])), [data.sources])
  const outcomeById = useMemo(() => new Map(data.outcomes.map((item) => [item.outcome_id, item])), [data.outcomes])
  const contrastById = useMemo(() => new Map(contrasts.map((item) => [item.contrast_id, item])), [contrasts])
  const effectById = useMemo(() => new Map(effects.map((item) => [item.effect_estimate_id, item])), [effects])
  const maturityByLevel = useMemo(() => new Map(maturityDefinitions.map((item) => [item.maturity_level, item])), [maturityDefinitions])
  const gradeFramework = frameworks.find((item) => item.framework_key === 'grade' && item.active)

  return <DetailSection title="Body evidence: propositions, synthesis, certainty & claims" icon={<Layers3 size={17} />}>
    <div className="record-note">Stage 8 is cross-source. This view shows body-level propositions that include the selected source. Source EML remains a record-contribution maturity signal; body EML is assessed only on a reviewed synthesis outcome. GRADE != EML, certainty != effect magnitude, and effect direction != maturity.</div>
    {loading && <div className="small-copy" style={{ marginTop: 12 }}><RefreshCw className="spin" size={14} /> Loading Stage 8 body evidence…</div>}

    {status && <div className="product-card" style={{ marginTop: 14 }}>
      <div className="product-head"><strong>Body curation programme state</strong><ReviewPills source={status.mapping_source} status={status.review_status} /></div>
      <div className="product-meta"><span>{humanize(status.curation_status)}</span></div>
      {status.notes && <p className="small-copy">{status.notes}</p>}
      {canEdit && <label><span className="field-label">Curation state</span><select className="select-input" value={status.curation_status} onChange={(e) => void updateCurationStatus(e.target.value)}>{curationStatuses.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label>}
    </div>}

    <div style={{ marginTop: 18 }}>
      <div className="product-head"><span className="field-label">Propositions involving this source ({propositions.length})</span>{canEdit && <button className="text-button" onClick={() => setShowPropositionForm((value) => !value)}><Plus size={14} /> Create proposition</button>}</div>
      {showPropositionForm && <PropositionForm source={source} studyId={study?.study_id ?? null} onDone={async () => { setShowPropositionForm(false); await load() }} onError={onError} />}
      {!propositions.length && <EmptyLine>No curated proposition currently includes this source. The seed intentionally begins with zero body-level propositions.</EmptyLine>}
    </div>

    <div className="stack-list" style={{ marginTop: 14 }}>{propositions.map((proposition) => {
      const propositionContributions = contributions.filter((item) => item.proposition_id === proposition.proposition_id)
      const propositionSyntheses = syntheses.filter((item) => item.proposition_id === proposition.proposition_id)
      return <div className="product-card" key={proposition.proposition_id}>
        <div className="product-head"><div><strong>{proposition.label}</strong><span className="match-pill">{humanize(proposition.status)}</span></div><ReviewPills source={proposition.mapping_source} status={proposition.review_status} /></div>
        <p>{proposition.proposition_text}</p>
        <p className="small-copy"><strong>Scope:</strong> {proposition.population_scope} · {proposition.target_or_outcome_scope}{proposition.timeframe_scope ? ` · ${proposition.timeframe_scope}` : ''}</p>
        <p className="small-copy"><strong>Intervention/exposure:</strong> {proposition.intervention_or_exposure}{proposition.comparator_scope ? ` · comparator: ${proposition.comparator_scope}` : ''}</p>
        {canEdit && <ReviewButtons onApprove={() => void reviewSimple('evidence_proposition', 'proposition_id', proposition.proposition_id, 'approved', 'status')} onReject={() => void reviewSimple('evidence_proposition', 'proposition_id', proposition.proposition_id, 'rejected')} />}

        <div style={{ marginTop: 14 }}>
          <div className="product-head"><span className="field-label">Evidence contributions ({propositionContributions.length})</span>{canEdit && <button className="text-button" onClick={() => setContributionFormProposition(contributionFormProposition === proposition.proposition_id ? null : proposition.proposition_id)}><Plus size={14} /> Add this source</button>}</div>
          {contributionFormProposition === proposition.proposition_id && <ContributionForm propositionId={proposition.proposition_id} source={source} studyId={study?.study_id ?? null} outcomes={sourceOutcomes} contrasts={contrasts} effects={effects} onDone={async () => { setContributionFormProposition(null); await load() }} onError={onError} />}
          <div className="stack-list">{propositionContributions.map((item) => <div className="record-note" key={item.contribution_id}>
            <strong>{contributionSourceName.get(item.source_id ?? '') ?? item.source_id ?? 'Source version contribution'}</strong> · {humanize(item.contribution_role)} · {humanize(item.inclusion_status)} <ReviewPills source={item.mapping_source} status={item.review_status} />
            {item.outcome_id != null && <p className="small-copy">Outcome: {outcomeById.get(item.outcome_id)?.outcome_name ?? item.outcome_id}{item.contrast_id != null ? ` · Contrast: ${contrastById.get(item.contrast_id)?.contrast_label ?? item.contrast_id}` : ''}{item.effect_estimate_id != null ? ` · Effect: ${effectById.get(item.effect_estimate_id)?.metric ?? item.effect_estimate_id}` : ''}</p>}
            {item.inclusion_reason && <p className="small-copy">{item.inclusion_reason}</p>}
            {canEdit && <ReviewButtons onApprove={() => void reviewSimple('proposition_evidence_contribution', 'contribution_id', item.contribution_id, 'approved')} onReject={() => void reviewSimple('proposition_evidence_contribution', 'contribution_id', item.contribution_id, 'rejected')} />}
          </div>)}</div>
        </div>

        <div style={{ marginTop: 16 }}>
          <div className="product-head"><span className="field-label">Body syntheses ({propositionSyntheses.length})</span>{canEdit && <button className="text-button" onClick={() => setSynthesisFormProposition(synthesisFormProposition === proposition.proposition_id ? null : proposition.proposition_id)}><Plus size={14} /> Add synthesis</button>}</div>
          {synthesisFormProposition === proposition.proposition_id && <SynthesisForm propositionId={proposition.proposition_id} onDone={async () => { setSynthesisFormProposition(null); await load() }} onError={onError} />}
          <div className="stack-list">{propositionSyntheses.map((synthesis) => {
            const outcomes = synthesisOutcomes.filter((item) => item.body_synthesis_id === synthesis.body_synthesis_id)
            return <div className="product-card" key={synthesis.body_synthesis_id}>
              <div className="product-head"><div><strong>{synthesis.title}</strong><span className="match-pill">{humanize(synthesis.synthesis_kind)}</span></div><ReviewPills source={synthesis.mapping_source} status={synthesis.review_status} /></div>
              <p>{synthesis.method_summary}</p>
              <div className="product-meta"><span>Version {synthesis.version}</span><span>{humanize(synthesis.status)}</span></div>
              {canEdit && <ReviewButtons onApprove={() => void reviewSimple('body_evidence_synthesis', 'body_synthesis_id', synthesis.body_synthesis_id, 'approved', 'status')} onReject={() => void reviewSimple('body_evidence_synthesis', 'body_synthesis_id', synthesis.body_synthesis_id, 'rejected')} />}

              <div style={{ marginTop: 12 }}>
                <div className="product-head"><span className="field-label">Synthesis outcomes ({outcomes.length})</span>{canEdit && <button className="text-button" onClick={() => setOutcomeFormSynthesis(outcomeFormSynthesis === synthesis.body_synthesis_id ? null : synthesis.body_synthesis_id)}><Plus size={14} /> Add outcome</button>}</div>
                {outcomeFormSynthesis === synthesis.body_synthesis_id && <SynthesisOutcomeForm synthesis={synthesis} onDone={async () => { setOutcomeFormSynthesis(null); await load() }} onError={onError} />}
                <div className="stack-list">{outcomes.map((outcome) => {
                  const outcomeCertainty = certainties.find((item) => item.synthesis_outcome_id === outcome.synthesis_outcome_id)
                  const outcomeMaturity = maturities.find((item) => item.synthesis_outcome_id === outcome.synthesis_outcome_id)
                  const outcomeClaims = claims.filter((item) => item.synthesis_outcome_id === outcome.synthesis_outcome_id)
                  return <div className="outcome-card" key={outcome.synthesis_outcome_id}>
                    <div className="outcome-head"><div><strong>{outcome.outcome_label}</strong><span className="rung-pill">{humanize(outcome.conclusion_direction)}</span></div><ReviewPills source={outcome.mapping_source} status={outcome.review_status} /></div>
                    <p>{outcome.conclusion_summary}</p>
                    {outcome.pooled_estimate != null && <div className="effect-line">{outcome.metric ?? outcome.estimate_type ?? 'Pooled estimate'}: <strong>{outcome.pooled_estimate}</strong>{outcome.ci_lower != null && outcome.ci_upper != null ? ` (${outcome.ci_lower} to ${outcome.ci_upper})` : ''}</div>}
                    <p className="small-copy">Included studies: {outcome.included_study_count ?? 'not recorded'} · results: {outcome.included_result_count ?? 'not recorded'}</p>
                    {canEdit && <ReviewButtons onApprove={() => void reviewSimple('synthesis_outcome', 'synthesis_outcome_id', outcome.synthesis_outcome_id, 'approved', 'status')} onReject={() => void reviewSimple('synthesis_outcome', 'synthesis_outcome_id', outcome.synthesis_outcome_id, 'rejected')} />}

                    <div className="stack-list" style={{ marginTop: 10 }}>
                      <div className="record-note"><strong>Body certainty</strong> · {outcomeCertainty ? `${humanize(outcomeCertainty.framework_key)}: ${humanize(outcomeCertainty.certainty_judgement)}` : 'not assessed'} {outcomeCertainty && <ReviewPills source={outcomeCertainty.mapping_source} status={outcomeCertainty.review_status} />}{outcomeCertainty?.basis && <p className="small-copy">{outcomeCertainty.basis}</p>}{canEdit && !outcomeCertainty && <button className="text-button" onClick={() => setCertaintyFormOutcome(outcome.synthesis_outcome_id)}><Plus size={14} /> Add body certainty</button>}{certaintyFormOutcome === outcome.synthesis_outcome_id && <CertaintyForm outcomeId={outcome.synthesis_outcome_id} gradeAvailable={Boolean(gradeFramework)} onDone={async () => { setCertaintyFormOutcome(null); await load() }} onError={onError} />}{canEdit && outcomeCertainty && <ReviewButtons onApprove={() => void reviewCertainty(outcomeCertainty.body_certainty_assessment_id, 'approved')} onReject={() => void reviewCertainty(outcomeCertainty.body_certainty_assessment_id, 'rejected')} />}</div>

                      <div className="record-note"><strong>Body EML</strong> · {outcomeMaturity ? `${maturityByLevel.get(outcomeMaturity.maturity_level)?.code ?? `EML${outcomeMaturity.maturity_level}`} — ${maturityByLevel.get(outcomeMaturity.maturity_level)?.short_label ?? ''}` : 'not assessed'} {outcomeMaturity && <ReviewPills source={outcomeMaturity.mapping_source} status={outcomeMaturity.review_status} />}{outcomeMaturity?.basis && <p className="small-copy">{outcomeMaturity.basis}</p>}{canEdit && !outcomeMaturity && <button className="text-button" onClick={() => setMaturityFormOutcome(outcome.synthesis_outcome_id)}><Plus size={14} /> Add body EML</button>}{maturityFormOutcome === outcome.synthesis_outcome_id && <MaturityForm outcomeId={outcome.synthesis_outcome_id} maturityDefinitions={maturityDefinitions} onDone={async () => { setMaturityFormOutcome(null); await load() }} onError={onError} />}{canEdit && outcomeMaturity && <ReviewButtons onApprove={() => void reviewMaturity(outcomeMaturity.body_maturity_assessment_id, 'approved')} onReject={() => void reviewMaturity(outcomeMaturity.body_maturity_assessment_id, 'rejected')} />}</div>

                      <div className="record-note"><div className="product-head"><strong>Governed claims ({outcomeClaims.length})</strong>{canEdit && <button className="text-button" onClick={() => setClaimFormOutcome(claimFormOutcome === outcome.synthesis_outcome_id ? null : outcome.synthesis_outcome_id)}><Plus size={14} /> Draft claim</button>}</div>{claimFormOutcome === outcome.synthesis_outcome_id && <ClaimForm proposition={proposition} outcomeId={outcome.synthesis_outcome_id} onDone={async () => { setClaimFormOutcome(null); await load() }} onError={onError} />}{outcomeClaims.map((claim) => <div className="quality-row" key={claim.body_claim_id}><div><strong>{claim.claim_text}</strong><span>{humanize(claim.status)}</span></div>{claim.required_caveat && <p className="small-copy">Caveat: {claim.required_caveat}</p>}{canEdit && claim.status === 'draft' && <ReviewButtons approveTitle="Approve internally" onApprove={() => void approveClaim(claim.body_claim_id)} onReject={() => void reviewSimple('body_approved_claim', 'body_claim_id', claim.body_claim_id, 'rejected')} />}</div>)}</div>
                    </div>
                  </div>
                })}</div>
              </div>
            </div>
          })}</div>
        </div>
      </div>
    })}</div>
  </DetailSection>
}

function PropositionForm({ source, studyId, onDone, onError }: { source: EvidenceSource; studyId: number | null; onDone: () => Promise<void>; onError: (value: string | null) => void }) {
  const [form, setForm] = useState({ proposition_key: '', label: '', intervention_or_exposure: '', comparator_scope: '', population_scope: '', context_scope: '', target_or_outcome_scope: '', timeframe_scope: '', route_scope: '', proposition_text: '', contribution_key: '', contribution_role: 'contextual', result_direction: 'uncertain', inclusion_reason: '' })
  async function save() {
    if (!form.proposition_key || !form.label || !form.intervention_or_exposure || !form.population_scope || !form.target_or_outcome_scope || !form.proposition_text || !form.contribution_key) { onError('Proposition key, label, intervention/exposure, population, target/outcome, proposition text and contribution key are required.'); return }
    const { data: proposition, error } = await supabase.from('evidence_proposition').insert({ proposition_key: form.proposition_key, label: form.label, intervention_or_exposure: form.intervention_or_exposure, comparator_scope: form.comparator_scope || null, population_scope: form.population_scope, context_scope: form.context_scope || null, target_or_outcome_scope: form.target_or_outcome_scope, timeframe_scope: form.timeframe_scope || null, route_scope: splitList(form.route_scope), proposition_text: form.proposition_text, status: 'draft', mapping_source: 'human_review', review_status: 'proposed' }).select('proposition_id').single()
    if (error || !proposition) { onError(error?.message ?? 'Unable to create proposition.'); return }
    const contribution = await supabase.from('proposition_evidence_contribution').insert({ proposition_id: proposition.proposition_id, contribution_key: form.contribution_key, source_id: source.source_id, study_id: studyId, contribution_role: form.contribution_role, result_direction: form.result_direction, inclusion_status: 'candidate', inclusion_reason: form.inclusion_reason || null, mapping_source: 'human_review', review_status: 'proposed' })
    if (contribution.error) onError(contribution.error.message); else await onDone()
  }
  return <div className="quality-form"><div className="two-fields"><EditInput label="Proposition key" value={form.proposition_key} onChange={(value) => setForm({ ...form, proposition_key: value })} /><EditInput label="Label" value={form.label} onChange={(value) => setForm({ ...form, label: value })} /></div><EditInput label="Intervention / exposure" value={form.intervention_or_exposure} onChange={(value) => setForm({ ...form, intervention_or_exposure: value })} /><div className="two-fields"><EditInput label="Population scope" value={form.population_scope} onChange={(value) => setForm({ ...form, population_scope: value })} /><EditInput label="Comparator scope" value={form.comparator_scope} onChange={(value) => setForm({ ...form, comparator_scope: value })} /></div><div className="two-fields"><EditInput label="Target / outcome scope" value={form.target_or_outcome_scope} onChange={(value) => setForm({ ...form, target_or_outcome_scope: value })} /><EditInput label="Timeframe" value={form.timeframe_scope} onChange={(value) => setForm({ ...form, timeframe_scope: value })} /></div><div className="two-fields"><EditInput label="Context scope" value={form.context_scope} onChange={(value) => setForm({ ...form, context_scope: value })} /><EditInput label="Route scope (comma separated)" value={form.route_scope} onChange={(value) => setForm({ ...form, route_scope: value })} /></div><label className="field-label">Proposition text</label><textarea className="textarea" rows={3} value={form.proposition_text} onChange={(e) => setForm({ ...form, proposition_text: e.target.value })} /><div className="two-fields"><EditInput label="Initial contribution key" value={form.contribution_key} onChange={(value) => setForm({ ...form, contribution_key: value })} /><label><span className="field-label">Initial contribution role</span><select className="select-input" value={form.contribution_role} onChange={(e) => setForm({ ...form, contribution_role: e.target.value })}>{contributionRoles.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label></div><EditInput label="Inclusion reason" value={form.inclusion_reason} onChange={(value) => setForm({ ...form, inclusion_reason: value })} /><button className="primary-button fit" onClick={() => void save()}><Save size={14} /> Create proposition + source contribution</button></div>
}

function ContributionForm({ propositionId, source, studyId, outcomes, contrasts, effects, onDone, onError }: { propositionId: number; source: EvidenceSource; studyId: number | null; outcomes: any[]; contrasts: Contrast[]; effects: Effect[]; onDone: () => Promise<void>; onError: (value: string | null) => void }) {
  const [form, setForm] = useState({ contribution_key: '', outcome_id: '', contrast_id: '', effect_estimate_id: '', contribution_role: 'contextual', result_direction: 'uncertain', inclusion_status: 'candidate', inclusion_reason: '' })
  const selectedOutcome = num(form.outcome_id)
  const relevantEffects = effects.filter((item) => selectedOutcome == null || item.outcome_id === selectedOutcome)
  async function save() {
    if (!form.contribution_key) { onError('Contribution key is required.'); return }
    const effectId = num(form.effect_estimate_id)
    const effect = relevantEffects.find((item) => item.effect_estimate_id === effectId)
    const { error } = await supabase.from('proposition_evidence_contribution').insert({ proposition_id: propositionId, contribution_key: form.contribution_key, source_id: source.source_id, study_id: studyId, outcome_id: selectedOutcome, contrast_id: effect?.contrast_id ?? num(form.contrast_id), effect_estimate_id: effectId, contribution_role: form.contribution_role, result_direction: form.result_direction, inclusion_status: form.inclusion_status, inclusion_reason: form.inclusion_reason || null, mapping_source: 'human_review', review_status: 'proposed' })
    if (error) onError(error.message); else await onDone()
  }
  return <div className="quality-form"><EditInput label="Contribution key" value={form.contribution_key} onChange={(value) => setForm({ ...form, contribution_key: value })} /><div className="two-fields"><label><span className="field-label">Outcome (optional)</span><select className="select-input" value={form.outcome_id} onChange={(e) => setForm({ ...form, outcome_id: e.target.value, effect_estimate_id: '', contrast_id: '' })}><option value="">Source-level contribution</option>{outcomes.map((item) => <option key={item.outcome_id} value={item.outcome_id}>{item.outcome_name}</option>)}</select></label><label><span className="field-label">Contrast (optional)</span><select className="select-input" value={form.contrast_id} onChange={(e) => setForm({ ...form, contrast_id: e.target.value })}><option value="">No contrast</option>{contrasts.map((item) => <option key={item.contrast_id} value={item.contrast_id}>{item.contrast_label}</option>)}</select></label></div><label><span className="field-label">Effect estimate (optional)</span><select className="select-input" value={form.effect_estimate_id} onChange={(e) => setForm({ ...form, effect_estimate_id: e.target.value })}><option value="">No specific effect</option>{relevantEffects.map((item) => <option key={item.effect_estimate_id} value={item.effect_estimate_id}>{item.metric}: {item.estimate_value} ({humanize(item.estimate_scope)})</option>)}</select></label><div className="two-fields"><label><span className="field-label">Role</span><select className="select-input" value={form.contribution_role} onChange={(e) => setForm({ ...form, contribution_role: e.target.value })}>{contributionRoles.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><label><span className="field-label">Direction</span><select className="select-input" value={form.result_direction} onChange={(e) => setForm({ ...form, result_direction: e.target.value })}>{directions.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label></div><div className="two-fields"><label><span className="field-label">Inclusion</span><select className="select-input" value={form.inclusion_status} onChange={(e) => setForm({ ...form, inclusion_status: e.target.value })}>{['candidate', 'included', 'excluded', 'deferred'].map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><EditInput label="Inclusion reason" value={form.inclusion_reason} onChange={(value) => setForm({ ...form, inclusion_reason: value })} /></div><button className="primary-button fit" onClick={() => void save()}><Save size={14} /> Save contribution</button></div>
}

function SynthesisForm({ propositionId, onDone, onError }: { propositionId: number; onDone: () => Promise<void>; onError: (value: string | null) => void }) {
  const [form, setForm] = useState({ synthesis_key: '', title: '', synthesis_kind: 'structured_internal_synthesis', method_summary: '', search_or_selection_basis: '', version: '1' })
  async function save() {
    if (!form.synthesis_key || !form.title || !form.method_summary || !form.version) { onError('Synthesis key, title, method summary and version are required.'); return }
    const { error } = await supabase.from('body_evidence_synthesis').insert({ proposition_id: propositionId, ...form, search_or_selection_basis: form.search_or_selection_basis || null, status: 'draft', mapping_source: 'human_review', review_status: 'proposed' })
    if (error) onError(error.message); else await onDone()
  }
  return <div className="quality-form"><div className="two-fields"><EditInput label="Synthesis key" value={form.synthesis_key} onChange={(value) => setForm({ ...form, synthesis_key: value })} /><EditInput label="Title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} /></div><label><span className="field-label">Synthesis kind</span><select className="select-input" value={form.synthesis_kind} onChange={(e) => setForm({ ...form, synthesis_kind: e.target.value })}>{synthesisKinds.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><label className="field-label">Method summary</label><textarea className="textarea" rows={3} value={form.method_summary} onChange={(e) => setForm({ ...form, method_summary: e.target.value })} /><div className="two-fields"><EditInput label="Selection basis" value={form.search_or_selection_basis} onChange={(value) => setForm({ ...form, search_or_selection_basis: value })} /><EditInput label="Version" value={form.version} onChange={(value) => setForm({ ...form, version: value })} /></div><button className="primary-button fit" onClick={() => void save()}><Save size={14} /> Save synthesis</button></div>
}

function SynthesisOutcomeForm({ synthesis, onDone, onError }: { synthesis: BodySynthesis; onDone: () => Promise<void>; onError: (value: string | null) => void }) {
  const [form, setForm] = useState({ outcome_key: '', outcome_label: '', conclusion_direction: 'uncertain', conclusion_summary: '', estimate_type: '', metric: '', pooled_estimate: '', ci_level: '', ci_lower: '', ci_upper: '', included_study_count: '', included_result_count: '' })
  async function save() {
    if (!form.outcome_key || !form.outcome_label || !form.conclusion_summary) { onError('Outcome key, label and conclusion summary are required.'); return }
    const pooledEstimate = num(form.pooled_estimate)
    const { error } = await supabase.from('synthesis_outcome').insert({ body_synthesis_id: synthesis.body_synthesis_id, proposition_id: synthesis.proposition_id, outcome_key: form.outcome_key, outcome_label: form.outcome_label, conclusion_direction: form.conclusion_direction, conclusion_summary: form.conclusion_summary, estimate_type: pooledEstimate == null ? null : (form.estimate_type || 'other'), metric: pooledEstimate == null ? null : (form.metric || 'unspecified'), pooled_estimate: pooledEstimate, ci_level: num(form.ci_level), ci_lower: num(form.ci_lower), ci_upper: num(form.ci_upper), included_study_count: num(form.included_study_count), included_result_count: num(form.included_result_count), status: 'draft', mapping_source: 'human_review', review_status: 'proposed' })
    if (error) onError(error.message); else await onDone()
  }
  return <div className="quality-form"><div className="two-fields"><EditInput label="Outcome key" value={form.outcome_key} onChange={(value) => setForm({ ...form, outcome_key: value })} /><EditInput label="Outcome label" value={form.outcome_label} onChange={(value) => setForm({ ...form, outcome_label: value })} /></div><label><span className="field-label">Conclusion direction</span><select className="select-input" value={form.conclusion_direction} onChange={(e) => setForm({ ...form, conclusion_direction: e.target.value })}>{directions.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><label className="field-label">Conclusion summary</label><textarea className="textarea" rows={3} value={form.conclusion_summary} onChange={(e) => setForm({ ...form, conclusion_summary: e.target.value })} /><div className="triple-fields"><EditInput label="Metric" value={form.metric} onChange={(value) => setForm({ ...form, metric: value })} /><EditInput label="Pooled estimate" type="number" value={form.pooled_estimate} onChange={(value) => setForm({ ...form, pooled_estimate: value })} /><EditInput label="CI level (0–1)" type="number" value={form.ci_level} onChange={(value) => setForm({ ...form, ci_level: value })} /></div><div className="triple-fields"><EditInput label="CI lower" type="number" value={form.ci_lower} onChange={(value) => setForm({ ...form, ci_lower: value })} /><EditInput label="CI upper" type="number" value={form.ci_upper} onChange={(value) => setForm({ ...form, ci_upper: value })} /><EditInput label="Estimate type" value={form.estimate_type} onChange={(value) => setForm({ ...form, estimate_type: value })} /></div><div className="two-fields"><EditInput label="Included studies" type="number" value={form.included_study_count} onChange={(value) => setForm({ ...form, included_study_count: value })} /><EditInput label="Included results" type="number" value={form.included_result_count} onChange={(value) => setForm({ ...form, included_result_count: value })} /></div><button className="primary-button fit" onClick={() => void save()}><Save size={14} /> Save synthesis outcome</button></div>
}

function CertaintyForm({ outcomeId, gradeAvailable, onDone, onError }: { outcomeId: number; gradeAvailable: boolean; onDone: () => Promise<void>; onError: (value: string | null) => void }) {
  const [form, setForm] = useState({ certainty_judgement: 'low', basis: '', framework_version: '' })
  async function save() {
    if (!gradeAvailable) { onError('GRADE framework definition is unavailable.'); return }
    if (!form.basis) { onError('Body-certainty basis is required.'); return }
    const { error } = await supabase.from('body_certainty_assessment').insert({ synthesis_outcome_id: outcomeId, framework_key: 'grade', framework_version: form.framework_version || null, certainty_judgement: form.certainty_judgement, assessment_status: 'assessment_in_progress', basis: form.basis, mapping_source: 'human_review', review_status: 'proposed' })
    if (error) onError(error.message); else await onDone()
  }
  return <div className="quality-form"><div className="two-fields"><label><span className="field-label">GRADE certainty</span><select className="select-input" value={form.certainty_judgement} onChange={(e) => setForm({ ...form, certainty_judgement: e.target.value })}>{['high', 'moderate', 'low', 'very_low'].map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><EditInput label="Framework version" value={form.framework_version} onChange={(value) => setForm({ ...form, framework_version: value })} /></div><label className="field-label">Basis</label><textarea className="textarea" rows={3} value={form.basis} onChange={(e) => setForm({ ...form, basis: e.target.value })} /><button className="primary-button fit" onClick={() => void save()}><Save size={14} /> Save body certainty</button></div>
}

function MaturityForm({ outcomeId, maturityDefinitions, onDone, onError }: { outcomeId: number; maturityDefinitions: MaturityDefinition[]; onDone: () => Promise<void>; onError: (value: string | null) => void }) {
  const [form, setForm] = useState({ maturity_level: '0', basis: '', direct_study_count: '', genuine_replication_count: '', independent_replication_count: '', replication_basis: '', consistency_pattern: 'not_assessed', unresolved_boundaries: '' })
  async function save() {
    if (!form.basis) { onError('Body-EML basis is required.'); return }
    const { error } = await supabase.from('body_maturity_assessment').insert({ synthesis_outcome_id: outcomeId, scale_version: 'hrp-eml-v1', maturity_level: Number(form.maturity_level), assessment_status: 'provisional', basis: form.basis, direct_study_count: num(form.direct_study_count), genuine_replication_count: num(form.genuine_replication_count), independent_replication_count: num(form.independent_replication_count), replication_basis: form.replication_basis || null, consistency_pattern: form.consistency_pattern, unresolved_boundaries: form.unresolved_boundaries || null, mapping_source: 'human_review', review_status: 'proposed' })
    if (error) onError(error.message); else await onDone()
  }
  return <div className="quality-form"><label><span className="field-label">Body EML</span><select className="select-input" value={form.maturity_level} onChange={(e) => setForm({ ...form, maturity_level: e.target.value })}>{maturityDefinitions.map((value) => <option key={value.maturity_level} value={value.maturity_level}>{value.code} — {value.label}</option>)}</select></label><label className="field-label">Basis</label><textarea className="textarea" rows={3} value={form.basis} onChange={(e) => setForm({ ...form, basis: e.target.value })} /><div className="triple-fields"><EditInput label="Direct studies" type="number" value={form.direct_study_count} onChange={(value) => setForm({ ...form, direct_study_count: value })} /><EditInput label="Genuine replications" type="number" value={form.genuine_replication_count} onChange={(value) => setForm({ ...form, genuine_replication_count: value })} /><EditInput label="Independent replications" type="number" value={form.independent_replication_count} onChange={(value) => setForm({ ...form, independent_replication_count: value })} /></div><label><span className="field-label">Consistency</span><select className="select-input" value={form.consistency_pattern} onChange={(e) => setForm({ ...form, consistency_pattern: e.target.value })}>{consistencyPatterns.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><EditInput label="Replication basis" value={form.replication_basis} onChange={(value) => setForm({ ...form, replication_basis: value })} /><EditInput label="Unresolved boundaries" value={form.unresolved_boundaries} onChange={(value) => setForm({ ...form, unresolved_boundaries: value })} /><button className="primary-button fit" onClick={() => void save()}><Save size={14} /> Save body EML</button></div>
}

function ClaimForm({ proposition, outcomeId, onDone, onError }: { proposition: Proposition; outcomeId: number; onDone: () => Promise<void>; onError: (value: string | null) => void }) {
  const [form, setForm] = useState({ claim_key: '', product: '', claim_text: '', required_caveat: '', population_scope: proposition.population_scope, context_scope: proposition.context_scope ?? '', route_scope: proposition.route_scope.join(', '), certainty_summary: '', version: '1' })
  async function save() {
    if (!form.claim_key || !form.claim_text || !form.population_scope || !form.version) { onError('Claim key, claim text, population scope and version are required.'); return }
    const { error } = await supabase.from('body_approved_claim').insert({ claim_key: form.claim_key, proposition_id: proposition.proposition_id, synthesis_outcome_id: outcomeId, product: form.product || null, claim_text: form.claim_text, required_caveat: form.required_caveat || null, population_scope: form.population_scope, context_scope: form.context_scope || null, route_scope: splitList(form.route_scope), certainty_summary: form.certainty_summary || null, status: 'draft', version: form.version, mapping_source: 'human_review', review_status: 'proposed' })
    if (error) onError(error.message); else await onDone()
  }
  return <div className="quality-form"><div className="two-fields"><EditInput label="Claim key" value={form.claim_key} onChange={(value) => setForm({ ...form, claim_key: value })} /><EditInput label="Product (optional)" value={form.product} onChange={(value) => setForm({ ...form, product: value })} /></div><label className="field-label">Claim text</label><textarea className="textarea" rows={3} value={form.claim_text} onChange={(e) => setForm({ ...form, claim_text: e.target.value })} /><EditInput label="Required caveat" value={form.required_caveat} onChange={(value) => setForm({ ...form, required_caveat: value })} /><div className="two-fields"><EditInput label="Population scope" value={form.population_scope} onChange={(value) => setForm({ ...form, population_scope: value })} /><EditInput label="Context scope" value={form.context_scope} onChange={(value) => setForm({ ...form, context_scope: value })} /></div><div className="two-fields"><EditInput label="Route scope (comma separated)" value={form.route_scope} onChange={(value) => setForm({ ...form, route_scope: value })} /><EditInput label="Version" value={form.version} onChange={(value) => setForm({ ...form, version: value })} /></div><EditInput label="Certainty summary" value={form.certainty_summary} onChange={(value) => setForm({ ...form, certainty_summary: value })} /><button className="primary-button fit" onClick={() => void save()}><Save size={14} /> Save draft claim</button></div>
}
