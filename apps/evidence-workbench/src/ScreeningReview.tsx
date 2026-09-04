import { AlertTriangle, Bot, CheckCircle2, ClipboardCheck, ShieldCheck, UserCheck } from 'lucide-react'
import { supabase } from './lib/supabase'
import { DetailSection, Info } from './WorkbenchUi'
import { hasScreeningDisagreement, reviewAuthorityLabel, screeningReview } from './review'
import { humanize, type EvidenceSource } from './workbench'
import './review-queue.css'

export function ScreeningReviewSection({
  source,
  canEdit,
  onRefresh,
  onError,
}: {
  source: EvidenceSource
  canEdit: boolean
  onRefresh: () => Promise<void>
  onError: (value: string | null) => void
}) {
  const screening = screeningReview(source)
  const disagreement = hasScreeningDisagreement(source)

  async function setReviewStatus(reviewStatus: string) {
    const { error } = await supabase
      .from('evidence_source')
      .update({ review_status: reviewStatus })
      .eq('source_id', source.source_id)

    if (error) onError(error.message)
    else await onRefresh()
  }

  if (!screening) {
    return (
      <DetailSection title="Screening & provenance" icon={<ClipboardCheck size={17} />}>
        <div className="screening-empty">
          <ShieldCheck size={18} />
          <div>
            <strong>No provisional screening provenance</strong>
            <p>This source predates the staged screening workflow or has already been normalised without machine/assistant screening metadata.</p>
          </div>
        </div>
      </DetailSection>
    )
  }

  return (
    <DetailSection title="Screening & provenance" icon={<ClipboardCheck size={17} />}>
      <div className="screening-status-row">
        <span className="authority-pill"><Bot size={12} /> {reviewAuthorityLabel(source)}</span>
        <span className={`review-state-pill review-state-${source.review_status}`}>{humanize(source.review_status)}</span>
        {disagreement && <span className="disagreement-pill"><AlertTriangle size={12} /> Classification disagreement</span>}
      </div>

      <div className="screening-grid">
        <Info label="Screening decision" value={humanize(screening.decision)} />
        <Info label="Paper role" value={humanize(screening.paper_role)} />
        <Info label="Study design" value={screening.study_design} />
        <Info label="Primary CSI domain" value={humanize(screening.primary_domain)} />
        <Info label="CSI domains" value={screening.domains.map(humanize).join(', ') || 'Not specified'} />
        <Info label="Health scope" value={humanize(screening.health_scope)} />
        <Info label="Full-text priority" value={humanize(screening.priority)} />
        <Info label="Reference confidence" value={screening.confidence == null ? 'Not specified' : screening.confidence.toFixed(2)} />
      </div>

      {screening.abstract && (
        <details className="screening-abstract">
          <summary>Abstract evidence used for screening</summary>
          <p>{screening.abstract}</p>
        </details>
      )}

      {screening.note && (
        <div className="adjudication-note">
          <strong>Adjudication note</strong>
          <p>{screening.note}</p>
        </div>
      )}

      {screening.model_judgements.length > 0 && (
        <div className="model-comparison">
          <div className="model-comparison-title"><Bot size={14} /> Machine comparison</div>
          <div className="model-table-wrap">
            <table className="model-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Decision</th>
                  <th>Role</th>
                  <th>Primary domain</th>
                  <th>Priority</th>
                  <th>Confidence</th>
                </tr>
              </thead>
              <tbody>
                {screening.model_judgements.map((item, index) => (
                  <tr key={`${item.label ?? item.model ?? 'model'}-${index}`}>
                    <td>{item.label ?? item.model ?? 'Model'}</td>
                    <td>{humanize(item.decision)}</td>
                    <td>{humanize(item.paper_role)}</td>
                    <td>{humanize(item.primary_domain)}</td>
                    <td>{humanize(item.priority)}</td>
                    <td>{item.confidence == null ? '—' : item.confidence.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {canEdit && !['approved_seed', 'approved_release'].includes(source.review_status) && (
        <div className="review-actions">
          <div className="review-actions-copy">
            <UserCheck size={15} />
            <span>Reviewer status changes are audit-logged. Human verification does not publish this source to the CSI Gateway.</span>
          </div>
          <div className="review-buttons">
            {source.review_status !== 'reviewing' && (
              <button className="secondary-button" onClick={() => setReviewStatus('reviewing')}>Start review</button>
            )}
            {source.review_status !== 'human_verified' && (
              <button className="secondary-button" onClick={() => setReviewStatus('human_verified')}><CheckCircle2 size={14} /> Human verified</button>
            )}
            <button className="primary-button" onClick={() => setReviewStatus('ready_for_approval')}>Ready for approval</button>
          </div>
        </div>
      )}
    </DetailSection>
  )
}
