# Lab 2 - Sprint 1: Coleta de Repositórios Java

## 📋 Objetivo

Coletar os **1.000 repositórios Java mais populares** do GitHub usando GraphQL API, extraindo dados para análise de qualidade de software.

## 🚀 Como Executar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Executar coleta

```bash
python main.py
```

### 3. Resultado

Um arquivo `repositorios.csv` será gerado com 1.000 linhas contendo:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `rank` | int | Posição na lista (1-1000) |
| `nameWithOwner` | str | Nome do repositório (dono/repo) |
| `url` | str | Link direto no GitHub |
| `stars` | int | Número de estrelas (RQ 01) |
| `forks` | int | Número de forks |
| `watchers` | int | Número de watchers |
| `releases` | int | Número de releases (RQ 03) |
| `created_at` | str | Data de criação (ISO) |
| `age_years` | float | Idade em anos (RQ 02) |

## ⏱️ Tempo de Execução

- **Requisições**: ~40 (1.000 repos ÷ 25 por página)
- **Rate Limit Consumido**: ~250 pontos de 1.000
- **Tempo Estimado**: 5-10 minutos

## 📊 Dados Coletados

- **Repositórios**: Top 1.000 Java mais populares
- **Filtro**: `language:Java stars:>100 sort:stars-desc`
- **Exclusões**: Arquivos, forks

## 🔧 Infraestrutura

- **GraphQL Endpoint**: `https://api.github.com/graphql`
- **Autenticação**: Token do GitHub (`.env`)
- **Retry**: Backoff exponencial (2^n segundos) com máx 5 tentativas
- **Paginação**: Cursor-based

## 📝 Próximas Etapas

- Sprint 1.5: Clone dos 1.000 repositórios *(seu colega)*
- Sprint 2: Análise com CK tool *(seu colega)*
- Sprint 3: Análise estatística + Relatório final

---

**Desenvolvido para**: Lab de Experimentação de Software - Sexto Período
