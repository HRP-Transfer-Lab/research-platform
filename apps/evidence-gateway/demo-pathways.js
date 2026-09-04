import { fetchGatewayEvidence } from './gateway-client.js'

const state = {
  records: [],
  recommendations: null,
  activeScenario: null,
}

const $ = (id) => document.getElementById(id)

function esc(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function humanize(value) {
  if (!value) return 'Not backfilled'
  const labels = {
    personal: 'Personal',
    performance_work: 'Performance & work',
    health_clinical_adjacent: 'Health & clinical-adjacent',
    direct_intervention: 'Direct intervention',
    evidence_synthesis: 'Evidence synthesis',
    mechanism: 'Mechanism',
    protocol: 'Protocol',
    approved: 'Approved',
    provisional: 'Provisional',
    excluded: 'Boundary / excluded',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  }
  return labels[value] || String(value).replaceAll('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function setControl(id, value) {
  const control = $(id)
  if (!control || value == null) return
  control.value = value
  control.dispatchEvent(new Event('input', { bubbles: true }))
}

function applyFilters(filters = {}) {
  setControl('searchInput', filters.q ?? '')
  setControl('statusFilter', filters.status ?? 'all')
  setControl('domainFilter', filters.domain ?? 'all')
  setControl('roleFilter', filters.role ?? 'all')
  setControl('priorityFilter', filters.priority ?? 'all')
  setControl('sortFilter', filters.sort ?? 'newest')
}

function gatewayQueryForScenario(scenario) {
  return {
    contract_version: 'csi-evidence-demo-query-v1',
    mode: 'demo',
    situation_id: scenario.id,
    domain: scenario.domain,
    filters: {
      ...scenario.gateway_filters,
      include_status_labels: true,
      exclude_boundary_records_from_recommendation: true,
    },
    evidence_source_ids: scenario.evidence_source_ids,
    governance: {
      provisional_evidence_allowed_for_demo: true,
      production_claims_require_approved_evidence: true,
    },
  }
}

function updateUrl(scenarioId) {
  const url = new URL(window.location.href)
  if (scenarioId) url.searchParams.set('scenario', scenarioId)
  else url.searchParams.delete('scenario')
  history.replaceState({}, '', url)
}

function scenarioEvidence(scenario) {
  const byId = new Map(state.records.map((record) => [record.source_id, record]))
  return scenario.evidence_source_ids
    .map((id) => byId.get(id))
    .filter(Boolean)
}

function focusEvidence(record) {
  applyFilters({
    q: record.title,
    status: record.evidence_status || 'all',
    domain: 'all',
    role: 'all',
    priority: 'all',
    sort: 'newest',
  })
  document.querySelector('.gateway-layout')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function renderScenario(scenario) {
  const panel = $('demoRecommendationPanel')
  if (!panel) return
  const evidence = scenarioEvidence(scenario)
  const query = gatewayQueryForScenario(scenario)

  panel.hidden = false
  panel.innerHTML = `
    <div class="demo-rec-head">
      <div>
        <div class="demo-rec-kicker">${esc(scenario.label)} · evidence-backed demo output</div>
        <h3>${esc(scenario.title)}</h3>
        <p>${esc(scenario.situation)}</p>
      </div>
      <button id="closeDemoRecommendation" class="demo-icon-button" type="button" aria-label="Close demo recommendation">×</button>
    </div>
    <div class="demo-rec-grid">
      <section class="demo-rec-main">
        <div class="demo-rec-label">Recommendation logic</div>
        <p class="demo-rec-summary">${esc(scenario.recommendation)}</p>
        <ol class="demo-action-list">
          ${scenario.actions.map((action) => `<li>${esc(action)}</li>`).join('')}
        </ol>
        <div class="demo-caveat">${esc(scenario.caveat)}</div>
      </section>
      <aside class="demo-evidence-stack">
        <div class="demo-rec-label">Evidence signals used</div>
        ${evidence.map((record) => `
          <button class="demo-evidence-ref" type="button" data-source-id="${esc(record.source_id)}">
            <span class="demo-evidence-status ${esc(record.evidence_status || 'provisional')}">${esc(humanize(record.evidence_status))}</span>
            <strong>${esc(record.title)}</strong>
            <small>${esc([record.publication_year, humanize(record.paper_role), humanize(record.priority)].filter(Boolean).join(' · '))}</small>
          </button>
        `).join('') || '<div class="demo-no-evidence">Referenced evidence is not present in the current snapshot.</div>'}
      </aside>
    </div>
    <div class="demo-query-row">
      <div>
        <strong>CSI demo query</strong>
        <span>Machine-readable evidence request for a CSI Explorer prototype.</span>
      </div>
      <button id="copyCsiQuery" class="demo-secondary-button" type="button">Copy CSI query</button>
    </div>
    <pre id="csiQueryPreview" class="demo-query-preview">${esc(JSON.stringify(query, null, 2))}</pre>
  `

  $('closeDemoRecommendation')?.addEventListener('click', () => {
    panel.hidden = true
    state.activeScenario = null
    updateUrl(null)
  })

  $('copyCsiQuery')?.addEventListener('click', async (event) => {
    await navigator.clipboard.writeText(JSON.stringify(query, null, 2))
    const button = event.currentTarget
    const original = button.textContent
    button.textContent = 'Copied'
    setTimeout(() => { button.textContent = original }, 1200)
  })

  for (const button of panel.querySelectorAll('[data-source-id]')) {
    button.addEventListener('click', () => {
      const record = state.records.find((item) => item.source_id === button.dataset.sourceId)
      if (record) focusEvidence(record)
    })
  }
}

function openScenario(id, { updateHistory = true } = {}) {
  const scenario = state.recommendations?.scenarios?.find((item) => item.id === id)
  if (!scenario) return
  state.activeScenario = id
  applyFilters({
    q: '',
    sort: 'newest',
    ...scenario.gateway_filters,
  })
  renderScenario(scenario)
  document.querySelectorAll('.demo-pathway-card').forEach((button) => {
    button.classList.toggle('active', button.dataset.scenario === id)
  })
  if (updateHistory) updateUrl(id)
  $('demoRecommendationPanel')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

function renderPathways() {
  const metrics = document.querySelector('.metrics')
  if (!metrics || !state.recommendations?.scenarios?.length) return

  const section = document.createElement('section')
  section.className = 'demo-pathways'
  section.innerHTML = `
    <div class="demo-pathways-head">
      <div>
        <div class="demo-pathways-kicker">Working CSI demonstrations</div>
        <h2>See how the Gateway becomes an evidence layer for Personal, Work and Health CSI.</h2>
        <p>Each pathway applies a real Gateway query, produces a bounded recommendation and exposes the evidence IDs behind it.</p>
      </div>
      <div class="demo-pathways-contract">DEMO MODE · STATUS-LABELLED EVIDENCE</div>
    </div>
    <div class="demo-pathway-grid">
      ${state.recommendations.scenarios.map((scenario) => `
        <button class="demo-pathway-card demo-pathway-${esc(scenario.id)}" type="button" data-scenario="${esc(scenario.id)}">
          <span>${esc(scenario.label)}</span>
          <strong>${esc(scenario.title)}</strong>
          <small>${esc(scenario.situation)}</small>
          <em>Open demo →</em>
        </button>
      `).join('')}
    </div>
  `

  const panel = document.createElement('section')
  panel.id = 'demoRecommendationPanel'
  panel.className = 'demo-recommendation-panel'
  panel.hidden = true

  metrics.after(section, panel)

  for (const button of section.querySelectorAll('[data-scenario]')) {
    button.addEventListener('click', () => openScenario(button.dataset.scenario))
  }
}

function addCardNotes() {
  const list = $('resultsList')
  if (!list || !state.records.length) return
  const byTitle = new Map(state.records.map((record) => [record.title, record]))

  for (const card of list.querySelectorAll('.evidence-card')) {
    if (card.querySelector('.card-evidence-note')) continue
    const title = card.querySelector('h3')?.textContent
    const record = byTitle.get(title)
    if (!record?.evidence_note) continue
    const note = document.createElement('p')
    note.className = 'card-evidence-note'
    const text = String(record.evidence_note)
    note.textContent = text.length > 155 ? `${text.slice(0, 152)}…` : text
    const chips = card.querySelector('.card-chips')
    if (chips) card.insertBefore(note, chips)
    else card.append(note)
  }
}

function applyUrlState() {
  const params = new URLSearchParams(window.location.search)
  const scenario = params.get('scenario')
  if (scenario) {
    openScenario(scenario, { updateHistory: false })
    return
  }
  applyFilters({
    q: params.get('q') ?? '',
    status: params.get('status') ?? 'all',
    domain: params.get('domain') ?? 'all',
    role: params.get('role') ?? 'all',
    priority: params.get('priority') ?? 'all',
    sort: params.get('sort') ?? 'newest',
  })
}

async function startDemoLayer() {
  try {
    const [records, recommendationResponse] = await Promise.all([
      fetchGatewayEvidence(),
      fetch('./demo-recommendations.v1.json'),
    ])
    if (!recommendationResponse.ok) throw new Error('Could not load demo recommendation pathways.')
    state.records = records
    state.recommendations = await recommendationResponse.json()
    renderPathways()
    applyUrlState()
    addCardNotes()

    const list = $('resultsList')
    if (list) {
      const observer = new MutationObserver(() => addCardNotes())
      observer.observe(list, { childList: true, subtree: true })
    }

    window.HRPEvidenceGatewayDemo = Object.freeze({
      openScenario,
      applyFilters,
      gatewayQueryForScenario: (id) => {
        const scenario = state.recommendations?.scenarios?.find((item) => item.id === id)
        return scenario ? gatewayQueryForScenario(scenario) : null
      },
    })
  } catch (error) {
    console.error('HRP Evidence Gateway demo layer failed to initialise', error)
  }
}

void startDemoLayer()
