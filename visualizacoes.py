"""
Geração de visualizações para cada RQ do Lab01S02.
Lê os dados de repositorios.csv e gera gráficos na pasta 'graficos/'.
"""

import csv
import os
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


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

    print(f"\nTodos os gráficos foram salvos na pasta '{OUTPUT_DIR}/'.")


if __name__ == "__main__":
    main()
