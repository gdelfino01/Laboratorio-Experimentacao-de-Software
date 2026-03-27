import csv
import os
import shutil
import stat
import sys
import statistics
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .io_utils import run_subprocess, sanitize_repo_name


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
