import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .config import SUMMARY_FIELDS
from .io_utils import save_csv

NUMERIC_METRICS = [
    "changed_files",
    "additions",
    "deletions",
    "total_lines_changed",
    "analysis_time_hours",
    "description_length",
    "participants_count",
    "comments_count",
    "reviews_count",
]

METRIC_LABELS = {
    "changed_files": "Arquivos alterados",
    "additions": "Linhas adicionadas",
    "deletions": "Linhas removidas",
    "total_lines_changed": "Total de linhas modificadas",
    "analysis_time_hours": "Tempo de analise (horas)",
    "description_length": "Tamanho da descricao (caracteres)",
    "participants_count": "Participantes",
    "comments_count": "Comentarios",
    "reviews_count": "Numero de revisoes",
}


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
    if not rows:
        return "_Sem dados para esta secao._"

    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(value) for value in row) + " |")

    return "\n".join([header_line, separator_line, *body])


def _collect_metric_values(rows: Iterable[Dict[str, Any]], metric: str) -> List[float]:
    values: List[float] = []
    for row in rows:
        values.append(_to_float(row.get(metric)))
    return values


def _stats(values: List[float]) -> Dict[str, Any]:
    if not values:
        return {
            "count": 0,
            "median": None,
            "mean": None,
            "min": None,
            "max": None,
        }

    return {
        "count": float(len(values)),
        "median": float(statistics.median(values)),
        "mean": float(statistics.mean(values)),
        "min": float(min(values)),
        "max": float(max(values)),
    }


def build_summary_rows(dataset_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    summary_rows: List[Dict[str, Any]] = []

    groups = {
        "all": dataset_rows,
        "merged": [row for row in dataset_rows if str(row.get("pr_state", "")).upper() == "MERGED"],
        "closed": [row for row in dataset_rows if str(row.get("pr_state", "")).upper() == "CLOSED"],
    }

    for group_name, group_rows in groups.items():
        for metric in NUMERIC_METRICS:
            values = _collect_metric_values(group_rows, metric)
            stats = _stats(values)
            summary_rows.append(
                {
                    "group": group_name,
                    "metric": metric,
                    "count": int(stats["count"]),
                    "median": _round_or_none(stats["median"], 3),
                    "mean": _round_or_none(stats["mean"], 3),
                    "min": _round_or_none(stats["min"], 3),
                    "max": _round_or_none(stats["max"], 3),
                }
            )

    return summary_rows


def _summary_lookup(summary_rows: List[Dict[str, Any]], group: str, metric: str, field: str) -> str:
    for row in summary_rows:
        if row.get("group") == group and row.get("metric") == metric:
            value = row.get(field)
            if value is None:
                return "N/A"
            return str(value)
    return "N/A"


def _round_or_none(value: Any, digits: int = 3) -> Any:
    if value is None:
        return None
    return round(float(value), digits)


def generate_draft_report(
    dataset_rows: List[Dict[str, Any]],
    selected_repositories: List[Dict[str, Any]],
    summary_csv_path: Path,
    report_output_path: Path,
) -> Path:
    summary_rows = build_summary_rows(dataset_rows)
    save_csv(summary_rows, summary_csv_path, SUMMARY_FIELDS)

    total_repos = len(selected_repositories)
    total_prs = len(dataset_rows)
    merged_count = len([r for r in dataset_rows if str(r.get("pr_state", "")).upper() == "MERGED"])
    closed_count = len([r for r in dataset_rows if str(r.get("pr_state", "")).upper() == "CLOSED"])

    median_rows = []
    for metric in NUMERIC_METRICS:
        median_rows.append(
            [
                METRIC_LABELS.get(metric, metric),
                _summary_lookup(summary_rows, "all", metric, "median"),
                _summary_lookup(summary_rows, "merged", metric, "median"),
                _summary_lookup(summary_rows, "closed", metric, "median"),
            ]
        )

    report_lines = [
        "# Relatorio Parcial - Lab03S02: Caracterizando a Atividade de Code Review no GitHub",
        "",
        "Data de geracao: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "",
        "## 1. Introducao",
        "",
        "A pratica de code review no GitHub acontece principalmente via avaliacao de Pull Requests (PRs).",
        "Este relatorio parcial apresenta as hipoteses iniciais e um resumo descritivo do dataset coletado.",
        "",
        "## 2. Hipoteses Iniciais",
        "",
        "- H1 (RQ01): PRs maiores tendem a ter menor taxa de merge.",
        "- H2 (RQ02): PRs com maior tempo de analise tendem a terminar mais em CLOSED do que MERGED.",
        "- H3 (RQ03): PRs com descricao mais detalhada tendem a ter maior taxa de merge.",
        "- H4 (RQ04): PRs com mais interacoes tendem a ter maior probabilidade de CLOSED.",
        "- H5 (RQ05): PRs maiores tendem a receber mais revisoes.",
        "- H6 (RQ06): PRs com maior tempo de analise tendem a receber mais revisoes.",
        "- H7 (RQ07): PRs com descricao maior tendem a receber mais revisoes.",
        "- H8 (RQ08): PRs com mais interacoes tendem a receber mais revisoes.",
        "",
        "## 3. Metodologia (Sprint 2)",
        "",
        "Selecao de repositorios:",
        "- Top repositorios populares por estrelas no GitHub.",
        "- Minimo de 100 PRs (MERGED + CLOSED) por repositorio.",
        "- Alvo de 200 repositorios.",
        "",
        "Filtros de PR:",
        "- Estado MERGED ou CLOSED.",
        "- Pelo menos 1 review.",
        "- Tempo entre criacao e atividade final maior que 1 hora.",
        "",
        "Metricas por PR:",
        "- Tamanho: arquivos alterados, linhas adicionadas e removidas.",
        "- Tempo de analise: horas ate merge/close.",
        "- Descricao: numero de caracteres no corpo do PR.",
        "- Interacoes: participantes e comentarios.",
        "- Numero de revisoes.",
        "",
        "## 4. Cobertura do Dataset",
        "",
        f"- Repositorios selecionados: {total_repos}",
        f"- PRs no dataset final: {total_prs}",
        f"- PRs MERGED: {merged_count}",
        f"- PRs CLOSED: {closed_count}",
        "",
        "## 5. Sumarizacao Descritiva (Medianas)",
        "",
        _markdown_table(
            ["Metrica", "Mediana (todos PRs)", "Mediana (MERGED)", "Mediana (CLOSED)"],
            median_rows,
        ),
        "",
        "## 6. Proximos Passos",
        "",
        "Na Sprint 3 serao executadas as analises estatisticas (correlacao Spearman/Pearson),",
        "visualizacoes e discussao completa para responder formalmente as RQs.",
    ]

    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Saved report draft: {report_output_path}")

    return report_output_path
