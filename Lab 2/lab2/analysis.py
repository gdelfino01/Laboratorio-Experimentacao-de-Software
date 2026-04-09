from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from scipy.stats import pearsonr, spearmanr


PROCESS_QUALITY_RELATIONS: List[Tuple[str, str, str]] = [
    ("RQ01", "stars", "Popularidade (estrelas)"),
    ("RQ02", "age_years", "Maturidade (idade em anos)"),
    ("RQ03", "releases", "Atividade (número de releases)"),
    ("RQ04_LOC", "repo_loc", "Tamanho (LOC do repositório)"),
    ("RQ04_COMMENTS", "repo_comment_lines", "Tamanho (linhas de comentários)"),
]

QUALITY_COLUMNS = ["cbo_mean", "dit_mean", "lcom_mean"]
CORRELATION_COLUMNS = [
    "rq",
    "process_metric",
    "process_label",
    "quality_metric",
    "n",
    "spearman_corr",
    "spearman_pvalue",
    "pearson_corr",
    "pearson_pvalue",
]
DESCRIPTIVE_COLUMNS = [
    "stars",
    "age_years",
    "releases",
    "repo_loc",
    "repo_comment_lines",
    "cbo_mean",
    "dit_mean",
    "lcom_mean",
]


def _coerce_numeric_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    parsed = df.copy()
    for column in columns:
        if column in parsed.columns:
            parsed[column] = pd.to_numeric(parsed[column], errors="coerce")
    return parsed


def _compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []

    for rq, process_col, process_label in PROCESS_QUALITY_RELATIONS:
        if process_col not in df.columns:
            continue

        for quality_col in QUALITY_COLUMNS:
            if quality_col not in df.columns:
                continue

            pair = df[[process_col, quality_col]].dropna()
            n = len(pair)
            if n < 3:
                rows.append(
                    {
                        "rq": rq,
                        "process_metric": process_col,
                        "process_label": process_label,
                        "quality_metric": quality_col,
                        "n": n,
                        "spearman_corr": None,
                        "spearman_pvalue": None,
                        "pearson_corr": None,
                        "pearson_pvalue": None,
                    }
                )
                continue

            spearman_corr, spearman_pvalue = spearmanr(pair[process_col], pair[quality_col])
            pearson_corr, pearson_pvalue = pearsonr(pair[process_col], pair[quality_col])

            rows.append(
                {
                    "rq": rq,
                    "process_metric": process_col,
                    "process_label": process_label,
                    "quality_metric": quality_col,
                    "n": n,
                    "spearman_corr": round(float(spearman_corr), 6),
                    "spearman_pvalue": round(float(spearman_pvalue), 6),
                    "pearson_corr": round(float(pearson_corr), 6),
                    "pearson_pvalue": round(float(pearson_pvalue), 6),
                }
            )

    if not rows:
        return pd.DataFrame(columns=CORRELATION_COLUMNS)
    return pd.DataFrame(rows, columns=CORRELATION_COLUMNS)


def _compute_descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, object]] = []

    for column in DESCRIPTIVE_COLUMNS:
        if column not in df.columns:
            continue

        series = pd.to_numeric(df[column], errors="coerce").dropna()
        if series.empty:
            continue

        rows.append(
            {
                "metric": column,
                "n": int(series.count()),
                "mean": round(float(series.mean()), 6),
                "median": round(float(series.median()), 6),
                "stdev": round(float(series.std(ddof=0)), 6),
                "min": round(float(series.min()), 6),
                "max": round(float(series.max()), 6),
            }
        )

    return pd.DataFrame(rows)


def _save_correlation_plots(df: pd.DataFrame, figures_dir: Path) -> None:
    sns.set_theme(style="whitegrid")
    figures_dir.mkdir(parents=True, exist_ok=True)

    for rq, process_col, process_label in PROCESS_QUALITY_RELATIONS:
        if process_col not in df.columns:
            continue

        for quality_col in QUALITY_COLUMNS:
            if quality_col not in df.columns:
                continue

            pair = df[[process_col, quality_col]].dropna()
            if len(pair) < 3:
                continue

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.scatterplot(data=pair, x=process_col, y=quality_col, alpha=0.5, s=35, ax=ax)
            sns.regplot(
                data=pair,
                x=process_col,
                y=quality_col,
                scatter=False,
                ci=None,
                line_kws={"color": "#d62728", "linewidth": 2},
                ax=ax,
            )

            ax.set_title(f"{rq}: {process_label} vs {quality_col}")
            ax.set_xlabel(process_label)
            ax.set_ylabel(quality_col)
            fig.tight_layout()

            output_file = figures_dir / f"{rq.lower()}_{process_col}_vs_{quality_col}.png"
            fig.savefig(output_file, dpi=150)
            plt.close(fig)

    heatmap_columns = [
        "stars",
        "age_years",
        "releases",
        "repo_loc",
        "repo_comment_lines",
        "cbo_mean",
        "dit_mean",
        "lcom_mean",
    ]
    available_columns = [column for column in heatmap_columns if column in df.columns]
    heatmap_df = df[available_columns].dropna()
    if len(heatmap_df) >= 2 and len(available_columns) >= 2:
        corr_matrix = heatmap_df.corr(method="spearman")
        if corr_matrix.isna().all().all():
            return
        fig, ax = plt.subplots(figsize=(11, 8))
        sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", center=0, ax=ax)
        ax.set_title("Matriz de correlação (Spearman)")
        fig.tight_layout()
        fig.savefig(figures_dir / "correlation_heatmap_spearman.png", dpi=150)
        plt.close(fig)


def analyze_dataset(
    dataset_csv_path: Path,
    output_dir: Path,
    figures_dir: Path | None = None,
) -> Dict[str, str]:
    if not dataset_csv_path.exists():
        raise FileNotFoundError(f"Dataset consolidado não encontrado: {dataset_csv_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    selected_figures_dir = figures_dir or (output_dir / "figures")

    raw_df = pd.read_csv(dataset_csv_path)
    filtered_df = raw_df.copy()
    if "status" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["status"].astype(str).str.lower() == "success"]

    numeric_columns = [
        "stars",
        "age_years",
        "releases",
        "repo_loc",
        "repo_comment_lines",
        "cbo_mean",
        "dit_mean",
        "lcom_mean",
    ]
    filtered_df = _coerce_numeric_columns(filtered_df, numeric_columns)

    descriptive_stats_df = _compute_descriptive_stats(filtered_df)
    correlations_df = _compute_correlations(filtered_df)

    descriptive_path = output_dir / "rq_summary_stats.csv"
    correlations_path = output_dir / "rq_correlations.csv"

    descriptive_stats_df.to_csv(descriptive_path, index=False)
    correlations_df.to_csv(correlations_path, index=False)

    _save_correlation_plots(filtered_df, selected_figures_dir)

    result = {
        "dataset": str(dataset_csv_path),
        "descriptive_stats": str(descriptive_path),
        "correlations": str(correlations_path),
        "figures_dir": str(selected_figures_dir),
        "rows_analyzed": str(len(filtered_df)),
    }

    print("Análise concluída:")
    for key, value in result.items():
        print(f" - {key}: {value}")

    return result