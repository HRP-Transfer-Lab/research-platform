import { useMemo, useState } from 'react'
import { Archive, Clipboard, FileSearch, Plus, RefreshCw, Upload } from 'lucide-react'
import { supabase } from './lib/supabase'
import { humanize, type AuditRow, type RegistryData, type Release, type ResearchCandidate, type Role, type WorkbenchMember } from './workbench'
import { EditInput } from './WorkbenchUi'

export function ReleasesPage({ data, isOwner, onRefresh, onError }: { data: RegistryData; isOwner: boolean; onRefresh: () => Promise<void>; onError: (v: string | null) => void }) {
  async function changeStatus(release: Release, status: string) {
    const { error } = await supabase.from('evidence_release').update({ status }).eq('release_id', release.release_id)
    if (error) onError(error.message); else await onRefresh()
  }
  return <main className="wide-page"><div className="page-heading"><div className="eyebrow">VERSIONED EVIDENCE</div><h2>Evidence releases</h2><p>Production consumers should use approved, reproducible releases rather than draft literature records.</p></div><div className="release-grid">{data.releases.map((release) => { const count = data.sources.filter((s) => s.release_id === release.release_id).length; return <div className="release-card" key={release.release_id}><div className="release-card-head"><div><span className="release-id">{release.release_id}</span><span className="status-pill">{humanize(release.status)}</span></div><Archive size={22} /></div><div className="release-stats"><div><strong>{count}</strong><span>sources</span></div><div><strong>{release.schema_version}</strong><span>schema</span></div><div><strong>{release.taxonomy_version}</strong><span>taxonomy</span></div></div><p>{release.notes}</p><div className="release-source"><strong>Review source</strong><span>{release.source_review_document}</span><span>{release.source_review_section}</span></div>{isOwner && <label className="owner-status"><span className="field-label">Owner release status</span><select className="select-input" value={release.status} onChange={(e) => changeStatus(release, e.target.value)}><option value="draft">Draft</option><option value="approved_seed">Approved seed</option><option value="approved_release">Approved release</option><option value="retired">Retired</option></select></label>}</div>})}</div></main>
}

export function AuditPage({ rows, onRefresh }: { rows: AuditRow[]; onRefresh: () => void }) {
  return <main className="wide-page"><div className="page-heading with-action"><div><div className="eyebrow">PROVENANCE</div><h2>Workbench audit trail</h2><p>Latest browser-side mutations to scientific records and access roles.</p></div><button className="secondary-button" onClick={onRefresh}><RefreshCw size={15} /> Refresh</button></div><div className="audit-table"><div className="audit-header"><span>Time</span><span>Action</span><span>Table</span><span>Record</span><span>Actor</span></div>{rows.map((row) => { const record = row.after_row ?? row.before_row ?? {}; const identity = record.source_id ?? record.study_id ?? record.outcome_id ?? record.component_id ?? record.product_relevance_id ?? record.release_id ?? record.user_id ?? '—'; return <div className="audit-row" key={row.audit_id}><span>{new Date(row.occurred_at).toLocaleString()}</span><span><span className={`action-pill action-${row.action.toLowerCase()}`}>{row.action}</span></span><span>{humanize(row.table_name)}</span><span className="mono">{String(identity)}</span><span className="mono small-mono">{row.actor_user_id ?? 'service/admin'}</span></div>})}{rows.length === 0 && <div className="empty-state">No Workbench mutations recorded yet.</div>}</div></main>
}

export function AccessPage({ rows, currentUserId, onRefresh, onError }: { rows: WorkbenchMember[]; currentUserId: string; onRefresh: () => Promise<void>; onError: (v: string | null) => void }) {
  const [uid, setUid] = useState('')
  const [role, setRole] = useState<Role>('viewer')
  const [name, setName] = useState('')
  async function add() {
    const { error } = await supabase.from('workbench_member').insert({ user_id: uid.trim(), role, display_name: name.trim() || null, created_by: currentUserId })
    if (error) onError(error.message); else { setUid(''); setName(''); await onRefresh() }
  }
  async function change(userId: string, nextRole: Role, active: boolean) {
    const { error } = await supabase.from('workbench_member').update({ role: nextRole, active }).eq('user_id', userId)
    if (error) onError(error.message); else await onRefresh()
  }
  return <main className="wide-page"><div className="page-heading"><div className="eyebrow">OWNER CONTROL</div><h2>Workbench access</h2><p>Membership is explicit. Authentication without a row here cannot read Registry tables.</p></div><div className="access-layout"><section className="member-list"><h3>Members</h3>{rows.map((m) => <div className="member-row" key={m.user_id}><div className="member-avatar">{(m.display_name || 'R')[0].toUpperCase()}</div><div className="member-copy"><strong>{m.display_name || 'Reviewer'}</strong><code>{m.user_id}</code></div><select className="select-input compact-select" value={m.role} onChange={(e) => change(m.user_id, e.target.value as Role, m.active)}><option value="viewer">Viewer</option><option value="editor">Editor</option><option value="owner">Owner</option></select><label className="active-check"><input type="checkbox" checked={m.active} onChange={(e) => change(m.user_id, m.role, e.target.checked)} /> Active</label></div>)}</section><section className="add-member-card"><h3>Add member</h3><p>The person signs in once and sends you their Supabase user ID. No email address is required in this role table.</p><EditInput label="User UUID" value={uid} onChange={setUid} /><EditInput label="Display name (optional)" value={name} onChange={setName} /><label className="field-label">Role</label><select className="select-input" value={role} onChange={(e) => setRole(e.target.value as Role)}><option value="viewer">Viewer — read evidence</option><option value="editor">Editor — review/edit evidence</option><option value="owner">Owner — releases, claims & access</option></select><button className="primary-button full" disabled={!uid.trim()} onClick={add}><Plus size={15} /> Add member</button></section></div></main>
}


export function DiscoveryPage({
  rows,
  canEdit,
  currentUserId,
  onRefresh,
  onError,
}: {
  rows: ResearchCandidate[]
  canEdit: boolean
  currentUserId: string
  onRefresh: () => Promise<void>
  onError: (v: string | null) => void
}) {
  async function importQueue(file: File) {
    try {
      const parsed = JSON.parse(await file.text())
      const candidates = Array.isArray(parsed?.candidates) ? parsed.candidates : []
      if (!candidates.length) {
        onError('No candidates found in this scout queue file.')
        return
      }
      const payload = candidates.map((item: any) => ({
        candidate_id: item.candidate_id,
        source: item.source,
        title: item.title,
        identifiers: item.identifiers ?? {},
        published_raw: item.published ?? null,
        venue: item.venue ?? null,
        source_url: item.url ?? null,
        topic_family: item.topic_family,
        consumers: item.consumers ?? [],
        relevance_terms: item.relevance_terms ?? [],
        discovery_status: 'discovered_unscreened',
        claim_status: 'no_public_claim',
        exclusion_reason: null,
        raw_candidate: item,
        last_seen_at: new Date().toISOString(),
      }))
      const { error } = await supabase.from('research_candidate').upsert(payload, { onConflict: 'candidate_id' })
      if (error) onError(error.message)
      else await onRefresh()
    } catch (error) {
      onError(error instanceof Error ? error.message : String(error))
    }
  }

  async function setStatus(candidate: ResearchCandidate, discovery_status: ResearchCandidate['discovery_status']) {
    const payload: any = {
      discovery_status,
      screened_at: discovery_status === 'discovered_unscreened' ? null : new Date().toISOString(),
      screened_by: discovery_status === 'discovered_unscreened' ? null : currentUserId,
    }
    const { error } = await supabase.from('research_candidate').update(payload).eq('candidate_id', candidate.candidate_id)
    if (error) onError(error.message)
    else await onRefresh()
  }

  const unscreened = rows.filter((row) => row.discovery_status === 'discovered_unscreened').length
  const screening = rows.filter((row) => row.discovery_status === 'screening').length
  const included = rows.filter((row) => row.discovery_status === 'include_for_review').length

  return <main className="wide-page">
    <div className="page-heading with-action">
      <div>
        <div className="eyebrow">DISCOVERY · NOT YET EVIDENCE</div>
        <h2>Research discovery inbox</h2>
        <p>Scout candidates stay outside the Evidence Registry until they are screened, extracted, human-verified, appraised and released.</p>
      </div>
      {canEdit && <label className="secondary-button">
        <Upload size={15} /> Import scout queue
        <input type="file" accept="application/json,.json" hidden onChange={(event) => {
          const file = event.target.files?.[0]
          if (file) void importQueue(file)
          event.currentTarget.value = ''
        }} />
      </label>}
    </div>

    <section className="discovery-guide">
      <div className="discovery-guide-head">
        <div>
          <div className="eyebrow">HOW TO USE THIS INBOX</div>
          <h3>Scout → import → screen → full evidence review</h3>
        </div>
        <div className="discovery-counts">
          <span><strong>{unscreened}</strong> unscreened</span>
          <span><strong>{screening}</strong> screening</span>
          <span><strong>{included}</strong> included for review</span>
        </div>
      </div>
      <div className="discovery-steps">
        <div className="discovery-step"><strong>1 · Run the scout</strong><span>From the research-platform repo:</span><code>python3 components/research-intel-agents/research_scout.py scan</code></div>
        <div className="discovery-step"><strong>2 · Import the queue</strong><span>Click <b>Import scout queue</b>. On Kastel Mini the file is:</span><code>~/hrp-lab/research-platform/.local/research-intel-agents/review-queue-latest.json</code><span>If the file picker opens in Desktop, press <b>Ctrl+L</b>, paste the path, then press Enter.</span></div>
        <div className="discovery-step"><strong>3 · Screen each paper</strong><span>Open the source and choose the most appropriate screening decision below.</span></div>
        <div className="discovery-step"><strong>4 · Keep the evidence boundary</strong><span><b>Include for review</b> only means “worth a full scientific review”. It does not create an Evidence Registry record or support a public claim.</span></div>
      </div>
      <div className="screening-key">
        <span><b>Unscreened</b> not assessed yet</span>
        <span><b>Screening</b> currently checking the source</span>
        <span><b>Include for review</b> relevant enough for extraction/appraisal</span>
        <span><b>Exclude</b> out of scope or not useful for this evidence question</span>
        <span><b>Duplicate</b> already represented elsewhere</span>
      </div>
    </section>

    <div className="release-grid">
      {rows.map((candidate) => <article className="release-card" key={candidate.candidate_id}>
        <div className="release-card-head">
          <div><span className="release-id">{candidate.source}</span><span className="status-pill">{humanize(candidate.discovery_status)}</span></div>
          <FileSearch size={22} />
        </div>
        <h3>{candidate.title}</h3>
        <p>{candidate.venue ?? humanize(candidate.topic_family)}</p>
        <div className="release-source">
          <strong>{humanize(candidate.topic_family)}</strong>
          <span>{candidate.relevance_terms.join(', ') || 'No relevance terms recorded'}</span>
          <span>Consumers: {candidate.consumers.join(', ') || 'Not assigned'}</span>
        </div>
        {candidate.source_url && <p><a href={candidate.source_url} target="_blank" rel="noreferrer">Open source ↗</a></p>}
        <div className="record-note"><strong>Claim boundary:</strong> discovery metadata only — no public claim.</div>
        {canEdit && <label className="owner-status">
          <span className="field-label">Screening decision</span>
          <select className="select-input" value={candidate.discovery_status} onChange={(event) => void setStatus(candidate, event.target.value as ResearchCandidate['discovery_status'])}>
            <option value="discovered_unscreened">Unscreened</option>
            <option value="screening">Screening</option>
            <option value="include_for_review">Include for review</option>
            <option value="exclude">Exclude</option>
            <option value="duplicate">Duplicate</option>
          </select>
        </label>}
      </article>)}
      {rows.length === 0 && <div className="empty-state">No discovery candidates imported yet.</div>}
    </div>
  </main>
}


const contentBriefTopics = [
  {
    id: 'attention_control',
    label: 'Attention Control',
    stream: 'SYNERGY_IQ',
    terms: ['attention control','attentional control','executive attention','cognitive control','inhibitory control','interference control','executive function'],
  },
  {
    id: 'relational_memory',
    label: 'Relational Memory',
    stream: 'SYNERGY_IQ',
    terms: ['relational memory','relational integration','relational reasoning','associative memory','episodic memory','cognitive map'],
  },
  {
    id: 'binding_memory',
    label: 'Binding Memory',
    stream: 'SYNERGY_IQ',
    terms: ['memory binding','working memory binding','feature binding','relational binding','associative binding'],
  },
  {
    id: 'path_horizon',
    label: 'Path Horizon',
    stream: 'SYNERGY_IQ',
    terms: ['planning horizon','prospective planning','multi-step planning','graph reasoning','lookahead','planning depth','prospective memory'],
  },
  {
    id: 'knowledge_access',
    label: 'Knowledge Access',
    stream: 'SYNERGY_IQ',
    terms: ['crystallized intelligence','crystallised intelligence','semantic memory','semantic retrieval','knowledge retrieval','retrieval practice'],
  },
  {
    id: 'generative_search',
    label: 'Generative Search',
    stream: 'SYNERGY_IQ',
    terms: ['divergent thinking','idea generation','hypothesis generation','creative ideation','creative thinking'],
  },
  {
    id: 'reasoning',
    label: 'Reasoning',
    stream: 'SYNERGY_IQ',
    terms: ['fluid intelligence','abstract reasoning','inductive reasoning','deductive reasoning','relational reasoning','reasoning training','clinical reasoning'],
  },
  {
    id: 'transfer_mutualism',
    label: 'Transfer & Mutualism',
    stream: 'SYNERGY_IQ',
    terms: ['far transfer','near transfer','cognitive transfer','general intelligence','positive manifold','mutualism','mutualistic','cognitive network'],
  },
  {
    id: 'human_ai',
    label: 'Human Intelligence × AI',
    stream: 'SYNERGY_IQ_AND_SWI',
    terms: ['cognitive offloading','human ai','human-ai','generative ai','critical thinking','automation bias','algorithmic reliance','ai-assisted','human judgement','human judgment'],
  },
  {
    id: 'swi_work',
    label: 'SWI Work Design',
    stream: 'SWI_BETA',
    terms: ['workload','work design','workplace interruption','role clarity','organisational change','organizational change','work intensification','employee autonomy','job demands','verification burden'],
  },
] as const

function normalise(value: unknown) {
  return String(value ?? '').toLowerCase().replaceAll('-', ' ').replace(/\s+/g, ' ').trim()
}

function evidenceHaystack(source: any, data: RegistryData) {
  const study = data.studies.find((item) => item.source_id === source.source_id)
  const components = data.components.filter((item) => item.study_id === study?.study_id)
  const outcomes = data.outcomes.filter((item) => item.study_id === study?.study_id)
  const products = data.products.filter((item) => item.source_id === source.source_id)
  const tags = Array.isArray(source.raw_record?.tags) ? source.raw_record.tags : []
  return normalise([
    source.title,
    source.venue,
    source.route_rationale,
    source.raw_record?.review?.primary_classification,
    ...tags,
    ...(study?.population_tags ?? []),
    study?.population_summary,
    ...components.flatMap((item) => [item.route, item.secondary_route, item.target_summary, item.method_summary]),
    ...outcomes.flatMap((item) => [item.outcome_name, item.functional_domain, item.result_summary, ...(item.transfer_axes ?? [])]),
    ...products.flatMap((item) => [item.product, item.support_scope, item.rationale]),
  ].filter(Boolean).join(' | '))
}

function matchScore(text: string, terms: readonly string[]) {
  return terms.reduce((score, term) => score + (text.includes(normalise(term)) ? 1 : 0), 0)
}

export function ContentBriefPage({
  data,
  candidates,
}: {
  data: RegistryData
  candidates: ResearchCandidate[]
}) {
  const [topicId, setTopicId] = useState<(typeof contentBriefTopics)[number]['id']>('attention_control')
  const [extraTerms, setExtraTerms] = useState('')
  const [copied, setCopied] = useState(false)

  const topic = contentBriefTopics.find((item) => item.id === topicId) ?? contentBriefTopics[0]
  const terms = useMemo(() => {
    const custom = extraTerms.split(',').map((item) => item.trim()).filter(Boolean)
    return [...topic.terms, ...custom]
  }, [topic, extraTerms])

  const matched = useMemo(() => {
    return data.sources
      .map((source) => ({ source, score: matchScore(evidenceHaystack(source, data), terms) }))
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score || String(b.source.publication_date ?? b.source.publication_year ?? '').localeCompare(String(a.source.publication_date ?? a.source.publication_year ?? '')))
  }, [data, terms])

  const approved = matched.filter(({ source }) => ['approved_seed','approved_release'].includes(source.review_status))
  const reviewing = matched.filter(({ source }) => !['approved_seed','approved_release'].includes(source.review_status))

  const recent = useMemo(() => {
    return candidates
      .map((candidate) => {
        const text = normalise([candidate.title, candidate.topic_family, ...(candidate.relevance_terms ?? [])].join(' | '))
        const score = candidate.topic_family === topic.id ? 5 + matchScore(text, terms) : matchScore(text, terms)
        return { candidate, score }
      })
      .filter((item) => item.score > 0 && !['exclude','duplicate'].includes(item.candidate.discovery_status))
      .sort((a, b) => b.score - a.score)
  }, [candidates, topic, terms])

  function sourceLine(source: any) {
    const date = source.publication_date ?? source.publication_year ?? 'date unknown'
    return `- ${source.title} — ${source.venue ?? source.source_kind} (${date}) [${source.review_status}]`
  }

  const briefText = useMemo(() => {
    const approvedLines = approved.slice(0, 12).map(({ source }) => sourceLine(source))
    const reviewLines = reviewing.slice(0, 20).map(({ source }) => sourceLine(source))
    const recentLines = recent.slice(0, 12).map(({ candidate }) => `- ${candidate.title} — ${candidate.source} [${candidate.discovery_status}; no public claim]`)
    return [
      `# HRP Evidence-to-Content Brief — ${topic.label}`,
      '',
      `Release stream: ${topic.stream}`,
      `Topic terms: ${terms.join(', ')}`,
      `Registry matches: ${matched.length} total · ${approved.length} approved · ${reviewing.length} reviewing`,
      `Recent discovery matches: ${recent.length}`,
      '',
      '## Approved evidence baseline',
      'These records may inform public evidence claims only within their reviewed scope, caveats and evidence maturity.',
      ...(approvedLines.length ? approvedLines : ['- No approved matching record found.']),
      '',
      '## Full review corpus',
      'Use these records to identify themes, mechanisms, tensions, counterevidence and papers worth checking. Do not silently treat them as approved claim support.',
      ...(reviewLines.length ? reviewLines : ['- No reviewing match found.']),
      '',
      '## Recent research delta',
      'Discovery signals are freshness/novelty inputs only until screened, extracted, verified and appraised.',
      ...(recentLines.length ? recentLines : ['- No current discovery match found.']),
      '',
      '## Content / claim boundary',
      '- Start from the whole relevant evidence landscape, not only recent publications.',
      '- Distinguish approved evidence from reviewing evidence and discovery signals in drafting.',
      '- Do not infer product efficacy, far transfer or IQ change from literature relevance alone.',
      '- Pair this evidence brief with Search Console intent/query evidence before deciding CREATE / MERGE / REFRESH / DERIVE / DO_NOT_CREATE.',
      '- Prefer refreshing an existing high-value IQ Mindware page before creating a competing page.',
    ].join('\n')
  }, [topic, terms, matched.length, approved, reviewing, recent])

  async function copyBrief() {
    await navigator.clipboard.writeText(briefText)
    setCopied(true)
    setTimeout(() => setCopied(false), 1600)
  }

  return <main className="wide-page">
    <div className="page-heading with-action">
      <div>
        <div className="eyebrow">EVIDENCE → RELEASE → SEO</div>
        <h2>Evidence-to-content brief</h2>
        <p>Use the whole relevant Registry as the scientific baseline, then layer on the recent scout delta. Status boundaries remain visible so reviewing papers do not silently become public evidence claims.</p>
      </div>
      <button className="secondary-button" onClick={() => void copyBrief()}><Clipboard size={15} /> {copied ? 'Copied' : 'Copy brief'}</button>
    </div>

    <section className="content-brief-controls">
      <label>
        <span className="field-label">Release / topic</span>
        <select className="select-input" value={topicId} onChange={(event) => setTopicId(event.target.value as (typeof contentBriefTopics)[number]['id'])}>
          {contentBriefTopics.map((item) => <option key={item.id} value={item.id}>{item.label} · {item.stream}</option>)}
        </select>
      </label>
      <label>
        <span className="field-label">Optional extra search terms</span>
        <input className="text-input" value={extraTerms} onChange={(event) => setExtraTerms(event.target.value)} placeholder="e.g. task switching, interruption, verification" />
      </label>
    </section>

    <section className="brief-summary-grid">
      <div className="brief-summary-card approved"><span>Approved baseline</span><strong>{approved.length}</strong><small>reviewed records that may support claims within their existing boundaries</small></div>
      <div className="brief-summary-card reviewing"><span>Review corpus</span><strong>{reviewing.length}</strong><small>use for themes, tensions and candidate evidence — not automatic claim support</small></div>
      <div className="brief-summary-card recent"><span>Recent delta</span><strong>{recent.length}</strong><small>new scout signals awaiting the normal review lifecycle</small></div>
      <div className="brief-summary-card total"><span>Total topic landscape</span><strong>{matched.length}</strong><small>matched Registry records before the recent discovery layer</small></div>
    </section>

    <section className="content-brief-grid">
      <div className="content-brief-panel">
        <div className="content-brief-panel-head"><div><div className="eyebrow">1 · BASELINE</div><h3>Approved evidence</h3></div><span>{approved.length}</span></div>
        <p className="content-brief-note">Use only within the record's reviewed population, design, route, outcome and claim caveats.</p>
        <div className="brief-source-list">
          {approved.slice(0, 12).map(({ source, score }) => <a key={source.source_id} className="brief-source" href={source.source_url} target="_blank" rel="noreferrer"><strong>{source.title}</strong><span>{source.venue ?? humanize(source.source_kind)} · match {score} · {humanize(source.review_status)}</span></a>)}
          {approved.length === 0 && <div className="empty-state">No approved Registry records matched this topic. Treat this as a claim-gap, not permission to use reviewing papers as substitutes.</div>}
        </div>
      </div>

      <div className="content-brief-panel">
        <div className="content-brief-panel-head"><div><div className="eyebrow">2 · LANDSCAPE</div><h3>Full review corpus</h3></div><span>{reviewing.length}</span></div>
        <p className="content-brief-note">Use to identify mechanisms, disagreements, boundary conditions and papers that deserve verification before publication.</p>
        <div className="brief-source-list">
          {reviewing.slice(0, 20).map(({ source, score }) => <a key={source.source_id} className="brief-source" href={source.source_url} target="_blank" rel="noreferrer"><strong>{source.title}</strong><span>{source.venue ?? humanize(source.source_kind)} · match {score} · {humanize(source.review_status)}</span></a>)}
          {reviewing.length === 0 && <div className="empty-state">No reviewing Registry records matched this topic.</div>}
        </div>
      </div>

      <div className="content-brief-panel">
        <div className="content-brief-panel-head"><div><div className="eyebrow">3 · DELTA</div><h3>Recent scout signals</h3></div><span>{recent.length}</span></div>
        <p className="content-brief-note">Freshness signal only. These candidates cannot support a public claim until they pass the Workbench review lifecycle.</p>
        <div className="brief-source-list">
          {recent.slice(0, 12).map(({ candidate }) => <a key={candidate.candidate_id} className="brief-source" href={candidate.source_url ?? '#'} target="_blank" rel="noreferrer"><strong>{candidate.title}</strong><span>{candidate.source} · {humanize(candidate.discovery_status)} · no public claim</span></a>)}
          {recent.length === 0 && <div className="empty-state">No recent scout candidates match this topic.</div>}
        </div>
      </div>
    </section>

    <section className="content-brief-boundary">
      <strong>How this feeds the release cycle</strong>
      <span>Whole Registry baseline → recent research delta → Search Console query/intent evidence → existing-page/cannibalisation check → evidence-led content brief → Problem → Science → Method → Product → release → +7/+14/+28 SEO learning.</span>
    </section>
  </main>
}
