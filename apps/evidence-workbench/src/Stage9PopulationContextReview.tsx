import { useEffect, useMemo, useState } from 'react'
import { Check, RefreshCw, Users, X } from 'lucide-react'
import { supabase } from './lib/supabase'
import { DetailSection, EmptyLine } from './WorkbenchUi'
import { humanize, type EvidenceSource, type RegistryData } from './workbench'

type Term = {
  term_id: string
  facet_kind: string
  canonical_label: string
  description: string
  parent_term_id: string | null
}

type StudyStatus = {
  study_id: number
  facet_kind: string
  extraction_status: string
  notes: string | null
  mapping_source: string
  review_status: string
}

type StudyLink = {
  study_id: number
  term_id: string
  relationship: string
  evidence_basis: string
  mapping_source: string
  review_status: string
}

type DeliveryStatus = {
  component_id: number
  extraction_status: string
  notes: string | null
  mapping_source: string
  review_status: string
}

type DeliveryLink = {
  component_id: number
  term_id: string
  evidence_basis: string
  mapping_source: string
  review_status: string
}

type ContextFit = {
  context_fit_assessment_id: number
  proposition_id: number
  study_id: number
  fit_dimension: string
  fit_judgement: string
  boundary_summary: string | null
  rationale: string
  mapping_source: string
  review_status: string
}

const facetOrder = [
  'life_stage',
  'role',
  'health_condition_context',
  'baseline_cognitive_status',
  'education_level',
  'study_setting',
  'geography',
]

const reviewableStatuses = [
  'not_yet_extracted',
  'reviewed_mapped',
  'reviewed_no_mapping',
  'not_reported',
  'not_applicable',
]

function ReviewPills({ source, status }: { source: string; status: string }) {
  return <span className="detail-meta-row"><span className="status-pill">{humanize(source)}</span><span className="status-pill">{humanize(status)}</span></span>
}

function ReviewButtons({ onApprove, onReject }: { onApprove: () => void; onReject: () => void }) {
  return <span className="detail-meta-row"><button className="icon-button mini" title="Approve" onClick={onApprove}><Check size={13} /></button><button className="icon-button mini" title="Reject" onClick={onReject}><X size={13} /></button></span>
}

export function Stage9PopulationContextReview({
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
  const [terms, setTerms] = useState<Term[]>([])
  const [studyStatuses, setStudyStatuses] = useState<StudyStatus[]>([])
  const [studyLinks, setStudyLinks] = useState<StudyLink[]>([])
  const [deliveryStatuses, setDeliveryStatuses] = useState<DeliveryStatus[]>([])
  const [deliveryLinks, setDeliveryLinks] = useState<DeliveryLink[]>([])
  const [contextFit, setContextFit] = useState<ContextFit[]>([])

  useEffect(() => { void load() }, [source.source_id, study?.study_id, componentIds.join(',')])

  async function load() {
    if (!study) {
      setTerms([]); setStudyStatuses([]); setStudyLinks([]); setDeliveryStatuses([]); setDeliveryLinks([]); setContextFit([])
      return
    }
    setLoading(true)
    onError(null)

    const base = await Promise.all([
      supabase.from('population_context_term').select('*').order('facet_kind').order('canonical_label'),
      supabase.from('study_population_context_status').select('*').eq('study_id', study.study_id),
      supabase.from('study_population_context_term').select('*').eq('study_id', study.study_id).order('term_id'),
      supabase.from('context_fit_assessment').select('*').eq('study_id', study.study_id).order('fit_dimension'),
    ])
    const baseError = base.find((result) => result.error)?.error
    if (baseError) { onError(baseError.message); setLoading(false); return }

    let componentStatusRows: DeliveryStatus[] = []
    let componentLinkRows: DeliveryLink[] = []
    if (componentIds.length) {
      const componentQueries = await Promise.all([
        supabase.from('component_delivery_context_status').select('*').in('component_id', componentIds),
        supabase.from('component_delivery_context_term').select('*').in('component_id', componentIds).order('component_id'),
      ])
      const componentError = componentQueries.find((result) => result.error)?.error
      if (componentError) { onError(componentError.message); setLoading(false); return }
      componentStatusRows = (componentQueries[0].data ?? []) as DeliveryStatus[]
      componentLinkRows = (componentQueries[1].data ?? []) as DeliveryLink[]
    }

    setTerms((base[0].data ?? []) as Term[])
    setStudyStatuses((base[1].data ?? []) as StudyStatus[])
    setStudyLinks((base[2].data ?? []) as StudyLink[])
    setContextFit((base[3].data ?? []) as ContextFit[])
    setDeliveryStatuses(componentStatusRows)
    setDeliveryLinks(componentLinkRows)
    setLoading(false)
  }

  async function reviewStudyLink(row: StudyLink, reviewStatus: 'approved' | 'rejected') {
    const updates = { mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }
    const { error } = await supabase.from('study_population_context_term').update(updates)
      .eq('study_id', row.study_id).eq('term_id', row.term_id).eq('relationship', row.relationship)
    if (error) { onError(error.message); return }

    if (reviewStatus === 'approved') {
      const facet = terms.find((item) => item.term_id === row.term_id)?.facet_kind
      if (facet) {
        const { error: statusError } = await supabase.from('study_population_context_status').update({
          extraction_status: 'reviewed_mapped', mapping_source: 'human_review', review_status: 'approved', updated_at: new Date().toISOString(),
        }).eq('study_id', row.study_id).eq('facet_kind', facet)
        if (statusError) { onError(statusError.message); return }
      }
    }
    await load()
  }

  async function setStudyFacetStatus(facet: string, extractionStatus: string) {
    if (!study) return
    const { error } = await supabase.from('study_population_context_status').update({
      extraction_status: extractionStatus,
      mapping_source: 'human_review',
      review_status: extractionStatus === 'not_yet_extracted' ? 'reviewed' : 'approved',
      updated_at: new Date().toISOString(),
    }).eq('study_id', study.study_id).eq('facet_kind', facet)
    if (error) onError(error.message); else await load()
  }

  async function reviewDeliveryLink(row: DeliveryLink, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('component_delivery_context_term').update({
      mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString(),
    }).eq('component_id', row.component_id).eq('term_id', row.term_id)
    if (error) { onError(error.message); return }
    if (reviewStatus === 'approved') {
      const { error: statusError } = await supabase.from('component_delivery_context_status').update({
        extraction_status: 'reviewed_mapped', mapping_source: 'human_review', review_status: 'approved', updated_at: new Date().toISOString(),
      }).eq('component_id', row.component_id)
      if (statusError) { onError(statusError.message); return }
    }
    await load()
  }

  async function setDeliveryStatus(componentId: number, extractionStatus: string) {
    const { error } = await supabase.from('component_delivery_context_status').update({
      extraction_status: extractionStatus,
      mapping_source: 'human_review',
      review_status: extractionStatus === 'not_yet_extracted' ? 'reviewed' : 'approved',
      updated_at: new Date().toISOString(),
    }).eq('component_id', componentId)
    if (error) onError(error.message); else await load()
  }

  async function reviewContextFit(id: number, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('context_fit_assessment').update({
      mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString(),
    }).eq('context_fit_assessment_id', id)
    if (error) onError(error.message); else await load()
  }

  const termById = useMemo(() => new Map(terms.map((item) => [item.term_id, item])), [terms])

  return <DetailSection title="Population & context" icon={<Users size={17} />}>
    <div className="record-note">Stage 9 keeps life stage, role, health/condition context, baseline cognitive status, education, study setting, delivery context and geography orthogonal. Application family remains a separate Stage 3 lens. Context fit is proposition-relative and is not study quality, RoB, GRADE, effect magnitude or EML.</div>
    {loading && <div className="small-copy" style={{ marginTop: 12 }}><RefreshCw className="spin" size={14} /> Loading Stage 9 population/context architecture…</div>}
    {!study && <EmptyLine>No normalized study row.</EmptyLine>}

    {study && <div style={{ marginTop: 16 }}>
      <div className="record-note"><strong>Retained source description:</strong> {study.population_summary || 'Not recorded'}<br /><strong>Retained study setting:</strong> {study.setting || 'Not recorded'}</div>
      <div className="stack-list" style={{ marginTop: 12 }}>{facetOrder.map((facet) => {
        const status = studyStatuses.find((item) => item.facet_kind === facet)
        const links = studyLinks.filter((item) => termById.get(item.term_id)?.facet_kind === facet)
        return <div className="product-card" key={facet}>
          <div className="product-head"><strong>{humanize(facet)}</strong>{status && <ReviewPills source={status.mapping_source} status={status.review_status} />}</div>
          {status && <div className="product-meta"><span>{humanize(status.extraction_status)}</span></div>}
          {canEdit && status && <label><span className="field-label">Facet extraction state</span><select className="select-input" value={status.extraction_status} onChange={(e) => void setStudyFacetStatus(facet, e.target.value)}>{reviewableStatuses.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label>}
          <div className="stack-list" style={{ marginTop: 10 }}>{links.length ? links.map((row) => {
            const term = termById.get(row.term_id)
            return <div className="record-note" key={`${row.term_id}-${row.relationship}`}>
              <div className="product-head"><div><strong>{term?.canonical_label ?? row.term_id}</strong><span className="match-pill">{humanize(row.relationship)}</span></div><ReviewPills source={row.mapping_source} status={row.review_status} /></div>
              <p className="small-copy">{row.evidence_basis}</p>
              {canEdit && row.review_status === 'proposed' && <ReviewButtons onApprove={() => void reviewStudyLink(row, 'approved')} onReject={() => void reviewStudyLink(row, 'rejected')} />}
            </div>
          }) : <EmptyLine>No normalized mapping for this facet.</EmptyLine>}</div>
        </div>
      })}</div>
    </div>}

    {study && <div style={{ marginTop: 22 }}>
      <span className="field-label">Component delivery context</span>
      <div className="stack-list">{components.length ? components.map((component) => {
        const status = deliveryStatuses.find((item) => item.component_id === component.component_id)
        const links = deliveryLinks.filter((item) => item.component_id === component.component_id)
        return <div className="product-card" key={component.component_id}>
          <div className="product-head"><strong>{component.component_name}</strong>{status && <ReviewPills source={status.mapping_source} status={status.review_status} />}</div>
          <div className="record-note">Retained delivery mode: {component.delivery_mode || 'Not recorded'} · Retained setting: {component.setting || 'Not recorded'}</div>
          {status && <div className="product-meta"><span>{humanize(status.extraction_status)}</span></div>}
          {canEdit && status && <label><span className="field-label">Delivery extraction state</span><select className="select-input" value={status.extraction_status} onChange={(e) => void setDeliveryStatus(component.component_id, e.target.value)}>{reviewableStatuses.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label>}
          <div className="stack-list" style={{ marginTop: 10 }}>{links.length ? links.map((row) => {
            const term = termById.get(row.term_id)
            return <div className="record-note" key={row.term_id}>
              <div className="product-head"><strong>{term?.canonical_label ?? row.term_id}</strong><ReviewPills source={row.mapping_source} status={row.review_status} /></div>
              <p className="small-copy">{row.evidence_basis}</p>
              {canEdit && row.review_status === 'proposed' && <ReviewButtons onApprove={() => void reviewDeliveryLink(row, 'approved')} onReject={() => void reviewDeliveryLink(row, 'rejected')} />}
            </div>
          }) : <EmptyLine>No normalized delivery-context mapping.</EmptyLine>}</div>
        </div>
      }) : <EmptyLine>No intervention components for this source.</EmptyLine>}</div>
    </div>}

    {study && <div style={{ marginTop: 22 }}>
      <span className="field-label">Proposition-relative context fit</span>
      <div className="record-note">Context-fit judgements are only meaningful relative to an explicit Stage 8 proposition. The immutable seed contains none, so Stage 9 does not manufacture fit scores.</div>
      <div className="stack-list" style={{ marginTop: 10 }}>{contextFit.length ? contextFit.map((row) => <div className="product-card" key={row.context_fit_assessment_id}>
        <div className="product-head"><strong>{humanize(row.fit_dimension)} · {humanize(row.fit_judgement)}</strong><ReviewPills source={row.mapping_source} status={row.review_status} /></div>
        <p>{row.rationale}</p>
        {row.boundary_summary && <p className="small-copy"><strong>Boundary:</strong> {row.boundary_summary}</p>}
        {canEdit && row.review_status === 'proposed' && <ReviewButtons onApprove={() => void reviewContextFit(row.context_fit_assessment_id, 'approved')} onReject={() => void reviewContextFit(row.context_fit_assessment_id, 'rejected')} />}
      </div>) : <EmptyLine>No proposition-relative context-fit assessment.</EmptyLine>}</div>
    </div>}
  </DetailSection>
}
