export const EML_SCALE_VERSION = 'hrp-eml-v1'

export const EML_LABELS = Object.freeze({
  0: 'Rationale only',
  1: 'Mechanism / paradigm support',
  2: 'Initial direct demonstration',
  3: 'Replicated direct evidence',
  4: 'Convergent body',
  5: 'Transfer & durability',
  6: 'Real-world effectiveness',
  7: 'Generalised / scale-ready',
})

export const EML_COLORS = Object.freeze({
  0: 'neutral',
  1: 'blue',
  2: 'indigo',
  3: 'teal',
  4: 'emerald',
  5: 'green',
  6: 'lime',
  7: 'gold',
})

/**
 * Conservative screening-only contribution coding.
 * This is NOT a body-level effectiveness rating.
 * Screening metadata can justify only EML 0–2:
 * protocol -> 0; mechanism/measurement -> 1; direct intervention -> 2.
 * Synthesis, replication, transfer, effectiveness and scale-readiness require
 * structured extraction/appraisal before a higher body-level EML is shown.
 */
export function provisionalContribution(record) {
  const role = String(record?.paper_role || '').toLowerCase()
  let level = null
  let basis = 'Screening metadata does not justify an EML contribution level yet.'

  if (role === 'protocol') {
    level = 0
    basis = 'Protocol/rationale record: contributes rationale only until outcome evidence is available.'
  } else if (role === 'mechanism' || role === 'measurement') {
    level = 1
    basis = 'Mechanism/measurement record: contributes mechanistic or paradigm support, not direct effectiveness evidence.'
  } else if (role === 'direct_intervention') {
    level = 2
    basis = 'Direct intervention record: may contribute an initial direct demonstration after verification; replication and body-level effectiveness are not inferred.'
  } else if (role === 'evidence_synthesis') {
    basis = 'Evidence synthesis detected, but body-level EML requires structured synthesis appraisal and cannot be inferred from the screening label alone.'
  }

  return {
    scaleVersion: EML_SCALE_VERSION,
    level,
    label: level == null ? 'Body-level rating pending' : EML_LABELS[level],
    colorToken: level == null ? 'neutral' : EML_COLORS[level],
    basis,
    scope: 'record_contribution',
    provisional: true,
    bodyLevelAvailable: false,
  }
}

export function contributionSummary(records) {
  const contributions = records
    .map(provisionalContribution)
    .filter((item) => item.level != null)
  const levels = [...new Set(contributions.map((item) => item.level))].sort((a, b) => a - b)
  const max = levels.at(-1) ?? null
  const hasSynthesis = records.some((record) => record?.paper_role === 'evidence_synthesis')

  if (max == null) {
    return {
      min: null,
      max: null,
      label: hasSynthesis ? 'Body-level EML pending appraisal' : 'EML not yet classifiable',
      colorToken: 'neutral',
      bodyLevelAvailable: false,
    }
  }

  const min = levels[0]
  return {
    min,
    max,
    label: min === max
      ? `Provisional contribution EML ${max} · ${EML_LABELS[max]}`
      : `Provisional contribution range EML ${min}–${max}`,
    colorToken: EML_COLORS[max],
    bodyLevelAvailable: false,
  }
}
