# Dashboard de Métricas Kanban — CRM Sistêmico

Dashboard estático que coleta dados do Jira automaticamente (via GitHub Actions)
e publica métricas de fluxo no GitHub Pages, sem necessidade de servidor próprio.

## Métricas

1. **Idade de Backlog** — tempo cumulativo (dias) em que cada item ficou no status "Backlog", somando todas as vezes em que retornou para esse status.
2. **Lead Time** — tempo entre a criação da issue e a conclusão.
3. **Cycle Time** — tempo entre "Em andamento" e "Concluído".
4. **Tempo para Refinar** — tempo entre a criação e a adição da label "refinado".
5. **CFD** — Cumulative Flow Diagram com a contagem diária de itens em cada status.

Todas as métricas filtram apenas issues do projeto `CV` com o campo
"Gerência" = "CRM - Sistêmico".

## Como funciona

```
scripts/collect_metrics.py   -> chama a API do Jira, calcula métricas, gera docs/data.json
scripts/build_dashboard.py   -> gera docs/index.html a partir do data.json (Chart.js via CDN)
.github/workflows/update-dashboard.yml -> roda os dois scripts todo dia e publica em GitHub Pages
```

O HTML final é **autocontido**: os dados ficam embutidos no próprio arquivo.
Ninguém que acessa o dashboard faz chamadas ao Jira nem vê o token de API.

## Configuração necessária (Settings > Secrets and variables > Actions)

| Secret           | Valor                                              |
|-------------------|----------------------------------------------------|
| `JIRA_BASE_URL`    | `https://acerto.atlassian.net`                     |
| `JIRA_EMAIL`       | e-mail da conta usada para gerar o token            |
| `JIRA_API_TOKEN`   | token gerado em id.atlassian.com                    |

## Rodar localmente (opcional, para testar antes de subir)

```bash
export JIRA_BASE_URL="https://acerto.atlassian.net"
export JIRA_EMAIL="seu-email@empresa.com"
export JIRA_API_TOKEN="seu-token"

pip install -r requirements.txt   # não há dependências externas além da stdlib
python scripts/collect_metrics.py
python scripts/build_dashboard.py

# abra docs/index.html no navegador
```
