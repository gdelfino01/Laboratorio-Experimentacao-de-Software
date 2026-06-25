"""Statistical analysis for the GraphQL vs REST experiment (Lab 05).

Reads the CSV produced by the experiment runner and performs:
  1. Descriptive statistics (mean, median, std, IQR, min, max)
  2. Normality test (Shapiro–Wilk)
  3. Paired hypothesis tests (Wilcoxon signed-rank) for RQ1 and RQ2
  4. Effect size (Cliff's δ)
  5. Chart generation (boxplots, barplots) saved to output/

Usage
-----
    py src/analysis.py                          # default CSV path
    py src/analysis.py --input output/other.csv # custom path
"""

from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # non-interactive backend — works without display

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

# ─── Paths ────────────────────────────────────────────────────────────────────
_LAB5_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_CSV = _LAB5_ROOT / "output" / "experiment_runs.csv"
OUTPUT_DIR = _LAB5_ROOT / "output"

ALPHA = 0.05  # significance level


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Descriptive statistics
# ═══════════════════════════════════════════════════════════════════════════════

def descriptive_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics per treatment for both metrics."""
    records = []
    for treatment in ["REST", "GRAPHQL"]:
        subset = df[df["treatment"] == treatment]
        for metric in ["response_time_ms", "response_bytes"]:
            values = subset[metric].dropna()
            q1, q3 = values.quantile(0.25), values.quantile(0.75)
            records.append({
                "treatment": treatment,
                "metric": metric,
                "n": len(values),
                "mean": round(values.mean(), 3),
                "median": round(values.median(), 3),
                "std": round(values.std(), 3),
                "min": round(values.min(), 3),
                "max": round(values.max(), 3),
                "Q1": round(q1, 3),
                "Q3": round(q3, 3),
                "IQR": round(q3 - q1, 3),
            })
    return pd.DataFrame(records)


def descriptive_per_query(df: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics per (query_id, treatment) pair."""
    records = []
    for qid in sorted(df["query_id"].unique()):
        for treatment in ["REST", "GRAPHQL"]:
            subset = df[(df["query_id"] == qid) & (df["treatment"] == treatment)]
            for metric in ["response_time_ms", "response_bytes"]:
                values = subset[metric].dropna()
                records.append({
                    "query_id": qid,
                    "treatment": treatment,
                    "metric": metric,
                    "n": len(values),
                    "mean": round(values.mean(), 3),
                    "median": round(values.median(), 3),
                    "std": round(values.std(), 3),
                })
    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Normality test (Shapiro–Wilk)
# ═══════════════════════════════════════════════════════════════════════════════

def normality_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Shapiro–Wilk normality test per (treatment, metric) group."""
    records = []
    for treatment in ["REST", "GRAPHQL"]:
        subset = df[df["treatment"] == treatment]
        for metric in ["response_time_ms", "response_bytes"]:
            values = subset[metric].dropna()
            if len(values) >= 3:
                stat, p = stats.shapiro(values)
            else:
                stat, p = float("nan"), float("nan")
            records.append({
                "treatment": treatment,
                "metric": metric,
                "shapiro_stat": round(stat, 6),
                "shapiro_p": round(p, 6),
                "normal_at_005": p > ALPHA if not np.isnan(p) else None,
            })
    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Paired hypothesis tests (Wilcoxon signed-rank)
# ═══════════════════════════════════════════════════════════════════════════════

def _paired_arrays(df: pd.DataFrame, metric: str, query_id: str | None = None):
    """Build paired REST/GraphQL arrays matched by (iteration, query_id)."""
    sub = df.copy()
    if query_id is not None:
        sub = sub[sub["query_id"] == query_id]

    rest = sub[sub["treatment"] == "REST"].set_index(["iteration", "query_id"])[metric]
    gql = sub[sub["treatment"] == "GRAPHQL"].set_index(["iteration", "query_id"])[metric]

    # Inner join ensures pairing
    joined = pd.DataFrame({"rest": rest, "graphql": gql}).dropna()
    return joined["rest"].values, joined["graphql"].values


def wilcoxon_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Run Wilcoxon signed-rank test for each metric (overall and per query)."""
    records = []

    for metric, rq in [("response_time_ms", "RQ1"), ("response_bytes", "RQ2")]:
        # ── Overall ──────────────────────────────────────────────────────
        rest_vals, gql_vals = _paired_arrays(df, metric)
        if len(rest_vals) >= 10:
            stat, p = stats.wilcoxon(rest_vals, gql_vals, alternative="two-sided")
        else:
            stat, p = float("nan"), float("nan")
        records.append({
            "rq": rq,
            "metric": metric,
            "scope": "overall",
            "n_pairs": len(rest_vals),
            "wilcoxon_stat": round(stat, 4),
            "p_value": round(p, 6),
            "reject_H0": p < ALPHA if not np.isnan(p) else None,
            "cliff_delta": round(_cliff_delta(rest_vals, gql_vals), 4),
            "effect_magnitude": _cliff_magnitude(_cliff_delta(rest_vals, gql_vals)),
        })

        # ── Per query ────────────────────────────────────────────────────
        for qid in sorted(df["query_id"].unique()):
            r, g = _paired_arrays(df, metric, query_id=qid)
            if len(r) >= 10:
                stat, p = stats.wilcoxon(r, g, alternative="two-sided")
            else:
                stat, p = float("nan"), float("nan")
            records.append({
                "rq": rq,
                "metric": metric,
                "scope": qid,
                "n_pairs": len(r),
                "wilcoxon_stat": round(stat, 4),
                "p_value": round(p, 6),
                "reject_H0": p < ALPHA if not np.isnan(p) else None,
                "cliff_delta": round(_cliff_delta(r, g), 4),
                "effect_magnitude": _cliff_magnitude(_cliff_delta(r, g)),
            })

    return pd.DataFrame(records)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Effect size — Cliff's δ
# ═══════════════════════════════════════════════════════════════════════════════

def _cliff_delta(x: np.ndarray, y: np.ndarray) -> float:
    """Compute Cliff's delta (non-parametric effect size).

    δ > 0 means values in x tend to be larger than in y.
    δ < 0 means values in x tend to be smaller.
    """
    if len(x) == 0 or len(y) == 0:
        return float("nan")
    n = len(x) * len(y)
    more = sum(1 for xi in x for yi in y if xi > yi)
    less = sum(1 for xi in x for yi in y if xi < yi)
    return (more - less) / n


def _cliff_magnitude(delta: float) -> str:
    """Classify Cliff's δ magnitude (Romano et al., 2006)."""
    if np.isnan(delta):
        return "N/A"
    d = abs(delta)
    if d < 0.147:
        return "negligible"
    elif d < 0.33:
        return "small"
    elif d < 0.474:
        return "medium"
    else:
        return "large"


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Chart generation
# ═══════════════════════════════════════════════════════════════════════════════

def _apply_style():
    """Apply a consistent, publication-quality style."""
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
    plt.rcParams.update({
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
    })


def plot_boxplots_overall(df: pd.DataFrame, output_dir: Path) -> None:
    """Side-by-side boxplots for response time and response size."""
    _apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # ── RQ1: Response Time ───────────────────────────────────────────────
    sns.boxplot(
        data=df, x="treatment", y="response_time_ms",
        order=["REST", "GRAPHQL"], palette=["#3b82f6", "#f97316"],
        ax=axes[0], width=0.5,
    )
    axes[0].set_title("RQ1 — Tempo de Resposta", fontweight="bold")
    axes[0].set_xlabel("Tratamento")
    axes[0].set_ylabel("Tempo de resposta (ms)")

    # ── RQ2: Response Size ───────────────────────────────────────────────
    sns.boxplot(
        data=df, x="treatment", y="response_bytes",
        order=["REST", "GRAPHQL"], palette=["#3b82f6", "#f97316"],
        ax=axes[1], width=0.5,
    )
    axes[1].set_title("RQ2 — Tamanho da Resposta", fontweight="bold")
    axes[1].set_xlabel("Tratamento")
    axes[1].set_ylabel("Tamanho da resposta (bytes)")

    fig.suptitle("GraphQL vs REST — Comparação Geral", fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    path = output_dir / "boxplots_overall.png"
    fig.savefig(path)
    plt.close(fig)
    print(f"  [chart] {path}")


def plot_boxplots_per_query(df: pd.DataFrame, output_dir: Path) -> None:
    """Boxplots faceted by query_id for both metrics."""
    _apply_style()

    for metric, title, ylabel, fname in [
        ("response_time_ms", "RQ1 — Tempo de Resposta por Query", "Tempo (ms)", "boxplots_time_per_query.png"),
        ("response_bytes", "RQ2 — Tamanho da Resposta por Query", "Tamanho (bytes)", "boxplots_size_per_query.png"),
    ]:
        queries = sorted(df["query_id"].unique())
        fig, axes = plt.subplots(1, len(queries), figsize=(4 * len(queries), 5), sharey=False)
        if len(queries) == 1:
            axes = [axes]

        for ax, qid in zip(axes, queries):
            subset = df[df["query_id"] == qid]
            label_text = subset["query_label"].iloc[0] if "query_label" in subset.columns else qid
            sns.boxplot(
                data=subset, x="treatment", y=metric,
                order=["REST", "GRAPHQL"], palette=["#3b82f6", "#f97316"],
                ax=ax, width=0.5,
            )
            ax.set_title(f"{qid}\n({label_text})", fontsize=10)
            ax.set_xlabel("")
            ax.set_ylabel(ylabel if ax == axes[0] else "")

        fig.suptitle(title, fontsize=13, fontweight="bold", y=1.02)
        fig.tight_layout()
        path = output_dir / fname
        fig.savefig(path)
        plt.close(fig)
        print(f"  [chart] {path}")


def plot_barplot_medians(df: pd.DataFrame, output_dir: Path) -> None:
    """Grouped barplots showing median values per query."""
    _apply_style()

    for metric, title, ylabel, fname in [
        ("response_time_ms", "Mediana do Tempo de Resposta por Query", "Tempo (ms)", "barplot_time_medians.png"),
        ("response_bytes", "Mediana do Tamanho da Resposta por Query", "Tamanho (bytes)", "barplot_size_medians.png"),
    ]:
        medians = (
            df.groupby(["query_id", "treatment"])[metric]
            .median()
            .reset_index()
            .rename(columns={metric: "median"})
        )
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(
            data=medians, x="query_id", y="median", hue="treatment",
            hue_order=["REST", "GRAPHQL"], palette=["#3b82f6", "#f97316"],
            ax=ax,
        )
        ax.set_title(title, fontweight="bold")
        ax.set_xlabel("Query")
        ax.set_ylabel(ylabel)
        ax.legend(title="Tratamento")
        fig.tight_layout()
        path = output_dir / fname
        fig.savefig(path)
        plt.close(fig)
        print(f"  [chart] {path}")


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Console report
# ═══════════════════════════════════════════════════════════════════════════════

def print_report(
    desc: pd.DataFrame,
    desc_q: pd.DataFrame,
    normality: pd.DataFrame,
    tests: pd.DataFrame,
) -> None:
    """Print a nicely formatted console summary."""
    sep = "=" * 72

    print(f"\n{sep}")
    print("  ANALISE ESTATISTICA - GraphQL vs REST (Lab 05)")
    print(sep)

    # ── Descriptive ──────────────────────────────────────────────────────
    print("\n-- 1. Estatisticas Descritivas (Geral) --\n")
    print(desc.to_string(index=False))

    print("\n-- 2. Estatisticas Descritivas (Por Query) --\n")
    print(desc_q.to_string(index=False))

    # ── Normality ────────────────────────────────────────────────────────
    print("\n-- 3. Teste de Normalidade (Shapiro-Wilk) --\n")
    print(normality.to_string(index=False))

    # ── Hypothesis tests ─────────────────────────────────────────────────
    print("\n-- 4. Testes de Hipotese (Wilcoxon Signed-Rank) --\n")
    print(tests.to_string(index=False))

    # ── Verdict ──────────────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  CONCLUSOES (alpha = 0.05)")
    print(sep)

    overall = tests[tests["scope"] == "overall"]
    for _, row in overall.iterrows():
        rq = row["rq"]
        p = row["p_value"]
        reject = row["reject_H0"]
        delta = row["cliff_delta"]
        mag = row["effect_magnitude"]
        decision = "REJEITADA" if reject else "NAO rejeitada"
        print(
            f"\n  {rq} ({row['metric']}): "
            f"p = {p:.6f} -> H0 {decision}"
        )
        print(f"     Cliff's delta = {delta:.4f} ({mag})")

    print(f"\n{sep}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Export summary tables as CSV
# ═══════════════════════════════════════════════════════════════════════════════

def export_tables(
    desc: pd.DataFrame,
    desc_q: pd.DataFrame,
    normality: pd.DataFrame,
    tests: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Persist analysis tables as CSVs for use in the report."""
    desc.to_csv(output_dir / "stats_descriptive.csv", index=False)
    desc_q.to_csv(output_dir / "stats_descriptive_per_query.csv", index=False)
    normality.to_csv(output_dir / "stats_normality.csv", index=False)
    tests.to_csv(output_dir / "stats_hypothesis_tests.csv", index=False)
    print(f"  [csv] tables saved to {output_dir}/stats_*.csv")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyse experiment results.")
    parser.add_argument(
        "--input", type=Path, default=DEFAULT_INPUT_CSV,
        help="Path to the experiment CSV (default: %(default)s).",
    )
    args = parser.parse_args(argv)

    csv_path: Path = args.input
    if not csv_path.exists():
        print(
            f"error: CSV not found at {csv_path}\n"
            f"Run the experiment first: py src/main.py --repetitions 30 --warmup 3",
            file=sys.stderr,
        )
        return 1

    # ── Load & validate ──────────────────────────────────────────────────
    df = pd.read_csv(csv_path)
    required_cols = {"iteration", "query_id", "treatment", "response_time_ms", "response_bytes"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"error: CSV missing columns: {missing}", file=sys.stderr)
        return 1

    # Filter out errors
    df = df[df["status_code"] == 200].copy()
    df["response_time_ms"] = pd.to_numeric(df["response_time_ms"], errors="coerce")
    df["response_bytes"] = pd.to_numeric(df["response_bytes"], errors="coerce")

    print(f"Loaded {len(df)} valid measurements from {csv_path}")
    print(f"Queries: {sorted(df['query_id'].unique())}")
    print(f"Treatments: {sorted(df['treatment'].unique())}")
    print(f"Iterations: {df['iteration'].nunique()}")

    # ── Analysis ─────────────────────────────────────────────────────────
    desc = descriptive_stats(df)
    desc_q = descriptive_per_query(df)
    normality = normality_tests(df)
    tests = wilcoxon_tests(df)

    # ── Output ───────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print_report(desc, desc_q, normality, tests)
    export_tables(desc, desc_q, normality, tests, OUTPUT_DIR)

    print("\nGenerating charts...")
    plot_boxplots_overall(df, OUTPUT_DIR)
    plot_boxplots_per_query(df, OUTPUT_DIR)
    plot_barplot_medians(df, OUTPUT_DIR)

    print("\n[OK] Analysis complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
