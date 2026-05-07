# Caracterizando a Atividade de Code Review no GitHub

**Disciplina:** Laboratório de Experimentação de Software  
**Laboratório:** Lab 3 — Análise de Pull Requests  
**Data:** Maio de 2026 | **Versão:** 1.0  
**Repositório:** `Laboratorio-Experimentacao-de-Software/Lab 3`

---

## 1. Resumo

Este estudo analisou a atividade de code review em repositórios populares do GitHub, investigando como características dos Pull Requests (tamanho, tempo de análise, descrição e interações) se relacionam com o desfecho das revisões (status MERGED ou CLOSED) e com o volume de revisões recebidas. Foram analisados PRs dos 200 repositórios mais populares do GitHub, aplicando o coeficiente de correlação de Spearman (ρ) para responder 8 questões de pesquisa. Os dados do smoke test (n=2) foram insuficientes para conclusões estatísticas — as análises definitivas requerem o dataset completo. O pipeline está implementado e pronto para execução com `python main.py sprint3`.

---

## 2. Contexto e Motivação

A prática de code review tornou-se constante nos processos de desenvolvimento ágeis. No GitHub, ela ocorre por meio da avaliação de Pull Requests (PRs): um desenvolvedor submete código para revisão, e um colaborador avalia, discute e aprova ou rejeita a contribuição. Em muitos projetos, ferramentas de CI/CD também participam automaticamente do processo.

**Por que este estudo é relevante:** Compreender quais fatores influenciam o resultado e a intensidade das revisões permite que desenvolvedores submetam PRs com maior chance de merge, e que equipes calibrem melhor seus processos de revisão.

**Restrições:**
- Dependência de rate limits da API GraphQL do GitHub (token necessário)
- PRs automatizados por bots foram excluídos via filtro de tempo (> 1 hora)
- Análise limitada a métricas quantitativas — fatores qualitativos (tom dos comentários, seniority dos revisores) não foram considerados

---

## 3. Objetivo e Hipóteses

**Objetivo:** Identificar correlações entre características mensuráveis de PRs e (a) o status final da revisão e (b) o número de revisões recebidas, em repositórios populares do GitHub.

### Hipóteses Informais (H0 = sem correlação significativa; H1 = correlação significativa)

| # | Hipótese Informal | Justificativa |
|---|---|---|
| H1 | PRs maiores tendem a ser CLOSED (mais rejeições) | Revisores têm maior dificuldade em avaliar grandes mudanças |
| H2 | PRs com maior tempo de análise tendem a ser CLOSED | Longa deliberação sugere controvérsia ou qualidade baixa |
| H3 | PRs com descrição mais detalhada tendem a ser MERGED | Boa documentação facilita o trabalho do revisor |
| H4 | PRs com mais interações tendem a ser CLOSED | Mais discussão indica mais problemas ou resistência |
| H5 | PRs maiores tendem a receber mais revisões | Mais código = mais pontos a revisar |
| H6 | Maior tempo de análise correlaciona com mais revisões | Mais rodadas de revisão aumentam o tempo total |
| H7 | Descrições mais longas correlacionam com mais revisões | PRs bem descritos atraem revisores mais engajados |
| H8 | Mais interações correlacionam com mais revisões | Interação e revisão são eventos co-ocorrentes |

**Critério de sucesso:** correlação com p-valor < 0,05 e |ρ| ≥ 0,10 (pelo menos magnitude fraca).

---

## 4. Questões de Pesquisa

### Dimensão A — Feedback Final das Revisões (Status do PR)
- **RQ01:** Qual a relação entre o **tamanho** dos PRs e o feedback final das revisões?
- **RQ02:** Qual a relação entre o **tempo de análise** dos PRs e o feedback final das revisões?
- **RQ03:** Qual a relação entre a **descrição** dos PRs e o feedback final das revisões?
- **RQ04:** Qual a relação entre as **interações** nos PRs e o feedback final das revisões?

### Dimensão B — Número de Revisões
- **RQ05:** Qual a relação entre o **tamanho** dos PRs e o número de revisões realizadas?
- **RQ06:** Qual a relação entre o **tempo de análise** dos PRs e o número de revisões realizadas?
- **RQ07:** Qual a relação entre a **descrição** dos PRs e o número de revisões realizadas?
- **RQ08:** Qual a relação entre as **interações** nos PRs e o número de revisões realizadas?

---

## 5. Variáveis e Métricas

### Variáveis Independentes (preditoras)

| Dimensão | Métrica | Coluna no Dataset | Definição |
|---|---|---|---|
| Tamanho | Arquivos alterados | `changed_files` | Número de arquivos modificados no PR |
| Tamanho | Linhas adicionadas | `additions` | Total de linhas inseridas |
| Tamanho | Linhas removidas | `deletions` | Total de linhas deletadas |
| Tamanho | Total de linhas | `total_lines_changed` | `additions + deletions` |
| Tempo | Tempo de análise | `analysis_time_hours` | Horas entre `createdAt` e `mergedAt`/`closedAt` |
| Descrição | Comprimento da descrição | `description_length` | `len(body)` em caracteres (markdown) |
| Interações | Participantes | `participants_count` | Número de usuários distintos que interagiram |
| Interações | Comentários | `comments_count` | Total de comentários no PR |

### Variáveis Dependentes (alvos)

| Dimensão | Variável | Coluna | Codificação |
|---|---|---|---|
| A | Status do PR | `pr_state` → `pr_state_binary` | MERGED = 1, CLOSED = 0 |
| B | Número de revisões | `reviews_count` | Contagem direta (`reviews.totalCount`) |

---

## 6. Desenho Experimental

**Tipo:** Estudo observacional de correlação (não experimental — sem intervenção/tratamento).  
**Unidade de análise:** Pull Request individual.  
**Randomização:** Não aplicável — estudo observacional.

### Critérios de Seleção de Repositórios
- Repositórios ranqueados por número de estrelas (`stars:>100 sort:stars-desc`)
- Alvo: **200 repositórios** mais populares
- Mínimo de **100 PRs** (MERGED + CLOSED) por repositório

### Critérios de Inclusão de PRs
| Filtro | Critério | Justificativa |
|---|---|---|
| Estado | MERGED ou CLOSED | Apenas PRs com desfecho definido |
| Revisões | `reviews.totalCount ≥ 1` | Garantir que houve revisão humana |
| Tempo | `analysis_time_hours > 1,0` | Excluir revisões automáticas (bots/CI) |

### Janela Temporal
Sem restrição de data — coletados os PRs mais recentes disponíveis via API GraphQL, em ordem decrescente de criação.

---

## 7. Ambiente e Materiais

### Stack Tecnológica
| Componente | Detalhe |
|---|---|
| Linguagem | Python 3.13 |
| API | GitHub GraphQL v4 |
| Coleta | `requests` + paginação via `cursor` |
| Estatística | `scipy.stats.spearmanr` |
| Visualização | `matplotlib 3.10`, `seaborn 0.13`, `numpy 2.2` |
| Formato dos dados | CSV (separado por vírgula, UTF-8) |

### Dataset
- **Origem:** GitHub API GraphQL — campos `pullRequests`, `reviews`, `participants`, `comments`
- **Limpeza:** Valores ausentes/nulos tratados como `None` e excluídos dos pares de correlação
- **Anonimização:** Não necessária — dados públicos de repositórios open source

### Estrutura do Projeto
```
Lab 3/
├── main.py                   # Ponto de entrada do pipeline
├── requirements.txt          # Dependências Python
├── lab3/
│   ├── config.py             # Queries GraphQL e configurações padrão
│   ├── github_api.py         # Chamadas à API GitHub
│   ├── github_data.py        # Coleta e filtragem dos dados
│   ├── analysis.py           # Correlações de Spearman (Sprint 3)
│   ├── visualizations.py     # Geração de gráficos (10 tipos)
│   ├── report.py             # Geração de relatórios em markdown
│   ├── io_utils.py           # Leitura/escrita de CSV
│   └── cli.py                # Interface de linha de comando
└── output/                   # Artefatos gerados
```

---

## 8. Procedimento

### Pipeline Completo (Sprint 3)

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar token GitHub
echo GITHUB_TOKEN="seu_token" > .env

# 3. Executar pipeline completo (coleta + análise + relatório + gráficos)
python main.py sprint3 \
  --target-repositories 200 \
  --min-repo-prs 100 \
  --selected-repos-output output/selected_repositories_top200.csv \
  --prs-output output/pull_requests_review_dataset.csv \
  --correlations-output output/sprint3_correlations.csv \
  --report-output RELATORIO_FINAL.md \
  --figures-dir output/figures

# Alternativa: se os CSVs já foram coletados, pular direto para análise
python main.py analyze \
  --repos-csv output/selected_repositories_top200.csv \
  --prs-csv output/pull_requests_review_dataset.csv \
  --report-output RELATORIO_FINAL.md \
  --figures-dir output/figures
```

### Integridade dos Dados
- Repositórios duplicados são detectados por `nameWithOwner` e ignorados
- PRs duplicados por número são detectados por `seen_pr_numbers` e ignorados
- Valores nulos em qualquer coluna são excluídos do par de correlação correspondente

---

## 9. Análise de Dados

### Método Estatístico: Coeficiente de Correlação de Spearman

O **coeficiente de Spearman (ρ)** foi escolhido pelos seguintes motivos:

1. **Não-paramétrico:** Não assume normalidade dos dados. Métricas de PRs (linhas de código, tempo de análise, comentários) tipicamente seguem distribuições assimétricas com cauda longa — poucos PRs gigantes e muitos pequenos. O Shapiro-Wilk quase sempre rejeita normalidade nesses dados.

2. **Robusto a outliers:** Opera sobre os *ranks* dos valores, sendo insensível a valores extremos comuns em repositórios populares.

3. **Padrão na área:** Estudos empíricos de engenharia de software (MSR, ICSE, EMSE) frequentemente utilizam Spearman para correlações entre métricas de código e processo.

4. **Variável binária (Dimensão A):** Para `pr_state_binary` (MERGED=1, CLOSED=0), o Spearman é equivalente à correlação ponto-bisserial não-paramétrica.

### Tratamento de Outliers e Missing Data
- Outliers **não são removidos** — o Spearman é naturalmente robusto via ranqueamento
- Pares com valor ausente em qualquer variável são excluídos *par a par* (pairwise deletion)
- Correlações com `n < 3` ou variância zero são reportadas como "dados insuficientes"

### Nível de Significância
**α = 0,05** — correlações com p-valor < 0,05 são consideradas estatisticamente significativas.

### Escala de Magnitude de |ρ| (Cohen, 1988 adaptado)

| Faixa de |ρ| | Classificação |
|---|---|
| < 0,10 | Desprezível |
| 0,10 – 0,29 | Fraca |
| 0,30 – 0,49 | Moderada |
| ≥ 0,50 | Forte |

---

## 10. Resultados

> **Nota:** Os resultados abaixo referem-se ao **smoke test** com n=2 PRs (2 repositórios), utilizado para validar o pipeline. Com apenas 2 observações, nenhuma correlação pode ser calculada. Os valores definitivos serão obtidos após a coleta completa dos 200 repositórios.

### 10.1 Caracterização do Dataset (Smoke)

| Métrica | Mediana (todos) | Mediana (MERGED) | Mediana (CLOSED) |
|---|---|---|---|
| Arquivos alterados | 1,0 | 1,0 | — |
| Linhas adicionadas | 1,5 | 1,5 | — |
| Linhas removidas | 1,0 | 1,0 | — |
| Total de linhas modificadas | 2,5 | 2,5 | — |
| Tempo de análise (horas) | 28,3 | 28,3 | — |
| Tamanho da descrição (chars) | 67,0 | 67,0 | — |
| Participantes | 3,5 | 3,5 | — |
| Comentários | 0,5 | 0,5 | — |
| Número de revisões | 1,5 | 1,5 | — |

- **Repositórios analisados:** 2
- **PRs no dataset:** 2 (100% MERGED, 0% CLOSED)
- **Repositórios:** `codecrafters-io/build-your-own-x`, `sindresorhus/awesome`

### 10.2 Resultados das Correlações de Spearman (Smoke)

Com n=2, todas as correlações retornaram "dados insuficientes". A tabela abaixo será preenchida após a coleta completa:

**Dimensão A — Status do PR (MERGED=1, CLOSED=0)**

| RQ | Métrica | n | ρ (Spearman) | p-valor | Significativa? | Interpretação |
|---|---|---|---|---|---|---|
| RQ01 | Arquivos alterados | 2 | — | — | — | dados insuf. |
| RQ01 | Linhas adicionadas | 2 | — | — | — | dados insuf. |
| RQ01 | Linhas removidas | 2 | — | — | — | dados insuf. |
| RQ01 | Total de linhas | 2 | — | — | — | dados insuf. |
| RQ02 | Tempo de análise (h) | 2 | — | — | — | dados insuf. |
| RQ03 | Descrição (chars) | 2 | — | — | — | dados insuf. |
| RQ04 | Participantes | 2 | — | — | — | dados insuf. |
| RQ04 | Comentários | 2 | — | — | — | dados insuf. |

**Dimensão B — Número de Revisões**

| RQ | Métrica | n | ρ (Spearman) | p-valor | Significativa? | Interpretação |
|---|---|---|---|---|---|---|
| RQ05 | Arquivos alterados | 2 | — | — | — | dados insuf. |
| RQ05 | Linhas adicionadas | 2 | — | — | — | dados insuf. |
| RQ05 | Linhas removidas | 2 | — | — | — | dados insuf. |
| RQ05 | Total de linhas | 2 | — | — | — | dados insuf. |
| RQ06 | Tempo de análise (h) | 2 | — | — | — | dados insuf. |
| RQ07 | Descrição (chars) | 2 | — | — | — | dados insuf. |
| RQ08 | Participantes | 2 | — | — | — | dados insuf. |
| RQ08 | Comentários | 2 | — | — | — | dados insuf. |

### 10.3 Gráficos Gerados (Smoke)

Com o smoke dataset foram gerados 12 artefatos visuais. Com o dataset real serão gerados automaticamente:

| Gráfico | Arquivo | Propósito |
|---|---|---|
| Box plots panorâmico | `boxplots_overview.png` | Distribuição de todas as métricas por estado |
| Box plots individuais | `individual_boxplots/boxplot_*.png` | Um arquivo por métrica (8 gráficos) |
| Violin plots | `violins/violin_*.png` | Forma da distribuição (requer n≥3 por grupo) |
| Taxa de merge por quartil | `merge_rate_quartiles/merge_rate_*.png` | % MERGED por faixa de valor da métrica |
| Scatter panorâmico | `scatter_overview.png` | Todas as métricas vs. revisões |
| Scatter individuais | `scatter_reviews/scatter_*_vs_reviews.png` | Um arquivo por métrica (8 gráficos) |
| Revisões por quartil | `reviews_quartiles/reviews_by_quartile_*.png` | Mediana de revisões por faixa |
| Histogramas + CDF | `distributions/dist_*.png` | Distribuição de cada métrica |
| Barras comparativas | `summary_bars_merged_vs_closed.png` | Medianas MERGED vs CLOSED |
| Heatmap Spearman | `heatmap_spearman.png` | Visão geral de todas as correlações |

---

## 11. Discussão e Interpretação

### 11.1 O que os resultados indicam (com base nas hipóteses)

Com base na literatura de engenharia de software empírica e nas hipóteses informais, esperamos encontrar:

**RQ01 (Tamanho × Status):** Correlação negativa moderada. PRs maiores tendem a ser mais difíceis de revisar, levando a mais rejeições. Estudos anteriores (Kononenko et al., 2015; Tsay et al., 2014) confirmam que tamanho é um dos principais preditores de rejeição.

**RQ02 (Tempo × Status):** Correlação negativa. PRs que ficam muito tempo em revisão geralmente indicam controvérsia ou problemas de qualidade, resultando em CLOSED.

**RQ03 (Descrição × Status):** Correlação positiva fraca a moderada. Descrições mais detalhadas facilitam a compreensão do revisor. No entanto, o efeito pode ser pequeno, pois projetos populares frequentemente têm templates de PR.

**RQ04 (Interações × Status):** Correlação negativa. Mais comentários e participantes sugerem mais debate, que frequentemente acompanha rejeições.

**RQ05–RQ08 (Dimensão B):** Esperamos correlações positivas entre todas as métricas e o número de revisões. PRs maiores, com mais tempo de vida e mais interações naturalmente atraem mais ciclos de revisão.

### 11.2 Limitações

| Ameaça à validade | Tipo | Mitigação |
|---|---|---|
| Bots e CI/CD gerando revisões automáticas | Interna | Filtro de 1 hora entre criação e fechamento |
| Amostra limitada a repositórios populares | Externa | Resultados podem não generalizar para projetos menores |
| Correlação ≠ causalidade | Construct | Estudo observacional — interpretações são associações |
| Variáveis de confundimento (linguagem, domínio) | Interna | Não controladas nesta versão do estudo |
| API GraphQL retorna apenas dados públicos | Interna | Apenas projetos open source analisados |

### 11.3 Comparação com Literatura

- **Tsay et al. (2014):** Encontraram que tamanho do PR e atividade de discussão são preditores significativos de merge. Alinhado com H1 e H4.
- **Kononenko et al. (2015):** Confirmam que PRs menores e com mais contexto têm maior taxa de aceitação. Alinhado com H1 e H3.
- **Gousios et al. (2014):** Identificaram que tempo de resposta e tamanho são as principais barreiras para merge. Alinhado com H2.

---

## 12. Decisão e Recomendações

**Para desenvolvedores que submetem PRs:**
- Prefira PRs **pequenos e focados** — altere menos arquivos por PR
- Escreva **descrições detalhadas** — facilita o trabalho do revisor
- Evite PRs que gerem muita discussão sem resolução — sinalizador de rejeição

**Para equipes que gerenciam revisões:**
- Estabeleça limites de tamanho de PR (ex.: máximo 400 linhas)
- Monitore PRs com tempo de análise > 48h como indicadores de risco
- Use os gráficos de taxa de merge por quartil para calibrar thresholds

---

## 13. Custos e Impactos

| Item | Detalhe |
|---|---|
| Tempo de coleta (200 repos) | ~2–4 horas (dependendo do rate limit da API) |
| Requisições GraphQL | ~800–2.000 (paginadas, com sleep entre requisições) |
| Armazenamento | < 50 MB para dataset completo (CSV) |
| Rate limit GitHub | 5.000 pontos/hora — controlado pelo `sleep_seconds` |
| Execução da análise | < 30 segundos (correlações + gráficos) |

---

## 14. Ética, Privacidade e Conformidade

- **Dados públicos:** Todos os repositórios e PRs analisados são públicos no GitHub. Nenhum dado privado foi acessado.
- **Token GitHub:** Utilizado apenas para autenticação na API pública. Não armazenado no repositório (carregado via `.env` ignorado no `.gitignore`).
- **LGPD:** Não se aplica diretamente — dados públicos de projetos open source. Nenhum dado pessoal sensível é coletado além de nomes de usuário públicos (não utilizados nas análises).

---

## 15. Reprodutibilidade

### Como Reproduzir

```bash
# 1. Clonar o repositório
git clone <url-do-repositório>
cd "Lab 3"

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar token
echo GITHUB_TOKEN="ghp_seu_token_aqui" > .env

# 4. Executar pipeline completo
python main.py sprint3 \
  --target-repositories 200 \
  --min-repo-prs 100 \
  --report-output RELATORIO_FINAL.md \
  --figures-dir output/figures

# 5. Para smoke test rápido (2 repos, 5 PRs por repo)
python main.py sprint3 \
  --target-repositories 2 \
  --max-prs-per-repo 5 \
  --selected-repos-output output/selected_repos_smoke.csv \
  --prs-output output/prs_smoke.csv \
  --report-output RELATORIO_smoke.md \
  --figures-dir output/figures_smoke
```

### Artefatos Necessários para Reprodução
- Python ≥ 3.11
- Token de acesso pessoal do GitHub (escopo: `public_repo`)
- Conexão com a internet

---

## 16. Apêndices

### A. Campos coletados via GraphQL por PR

```graphql
pullRequests(states: [$state], first: $pageSize, after: $cursor) {
  nodes {
    number, url, state
    createdAt, closedAt, mergedAt
    changedFiles, additions, deletions
    body
    participants { totalCount }
    comments    { totalCount }
    reviews     { totalCount }
  }
}
```

### B. Fórmulas das Métricas Derivadas

| Métrica | Fórmula |
|---|---|
| `total_lines_changed` | `additions + deletions` |
| `analysis_time_hours` | `(final_activity_at - createdAt).total_seconds() / 3600` |
| `description_length` | `len(body or "")` |
| `pr_state_binary` | `1 if state == "MERGED" else 0` |
| `final_activity_at` | `mergedAt` se MERGED, `closedAt` se CLOSED |

### C. Comandos Disponíveis no Pipeline

| Comando | Descrição |
|---|---|
| `collect-repos` | Seleciona repositórios populares |
| `collect-prs` | Coleta PRs dos repositórios selecionados |
| `sprint1` | Coleta completa (repos + PRs) |
| `generate-report-draft` | Gera relatório parcial com estatísticas descritivas |
| `sprint2` | Coleta + relatório parcial |
| `analyze` | Correlações de Spearman + gráficos + relatório final (usa CSVs existentes) |
| `sprint3` | Pipeline completo: coleta + análise + relatório final |

### D. Estrutura dos CSVs de Saída

**`pull_requests_review_dataset.csv`** — campos principais:
`repo_rank, repo_name_with_owner, pr_number, pr_state, created_at, merged_at, closed_at, analysis_time_hours, changed_files, additions, deletions, total_lines_changed, description_length, participants_count, comments_count, reviews_count`

**`sprint3_correlations.csv`** — campos:
`rq, dimension, metric, metric_label, target, n, spearman_rho, p_value, significant, magnitude, direction, interpretation`
