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
from .analysis import analyze_dataset
from .github_data import fetch_repositories, process_repositories
from .io_utils import save_csv
from .metrics import measure_all_repositories, measure_one_repository
from .report import generate_final_report


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

    batch_parser = subparsers.add_parser(
        "measure-all-repos",
        help="Executa medição em lote com CK para os repositórios do CSV de entrada.",
    )
    batch_parser.add_argument(
        "--repos-csv",
        type=Path,
        default=Path("repositorios.csv"),
        help="CSV com os 1000 repositórios coletados.",
    )
    batch_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    batch_parser.add_argument("--workspace-dir", type=Path, default=DEFAULT_WORKSPACE_DIR)
    batch_parser.add_argument("--ck-dir", type=Path, default=DEFAULT_CK_DIR)
    batch_parser.add_argument("--force-rebuild-ck", action="store_true")
    batch_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limita o número de repositórios processados (útil para testes).",
    )
    batch_parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Desabilita retomada por checkpoint.",
    )
    batch_parser.add_argument(
        "--refresh-clone",
        action="store_true",
        help="Remove clone antigo e clona novamente antes de medir.",
    )

    analyze_parser = subparsers.add_parser(
        "analyze-data",
        help="Executa análise estatística e gera visualizações das RQs.",
    )
    analyze_parser.add_argument(
        "--dataset-csv",
        type=Path,
        default=Path("output") / "repo_metrics_1000.csv",
    )
    analyze_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    analyze_parser.add_argument(
        "--figures-dir",
        type=Path,
        default=None,
        help="Diretório de saída dos gráficos (padrão: output/figures).",
    )

    report_parser = subparsers.add_parser(
        "generate-report",
        help="Gera o relatório final em Markdown com base nos CSVs de análise.",
    )
    report_parser.add_argument(
        "--dataset-csv",
        type=Path,
        default=Path("output") / "repo_metrics_1000.csv",
    )
    report_parser.add_argument(
        "--summary-csv",
        type=Path,
        default=Path("output") / "rq_summary_stats.csv",
    )
    report_parser.add_argument(
        "--correlations-csv",
        type=Path,
        default=Path("output") / "rq_correlations.csv",
    )
    report_parser.add_argument(
        "--output-report",
        type=Path,
        default=Path("RELATORIO_FINAL.md"),
    )

    all_parser = subparsers.add_parser(
        "run-all",
        help="Pipeline completo: coleta, medição em lote, análise e relatório final.",
    )
    all_parser.add_argument("--total", type=int, default=DEFAULT_TOTAL_REPOS)
    all_parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    all_parser.add_argument(
        "--repos-output",
        type=Path,
        default=Path("repositorios.csv"),
    )
    all_parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    all_parser.add_argument("--workspace-dir", type=Path, default=DEFAULT_WORKSPACE_DIR)
    all_parser.add_argument("--ck-dir", type=Path, default=DEFAULT_CK_DIR)
    all_parser.add_argument("--force-rebuild-ck", action="store_true")
    all_parser.add_argument("--limit", type=int, default=None)
    all_parser.add_argument("--no-resume", action="store_true")
    all_parser.add_argument("--refresh-clone", action="store_true")
    all_parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("RELATORIO_FINAL.md"),
    )

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

        if args.command == "measure-all-repos":
            measure_all_repositories(
                repos_csv_path=args.repos_csv,
                output_dir=args.output_dir,
                workspace_dir=args.workspace_dir,
                ck_repo_dir=args.ck_dir,
                force_rebuild_ck=args.force_rebuild_ck,
                limit=args.limit,
                resume=not args.no_resume,
                refresh_clone=args.refresh_clone,
            )
            return

        if args.command == "analyze-data":
            analyze_dataset(
                dataset_csv_path=args.dataset_csv,
                output_dir=args.output_dir,
                figures_dir=args.figures_dir,
            )
            return

        if args.command == "generate-report":
            generate_final_report(
                dataset_csv_path=args.dataset_csv,
                summary_stats_csv_path=args.summary_csv,
                correlations_csv_path=args.correlations_csv,
                report_output_path=args.output_report,
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

        if args.command == "run-all":
            print("=" * 70)
            print(" Pipeline completo do Lab 2")
            print("=" * 70)

            repositories = fetch_repositories(total_repos=args.total, page_size=args.page_size)
            processed = process_repositories(repositories)
            save_csv(processed, args.repos_output)

            measure_all_repositories(
                repos_csv_path=args.repos_output,
                output_dir=args.output_dir,
                workspace_dir=args.workspace_dir,
                ck_repo_dir=args.ck_dir,
                force_rebuild_ck=args.force_rebuild_ck,
                limit=args.limit,
                resume=not args.no_resume,
                refresh_clone=args.refresh_clone,
            )

            analyze_dataset(
                dataset_csv_path=args.output_dir / "repo_metrics_1000.csv",
                output_dir=args.output_dir,
                figures_dir=args.output_dir / "figures",
            )

            generate_final_report(
                dataset_csv_path=args.output_dir / "repo_metrics_1000.csv",
                summary_stats_csv_path=args.output_dir / "rq_summary_stats.csv",
                correlations_csv_path=args.output_dir / "rq_correlations.csv",
                report_output_path=args.report_path,
            )
            return

        raise RuntimeError(f"Comando não suportado: {args.command}")

    except subprocess.CalledProcessError as exc:
        print(f"\nERRO ao executar comando externo: {exc}")
        sys.exit(exc.returncode or 1)
    except Exception as exc:
        print(f"\nERRO: {exc}")
        sys.exit(1)
