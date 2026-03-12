# Relatório – Lab01S02: Características de Sistemas Populares De Engenharia de Softaware - Open-Source

## 1. Introdução

### 1.1 Contextualização

O GitHub é a maior plataforma de hospedagem de código-fonte do mundo, reunindo milhões de repositórios open-source mantidos por desenvolvedores, empresas e comunidades. O número de estrelas de um repositório é amplamente utilizado como indicador de popularidade, refletindo o interesse e a aprovação da comunidade de desenvolvedores. Compreender as características dos projetos mais populares permite identificar padrões de sucesso e boas práticas no desenvolvimento de software open-source.

### 1.2 Problema Foco do Experimento

Apesar da grande quantidade de projetos disponíveis no GitHub, pouco se sabe de forma sistemática sobre as características que definem os sistemas mais populares. Questões como a maturidade desses projetos, o nível de contribuição externa que recebem, a frequência com que publicam releases, a regularidade de atualizações, as linguagens em que são escritos e a eficiência na gestão de issues permanecem sem respostas baseadas em dados concretos. Este experimento busca preencher essa lacuna analisando os 1.000 repositórios com maior número de estrelas no GitHub.

### 1.3 Questões de Pesquisa

- **RQ01.** Sistemas populares são maduros/antigos?
- **RQ02.** Sistemas populares recebem muita contribuição externa?
- **RQ03.** Sistemas populares lançam releases com frequência?
- **RQ04.** Sistemas populares são atualizados com frequência?
- **RQ05.** Sistemas populares são escritos nas linguagens mais populares?
- **RQ06.** Sistemas populares possuem um alto percentual de issues fechadas?
- **RQ07.** Linguagens mais populares também apresentam maiores indicadores de colaboração e manutenção?

### 1.4 Hipóteses

- **H1 (RQ01):** Espera-se que a maioria dos repositórios populares tenha sido criada há pelo menos **5 anos**, pois sistemas consolidados tiveram mais tempo para acumular estrelas e visibilidade na comunidade.

- **H2 (RQ02):** Espera-se que repositórios populares apresentem um **número elevado de pull requests aceitas** (mediana acima de 500), dado que a alta visibilidade atrai contribuidores externos interessados em colaborar.

- **H3 (RQ03):** Espera-se que a maioria dos projetos populares possua um **número expressivo de releases** (mediana acima de 20), indicando ciclos de desenvolvimento ativos com entregas regulares.

- **H4 (RQ04):** Espera-se que os repositórios populares tenham sido **atualizados muito recentemente** (mediana de tempo desde a última atualização inferior a 30 dias), refletindo manutenção contínua.

- **H5 (RQ05):** Espera-se que linguagens como **JavaScript, Python, TypeScript e Java** dominem entre os repositórios mais populares, acompanhando as tendências do ecossistema open-source.

- **H6 (RQ06):** Espera-se que a razão entre issues fechadas e total de issues seja **alta (acima de 0,70)**, sugerindo comunidades ativas que resolvem a maioria dos problemas reportados.

- **H7 (RQ07):** Espera-se que as linguagens mais frequentes entre os repositórios populares também apresentem maiores medianas de PRs aceitas, releases e menor tempo sem atualização.

### 1.5 Objetivos

**Objetivo Principal:**
Caracterizar os 1.000 repositórios mais populares do GitHub (por número de estrelas e com tema de engenharia de software) em relação à maturidade, contribuição externa, frequência de releases, atualização, linguagem de programação e gestão de issues.

**Objetivos Específicos:**
1. Coletar dados dos 1.000 repositórios mais estrelados via API GraphQL do GitHub, utilizando paginação automática.
2. Armazenar os dados coletados em formato CSV para análise reprodutível.
3. Calcular métricas quantitativas (medianas e médias) para cada questão de pesquisa.
4. Confrontar os resultados obtidos com as hipóteses formuladas.
5. Investigar se sistemas escritos em linguagens mais populares recebem mais contribuição, lançam mais releases e são atualizados com maior frequência.

---

## 2. Metodologia

### 2.1 Passo a Passo do Experimento

1. **Configuração do ambiente:** Instalação das dependências Python (`requests`, `python-dotenv`) e configuração do token de acesso à API do GitHub via variável de ambiente (`GITHUB_TOKEN`).
2. **Construção da query GraphQL:** Elaboração de uma consulta que retorna, para cada repositório, todos os campos necessários para responder às sete questões de pesquisa.
3. **Coleta com paginação:** Execução de requisições paginadas à API GraphQL do GitHub (40 páginas de 25 repositórios cada), ordenadas por número de estrelas em ordem decrescente, totalizando 1.000 repositórios.
4. **Processamento dos dados:** Cálculo de métricas derivadas (idade em dias, dias desde última atualização, razão de issues fechadas) a partir dos dados brutos retornados pela API.
5. **Armazenamento em CSV:** Exportação dos dados processados para o arquivo `repositorios.csv`.
6. **Sumarização:** Cálculo e exibição de valores medianos e médios para cada questão de pesquisa, além da contagem de linguagens primárias.

### 2.2 Decisões

| Decisão | Justificativa |
|---------|---------------|
| Uso da API GraphQL (em vez da REST) | Permite obter todos os campos necessários em uma única requisição por página, reduzindo o número de chamadas à API. |
| Paginação com cursor (`endCursor`) | Mecanismo recomendado pelo GitHub para percorrer grandes conjuntos de resultados de forma eficiente e consistente. |
| Tamanho de página = 25 | Valor máximo permitido pela API GraphQL do GitHub para buscas, minimizando o número total de requisições. |
| Critério de seleção: `microservices OR microservice OR software-engineering OR software engineering stars:>1 sort:stars-desc` | Garante a obtenção dos repositórios ordenados por popularidade (estrelas) que tem como tema engenharia de software ou microsserviços. |
| Intervalo de 1 segundo entre requisições | Evita atingir os limites de taxa (rate limit) da API do GitHub. |
| Retry com backoff exponencial (até 5 tentativas) | Garante resiliência contra erros transitórios (HTTP 502) e rate limiting. |
| Uso de mediana como medida central | A mediana é mais robusta a outliers do que a média, sendo mais adequada para distribuições assimétricas típicas de dados de repositórios. |

### 2.3 Materiais Utilizados

| Material | Descrição |
|----------|-----------|
| **GitHub API v4 (GraphQL)** | Fonte de dados para coleta de informações dos repositórios. |
| **Python 3** | Linguagem de programação utilizada para automação da coleta e processamento. |
| **Biblioteca `requests`** | Utilizada para realizar requisições HTTP à API GraphQL. |
| **Biblioteca `python-dotenv`** | Gerenciamento seguro do token de autenticação via arquivo `.env`. |
| **Módulo `csv`** | Exportação dos dados processados para arquivo CSV. |
| **Módulo `statistics`** | Cálculo de média e mediana das métricas coletadas. |
| **Token pessoal do GitHub (PAT)** | Autenticação para acesso à API com limites de taxa mais elevados. |

### 2.4 Métodos Utilizados

- **Mineração de repositórios de software:** Coleta automatizada de dados de repositórios do GitHub usando a API GraphQL, uma abordagem consolidada em estudos de Engenharia de Software Experimental.
- **Estatística descritiva:** Uso de média e mediana para sumarizar as distribuições de cada métrica, e contagem de frequência para dados categóricos (linguagem de programação).
- **Análise comparativa:** Comparação dos valores obtidos com as hipóteses formuladas previamente com base no senso comum e na literatura.

### 2.5 Métricas e suas Unidades

| Métrica | Questão | Descrição | Unidade |
|---------|---------|-----------|---------|
| Idade do repositório | RQ01 | Diferença entre a data atual e a data de criação do repositório. | Dias |
| Total de PRs aceitas | RQ02 | Número total de pull requests com estado "merged" (aceitas e incorporadas). | Unidades (contagem) |
| Total de releases | RQ03 | Número total de releases publicadas no repositório. | Unidades (contagem) |
| Tempo até última atualização | RQ04 | Diferença entre a data atual e a data do último push/atualização do repositório. | Dias |
| Linguagem primária | RQ05 | Linguagem de programação principal definida pelo GitHub para o repositório. | Categórica (nome da linguagem) |
| Razão de issues fechadas | RQ06 | Proporção entre o número de issues fechadas e o número total de issues (fechadas + abertas). | Razão (0,00 a 1,00) |
| Indicadores por linguagem | RQ07 | Medianas de PRs aceitas, releases, dias sem atualização e razão de issues fechadas por linguagem primária. | Misto (contagem, dias e razão) |

---

## 3. Visualização dos Resultados

Os resultados foram visualizados por meio de gráficos estatísticos gerados automaticamente pelo script `visualizacoes.py`, salvos na pasta `graficos/`. A escolha de cada tipo de gráfico foi orientada pela natureza dos dados e pelo objetivo de cada questão de pesquisa. O detalhamento completo de cada gráfico está no arquivo `graficos.md`.

### 3.1 Resultados Tabulares

#### RQ01 — Idade dos Repositórios (em anos)

| Estatística | Valor |
|-------------|-------|
| Mediana | 5,48 anos |
| Média | 5,59 anos |
| Mínimo | 0,00 anos |
| Máximo | 15,15 anos |
| 1º Quartil (Q1) | 2,57 anos |
| 3º Quartil (Q3) | 8,26 anos |

#### RQ02 — Pull Requests Aceitas

| Estatística | Valor |
|-------------|-------|
| Mediana | 6 |
| Média | 223 |
| Mínimo | 0 |
| Máximo | 18.454 |

#### RQ03 — Releases

| Estatística | Valor |
|-------------|-------|
| Mediana (todos) | 0 |
| Média | 12 |
| Repos sem releases (0) | 705 (70,5%) |
| Repos com ≥1 release | 295 (29,5%) |
| Mediana (apenas repos com releases) | 12 |

#### RQ04 — Dias Desde a Última Atualização

| Estatística | Valor |
|-------------|-------|
| Mediana | 382 dias |
| Média | 697 dias |
| Mínimo | 0 dias |
| Máximo | 4.888 dias |

#### RQ05 — Linguagens Primárias (Amostra Atual)

| Linguagem | Quantidade | Percentual |
|-----------|------------|------------|
| Desconhecida | 25 | 25,0% |
| Python | 21 | 21,0% |
| Jupyter Notebook | 10 | 10,0% |
| JavaScript | 7 | 7,0% |
| TypeScript | 6 | 6,0% |
| Go | 6 | 6,0% |
| Java | 4 | 4,0% |
| C++ | 4 | 4,0% |
| CSS | 3 | 3,0% |
| MDX | 2 | 2,0% |

#### RQ06 — Razão de Issues Fechadas

| Estatística | Valor |
|-------------|-------|
| Registros válidos | 98 |
| Mediana | 0,7368 |
| Média | 0,6667 |
| Mínimo | 0,0000 |
| Máximo | 1,0000 |
| 1º Quartil (Q1) | 0,4641 |
| 3º Quartil (Q3) | 0,9117 |
| Repos com razão ≥ 0,70 | 58 (59,18%) |

#### RQ07 — Indicadores por Linguagem (Top 8)

| Linguagem | n | Mediana PRs | Mediana Releases | Mediana dias sem atualização | Mediana razão issues |
|-----------|---|-------------|------------------|------------------------------|----------------------|
| Desconhecida | 25 | 12,0 | 0,0 | 472,0 | 0,5660 |
| Python | 21 | 145,0 | 9,0 | 7,0 | 0,7362 |
| Jupyter Notebook | 10 | 119,5 | 0,0 | 10,0 | 0,7976 |
| JavaScript | 7 | 66,0 | 0,0 | 25,0 | 0,6000 |
| TypeScript | 6 | 1735,5 | 285,5 | 1,0 | 0,7870 |
| Go | 6 | 2640,0 | 117,0 | 3,0 | 0,7697 |
| Java | 4 | 593,5 | 40,0 | 3,5 | 0,7477 |
| C++ | 4 | 1199,0 | 31,0 | 1,0 | 0,7520 |


### 3.2 Gráficos Gerados

| Gráfico | Arquivo | RQ |
|---------|---------|-----|
| Boxplot da Idade | `graficos/rq01_boxplot.png` | RQ01 |
| Histograma da Idade | `graficos/rq01_histograma.png` | RQ01 |
| Boxplot de PRs Aceitas (log) | `graficos/rq02_boxplot.png` | RQ02 |
| Scatter Estrelas × PRs | `graficos/rq02_scatter.png` | RQ02 |
| Barras com/sem Releases | `graficos/rq03_barras.png` | RQ03 |
| Boxplot de Releases (log) | `graficos/rq03_boxplot.png` | RQ03 |
| Histograma de Releases | `graficos/rq03_histograma.png` | RQ03 |
| Boxplot Dias Desde Atualização | `graficos/rq04_boxplot.png` | RQ04 |
| Histograma Dias Desde Atualização | `graficos/rq04_histograma.png` | RQ04 |
| Barras de Linguagens Primárias | `graficos/rq05_top_linguagens.png` | RQ05 |
| Curva Acumulada de Linguagens | `graficos/rq05_pareto_linguagens.png` | RQ05 |
| Boxplot Razão de Issues Fechadas | `graficos/rq06_boxplot.png` | RQ06 |
| Histograma Razão de Issues Fechadas | `graficos/rq06_histograma.png` | RQ06 |
| PRs e Releases por Linguagem | `graficos/rq07_prs_releases_por_linguagem.png` | RQ07 |

---

## 4. Discussão dos Resultados

### 4.1 Confronto com as Questões de Pesquisa

#### RQ01 — Sistemas populares são maduros/antigos?

**Resultado:** A mediana da idade é de **5,48 anos** e a média é de 5,59 anos. O primeiro quartil está em 2,57 anos e o terceiro quartil em 8,26 anos.

**Confronto com H1:** A hipótese previa que a maioria teria pelo menos 5 anos. Com a mediana em 5,48, a hipótese **H1 é confirmada**: mais da metade dos repositórios populares tem pelo menos 5 anos de existência. Isso indica que a acumulação de estrelas é, de fato, um processo que demanda tempo. No entanto, o Q1 em 2,57 anos mostra que 25% dos projetos têm menos de 2,5 anos, indicando que projetos recentes com propostas inovadoras (ex: ferramentas de IA generativa, LLMs) também alcançam alta popularidade rapidamente.

#### RQ02 — Sistemas populares recebem muita contribuição externa?

**Resultado:** A mediana de PRs aceitas é de apenas **6**, enquanto a média é de 223. A discrepância revela uma distribuição extremamente assimétrica: poucos projetos concentram milhares de PRs (máximo de 18.454), enquanto a maioria recebe poucas contribuições.

**Confronto com H2:** A hipótese previa mediana acima de 500. Com mediana de 6, a hipótese **H2 é refutada**. A maioria dos repositórios populares no contexto de engenharia de software são listas curadas, tutoriais e materiais de referência que, por natureza, não demandam grande volume de pull requests. A popularidade (estrelas) não implica necessariamente contribuição externa ativa via PRs.

#### RQ03 — Sistemas populares lançam releases com frequência?

**Resultado:** **70,5% dos repositórios** (705) não possuem nenhuma release. Entre os 295 que publicam releases, a mediana é de **12 releases**.

**Confronto com H3:** A hipótese previa mediana acima de 20. Com mediana geral de 0 e, mesmo filtrando os que têm releases, mediana de 12, a hipótese **H3 é refutada**. A grande maioria dos projetos populares de engenharia de software não utiliza o sistema de releases do GitHub, o que é coerente com a natureza de muitos deles (documentação, listas, tutoriais). Contudo, entre os projetos com releases, o número é expressivo e indica ciclos de desenvolvimento ativos.

#### RQ04 — Sistemas populares são atualizados com frequência?

**Resultado:** A mediana de dias desde a última atualização é de **382 dias** e a média é de 697 dias.

**Confronto com H4:** A hipótese previa mediana inferior a 30 dias. Com 382 dias, a hipótese **H4 é refutada**. Muitos repositórios populares de engenharia de software atingem um estado estável (listas curadas, tutoriais completos) e não necessitam de atualizações frequentes. Isso difere de projetos de software ativo (frameworks, bibliotecas), que são atualizados continuamente.

#### RQ05 — Sistemas populares são escritos nas linguagens mais populares?

**Resultado:** Na amostra atual do arquivo `repositorios.csv`, as linguagens mais frequentes foram **Desconhecida (25%)**, **Python (21%)**, **Jupyter Notebook (10%)**, seguidas por JavaScript (7%), TypeScript (6%) e Go (6%).

**Confronto com H5:** A hipótese **H5 é parcialmente confirmada**. Linguagens tradicionais do ecossistema (Python, JavaScript, TypeScript e Java) aparecem no topo, mas o conjunto também apresenta forte presença de projetos sem linguagem principal definida e de repositórios orientados a notebooks.

#### RQ06 — Sistemas populares possuem alto percentual de issues fechadas?

**Resultado:** Considerando 98 repositórios com valor válido, a mediana da razão de issues fechadas foi **0,7368** (Q1 = 0,4641; Q3 = 0,9117). Além disso, **59,18%** dos repositórios apresentam razão maior ou igual a 0,70.

**Confronto com H6:** A hipótese **H6 é confirmada** pela mediana acima de 0,70. Entretanto, a dispersão (Q1 abaixo de 0,50) indica que parte relevante dos projetos ainda apresenta gestão de issues menos eficiente.

#### RQ07 — Linguagens mais populares também concentram melhores indicadores de colaboração e manutenção?

**Resultado:** A comparação por linguagem mostrou comportamento heterogêneo. Linguagens com menor frequência na amostra, como **Go** e **TypeScript**, apresentaram medianas muito altas de PRs aceitas e releases. Já linguagens mais frequentes, como Python, tiveram indicadores bons, porém menos extremos. Em atualização, TypeScript e C++ tiveram mediana de 1 dia sem atualização, enquanto o grupo "Desconhecida" ficou em 472 dias.

**Confronto com H7:** A hipótese **H7 é parcialmente refutada**. A frequência de uma linguagem no conjunto não implica, por si só, maior colaboração externa ou maior ritmo de releases. Os resultados sugerem que o tipo do projeto e o perfil da comunidade são fatores mais determinantes do que a popularidade da linguagem isoladamente.

---

## 5. Conclusão

O experimento foi concluído com visualizações e discussão cobrindo **RQ01 a RQ07**. As novas análises mostraram que o ecossistema estudado combina projetos altamente ativos com outros mais estáveis/documentais, o que explica a coexistência de métricas de colaboração muito altas em subgrupos e baixa atividade em parte significativa da amostra.

Do ponto de vista de decisão, os resultados indicam que avaliar popularidade apenas por estrelas é insuficiente para inferir maturidade operacional. Para análises futuras, recomenda-se segmentar o conjunto por tipo de repositório (biblioteca, framework, tutorial, lista curada, notebook) antes de comparar colaboração, releases e manutenção.

Como continuidade, podem ser exploradas duas extensões: (i) ampliar a amostra para o total planejado de 1.000 repositórios no mesmo pipeline e (ii) confrontar os achados com estudos prévios de mineração de repositórios em Engenharia de Software.


