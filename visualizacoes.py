"""
Geração de visualizações para cada RQ do Lab01S02.
Lê os dados de repositorios.csv e gera gráficos na pasta 'graficos/'.
"""

import csv
import math
import os
import statistics
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


OUTPUT_DIR = "graficos"
CSV_FILE = "repositorios.csv"


def load_csv(filename: str) -> list[dict]:
    with open(filename, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def numeric_values(data: list[dict], key: str) -> list[float]:
    values = []
    for row in data:
        try:
            values.append(float(row[key]))
        except (ValueError, KeyError):
            continue
    return values


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def save(fig, name: str):
    fig.savefig(os.path.join(OUTPUT_DIR, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Salvo: {OUTPUT_DIR}/{name}")


def median(values: list[float]) -> float:
    if not values:
        return 0.0
    return statistics.median(values)


# ── RQ01: Idade dos repositórios ────────────────────────────────────
def rq01(data: list[dict]):
    print("\n[RQ01] Idade dos repositórios")
    days = numeric_values(data, "idade_dias")
    years = [d / 365.25 for d in days]

    # Boxplot
    fig, ax = plt.subplots(figsize=(8, 4))
    bp = ax.boxplot(years, vert=False, patch_artist=True,
                    boxprops=dict(facecolor="#4C72B0", alpha=0.7),
                    medianprops=dict(color="white", linewidth=2))
    ax.set_xlabel("Idade (anos)")
    ax.set_title("RQ01 — Distribuição da Idade dos Repositórios")
    med = statistics.median(years)
    ax.axvline(med, color="red", linestyle="--", label=f"Mediana: {med:.1f} anos")
    ax.legend()
    save(fig, "rq01_boxplot.png")

    # Histograma
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(years, bins=20, color="#4C72B0", edgecolor="white", alpha=0.85)
    ax.axvline(med, color="red", linestyle="--", label=f"Mediana: {med:.1f} anos")
    ax.set_xlabel("Idade (anos)")
    ax.set_ylabel("Número de repositórios")
    ax.set_title("RQ01 — Histograma da Idade dos Repositórios")
    ax.legend()
    save(fig, "rq01_histograma.png")


# ── RQ02: Pull Requests aceitas ─────────────────────────────────────
def rq02(data: list[dict]):
    print("\n[RQ02] Pull Requests aceitas")
    prs = numeric_values(data, "prs_aceitas")

    if not prs:
        print("  Coluna 'prs_aceitas' não encontrada no CSV.")
        return

    # Boxplot (escala log)
    prs_pos = [v for v in prs if v > 0]
    if not prs_pos:
        print("  Nenhum repo com PRs > 0.")
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    bp = ax.boxplot(prs_pos, vert=False, patch_artist=True,
                    boxprops=dict(facecolor="#DD8452", alpha=0.7),
                    medianprops=dict(color="white", linewidth=2))
    ax.set_xscale("log")
    ax.set_xlabel("PRs aceitas (escala log)")
    ax.set_title("RQ02 — Distribuição de Pull Requests Aceitas")
    med = statistics.median(prs)
    ax.axvline(max(med, 1), color="red", linestyle="--", label=f"Mediana: {med:.0f}")
    ax.legend()
    save(fig, "rq02_boxplot.png")

    # Scatter: estrelas × PRs
    stars = numeric_values(data, "estrelas")
    if len(stars) == len(prs):
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(stars, prs, alpha=0.4, s=15, color="#DD8452")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Estrelas (log)")
        ax.set_ylabel("PRs aceitas (log)")
        ax.set_title("RQ02 — Estrelas × PRs Aceitas")
        save(fig, "rq02_scatter.png")


# ── RQ03: Releases ──────────────────────────────────────────────────
def rq03(data: list[dict]):
    print("\n[RQ03] Releases")
    rels = numeric_values(data, "releases")

    # Boxplot (escala log, apenas >0)
    rels_pos = [v for v in rels if v > 0]
    if rels_pos:
        fig, ax = plt.subplots(figsize=(8, 4))
        bp = ax.boxplot(rels_pos, vert=False, patch_artist=True,
                        boxprops=dict(facecolor="#55A868", alpha=0.7),
                        medianprops=dict(color="white", linewidth=2))
        ax.set_xscale("log")
        ax.set_xlabel("Releases (escala log, repos com ≥1 release)")
        ax.set_title("RQ03 — Distribuição de Releases (repos com releases)")
        med = statistics.median(rels_pos)
        ax.axvline(med, color="red", linestyle="--", label=f"Mediana (>0): {med:.0f}")
        ax.legend()
        save(fig, "rq03_boxplot.png")

    # Histograma com destaque para 0
    fig, ax = plt.subplots(figsize=(8, 5))
    zero_count = sum(1 for v in rels if v == 0)
    non_zero = [v for v in rels if v > 0]
    ax.bar(["0 releases"], [zero_count], color="#C44E52", alpha=0.8, width=0.4)
    ax.bar(["≥1 release"], [len(non_zero)], color="#55A868", alpha=0.8, width=0.4)
    ax.set_ylabel("Número de repositórios")
    ax.set_title(f"RQ03 — Repos com vs sem releases ({zero_count} sem / {len(non_zero)} com)")
    for i, v in enumerate([zero_count, len(non_zero)]):
        ax.text(i, v + 5, str(v), ha="center", fontweight="bold")
    save(fig, "rq03_barras.png")

    # Histograma dos que têm releases
    if non_zero:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(non_zero, bins=30, color="#55A868", edgecolor="white", alpha=0.85)
        med = statistics.median(non_zero)
        ax.axvline(med, color="red", linestyle="--", label=f"Mediana: {med:.0f}")
        ax.set_xlabel("Total de releases")
        ax.set_ylabel("Número de repositórios")
        ax.set_title("RQ03 — Histograma de Releases (repos com ≥1 release)")
        ax.legend()
        save(fig, "rq03_histograma.png")


# ── RQ04: Dias desde última atualização ─────────────────────────────
def rq04(data: list[dict]):
    print("\n[RQ04] Atualização recente")
    days = numeric_values(data, "dias_desde_ultima_atualizacao")
    if not days:
        print("  Coluna 'dias_desde_ultima_atualizacao' não encontrada no CSV. Pule ou re-gere o CSV.")
        return

    # Boxplot
    fig, ax = plt.subplots(figsize=(8, 4))
    bp = ax.boxplot(days, vert=False, patch_artist=True,
                    boxprops=dict(facecolor="#8172B3", alpha=0.7),
                    medianprops=dict(color="white", linewidth=2))
    ax.set_xlabel("Dias desde última atualização")
    ax.set_title("RQ04 — Tempo Desde a Última Atualização")
    med = statistics.median(days)
    ax.axvline(med, color="red", linestyle="--", label=f"Mediana: {med:.0f} dias")
    ax.legend()
    save(fig, "rq04_boxplot.png")

    # Histograma
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(days, bins=30, color="#8172B3", edgecolor="white", alpha=0.85)
    ax.axvline(med, color="red", linestyle="--", label=f"Mediana: {med:.0f} dias")
    ax.set_xlabel("Dias desde última atualização")
    ax.set_ylabel("Número de repositórios")
    ax.set_title("RQ04 — Histograma do Tempo Desde Última Atualização")
    ax.legend()
    save(fig, "rq04_histograma.png")


# ── RQ05: Linguagens mais populares ────────────────────────────────
def rq05(data: list[dict]):
    print("\n[RQ05] Linguagens primárias")
    languages = [row.get("linguagem_primaria") or "Desconhecida" for row in data]
    counts = Counter(languages)
    top_n = 12
    top_items = counts.most_common(top_n)

    if not top_items:
        print("  Sem dados de linguagem para plotar.")
        return

    names = [item[0] for item in top_items][::-1]
    values = [item[1] for item in top_items][::-1]
    total = len(languages)

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(names, values, color="#4C78A8", alpha=0.85)
    ax.set_title("RQ05 — Top Linguagens Primárias")
    ax.set_xlabel("Número de repositórios")
    for bar, value in zip(bars, values):
        pct = (value * 100 / total) if total else 0
        ax.text(value + 0.3, bar.get_y() + bar.get_height() / 2, f"{value} ({pct:.1f}%)", va="center")
    save(fig, "rq05_top_linguagens.png")

    fig, ax = plt.subplots(figsize=(10, 5))
    ordered = counts.most_common()
    labels = [item[0] for item in ordered]
    vals = [item[1] for item in ordered]
    cumulative = []
    acc = 0
    for value in vals:
        acc += value
        cumulative.append((acc / total) * 100 if total else 0)

    ax.bar(range(len(vals)), vals, color="#72B7B2", alpha=0.8)
    ax2 = ax.twinx()
    ax2.plot(range(len(cumulative)), cumulative, color="#E45756", marker="o", linewidth=2)
    ax2.set_ylabel("Percentual acumulado (%)")
    ax.set_ylabel("Número de repositórios")
    ax.set_xlabel("Linguagens (ordenadas por frequência)")
    ax.set_title("RQ05 — Curva Acumulada de Linguagens")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax2.set_ylim(0, 105)
    save(fig, "rq05_pareto_linguagens.png")


# ── RQ06: Razão de issues fechadas ─────────────────────────────────
def rq06(data: list[dict]):
    print("\n[RQ06] Razão de issues fechadas")
    ratios = []
    for row in data:
        value = row.get("razao_issues_fechadas", "")
        try:
            ratios.append(float(value))
        except (ValueError, TypeError):
            continue

    if not ratios:
        print("  Coluna 'razao_issues_fechadas' sem valores numéricos.")
        return

    med = statistics.median(ratios)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.boxplot(
        ratios,
        vert=False,
        patch_artist=True,
        boxprops=dict(facecolor="#54A24B", alpha=0.7),
        medianprops=dict(color="white", linewidth=2),
    )
    ax.axvline(med, color="red", linestyle="--", label=f"Mediana: {med:.2f}")
    ax.axvline(0.7, color="#333333", linestyle=":", label="Referência H6: 0,70")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Razão de issues fechadas")
    ax.set_title("RQ06 — Distribuição da Razão de Issues Fechadas")
    ax.legend()
    save(fig, "rq06_boxplot.png")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(ratios, bins=20, color="#54A24B", edgecolor="white", alpha=0.85)
    ax.axvline(med, color="red", linestyle="--", label=f"Mediana: {med:.2f}")
    ax.axvline(0.7, color="#333333", linestyle=":", label="Referência H6: 0,70")
    ax.set_xlabel("Razão de issues fechadas")
    ax.set_ylabel("Número de repositórios")
    ax.set_xlim(0, 1)
    ax.set_title("RQ06 — Histograma da Razão de Issues Fechadas")
    ax.legend()
    save(fig, "rq06_histograma.png")


# ── RQ07: Linguagem x indicadores de manutenção ────────────────────
def rq07(data: list[dict]):
    print("\n[RQ07] Relação entre linguagem e indicadores")
    grouped = defaultdict(list)
    for row in data:
        grouped[row.get("linguagem_primaria") or "Desconhecida"].append(row)

    top_languages = [lang for lang, _ in Counter(grouped.keys()).most_common()]
    # Reordena por quantidade real de repositórios e mantém top 8 para legibilidade.
    top_languages = sorted(grouped.keys(), key=lambda lang: len(grouped[lang]), reverse=True)[:8]

    if not top_languages:
        print("  Sem dados suficientes para RQ07.")
        return

    med_prs = []
    med_releases = []
    med_days = []
    med_ratio = []
    for language in top_languages:
        rows = grouped[language]
        prs = numeric_values(rows, "prs_aceitas")
        releases = numeric_values(rows, "releases")
        days = numeric_values(rows, "dias_desde_ultima_atualizacao")
        ratio = numeric_values(rows, "razao_issues_fechadas")
        med_prs.append(median(prs))
        med_releases.append(median(releases))
        med_days.append(median(days))
        med_ratio.append(median(ratio))

    fig, ax = plt.subplots(figsize=(10, 5))
    x = range(len(top_languages))
    adjusted_prs = [value + 1 for value in med_prs]
    adjusted_rel = [value + 1 for value in med_releases]
    ax.plot(x, adjusted_prs, marker="o", label="PRs aceitas (mediana +1)")
    ax.plot(x, adjusted_rel, marker="o", label="Releases (mediana +1)")
    ax.set_yscale("log")
    ax.set_xticks(list(x))
    ax.set_xticklabels(top_languages, rotation=35, ha="right")
    ax.set_ylabel("Escala log")
    ax.set_title("RQ07 — PRs e Releases por Linguagem (medianas)")
    ax.legend()
    save(fig, "rq07_prs_releases_por_linguagem.png")


# ── MAIN ─────────────────────────────────────────────────────────────
def main():
    data = load_csv(CSV_FILE)
    print(f"Registros carregados: {len(data)}")
    print(f"Colunas disponíveis: {list(data[0].keys()) if data else 'nenhuma'}")

    ensure_output_dir()

    rq01(data)
    rq02(data)
    rq03(data)
    rq04(data)
    rq05(data)
    rq06(data)
    rq07(data)

    print(f"\nTodos os gráficos foram salvos na pasta '{OUTPUT_DIR}/'.")


if __name__ == "__main__":
    main()
