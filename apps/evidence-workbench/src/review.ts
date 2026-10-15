import type { EvidenceSource } from './workbench'

export type ReviewLane = 'all' | 'needs_review' | 'disagreement' | 'ready_for_approval' | 'approved'

export type ScreeningJudgement = {
  label?: string
  model?: string
  decision?: string
  paper_role?: string
  study_design?: string
  primary_domain?: string
  domains?: string[]
  health_scope?: string
  priority?: string
  confidence?: number | null
}

export type ScreeningReview = {
  authority: string
  decision?: string
  paper_role?: string
  study_design?: string
  primary_domain?: string
  domains: string[]
  health_scope?: string
  priority?: string
  confidence?: number | null
  note?: string
  abstract?: string
  model_judgements: ScreeningJudgement[]
}

export function screeningReview(source: EvidenceSource): ScreeningReview | null {
  const review = source.raw_record?.review ?? {}
  const screening = review.screening ?? source.raw_record?.screening ?? null

  if (!screening && !review.authority) return null

  const rawModels = screening?.model_judgements ?? review.model_judgements ?? []
  const modelJudgements = Array.isArray(rawModels)
    ? rawModels.filter((item: unknown): item is Record<string, unknown> => Boolean(item) && typeof item === 'object').map((item) => ({
        label: typeof item.label === 'string' ? item.label : undefined,
        model: typeof item.model === 'string' ? item.model : undefined,
        decision: typeof item.decision === 'string' ? item.decision : typeof item.screening_decision === 'string' ? item.screening_decision : undefined,
        paper_role: typeof item.paper_role === 'string' ? item.paper_role : undefined,
        study_design: typeof item.study_design === 'string' ? item.study_design : undefined,
        primary_domain: typeof item.primary_domain === 'string' ? item.primary_domain : typeof item.primary_csi_domain === 'string' ? item.primary_csi_domain : undefined,
        domains: Array.isArray(item.domains) ? item.domains.map(String) : Array.isArray(item.csi_domains) ? item.csi_domains.map(String) : undefined,
        health_scope: typeof item.health_scope === 'string' ? item.health_scope : undefined,
        priority: typeof item.priority === 'string' ? item.priority : typeof item.fulltext_priority === 'string' ? item.fulltext_priority : undefined,
        confidence: typeof item.confidence === 'number' ? item.confidence : typeof item.abstract_only_confidence === 'number' ? item.abstract_only_confidence : null,
      }))
    : []

  return {
    authority: String(review.authority ?? screening?.authority ?? 'unspecified'),
    decision: screening?.decision ?? screening?.screening_decision,
    paper_role: screening?.paper_role,
    study_design: screening?.study_design ?? screening?.study_design_label,
    primary_domain: screening?.primary_domain ?? screening?.primary_csi_domain,
    domains: Array.isArray(screening?.domains)
      ? screening.domains.map(String)
      : Array.isArray(screening?.csi_domains)
        ? screening.csi_domains.map(String)
        : [],
    health_scope: screening?.health_scope,
    priority: screening?.priority ?? screening?.fulltext_priority,
    confidence: typeof screening?.confidence === 'number'
      ? screening.confidence
      : typeof screening?.reference_confidence === 'number'
        ? screening.reference_confidence
        : null,
    note: screening?.note ?? screening?.adjudication_note ?? review.adjudication_note,
    abstract: typeof screening?.abstract === 'string' ? screening.abstract : undefined,
    model_judgements: modelJudgements,
  }
}

function normaliseSet(values?: string[]) {
  return [...new Set((values ?? []).map(String))].sort()
}

function sameSet(a?: string[], b?: string[]) {
  const left = normaliseSet(a)
  const right = normaliseSet(b)
  return left.length === right.length && left.every((value, index) => value === right[index])
}

export function hasScreeningDisagreement(source: EvidenceSource) {
  const screening = screeningReview(source)
  if (!screening || screening.model_judgements.length === 0) return false

  return screening.model_judgements.some((item) => {
    if (screening.decision && item.decision && item.decision !== screening.decision) return true
    if (screening.paper_role && item.paper_role && item.paper_role !== screening.paper_role) return true
    if (screening.primary_domain && item.primary_domain && item.primary_domain !== screening.primary_domain) return true
    if (screening.health_scope && item.health_scope && item.health_scope !== screening.health_scope) return true
    if (screening.priority && item.priority && item.priority !== screening.priority) return true
    if (screening.domains.length && item.domains?.length && !sameSet(item.domains, screening.domains)) return true
    return false
  })
}

export function sourceReviewLane(source: EvidenceSource): Exclude<ReviewLane, 'all'> {
  if (source.review_status === 'approved_seed' || source.review_status === 'approved_release') return 'approved'
  if (source.review_status === 'human_verified' || source.review_status === 'ready_for_approval') return 'ready_for_approval'
  if (hasScreeningDisagreement(source)) return 'disagreement'
  return 'needs_review'
}

export function matchesReviewLane(source: EvidenceSource, lane: ReviewLane) {
  if (lane === 'all') return true
  if (lane === 'needs_review') {
    return sourceReviewLane(source) === 'needs_review' || sourceReviewLane(source) === 'disagreement'
  }
  return sourceReviewLane(source) === lane
}

export function reviewAuthorityLabel(source: EvidenceSource) {
  const review = screeningReview(source)
  if (!review) {
    if (source.review_status === 'approved_seed' || source.review_status === 'approved_release') return 'Human approved'
    return 'No screening provenance'
  }
  if (source.review_status === 'human_verified' || source.review_status === 'ready_for_approval') return 'Human verified'
  if (source.review_status === 'approved_seed' || source.review_status === 'approved_release') return 'Human approved'
  if (review.authority === 'assistant_adjudicated_not_human_approved') return 'Assistant adjudicated'
  return review.authority.replaceAll('_', ' ')
}
