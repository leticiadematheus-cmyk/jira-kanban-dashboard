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
  header { margin-bottom: 24px; }
  h1 { font-size: 1.5rem; margin: 0 0 4px; }
  .subtitle { color: var(--muted); font-size: 0.85rem; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
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

<div class="grid">
  <div class="kpi">
    <div class="label">Idade média de Backlog</div>
    <div class="value">__KPI_BACKLOG__ <span class="unit">dias</span></div>
  </div>
  <div class="kpi">
    <div class="label">Lead Time médio</div>
    <div class="value">__KPI_LEADTIME__ <span class="unit">dias</span></div>
  </div>
  <div class="kpi">
    <div class="label">Cycle Time médio</div>
    <div class="value">__KPI_CYCLETIME__ <span class="unit">dias</span></div>
  </div>
  <div class="kpi">
    <div class="label">Tempo médio para Refinar</div>
    <div class="value">__KPI_REFINAR__ <span class="unit">dias</span></div>
  </div>
  <div class="kpi">
    <div class="label">Total de itens analisados</div>
    <div class="value">__TOTAL_ISSUES__</div>
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
    <div class="panel-head"><h2>Distribuição — Idade de Backlog (dias)</h2></div>
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
    <div class="panel-head"><h2>Distribuição — Tempo para Refinar (dias)</h2></div>
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

function priorityBadge(p) {
  const color = PRIORITY_COLORS[p] || "#64748b";
  return `<span class="badge" style="background:${color}22;color:${color}">${p || "—"}</span>`;
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

// ---- CFD ----
const cfdChart = new Chart(document.getElementById("cfdChart"), {
  type: "line",
  data: {
    labels: DATA.cfd.dates,
    datasets: STATUS_ORDER.map(status => ({
      label: status,
      data: DATA.cfd.series[status] || [],
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
      const dateIndex = points[0].index;
      const targetDate = DATA.cfd.dates[dateIndex];
      // Aproximação: mostra itens cujo status atual corresponde a algum status do CFD.
      // Para granularidade exata por dia seria necessário guardar o histórico completo no client.
      const keys = DATA.issues
        .filter(i => STATUS_ORDER.includes(i.status))
        .map(i => i.key);
      renderDrillList("cfdDrill", keys, `Itens com status atual (referência: ${targetDate})`);
    }
  }
});

// ---- Histogramas com drill-down ----
function buildHistogram(items, bucketSize) {
  if (!items.length) return { labels: [], data: [], bucketKeys: [] };
  const buckets = {};
  for (const item of items) {
    const bucket = Math.floor(item.dias / bucketSize) * bucketSize;
    if (!buckets[bucket]) buckets[bucket] = [];
    buckets[bucket].push(item.key);
  }
  const labels = Object.keys(buckets).map(Number).sort((a,b)=>a-b);
  return {
    labels: labels.map(l => `${l}-${l + bucketSize}`),
    data: labels.map(l => buckets[l].length),
    bucketKeys: labels.map(l => buckets[l])
  };
}

function renderDistribution(canvasId, drillId, metricArray, color, priorityFilterId) {
  let chart;

  function draw(items) {
    const hist = buildHistogram(items, 2);
    if (chart) chart.destroy();
    chart = new Chart(document.getElementById(canvasId), {
      type: "bar",
      data: {
        labels: hist.labels,
        datasets: [{ label: "Itens", data: hist.data, backgroundColor: color }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        onClick: (evt, elements) => {
          if (!elements.length) return;
          const idx = elements[0].index;
          renderDrillList(drillId, hist.bucketKeys[idx]);
        }
      }
    });
  }

  draw(metricArray);

  if (priorityFilterId) {
    const select = document.getElementById(priorityFilterId);
    const priorities = ["Todas as prioridades", ...PRIORITY_ORDER.filter(p =>
      metricArray.some(i => i.prioridade === p)
    )];
    select.innerHTML = priorities.map(p => `<option value="${p}">${p}</option>`).join("");
    select.addEventListener("change", () => {
      const val = select.value;
      const filtered = val === "Todas as prioridades"
        ? metricArray
        : metricArray.filter(i => i.prioridade === val);
      draw(filtered);
      document.getElementById(drillId).classList.remove("open");
    });
  }
}

renderDistribution("backlogChart", "backlogDrill", DATA.metricas.idade_backlog, "#60a5fa", null);
renderDistribution("leadTimeChart", "leadTimeDrill", DATA.metricas.lead_time, "#34d399", "leadTimePriorityFilter");
renderDistribution("cycleTimeChart", "cycleTimeDrill", DATA.metricas.cycle_time, "#fbbf24", "cycleTimePriorityFilter");
renderDistribution("refinarChart", "refinarDrill", DATA.metricas.tempo_refinar, "#fb923c", null);

// ---- Tabela detalhada ----
const tbody = document.querySelector("#detailTable tbody");
const fmt = v => v === null || v === undefined ? "—" : v;

function renderTable(rows) {
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

renderTable(DATA.issues);

document.getElementById("tableFilter").addEventListener("input", (e) => {
  const term = e.target.value.toLowerCase();
  const filtered = DATA.issues.filter(row =>
    (row.key || "").toLowerCase().includes(term) ||
    (row.summary || "").toLowerCase().includes(term) ||
    (row.tipo || "").toLowerCase().includes(term) ||
    (row.status || "").toLowerCase().includes(term) ||
    (row.prioridade || "").toLowerCase().includes(term)
  );
  renderTable(filtered);
});
</script>
</body>
</html>
"""


def avg(values):
    if not values:
        return "—"
    return round(sum(v["dias"] for v in values) / len(values), 1)


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
    html = html.replace("__KPI_BACKLOG__", str(avg(data["metricas"]["idade_backlog"])))
    html = html.replace("__KPI_LEADTIME__", str(avg(data["metricas"]["lead_time"])))
    html = html.replace("__KPI_CYCLETIME__", str(avg(data["metricas"]["cycle_time"])))
    html = html.replace("__KPI_REFINAR__", str(avg(data["metricas"]["tempo_refinar"])))
    html = html.replace("__TOTAL_ISSUES__", str(data["total_issues"]))
    html = html.replace("__GERADO_EM__", data["gerado_em"])

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Dashboard gerado em {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
