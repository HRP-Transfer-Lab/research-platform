import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronRight, ClipboardList, Search, ShieldCheck } from 'lucide-react'
import { SourceDetailWithMaturity } from './SourceDetailWithMaturity'
import { BucketPill, RoutePill } from './WorkbenchUi'
import { hasScreeningDisagreement, matchesReviewLane, reviewAuthorityLabel, screeningReview, sourceReviewLane, type ReviewLane } from './review'
import { humanize, primaryClassification, type EvidenceSource, type RegistryData } from './workbench'
import './review-queue.css'

const lanes: { id: ReviewLane; label: string }[] = [
  { id: 'needs_review', label: 'Needs review' },
  { id: 'disagreement', label: 'Disagreements' },
  { id: 'ready_for_approval', label: 'Ready for approval' },
  { id: 'approved', label: 'Approved' },
  { id: 'all', label: 'All sources' },
]

export function ReviewQueuePage({
  data,
  canEdit,
  onRefresh,
  onError,
}: {
  data: RegistryData
  canEdit: boolean
  onRefresh: () => Promise<void>
  onError: (value: string | null) => void
}) {
  const [lane, setLane] = useState<ReviewLane>('needs_review')
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const counts = useMemo(() => ({
    needs_review: data.sources.filter((source) => matchesReviewLane(source, 'needs_review')).length,
    disagreement: data.sources.filter((source) => matchesReviewLane(source, 'disagreement')).length,
    ready_for_approval: data.sources.filter((source) => matchesReviewLane(source, 'ready_for_approval')).length,
    approved: data.sources.filter((source) => matchesReviewLane(source, 'approved')).length,
    all: data.sources.length,
  }), [data.sources])

  const filtered = useMemo(() => {
    const normalised = query.trim().toLowerCase()
    return data.sources.filter((source) => {
      if (!matchesReviewLane(source, lane)) return false
      if (!normalised) return true
      const screening = screeningReview(source)
      const text = [
        source.title,
        source.venue,
        source.doi,
        screening?.decision,
        screening?.paper_role,
        screening?.primary_domain,
        screening?.domains.join(' '),
        screening?.note,
      ].filter(Boolean).join(' ').toLowerCase()
      return text.includes(normalised)
    })
  }, [data.sources, lane, query])

  useEffect(() => {
    if (!filtered.some((source) => source.source_id === selectedId)) {
      setSelectedId(filtered[0]?.source_id ?? null)
    }
  }, [filtered, selectedId])

  const selected = data.sources.find((source) => source.source_id === selectedId) ?? null

  return (
    <main className="review-page">
      <section className="review-intro">
        <div>
          <div className="review-kicker"><ClipboardList size={15} /> Scientific review workflow</div>
          <h2>Provisional Evidence Review Queue</h2>
          <p>Screen machine- or assistant-adjudicated sources before deeper extraction, approval and release. Nothing in this queue is published to the CSI Evidence Gateway unless it later enters an approved release.</p>
        </div>
        <div className="review-safety"><ShieldCheck size={18} /><span>Working Registry ≠ approved evidence release</span></div>
      </section>

      <section className="queue-tabs" aria-label="Review queue lanes">
        {lanes.map((item) => (
          <button key={item.id} className={`queue-tab ${lane === item.id ? 'active' : ''}`} onClick={() => setLane(item.id)}>
            <span>{item.label}</span><strong>{counts[item.id]}</strong>
          </button>
        ))}
      </section>

      <section className="review-grid">
        <aside className="review-list-panel">
          <div className="review-search"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search title, DOI, role, domain…" /></div>
          <div className="review-list-heading"><strong>{filtered.length}</strong> records in {lanes.find((item) => item.id === lane)?.label.toLowerCase()}</div>
          <div className="review-list">
            {filtered.map((source) => <ReviewCard key={source.source_id} source={source} selected={source.source_id === selectedId} onClick={() => setSelectedId(source.source_id)} />)}
            {filtered.length === 0 && <div className="review-empty">No records in this queue.</div>}
          </div>
        </aside>
        <section className="review-detail-panel">
          {selected ? (
            <SourceDetailWithMaturity source={selected} data={data} canEdit={canEdit} onRefresh={onRefresh} onError={onError} />
          ) : (
            <div className="review-empty-detail"><ClipboardList size={28} /><p>Select a record to review.</p></div>
          )}
        </section>
      </section>
    </main>
  )
}

function ReviewCard({ source, selected, onClick }: { source: EvidenceSource; selected: boolean; onClick: () => void }) {
  const screening = screeningReview(source)
  const lane = sourceReviewLane(source)
  const disagreement = hasScreeningDisagreement(source)

  return (
    <button className={`review-card ${selected ? 'selected' : ''}`} onClick={onClick}>
      <div className="review-card-top">
        <BucketPill bucket={source.review_bucket} />
        <span className={`queue-state queue-state-${lane}`}>{humanize(lane)}</span>
      </div>
      <h3>{source.title}</h3>
      <p>{source.venue ?? source.doi ?? humanize(source.source_kind)}</p>
      <div className="review-card-meta">
        <span>{reviewAuthorityLabel(source)}</span>
        {screening?.confidence != null && <span>Confidence {screening.confidence.toFixed(2)}</span>}
      </div>
      {disagreement && <div className="review-card-alert"><AlertTriangle size={12} /> Models disagree</div>}
      <div className="review-card-bottom">
        <RoutePill route={screening?.paper_role ?? primaryClassification(source)} />
        {lane === 'ready_for_approval' && <CheckCircle2 size={14} />}
        {lane !== 'ready_for_approval' && <ChevronRight size={14} />}
      </div>
    </button>
  )
}
