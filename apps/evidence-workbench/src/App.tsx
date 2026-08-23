import { useEffect, useMemo, useState } from 'react'
import { Activity, Archive, BookOpen, CheckCircle2, ChevronRight, ClipboardCheck, Database, FileSearch, Filter, FlaskConical, LogOut, RefreshCw, Search, ShieldCheck, Sparkles, Users, X } from 'lucide-react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from './lib/supabase'
import { LoginScreen, PendingAccess } from './AuthViews'
import { SourceDetail } from './SourceDetail'
import { AccessPage, AuditPage, ReleasesPage } from './WorkbenchPages'
import { BucketPill, CenteredLoader, Metric, NavButton, RoutePill, SelectField } from './WorkbenchUi'
import { emptyData, humanize, primaryClassification, routeOptions, type AuditRow, type Component, type EvidenceSource, type Outcome, type ProductRelevance, type QualityAssessment, type RegistryData, type Release, type Study, type Tab, type WorkbenchMember } from './workbench'

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [authReady, setAuthReady] = useState(false)
  const [member, setMember] = useState<WorkbenchMember | null>(null)
  const [memberChecked, setMemberChecked] = useState(false)
  const [data, setData] = useState<RegistryData>(emptyData)
  const [audit, setAudit] = useState<AuditRow[]>([])
  const [members, setMembers] = useState<WorkbenchMember[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('library')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [bucket, setBucket] = useState('all')
  const [route, setRoute] = useState('all')
  const [product, setProduct] = useState('all')

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setAuthReady(true)
    })
    const { data: sub } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next)
      setMember(null)
      setMemberChecked(false)
      if (!next) setData(emptyData)
    })
    return () => sub.subscription.unsubscribe()
  }, [])

  useEffect(() => {
    if (!session) return
    checkMembership(session.user.id)
  }, [session])

  useEffect(() => {
    if (!member) return
    loadRegistry()
  }, [member?.user_id])

  async function checkMembership(userId: string) {
    setMemberChecked(false)
    const { data: row, error: accessError } = await supabase
      .from('workbench_member')
      .select('user_id,role,active,display_name,created_at')
      .eq('user_id', userId)
      .maybeSingle()
    if (accessError) {
      setError(accessError.message)
      setMember(null)
    } else {
      setMember((row as WorkbenchMember | null) ?? null)
    }
    setMemberChecked(true)
  }

  async function loadRegistry() {
    setLoading(true)
    setError(null)
    const [sources, studies, components, outcomes, products, quality, releases] = await Promise.all([
      supabase.from('evidence_source').select('*').order('publication_date', { ascending: false, nullsFirst: false }),
      supabase.from('study').select('*'),
      supabase.from('intervention_component').select('*').order('component_id'),
      supabase.from('evidence_outcome').select('*').order('outcome_id'),
      supabase.from('product_relevance').select('*').order('product_relevance_id'),
      supabase.from('quality_assessment').select('*').order('quality_assessment_id'),
      supabase.from('evidence_release').select('*').order('released_on', { ascending: false }),
    ])
    const firstError = [sources, studies, components, outcomes, products, quality, releases].find((r) => r.error)?.error
    if (firstError) {
      setError(firstError.message)
    } else {
      const next: RegistryData = {
        sources: (sources.data ?? []) as EvidenceSource[],
        studies: (studies.data ?? []) as Study[],
        components: (components.data ?? []) as Component[],
        outcomes: (outcomes.data ?? []) as Outcome[],
        products: (products.data ?? []) as ProductRelevance[],
        quality: (quality.data ?? []) as QualityAssessment[],
        releases: (releases.data ?? []) as Release[],
      }
      setData(next)
      setSelectedId((current) => current ?? next.sources[0]?.source_id ?? null)
    }
    setLoading(false)
  }

  async function loadAudit() {
    const { data: rows, error: auditError } = await supabase
      .from('workbench_audit_log')
      .select('*')
      .order('occurred_at', { ascending: false })
      .limit(100)
    if (auditError) setError(auditError.message)
    else setAudit((rows ?? []) as AuditRow[])
  }

  async function loadMembers() {
    const { data: rows, error: membersError } = await supabase
      .from('workbench_member')
      .select('user_id,role,active,display_name,created_at')
      .order('created_at')
    if (membersError) setError(membersError.message)
    else setMembers((rows ?? []) as WorkbenchMember[])
  }

  function switchTab(next: Tab) {
    setTab(next)
    if (next === 'audit') void loadAudit()
    if (next === 'access') void loadMembers()
  }

  const productsAvailable = useMemo(
    () => Array.from(new Set(data.products.map((p) => p.product))).sort(),
    [data.products],
  )

  const filteredSources = useMemo(() => {
    const q = search.trim().toLowerCase()
    return data.sources.filter((source) => {
      const study = data.studies.find((s) => s.source_id === source.source_id)
      const studyComponents = data.components.filter((c) => c.study_id === study?.study_id)
      const sourceProducts = data.products.filter((p) => p.source_id === source.source_id)
      const tags = source.raw_record?.tags ?? []
      const haystack = [
        source.title,
        source.venue,
        source.route_rationale,
        primaryClassification(source),
        ...(study?.population_tags ?? []),
        ...(Array.isArray(tags) ? tags : []),
        ...sourceProducts.map((p) => p.product),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      const matchesSearch = !q || haystack.includes(q)
      const matchesBucket = bucket === 'all' || source.review_bucket === bucket
      const matchesRoute =
        route === 'all' ||
        primaryClassification(source).includes(route) ||
        studyComponents.some((c) => c.route === route || c.secondary_route === route)
      const matchesProduct = product === 'all' || sourceProducts.some((p) => p.product === product)
      return matchesSearch && matchesBucket && matchesRoute && matchesProduct
    })
  }, [data, search, bucket, route, product])

  if (!authReady) return <CenteredLoader label="Checking secure session…" />
  if (!session) return <LoginScreen />
  if (!memberChecked) return <CenteredLoader label="Checking Workbench access…" />
  if (!member) return <PendingAccess session={session} onRetry={() => checkMembership(session.user.id)} />

  const canEdit = member.role === 'editor' || member.role === 'owner'
  const isOwner = member.role === 'owner'
  const selected = data.sources.find((s) => s.source_id === selectedId) ?? null

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <div className="brand-mark"><FlaskConical size={21} /></div>
          <div>
            <div className="eyebrow">HRP TRANSFER LAB</div>
            <h1>Evidence Workbench</h1>
          </div>
        </div>
        <nav className="topnav" aria-label="Workbench sections">
          <NavButton active={tab === 'library'} onClick={() => switchTab('library')} icon={<BookOpen size={16} />} label="Evidence" />
          <NavButton active={tab === 'releases'} onClick={() => switchTab('releases')} icon={<Archive size={16} />} label="Releases" />
          {canEdit && <NavButton active={tab === 'audit'} onClick={() => switchTab('audit')} icon={<Activity size={16} />} label="Audit" />}
          {isOwner && <NavButton active={tab === 'access'} onClick={() => switchTab('access')} icon={<Users size={16} />} label="Access" />}
        </nav>
        <div className="account-block">
          <span className={`role-badge role-${member.role}`}>{member.role}</span>
          <span className="account-email">{session.user.email ?? member.display_name ?? 'Authenticated reviewer'}</span>
          <button className="icon-button" title="Sign out" onClick={() => supabase.auth.signOut()}><LogOut size={17} /></button>
        </div>
      </header>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={() => setError(null)}><X size={16} /></button>
        </div>
      )}

      {tab === 'library' && (
        <main className="library-page">
          <section className="metrics-row">
            <Metric icon={<Database size={18} />} label="Reviewed sources" value={data.sources.length} />
            <Metric icon={<ClipboardCheck size={18} />} label="Direct interventions" value={data.sources.filter((s) => s.review_bucket.startsWith('A_')).length} />
            <Metric icon={<Sparkles size={18} />} label="Mechanism / measurement" value={data.sources.filter((s) => s.review_bucket.startsWith('B_')).length} />
            <Metric icon={<FileSearch size={18} />} label="Outcomes coded" value={data.outcomes.length} />
            <Metric icon={<ShieldCheck size={18} />} label="Current release" value={data.releases[0]?.release_id ?? '—'} compact />
          </section>

          <section className="workbench-grid">
            <aside className="filter-panel">
              <div className="panel-title"><Filter size={16} /> Evidence filters</div>
              <label className="field-label">Search</label>
              <div className="search-box"><Search size={15} /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Title, target, population…" /></div>
              <SelectField label="Evidence class" value={bucket} onChange={setBucket} options={[
                ['all', 'All evidence'],
                ['A_direct_intervention', 'Direct intervention'],
                ['B_measurement_mechanism', 'Mechanism / measurement'],
                ['C_human_ai_activity_system', 'Human–AI / activity system'],
              ]} />
              <SelectField label="Route / classification" value={route} onChange={setRoute} options={[["all", "All routes"], ...routeOptions.map((r) => [r, humanize(r)] as [string, string])]} />
              <SelectField label="Product relevance" value={product} onChange={setProduct} options={[["all", "All products"], ...productsAvailable.map((p) => [p, humanize(p)] as [string, string])]} />
              <button className="secondary-button full" onClick={() => { setSearch(''); setBucket('all'); setRoute('all'); setProduct('all') }}>Clear filters</button>
              <div className="filter-note">
                <ShieldCheck size={15} />
                <span>Product relevance means evidence can inform a product; it does not mean the product itself is validated.</span>
              </div>
            </aside>

            <section className="source-list-panel">
              <div className="list-heading">
                <div><strong>{filteredSources.length}</strong> sources</div>
                <button className="icon-button" title="Refresh" onClick={loadRegistry} disabled={loading}><RefreshCw className={loading ? 'spin' : ''} size={16} /></button>
              </div>
              <div className="source-list">
                {filteredSources.map((source) => (
                  <button key={source.source_id} className={`source-card ${selectedId === source.source_id ? 'selected' : ''}`} onClick={() => setSelectedId(source.source_id)}>
                    <div className="source-card-top">
                      <BucketPill bucket={source.review_bucket} />
                      <span className="source-date">{source.publication_date ?? source.publication_year ?? '—'}</span>
                    </div>
                    <h3>{source.title}</h3>
                    <p>{source.venue ?? humanize(source.source_kind)}</p>
                    <div className="source-card-bottom">
                      <RoutePill route={primaryClassification(source)} />
                      <ChevronRight size={15} />
                    </div>
                  </button>
                ))}
                {!loading && filteredSources.length === 0 && <div className="empty-state">No evidence matches these filters.</div>}
              </div>
            </section>

            <section className="detail-panel">
              {selected ? (
                <SourceDetail
                  source={selected}
                  data={data}
                  canEdit={canEdit}
                  onRefresh={loadRegistry}
                  onError={setError}
                />
              ) : (
                <div className="empty-detail"><BookOpen size={30} /><p>Select an evidence record.</p></div>
              )}
            </section>
          </section>
        </main>
      )}

      {tab === 'releases' && <ReleasesPage data={data} isOwner={isOwner} onRefresh={loadRegistry} onError={setError} />}
      {tab === 'audit' && canEdit && <AuditPage rows={audit} onRefresh={loadAudit} />}
      {tab === 'access' && isOwner && <AccessPage rows={members} currentUserId={session.user.id} onRefresh={loadMembers} onError={setError} />}
    </div>
  )
}

export default App
