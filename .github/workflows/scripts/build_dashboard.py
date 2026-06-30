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
  header {
    margin-bottom: 24px;
  }
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
  .panel h2 { margin-top: 0; font-size: 1.1rem; }
  .charts-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
    gap: 16px;
  }
  canvas { max-height: 320px; }
  table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 500; }
  tr:hover { background: rgba(255,255,255,0.03); }
  .scroll-table { max-height: 420px; overflow-y: auto; }
  .updated { color: var(--muted); font-size: 0.75rem; margin-top: 24px; text-align: center; }
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
  <h2>Cumulative Flow Diagram (CFD)</h2>
  <canvas id="cfdChart"></canvas>
</div>

<div class="charts-row">
  <div class="panel">
    <h2>Distribuição — Idade de Backlog (dias)</h2>
    <canvas id="backlogChart"></canvas>
  </div>
  <div class="panel">
    <h2>Distribuição — Lead Time (dias)</h2>
    <canvas id="leadTimeChart"></canvas>
  </div>
  <div class="panel">
    <h2>Distribuição — Cycle Time (dias)</h2>
    <canvas id="cycleTimeChart"></canvas>
  </div>
  <div class="panel">
    <h2>Distribuição — Tempo para Refinar (dias)</h2>
    <canvas id="refinarChart"></canvas>
  </div>
</div>

<div class="panel">
  <h2>Detalhamento por item</h2>
  <div class="scroll-table">
    <table id="detailTable">
      <thead>
        <tr>
          <th>Chave</th>
          <th>Resumo</th>
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

Chart.defaults.color = "#94a3b8";
Chart.defaults.borderColor = "#334155";

// ---- CFD ----
new Chart(document.getElementById("cfdChart"), {
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
    }
  }
});

// ---- Histogramas simples ----
function buildHistogram(values, bucketSize) {
  if (!values.length) return { labels: [], data: [] };
  const max = Math.max(...values);
  const buckets = {};
  for (const v of values) {
    const bucket = Math.floor(v / bucketSize) * bucketSize;
    buckets[bucket] = (buckets[bucket] || 0) + 1;
  }
  const labels = Object.keys(buckets).map(Number).sort((a,b)=>a-b);
  return {
    labels: labels.map(l => `${l}-${l + bucketSize}`),
    data: labels.map(l => buckets[l])
  };
}

function renderDistribution(canvasId, metricArray, color) {
  const values = metricArray.map(i => i.dias);
  const hist = buildHistogram(values, 2);
  new Chart(document.getElementById(canvasId), {
    type: "bar",
    data: {
      labels: hist.labels,
      datasets: [{ label: "Itens", data: hist.data, backgroundColor: color }]
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
    }
  });
}

renderDistribution("backlogChart", DATA.metricas.idade_backlog, "#60a5fa");
renderDistribution("leadTimeChart", DATA.metricas.lead_time, "#34d399");
renderDistribution("cycleTimeChart", DATA.metricas.cycle_time, "#fbbf24");
renderDistribution("refinarChart", DATA.metricas.tempo_refinar, "#fb923c");

// ---- Tabela detalhada ----
const tbody = document.querySelector("#detailTable tbody");
const fmt = v => v === null || v === undefined ? "—" : v;
DATA.issues.forEach(row => {
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <td>${row.key}</td>
    <td>${row.summary}</td>
    <td>${row.status}</td>
    <td>${fmt(row.backlog_age_dias)}</td>
    <td>${fmt(row.lead_time_dias)}</td>
    <td>${fmt(row.cycle_time_dias)}</td>
    <td>${fmt(row.tempo_refinar_dias)}</td>
  `;
  tbody.appendChild(tr);
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
