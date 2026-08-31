import { useEffect, useMemo, useState } from 'react'
import { Check, GitCompareArrows, RefreshCw, X } from 'lucide-react'
import { supabase } from './lib/supabase'
import { DetailSection, EmptyLine } from './WorkbenchUi'
import { compactJson, humanize, type EvidenceSource, type RegistryData } from './workbench'

type Stage5Status = {
  study_id: number
  arm_extraction_status: string
  arm_mapping_source: string
  arm_review_status: string
  contrast_extraction_status: string
  contrast_mapping_source: string
  contrast_review_status: string
  notes: string | null
}

type StudyArm = {
  arm_id: number
  study_id: number
  arm_key: string
  arm_label: string
  author_arm_label: string | null
  arm_role: string
  assignment_structure: string
  arm_description: string | null
  sample_json: any
  mapping_source: string
  review_status: string
}

type ArmComponent = {
  arm_id: number
  component_id: number
  membership_role: string
  rationale: string | null
  mapping_source: string
  review_status: string
}

type StudyContrast = {
  contrast_id: number
  study_id: number
  contrast_key: string
  contrast_label: string
  contrast_type: string
  estimand_summary: string | null
  mapping_source: string
  review_status: string
}

type ContrastArmMember = {
  contrast_id: number
  arm_id: number
  contrast_side: string
  contrast_coefficient: number | null
  rationale: string | null
  mapping_source: string
  review_status: string
}

const armRoles = [
  'intervention', 'active_control', 'passive_control', 'waitlist',
  'treatment_as_usual', 'alternative_intervention', 'reference',
  'observational_exposure', 'experimental_condition', 'measurement_condition', 'unclear',
]

const assignmentStructures = [
  'parallel_group', 'cluster_group', 'factorial_cell', 'within_subject_condition',
  'single_group', 'observational_group', 'unclear',
]

const membershipRoles = ['defining', 'shared', 'add_on', 'background', 'unclear']
const contrastTypes = ['pairwise', 'multiarm_pairwise', 'factorial_main_effect', 'factorial_interaction', 'within_subject', 'observational', 'other']

function ReviewPills({ source, status }: { source: string; status: string }) {
  return <span className="detail-meta-row"><span className="status-pill">{humanize(source)}</span><span className="status-pill">{humanize(status)}</span></span>
}

function ReviewButtons({ onApprove, onReject }: { onApprove: () => void; onReject: () => void }) {
  return <span className="detail-meta-row"><button className="icon-button mini" title="Approve" onClick={onApprove}><Check size={13} /></button><button className="icon-button mini" title="Reject" onClick={onReject}><X size={13} /></button></span>
}

export function Stage5StudyDesignReview({
  source,
  data,
  canEdit,
  onError,
}: {
  source: EvidenceSource
  data: RegistryData
  canEdit: boolean
  onError: (value: string | null) => void
}) {
  const study = data.studies.find((item) => item.source_id === source.source_id)
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<Stage5Status | null>(null)
  const [arms, setArms] = useState<StudyArm[]>([])
  const [armComponents, setArmComponents] = useState<ArmComponent[]>([])
  const [contrasts, setContrasts] = useState<StudyContrast[]>([])
  const [contrastMembers, setContrastMembers] = useState<ContrastArmMember[]>([])

  const componentById = useMemo(() => new Map(data.components.map((item) => [item.component_id, item])), [data.components])
  const armById = useMemo(() => new Map(arms.map((item) => [item.arm_id, item])), [arms])

  useEffect(() => {
    void load()
  }, [source.source_id, study?.study_id])

  async function load() {
    if (!study) {
      setStatus(null)
      setArms([])
      setArmComponents([])
      setContrasts([])
      setContrastMembers([])
      return
    }
    setLoading(true)
    onError(null)

    const [statusRow, armRows, contrastRows] = await Promise.all([
      supabase.from('study_stage5_status').select('*').eq('study_id', study.study_id).maybeSingle(),
      supabase.from('study_arm').select('*').eq('study_id', study.study_id).order('arm_id'),
      supabase.from('study_contrast').select('*').eq('study_id', study.study_id).order('contrast_id'),
    ])
    const firstError = [statusRow, armRows, contrastRows].find((result) => result.error)?.error
    if (firstError) {
      onError(firstError.message)
      setLoading(false)
      return
    }

    const nextArms = (armRows.data ?? []) as StudyArm[]
    const nextContrasts = (contrastRows.data ?? []) as StudyContrast[]
    const armIds = nextArms.map((item) => item.arm_id)
    const contrastIds = nextContrasts.map((item) => item.contrast_id)

    const [componentRows, memberRows] = await Promise.all([
      armIds.length
        ? supabase.from('arm_component').select('*').in('arm_id', armIds).order('arm_id')
        : Promise.resolve({ data: [], error: null } as any),
      contrastIds.length
        ? supabase.from('contrast_arm_member').select('*').in('contrast_id', contrastIds).order('contrast_id')
        : Promise.resolve({ data: [], error: null } as any),
    ])
    const linkError = [componentRows, memberRows].find((result) => result.error)?.error
    if (linkError) onError(linkError.message)
    else {
      setStatus((statusRow.data ?? null) as Stage5Status | null)
      setArms(nextArms)
      setContrasts(nextContrasts)
      setArmComponents((componentRows.data ?? []) as ArmComponent[])
      setContrastMembers((memberRows.data ?? []) as ContrastArmMember[])
    }
    setLoading(false)
  }

  async function reviewStudyDimension(dimension: 'arm' | 'contrast', reviewStatus: 'approved' | 'rejected') {
    if (!study) return
    const payload = dimension === 'arm'
      ? { arm_mapping_source: 'human_review', arm_review_status: reviewStatus, updated_at: new Date().toISOString() }
      : { contrast_mapping_source: 'human_review', contrast_review_status: reviewStatus, updated_at: new Date().toISOString() }
    const { error } = await supabase.from('study_stage5_status').update(payload).eq('study_id', study.study_id)
    if (error) onError(error.message); else await load()
  }

  async function reviewArm(armId: number, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('study_arm').update({ mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }).eq('arm_id', armId)
    if (error) onError(error.message); else await load()
  }

  async function correctArm(armId: number, field: 'arm_role' | 'assignment_structure', value: string) {
    const { error } = await supabase.from('study_arm').update({ [field]: value, mapping_source: 'human_review', review_status: 'approved', updated_at: new Date().toISOString() }).eq('arm_id', armId)
    if (error) onError(error.message); else await load()
  }

  async function reviewComponentLink(link: ArmComponent, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('arm_component').update({ mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }).eq('arm_id', link.arm_id).eq('component_id', link.component_id)
    if (error) onError(error.message); else await load()
  }

  async function correctComponentLink(link: ArmComponent, value: string) {
    const { error } = await supabase.from('arm_component').update({ membership_role: value, mapping_source: 'human_review', review_status: 'approved', updated_at: new Date().toISOString() }).eq('arm_id', link.arm_id).eq('component_id', link.component_id)
    if (error) onError(error.message); else await load()
  }

  async function reviewContrast(contrastId: number, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('study_contrast').update({ mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }).eq('contrast_id', contrastId)
    if (error) onError(error.message); else await load()
  }

  async function correctContrast(contrastId: number, value: string) {
    const { error } = await supabase.from('study_contrast').update({ contrast_type: value, mapping_source: 'human_review', review_status: 'approved', updated_at: new Date().toISOString() }).eq('contrast_id', contrastId)
    if (error) onError(error.message); else await load()
  }

  async function reviewContrastMember(link: ContrastArmMember, reviewStatus: 'approved' | 'rejected') {
    const { error } = await supabase.from('contrast_arm_member').update({ mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() }).eq('contrast_id', link.contrast_id).eq('arm_id', link.arm_id)
    if (error) onError(error.message); else await load()
  }

  return (
    <DetailSection title="Study arms, conditions & contrasts" icon={<GitCompareArrows size={17} />}>
      <div className="record-note">Stage 5 separates study arms/conditions from reusable intervention components and from scientific contrasts. Agent-generated rows remain proposals until human review; missing arm sample sizes are not inferred from study totals.</div>
      {loading && <div className="small-copy" style={{ marginTop: 12 }}><RefreshCw className="spin" size={14} /> Loading Stage 5 design structure…</div>}
      {!study && <EmptyLine>No normalized study row.</EmptyLine>}

      {study && status && <div className="stack-list" style={{ marginTop: 14 }}>
        <div className="product-card">
          <div className="product-head"><strong>Arm/condition extraction</strong><ReviewPills source={status.arm_mapping_source} status={status.arm_review_status} /></div>
          <div className="product-meta"><span>{humanize(status.arm_extraction_status)}</span></div>
          {canEdit && <ReviewButtons onApprove={() => void reviewStudyDimension('arm', 'approved')} onReject={() => void reviewStudyDimension('arm', 'rejected')} />}
        </div>
        <div className="product-card">
          <div className="product-head"><strong>Contrast extraction</strong><ReviewPills source={status.contrast_mapping_source} status={status.contrast_review_status} /></div>
          <div className="product-meta"><span>{humanize(status.contrast_extraction_status)}</span></div>
          {status.notes && <p>{status.notes}</p>}
          {canEdit && <ReviewButtons onApprove={() => void reviewStudyDimension('contrast', 'approved')} onReject={() => void reviewStudyDimension('contrast', 'rejected')} />}
        </div>
      </div>}

      {study && <div style={{ marginTop: 18 }}><span className="field-label">Arms / conditions ({arms.length})</span>
        <div className="stack-list">
          {arms.length ? arms.map((arm) => {
            const links = armComponents.filter((item) => item.arm_id === arm.arm_id)
            return <div className="product-card" key={arm.arm_id}>
              <div className="product-head"><div><strong>{arm.arm_label}</strong><span className="match-pill">{humanize(arm.arm_role)}</span></div><ReviewPills source={arm.mapping_source} status={arm.review_status} /></div>
              <div className="product-meta"><span>{humanize(arm.assignment_structure)}</span><span>{arm.author_arm_label || 'No separate author label'}</span></div>
              {arm.arm_description && <p>{arm.arm_description}</p>}
              {Object.keys(arm.sample_json ?? {}).length > 0 && <p className="small-copy">Arm sample: {compactJson(arm.sample_json)}</p>}
              {links.length ? <div className="stack-list">{links.map((link) => {
                const component = componentById.get(link.component_id)
                return <div className="record-note" key={`${link.arm_id}-${link.component_id}`}><strong>{component?.component_name ?? `Component ${link.component_id}`}</strong> · {humanize(link.membership_role)} <ReviewPills source={link.mapping_source} status={link.review_status} />{canEdit && <><select className="select-input" value={link.membership_role} onChange={(e) => void correctComponentLink(link, e.target.value)}>{membershipRoles.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select><ReviewButtons onApprove={() => void reviewComponentLink(link, 'approved')} onReject={() => void reviewComponentLink(link, 'rejected')} /></>}</div>
              })}</div> : <p className="small-copy">No normalized intervention component membership assigned.</p>}
              {canEdit && <div className="two-fields"><label><span className="field-label">Arm role</span><select className="select-input" value={arm.arm_role} onChange={(e) => void correctArm(arm.arm_id, 'arm_role', e.target.value)}>{armRoles.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><label><span className="field-label">Assignment structure</span><select className="select-input" value={arm.assignment_structure} onChange={(e) => void correctArm(arm.arm_id, 'assignment_structure', e.target.value)}>{assignmentStructures.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><ReviewButtons onApprove={() => void reviewArm(arm.arm_id, 'approved')} onReject={() => void reviewArm(arm.arm_id, 'rejected')} /></div>}
            </div>
          }) : <EmptyLine>No arm/condition candidates mapped for this seed study.</EmptyLine>}
        </div>
      </div>}

      {study && <div style={{ marginTop: 18 }}><span className="field-label">Contrasts ({contrasts.length})</span>
        <div className="stack-list">
          {contrasts.length ? contrasts.map((contrast) => {
            const members = contrastMembers.filter((item) => item.contrast_id === contrast.contrast_id)
            return <div className="product-card" key={contrast.contrast_id}>
              <div className="product-head"><div><strong>{contrast.contrast_label}</strong><span className="match-pill">{humanize(contrast.contrast_type)}</span></div><ReviewPills source={contrast.mapping_source} status={contrast.review_status} /></div>
              {contrast.estimand_summary && <p>{contrast.estimand_summary}</p>}
              <div className="stack-list">{members.map((member) => {
                const arm = armById.get(member.arm_id)
                return <div className="record-note" key={`${member.contrast_id}-${member.arm_id}`}><strong>{arm?.arm_label ?? `Arm ${member.arm_id}`}</strong> · {humanize(member.contrast_side)}{member.contrast_coefficient != null ? ` · coefficient ${member.contrast_coefficient}` : ''} <ReviewPills source={member.mapping_source} status={member.review_status} />{canEdit && <ReviewButtons onApprove={() => void reviewContrastMember(member, 'approved')} onReject={() => void reviewContrastMember(member, 'rejected')} />}</div>
              })}</div>
              {canEdit && <div className="two-fields"><label><span className="field-label">Contrast type</span><select className="select-input" value={contrast.contrast_type} onChange={(e) => void correctContrast(contrast.contrast_id, e.target.value)}>{contrastTypes.map((value) => <option key={value} value={value}>{humanize(value)}</option>)}</select></label><ReviewButtons onApprove={() => void reviewContrast(contrast.contrast_id, 'approved')} onReject={() => void reviewContrast(contrast.contrast_id, 'rejected')} /></div>}
            </div>
          }) : <EmptyLine>No contrast candidates mapped for this seed study.</EmptyLine>}
        </div>
      </div>}
    </DetailSection>
  )
}
