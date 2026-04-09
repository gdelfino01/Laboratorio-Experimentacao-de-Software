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
| Métrica | Média | Mediana | Desvio Padrão | Mínimo | Máximo |
| --- | --- | --- | --- | --- | --- |
| Estrelas | 9397.2996 | 5765.5000 | 10698.5335 | 3474.0000 | 124039.0000 |
| Idade (anos) | 10.0959 | 10.2650 | 3.1762 | 0.5100 | 17.4300 |
| Releases | 40.4370 | 11.0000 | 89.0187 | 0.0000 | 1000.0000 |
| LOC do Repositório | 119470.2087 | 17821.5000 | 442849.2105 | 2.0000 | 10752314.0000 |
| Linhas de Comentários | 45291.3657 | 4975.5000 | 409534.7392 | 0.0000 | 12466809.0000 |
| CBO (média por repositório) | 5.3769 | 5.3263 | 1.8586 | 0.0000 | 21.8935 |
| DIT (média por repositório) | 1.4565 | 1.3938 | 0.3519 | 1.0000 | 4.3880 |
| LCOM (média por repositório) | 119.3475 | 24.5527 | 1744.2995 | 0.0000 | 54025.1128 |

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
| Métrica de Qualidade | Spearman (rho) | p-valor Spearman | Pearson (r) | p-valor Pearson |
| --- | --- | --- | --- | --- |
| CBO (média) | 0.031 | 0.3355 | -0.128 | 6.30e-05 |
| DIT (média) | -0.045 | 0.1649 | -0.115 | 3.52e-04 |
| LCOM (média) | 0.054 | 0.0917 | 0.021 | 0.5148 |

#### RQ02 - Maturidade vs Qualidade
| Métrica de Qualidade | Spearman (rho) | p-valor Spearman | Pearson (r) | p-valor Pearson |
| --- | --- | --- | --- | --- |
| CBO (média) | 0.007 | 0.8303 | 0.010 | 0.7471 |
| DIT (média) | 0.288 | <0.0001 | 0.191 | <0.0001 |
| LCOM (média) | 0.199 | <0.0001 | 0.030 | 0.3549 |

#### RQ03 - Atividade vs Qualidade
| Métrica de Qualidade | Spearman (rho) | p-valor Spearman | Pearson (r) | p-valor Pearson |
| --- | --- | --- | --- | --- |
| CBO (média) | 0.397 | <0.0001 | 0.207 | <0.0001 |
| DIT (média) | 0.202 | <0.0001 | 0.051 | 0.1106 |
| LCOM (média) | 0.326 | <0.0001 | -0.013 | 0.6909 |

#### RQ04 - Tamanho vs Qualidade
| Métrica de Qualidade | Spearman (rho) | p-valor Spearman | Pearson (r) | p-valor Pearson |
| --- | --- | --- | --- | --- |
| CBO (média) | 0.428 | <0.0001 | 0.190 | <0.0001 |
| DIT (média) | 0.241 | <0.0001 | 0.037 | 0.2458 |
| LCOM (média) | 0.461 | <0.0001 | 0.063 | 0.0514 |
| CBO (média) | 0.399 | <0.0001 | 0.075 | 0.0203 |
| DIT (média) | 0.216 | <0.0001 | -0.002 | 0.9403 |
| LCOM (média) | 0.436 | <0.0001 | 0.021 | 0.5102 |

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