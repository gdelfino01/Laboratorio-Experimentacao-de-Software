import csv
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
if not GITHUB_TOKEN:
    raise EnvironmentError("Defina GITHUB_TOKEN no arquivo .env")

GRAPHQL_URL = "https://api.github.com/graphql"
HEADERS = {"Authorization": f"Bearer {GITHUB_TOKEN}"}

SEARCH_QUERY = "language:Java stars:>100 sort:stars-desc"
TOTAL_REPOS = 1000
PAGE_SIZE = 25

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
        stargazerCount
        forkCount
        watchers {
          totalCount
        }
        releases {
          totalCount
        }
        isArchived
        isFork
      }
    }
  }
}
"""

def run_query(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Executa query GraphQL com retry automático (backoff exponencial)"""
    last_error = None
    
    for attempt in range(5):
        try:
            resp = requests.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=HEADERS,
                timeout=60
            )
            
            if resp.status_code in (502, 503):
                wait_time = 2 ** attempt * 5
                print(f"   Erro {resp.status_code}, tentativa {attempt + 1}/5, aguardando {wait_time}s...")
                time.sleep(wait_time)
                continue
            
            if resp.status_code == 401:
                raise Exception(" Token inválido ou expirado. Verifique GITHUB_TOKEN no .env")
            
            if resp.status_code != 200:
                print(f"   HTTP {resp.status_code}, tentativa {attempt + 1}/5")
                time.sleep(2 ** attempt * 5)
                continue
            
            try:
                data = resp.json()
            except Exception:
                print(f"   Resposta não-JSON, tentativa {attempt + 1}/5")
                time.sleep(2 ** attempt * 5)
                continue
            
            errors = data.get("errors", [])
            if errors:
                message = " | ".join(e.get("message", "?") for e in errors)
                last_error = message
                
                if any(term in message.lower() for term in ["rate limit", "secondary rate limit"]):
                    wait_time = 2 ** attempt * 5
                    print(f"  Rate limit, tentativa {attempt + 1}/5, aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise RuntimeError(f"Erro GraphQL: {message}")
            
            return data
        
        except requests.exceptions.Timeout:
            print(f"  Timeout, tentativa {attempt + 1}/5")
            time.sleep(2 ** attempt * 5)
            continue
        except requests.exceptions.ConnectionError:
            print(f"  Erro de conexão, tentativa {attempt + 1}/5")
            time.sleep(2 ** attempt * 5)
            continue
    
    raise RuntimeError(f"Número máximo de tentativas excedido. Último erro: {last_error}")


def parse_iso_date(date_string: str) -> datetime:
    """Converte data ISO para datetime"""
    return datetime.fromisoformat(date_string.replace("Z", "+00:00"))


def calculate_age_years(created_at: str) -> float:
    """Calcula idade do repositório em anos"""
    created_date = parse_iso_date(created_at)
    now = datetime.now(timezone.utc)
    age_days = (now - created_date).days
    return round(age_days / 365.25, 2)


def fetch_repositories() -> List[Dict[str, Any]]:
    """Coleta 1.000 repositórios Java mais populares do GitHub"""
    repositories: List[Dict[str, Any]] = []
    seen_names = set()
    cursor = None
    
    while len(repositories) < TOTAL_REPOS:
        size = min(PAGE_SIZE, TOTAL_REPOS - len(repositories))
        variables = {
            "queryString": SEARCH_QUERY,
            "pageSize": size,
            "cursor": cursor
        }
        
        print(f" Buscando repositórios... ({len(repositories)}/{TOTAL_REPOS})")
        
        data = run_query(QUERY, variables)
        search_data = data["data"]["search"]
        rate_limit = data["data"].get("rateLimit", {})
        
        for node in search_data.get("nodes", []):
            if not node:
                continue
            
            repo_name = node.get("nameWithOwner")
            
            if not repo_name or repo_name in seen_names:
                continue
            if node.get("isArchived") or node.get("isFork"):
                continue
            
            repositories.append(node)
            seen_names.add(repo_name)
        
        print(f"   Taxa restante: {rate_limit.get('remaining', '?')} | "
              f"Custo: {rate_limit.get('cost', '?')}")
        
        if not search_data["pageInfo"]["hasNextPage"]:
            break
        
        cursor = search_data["pageInfo"]["endCursor"]
        time.sleep(1)  
    
    print(f"\n Total coletado: {len(repositories)} repositórios")
    return repositories[:TOTAL_REPOS]


def process_repositories(repositories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Processa repositórios e extrai os campos necessários"""
    processed = []
    
    for rank, repo in enumerate(repositories, 1):
        watchers = repo.get("watchers", {}).get("totalCount", 0)
        
        processed.append({
            "rank": rank,
            "nameWithOwner": repo.get("nameWithOwner", "N/A"),
            "url": repo.get("url", "N/A"),
            "stars": repo.get("stargazerCount", 0),
            "forks": repo.get("forkCount", 0),
            "watchers": watchers,
            "releases": repo.get("releases", {}).get("totalCount", 0),
            "created_at": repo.get("createdAt", "N/A"),
            "age_years": calculate_age_years(repo.get("createdAt", "2000-01-01T00:00:00Z")),
        })
    
    return processed


def save_csv(data: List[Dict[str, Any]], filename: str = "repositorios.csv") -> None:
    """Salva dados em arquivo CSV"""
    if not data:
        print(" Nenhum dado para salvar.")
        return
    
    fieldnames = [
        "rank",
        "nameWithOwner",
        "url",
        "stars",
        "forks",
        "watchers",
        "releases",
        "created_at",
        "age_years"
    ]
    
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f" Dados salvos em '{filename}'")
    print(f"   Total de linhas: {len(data)}")


def main():
    """Coleta 1.000 repositórios Java mais populares do GitHub"""
    print("=" * 70)
    print("🚀 Lab 2 - Sprint 1: Coleta de 1.000 Repositórios Java")
    print("=" * 70)
    print()
    
    try:
        # Coletar
        print(" Fase 1: Coleta de Repositórios")
        print("-" * 70)
        repositories = fetch_repositories()
        
        # Processar
        print("\n Fase 2: Processamento de Dados")
        print("-" * 70)
        processed = process_repositories(repositories)
        
        # Salvar
        print("\n Fase 3: Salvamento em CSV")
        print("-" * 70)
        save_csv(processed)
        
        # Resumo
        print("\n" + "=" * 70)
        print(" SUCESSO!")
        print("=" * 70)
        print(f"Total de repositórios coletados: {len(processed)}")
        print(f"Arquivo: repositorios.csv")
        print()
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        exit(1)


if __name__ == "__main__":
    main()
