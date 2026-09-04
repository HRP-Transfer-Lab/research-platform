const SUPABASE_URL = 'https://dkntitdzgeemvyukfmhs.supabase.co'
const SUPABASE_PUBLISHABLE_KEY = 'sb_publishable_6c2ViStJuEb7TiKTBfRJmw_krtfvtBu'
const TABLE = 'hrp_evidence_gateway_demo'

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

export async function fetchGatewayEvidence(signal) {
  const url = new URL(`${SUPABASE_URL}/rest/v1/${TABLE}`)
  url.searchParams.set('select', SELECT_FIELDS)
  url.searchParams.set('order', 'publication_date.desc.nullslast,publication_year.desc,title.asc')

  const response = await fetch(url, {
    method: 'GET',
    headers: {
      apikey: SUPABASE_PUBLISHABLE_KEY,
      Accept: 'application/json',
    },
    signal,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`Evidence Gateway request failed (${response.status}): ${detail}`)
  }

  const rows = await response.json()
  if (!Array.isArray(rows)) throw new Error('Evidence Gateway returned an unexpected response.')
  return rows.map(normaliseRecord)
}

export function normaliseRecord(row) {
  return {
    ...row,
    domains: Array.isArray(row.domains) ? row.domains : [],
    publication_year: row.publication_year == null ? null : Number(row.publication_year),
  }
}

export const gatewayDemoContract = Object.freeze({
  mode: 'demo',
  table: TABLE,
  release: 'hrp-evidence-gateway-demo-2026-09-04',
  claimsSafe: false,
  includesProvisionalEvidence: true,
})
