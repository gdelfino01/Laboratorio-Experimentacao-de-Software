# Lab 2 - Coleta, Medição, Análise e Relatório Final

## Objetivo

Este projeto executa o pipeline completo do laboratório:

1. Coleta dos top-1000 repositórios Java do GitHub.
2. Medição de qualidade por repositório com CK (CBO, DIT, LCOM).
3. Sumarização por repositório (média, mediana, desvio padrão).
4. Análise estatística das RQs com Spearman e Pearson.
5. Geração de gráficos de correlação.
6. Geração automática do relatório final em Markdown.

## Pré-requisitos

- Python 3.10+
- Java 11+ (para rodar o CK)
- Git
- Token GitHub com acesso à API GraphQL no arquivo `.env`:

```env
GITHUB_TOKEN="seu_token_aqui"
```

## Instalação

```bash
pip install -r requirements.txt
```

## Comandos principais

### 1. Coletar os 1000 repositórios

```bash
python main.py collect-repos --total 1000 --output repositorios.csv
```

### 2. Medir todos os repositórios com CK

```bash
python main.py measure-all-repos --repos-csv repositorios.csv
```

Opções úteis:

- `--limit 20`: executa amostra para teste rápido.
- `--no-resume`: desativa retomada por checkpoint.
- `--refresh-clone`: força novo clone.
- `--force-rebuild-ck`: recompila CK.

### 3. Rodar análise estatística e gerar gráficos

```bash
python main.py analyze-data --dataset-csv output/repo_metrics_1000.csv
```

### 4. Gerar relatório final

```bash
python main.py generate-report \
	--dataset-csv output/repo_metrics_1000.csv \
	--summary-csv output/rq_summary_stats.csv \
	--correlations-csv output/rq_correlations.csv \
	--output-report RELATORIO_FINAL.md
```

### 5. Pipeline completo (fim a fim)

```bash
python main.py run-all --total 1000
```

## Arquivos gerados

- `repositorios.csv`: top-1000 repositórios Java e métricas de processo.
- `output/repo_metrics_1000.csv`: dataset consolidado por repositório (processo + qualidade + tamanho).
- `output/repo_failures.csv`: falhas de processamento.
- `output/rq_summary_stats.csv`: estatísticas descritivas globais.
- `output/rq_correlations.csv`: correlações Spearman/Pearson por RQ.
- `output/figures/*.png`: gráficos de dispersão e heatmap de correlação.
- `RELATORIO_FINAL.md`: relatório final para entrega.

## Mapeamento das questões de pesquisa

- RQ01: `stars` vs `cbo_mean`, `dit_mean`, `lcom_mean`
- RQ02: `age_years` vs `cbo_mean`, `dit_mean`, `lcom_mean`
- RQ03: `releases` vs `cbo_mean`, `dit_mean`, `lcom_mean`
- RQ04: `repo_loc` e `repo_comment_lines` vs `cbo_mean`, `dit_mean`, `lcom_mean`

## Observações

- O processamento completo dos 1000 repositórios pode levar várias horas.
- O pipeline é tolerante a falhas: erros individuais não interrompem o lote.
- A saída consolidada contém coluna `status` para filtrar apenas `success` na análise.
