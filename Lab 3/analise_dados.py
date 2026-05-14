"""
Script de análise de dados e gráficos - Lab 3
Executa: limpeza dos arquivos smoke, amostragem aleatória de 100 PRs,
análise estatística e geração de gráficos.
"""

import csv
import os
import random
import shutil
from pathlib import Path

# ─── Configurações de caminhos ───────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
RESULTADOS_DIR = BASE_DIR / "resultados"
GRAFICOS_DIR = RESULTADOS_DIR / "graficos"

PRS_CSV = RESULTADOS_DIR / "prs.csv"
REPOS_CSV = RESULTADOS_DIR / "repos.csv"
PRS_100_CSV = RESULTADOS_DIR / "prs_100.csv"

SEED = 42  # semente para reprodutibilidade

# ─── 1. Excluir arquivos smoke do output ────────────────────────────────────
def limpar_smoke():
    smoke_patterns = [
        "correlations_smoke.csv",
        "prs_smoke.csv",
        "selected_repos_smoke.csv",
        "summary_smoke.csv",
        "summary_sprint3_smoke.csv",
        "checkpoint_prs.txt",
        "figures_smoke",
    ]
    for name in smoke_patterns:
        path = OUTPUT_DIR / name
        if path.is_dir():
            shutil.rmtree(path)
            print(f"  [DEL dir] {path.name}")
        elif path.exists():
            path.unlink()
            print(f"  [DEL file] {path.name}")
    print("Limpeza dos arquivos smoke concluída.\n")

# ─── 2. Carregar todos os PRs ────────────────────────────────────────────────
def carregar_todos_prs():
    with open(PRS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    print(f"Total de PRs carregados para análise: {total}\n")

    fieldnames = list(rows[0].keys()) if rows else []
    
    # Podemos salvar um CSV apenas de "prs_analisados" se quisermos, mas o arquivo original tem tudo
    with open(PRS_100_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Arquivo salvo para referência de analisados: {PRS_100_CSV}\n")
    return rows, fieldnames

# ─── 3. Análise estatística ──────────────────────────────────────────────────
def _to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def _stats(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return {}
    vals_sorted = sorted(vals)
    n = len(vals_sorted)
    media = sum(vals_sorted) / n
    mediana = vals_sorted[n // 2] if n % 2 else (vals_sorted[n // 2 - 1] + vals_sorted[n // 2]) / 2
    return {
        "n": n,
        "media": round(media, 3),
        "mediana": round(mediana, 3),
        "min": round(min(vals_sorted), 3),
        "max": round(max(vals_sorted), 3),
    }

METRICAS = {
    "files_changed":       "Arquivos Alterados",
    "lines_added":         "Linhas Adicionadas",
    "lines_removed":       "Linhas Removidas",
    "analysis_time_hours": "Tempo de Análise (h)",
    "body_length":         "Tamanho da Descrição (chars)",
    "participants_count":  "Participantes",
    "comments_count":      "Comentários",
    "reviews_count":       "Revisões",
}

def analisar(sample):
    merged = [r for r in sample if r.get("status", "").upper() == "MERGED"]
    closed = [r for r in sample if r.get("status", "").upper() == "CLOSED"]

    print(f"{'='*60}")
    print(f"ANÁLISE DESCRITIVA - {len(sample)} PRs")
    print(f"  MERGED: {len(merged)}  |  CLOSED: {len(closed)}")
    print(f"{'='*60}\n")

    resultados = {}
    for col, label in METRICAS.items():
        all_vals  = [_to_float(r.get(col)) for r in sample]
        mrg_vals  = [_to_float(r.get(col)) for r in merged]
        cls_vals  = [_to_float(r.get(col)) for r in closed]
        resultados[col] = {
            "label": label,
            "all":    _stats(all_vals),
            "merged": _stats(mrg_vals),
            "closed": _stats(cls_vals),
        }
        s = resultados[col]["all"]
        print(f"  {label}")
        print(f"    Todos   -> mediana={s.get('mediana','N/A')}, media={s.get('media','N/A')}, "
              f"min={s.get('min','N/A')}, max={s.get('max','N/A')}")
        sm = resultados[col]["merged"]
        sc = resultados[col]["closed"]
        print(f"    MERGED  -> mediana={sm.get('mediana','N/A')}  |  CLOSED -> mediana={sc.get('mediana','N/A')}\n")

    return resultados, merged, closed

# ─── 4. Correlação de Spearman ──────────────────────────────────────────────
def spearman(x, y):
    """Calcula rho de Spearman sem scipy."""
    assert len(x) == len(y), "x e y devem ter o mesmo tamanho"
    n = len(x)
    if n < 3:
        return None, None

    def rank(lst):
        sorted_idx = sorted(range(n), key=lambda i: lst[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j < n - 1 and lst[sorted_idx[j + 1]] == lst[sorted_idx[j]]:
                j += 1
            avg_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[sorted_idx[k]] = avg_rank
            i = j + 1
        return r

    rx, ry = rank(x), rank(y)
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n
    num = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    den = (sum((rx[i] - mean_rx) ** 2 for i in range(n)) *
           sum((ry[i] - mean_ry) ** 2 for i in range(n))) ** 0.5
    rho = num / den if den else 0.0

    # aproximação t-student para p-value
    import math
    if abs(rho) >= 1.0:
        return round(rho, 4), 0.0
    t = rho * ((n - 2) ** 0.5) / ((1 - rho ** 2) ** 0.5)
    # p-value 2-caudas via regularized incomplete beta (aproximado)
    df = n - 2
    x_t = df / (df + t * t)
    # série de potências simples (aproximação suficiente para n>=10)
    def betainc_approx(a, b, x_val):
        if x_val <= 0:
            return 0.0
        if x_val >= 1:
            return 1.0
        result, term = x_val ** a * (1 - x_val) ** b / a, 1.0
        for k in range(1, 200):
            term *= x_val * (a + b + k - 1) / (a + k)
            result += term * x_val ** k / (a + k)
            if abs(term) < 1e-10:
                break
        return result

    p = 2 * betainc_approx(df / 2, 0.5, x_t)
    p = min(p, 1.0)
    return round(rho, 4), round(p, 4)


PARES_CORRELACAO = [
    # RQ01 – tamanho vs. status (1=merged, 0=closed)
    ("files_changed", "is_merged", "RQ01 – Arquivos Alterados × Status"),
    ("lines_added",   "is_merged", "RQ01 – Linhas Adicionadas × Status"),
    # RQ02 – tempo vs. status
    ("analysis_time_hours", "is_merged", "RQ02 – Tempo de Análise × Status"),
    # RQ03 – descrição vs. status
    ("body_length", "is_merged", "RQ03 – Tamanho da Descrição × Status"),
    # RQ04 – interações vs. status
    ("participants_count", "is_merged", "RQ04 – Participantes × Status"),
    ("comments_count",     "is_merged", "RQ04 – Comentários × Status"),
    # RQ05 – tamanho vs. revisões
    ("files_changed", "reviews_count", "RQ05 – Arquivos Alterados × Revisões"),
    ("lines_added",   "reviews_count", "RQ05 – Linhas Adicionadas × Revisões"),
    # RQ06 – tempo vs. revisões
    ("analysis_time_hours", "reviews_count", "RQ06 – Tempo de Análise × Revisões"),
    # RQ07 – descrição vs. revisões
    ("body_length", "reviews_count", "RQ07 – Tamanho da Descrição × Revisões"),
    # RQ08 – interações vs. revisões
    ("participants_count", "reviews_count", "RQ08 – Participantes × Revisões"),
    ("comments_count",     "reviews_count", "RQ08 – Comentários × Revisões"),
]

def calcular_correlacoes(sample):
    print(f"\n{'='*60}")
    print("CORRELAÇÕES DE SPEARMAN")
    print(f"{'='*60}")

    # adiciona coluna is_merged
    for r in sample:
        r["is_merged"] = 1.0 if r.get("status", "").upper() == "MERGED" else 0.0

    correlacoes = []
    for col_x, col_y, label in PARES_CORRELACAO:
        pairs = []
        for r in sample:
            vx = _to_float(r.get(col_x))
            vy = _to_float(r.get(col_y))
            if vx is not None and vy is not None:
                pairs.append((vx, vy))
        if len(pairs) < 5:
            print(f"  {label}: dados insuficientes ({len(pairs)} pares)")
            continue
        xs, ys = zip(*pairs)
        rho, pval = spearman(list(xs), list(ys))
        sig = "**" if pval is not None and pval < 0.05 else ""
        print(f"  {label}")
        print(f"    rho = {rho}   p = {pval} {sig}\n")
        correlacoes.append({
            "par": label,
            "x": col_x,
            "y": col_y,
            "n": len(pairs),
            "rho": rho,
            "p_value": pval,
            "significativo": "sim" if pval is not None and pval < 0.05 else "não",
        })

    # Salvar CSV de correlações
    corr_csv = RESULTADOS_DIR / "correlacoes.csv"
    if correlacoes:
        with open(corr_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(correlacoes[0].keys()))
            writer.writeheader()
            writer.writerows(correlacoes)
        print(f"  Correlações salvas em: {corr_csv}\n")

    return correlacoes

# ─── 5. Gráficos ─────────────────────────────────────────────────────────────
def gerar_graficos(sample, correlacoes):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
    except ImportError:
        print("matplotlib não instalado – pulando gráficos.")
        return

    GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "figure.dpi": 150,
        "font.family": "DejaVu Sans",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })

    cor_merged = "#2196F3"
    cor_closed = "#FF5722"

    merged = [r for r in sample if r.get("status", "").upper() == "MERGED"]
    closed = [r for r in sample if r.get("status", "").upper() == "CLOSED"]

    # ── G1: Distribuição MERGED vs CLOSED ────────────────────────────────────
    fig, ax = plt.subplots(figsize=(6, 5))
    counts = [len(merged), len(closed)]
    bars = ax.bar(["MERGED", "CLOSED"], counts,
                  color=[cor_merged, cor_closed], width=0.5, edgecolor="white")
    for bar, cnt in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, cnt + 0.5,
                str(cnt), ha="center", va="bottom", fontweight="bold")
    ax.set_title("Distribuição de PRs por Status", fontsize=13, pad=12)
    ax.set_ylabel("Quantidade de PRs")
    ax.set_ylim(0, max(counts) * 1.2)
    plt.tight_layout()
    plt.savefig(GRAFICOS_DIR / "g1_distribuicao_status.png")
    plt.close()
    print("  Gráfico salvo: g1_distribuicao_status.png")

    # ── G2: Boxplot – Arquivos Alterados por Status ──────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    data_m = [_to_float(r["files_changed"]) for r in merged if _to_float(r.get("files_changed")) is not None]
    data_c = [_to_float(r["files_changed"]) for r in closed if _to_float(r.get("files_changed")) is not None]
    bp = ax.boxplot([data_m, data_c], labels=["MERGED", "CLOSED"],
                    patch_artist=True, showfliers=True, widths=0.5)
    for patch, color in zip(bp["boxes"], [cor_merged, cor_closed]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_title("Arquivos Alterados por Status (RQ01)", fontsize=13, pad=12)
    ax.set_ylabel("Nº de arquivos alterados")
    plt.tight_layout()
    plt.savefig(GRAFICOS_DIR / "g2_boxplot_files_status.png")
    plt.close()
    print("  Gráfico salvo: g2_boxplot_files_status.png")

    # ── G3: Boxplot – Tempo de Análise por Status ────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    data_m = [_to_float(r["analysis_time_hours"]) for r in merged if _to_float(r.get("analysis_time_hours")) is not None]
    data_c = [_to_float(r["analysis_time_hours"]) for r in closed if _to_float(r.get("analysis_time_hours")) is not None]
    bp = ax.boxplot([data_m, data_c], labels=["MERGED", "CLOSED"],
                    patch_artist=True, showfliers=True, widths=0.5)
    for patch, color in zip(bp["boxes"], [cor_merged, cor_closed]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_title("Tempo de Análise por Status (RQ02)", fontsize=13, pad=12)
    ax.set_ylabel("Horas até merge/close")
    plt.tight_layout()
    plt.savefig(GRAFICOS_DIR / "g3_boxplot_tempo_status.png")
    plt.close()
    print("  Gráfico salvo: g3_boxplot_tempo_status.png")

    # ── G4: Boxplot – Tamanho da Descrição por Status ────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    data_m = [_to_float(r["body_length"]) for r in merged if _to_float(r.get("body_length")) is not None]
    data_c = [_to_float(r["body_length"]) for r in closed if _to_float(r.get("body_length")) is not None]
    bp = ax.boxplot([data_m, data_c], labels=["MERGED", "CLOSED"],
                    patch_artist=True, showfliers=True, widths=0.5)
    for patch, color in zip(bp["boxes"], [cor_merged, cor_closed]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_title("Tamanho da Descrição por Status (RQ03)", fontsize=13, pad=12)
    ax.set_ylabel("Caracteres no corpo do PR")
    plt.tight_layout()
    plt.savefig(GRAFICOS_DIR / "g4_boxplot_descricao_status.png")
    plt.close()
    print("  Gráfico salvo: g4_boxplot_descricao_status.png")

    # ── G5: Boxplot – Interações (comentários) por Status ────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    data_m = [_to_float(r["comments_count"]) for r in merged if _to_float(r.get("comments_count")) is not None]
    data_c = [_to_float(r["comments_count"]) for r in closed if _to_float(r.get("comments_count")) is not None]
    bp = ax.boxplot([data_m, data_c], labels=["MERGED", "CLOSED"],
                    patch_artist=True, showfliers=True, widths=0.5)
    for patch, color in zip(bp["boxes"], [cor_merged, cor_closed]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax.set_title("Comentários por Status (RQ04)", fontsize=13, pad=12)
    ax.set_ylabel("Nº de comentários")
    plt.tight_layout()
    plt.savefig(GRAFICOS_DIR / "g5_boxplot_comentarios_status.png")
    plt.close()
    print("  Gráfico salvo: g5_boxplot_comentarios_status.png")

    # ── G6: Scatter – Arquivos Alterados vs Revisões ─────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    # build color list by index (dicts not hashable)
    colors_list = [cor_merged if r.get("status", "").upper() == "MERGED" else cor_closed for r in sample]
    legend_patches = [mpatches.Patch(color=cor_merged, label="MERGED"),
                      mpatches.Patch(color=cor_closed, label="CLOSED")]

    xs = [_to_float(r.get("files_changed")) for r in sample]
    ys = [_to_float(r.get("reviews_count")) for r in sample]
    valid = [(x, y, c) for x, y, c in zip(xs, ys, colors_list) if x is not None and y is not None]
    if valid:
        vx, vy, vc = zip(*valid)
        ax.scatter(vx, vy, c=list(vc), alpha=0.6, edgecolors="white", linewidths=0.5, s=60)
    ax.set_title("Arquivos Alterados x Revisoes (RQ05)", fontsize=13, pad=12)
    ax.set_xlabel("No de arquivos alterados")
    ax.set_ylabel("No de revisoes")
    ax.legend(handles=legend_patches, loc="upper right")
    plt.tight_layout()
    plt.savefig(GRAFICOS_DIR / "g6_scatter_files_revisoes.png")
    plt.close()
    print("  Grafico salvo: g6_scatter_files_revisoes.png")

    # ── G7: Scatter – Tempo de Análise vs Revisões ───────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    xs = [_to_float(r.get("analysis_time_hours")) for r in sample]
    ys = [_to_float(r.get("reviews_count")) for r in sample]
    valid = [(x, y, c) for x, y, c in zip(xs, ys, colors_list) if x is not None and y is not None]
    if valid:
        vx, vy, vc = zip(*valid)
        ax.scatter(vx, vy, c=list(vc), alpha=0.6, edgecolors="white", linewidths=0.5, s=60)
    ax.set_title("Tempo de Analise x Revisoes (RQ06)", fontsize=13, pad=12)
    ax.set_xlabel("Horas ate merge/close")
    ax.set_ylabel("No de revisoes")
    ax.legend(handles=legend_patches, loc="upper right")
    plt.tight_layout()
    plt.savefig(GRAFICOS_DIR / "g7_scatter_tempo_revisoes.png")
    plt.close()
    print("  Grafico salvo: g7_scatter_tempo_revisoes.png")

    # ── G8: Scatter – Descrição vs Revisões ──────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    xs = [_to_float(r.get("body_length")) for r in sample]
    ys = [_to_float(r.get("reviews_count")) for r in sample]
    valid = [(x, y, c) for x, y, c in zip(xs, ys, colors_list) if x is not None and y is not None]
    if valid:
        vx, vy, vc = zip(*valid)
        ax.scatter(vx, vy, c=list(vc), alpha=0.6, edgecolors="white", linewidths=0.5, s=60)
    ax.set_title("Tamanho da Descricao x Revisoes (RQ07)", fontsize=13, pad=12)
    ax.set_xlabel("Caracteres no corpo do PR")
    ax.set_ylabel("No de revisoes")
    ax.legend(handles=legend_patches, loc="upper right")
    plt.tight_layout()
    plt.savefig(GRAFICOS_DIR / "g8_scatter_descricao_revisoes.png")
    plt.close()
    print("  Grafico salvo: g8_scatter_descricao_revisoes.png")

    # ── G9: Heatmap de correlações (simplificado) ────────────────────────────
    if correlacoes:
        labels_corr = [c["par"].split("–")[-1].strip() for c in correlacoes]
        rhos = [c["rho"] for c in correlacoes]
        fig, ax = plt.subplots(figsize=(10, 5))
        colors_bar = [cor_merged if r >= 0 else cor_closed for r in rhos]
        bars = ax.barh(labels_corr, rhos, color=colors_bar, edgecolor="white")
        ax.axvline(0, color="gray", linewidth=0.8, linestyle="--")
        ax.set_title("Coeficientes de Correlação Spearman (ρ)", fontsize=13, pad=12)
        ax.set_xlabel("ρ de Spearman")
        for bar, val in zip(bars, rhos):
            ax.text(val + (0.01 if val >= 0 else -0.01), bar.get_y() + bar.get_height() / 2,
                    f"{val:.3f}", va="center", ha="left" if val >= 0 else "right", fontsize=8)
        ax.set_xlim(-0.6, 0.6)
        plt.tight_layout()
        plt.savefig(GRAFICOS_DIR / "g9_correlacoes_spearman.png")
        plt.close()
        print("  Gráfico salvo: g9_correlacoes_spearman.png")

    print(f"\n  Todos os gráficos salvos em: {GRAFICOS_DIR}\n")


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  LAB 3 – ANÁLISE DE CODE REVIEW NO GITHUB")
    print("=" * 60 + "\n")

    print("1. Limpando arquivos smoke...")
    limpar_smoke()

    print("2. Carregando todos os PRs...")
    sample, fieldnames = carregar_todos_prs()

    print("3. Análise descritiva...")
    resultados, merged, closed = analisar(sample)

    print("4. Calculando correlações de Spearman...")
    correlacoes = calcular_correlacoes(sample)

    print("5. Gerando gráficos...")
    gerar_graficos(sample, correlacoes)

    print("=" * 60)
    print("  ANÁLISE CONCLUÍDA!")
    print(f"  PRs analisados: {len(sample)} ({len(merged)} MERGED, {len(closed)} CLOSED)")
    print(f"  Gráficos em: {GRAFICOS_DIR}")
    print(f"  Correlações: {RESULTADOS_DIR / 'correlacoes.csv'}")
    print(f"  Amostra: {PRS_100_CSV}")
    print("=" * 60 + "\n")
