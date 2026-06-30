#!/usr/bin/env python3
"""
Coleta dados do Jira via API REST v3, calcula métricas ágeis de Kanban
e gera um dashboard HTML estático autocontido.

Métricas calculadas:
  1. Idade de Backlog (tempo cumulativo em dias no status "Backlog")
  2. Lead Time (created -> Concluído)
  3. Cycle Time (Em andamento -> Concluído)
  4. Tempo para Refinar (created -> data em que a label "refinado" foi adicionada)
  5. CFD - Cumulative Flow Diagram (contagem cumulativa de itens por status ao longo do tempo)

Configuração via variáveis de ambiente:
  JIRA_BASE_URL   -> ex: https://acerto.atlassian.net
  JIRA_EMAIL      -> e-mail da conta usada para gerar o token
  JIRA_API_TOKEN  -> token gerado em id.atlassian.com
  JIRA_JQL        -> JQL usado para filtrar as issues (opcional, tem default abaixo)
"""

import os
import json
import base64
import urllib.request
import urllib.error
import datetime
from collections import defaultdict

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

JIRA_BASE_URL = os.environ["JIRA_BASE_URL"].rstrip("/")
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]

DEFAULT_JQL = (
    'project = CV AND "Gerência[Select List (multiple choices)]" = "CRM - Sistêmico" '
    "ORDER BY created ASC"
)
JIRA_JQL = os.environ.get("JIRA_JQL", DEFAULT_JQL)

# Nomes EXATOS dos status conforme informado
STATUS_BACKLOG = "Backlog"
STATUS_PRIORIZADO = "Priorizado"
STATUS_EM_ANDAMENTO = "Em andamento"
STATUS_EM_REVISAO = "Em revisão"
STATUS_PENDENTE = "Pendente"
STATUS_CONCLUIDO = "Concluído"

CFD_STATUS_ORDER = [
    STATUS_BACKLOG,
    STATUS_PRIORIZADO,
    STATUS_EM_ANDAMENTO,
    STATUS_EM_REVISAO,
    STATUS_PENDENTE,
    STATUS_CONCLUIDO,
]

LABEL_REFINADO = "refinado"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
OUTPUT_DATA_JSON = os.path.join(OUTPUT_DIR, "data.json")


# ---------------------------------------------------------------------------
# Cliente HTTP simples para a API do Jira
# ---------------------------------------------------------------------------

def _auth_header():
    token = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
    return f"Basic {token}"


def jira_get(path, params=None):
    url = f"{JIRA_BASE_URL}{path}"
    if params:
        query = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items())
        url = f"{url}?{query}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", _auth_header())
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Erro {e.code} ao chamar {url}: {body}")


def search_all_issues(jql):
    """Busca todas as issues que casam com o JQL, paginando, trazendo o changelog completo."""
    issues = []
    next_page_token = None
    while True:
        body = {
            "jql": jql,
            "maxResults": 100,
            "fields": ["created", "labels", "status", "summary", "issuetype", "parent", "priority"],
            "expand": "changelog",
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token

        url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(), method="POST"
        )
        req.add_header("Authorization", _auth_header())
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Erro {e.code} ao buscar issues: {e.read().decode()}")

        batch = data.get("issues", [])
        issues.extend(batch)

        # changelog pode vir paginado dentro da issue para casos com muitas transições
        for issue in batch:
            changelog = issue.get("changelog", {})
            if changelog.get("total", 0) > len(changelog.get("histories", [])):
                issue["changelog"]["histories"] = _fetch_full_changelog(issue["id"])

        next_page_token = data.get("nextPageToken")
        if not next_page_token or not batch:
            break
    return issues


def _fetch_full_changelog(issue_id):
    histories = []
    start_at = 0
    while True:
        data = jira_get(
            f"/rest/api/3/issue/{issue_id}/changelog",
            {"startAt": start_at, "maxResults": 100},
        )
        histories.extend(data.get("values", []))
        if data.get("isLast", True):
            break
        start_at += 100
    return histories


# ---------------------------------------------------------------------------
# Extração de transições de status e labels a partir do changelog
# ---------------------------------------------------------------------------

def parse_datetime(value):
    # Jira retorna formato tipo 2024-05-01T10:00:00.000-0300
    return datetime.datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")


def extract_status_transitions(issue):
    """Retorna lista ordenada de (timestamp, status_anterior, status_novo)."""
    transitions = []
    histories = issue.get("changelog", {}).get("histories", [])
    for history in histories:
        created = parse_datetime(history["created"])
        for item in history.get("items", []):
            if item.get("field") == "status":
                transitions.append((created, item.get("fromString"), item.get("toString")))
    transitions.sort(key=lambda t: t[0])
    return transitions


def extract_label_added_date(issue, label_name):
    """Retorna a data em que a label foi adicionada pela primeira vez, se houver."""
    label_name_norm = label_name.strip().lower()
    histories = issue.get("changelog", {}).get("histories", [])
    events = []
    for history in histories:
        created = parse_datetime(history["created"])
        for item in history.get("items", []):
            if item.get("field") == "labels":
                added = (item.get("toString") or "").split()
                added_norm = [a.strip().lower() for a in added]
                if label_name_norm in added_norm:
                    events.append(created)
    if events:
        return min(events)
    # fallback: se a label já está presente desde a criação e não há evento de adição
    current_labels = issue.get("fields", {}).get("labels", [])
    current_labels_norm = [l.strip().lower() for l in current_labels]
    if label_name_norm in current_labels_norm:
        return parse_datetime(issue["fields"]["created"])
    return None


# ---------------------------------------------------------------------------
# Cálculo das métricas
# ---------------------------------------------------------------------------

def calc_backlog_age_days(issue, now):
    """Soma todos os períodos em que a issue esteve no status Backlog."""
    transitions = extract_status_transitions(issue)
    created = parse_datetime(issue["fields"]["created"])

    # Constrói linha do tempo de status: (inicio, fim, status)
    timeline = []
    current_status = STATUS_BACKLOG  # assume-se que toda issue nasce em Backlog
    current_start = created

    for ts, _from, to in transitions:
        timeline.append((current_start, ts, current_status))
        current_status = to
        current_start = ts
    timeline.append((current_start, now, current_status))

    total_days = 0.0
    for start, end, status in timeline:
        if status == STATUS_BACKLOG:
            total_days += (end - start).total_seconds() / 86400.0
    return round(total_days, 2)


def calc_lead_time_days(issue):
    transitions = extract_status_transitions(issue)
    created = parse_datetime(issue["fields"]["created"])
    concluded_dates = [ts for ts, _f, to in transitions if to == STATUS_CONCLUIDO]
    if not concluded_dates:
        return None
    concluded_at = max(concluded_dates)
    return round((concluded_at - created).total_seconds() / 86400.0, 2)


def calc_cycle_time_days(issue):
    transitions = extract_status_transitions(issue)
    started_dates = [ts for ts, _f, to in transitions if to == STATUS_EM_ANDAMENTO]
    concluded_dates = [ts for ts, _f, to in transitions if to == STATUS_CONCLUIDO]
    if not started_dates or not concluded_dates:
        return None
    started_at = min(started_dates)
    concluded_at = max(concluded_dates)
    if concluded_at < started_at:
        return None
    return round((concluded_at - started_at).total_seconds() / 86400.0, 2)


def calc_tempo_refinar_days(issue):
    created = parse_datetime(issue["fields"]["created"])
    refined_at = extract_label_added_date(issue, LABEL_REFINADO)
    if refined_at is None:
        return None
    return round((refined_at - created).total_seconds() / 86400.0, 2)


def build_status_timeline(issue, now):
    """Retorna lista de (inicio, fim, status) para uso no CFD."""
    transitions = extract_status_transitions(issue)
    created = parse_datetime(issue["fields"]["created"])

    timeline = []
    current_status = STATUS_BACKLOG
    current_start = created
    for ts, _from, to in transitions:
        timeline.append((current_start, ts, current_status))
        current_status = to
        current_start = ts
    timeline.append((current_start, now, current_status))
    return timeline


def build_cfd(all_timelines, now):
    """
    Gera série temporal diária com contagem cumulativa de itens por status.
    all_timelines: lista de listas de (inicio, fim, status) por issue.
    """
    if not all_timelines:
        return {"dates": [], "series": {s: [] for s in CFD_STATUS_ORDER}}

    min_date = min(tl[0][0] for tl in all_timelines).date()
    max_date = now.date()

    dates = []
    d = min_date
    while d <= max_date:
        dates.append(d)
        d += datetime.timedelta(days=1)

    series = {status: [] for status in CFD_STATUS_ORDER}

    for day in dates:
        counts = defaultdict(int)
        # Para cada issue, identifica o status vigente ao final do dia
        for timeline in all_timelines:
            status_at_day = None
            for start, end, status in timeline:
                if start.date() <= day and (end.date() >= day or end == start):
                    status_at_day = status
            if status_at_day in CFD_STATUS_ORDER:
                counts[status_at_day] += 1

        for status in CFD_STATUS_ORDER:
            series[status].append(counts.get(status, 0))

    return {
        "dates": [d.isoformat() for d in dates],
        "series": series,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Buscando issues no Jira...")
    issues = search_all_issues(JIRA_JQL)
    print(f"{len(issues)} issues encontradas.")

    now = datetime.datetime.now()

    backlog_age = []
    lead_time = []
    cycle_time = []
    tempo_refinar = []
    all_timelines = []
    issue_rows = []

    for issue in issues:
        key = issue["key"]
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        status_atual = fields.get("status", {}).get("name", "")
        issue_type = (fields.get("issuetype") or {}).get("name", "")
        parent_field = fields.get("parent")
        parent_key = parent_field.get("key") if parent_field else None
        parent_summary = (parent_field.get("fields", {}) or {}).get("summary") if parent_field else None
        priority = (fields.get("priority") or {}).get("name", "Sem prioridade")

        b_age = calc_backlog_age_days(issue, now)
        l_time = calc_lead_time_days(issue)
        c_time = calc_cycle_time_days(issue)
        t_refinar = calc_tempo_refinar_days(issue)
        timeline = build_status_timeline(issue, now)
        all_timelines.append(timeline)

        if b_age is not None:
            backlog_age.append({"key": key, "dias": b_age, "prioridade": priority})
        if l_time is not None:
            lead_time.append({"key": key, "dias": l_time, "prioridade": priority})
        if c_time is not None:
            cycle_time.append({"key": key, "dias": c_time, "prioridade": priority})
        if t_refinar is not None:
            tempo_refinar.append({"key": key, "dias": t_refinar, "prioridade": priority})

        issue_rows.append({
            "key": key,
            "summary": summary,
            "status": status_atual,
            "tipo": issue_type,
            "parent_key": parent_key,
            "parent_summary": parent_summary,
            "prioridade": priority,
            "backlog_age_dias": b_age,
            "lead_time_dias": l_time,
            "cycle_time_dias": c_time,
            "tempo_refinar_dias": t_refinar,
        })

    cfd = build_cfd(all_timelines, now)

    output = {
        "gerado_em": now.isoformat(),
        "total_issues": len(issues),
        "jql": JIRA_JQL,
        "metricas": {
            "idade_backlog": backlog_age,
            "lead_time": lead_time,
            "cycle_time": cycle_time,
            "tempo_refinar": tempo_refinar,
        },
        "cfd": cfd,
        "issues": issue_rows,
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_DATA_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"Dados salvos em {OUTPUT_DATA_JSON}")


if __name__ == "__main__":
    main()
