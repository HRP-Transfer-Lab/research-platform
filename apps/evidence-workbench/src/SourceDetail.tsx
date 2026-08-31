import { useEffect, useState } from 'react'
import { Activity, ClipboardCheck, ExternalLink, FlaskConical, Pencil, Plus, Save, ShieldCheck, Sparkles, Users } from 'lucide-react'
import { supabase } from './lib/supabase'
import { asAuthorLine, compactJson, humanize, routeOptions, type Component, type EvidenceSource, type Outcome, type ProductRelevance, type RegistryData, type Study } from './workbench'
import { BucketPill, DetailSection, Dose, EditInput, EmptyLine, Info, RoutePill } from './WorkbenchUi'

export function SourceDetail({ source, data, canEdit, onRefresh, onError }: { source: EvidenceSource; data: RegistryData; canEdit: boolean; onRefresh: () => Promise<void>; onError: (v: string | null) => void }) {
  const study = data.studies.find((s) => s.source_id === source.source_id)
  const components = data.components.filter((c) => c.study_id === study?.study_id)
  const outcomes = data.outcomes.filter((o) => o.study_id === study?.study_id)
  const products = data.products.filter((p) => p.source_id === source.source_id)
  const quality = data.quality.filter((q) => q.source_id === source.source_id)
  const [editingSource, setEditingSource] = useState(false)
  const [routeRationale, setRouteRationale] = useState(source.route_rationale ?? '')
  const [reviewStatus, setReviewStatus] = useState(source.review_status)
  const [qualityOpen, setQualityOpen] = useState(false)

  useEffect(() => {
    setRouteRationale(source.route_rationale ?? '')
    setReviewStatus(source.review_status)
    setEditingSource(false)
    setQualityOpen(false)
  }, [source.source_id])

  async function saveSource() {
    const { error } = await supabase.from('evidence_source').update({ route_rationale: routeRationale, review_status: reviewStatus }).eq('source_id', source.source_id)
    if (error) onError(error.message)
    else { setEditingSource(false); await onRefresh() }
  }

  return (
    <div className="detail-scroll">
      <div className="detail-hero">
        <div className="detail-meta-row"><BucketPill bucket={source.review_bucket} /><span className="status-pill">Historical seed record</span><span className="status-pill">{humanize(source.review_status)}</span></div>
        <h2>{source.title}</h2>
        <p className="authors">{asAuthorLine(source.authors)}</p>
        <div className="citation-line"><span>{source.venue ?? humanize(source.source_kind)}</span><span>•</span><span>{source.publication_date ?? source.publication_year ?? 'Date not extracted'}</span>{source.peer_review_status && <><span>•</span><span>{humanize(source.peer_review_status)}</span></>}</div>
        <div className="hero-actions">
          <a className="secondary-button" href={source.source_url} target="_blank" rel="noreferrer"><ExternalLink size={15} /> Open source</a>
          {source.doi && <span className="identifier">DOI {source.doi}</span>}
          {source.pmid && <span className="identifier">PMID {source.pmid}</span>}
        </div>
      </div>

      <DetailSection title="Review interpretation" icon={<Activity size={17} />} action={canEdit ? <button className="text-button" onClick={() => setEditingSource((v) => !v)}><Pencil size={14} /> {editingSource ? 'Cancel' : 'Edit'}</button> : null}>
        {editingSource ? (
          <div className="edit-stack">
            <label className="field-label">Review status</label>
            <select className="select-input" value={reviewStatus} onChange={(e) => setReviewStatus(e.target.value)}><option value="draft">Draft</option><option value="reviewing">Reviewing</option><option value="approved_seed">Approved seed</option><option value="approved_release">Approved release</option></select>
            <label className="field-label">Interpretive rationale</label>
            <textarea className="textarea" rows={5} value={routeRationale} onChange={(e) => setRouteRationale(e.target.value)} />
            <button className="primary-button fit" onClick={saveSource}><Save size={15} /> Save interpretation</button>
          </div>
        ) : (
          <>
            <p className="body-copy">{source.route_rationale || 'No interpretive rationale extracted.'}</p>
            <div className="record-note">The original Git release JSON remains the immutable seed snapshot. Canonical route/evidence-role semantics are reviewed separately above; Workbench edits modify the operational Postgres record and are audit-logged.</div>
          </>
        )}
      </DetailSection>

      <DetailSection title="Study & population" icon={<Users size={17} />}>
        {study ? <StudyCard study={study} canEdit={canEdit} onRefresh={onRefresh} onError={onError} /> : <EmptyLine>No normalized study row.</EmptyLine>}
      </DetailSection>

      <DetailSection title="Intervention / protocol" icon={<FlaskConical size={17} />}>
        {components.length ? components.map((c) => <ComponentCard key={c.component_id} component={c} canEdit={canEdit} onRefresh={onRefresh} onError={onError} />) : <EmptyLine>This record informs mechanism, measurement or activity-system design rather than containing a normalized intervention component.</EmptyLine>}
      </DetailSection>

      <DetailSection title={`Outcomes & transfer (${outcomes.length})`} icon={<ClipboardCheck size={17} />}>
        <div className="stack-list">{outcomes.map((o) => <OutcomeCard key={o.outcome_id} outcome={o} canEdit={canEdit} onRefresh={onRefresh} onError={onError} />)}</div>
      </DetailSection>

      <DetailSection title="IQM / H-AGI relevance" icon={<Sparkles size={17} />}>
        <div className="stack-list">{products.map((p) => <ProductCard key={p.product_relevance_id} item={p} canEdit={canEdit} onRefresh={onRefresh} onError={onError} />)}</div>
      </DetailSection>

      <DetailSection title="Quality appraisal" icon={<ShieldCheck size={17} />} action={canEdit ? <button className="text-button" onClick={() => setQualityOpen((v) => !v)}><Plus size={14} /> Add appraisal</button> : null}>
        {qualityOpen && <QualityForm sourceId={source.source_id} onDone={async () => { setQualityOpen(false); await onRefresh() }} onError={onError} />}
        {quality.length ? quality.map((q) => <div className="quality-row" key={q.quality_assessment_id}><div><strong>{q.tool}</strong><span>{humanize(q.assessment_level)}</span></div><div className="quality-judgement">{q.judgement ?? 'Pending judgement'}</div><p>{q.notes}</p></div>) : <EmptyLine>No formal RoB/reporting appraisal recorded yet.</EmptyLine>}
      </DetailSection>
    </div>
  )
}

function StudyCard({ study, canEdit, onRefresh, onError }: { study: Study; canEdit: boolean; onRefresh: () => Promise<void>; onError: (v: string | null) => void }) {
  const [edit, setEdit] = useState(false)
  const [form, setForm] = useState({ design: study.design ?? '', population_summary: study.population_summary ?? '', setting: study.setting ?? '' })
  useEffect(() => setForm({ design: study.design ?? '', population_summary: study.population_summary ?? '', setting: study.setting ?? '' }), [study.study_id])
  async function save() {
    const { error } = await supabase.from('study').update(form).eq('study_id', study.study_id)
    if (error) onError(error.message); else { setEdit(false); await onRefresh() }
  }
  if (edit) return <div className="edit-stack subedit"><EditInput label="Design" value={form.design} onChange={(v) => setForm({ ...form, design: v })} /><EditInput label="Population" value={form.population_summary} onChange={(v) => setForm({ ...form, population_summary: v })} /><EditInput label="Setting" value={form.setting} onChange={(v) => setForm({ ...form, setting: v })} /><div className="record-note">Historical comparator summary is preserved as compatibility metadata. Review canonical arms, conditions and contrasts in the Stage 5 section above.</div><div className="edit-actions"><button className="primary-button fit" onClick={save}><Save size={14} /> Save</button><button className="secondary-button fit" onClick={() => setEdit(false)}>Cancel</button></div></div>
  return (
    <div className="info-grid">
      <Info label="Design" value={study.design} />
      <Info label="Population" value={study.population_summary} />
      <Info label="Setting" value={study.setting} />
      <Info label="Historical comparator summary" value={study.comparator_summary} />
      <Info label="Sample" value={compactJson(study.sample_json)} />
      <Info label="Population tags" value={study.population_tags?.map(humanize).join(', ')} />
      {canEdit && <button className="text-button edit-link" onClick={() => setEdit(true)}><Pencil size={14} /> Edit study fields</button>}
    </div>
  )
}

function ComponentCard({ component, canEdit, onRefresh, onError }: { component: Component; canEdit: boolean; onRefresh: () => Promise<void>; onError: (v: string | null) => void }) {
  const [edit, setEdit] = useState(false)
  const [form, setForm] = useState({ route: component.route, target_summary: component.target_summary ?? '', method_summary: component.method_summary ?? '', sessions_min: component.sessions_min?.toString() ?? '', session_minutes_min: component.session_minutes_min?.toString() ?? '', weeks_min: component.weeks_min?.toString() ?? '' })
  async function save() {
    const payload = { route: form.route, target_summary: form.target_summary || null, method_summary: form.method_summary || null, sessions_min: form.sessions_min ? Number(form.sessions_min) : null, session_minutes_min: form.session_minutes_min ? Number(form.session_minutes_min) : null, weeks_min: form.weeks_min ? Number(form.weeks_min) : null }
    const { error } = await supabase.from('intervention_component').update(payload).eq('component_id', component.component_id)
    if (error) onError(error.message); else { setEdit(false); await onRefresh() }
  }
  return (
    <div className="protocol-card">
      <div className="protocol-head"><div><strong>{component.component_name}</strong><RoutePill route={component.route} /></div>{canEdit && <button className="text-button" onClick={() => setEdit((v) => !v)}><Pencil size={14} /> {edit ? 'Cancel' : 'Edit'}</button>}</div>
      {edit ? <div className="edit-stack subedit"><label className="field-label">Route</label><select className="select-input" value={form.route} onChange={(e) => setForm({ ...form, route: e.target.value })}>{routeOptions.map((r) => <option key={r} value={r}>{humanize(r)}</option>)}</select><EditInput label="Target" value={form.target_summary} onChange={(v) => setForm({ ...form, target_summary: v })} /><EditInput label="Method" value={form.method_summary} onChange={(v) => setForm({ ...form, method_summary: v })} /><div className="triple-fields"><EditInput label="Sessions" type="number" value={form.sessions_min} onChange={(v) => setForm({ ...form, sessions_min: v })} /><EditInput label="Minutes/session" type="number" value={form.session_minutes_min} onChange={(v) => setForm({ ...form, session_minutes_min: v })} /><EditInput label="Weeks" type="number" value={form.weeks_min} onChange={(v) => setForm({ ...form, weeks_min: v })} /></div><button className="primary-button fit" onClick={save}><Save size={14} /> Save component</button></div> : <div className="protocol-body"><Info label="Target" value={component.target_summary} /><Info label="Method" value={component.method_summary || compactJson(component.protocol_json)} /><div className="dose-row"><Dose label="Sessions" value={component.sessions_min} max={component.sessions_max} /><Dose label="Minutes" value={component.session_minutes_min} max={component.session_minutes_max} /><Dose label="Weeks" value={component.weeks_min} max={component.weeks_max} /><Dose label="Frequency/wk" value={component.frequency_per_week_min} max={component.frequency_per_week_max} /></div></div>}
    </div>
  )
}

function OutcomeCard({ outcome, canEdit, onRefresh, onError }: { outcome: Outcome; canEdit: boolean; onRefresh: () => Promise<void>; onError: (v: string | null) => void }) {
  const [edit, setEdit] = useState(false)
  const [form, setForm] = useState({ outcome_name: outcome.outcome_name, result_direction: outcome.result_direction ?? '', result_summary: outcome.result_summary ?? '' })
  async function save() {
    const { error } = await supabase.from('evidence_outcome').update({ ...form, result_direction: form.result_direction || null, result_summary: form.result_summary || null }).eq('outcome_id', outcome.outcome_id)
    if (error) onError(error.message); else { setEdit(false); await onRefresh() }
  }
  return (
    <div className="outcome-card">
      <div className="outcome-head"><div><strong>{outcome.outcome_name}</strong><span className="rung-pill">Legacy: {humanize(outcome.evidence_rung)}</span></div>{canEdit && <button className="icon-button mini" onClick={() => setEdit((v) => !v)}><Pencil size={13} /></button>}</div>
      {edit ? <div className="edit-stack subedit"><EditInput label="Outcome" value={form.outcome_name} onChange={(v) => setForm({ ...form, outcome_name: v })} /><div className="record-note">Legacy evidence rung and raw timepoint are preserved as historical compatibility metadata. Review outcome distance, timing, transfer, role and Bridge evidence in the Stage 4 review section.</div><EditInput label="Direction" value={form.result_direction} onChange={(v) => setForm({ ...form, result_direction: v })} /><label className="field-label">Result summary</label><textarea className="textarea" rows={3} value={form.result_summary} onChange={(e) => setForm({ ...form, result_summary: e.target.value })} /><button className="primary-button fit" onClick={save}><Save size={14} /> Save outcome</button></div> : <><div className="outcome-grid"><Info label="Raw historical timepoint" value={outcome.timepoint} /><Info label="Direction" value={humanize(outcome.result_direction)} /><Info label="Measure" value={outcome.measure_name} /><Info label="Transfer" value={outcome.transfer_axes?.map(humanize).join(', ') || 'Not separately coded'} /></div>{outcome.result_summary && <p className="small-copy">{outcome.result_summary}</p>}{outcome.effect_estimate != null && <div className="effect-line">Historical quantitative compatibility — {outcome.effect_metric ?? 'Effect'}: <strong>{outcome.effect_estimate}</strong>{outcome.ci_lower != null && outcome.ci_upper != null ? ` (${outcome.ci_lower} to ${outcome.ci_upper})` : ''}</div>}</>}
    </div>
  )
}

function ProductCard({ item, canEdit, onRefresh, onError }: { item: ProductRelevance; canEdit: boolean; onRefresh: () => Promise<void>; onError: (v: string | null) => void }) {
  const [edit, setEdit] = useState(false)
  const [form, setForm] = useState({ product: item.product, support_scope: item.support_scope ?? '', match_level: item.match_level ?? '', direction: item.direction ?? '', claim_status: item.claim_status ?? '', rationale: item.rationale ?? '' })
  async function save() {
    const { error } = await supabase.from('product_relevance').update(form).eq('product_relevance_id', item.product_relevance_id)
    if (error) onError(error.message); else { setEdit(false); await onRefresh() }
  }
  return <div className="product-card"><div className="product-head"><div><span className="product-name">{humanize(item.product)}</span><span className="match-pill">{humanize(item.match_level)}</span></div>{canEdit && <button className="icon-button mini" onClick={() => setEdit((v) => !v)}><Pencil size={13} /></button>}</div>{edit ? <div className="edit-stack subedit"><EditInput label="Product" value={form.product} onChange={(v) => setForm({ ...form, product: v })} /><EditInput label="Support scope" value={form.support_scope} onChange={(v) => setForm({ ...form, support_scope: v })} /><EditInput label="Match" value={form.match_level} onChange={(v) => setForm({ ...form, match_level: v })} /><EditInput label="Direction" value={form.direction} onChange={(v) => setForm({ ...form, direction: v })} /><EditInput label="Claim status" value={form.claim_status} onChange={(v) => setForm({ ...form, claim_status: v })} /><button className="primary-button fit" onClick={save}><Save size={14} /> Save relevance</button></div> : <><div className="product-meta"><span>{humanize(item.support_scope)}</span><span>{humanize(item.direction)}</span><span>{humanize(item.claim_status)}</span></div>{item.rationale && <p>{item.rationale}</p>}</>}</div>
}

function QualityForm({ sourceId, onDone, onError }: { sourceId: string; onDone: () => Promise<void>; onError: (v: string | null) => void }) {
  const [form, setForm] = useState({ assessment_level: 'study', tool: 'RoB 2', judgement: '', notes: '', assessor: '' })
  async function save() {
    const { error } = await supabase.from('quality_assessment').insert({ source_id: sourceId, ...form, assessed_on: new Date().toISOString().slice(0, 10) })
    if (error) onError(error.message); else await onDone()
  }
  return <div className="quality-form"><div className="two-fields"><label><span className="field-label">Level</span><select className="select-input" value={form.assessment_level} onChange={(e) => setForm({ ...form, assessment_level: e.target.value })}><option value="study">Study</option><option value="outcome">Outcome</option><option value="reporting">Reporting</option><option value="body_of_evidence">Body of evidence</option></select></label><EditInput label="Tool" value={form.tool} onChange={(v) => setForm({ ...form, tool: v })} /></div><div className="two-fields"><EditInput label="Judgement" value={form.judgement} onChange={(v) => setForm({ ...form, judgement: v })} /><EditInput label="Assessor" value={form.assessor} onChange={(v) => setForm({ ...form, assessor: v })} /></div><label className="field-label">Notes</label><textarea className="textarea" rows={3} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} /><button className="primary-button fit" onClick={save}><Save size={14} /> Save appraisal</button></div>
}
