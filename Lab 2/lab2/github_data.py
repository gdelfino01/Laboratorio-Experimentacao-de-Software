import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import requests

from .config import GRAPHQL_URL, QUERY, SEARCH_QUERY, DEFAULT_PAGE_SIZE, DEFAULT_TOTAL_REPOS


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise EnvironmentError(f"Defina {name} no arquivo .env")
    return value


def get_headers() -> Dict[str, str]:
    token = require_env("GITHUB_TOKEN")
    return {"Authorization": f"Bearer {token}"}


def run_query(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    last_error = None

    for attempt in range(5):
        try:
            resp = requests.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=get_headers(),
                timeout=60,
            )

            if resp.status_code in (502, 503):
                wait_time = 2**attempt * 5
                print(
                    f"   Erro {resp.status_code}, tentativa {attempt + 1}/5, "
                    f"aguardando {wait_time}s..."
                )
                time.sleep(wait_time)
                continue

            if resp.status_code == 401:
                raise RuntimeError(
                    "Token inválido ou expirado. Verifique GITHUB_TOKEN no .env"
                )

            if resp.status_code != 200:
                print(f"   HTTP {resp.status_code}, tentativa {attempt + 1}/5")
                time.sleep(2**attempt * 5)
                continue

            try:
                data = resp.json()
            except Exception:
                print(f"   Resposta não-JSON, tentativa {attempt + 1}/5")
                time.sleep(2**attempt * 5)
                continue

            errors = data.get("errors", [])
            if errors:
                message = " | ".join(e.get("message", "?") for e in errors)
                last_error = message

                if any(term in message.lower() for term in ["rate limit", "secondary rate limit"]):
                    wait_time = 2**attempt * 5
                    print(
                        f"   Rate limit, tentativa {attempt + 1}/5, "
                        f"aguardando {wait_time}s..."
                    )
                    time.sleep(wait_time)
                    continue

                raise RuntimeError(f"Erro GraphQL: {message}")

            return data

        except requests.exceptions.Timeout:
            print(f"   Timeout, tentativa {attempt + 1}/5")
            time.sleep(2**attempt * 5)
        except requests.exceptions.ConnectionError:
            print(f"   Erro de conexão, tentativa {attempt + 1}/5")
            time.sleep(2**attempt * 5)

    raise RuntimeError(f"Número máximo de tentativas excedido. Último erro: {last_error}")


def parse_iso_date(date_string: str) -> datetime:
    return datetime.fromisoformat(date_string.replace("Z", "+00:00"))


def calculate_age_years(created_at: str) -> float:
    created_date = parse_iso_date(created_at)
    now = datetime.now(timezone.utc)
    age_days = (now - created_date).days
    return round(age_days / 365.25, 2)


def fetch_repositories(
    total_repos: int = DEFAULT_TOTAL_REPOS,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> List[Dict[str, Any]]:
    repositories: List[Dict[str, Any]] = []
    seen_names = set()
    cursor = None

    while len(repositories) < total_repos:
        size = min(page_size, total_repos - len(repositories))
        variables = {
            "queryString": SEARCH_QUERY,
            "pageSize": size,
            "cursor": cursor,
        }

        print(f" Buscando repositórios... ({len(repositories)}/{total_repos})")

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
            f"   Taxa restante: {rate_limit.get('remaining', '?')} | "
            f"Custo: {rate_limit.get('cost', '?')}"
        )

        if not search_data["pageInfo"]["hasNextPage"]:
            break

        cursor = search_data["pageInfo"]["endCursor"]
        time.sleep(1)

    print(f"\n Total coletado: {len(repositories)} repositórios")
    return repositories[:total_repos]


def process_repositories(repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    processed: List[Dict[str, Any]] = []

    for rank, repo in enumerate(repositories, 1):
        watchers = repo.get("watchers", {}).get("totalCount", 0)
        processed.append(
            {
                "rank": rank,
                "nameWithOwner": repo.get("nameWithOwner", "N/A"),
                "url": repo.get("url", "N/A"),
                "stars": repo.get("stargazerCount", 0),
                "forks": repo.get("forkCount", 0),
                "watchers": watchers,
                "releases": repo.get("releases", {}).get("totalCount", 0),
                "created_at": repo.get("createdAt", "N/A"),
                "age_years": calculate_age_years(
                    repo.get("createdAt", "2000-01-01T00:00:00Z")
                ),
            }
        )

    return processed
