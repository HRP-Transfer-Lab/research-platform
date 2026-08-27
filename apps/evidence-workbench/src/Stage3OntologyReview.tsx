import { useEffect, useMemo, useState } from 'react'
import { BrainCircuit, Check, Plus, RefreshCw, X } from 'lucide-react'
import { supabase } from './lib/supabase'
import { DetailSection, EmptyLine } from './WorkbenchUi'
import { humanize, type EvidenceSource } from './workbench'

type ApplicationFamilyDefinition = {
  application_family: string
  label: string
  description: string
  active: boolean
}

type ApplicationFamilyLink = {
  source_version_id: string
  application_family: string
  relevance_level: string
  rationale: string | null
  mapping_source: string
  review_status: string
}

type TargetDefinition = {
  target_id: string
  canonical_label: string
  target_locus: string
  description: string
  ontology_status: string
}

type ComponentRow = {
  component_id: number
  component_name: string
  route: string
}

type ComponentTarget = {
  component_id: number
  target_id: string
  relationship: string
  rationale: string | null
  mapping_source: string
  review_status: string
}

type ComponentTargetStatus = {
  component_id: number
  extraction_status: string
  notes: string | null
  mapping_source: string
}

type MechanismDefinition = {
  mechanism_id: string
  canonical_label: string
  description: string
  mechanism_status: string
}

type MechanismAssertion = {
  mechanism_assertion_id: number
  source_version_id: string
  mechanism_id: string
  study_id: number | null
  component_id: number | null
  assertion_type: string
  assertion_direction: string
  support_summary: string | null
  author_reported_text: string | null
  mapping_source: string
  review_status: string
}

type MechanismStatus = {
  source_version_id: string
  extraction_status: string
  notes: string | null
  mapping_source: string
}

const relevanceOptions = ['primary', 'secondary', 'adjacent']
const targetRelationshipOptions = ['primary_target', 'secondary_target', 'target_engagement_only']
const mechanismTypeOptions = [
  'author_proposed',
  'hrp_candidate',
  'experimentally_manipulated',
  'target_engagement_supported',
  'mediator_tested',
  'mediator_supported',
  'mediator_not_supported',
  'boundary_condition',
]
const mechanismDirectionOptions = ['supports', 'mixed', 'null', 'contradicts', 'unclear', 'not_applicable']

function ReviewStatus({ mappingSource, reviewStatus }: { mappingSource: string; reviewStatus: string }) {
  return (
    <span className="detail-meta-row">
      <span className="status-pill">{humanize(mappingSource)}</span>
      <span className="status-pill">{humanize(reviewStatus)}</span>
    </span>
  )
}

export function Stage3OntologyReview({
  source,
  canEdit,
  onError,
}: {
  source: EvidenceSource
  canEdit: boolean
  onError: (value: string | null) => void
}) {
  const [loading, setLoading] = useState(false)
  const [sourceVersionId, setSourceVersionId] = useState<string | null>(null)
  const [studyId, setStudyId] = useState<number | null>(null)
  const [families, setFamilies] = useState<ApplicationFamilyDefinition[]>([])
  const [familyLinks, setFamilyLinks] = useState<ApplicationFamilyLink[]>([])
  const [targets, setTargets] = useState<TargetDefinition[]>([])
  const [components, setComponents] = useState<ComponentRow[]>([])
  const [componentTargets, setComponentTargets] = useState<ComponentTarget[]>([])
  const [componentStatuses, setComponentStatuses] = useState<ComponentTargetStatus[]>([])
  const [mechanisms, setMechanisms] = useState<MechanismDefinition[]>([])
  const [mechanismAssertions, setMechanismAssertions] = useState<MechanismAssertion[]>([])
  const [mechanismStatus, setMechanismStatus] = useState<MechanismStatus | null>(null)

  const [familyChoice, setFamilyChoice] = useState('mental_fitness')
  const [familyRelevance, setFamilyRelevance] = useState('secondary')
  const [familyRationale, setFamilyRationale] = useState('')
  const [targetChoice, setTargetChoice] = useState('')
  const [targetRelationship, setTargetRelationship] = useState('primary_target')
  const [targetRationale, setTargetRationale] = useState('')
  const [targetComponentId, setTargetComponentId] = useState<number | null>(null)
  const [mechanismChoice, setMechanismChoice] = useState('')
  const [mechanismType, setMechanismType] = useState('hrp_candidate')
  const [mechanismDirection, setMechanismDirection] = useState('supports')
  const [mechanismSummary, setMechanismSummary] = useState('')

  const targetById = useMemo(() => new Map(targets.map((item) => [item.target_id, item])), [targets])
  const mechanismById = useMemo(() => new Map(mechanisms.map((item) => [item.mechanism_id, item])), [mechanisms])

  useEffect(() => {
    void load()
  }, [source.source_id])

  async function load() {
    setLoading(true)
    onError(null)

    const membership = await supabase
      .from('release_source_version')
      .select('source_version_id')
      .eq('release_id', source.release_id)
      .eq('release_record_id', source.source_id)
      .maybeSingle()

    if (membership.error) {
      onError(membership.error.message)
      setLoading(false)
      return
    }

    const svId = membership.data?.source_version_id ?? null
    setSourceVersionId(svId)

    const study = await supabase
      .from('study')
      .select('study_id')
      .eq('source_id', source.source_id)
      .maybeSingle()

    if (study.error) {
      onError(study.error.message)
      setLoading(false)
      return
    }

    const sid = study.data?.study_id ?? null
    setStudyId(sid)

    const componentQuery = sid
      ? supabase.from('intervention_component').select('component_id,component_name,route').eq('study_id', sid).order('component_id')
      : Promise.resolve({ data: [], error: null } as any)

    const [familyDefs, targetDefs, mechanismDefs, componentRows] = await Promise.all([
      supabase.from('application_family_definition').select('application_family,label,description,active').eq('active', true).order('application_family'),
      supabase.from('target_definition').select('target_id,canonical_label,target_locus,description,ontology_status').neq('ontology_status', 'retired').order('canonical_label'),
      supabase.from('mechanism_definition').select('mechanism_id,canonical_label,description,mechanism_status').neq('mechanism_status', 'retired').order('canonical_label'),
      componentQuery,
    ])

    const firstError = [familyDefs, targetDefs, mechanismDefs, componentRows].find((result) => result.error)?.error
    if (firstError) {
      onError(firstError.message)
      setLoading(false)
      return
    }

    const nextComponents = (componentRows.data ?? []) as ComponentRow[]
    setFamilies((familyDefs.data ?? []) as ApplicationFamilyDefinition[])
    setTargets((targetDefs.data ?? []) as TargetDefinition[])
    setMechanisms((mechanismDefs.data ?? []) as MechanismDefinition[])
    setComponents(nextComponents)

    if (!targetChoice && targetDefs.data?.length) setTargetChoice(targetDefs.data[0].target_id)
    if (!mechanismChoice && mechanismDefs.data?.length) setMechanismChoice(mechanismDefs.data[0].mechanism_id)
    if (targetComponentId == null && nextComponents.length) setTargetComponentId(nextComponents[0].component_id)

    const componentIds = nextComponents.map((item) => item.component_id)
    const [familyRows, targetRows, targetStatusRows, mechanismRows, mechanismStatusRow] = await Promise.all([
      svId
        ? supabase.from('source_version_application_family').select('*').eq('source_version_id', svId).order('application_family')
        : Promise.resolve({ data: [], error: null } as any),
      componentIds.length
        ? supabase.from('component_target').select('*').in('component_id', componentIds).order('component_id')
        : Promise.resolve({ data: [], error: null } as any),
      componentIds.length
        ? supabase.from('component_target_extraction_status').select('*').in('component_id', componentIds).order('component_id')
        : Promise.resolve({ data: [], error: null } as any),
      svId
        ? supabase.from('mechanism_assertion').select('*').eq('source_version_id', svId).order('mechanism_assertion_id')
        : Promise.resolve({ data: [], error: null } as any),
      svId
        ? supabase.from('source_version_mechanism_status').select('*').eq('source_version_id', svId).maybeSingle()
        : Promise.resolve({ data: null, error: null } as any),
    ])

    const mappingError = [familyRows, targetRows, targetStatusRows, mechanismRows, mechanismStatusRow].find((result) => result.error)?.error
    if (mappingError) onError(mappingError.message)
    else {
      setFamilyLinks((familyRows.data ?? []) as ApplicationFamilyLink[])
      setComponentTargets((targetRows.data ?? []) as ComponentTarget[])
      setComponentStatuses((targetStatusRows.data ?? []) as ComponentTargetStatus[])
      setMechanismAssertions((mechanismRows.data ?? []) as MechanismAssertion[])
      setMechanismStatus((mechanismStatusRow.data ?? null) as MechanismStatus | null)
    }

    setLoading(false)
  }

  async function reviewFamily(item: ApplicationFamilyLink, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase
      .from('source_version_application_family')
      .update({ review_status: reviewStatus, mapping_source: 'human_review', updated_at: new Date().toISOString() })
      .eq('source_version_id', item.source_version_id)
      .eq('application_family', item.application_family)
    if (error) onError(error.message)
    else await load()
  }

  async function addFamily() {
    if (!sourceVersionId) return
    const { error } = await supabase.from('source_version_application_family').upsert({
      source_version_id: sourceVersionId,
      application_family: familyChoice,
      relevance_level: familyRelevance,
      rationale: familyRationale || 'Human-reviewed Workbench application-family mapping.',
      mapping_source: 'human_review',
      review_status: 'approved',
      updated_at: new Date().toISOString(),
    }, { onConflict: 'source_version_id,application_family' })
    if (error) onError(error.message)
    else {
      setFamilyRationale('')
      await load()
    }
  }

  async function reviewTarget(item: ComponentTarget, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase
      .from('component_target')
      .update({ review_status: reviewStatus, mapping_source: 'human_review', updated_at: new Date().toISOString() })
      .eq('component_id', item.component_id)
      .eq('target_id', item.target_id)
      .eq('relationship', item.relationship)
    if (error) return onError(error.message)
    await syncTargetStatus(item.component_id)
    await load()
  }

  async function syncTargetStatus(componentId: number) {
    const { data: rows, error } = await supabase
      .from('component_target')
      .select('review_status')
      .eq('component_id', componentId)
    if (error) return onError(error.message)
    const approved = (rows ?? []).some((row: any) => row.review_status === 'approved')
    const proposed = (rows ?? []).some((row: any) => row.review_status === 'proposed')
    const extractionStatus = approved && !proposed ? 'reviewed_mapped' : proposed ? 'partially_extracted' : 'reviewed_no_mapping'
    const { error: statusError } = await supabase
      .from('component_target_extraction_status')
      .update({ extraction_status: extractionStatus, mapping_source: 'human_review', updated_at: new Date().toISOString() })
      .eq('component_id', componentId)
    if (statusError) onError(statusError.message)
  }

  async function addTarget() {
    if (!targetComponentId || !targetChoice) return
    const { error } = await supabase.from('component_target').upsert({
      component_id: targetComponentId,
      target_id: targetChoice,
      relationship: targetRelationship,
      rationale: targetRationale || 'Human-reviewed Workbench target mapping.',
      mapping_source: 'human_review',
      review_status: 'approved',
      updated_at: new Date().toISOString(),
    }, { onConflict: 'component_id,target_id,relationship' })
    if (error) return onError(error.message)
    setTargetRationale('')
    await syncTargetStatus(targetComponentId)
    await load()
  }

  async function reviewMechanism(item: MechanismAssertion, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase
      .from('mechanism_assertion')
      .update({ review_status: reviewStatus, mapping_source: 'human_review', updated_at: new Date().toISOString() })
      .eq('mechanism_assertion_id', item.mechanism_assertion_id)
    if (error) return onError(error.message)
    await syncMechanismStatus()
    await load()
  }

  async function syncMechanismStatus() {
    if (!sourceVersionId) return
    const { data: rows, error } = await supabase
      .from('mechanism_assertion')
      .select('review_status')
      .eq('source_version_id', sourceVersionId)
    if (error) return onError(error.message)
    const approved = (rows ?? []).some((row: any) => row.review_status === 'approved')
    const proposed = (rows ?? []).some((row: any) => row.review_status === 'proposed')
    const extractionStatus = approved && !proposed ? 'reviewed_mapped' : proposed ? 'partially_extracted' : 'reviewed_no_mapping'
    const { error: statusError } = await supabase
      .from('source_version_mechanism_status')
      .update({ extraction_status: extractionStatus, mapping_source: 'human_review', updated_at: new Date().toISOString() })
      .eq('source_version_id', sourceVersionId)
    if (statusError) onError(statusError.message)
  }

  async function addMechanism() {
    if (!sourceVersionId || !mechanismChoice) return
    const { error } = await supabase.from('mechanism_assertion').insert({
      source_version_id: sourceVersionId,
      mechanism_id: mechanismChoice,
      study_id: studyId,
      component_id: null,
      assertion_type: mechanismType,
      assertion_direction: mechanismDirection,
      support_summary: mechanismSummary || 'Human-reviewed Workbench mechanism assertion.',
      mapping_source: 'human_review',
      review_status: 'approved',
    })
    if (error) return onError(error.message)
    setMechanismSummary('')
    await syncMechanismStatus()
    await load()
  }

  return (
    <DetailSection title="Application, target & mechanism review" icon={<BrainCircuit size={17} />}>
      <div className="record-note">
        Stage 3 separates application family, target locus/construct and mechanism. Agent-generated mappings are proposals only. Human acceptance converts the row to <strong>human_review / approved</strong>; rejection remains auditable as <strong>human_review / rejected</strong>.
      </div>

      {loading && <div className="small-copy" style={{ marginTop: 12 }}><RefreshCw className="spin" size={14} /> Loading Stage 3 mappings…</div>}

      <div style={{ marginTop: 16 }}>
        <span className="field-label">Application families</span>
        <div className="stack-list">
          {familyLinks.length ? familyLinks.map((item) => {
            const def = families.find((family) => family.application_family === item.application_family)
            return (
              <div className="product-card" key={item.application_family}>
                <div className="product-head">
                  <div><strong>{def?.label ?? humanize(item.application_family)}</strong> <span className="status-pill">{humanize(item.relevance_level)}</span> <ReviewStatus mappingSource={item.mapping_source} reviewStatus={item.review_status} /></div>
                  {canEdit && item.review_status === 'proposed' && <div className="edit-actions"><button className="icon-button mini" title="Approve application mapping" onClick={() => reviewFamily(item, 'approved')}><Check size={13} /></button><button className="icon-button mini" title="Reject application mapping" onClick={() => reviewFamily(item, 'rejected')}><X size={13} /></button></div>}
                </div>
                {item.rationale && <p className="small-copy">{item.rationale}</p>}
              </div>
            )
          }) : <EmptyLine>No application-family mappings recorded.</EmptyLine>}
        </div>
        {canEdit && sourceVersionId && <div className="edit-stack subedit" style={{ marginTop: 10 }}>
          <label><span className="field-label">Application family</span><select className="select-input" value={familyChoice} onChange={(event) => setFamilyChoice(event.target.value)}>{families.map((item) => <option key={item.application_family} value={item.application_family}>{item.label}</option>)}</select></label>
          <label><span className="field-label">Relevance</span><select className="select-input" value={familyRelevance} onChange={(event) => setFamilyRelevance(event.target.value)}>{relevanceOptions.map((item) => <option key={item} value={item}>{humanize(item)}</option>)}</select></label>
          <label><span className="field-label">Reviewer rationale</span><input className="text-input" value={familyRationale} onChange={(event) => setFamilyRationale(event.target.value)} placeholder="Why is this application domain relevant?" /></label>
          <button className="secondary-button fit" onClick={addFamily}><Plus size={13} /> Add / replace human-reviewed mapping</button>
        </div>}
      </div>

      <div style={{ marginTop: 18 }}>
        <span className="field-label">Intervention targets</span>
        {components.length ? components.map((component) => {
          const rows = componentTargets.filter((item) => item.component_id === component.component_id)
          const status = componentStatuses.find((item) => item.component_id === component.component_id)
          return (
            <div key={component.component_id} className="product-card" style={{ marginTop: 8 }}>
              <div className="product-head"><div><strong>{component.component_name}</strong> <span className="status-pill">{humanize(component.route)}</span> {status && <span className="status-pill">{humanize(status.extraction_status)}</span>}</div></div>
              <div className="stack-list" style={{ marginTop: 8 }}>
                {rows.length ? rows.map((item) => {
                  const target = targetById.get(item.target_id)
                  return (
                    <div key={`${item.target_id}-${item.relationship}`} className="product-card">
                      <div className="product-head">
                        <div><strong>{humanize(target?.canonical_label ?? item.target_id)}</strong> <span className="status-pill">{humanize(target?.target_locus)}</span> <span className="status-pill">{humanize(item.relationship)}</span> <ReviewStatus mappingSource={item.mapping_source} reviewStatus={item.review_status} /></div>
                        {canEdit && item.review_status === 'proposed' && <div className="edit-actions"><button className="icon-button mini" title="Approve target mapping" onClick={() => reviewTarget(item, 'approved')}><Check size={13} /></button><button className="icon-button mini" title="Reject target mapping" onClick={() => reviewTarget(item, 'rejected')}><X size={13} /></button></div>}
                      </div>
                      {item.rationale && <p className="small-copy">{item.rationale}</p>}
                    </div>
                  )
                }) : <EmptyLine>No target mapping recorded for this component.</EmptyLine>}
              </div>
            </div>
          )
        }) : <EmptyLine>No intervention component exists — valid for mechanism, measurement or observational evidence.</EmptyLine>}

        {canEdit && components.length > 0 && <div className="edit-stack subedit" style={{ marginTop: 10 }}>
          <label><span className="field-label">Component</span><select className="select-input" value={targetComponentId ?? ''} onChange={(event) => setTargetComponentId(Number(event.target.value))}>{components.map((item) => <option key={item.component_id} value={item.component_id}>{item.component_name}</option>)}</select></label>
          <label><span className="field-label">Target</span><select className="select-input" value={targetChoice} onChange={(event) => setTargetChoice(event.target.value)}>{targets.map((item) => <option key={item.target_id} value={item.target_id}>{humanize(item.canonical_label)} · {humanize(item.target_locus)}</option>)}</select></label>
          <label><span className="field-label">Relationship</span><select className="select-input" value={targetRelationship} onChange={(event) => setTargetRelationship(event.target.value)}>{targetRelationshipOptions.map((item) => <option key={item} value={item}>{humanize(item)}</option>)}</select></label>
          <label><span className="field-label">Reviewer rationale</span><input className="text-input" value={targetRationale} onChange={(event) => setTargetRationale(event.target.value)} placeholder="Why is this construct targeted?" /></label>
          <button className="secondary-button fit" onClick={addTarget}><Plus size={13} /> Add / replace human-reviewed target</button>
        </div>}
      </div>

      <div style={{ marginTop: 18 }}>
        <span className="field-label">Mechanism assertions</span>
        {mechanismStatus && <div className="small-copy" style={{ marginBottom: 8 }}>Extraction status: <strong>{humanize(mechanismStatus.extraction_status)}</strong></div>}
        <div className="stack-list">
          {mechanismAssertions.length ? mechanismAssertions.map((item) => {
            const mechanism = mechanismById.get(item.mechanism_id)
            return (
              <div className="product-card" key={item.mechanism_assertion_id}>
                <div className="product-head">
                  <div><strong>{humanize(mechanism?.canonical_label ?? item.mechanism_id)}</strong> <span className="status-pill">{humanize(item.assertion_type)}</span> <span className="status-pill">{humanize(item.assertion_direction)}</span> <ReviewStatus mappingSource={item.mapping_source} reviewStatus={item.review_status} /></div>
                  {canEdit && item.review_status === 'proposed' && <div className="edit-actions"><button className="icon-button mini" title="Approve mechanism assertion" onClick={() => reviewMechanism(item, 'approved')}><Check size={13} /></button><button className="icon-button mini" title="Reject mechanism assertion" onClick={() => reviewMechanism(item, 'rejected')}><X size={13} /></button></div>}
                </div>
                {item.support_summary && <p className="small-copy">{item.support_summary}</p>}
              </div>
            )
          }) : <EmptyLine>No mechanism assertion recorded. This does not imply evidence of no mechanism.</EmptyLine>}
        </div>

        {canEdit && sourceVersionId && <div className="edit-stack subedit" style={{ marginTop: 10 }}>
          <label><span className="field-label">Mechanism</span><select className="select-input" value={mechanismChoice} onChange={(event) => setMechanismChoice(event.target.value)}>{mechanisms.map((item) => <option key={item.mechanism_id} value={item.mechanism_id}>{humanize(item.canonical_label)}</option>)}</select></label>
          <label><span className="field-label">Assertion type</span><select className="select-input" value={mechanismType} onChange={(event) => setMechanismType(event.target.value)}>{mechanismTypeOptions.map((item) => <option key={item} value={item}>{humanize(item)}</option>)}</select></label>
          <label><span className="field-label">Direction</span><select className="select-input" value={mechanismDirection} onChange={(event) => setMechanismDirection(event.target.value)}>{mechanismDirectionOptions.map((item) => <option key={item} value={item}>{humanize(item)}</option>)}</select></label>
          <label><span className="field-label">Support summary</span><input className="text-input" value={mechanismSummary} onChange={(event) => setMechanismSummary(event.target.value)} placeholder="What supports or contradicts this mechanism?" /></label>
          <button className="secondary-button fit" onClick={addMechanism}><Plus size={13} /> Add human-reviewed mechanism assertion</button>
        </div>}
      </div>
    </DetailSection>
  )
}
