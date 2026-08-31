import { EvidenceMaturitySection } from './EvidenceMaturity'
import { SourceDetail } from './SourceDetail'
import { SourceSemantics } from './SourceSemantics'
import { Stage3OntologyReview } from './Stage3OntologyReview'
import { Stage4OutcomeReview } from './Stage4OutcomeReview'
import { Stage5StudyDesignReview } from './Stage5StudyDesignReview'
import { Stage6QuantitativeReview } from './Stage6QuantitativeReview'
import { Stage7QualityReview } from './Stage7QualityReview'
import { Stage8BodyEvidenceReview } from './Stage8BodyEvidenceReview'
import { Stage9PopulationContextReview } from './Stage9PopulationContextReview'
import { Stage10HarmsImplementationReview } from './Stage10HarmsImplementationReview'
import type { EvidenceSource, RegistryData } from './workbench'

export function SourceDetailWithMaturity({ source, data, canEdit, onRefresh, onError }: { source: EvidenceSource; data: RegistryData; canEdit: boolean; onRefresh: () => Promise<void>; onError: (value: string | null) => void }) {
  return (
    <div className="detail-combined-scroll">
      <EvidenceMaturitySection sourceId={source.source_id} canEdit={canEdit} onError={onError} />
      <SourceSemantics source={source} data={data} canEdit={canEdit} onRefresh={onRefresh} onError={onError} />
      <Stage3OntologyReview source={source} canEdit={canEdit} onError={onError} />
      <Stage4OutcomeReview source={source} data={data} canEdit={canEdit} onError={onError} />
      <Stage5StudyDesignReview source={source} data={data} canEdit={canEdit} onError={onError} />
      <Stage6QuantitativeReview source={source} data={data} canEdit={canEdit} onError={onError} />
      <Stage7QualityReview source={source} data={data} canEdit={canEdit} onError={onError} />
      <Stage8BodyEvidenceReview source={source} data={data} canEdit={canEdit} onError={onError} />
      <Stage9PopulationContextReview source={source} data={data} canEdit={canEdit} onError={onError} />
      <Stage10HarmsImplementationReview source={source} data={data} canEdit={canEdit} onError={onError} />
      <SourceDetail source={source} data={data} canEdit={canEdit} onRefresh={onRefresh} onError={onError} />
    </div>
  )
}