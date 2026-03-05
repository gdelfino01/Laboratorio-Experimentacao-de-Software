import os
import csv
import time
import statistics
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
if not GITHUB_TOKEN:
    raise EnvironmentError(
        "Defina GITHUB_TOKEN no arquivo .env ou como variável de ambiente."
    )

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
SEARCH_QUERY = "microservices OR microservice OR software-engineering OR software engineering stars:>1 sort:stars-desc"
TOTAL_REPOS = 1000
PAGE_SIZE = 25

QUERY = """
query ($queryString: String!, $pageSize: Int!, $cursor: String) {
  search(query: $queryString, type: REPOSITORY, first: $pageSize, after: $cursor) {
    pageInfo { endCursor hasNextPage }
    nodes {
      ... on Repository {
        nameWithOwner
        url
        createdAt
        stargazerCount
        mergedPullRequests: pullRequests(states: MERGED) { totalCount }
        releases { totalCount }
      }
    }
  }
}
"""


def run_query(query, variables):
    for attempt in range(5):
        resp = requests.post(GRAPHQL_URL, json={"query": query, "variables": variables}, headers=HEADERS, timeout=60)

        if resp.status_code in (502, 503):
            print(f"  Erro {resp.status_code} (body={resp.text[:200]}), tentativa {attempt + 1}/5...")
            time.sleep(2 ** attempt * 5)
            continue

        if resp.status_code != 200:
            print(f"  HTTP {resp.status_code}: {resp.text[:300]}")

        if resp.status_code == 401:
            raise Exception("Token inválido ou expirado. Verifique GITHUB_TOKEN no .env")

        try:
            data = resp.json()
        except Exception:
            print(f"  Resposta não-JSON (HTTP {resp.status_code}), tentativa {attempt + 1}/5...")
            time.sleep(2 ** attempt * 5)
            continue

        if "rate" in str(data.get("errors", "")).lower():
            print(f"  Rate limit atingido, aguardando...")
            time.sleep(2 ** attempt * 5)
            continue
        if "errors" in data:
            raise Exception(f"Erro GraphQL: {data['errors']}")
        return data
    raise Exception("Número máximo de tentativas excedido.")


def fetch_repositories():
    repos = []
    cursor = None

    while len(repos) < TOTAL_REPOS:
        size = min(PAGE_SIZE, TOTAL_REPOS - len(repos))
        variables = {"queryString": SEARCH_QUERY, "pageSize": size, "cursor": cursor}

        print(f"Buscando repos... ({len(repos)}/{TOTAL_REPOS})")
        data = run_query(QUERY, variables)
        search = data["data"]["search"]

        for node in search["nodes"]:
            if node and node.get("nameWithOwner"):
                repos.append(node)

        if not search["pageInfo"]["hasNextPage"]:
            break
        cursor = search["pageInfo"]["endCursor"]
        time.sleep(1)

    print(f"Total coletado: {len(repos)}")
    return repos[:TOTAL_REPOS]


def calc_age_days(created_at):
    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - created).days


def process_repos(repos):
    processed = []
    for r in repos:
        processed.append({
            "nome": r["nameWithOwner"],
            "url": r["url"],
            "estrelas": r["stargazerCount"],
            "idade_dias": calc_age_days(r["createdAt"]),
            "criado_em": r["createdAt"],
            "pr_aceitas": r["mergedPullRequests"]["totalCount"],
            "releases": r["releases"]["totalCount"],
        })
    return processed


def save_csv(data, filename="repositorios.csv"):
    if not data:
        return
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"Dados salvos em '{filename}'")


def print_summary(data):
    ages = [d["idade_dias"] for d in data]
    prs = [d["pr_aceitas"] for d in data]
    releases = [d["releases"] for d in data]

    print("\n--- RQ01: Idade dos repositórios ---")
    print(f"Média: {statistics.mean(ages):.0f} dias ({statistics.mean(ages)/365:.1f} anos)")
    print(f"Mediana: {statistics.median(ages):.0f} dias ({statistics.median(ages)/365:.1f} anos)")

    print("\n--- RQ02: Pull Requests aceitas ---")
    print(f"Média: {statistics.mean(prs):.0f}")
    print(f"Mediana: {statistics.median(prs):.0f}")

    print("\n--- RQ03: Total de releases ---")
    print(f"Média: {statistics.mean(releases):.0f}")
    print(f"Mediana: {statistics.median(releases):.0f}")


if __name__ == "__main__":
    repos_raw = fetch_repositories()
    repos_data = process_repos(repos_raw)
    save_csv(repos_data)
    print_summary(repos_data)
