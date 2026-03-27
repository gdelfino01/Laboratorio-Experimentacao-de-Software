import argparse
import subprocess
import sys
from pathlib import Path

from .config import (
    DEFAULT_CK_DIR,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PAGE_SIZE,
    DEFAULT_TOTAL_REPOS,
    DEFAULT_WORKSPACE_DIR,
)
from .github_data import fetch_repositories, process_repositories
from .io_utils import save_csv
from .metrics import measure_one_repository


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
        default=Path("repositorios.csv"),
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
        default=Path("repositorios.csv"),
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


def run() -> None:
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
        print(f"\nERRO ao executar comando externo: {exc}")
        sys.exit(exc.returncode or 1)
    except Exception as exc:
        print(f"\nERRO: {exc}")
        sys.exit(1)
