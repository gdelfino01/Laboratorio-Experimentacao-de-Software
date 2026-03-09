import csv
import os
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
if not GITHUB_TOKEN:
    raise EnvironmentError(
        "Defina GITHUB_TOKEN no arquivo .env ou como variável de ambiente."
    )

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json",
}

SEARCH_QUERY = os.getenv("SEARCH_QUERY", "stars:>0 sort:stars-desc")
TOTAL_REPOS = int(os.getenv("TOTAL_REPOS", "100"))
PAGE_SIZE = min(int(os.getenv("PAGE_SIZE", "10")), 10)
CSV_FILENAME = os.getenv("CSV_FILENAME", "repositorios.csv")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))
REQUEST_SLEEP_SECONDS = float(os.getenv("REQUEST_SLEEP_SECONDS", "0.8"))

QUERY = """
query ($queryString: String!, $pageSize: Int!, $cursor: String) {
  rateLimit {
    cost
    remaining
    resetAt
  }
  search(query: $queryString, type: REPOSITORY, first: $pageSize, after: $cursor) {
    repositoryCount
    pageInfo {
      endCursor
      hasNextPage
    }
    nodes {
      ... on Repository {
        nameWithOwner
        url
        createdAt
        pushedAt
        stargazerCount
        primaryLanguage {
          name
        }
        mergedPullRequests: pullRequests(states: MERGED) {
          totalCount
        }
        releases {
          totalCount
        }
        totalIssues: issues {
          totalCount
        }
        closedIssues: issues(states: CLOSED) {
          totalCount
        }
      }
    }
  }
}
"""


def run_query(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    last_error: Optional[str] = None

    for attempt in range(6):
        try:
            response = requests.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            last_error = f"Falha de rede: {exc}"
            time.sleep((2 ** attempt) * 2)
            continue

        try:
            data = response.json()
        except ValueError:
            last_error = f"Resposta inválida da API (status {response.status_code})."
            time.sleep((2 ** attempt) * 2)
            continue

        if response.status_code >= 500:
            last_error = f"Erro do GitHub (status {response.status_code})."
            time.sleep((2 ** attempt) * 2)
            continue

        errors = data.get("errors", [])
        if errors:
            message = " | ".join(error.get("message", "Erro desconhecido") for error in errors)
            last_error = message

            rate_limited = any(
                term in message.lower()
                for term in ["rate limit", "secondary rate limit", "abuse detection"]
            )
            if rate_limited:
                time.sleep((2 ** attempt) * 5)
                continue
            raise RuntimeError(f"Erro GraphQL: {message}")

        return data

    raise RuntimeError(last_error or "Número máximo de tentativas excedido.")


def parse_iso_date(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def days_since(date_string: str) -> int:
    return (datetime.now(timezone.utc) - parse_iso_date(date_string)).days


def safe_ratio(closed_issues: int, total_issues: int) -> Optional[float]:
    if total_issues == 0:
        return None
    return closed_issues / total_issues


def fetch_repositories() -> List[Dict[str, Any]]:
    repositories: List[Dict[str, Any]] = []
    seen_names = set()
    cursor = None

    while len(repositories) < TOTAL_REPOS:
        size = min(PAGE_SIZE, TOTAL_REPOS - len(repositories))
        variables = {
            "queryString": SEARCH_QUERY,
            "pageSize": size,
            "cursor": cursor,
        }

        print(f"Buscando repositórios... ({len(repositories)}/{TOTAL_REPOS})")
        data = run_query(QUERY, variables)

        search_data = data["data"]["search"]
        rate_limit = data["data"].get("rateLimit", {})

        for node in search_data.get("nodes", []):
            if not node:
                continue
            repo_name = node.get("nameWithOwner")
            if not repo_name or repo_name in seen_names:
                continue
            repositories.append(node)
            seen_names.add(repo_name)

        print(
            "Taxa restante:",
            rate_limit.get("remaining", "?"),
            "| Custo:",
            rate_limit.get("cost", "?"),
        )

        if not search_data["pageInfo"]["hasNextPage"]:
            break

        cursor = search_data["pageInfo"]["endCursor"]
        time.sleep(REQUEST_SLEEP_SECONDS)

    print(f"Total coletado: {len(repositories)}")
    return repositories[:TOTAL_REPOS]


def process_repositories(repositories: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    processed: List[Dict[str, Any]] = []

    for repo in repositories:
        total_issues = repo["totalIssues"]["totalCount"]
        closed_issues = repo["closedIssues"]["totalCount"]
        issue_ratio = safe_ratio(closed_issues, total_issues)
        primary_language = repo.get("primaryLanguage") or {}

        processed.append(
            {
                "nome": repo["nameWithOwner"],
                "url": repo["url"],
                "estrelas": repo["stargazerCount"],
                "criado_em": repo["createdAt"],
                "idade_dias": days_since(repo["createdAt"]),
                "atualizado_em": repo["pushedAt"],
                "dias_desde_ultima_atualizacao": days_since(repo["pushedAt"]),
                "linguagem_primaria": primary_language.get("name") or "Desconhecida",
                "prs_aceitas": repo["mergedPullRequests"]["totalCount"],
                "releases": repo["releases"]["totalCount"],
                "issues_total": total_issues,
                "issues_fechadas": closed_issues,
                "razao_issues_fechadas": round(issue_ratio, 4) if issue_ratio is not None else "N/A",
            }
        )

    return processed


def save_csv(data: List[Dict[str, Any]], filename: str = CSV_FILENAME) -> None:
    if not data:
        print("Nenhum dado para salvar.")
        return

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(data[0].keys()))
        writer.writeheader()
        writer.writerows(data)

    print(f"Dados salvos em '{filename}'")


def numeric_column(data: List[Dict[str, Any]], key: str) -> List[float]:
    values = []
    for row in data:
        value = row[key]
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def print_numeric_summary(title: str, values: List[float], suffix: str = "") -> None:
    if not values:
        print(f"\n--- {title} ---")
        print("Sem dados disponíveis.")
        return

    print(f"\n--- {title} ---")
    print(f"Mediana: {statistics.median(values):.2f}{suffix}")
    print(f"Média: {statistics.mean(values):.2f}{suffix}")
    print(f"Mínimo: {min(values):.2f}{suffix}")
    print(f"Máximo: {max(values):.2f}{suffix}")


def print_language_distribution(data: List[Dict[str, Any]], top_n: int = 15) -> None:
    counts = Counter(row["linguagem_primaria"] for row in data)
    print("\nLinguagens primárias mais frequentes ---")
    for language, count in counts.most_common(top_n):
        print(f"{language}: {count}")


def print_bonus_by_language(data: List[Dict[str, Any]], top_n: int = 10) -> None:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in data:
        grouped[row["linguagem_primaria"]].append(row)

    print("\nPor linguagem ---")
    for language, rows in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True)[:top_n]:
        prs = numeric_column(rows, "prs_aceitas")
        releases = numeric_column(rows, "releases")
        updated = numeric_column(rows, "dias_desde_ultima_atualizacao")
        print(
            f"{language}: "
            f"n={len(rows)}, "
            f"mediana PRs={statistics.median(prs):.2f}, "
            f"mediana releases={statistics.median(releases):.2f}, "
            f"mediana dias sem atualização={statistics.median(updated):.2f}"
        )


def print_summary(data: List[Dict[str, Any]]) -> None:
    print_numeric_summary("Idade dos repositórios (dias)", numeric_column(data, "idade_dias"), " dias")
    print_numeric_summary("Pull requests aceitas", numeric_column(data, "prs_aceitas"))
    print_numeric_summary("Total de releases", numeric_column(data, "releases"))
    print_numeric_summary("Tempo até a última atualização", numeric_column(data, "dias_desde_ultima_atualizacao"), " dias")
    print_language_distribution(data)
    print_numeric_summary("Razão de issues fechadas / total de issues", numeric_column(data, "razao_issues_fechadas"))
    print_bonus_by_language(data)


if __name__ == "__main__":
    raw_repositories = fetch_repositories()
    processed_data = process_repositories(raw_repositories)
    save_csv(processed_data)
    print_summary(processed_data)