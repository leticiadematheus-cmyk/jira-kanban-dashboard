#!/usr/bin/env python3
"""
Gera docs/index.html (dashboard estático) embutindo o conteúdo de docs/data.json.
Usa Chart.js via CDN. Não faz nenhuma chamada à API do Jira neste passo.
"""

import json
import os

BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
DATA_PATH = os.path.join(BASE_DIR, "data.json")
OUTPUT_PATH = os.path.join(BASE_DIR, "index.html")

CFD_COLORS = {
    "Backlog": "#94a3b8",
    "Priorizado": "#60a5fa",
    "Em andamento": "#fbbf24",
    "Em revisão": "#fb923c",
    "Pendente": "#f87171",
    "Concluído": "#34d399",
}

# Apenas ordena as prioridades conhecidas. Nomes que não estiverem aqui
# continuam aparecendo (ordenados alfabeticamente ao final) — a lista real
# é derivada dos dados no navegador.
PRIORITY_ORDER = ["Urgente", "Alta", "Média", "Baixa", "Muito baixa", "Sem prioridade"]
PRIORITY_COLORS = {
    "Urgente": "#ef4444",
    "Alta": "#f97316",
    "Média": "#eab308",
    "Baixa": "#60a5fa",
    "Muito baixa": "#94a3b8",
    "Sem prioridade": "#64748b",
}

TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Métricas Kanban - CRM Sistêmico</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0f172a;
    --card: #1e293b;
    --text: #e2e8f0;
    --muted: #94a3b8;
    --accent: #38bdf8;
    --border: #334155;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
  }
  header { margin-bottom: 16px; }
  h1 { font-size: 1.5rem; margin: 0 0 4px; }
  .subtitle { color: var(--muted); font-size: 0.85rem; }
  .period-bar {
    display: flex;
    align-items: flex-end;
    gap: 16px;
    flex-wrap: wrap;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 24px;
  }
  .period-bar .field { display: flex; flex-direction: column; gap: 4px; }
  .period-bar label { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; }
  .period-bar input[type="date"] {
    background: #0f172a; color: var(--text);
    border: 1px solid var(--border); border-radius: 8px;
    padding: 6px 10px; font-size: 0.85rem;
  }
  .btn {
    background: var(--accent); color: #04222f; border: none;
    border-radius: 8px; padding: 7px 14px; font-size: 0.82rem;
    font-weight: 600; cursor: pointer;
  }
  .btn.secondary { background: transparent; color: var(--muted); border: 1px solid var(--border); }
  .period-note { color: var(--muted); font-size: 0.72rem; margin-left: auto; max-width: 340px; line-height: 1.35; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }
  .kpi {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
  }
  .kpi .label { color: var(--muted); font-size: 0.8rem; margin-bottom: 6px; }
  .kpi .value { font-size: 1.8rem; font-weight: 600; }
  .kpi .unit { font-size: 0.9rem; color: var(--muted); font-weight: 400; }
  .kpi .count { color: var(--muted); font-size: 0.72rem; margin-top: 4px; }
  .panel {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
  }
  .panel-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 8px;
  }
  .panel h2 { margin: 0; font-size: 1.1rem; }
  .hint { color: var(--muted); font-size: 0.75rem; margin: 0 0 12px; }
  select {
    background: #0f172a;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 0.85rem;
  }
  .charts-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
    gap: 16px;
  }
  canvas { max-height: 320px; cursor: pointer; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 500; }
  tr:hover { background: rgba(255,255,255,0.03); }
  .scroll-table { max-height: 420px; overflow-y: auto; }
  .updated { color: var(--muted); font-size: 0.75rem; margin-top: 24px; text-align: center; }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
  }
  .empty-note { color: var(--muted); font-size: 0.8rem; padding: 24px 0; text-align: center; }
  .drill-panel {
    display: none;
    margin-top: 14px;
    border-top: 1px dashed var(--border);
    padding-top: 14px;
  }
  .drill-panel.open { display: block; }
  .drill-panel .drill-title {
    font-size: 0.85rem;
    color: var(--muted);
    margin-bottom: 8px;
  }
  .drill-panel table { font-size: 0.8rem; }
  .filter-input {
    background: #0f172a;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 0.85rem;
    width: 220px;
  }
  .table-toolbar {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 12px;
  }
</style>
</head>
<body>

<header>
  <h1>Métricas Kanban — CRM Sistêmico</h1>
  <div class="subtitle">__SUBTITLE__</div>
</header>

<div class="period-bar">
  <div class="field">
    <label for="dateStart">Data início</label>
    <input type="date" id="dateStart" />
  </div>
  <div class="field">
    <label for="dateEnd">Data fim</label>
    <input type="date" id="dateEnd" />
  </div>
  <button class="btn" id="applyPeriod">Aplicar período</button>
  <button class="btn secondary" id="resetPeriod">Limpar</button>
  <div class="period-note">
    O período filtra cada métrica pela data que faz sentido: Lead/Cycle Time pela
    <b>conclusão</b>, Tempo para Refinar pela data em que a label foi adicionada,
    Idade de Backlog e a tabela pela <b>criação</b>, e o CFD pela janela de tempo.
  </div>
</div>

<div class="grid">
  <div class="kpi">
    <div class="label">Idade média de Backlog</div>
    <div class="value"><span id="kpiBacklog">—</span> <span class="unit">dias</span></div>
    <div class="count" id="kpiBacklogCount"></div>
  </div>
  <div class="kpi">
    <div class="label">Lead Time médio</div>
    <div class="value"><span id="kpiLeadTime">—</span> <span class="unit">dias</span></div>
    <div class="count" id="kpiLeadTimeCount"></div>
  </div>
  <div class="kpi">
    <div class="label">Cycle Time médio</div>
    <div class="value"><span id="kpiCycleTime">—</span> <span class="unit">dias</span></div>
    <div class="count" id="kpiCycleTimeCount"></div>
  </div>
  <div class="kpi">
    <div class="label">Tempo médio para Refinar</div>
    <div class="value"><span id="kpiRefinar">—</span> <span class="unit">dias</span></div>
    <div class="count" id="kpiRefinarCount"></div>
  </div>
  <div class="kpi">
    <div class="label">Itens no período</div>
    <div class="value"><span id="kpiTotal">—</span></div>
    <div class="count" id="kpiTotalNote"></div>
  </div>
</div>

<div class="panel">
  <div class="panel-head"><h2>Cumulative Flow Diagram (CFD)</h2></div>
  <p class="hint">Clique em um ponto do gráfico para ver os itens que estavam em cada status naquele dia.</p>
  <canvas id="cfdChart"></canvas>
  <div class="drill-panel" id="cfdDrill"></div>
</div>

<div class="charts-row">
  <div class="panel">
    <div class="panel-head">
      <h2>Distribuição — Idade de Backlog (dias)</h2>
      <select id="backlogPriorityFilter"></select>
    </div>
    <p class="hint">Clique em uma barra para ver os itens daquela faixa.</p>
    <canvas id="backlogChart"></canvas>
    <div class="drill-panel" id="backlogDrill"></div>
  </div>
  <div class="panel">
    <div class="panel-head">
      <h2>Distribuição — Lead Time (dias)</h2>
      <select id="leadTimePriorityFilter"></select>
    </div>
    <p class="hint">Clique em uma barra para ver os itens daquela faixa.</p>
    <canvas id="leadTimeChart"></canvas>
    <div class="drill-panel" id="leadTimeDrill"></div>
  </div>
  <div class="panel">
    <div class="panel-head">
      <h2>Distribuição — Cycle Time (dias)</h2>
      <select id="cycleTimePriorityFilter"></select>
    </div>
    <p class="hint">Clique em uma barra para ver os itens daquela faixa.</p>
    <canvas id="cycleTimeChart"></canvas>
    <div class="drill-panel" id="cycleTimeDrill"></div>
  </div>
  <div class="panel">
    <div class="panel-head">
      <h2>Distribuição — Tempo para Refinar (dias)</h2>
      <select id="refinarPriorityFilter"></select>
    </div>
    <p class="hint">Clique em uma barra para ver os itens daquela faixa.</p>
    <canvas id="refinarChart"></canvas>
    <div class="drill-panel" id="refinarDrill"></div>
  </div>
</div>

<div class="panel">
  <h2>Detalhamento por item</h2>
  <div class="table-toolbar">
    <input class="filter-input" id="tableFilter" placeholder="Filtrar por chave, resumo, tipo..." />
  </div>
  <div class="scroll-table">
    <table id="detailTable">
      <thead>
        <tr>
          <th>Chave</th>
          <th>Resumo</th>
          <th>Tipo</th>
          <th>Parent</th>
          <th>Prioridade</th>
          <th>Status atual</th>
          <th>Idade Backlog</th>
          <th>Lead Time</th>
          <th>Cycle Time</th>
          <th>Tempo p/ Refinar</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
</div>

<div class="updated">Atualizado automaticamente via GitHub Actions • Última geração: __GERADO_EM__</div>

<script>
const DATA = __DATA_JSON__;
const STATUS_COLORS = __STATUS_COLORS_JSON__;
const STATUS_ORDER = __STATUS_ORDER_JSON__;
const PRIORITY_ORDER = __PRIORITY_ORDER_JSON__;
const PRIORITY_COLORS = __PRIORITY_COLORS_JSON__;

Chart.defaults.color = "#94a3b8";
Chart.defaults.borderColor = "#334155";

const issueByKey = {};
DATA.issues.forEach(i => issueByKey[i.key] = i);

// ---------------------------------------------------------------------------
// Estado do filtro de período (datas em formato ISO YYYY-MM-DD)
// ---------------------------------------------------------------------------
let dateStart = null;
let dateEnd = null;

function inRange(iso) {
  // Itens sem data de referência (ex.: métrica ainda não aplicável) ficam de fora
  // do recorte por período quando há filtro ativo.
  if (!iso) return !dateStart && !dateEnd;
  if (dateStart && iso < dateStart) return false;
  if (dateEnd && iso > dateEnd) return false;
  return true;
}

function normPriority(p) { return p || "Sem prioridade"; }

// Prioridades reais presentes nos dados (não mais uma lista fixa).
function allPriorities() {
  const set = new Set();
  Object.values(DATA.metricas).forEach(arr => arr.forEach(i => set.add(normPriority(i.prioridade))));
  DATA.issues.forEach(i => set.add(normPriority(i.prioridade)));
  const known = PRIORITY_ORDER.filter(p => set.has(p));
  const extra = [...set].filter(p => !PRIORITY_ORDER.includes(p)).sort((a, b) => a.localeCompare(b, "pt-BR"));
  return [...known, ...extra];
}

function priorityBadge(p) {
  const label = normPriority(p);
  const color = PRIORITY_COLORS[label] || "#64748b";
  return `<span class="badge" style="background:${color}22;color:${color}">${label}</span>`;
}

function renderDrillList(containerId, keys, titleOverride) {
  const el = document.getElementById(containerId);
  if (!keys.length) {
    el.innerHTML = '<div class="drill-title">Nenhum item encontrado.</div>';
    el.classList.add("open");
    return;
  }
  let rows = keys.map(k => {
    const issue = issueByKey[k];
    if (!issue) return "";
    return `<tr>
      <td>${issue.key}</td>
      <td>${issue.summary}</td>
      <td>${issue.tipo || "—"}</td>
      <td>${issue.parent_key || "—"}</td>
      <td>${priorityBadge(issue.prioridade)}</td>
      <td>${issue.status}</td>
    </tr>`;
  }).join("");
  el.innerHTML = `
    <div class="drill-title">${titleOverride || (keys.length + " item(ns) nesta seleção")}</div>
    <table>
      <thead><tr><th>Chave</th><th>Resumo</th><th>Tipo</th><th>Parent</th><th>Prioridade</th><th>Status</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
  el.classList.add("open");
}

// ---------------------------------------------------------------------------
// KPIs
// ---------------------------------------------------------------------------
function avgArr(arr) {
  if (!arr.length) return "—";
  return (arr.reduce((s, i) => s + i.dias, 0) / arr.length).toFixed(1);
}

function updateKpis() {
  const b = DATA.metricas.idade_backlog.filter(i => inRange(i.data_ref));
  const l = DATA.metricas.lead_time.filter(i => inRange(i.data_ref));
  const c = DATA.metricas.cycle_time.filter(i => inRange(i.data_ref));
  const r = DATA.metricas.tempo_refinar.filter(i => inRange(i.data_ref));
  const totalItems = DATA.issues.filter(i => inRange(i.created)).length;

  document.getElementById("kpiBacklog").textContent = avgArr(b);
  document.getElementById("kpiLeadTime").textContent = avgArr(l);
  document.getElementById("kpiCycleTime").textContent = avgArr(c);
  document.getElementById("kpiRefinar").textContent = avgArr(r);
  document.getElementById("kpiTotal").textContent = totalItems;

  document.getElementById("kpiBacklogCount").textContent = `${b.length} item(ns)`;
  document.getElementById("kpiLeadTimeCount").textContent = `${l.length} concluído(s)`;
  document.getElementById("kpiCycleTimeCount").textContent = `${c.length} concluído(s)`;
  document.getElementById("kpiRefinarCount").textContent = `${r.length} refinado(s)`;
  document.getElementById("kpiTotalNote").textContent = (dateStart || dateEnd) ? "criados no período" : "total";
}

// ---------------------------------------------------------------------------
// CFD (recortado pela janela de período)
// ---------------------------------------------------------------------------
let cfdChart;

function filteredCfd() {
  const dates = DATA.cfd.dates || [];
  const idx = [];
  dates.forEach((d, i) => {
    if ((!dateStart || d >= dateStart) && (!dateEnd || d <= dateEnd)) idx.push(i);
  });
  const series = {};
  STATUS_ORDER.forEach(s => {
    const full = DATA.cfd.series[s] || [];
    series[s] = idx.map(i => full[i]);
  });
  return { dates: idx.map(i => dates[i]), series };
}

function renderCfd() {
  const cfd = filteredCfd();
  if (cfdChart) cfdChart.destroy();
  cfdChart = new Chart(document.getElementById("cfdChart"), {
    type: "line",
    data: {
      labels: cfd.dates,
      datasets: STATUS_ORDER.map(status => ({
        label: status,
        data: cfd.series[status] || [],
        borderColor: STATUS_COLORS[status],
        backgroundColor: STATUS_COLORS[status] + "55",
        fill: true,
        tension: 0.2,
        pointRadius: 0,
      }))
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      scales: {
        x: { stacked: true, ticks: { maxTicksLimit: 12 } },
        y: { stacked: true, beginAtZero: true }
      },
      onClick: (evt) => {
        const points = cfdChart.getElementsAtEventForMode(evt, "index", { intersect: false }, true);
        if (!points.length) return;
        const targetDate = cfd.dates[points[0].index];
        const keys = DATA.issues.filter(i => STATUS_ORDER.includes(i.status)).map(i => i.key);
        renderDrillList("cfdDrill", keys, `Itens com status atual (referência: ${targetDate})`);
      }
    }
  });
}

// ---------------------------------------------------------------------------
// Histogramas com drill-down + filtro de prioridade + filtro de período
// ---------------------------------------------------------------------------
function buildHistogram(items, bucketSize) {
  if (!items.length) return { labels: [], data: [], bucketKeys: [] };
  const buckets = {};
  for (const item of items) {
    const bucket = Math.floor(item.dias / bucketSize) * bucketSize;
    if (!buckets[bucket]) buckets[bucket] = [];
    buckets[bucket].push(item.key);
  }
  const labels = Object.keys(buckets).map(Number).sort((a, b) => a - b);
  return {
    labels: labels.map(l => `${l}-${l + bucketSize}`),
    data: labels.map(l => buckets[l].length),
    bucketKeys: labels.map(l => buckets[l])
  };
}

const DIST_CONFIGS = [
  { canvasId: "backlogChart", drillId: "backlogDrill", metricKey: "idade_backlog", color: "#60a5fa", filterId: "backlogPriorityFilter" },
  { canvasId: "leadTimeChart", drillId: "leadTimeDrill", metricKey: "lead_time", color: "#34d399", filterId: "leadTimePriorityFilter" },
  { canvasId: "cycleTimeChart", drillId: "cycleTimeDrill", metricKey: "cycle_time", color: "#fbbf24", filterId: "cycleTimePriorityFilter" },
  { canvasId: "refinarChart", drillId: "refinarDrill", metricKey: "tempo_refinar", color: "#fb923c", filterId: "refinarPriorityFilter" },
];

const distCharts = {};

function drawDist(cfg) {
  const sel = document.getElementById(cfg.filterId).value || "Todas as prioridades";
  let items = DATA.metricas[cfg.metricKey].filter(i => inRange(i.data_ref));
  if (sel !== "Todas as prioridades") {
    items = items.filter(i => normPriority(i.prioridade) === sel);
  }
  const hist = buildHistogram(items, 2);
  if (distCharts[cfg.canvasId]) distCharts[cfg.canvasId].destroy();
  distCharts[cfg.canvasId] = new Chart(document.getElementById(cfg.canvasId), {
    type: "bar",
    data: {
      labels: hist.labels,
      datasets: [{ label: "Itens", data: hist.data, backgroundColor: cfg.color }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
      onClick: (evt, elements) => {
        if (!elements.length) return;
        renderDrillList(cfg.drillId, hist.bucketKeys[elements[0].index]);
      }
    }
  });
}

function initDistFilters() {
  const priorities = ["Todas as prioridades", ...allPriorities()];
  DIST_CONFIGS.forEach(cfg => {
    const select = document.getElementById(cfg.filterId);
    select.innerHTML = priorities.map(p => `<option value="${p}">${p}</option>`).join("");
    select.addEventListener("change", () => {
      drawDist(cfg);
      document.getElementById(cfg.drillId).classList.remove("open");
    });
  });
}

// ---------------------------------------------------------------------------
// Tabela (também respeita o período, pela data de criação)
// ---------------------------------------------------------------------------
const tbody = document.querySelector("#detailTable tbody");
const fmt = v => v === null || v === undefined ? "—" : v;

function currentTableRows() {
  const term = (document.getElementById("tableFilter").value || "").toLowerCase();
  return DATA.issues.filter(row => inRange(row.created)).filter(row =>
    (row.key || "").toLowerCase().includes(term) ||
    (row.summary || "").toLowerCase().includes(term) ||
    (row.tipo || "").toLowerCase().includes(term) ||
    (row.status || "").toLowerCase().includes(term) ||
    (row.prioridade || "").toLowerCase().includes(term)
  );
}

function renderTable() {
  const rows = currentTableRows();
  tbody.innerHTML = "";
  rows.forEach(row => {
    const tr = document.createElement("tr");
    const parentLabel = row.parent_key
      ? `${row.parent_key}${row.parent_summary ? " — " + row.parent_summary : ""}`
      : "—";
    tr.innerHTML = `
      <td>${row.key}</td>
      <td>${row.summary}</td>
      <td>${row.tipo || "—"}</td>
      <td>${parentLabel}</td>
      <td>${priorityBadge(row.prioridade)}</td>
      <td>${row.status}</td>
      <td>${fmt(row.backlog_age_dias)}</td>
      <td>${fmt(row.lead_time_dias)}</td>
      <td>${fmt(row.cycle_time_dias)}</td>
      <td>${fmt(row.tempo_refinar_dias)}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ---------------------------------------------------------------------------
// Orquestração
// ---------------------------------------------------------------------------
function renderAll() {
  updateKpis();
  renderCfd();
  DIST_CONFIGS.forEach(cfg => {
    drawDist(cfg);
    document.getElementById(cfg.drillId).classList.remove("open");
  });
  document.getElementById("cfdDrill").classList.remove("open");
  renderTable();
}

function computeBounds() {
  // Menor e maior data presentes nos dados, para limitar os inputs de data.
  const dates = [...(DATA.cfd.dates || [])];
  DATA.issues.forEach(i => { if (i.created) dates.push(i.created); });
  Object.values(DATA.metricas).forEach(arr => arr.forEach(i => { if (i.data_ref) dates.push(i.data_ref); }));
  if (!dates.length) return { min: null, max: null };
  dates.sort();
  return { min: dates[0], max: dates[dates.length - 1] };
}

const bounds = computeBounds();
const startInput = document.getElementById("dateStart");
const endInput = document.getElementById("dateEnd");
if (bounds.min) { startInput.min = bounds.min; endInput.min = bounds.min; startInput.value = bounds.min; }
if (bounds.max) { startInput.max = bounds.max; endInput.max = bounds.max; endInput.value = bounds.max; }

document.getElementById("applyPeriod").addEventListener("click", () => {
  dateStart = startInput.value || null;
  dateEnd = endInput.value || null;
  if (dateStart && dateEnd && dateStart > dateEnd) {
    const tmp = dateStart; dateStart = dateEnd; dateEnd = tmp;
    startInput.value = dateStart; endInput.value = dateEnd;
  }
  renderAll();
});

document.getElementById("resetPeriod").addEventListener("click", () => {
  dateStart = null;
  dateEnd = null;
  startInput.value = bounds.min || "";
  endInput.value = bounds.max || "";
  renderAll();
});

document.getElementById("tableFilter").addEventListener("input", renderTable);

// Início: sem recorte (mostra tudo), como no comportamento original.
initDistFilters();
renderAll();
</script>
</body>
</html>
"""


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = TEMPLATE
    html = html.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False))
    html = html.replace("__STATUS_COLORS_JSON__", json.dumps(CFD_COLORS, ensure_ascii=False))
    html = html.replace("__STATUS_ORDER_JSON__", json.dumps(list(CFD_COLORS.keys()), ensure_ascii=False))
    html = html.replace("__PRIORITY_ORDER_JSON__", json.dumps(PRIORITY_ORDER, ensure_ascii=False))
    html = html.replace("__PRIORITY_COLORS_JSON__", json.dumps(PRIORITY_COLORS, ensure_ascii=False))
    html = html.replace("__SUBTITLE__", f'JQL: {data["jql"]}')
    html = html.replace("__GERADO_EM__", data["gerado_em"])

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
