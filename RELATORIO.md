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

### 1.4 Hipóteses

- **H1 (RQ01):** Espera-se que a maioria dos repositórios populares tenha sido criada há pelo menos **5 anos**, pois sistemas consolidados tiveram mais tempo para acumular estrelas e visibilidade na comunidade.

- **H2 (RQ02):** Espera-se que repositórios populares apresentem um **número elevado de pull requests aceitas** (mediana acima de 500), dado que a alta visibilidade atrai contribuidores externos interessados em colaborar.

- **H3 (RQ03):** Espera-se que a maioria dos projetos populares possua um **número expressivo de releases** (mediana acima de 20), indicando ciclos de desenvolvimento ativos com entregas regulares.

- **H4 (RQ04):** Espera-se que os repositórios populares tenham sido **atualizados muito recentemente** (mediana de tempo desde a última atualização inferior a 30 dias), refletindo manutenção contínua.

- **H5 (RQ05):** Espera-se que linguagens como **JavaScript, Python, TypeScript e Java** dominem entre os repositórios mais populares, acompanhando as tendências do ecossistema open-source.

- **H6 (RQ06):** Espera-se que a razão entre issues fechadas e total de issues seja **alta (acima de 0,70)**, sugerindo comunidades ativas que resolvem a maioria dos problemas reportados.

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
2. **Construção da query GraphQL:** Elaboração de uma consulta que retorna, para cada repositório, todos os campos necessários para responder às seis questões de pesquisa.
3. **Coleta com paginação:** Execução de requisições paginadas à API GraphQL do GitHub (10 páginas de 100 repositórios cada), ordenadas por número de estrelas em ordem decrescente, totalizando 1.000 repositórios.
4. **Processamento dos dados:** Cálculo de métricas derivadas (idade em dias, dias desde última atualização, razão de issues fechadas) a partir dos dados brutos retornados pela API.
5. **Armazenamento em CSV:** Exportação dos dados processados para o arquivo `repositorios.csv`.
6. **Sumarização:** Cálculo e exibição de valores medianos e médios para cada questão de pesquisa, além da contagem de linguagens primárias.

### 2.2 Decisões

| Decisão | Justificativa |
|---------|---------------|
| Uso da API GraphQL (em vez da REST) | Permite obter todos os campos necessários em uma única requisição por página, reduzindo o número de chamadas à API. |
| Paginação com cursor (`endCursor`) | Mecanismo recomendado pelo GitHub para percorrer grandes conjuntos de resultados de forma eficiente e consistente. |
| Tamanho de página = 100 | Valor máximo permitido pela API GraphQL do GitHub para buscas, minimizando o número total de requisições. |
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

---


