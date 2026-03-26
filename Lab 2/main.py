# collect-repos
# measure-one-repo --repo-url https://github.com/google/gson
# sprint1 --repo-url https://github.com/google/gson

import argparse
import csv
import os
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, Iterable, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

GRAPHQL_URL = "https://api.github.com/graphql"
SEARCH_QUERY = "language:Java stars:>100 sort:stars-desc"
DEFAULT_TOTAL_REPOS = 100
DEFAULT_PAGE_SIZE = 25
DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_WORKSPACE_DIR = Path("workspace")
DEFAULT_CK_DIR = Path("tools") / "ck"

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


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise EnvironmentError(f"Defina {name} no arquivo .env")
    return value


def get_headers() -> Dict[str, str]:
    token = require_env("GITHUB_TOKEN")
    return {"Authorization": f"Bearer {token}"}


def run_query(query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
    """Executa query GraphQL com retry automático."""
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


def fetch_repositories(total_repos: int = DEFAULT_TOTAL_REPOS, page_size: int = DEFAULT_PAGE_SIZE) -> List[Dict[str, Any]]:
    """Coleta os repositórios Java mais populares do GitHub."""
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
            if node.get("isArchived") or node.get("isFork"):
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
    processed = []

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


def save_csv(data: List[Dict[str, Any]], filename: Path) -> None:
    if not data:
        raise ValueError("Nenhum dado para salvar.")

    filename.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(data[0].keys())

    with filename.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f" Dados salvos em '{filename}'")
    print(f"   Total de linhas: {len(data)}")


def run_subprocess(command: List[str], cwd: Optional[Path] = None) -> None:
    printable_command = " ".join(command)
    print(f"$ {printable_command}")
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def sanitize_repo_name(name_with_owner: str) -> str:
    return name_with_owner.replace("/", "__")


def clone_repository(repo_url: str, destination: Path, refresh: bool = True) -> Path:
    if destination.exists() and refresh:
        shutil.rmtree(destination)

    destination.parent.mkdir(parents=True, exist_ok=True)
    run_subprocess(["git", "clone", "--depth", "1", repo_url, str(destination)])
    return destination


def ensure_ck_jar(ck_repo_dir: Path, force_rebuild: bool = False) -> Path:
    ck_repo_dir = ck_repo_dir.resolve()
    ck_repo_dir.parent.mkdir(parents=True, exist_ok=True)

    if not ck_repo_dir.exists():
        run_subprocess(["git", "clone", "https://github.com/mauricioaniche/ck", str(ck_repo_dir)])

    if force_rebuild:
        target_dir = ck_repo_dir / "target"
        if target_dir.exists():
            shutil.rmtree(target_dir)

    run_subprocess(["mvn", "clean", "compile", "package", "-DskipTests"], cwd=ck_repo_dir)

    jar_candidates = sorted(
        ck_repo_dir.glob("target/*jar-with-dependencies.jar"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not jar_candidates:
        raise FileNotFoundError(
            "Não foi possível localizar o jar do CK em target/*jar-with-dependencies.jar"
        )

    ck_jar = jar_candidates[0]
    print(f" CK pronto em: {ck_jar}")
    return ck_jar


def run_ck(ck_jar: Path, project_dir: Path, output_dir: Path, use_jars: bool = False, variables_and_fields: bool = False) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    run_subprocess(
        [
            "java",
            "-jar",
            str(ck_jar),
            str(project_dir),
            str(use_jars).lower(),
            "0",
            str(variables_and_fields).lower(),
            str(output_dir),
        ]
    )


def find_ck_class_csv(output_dir: Path) -> Path:
    candidates = []
    for pattern in ["class.csv", "*class*.csv", "class_level*.csv"]:
        candidates.extend(output_dir.glob(pattern))

    unique_candidates = []
    seen = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            unique_candidates.append(candidate)
            seen.add(resolved)

    if not unique_candidates:
        raise FileNotFoundError(
            f"Nenhum CSV de classes do CK foi encontrado em {output_dir}"
        )

    return unique_candidates[0]


def to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()
    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def find_column_name(fieldnames: Iterable[str], desired_name: str) -> Optional[str]:
    normalized = desired_name.lower().strip()
    for field in fieldnames:
        if field.lower().strip() == normalized:
            return field
    return None


def summarize_numeric_series(values: List[float]) -> Dict[str, float]:
    if not values:
        raise ValueError("A lista de valores está vazia.")

    return {
        "mean": round(statistics.fmean(values), 4),
        "median": round(statistics.median(values), 4),
        "stdev": round(statistics.pstdev(values), 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def summarize_ck_metrics(class_csv_path: Path, repository_name: str, summary_output_path: Path) -> Dict[str, Any]:
    with class_csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        if not rows:
            raise ValueError(f"O arquivo {class_csv_path} não possui linhas de dados.")

        if not reader.fieldnames:
            raise ValueError(f"O arquivo {class_csv_path} não possui cabeçalho.")

        fieldnames = reader.fieldnames

    metric_columns = {}
    for metric in ["cbo", "dit", "lcom", "loc"]:
        column_name = find_column_name(fieldnames, metric)
        if column_name:
            metric_columns[metric] = column_name

    missing = [metric.upper() for metric in ["cbo", "dit", "lcom"] if metric not in metric_columns]
    if missing:
        raise ValueError(
            f"As colunas obrigatórias {', '.join(missing)} não foram encontradas em {class_csv_path}."
        )

    summary_row: Dict[str, Any] = {
        "repository": repository_name,
        "class_csv": str(class_csv_path),
        "classes_analyzed": len(rows),
    }

    for metric, column_name in metric_columns.items():
        values = [to_float(row.get(column_name)) for row in rows]
        numeric_values = [value for value in values if value is not None]
        if not numeric_values:
            continue

        stats = summarize_numeric_series(numeric_values)
        summary_row[f"{metric}_mean"] = stats["mean"]
        summary_row[f"{metric}_median"] = stats["median"]
        summary_row[f"{metric}_stdev"] = stats["stdev"]
        summary_row[f"{metric}_min"] = stats["min"]
        summary_row[f"{metric}_max"] = stats["max"]

    summary_output_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary_row.keys()))
        writer.writeheader()
        writer.writerow(summary_row)

    print(f" Resumo salvo em '{summary_output_path}'")
    return summary_row


def measure_one_repository(
    repo_url: str,
    output_dir: Path,
    workspace_dir: Path,
    ck_repo_dir: Path,
    force_rebuild_ck: bool = False,
) -> Dict[str, Any]:
    repo_name = repo_url.rstrip("/").split("github.com/")[-1].replace(".git", "")
    repo_slug = sanitize_repo_name(repo_name)

    cloned_repo_dir = workspace_dir / repo_slug
    repo_output_dir = output_dir / repo_slug
    ck_output_dir = repo_output_dir / "ck_raw"
    summary_output_path = repo_output_dir / "repo_metrics_summary.csv"

    print("=" * 70)
    print(f" Medindo repositório: {repo_name}")
    print("=" * 70)

    ck_jar = ensure_ck_jar(ck_repo_dir=ck_repo_dir, force_rebuild=force_rebuild_ck)
    clone_repository(repo_url=repo_url, destination=cloned_repo_dir, refresh=True)
    run_ck(ck_jar=ck_jar, project_dir=cloned_repo_dir, output_dir=ck_output_dir)

    class_csv_path = find_ck_class_csv(ck_output_dir)
    summary = summarize_ck_metrics(
        class_csv_path=class_csv_path,
        repository_name=repo_name,
        summary_output_path=summary_output_path,
    )

    print("\n Resultado resumido:")
    for key, value in summary.items():
        print(f" - {key}: {value}")

    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sprint 1 do laboratório: coleta dos 1.000 repositórios Java e automação do CK."
    )
    subparsers = parser.add_subparsers(dest="command")

    collect_parser = subparsers.add_parser(
        "collect-repos", help="Coleta os repositórios Java mais populares do GitHub."
    )
    collect_parser.add_argument("--total", type=int, default=DEFAULT_TOTAL_REPOS)
    collect_parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    collect_parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "repositorios.csv",
    )

    measure_parser = subparsers.add_parser(
        "measure-one-repo",
        help="Clona 1 repositório, executa o CK e gera o CSV resumido das métricas.",
    )
    measure_parser.add_argument(
        "--repo-url",
        required=True,
        help="URL do repositório GitHub a ser clonado e analisado.",
    )
    measure_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    measure_parser.add_argument("--workspace-dir", type=Path, default=DEFAULT_WORKSPACE_DIR)
    measure_parser.add_argument("--ck-dir", type=Path, default=DEFAULT_CK_DIR)
    measure_parser.add_argument("--force-rebuild-ck", action="store_true")

    full_parser = subparsers.add_parser(
        "sprint1",
        help="Executa a entrega completa da Sprint 1: coleta os repositórios e mede 1 repositório com CK.",
    )
    full_parser.add_argument("--total", type=int, default=DEFAULT_TOTAL_REPOS)
    full_parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    full_parser.add_argument(
        "--repos-output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR / "repositorios.csv",
    )
    full_parser.add_argument(
        "--repo-url",
        required=True,
        help="URL do repositório que será usado como evidência da coleta com CK.",
    )
    full_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    full_parser.add_argument("--workspace-dir", type=Path, default=DEFAULT_WORKSPACE_DIR)
    full_parser.add_argument("--ck-dir", type=Path, default=DEFAULT_CK_DIR)
    full_parser.add_argument("--force-rebuild-ck", action="store_true")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.command:
        print("Use um dos comandos: collect-repos, measure-one-repo ou sprint1.")
        sys.exit(1)

    try:
        if args.command == "collect-repos":
            print("=" * 70)
            print(" Sprint 1 - Coleta dos repositórios Java")
            print("=" * 70)
            repositories = fetch_repositories(total_repos=args.total, page_size=args.page_size)
            processed = process_repositories(repositories)
            save_csv(processed, args.output)
            return

        if args.command == "measure-one-repo":
            measure_one_repository(
                repo_url=args.repo_url,
                output_dir=args.output_dir,
                workspace_dir=args.workspace_dir,
                ck_repo_dir=args.ck_dir,
                force_rebuild_ck=args.force_rebuild_ck,
            )
            return

        if args.command == "sprint1":
            print("=" * 70)
            print(" Sprint 1 completa")
            print("=" * 70)
            repositories = fetch_repositories(total_repos=args.total, page_size=args.page_size)
            processed = process_repositories(repositories)
            save_csv(processed, args.repos_output)
            measure_one_repository(
                repo_url=args.repo_url,
                output_dir=args.output_dir,
                workspace_dir=args.workspace_dir,
                ck_repo_dir=args.ck_dir,
                force_rebuild_ck=args.force_rebuild_ck,
            )
            return

        raise RuntimeError(f"Comando não suportado: {args.command}")

    except subprocess.CalledProcessError as exc:
        print(f"\n❌ ERRO ao executar comando externo: {exc}")
        sys.exit(exc.returncode or 1)
    except Exception as exc:
        print(f"\n❌ ERRO: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
