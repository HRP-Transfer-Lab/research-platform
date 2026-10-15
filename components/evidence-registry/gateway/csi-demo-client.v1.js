const SUPABASE_URL = 'https://dkntitdzgeemvyukfmhs.supabase.co'
const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_6c2ViStJuEb7TiKTBfRJmw_krtfvtBu'
const DEMO_TABLE = 'hrp_evidence_gateway_demo'
const PUBLIC_GATEWAY_ORIGIN = 'https://hrp-evidence-gateway-demo.mark-ashton-smith.workers.dev'

const SELECT_FIELDS = [
  'source_id',
  'title',
  'publication_date',
  'publication_year',
  'venue',
  'doi',
  'pmid',
  'source_url',
  'evidence_status',
  'authority',
  'review_status',
  'review_bucket',
  'paper_role',
  'study_design',
  'primary_domain',
  'domains',
  'health_scope',
  'priority',
  'evidence_note',
  'snapshot_release',
].join(',')

export const csiDemoEvidenceContract = Object.freeze({
  contract_version: 'csi-evidence-demo-query-v1',
  mode: 'demo',
  source_relation: `public.${DEMO_TABLE}`,
  claims_safe: false,
  includes_provisional_evidence: true,
  production_relation: 'public.v_csi_gateway_evidence_v1',
})

function normalise(row) {
  return {
    ...row,
    domains: Array.isArray(row.domains) ? row.domains : [],
    publication_year: row.publication_year == null ? null : Number(row.publication_year),
  }
}

async function fetchAll(signal) {
  const url = new URL(`${SUPABASE_URL}/rest/v1/${DEMO_TABLE}`)
  url.searchParams.set('select', SELECT_FIELDS)
  url.searchParams.set('order', 'publication_date.desc.nullslast,publication_year.desc,title.asc')

  const response = await fetch(url, {
    headers: {
      apikey: SUPABASE_PUBLISHABLE_KEY,
      Accept: 'application/json',
    },
    signal,
  })

  if (!response.ok) {
    throw new Error(`CSI demo evidence request failed (${response.status}): ${await response.text()}`)
  }

  const rows = await response.json()
  if (!Array.isArray(rows)) throw new Error('CSI demo evidence response was not an array')
  return rows.map(normalise)
}

function matchesDomain(record, domain) {
  if (!domain || domain === 'all') return true
  return record.primary_domain === domain || record.domains.includes(domain)
}

function matchesText(record, q) {
  if (!q) return true
  const query = q.trim().toLowerCase()
  if (!query) return true
  return [
    record.title,
    record.venue,
    record.doi,
    record.pmid,
    record.evidence_note,
    record.paper_role,
    record.study_design,
    record.primary_domain,
    ...record.domains,
  ].filter(Boolean).join(' ').toLowerCase().includes(query)
}

function score(record) {
  const status = record.evidence_status === 'approved' ? 50 : record.evidence_status === 'provisional' ? 20 : -100
  const priority = record.priority === 'high' ? 20 : record.priority === 'medium' ? 8 : 0
  const role = record.paper_role === 'evidence_synthesis' ? 12 : record.paper_role === 'direct_intervention' ? 10 : record.paper_role === 'mechanism' ? 5 : 2
  const recency = Math.max(0, (record.publication_year || 2020) - 2020)
  return status + priority + role + recency
}

export async function queryCsiDemoEvidence(query = {}, { signal } = {}) {
  const {
    domain = 'all',
    q = '',
    statuses = ['approved', 'provisional'],
    roles = [],
    priorities = [],
    source_ids = [],
    limit = 12,
  } = query

  const rows = await fetchAll(signal)
  const sourceOrder = new Map(source_ids.map((id, index) => [id, index]))

  const filtered = rows.filter((record) => {
    if (record.evidence_status === 'excluded') return false
    if (statuses.length && !statuses.includes(record.evidence_status)) return false
    if (!matchesDomain(record, domain)) return false
    if (roles.length && !roles.includes(record.paper_role)) return false
    if (priorities.length && !priorities.includes(record.priority)) return false
    if (source_ids.length && !sourceOrder.has(record.source_id)) return false
    return matchesText(record, q)
  })

  filtered.sort((a, b) => {
    if (source_ids.length) return (sourceOrder.get(a.source_id) ?? 9999) - (sourceOrder.get(b.source_id) ?? 9999)
    return score(b) - score(a) || String(b.publication_date || b.publication_year || '').localeCompare(String(a.publication_date || a.publication_year || ''))
  })

  const evidence = filtered.slice(0, Math.max(1, Number(limit) || 12))

  return {
    contract_version: csiDemoEvidenceContract.contract_version,
    mode: 'demo',
    query: {
      domain,
      q,
      statuses,
      roles,
      priorities,
      source_ids,
      limit,
    },
    evidence,
    governance: {
      claims_safe: false,
      provisional_evidence_may_be_present: evidence.some((item) => item.evidence_status === 'provisional'),
      production_claims_require_approved_gateway: true,
      production_relation: csiDemoEvidenceContract.production_relation,
    },
  }
}

export function buildGatewayDeepLink(query = {}) {
  const url = new URL(PUBLIC_GATEWAY_ORIGIN)
  if (query.scenario) url.searchParams.set('scenario', query.scenario)
  if (query.domain && query.domain !== 'all') url.searchParams.set('domain', query.domain)
  if (query.q) url.searchParams.set('q', query.q)
  if (query.status && query.status !== 'all') url.searchParams.set('status', query.status)
  if (query.role && query.role !== 'all') url.searchParams.set('role', query.role)
  if (query.priority && query.priority !== 'all') url.searchParams.set('priority', query.priority)
  if (query.sort && query.sort !== 'newest') url.searchParams.set('sort', query.sort)
  return url.toString()
}

export function buildEvidenceCitation(record) {
  return {
    source_id: record.source_id,
    title: record.title,
    year: record.publication_year,
    evidence_status: record.evidence_status,
    paper_role: record.paper_role,
    primary_domain: record.primary_domain,
    source_url: record.source_url,
  }
}
