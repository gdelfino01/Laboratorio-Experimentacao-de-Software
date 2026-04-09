import csv
import os
import shutil
import stat
import sys
import statistics
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .io_utils import run_subprocess, sanitize_repo_name


FINAL_METRICS_FIELDNAMES = [
    "rank",
    "nameWithOwner",
    "url",
    "stars",
    "forks",
    "watchers",
    "releases",
    "created_at",
    "age_years",
    "repository",
    "class_csv",
    "classes_analyzed",
    "repo_loc",
    "repo_comment_lines",
    "repo_comment_density",
    "cbo_mean",
    "cbo_median",
    "cbo_stdev",
    "cbo_min",
    "cbo_max",
    "dit_mean",
    "dit_median",
    "dit_stdev",
    "dit_min",
    "dit_max",
    "lcom_mean",
    "lcom_median",
    "lcom_stdev",
    "lcom_min",
    "lcom_max",
    "loc_mean",
    "loc_median",
    "loc_stdev",
    "loc_min",
    "loc_max",
    "status",
    "error",
]


def resolve_maven_command(ck_repo_dir: Path) -> List[str]:
    env_maven = os.getenv("MAVEN_CMD", "").strip()
    if env_maven:
        return [env_maven]

    mvnw_cmd = ck_repo_dir / "mvnw.cmd"
    mvnw_sh = ck_repo_dir / "mvnw"

    if sys.platform == "win32" and mvnw_cmd.exists():
        return [str(mvnw_cmd)]

    if mvnw_sh.exists():
        return [str(mvnw_sh)]

    return ["mvn"]


def _on_rm_error(func: Any, path: str, exc_info: Any) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clone_repository(repo_url: str, destination: Path, refresh: bool = True) -> Path:
    if destination.exists() and refresh:
        try:
            shutil.rmtree(destination, onerror=_on_rm_error)
        except Exception as exc:
            print(
                f" Aviso: não foi possível limpar '{destination}'. "
                f"Reutilizando clone existente. Detalhe: {exc}"
            )
            return destination

    if destination.exists():
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    clone_command = ["git", "clone", "--depth", "1"]
    if sys.platform == "win32":
        clone_command.extend(["-c", "core.longpaths=true"])
    clone_command.extend([repo_url, str(destination)])
    run_subprocess(clone_command)
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

    maven_command = resolve_maven_command(ck_repo_dir)
    run_subprocess(
        [*maven_command, "clean", "compile", "package", "-DskipTests"],
        cwd=ck_repo_dir,
    )

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


def run_ck(
    ck_jar: Path,
    project_dir: Path,
    output_dir: Path,
    use_jars: bool = False,
    variables_and_fields: bool = False,
) -> None:
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


def _is_java_source(file_path: Path) -> bool:
    return file_path.is_file() and file_path.suffix.lower() == ".java"


def count_java_loc_and_comments(project_dir: Path) -> Dict[str, int]:
    total_loc = 0
    total_comment_lines = 0
    in_block_comment = False

    for file_path in project_dir.rglob("*.java"):
        if not _is_java_source(file_path):
            continue

        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as source_file:
                for line in source_file:
                    stripped = line.strip()
                    if not stripped:
                        continue

                    if in_block_comment:
                        total_comment_lines += 1
                        if "*/" in stripped:
                            in_block_comment = False
                        continue

                    if stripped.startswith("//"):
                        total_comment_lines += 1
                        continue

                    if stripped.startswith("/*"):
                        total_comment_lines += 1
                        if "*/" not in stripped:
                            in_block_comment = True
                        continue

                    if "/*" in stripped:
                        total_loc += 1
                        total_comment_lines += 1
                        if "*/" not in stripped.split("/*", 1)[1]:
                            in_block_comment = True
                        continue

                    total_loc += 1
        except OSError:
            # Ignora arquivos que não puderem ser lidos para não interromper o lote.
            continue

    return {
        "repo_loc": total_loc,
        "repo_comment_lines": total_comment_lines,
    }


def append_csv_row(file_path: Path, row: Dict[str, Any], fieldnames: List[str]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = file_path.exists()

    prepared_row = {field: row.get(field, "") for field in fieldnames}

    with file_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(prepared_row)


def load_processed_repositories(final_csv_path: Path) -> set[str]:
    if not final_csv_path.exists():
        return set()

    processed: set[str] = set()
    with final_csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = (row.get("nameWithOwner") or "").strip()
            status = (row.get("status") or "").strip().lower()
            if name and status == "success":
                processed.add(name)
    return processed


def safe_float(value: Any) -> Optional[float]:
    parsed = to_float(value)
    return None if parsed is None else float(parsed)


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


def summarize_ck_metrics(
    class_csv_path: Path,
    repository_name: str,
    summary_output_path: Path,
) -> Dict[str, Any]:
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
    sprint_evidence_output_path = output_dir / "medicao_1_repositorio.csv"

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

    with sprint_evidence_output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    print(f" Evidência da sprint salva em '{sprint_evidence_output_path}'")

    print("\n Resultado resumido:")
    for key, value in summary.items():
        print(f" - {key}: {value}")

    return summary


def measure_all_repositories(
    repos_csv_path: Path,
    output_dir: Path,
    workspace_dir: Path,
    ck_repo_dir: Path,
    force_rebuild_ck: bool = False,
    limit: Optional[int] = None,
    resume: bool = True,
    refresh_clone: bool = False,
) -> Dict[str, Any]:
    if not repos_csv_path.exists():
        raise FileNotFoundError(f"Arquivo de repositórios não encontrado: {repos_csv_path}")

    final_csv_path = output_dir / "repo_metrics_1000.csv"
    failures_csv_path = output_dir / "repo_failures.csv"

    processed_repositories = load_processed_repositories(final_csv_path) if resume else set()

    with repos_csv_path.open("r", newline="", encoding="utf-8") as repos_file:
        reader = csv.DictReader(repos_file)
        repositories = list(reader)

    if limit is not None and limit > 0:
        repositories = repositories[:limit]

    ck_jar = ensure_ck_jar(ck_repo_dir=ck_repo_dir, force_rebuild=force_rebuild_ck)

    success_count = 0
    failed_count = 0
    skipped_count = 0

    for index, repo_row in enumerate(repositories, start=1):
        name_with_owner = (repo_row.get("nameWithOwner") or "").strip()
        repo_url = (repo_row.get("url") or "").strip()

        if not name_with_owner or not repo_url:
            failed_count += 1
            failure_row = {
                "nameWithOwner": name_with_owner,
                "url": repo_url,
                "status": "failed",
                "error": "Linha inválida no CSV de repositórios.",
            }
            append_csv_row(
                failures_csv_path,
                failure_row,
                ["nameWithOwner", "url", "status", "error"],
            )
            continue

        if name_with_owner in processed_repositories:
            skipped_count += 1
            print(f"[{index}/{len(repositories)}] Pulando {name_with_owner} (já processado).")
            continue

        print(f"[{index}/{len(repositories)}] Processando {name_with_owner}...")

        repo_slug = sanitize_repo_name(name_with_owner)
        cloned_repo_dir = workspace_dir / repo_slug
        repo_output_dir = output_dir / repo_slug
        ck_output_dir = repo_output_dir / "ck_raw"
        summary_output_path = repo_output_dir / "repo_metrics_summary.csv"

        base_row: Dict[str, Any] = {
            "rank": repo_row.get("rank", ""),
            "nameWithOwner": name_with_owner,
            "url": repo_url,
            "stars": repo_row.get("stars", ""),
            "forks": repo_row.get("forks", ""),
            "watchers": repo_row.get("watchers", ""),
            "releases": repo_row.get("releases", ""),
            "created_at": repo_row.get("created_at", ""),
            "age_years": repo_row.get("age_years", ""),
            "status": "failed",
            "error": "",
        }

        try:
            clone_repository(
                repo_url=repo_url,
                destination=cloned_repo_dir,
                refresh=refresh_clone,
            )

            size_metrics = count_java_loc_and_comments(cloned_repo_dir)
            repo_loc = size_metrics["repo_loc"]
            repo_comment_lines = size_metrics["repo_comment_lines"]
            total_lines = repo_loc + repo_comment_lines
            repo_comment_density = round(repo_comment_lines / total_lines, 6) if total_lines > 0 else 0.0

            run_ck(ck_jar=ck_jar, project_dir=cloned_repo_dir, output_dir=ck_output_dir)

            class_csv_path = find_ck_class_csv(ck_output_dir)
            summary = summarize_ck_metrics(
                class_csv_path=class_csv_path,
                repository_name=name_with_owner,
                summary_output_path=summary_output_path,
            )

            result_row = {
                **base_row,
                **summary,
                "repo_loc": repo_loc,
                "repo_comment_lines": repo_comment_lines,
                "repo_comment_density": repo_comment_density,
                "status": "success",
                "error": "",
            }
            append_csv_row(final_csv_path, result_row, FINAL_METRICS_FIELDNAMES)
            success_count += 1

        except Exception as exc:
            error_message = str(exc)
            result_row = {
                **base_row,
                "repo_loc": "",
                "repo_comment_lines": "",
                "repo_comment_density": "",
                "repository": name_with_owner,
                "class_csv": "",
                "classes_analyzed": "",
                "status": "failed",
                "error": error_message,
            }
            append_csv_row(final_csv_path, result_row, FINAL_METRICS_FIELDNAMES)
            append_csv_row(
                failures_csv_path,
                {
                    "nameWithOwner": name_with_owner,
                    "url": repo_url,
                    "status": "failed",
                    "error": error_message,
                },
                ["nameWithOwner", "url", "status", "error"],
            )
            failed_count += 1
            print(f"   Falha em {name_with_owner}: {error_message}")

    summary_result = {
        "total_input": len(repositories),
        "success": success_count,
        "failed": failed_count,
        "skipped": skipped_count,
        "final_csv": str(final_csv_path),
        "failures_csv": str(failures_csv_path),
    }

    print("\nResumo da execução em lote:")
    for key, value in summary_result.items():
        print(f" - {key}: {value}")

    return summary_result
