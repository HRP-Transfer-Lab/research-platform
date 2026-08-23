import { EvidenceMaturitySection } from './EvidenceMaturity'
import { SourceDetail } from './SourceDetail'
import type { EvidenceSource, RegistryData } from './workbench'

export function SourceDetailWithMaturity({ source, data, canEdit, onRefresh, onError }: { source: EvidenceSource; data: RegistryData; canEdit: boolean; onRefresh: () => Promise<void>; onError: (value: string | null) => void }) {
  return (
    <div className="detail-combined-scroll">
      <EvidenceMaturitySection sourceId={source.source_id} canEdit={canEdit} onError={onError} />
      <SourceDetail source={source} data={data} canEdit={canEdit} onRefresh={onRefresh} onError={onError} />
    </div>
  )
}
