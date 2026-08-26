export type Role = 'viewer' | 'editor' | 'owner'
export type Tab = 'library' | 'releases' | 'audit' | 'access'

export type WorkbenchMember = {
  user_id: string
  role: Role
  active: boolean
  display_name: string | null
  created_at: string
}

export type EvidenceSource = {
  source_id: string
  release_id: string
  review_bucket: string
  title: string
  authors: unknown
  publication_date: string | null
  publication_year: number | null
  venue: string | null
  source_kind: string
  peer_review_status: string | null
  doi: string | null
  pmid: string | null
  arxiv_id: string | null
  source_url: string
  review_status: string
  method_extraction_status: string
  route_rationale: string | null
  raw_record: any
}

export type Study = {
  study_id: number
  source_id: string
  design: string | null
  setting: string | null
  population_summary: string | null
  population_tags: string[]
  age_min: number | null
  age_max: number | null
  age_mean: number | null
  sample_json: any
  comparator_summary: string | null
  preregistered: boolean | null
  registration_id: string | null
}

export type Component = {
  component_id: number
  study_id: number
  component_name: string
  primary_route: boolean
  route: string
  secondary_route: string | null
  target_level: string | null
  target_summary: string | null
  method_summary: string | null
  provider: string | null
  delivery_mode: string | null
  setting: string | null
  sessions_min: number | null
  sessions_max: number | null
  session_minutes_min: number | null
  session_minutes_max: number | null
  weeks_min: number | null
  weeks_max: number | null
  frequency_per_week_min: number | null
  frequency_per_week_max: number | null
  tailoring: string | null
  fidelity: string | null
  prompt_status: string | null
  protocol_json: any
}

export type Outcome = {
  outcome_id: number
  study_id: number
  outcome_name: string
  measure_name: string | null
  functional_domain: string | null
  timepoint: string | null
  evidence_rung: string | null
  transfer_axes: string[]
  bridge_evidence_level: string | null
  result_direction: string | null
  result_summary: string | null
  effect_metric: string | null
  effect_estimate: number | null
  ci_lower: number | null
  ci_upper: number | null
  objective: boolean | null
  outcome_json: any
}

export type ProductRelevance = {
  product_relevance_id: number
  source_id: string
  product: string
  support_scope: string | null
  match_level: string | null
  direction: string | null
  claim_status: string | null
  rationale: string | null
}

export type QualityAssessment = {
  quality_assessment_id: number
  source_id: string
  assessment_level: string
  tool: string
  judgement: string | null
  notes: string | null
  assessed_on: string | null
  assessor: string | null
}

export type Release = {
  release_id: string
  released_on: string
  schema_version: string
  taxonomy_version: string
  source_review_document: string
  source_review_section: string | null
  source_window_start: string | null
  source_window_end: string | null
  status: string
  notes: string | null
}

export type SourceEvidenceRole = {
  source_id: string
  evidence_role: string
  primary_role: boolean
  rationale: string | null
  mapping_source: string
  created_at: string
  updated_at: string
}

export type SourceControllerOverlay = {
  source_controller_overlay_id: number
  source_id: string
  component_id: number | null
  controller_overlay: string
  rationale: string | null
  mapping_source: string
  created_at: string
  updated_at: string
}

export type AuditRow = {
  audit_id: number
  occurred_at: string
  actor_user_id: string | null
  table_name: string
  action: string
  before_row: any
  after_row: any
}

export type RegistryData = {
  sources: EvidenceSource[]
  studies: Study[]
  components: Component[]
  outcomes: Outcome[]
  products: ProductRelevance[]
  quality: QualityAssessment[]
  releases: Release[]
  evidenceRoles: SourceEvidenceRole[]
  controllerOverlays: SourceControllerOverlay[]
}

export const routeOptions = [
  'develop_equip',
  'develop_train',
  'develop_condition',
  'regulate',
  'bridge',
  'redesign',
  'integrate',
]

export const evidenceRoleOptions = [
  'direct_intervention',
  'mechanism',
  'measurement',
  'observational',
  'synthesis',
]

export const controllerOverlayOptions = [
  'metacognitive_governor',
  'adaptive_controller',
  'external_scaffold',
  'other_controller_or_overlay',
]

export const emptyData: RegistryData = {
  sources: [],
  studies: [],
  components: [],
  outcomes: [],
  products: [],
  quality: [],
  releases: [],
  evidenceRoles: [],
  controllerOverlays: [],
}

export function humanize(value?: string | null) {
  if (!value) return 'Not specified'
  return value.replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function primaryClassification(source: EvidenceSource) {
  return source.raw_record?.review?.primary_classification || 'unclassified'
}

export function primaryEvidenceRole(sourceId: string, links: SourceEvidenceRole[]) {
  return links.find((item) => item.source_id === sourceId && item.primary_role)?.evidence_role
    ?? links.find((item) => item.source_id === sourceId)?.evidence_role
    ?? 'unclassified'
}

export function asAuthorLine(authors: unknown) {
  if (!Array.isArray(authors)) return ''
  return authors.join(', ')
}

export function compactJson(value: any) {
  if (!value || (typeof value === 'object' && Object.keys(value).length === 0)) return 'Not extracted'
  if (typeof value !== 'object') return String(value)
  return Object.entries(value)
    .map(([key, val]) => `${humanize(key)}: ${typeof val === 'object' ? JSON.stringify(val) : val}`)
    .join(' · ')
}

export function bucketLabel(bucket: string) {
  if (bucket.startsWith('A_')) return 'Direct intervention review stream'
  if (bucket.startsWith('B_')) return 'Mechanism / measurement review stream'
  if (bucket.startsWith('C_')) return 'Human–AI / activity-system review stream'
  return humanize(bucket)
}
