import { useEffect, useMemo, useState } from 'react'
import { Check, ClipboardCheck, Plus, RefreshCw, X } from 'lucide-react'
import { supabase } from './lib/supabase'
import { DetailSection, EmptyLine } from './WorkbenchUi'
import { humanize, type EvidenceSource, type RegistryData } from './workbench'

type Classification = {
  outcome_id: number
  legacy_rung_snapshot: string | null
  raw_timepoint_snapshot: string | null
  outcome_distance: string | null
  distance_status: string
  distance_mapping_source: string
  distance_review_status: string
  time_status: string
  time_mapping_source: string
  time_review_status: string
  transfer_status: string
  transfer_mapping_source: string
  transfer_review_status: string
  role_status: string
  role_mapping_source: string
  role_review_status: string
  bridge_status: string
  bridge_mapping_source: string
  bridge_review_status: string
  rationale: string | null
}

type LinkRow = {
  outcome_id: number
  value: string
  rationale: string | null
  mapping_source: string
  review_status: string
}

type Definition = {
  value: string
  label: string
  description: string
}

const dimensionMeta = {
  time: { table: 'outcome_time_link', valueColumn: 'time_class' },
  transfer: { table: 'outcome_transfer_axis', valueColumn: 'transfer_axis' },
  role: { table: 'outcome_role_link', valueColumn: 'outcome_role' },
  bridge: { table: 'outcome_bridge_evidence', valueColumn: 'bridge_evidence' },
} as const

type LinkDimension = keyof typeof dimensionMeta

function ReviewStatus({ mappingSource, reviewStatus }: { mappingSource: string; reviewStatus: string }) {
  return (
    <span className="detail-meta-row">
      <span className="status-pill">{humanize(mappingSource)}</span>
      <span className="status-pill">{humanize(reviewStatus)}</span>
    </span>
  )
}

export function Stage4OutcomeReview({
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
  const outcomes = useMemo(
    () => data.outcomes.filter((item) => item.study_id === study?.study_id),
    [data.outcomes, study?.study_id],
  )
  const outcomeIds = useMemo(() => outcomes.map((item) => item.outcome_id), [outcomes])

  const [loading, setLoading] = useState(false)
  const [classifications, setClassifications] = useState<Classification[]>([])
  const [timeLinks, setTimeLinks] = useState<LinkRow[]>([])
  const [transferLinks, setTransferLinks] = useState<LinkRow[]>([])
  const [roleLinks, setRoleLinks] = useState<LinkRow[]>([])
  const [bridgeLinks, setBridgeLinks] = useState<LinkRow[]>([])
  const [distanceDefs, setDistanceDefs] = useState<Definition[]>([])
  const [timeDefs, setTimeDefs] = useState<Definition[]>([])
  const [transferDefs, setTransferDefs] = useState<Definition[]>([])
  const [roleDefs, setRoleDefs] = useState<Definition[]>([])
  const [bridgeDefs, setBridgeDefs] = useState<Definition[]>([])
  const [addChoice, setAddChoice] = useState<Record<string, string>>({})

  useEffect(() => {
    void load()
  }, [source.source_id, outcomeIds.join(',')])

  async function load() {
    setLoading(true)
    onError(null)

    const [distances, times, transfers, roles, bridges] = await Promise.all([
      supabase.from('outcome_distance_definition').select('outcome_distance,label,description').eq('active', true).order('outcome_distance'),
      supabase.from('outcome_time_definition').select('time_class,label,description').eq('active', true).order('time_class'),
      supabase.from('transfer_axis_definition').select('transfer_axis,label,description').eq('active', true).order('transfer_axis'),
      supabase.from('outcome_role_definition').select('outcome_role,label,description').eq('active', true).order('outcome_role'),
      supabase.from('bridge_evidence_definition').select('bridge_evidence,label,description').eq('active', true).order('bridge_evidence'),
    ])

    const definitionError = [distances, times, transfers, roles, bridges].find((result) => result.error)?.error
    if (definitionError) {
      onError(definitionError.message)
      setLoading(false)
      return
    }

    setDistanceDefs((distances.data ?? []).map((row: any) => ({ value: row.outcome_distance, label: row.label, description: row.description })))
    setTimeDefs((times.data ?? []).map((row: any) => ({ value: row.time_class, label: row.label, description: row.description })))
    setTransferDefs((transfers.data ?? []).map((row: any) => ({ value: row.transfer_axis, label: row.label, description: row.description })))
    setRoleDefs((roles.data ?? []).map((row: any) => ({ value: row.outcome_role, label: row.label, description: row.description })))
    setBridgeDefs((bridges.data ?? []).map((row: any) => ({ value: row.bridge_evidence, label: row.label, description: row.description })))

    if (!outcomeIds.length) {
      setClassifications([])
      setTimeLinks([])
      setTransferLinks([])
      setRoleLinks([])
      setBridgeLinks([])
      setLoading(false)
      return
    }

    const [classificationRows, timeRows, transferRows, roleRows, bridgeRows] = await Promise.all([
      supabase.from('outcome_stage4_classification').select('*').in('outcome_id', outcomeIds).order('outcome_id'),
      supabase.from('outcome_time_link').select('*').in('outcome_id', outcomeIds).order('outcome_id'),
      supabase.from('outcome_transfer_axis').select('*').in('outcome_id', outcomeIds).order('outcome_id'),
      supabase.from('outcome_role_link').select('*').in('outcome_id', outcomeIds).order('outcome_id'),
      supabase.from('outcome_bridge_evidence').select('*').in('outcome_id', outcomeIds).order('outcome_id'),
    ])

    const mappingError = [classificationRows, timeRows, transferRows, roleRows, bridgeRows].find((result) => result.error)?.error
    if (mappingError) {
      onError(mappingError.message)
      setLoading(false)
      return
    }

    setClassifications((classificationRows.data ?? []) as Classification[])
    setTimeLinks(normaliseLinks(timeRows.data ?? [], 'time_class'))
    setTransferLinks(normaliseLinks(transferRows.data ?? [], 'transfer_axis'))
    setRoleLinks(normaliseLinks(roleRows.data ?? [], 'outcome_role'))
    setBridgeLinks(normaliseLinks(bridgeRows.data ?? [], 'bridge_evidence'))
    setLoading(false)
  }

  function normaliseLinks(rows: any[], valueColumn: string): LinkRow[] {
    return rows.map((row) => ({
      outcome_id: row.outcome_id,
      value: row[valueColumn],
      rationale: row.rationale ?? null,
      mapping_source: row.mapping_source,
      review_status: row.review_status,
    }))
  }

  function linksFor(dimension: LinkDimension, outcomeId: number) {
    const rows = dimension === 'time'
      ? timeLinks
      : dimension === 'transfer'
        ? transferLinks
        : dimension === 'role'
          ? roleLinks
          : bridgeLinks
    return rows.filter((row) => row.outcome_id === outcomeId)
  }

  function definitionsFor(dimension: LinkDimension) {
    if (dimension === 'time') return timeDefs
    if (dimension === 'transfer') return transferDefs
    if (dimension === 'role') return roleDefs
    return bridgeDefs
  }

  async function reviewDistance(row: Classification, reviewStatus: 'approved' | 'rejected') {
    const payload: any = {
      distance_mapping_source: 'human_review',
      distance_review_status: reviewStatus,
      updated_at: new Date().toISOString(),
    }
    if (reviewStatus === 'approved' && row.outcome_distance) payload.distance_status = 'reviewed_mapped'
    const { error } = await supabase.from('outcome_stage4_classification').update(payload).eq('outcome_id', row.outcome_id)
    if (error) onError(error.message)
    else await load()
  }

  async function setDistance(outcomeId: number, value?: string) {
    if (!value) return
    const { error } = await supabase.from('outcome_stage4_classification').update({
      outcome_distance: value,
      distance_status: 'reviewed_mapped',
      distance_mapping_source: 'human_review',
      distance_review_status: 'approved',
      updated_at: new Date().toISOString(),
    }).eq('outcome_id', outcomeId)
    if (error) onError(error.message)
    else await load()
  }

  async function markDistanceNoMapping(outcomeId: number) {
    const { error } = await supabase.from('outcome_stage4_classification').update({
      outcome_distance: null,
      distance_status: 'reviewed_no_mapping',
      distance_mapping_source: 'human_review',
      distance_review_status: 'approved',
      updated_at: new Date().toISOString(),
    }).eq('outcome_id', outcomeId)
    if (error) onError(error.message)
    else await load()
  }

  async function reviewLink(dimension: LinkDimension, row: LinkRow, reviewStatus: 'approved' | 'rejected') {
    const meta = dimensionMeta[dimension]
    const { error } = await supabase
      .from(meta.table)
      .update({ mapping_source: 'human_review', review_status: reviewStatus, updated_at: new Date().toISOString() })
      .eq('outcome_id', row.outcome_id)
      .eq(meta.valueColumn, row.value)
    if (error) {
      onError(error.message)
      return
    }

    const statusField = `${dimension}_status`
    const sourceField = `${dimension}_mapping_source`
    const reviewField = `${dimension}_review_status`
    const payload: any = {
      [sourceField]: 'human_review',
      [reviewField]: reviewStatus === 'approved' ? 'approved' : 'reviewed',
      updated_at: new Date().toISOString(),
    }
    if (reviewStatus === 'approved') payload[statusField] = 'reviewed_mapped'
    const { error: classificationError } = await supabase
      .from('outcome_stage4_classification')
      .update(payload)
      .eq('outcome_id', row.outcome_id)
    if (classificationError) onError(classificationError.message)
    else await load()
  }

  async function addLink(dimension: LinkDimension, outcomeId: number) {
    const meta = dimensionMeta[dimension]
    const key = `${outcomeId}:${dimension}`
    const definitions = definitionsFor(dimension)
    const value = addChoice[key] || definitions[0]?.value
    if (!value) return

    const payload: any = {
      outcome_id: outcomeId,
      [meta.valueColumn]: value,
      rationale: 'Human-reviewed Stage 4 Workbench mapping.',
      mapping_source: 'human_review',
      review_status: 'approved',
      updated_at: new Date().toISOString(),
    }
    const { error } = await supabase.from(meta.table).upsert(payload, { onConflict: `outcome_id,${meta.valueColumn}` })
    if (error) {
      onError(error.message)
      return
    }

    const { error: classificationError } = await supabase.from('outcome_stage4_classification').update({
      [`${dimension}_status`]: 'reviewed_mapped',
      [`${dimension}_mapping_source`]: 'human_review',
      [`${dimension}_review_status`]: 'approved',
      updated_at: new Date().toISOString(),
    }).eq('outcome_id', outcomeId)
    if (classificationError) onError(classificationError.message)
    else await load()
  }

  async function markNoMapping(dimension: LinkDimension, outcomeId: number) {
    const meta = dimensionMeta[dimension]
    const { error: linksError } = await supabase
      .from(meta.table)
      .update({ mapping_source: 'human_review', review_status: 'rejected', updated_at: new Date().toISOString() })
      .eq('outcome_id', outcomeId)
      .eq('review_status', 'proposed')
    if (linksError) {
      onError(linksError.message)
      return
    }

    const { error } = await supabase.from('outcome_stage4_classification').update({
      [`${dimension}_status`]: 'reviewed_no_mapping',
      [`${dimension}_mapping_source`]: 'human_review',
      [`${dimension}_review_status`]: 'approved',
      updated_at: new Date().toISOString(),
    }).eq('outcome_id', outcomeId)
    if (error) onError(error.message)
    else await load()
  }

  function dimensionRow(
    dimension: LinkDimension,
    label: string,
    row: Classification,
  ) {
    const links = linksFor(dimension, row.outcome_id)
    const definitions = definitionsFor(dimension)
    const status = row[`${dimension}_status` as keyof Classification] as string
    const mappingSource = row[`${dimension}_mapping_source` as keyof Classification] as string
    const reviewStatus = row[`${dimension}_review_status` as keyof Classification] as string
    const key = `${row.outcome_id}:${dimension}`

    return (
      <div className="product-card" style={{ marginTop: 8 }}>
        <div className="product-head">
          <div><span className="field-label">{label}</span><ReviewStatus mappingSource={mappingSource} reviewStatus={reviewStatus} /></div>
          <span className="status-pill">{humanize(status)}</span>
        </div>
        {links.length ? (
          <div className="stack-list">
            {links.map((link) => (
              <div key={`${dimension}-${link.value}`} className="detail-meta-row">
                <strong>{humanize(link.value)}</strong>
                <ReviewStatus mappingSource={link.mapping_source} reviewStatus={link.review_status} />
                {canEdit && link.review_status === 'proposed' && (
                  <>
                    <button className="icon-button mini" title="Approve" onClick={() => reviewLink(dimension, link, 'approved')}><Check size={13} /></button>
                    <button className="icon-button mini" title="Reject" onClick={() => reviewLink(dimension, link, 'rejected')}><X size={13} /></button>
                  </>
                )}
              </div>
            ))}
          </div>
        ) : <EmptyLine>No mapped value.</EmptyLine>}
        {canEdit && (
          <div className="detail-meta-row" style={{ marginTop: 8 }}>
            <select
              className="select-input"
              value={addChoice[key] || definitions[0]?.value || ''}
              onChange={(event) => setAddChoice((current) => ({ ...current, [key]: event.target.value }))}
            >
              {definitions.map((definition) => <option key={definition.value} value={definition.value}>{definition.label}</option>)}
            </select>
            <button className="secondary-button fit" onClick={() => addLink(dimension, row.outcome_id)}><Plus size={13} /> Add</button>
            <button className="text-button" onClick={() => markNoMapping(dimension, row.outcome_id)}>Reviewed: no mapping</button>
          </div>
        )}
      </div>
    )
  }

  return (
    <DetailSection title="Stage 4 outcome semantics" icon={<ClipboardCheck size={17} />}>
      <div className="record-note">
        Outcome distance, time, transfer, scientific role and Bridge evidence are reviewed independently. The historical evidence rung remains an audit snapshot only. Agent-generated mappings remain proposals until a human reviewer accepts, corrects or rejects them.
      </div>

      {loading && <div className="small-copy" style={{ marginTop: 12 }}><RefreshCw className="spin" size={14} /> Loading Stage 4 mappings…</div>}

      {!loading && !outcomes.length && <EmptyLine>No normalized outcomes for this source.</EmptyLine>}

      {!loading && outcomes.map((outcome) => {
        const row = classifications.find((item) => item.outcome_id === outcome.outcome_id)
        if (!row) return <EmptyLine key={outcome.outcome_id}>Missing Stage 4 classification row for {outcome.outcome_name}.</EmptyLine>

        return (
          <div className="protocol-card" key={outcome.outcome_id} style={{ marginTop: 14 }}>
            <div className="protocol-head">
              <div>
                <strong>{outcome.outcome_name}</strong>
                <div className="detail-meta-row" style={{ marginTop: 4 }}>
                  <span className="status-pill">Legacy rung: {humanize(row.legacy_rung_snapshot)}</span>
                  <span className="status-pill">Raw time: {humanize(row.raw_timepoint_snapshot)}</span>
                  <span className="status-pill">Result: {humanize(outcome.result_direction)}</span>
                </div>
              </div>
            </div>

            <div className="product-card" style={{ marginTop: 8 }}>
              <div className="product-head">
                <div><span className="field-label">Outcome distance</span><ReviewStatus mappingSource={row.distance_mapping_source} reviewStatus={row.distance_review_status} /></div>
                <span className="status-pill">{humanize(row.distance_status)}</span>
              </div>
              <div className="detail-meta-row" style={{ marginTop: 6 }}>
                <strong>{row.outcome_distance ? humanize(row.outcome_distance) : 'No mapped distance'}</strong>
                {canEdit && row.distance_review_status === 'proposed' && row.outcome_distance && (
                  <>
                    <button className="icon-button mini" title="Approve" onClick={() => reviewDistance(row, 'approved')}><Check size={13} /></button>
                    <button className="icon-button mini" title="Reject" onClick={() => reviewDistance(row, 'rejected')}><X size={13} /></button>
                  </>
                )}
              </div>
              {canEdit && (
                <div className="detail-meta-row" style={{ marginTop: 8 }}>
                  <select
                    className="select-input"
                    value={addChoice[`${row.outcome_id}:distance`] || distanceDefs[0]?.value || ''}
                    onChange={(event) => setAddChoice((current) => ({ ...current, [`${row.outcome_id}:distance`]: event.target.value }))}
                  >
                    {distanceDefs.map((definition) => <option key={definition.value} value={definition.value}>{definition.label}</option>)}
                  </select>
                  <button className="secondary-button fit" onClick={() => setDistance(row.outcome_id, addChoice[`${row.outcome_id}:distance`] || distanceDefs[0]?.value)}><Check size={13} /> Set/approve</button>
                  <button className="text-button" onClick={() => markDistanceNoMapping(row.outcome_id)}>Reviewed: no mapping</button>
                </div>
              )}
            </div>

            {dimensionRow('time', 'Time class', row)}
            {dimensionRow('transfer', 'Transfer axis', row)}
            {dimensionRow('role', 'Outcome role', row)}
            {dimensionRow('bridge', 'Bridge evidence', row)}

            {row.rationale && <p className="small-copy" style={{ marginTop: 10 }}>{row.rationale}</p>}
          </div>
        )
      })}
    </DetailSection>
  )
}
