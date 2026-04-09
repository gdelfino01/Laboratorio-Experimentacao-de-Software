# Relatório Final - Lab02S02: Qualidade Interna de Repositórios Java Open-Source

## 1. Introdução

### 1.1 Contextualização

Projetos open-source evoluem de forma colaborativa, com múltiplos contribuidores atuando em partes distintas do código ao longo do tempo.
Nesse cenário, características de qualidade interna como acoplamento, coesão e estrutura de herança podem se degradar com o crescimento do sistema.
A mensuração empírica dessas características permite avaliar como decisões e dinâmica de desenvolvimento se relacionam com a qualidade arquitetural.

### 1.2 Problema Foco do Experimento

Embora repositórios populares sejam amplamente estudados sob a ótica de atividade e adoção, ainda há lacunas na compreensão da relação entre
métricas de processo (popularidade, maturidade, atividade e tamanho) e métricas de produto calculadas por análise estática.
Este laboratório investiga essa relação em repositórios Java, utilizando a ferramenta CK para mensurar CBO, DIT e LCOM.

### 1.3 Questões de Pesquisa

- RQ01. Qual a relação entre a popularidade dos repositórios e as suas características de qualidade?
- RQ02. Qual a relação entre a maturidade dos repositórios e as suas características de qualidade?
- RQ03. Qual a relação entre a atividade dos repositórios e as suas características de qualidade?
- RQ04. Qual a relação entre o tamanho dos repositórios e as suas características de qualidade?

### 1.4 Hipóteses

- H1 (RQ01): repositórios mais populares tendem a apresentar melhor qualidade estrutural (especialmente menor LCOM médio).
- H2 (RQ02): repositórios mais maduros tendem a acumular maior complexidade estrutural (aumento de CBO/DIT).
- H3 (RQ03): maior atividade (mais releases) tende a estar associada a melhor manutenção e menor LCOM médio.
- H4 (RQ04): repositórios maiores (LOC/comentários) tendem a apresentar maior acoplamento e menor coesão.

### 1.5 Objetivos

Objetivo principal: analisar a relação entre métricas de processo e métricas de qualidade interna em repositórios Java open-source.

Objetivos específicos:
1. Consolidar as métricas por repositório para uma base única de análise.
2. Calcular estatísticas descritivas globais (média, mediana, desvio padrão).
3. Medir associação entre variáveis com correlações de Spearman e Pearson.
4. Produzir visualizações para apoiar interpretação das RQs.
5. Confrontar os resultados observados com as hipóteses formuladas.

## 2. Metodologia

### 2.1 Passo a Passo do Experimento

1. Coleta dos top-1000 repositórios Java por estrelas no GitHub.
2. Clonagem e execução do CK por repositório para extração de métricas de classe.
3. Sumarização por repositório das métricas CBO, DIT e LCOM (média, mediana, desvio padrão).
4. Consolidação com métricas de processo: estrelas, idade (anos), releases, LOC e linhas de comentários.
5. Filtragem de repositórios com status de sucesso para garantir consistência estatística.
6. Cálculo de correlações e geração de gráficos de dispersão e heatmap.

### 2.2 Métricas e Unidades

- Popularidade: número de estrelas.
- Maturidade: idade do repositório em anos.
- Atividade: número de releases.
- Tamanho: linhas de código e linhas de comentários no repositório.
- Qualidade interna: CBO, DIT e LCOM (resumo por repositório).

### 2.3 Decisões Analíticas

- Spearman foi priorizado na interpretação por maior robustez a distribuições assimétricas e outliers.
- Pearson foi mantido como referência complementar para associação linear.
- A análise considerou apenas repositórios com status success no dataset consolidado.

## 3. Visualização dos Resultados

### 3.1 Cobertura da Coleta

- Total de linhas no dataset consolidado: 1006.
- Repositórios analisados com sucesso: 968.
- Repositórios com falha no processamento: 38.

### 3.2 Resultados Tabulares

Resumo descritivo global:
| metric             |   n |         mean |      median |         stdev |     min |              max |
|--------------------|-----|--------------|-------------|---------------|---------|------------------|
| stars              | 968 |   9397.3     |  5765.5     |  10698.5      | 3474    | 124039           |
| age_years          | 968 |     10.0959  |    10.265   |      3.17618  |    0.51 |     17.43        |
| releases           | 968 |     40.437   |    11       |     89.0187   |    0    |   1000           |
| repo_loc           | 968 | 119470       | 17821.5     | 442849        |    2    |      1.07523e+07 |
| repo_comment_lines | 968 |  45291.4     |  4975.5     | 409535        |    0    |      1.24668e+07 |
| cbo_mean           | 968 |      5.37687 |     5.32635 |      1.85861  |    0    |     21.8935      |
| dit_mean           | 968 |      1.45645 |     1.3938  |      0.351884 |    1    |      4.388       |
| lcom_mean          | 968 |    119.348   |    24.5527  |   1744.3      |    0    |  54025.1         |

Medianas de referência do dataset analisado:
- Estrelas: 5765.5
- Idade (anos): 10.27
- Releases: 11.0
- LOC: 17821.5
- Linhas de comentários: 4975.5
- CBO médio por repositório: 5.326
- DIT médio por repositório: 1.394
- LCOM médio por repositório: 24.553

### 3.3 Correlações por RQ

#### RQ01 - Popularidade vs Qualidade
| rq   | process_metric   | process_label           | quality_metric   |   n |   spearman_corr |   spearman_pvalue |   pearson_corr |   pearson_pvalue |
|------|------------------|-------------------------|------------------|-----|-----------------|-------------------|----------------|------------------|
| RQ01 | stars            | Popularidade (estrelas) | cbo_mean         | 968 |        0.030986 |          0.335532 |      -0.128224 |         6.3e-05  |
| RQ01 | stars            | Popularidade (estrelas) | dit_mean         | 968 |       -0.044667 |          0.164949 |      -0.114641 |         0.000352 |
| RQ01 | stars            | Popularidade (estrelas) | lcom_mean        | 968 |        0.05423  |          0.091736 |       0.020961 |         0.514792 |

#### RQ02 - Maturidade vs Qualidade
| rq   | process_metric   | process_label              | quality_metric   |   n |   spearman_corr |   spearman_pvalue |   pearson_corr |   pearson_pvalue |
|------|------------------|----------------------------|------------------|-----|-----------------|-------------------|----------------|------------------|
| RQ02 | age_years        | Maturidade (idade em anos) | cbo_mean         | 968 |        0.006898 |          0.830279 |       0.010379 |         0.747066 |
| RQ02 | age_years        | Maturidade (idade em anos) | dit_mean         | 968 |        0.28829  |          0        |       0.191467 |         0        |
| RQ02 | age_years        | Maturidade (idade em anos) | lcom_mean        | 968 |        0.199031 |          0        |       0.029765 |         0.354929 |

#### RQ03 - Atividade vs Qualidade
| rq   | process_metric   | process_label                  | quality_metric   |   n |   spearman_corr |   spearman_pvalue |   pearson_corr |   pearson_pvalue |
|------|------------------|--------------------------------|------------------|-----|-----------------|-------------------|----------------|------------------|
| RQ03 | releases         | Atividade (número de releases) | cbo_mean         | 968 |        0.396713 |                 0 |       0.207094 |         0        |
| RQ03 | releases         | Atividade (número de releases) | dit_mean         | 968 |        0.202014 |                 0 |       0.051312 |         0.110616 |
| RQ03 | releases         | Atividade (número de releases) | lcom_mean        | 968 |        0.326236 |                 0 |      -0.012797 |         0.690891 |

#### RQ04 - Tamanho vs Qualidade
| rq            | process_metric     | process_label                   | quality_metric   |   n |   spearman_corr |   spearman_pvalue |   pearson_corr |   pearson_pvalue |
|---------------|--------------------|---------------------------------|------------------|-----|-----------------|-------------------|----------------|------------------|
| RQ04_LOC      | repo_loc           | Tamanho (LOC do repositório)    | cbo_mean         | 968 |        0.427861 |                 0 |       0.189603 |         0        |
| RQ04_LOC      | repo_loc           | Tamanho (LOC do repositório)    | dit_mean         | 968 |        0.241372 |                 0 |       0.037336 |         0.245835 |
| RQ04_LOC      | repo_loc           | Tamanho (LOC do repositório)    | lcom_mean        | 968 |        0.461183 |                 0 |       0.062647 |         0.051355 |
| RQ04_COMMENTS | repo_comment_lines | Tamanho (linhas de comentários) | cbo_mean         | 968 |        0.39944  |                 0 |       0.074604 |         0.020267 |
| RQ04_COMMENTS | repo_comment_lines | Tamanho (linhas de comentários) | dit_mean         | 968 |        0.21634  |                 0 |      -0.00241  |         0.940316 |
| RQ04_COMMENTS | repo_comment_lines | Tamanho (linhas de comentários) | lcom_mean        | 968 |        0.43573  |                 0 |       0.021192 |         0.510177 |

### 3.4 Gráficos Gerados

- output/figures/rq01_stars_vs_cbo_mean.png
- output/figures/rq01_stars_vs_dit_mean.png
- output/figures/rq01_stars_vs_lcom_mean.png
- output/figures/rq02_age_years_vs_cbo_mean.png
- output/figures/rq02_age_years_vs_dit_mean.png
- output/figures/rq02_age_years_vs_lcom_mean.png
- output/figures/rq03_releases_vs_cbo_mean.png
- output/figures/rq03_releases_vs_dit_mean.png
- output/figures/rq03_releases_vs_lcom_mean.png
- output/figures/rq04_loc_repo_loc_vs_cbo_mean.png
- output/figures/rq04_loc_repo_loc_vs_dit_mean.png
- output/figures/rq04_loc_repo_loc_vs_lcom_mean.png
- output/figures/rq04_comments_repo_comment_lines_vs_cbo_mean.png
- output/figures/rq04_comments_repo_comment_lines_vs_dit_mean.png
- output/figures/rq04_comments_repo_comment_lines_vs_lcom_mean.png
- output/figures/correlation_heatmap_spearman.png

## 4. Discussão dos Resultados

### 4.1 Confronto com as Questões de Pesquisa

#### RQ01 - Popularidade e Qualidade
Resultado observado: as correlações entre estrelas e qualidade são muito fracas, com destaque para LCOM (Spearman 0.054) e CBO (Spearman 0.031).
Confronto com H1: a hipótese é refutada, pois não há evidência de que maior popularidade esteja associada a melhor qualidade interna.

#### RQ02 - Maturidade e Qualidade
Resultado observado: maturidade apresenta associação positiva com DIT (Spearman 0.288) e também com LCOM (Spearman 0.199), sugerindo crescimento de complexidade em repositórios mais antigos.
Confronto com H2: hipótese parcialmente confirmada, com evidência mais forte para profundidade de herança e coesão pior ao longo do tempo.

#### RQ03 - Atividade e Qualidade
Resultado observado: releases se associam positivamente com CBO (Spearman 0.397) e LCOM (Spearman 0.326), contrariando a expectativa de melhora estrutural com maior atividade.
Confronto com H3: hipótese refutada, indicando que mais releases não significam, por si, menor acoplamento ou maior coesão.

#### RQ04 - Tamanho e Qualidade
Resultado observado: tamanho apresenta as maiores associações com qualidade, tanto por LOC quanto por linhas de comentários.
Para LOC, CBO (Spearman 0.428) e LCOM (Spearman 0.461) crescem com o tamanho; para comentários, CBO (Spearman 0.399) e LCOM (Spearman 0.436) seguem tendência semelhante.
Confronto com H4: hipótese confirmada, com evidência consistente de degradação estrutural em projetos maiores.

### 4.2 Síntese das Hipóteses

- H1: refutada.
- H2: parcialmente confirmada.
- H3: refutada.
- H4: confirmada.

A síntese aponta que maturidade e, principalmente, tamanho explicam melhor a variação das métricas de qualidade do que popularidade isolada.

## 5. Limitações e Ameaças à Validade

- Parte dos repositórios falhou no processamento automático, reduzindo a cobertura efetiva da amostra.
- Correlação não implica causalidade; os resultados indicam associação, não efeito causal.
- Métricas agregadas por repositório ocultam heterogeneidade interna por módulo/pacote.
- A presença de outliers (especialmente em LOC e LCOM) pode distorcer medidas lineares; por isso Spearman foi priorizado.

## 6. Conclusão

O experimento respondeu às quatro RQs com base em uma amostra ampla de repositórios Java e mostrou que qualidade interna se relaciona mais com escala e maturidade do que com popularidade.
Como continuidade, recomenda-se segmentar a base por tipo de sistema e domínio para reduzir viés de mistura e aprofundar a interpretação causal.