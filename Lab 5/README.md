# Lab 05 — GraphQL vs REST: Um Experimento Controlado

O objetivo é avaliar **quantitativamente** se a adoção de uma API GraphQL traz
benefícios mensuráveis em relação a uma API REST tradicional, considerando duas
métricas:

- **Tempo de resposta** (latência ponta-a-ponta da requisição) — RQ1
- **Tamanho da resposta** (em bytes) — RQ2

## Sistema sob teste

Comparação entre as duas APIs públicas oferecidas pelo GitHub:

- **REST API v3** (`https://api.github.com/...`)
- **GraphQL API v4** (`https://api.github.com/graphql`)

Ambas exigem autenticação via *Personal Access Token* (PAT) e atendem ao mesmo
domínio de dados (repositórios, usuários, issues, pull requests etc.), tornando
as consultas pareadas semanticamente equivalentes.

## Pré-requisitos

- Python 3.10+
- *GitHub Personal Access Token* com escopo `public_repo`

## Instalação

```powershell
cd "Lab 5"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
Copy-Item .env.example .env
# edite .env e cole seu token em GITHUB_TOKEN=...
```

## Execução (smoke test — 3 repetições)

```powershell
py src/main.py --repetitions 3 --warmup 1
```

## Execução completa (Sprint 2 — 30 repetições)

```powershell
py src/main.py --repetitions 30 --warmup 3 --output output/experiment_runs.csv
```

A saída é um CSV com uma linha por requisição contendo, no mínimo:

| Coluna             | Descrição                                            |
| ------------------ | ---------------------------------------------------- |
| `iteration`        | Índice da repetição (1..N)                           |
| `query_id`         | Identificador da consulta pareada (Q1..Q5)           |
| `treatment`        | `REST` ou `GRAPHQL`                                  |
| `endpoint`         | URL ou operação invocada                             |
| `status_code`      | Código HTTP da resposta                              |
| `response_time_ms` | Latência ponta-a-ponta em milissegundos              |
| `response_bytes`   | Tamanho do corpo da resposta em bytes                |
| `timestamp_utc`    | Início da requisição (ISO 8601, UTC)                 |

## Próximos passos (Sprint 2 / Sprint 3)

1. Executar a coleta com 30 repetições por consulta.
2. Aplicar testes pareados (Wilcoxon ou *t* pareado) para H0₁ e H0₂.
3. Calcular tamanhos de efeito (Cliff's *δ* / Cohen's *d*).
4. Produzir o `RELATORIO_LAB5.md` final e o dashboard em Plotly/Dash.
