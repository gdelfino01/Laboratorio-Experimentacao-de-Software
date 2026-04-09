from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError


def _format_df_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sem dados disponíveis para esta seção._"
    headers = [str(column) for column in df.columns]
    separator = ["---"] * len(headers)

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]

    for _, row in df.iterrows():
        values = [str(row[column]) for column in df.columns]
        lines.append("| " + " | ".join(values) + " |")

    return "\n".join(lines)


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()

def _corr_strength(value: float) -> str:
    abs_value = abs(value)
    if abs_value < 0.1:
        return "desprezível"
    if abs_value < 0.3:
        return "fraca"
    if abs_value < 0.5:
        return "moderada"
    if abs_value < 0.7:
        return "forte"
    return "muito forte"


def _is_significant(pvalue: float, alpha: float = 0.05) -> bool:
    return pvalue < alpha


def _to_float(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _summary_value(summary_df: pd.DataFrame, metric: str, field: str) -> float | None:
    if summary_df.empty or field not in summary_df.columns:
        return None
    metric_rows = summary_df[summary_df.get("metric", "") == metric]
    if metric_rows.empty:
        return None
    return _to_float(metric_rows.iloc[0].get(field))


def _corr_value(correlations_df: pd.DataFrame, rq: str, quality_metric: str, field: str) -> float | None:
    if correlations_df.empty or field not in correlations_df.columns:
        return None
    selected = correlations_df[
        (correlations_df.get("rq", "") == rq)
        & (correlations_df.get("quality_metric", "") == quality_metric)
    ]
    if selected.empty:
        return None
    return _to_float(selected.iloc[0].get(field))


def _format_num(value: float | None, digits: int = 3) -> str:
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def _format_pvalue(value: float | None) -> str:
    if value is None:
        return "N/A"
    if value == 0:
        return "<0.0001"
    if value < 0.001:
        return f"{value:.2e}"
    return f"{value:.4f}"


def _prepare_summary_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    if summary_df.empty:
        return summary_df

    df = summary_df.copy()
    metric_labels = {
        "stars": "Estrelas",
        "age_years": "Idade (anos)",
        "releases": "Releases",
        "repo_loc": "LOC do Repositório",
        "repo_comment_lines": "Linhas de Comentários",
        "cbo_mean": "CBO (média por repositório)",
        "dit_mean": "DIT (média por repositório)",
        "lcom_mean": "LCOM (média por repositório)",
    }
    df["metric"] = df["metric"].map(metric_labels).fillna(df["metric"])

    rename_map = {
        "metric": "Métrica",
        "n": "Repositórios",
        "mean": "Média",
        "median": "Mediana",
        "stdev": "Desvio Padrão",
        "min": "Mínimo",
        "max": "Máximo",
    }
    df = df.rename(columns=rename_map)

    for column in ["Média", "Mediana", "Desvio Padrão", "Mínimo", "Máximo"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").map(
                lambda value: "N/A" if pd.isna(value) else f"{value:.4f}"
            )

    if "Repositórios" in df.columns:
        df["Repositórios"] = pd.to_numeric(df["Repositórios"], errors="coerce").fillna(0).astype(int)

    return df[["Métrica", "Repositórios", "Média", "Mediana", "Desvio Padrão", "Mínimo", "Máximo"]]


def _prepare_rq_table(rq_df: pd.DataFrame) -> pd.DataFrame:
    if rq_df.empty:
        return rq_df

    df = rq_df.copy()
    quality_labels = {
        "cbo_mean": "CBO (média)",
        "dit_mean": "DIT (média)",
        "lcom_mean": "LCOM (média)",
    }
    df["quality_metric"] = df["quality_metric"].map(quality_labels).fillna(df["quality_metric"])

    df["spearman_corr"] = pd.to_numeric(df["spearman_corr"], errors="coerce").map(
        lambda value: "N/A" if pd.isna(value) else f"{value:.3f}"
    )
    df["pearson_corr"] = pd.to_numeric(df["pearson_corr"], errors="coerce").map(
        lambda value: "N/A" if pd.isna(value) else f"{value:.3f}"
    )
    df["spearman_pvalue"] = pd.to_numeric(df["spearman_pvalue"], errors="coerce").map(_format_pvalue)
    df["pearson_pvalue"] = pd.to_numeric(df["pearson_pvalue"], errors="coerce").map(_format_pvalue)

    df = df.rename(
        columns={
            "quality_metric": "Métrica de Qualidade",
            "spearman_corr": "Spearman (rho)",
            "spearman_pvalue": "p-valor Spearman",
            "pearson_corr": "Pearson (r)",
            "pearson_pvalue": "p-valor Pearson",
        }
    )

    return df[
        [
            "Métrica de Qualidade",
            "Spearman (rho)",
            "p-valor Spearman",
            "Pearson (r)",
            "p-valor Pearson",
        ]
    ]


def _rq_findings_text(df: pd.DataFrame, rq_label: str) -> str:
    if df.empty:
        return f"- {rq_label}: sem dados suficientes para análise."

    lines: list[str] = []
    for _, row in df.iterrows():
        quality_metric = str(row.get("quality_metric", ""))
        spearman = _to_float(row.get("spearman_corr"))
        pvalue = _to_float(row.get("spearman_pvalue"))
        n_value = int(_to_float(row.get("n")) or 0)

        if spearman is None or pvalue is None:
            lines.append(f"- {quality_metric}: correlação indisponível.")
            continue

        direction = "positiva" if spearman >= 0 else "negativa"
        strength = _corr_strength(spearman)
        significance = "significativa" if _is_significant(pvalue) else "não significativa"
        lines.append(
            f"- {quality_metric}: Spearman={spearman:.3f} ({direction}, {strength}), "
            f"p={pvalue:.4g}, n={n_value} ({significance})."
        )

    return "\n".join(lines)


def _hypothesis_verdicts(correlations_df: pd.DataFrame) -> list[str]:
    if correlations_df.empty:
        return [
            "- H1: inconclusiva (sem dados).",
            "- H2: inconclusiva (sem dados).",
            "- H3: inconclusiva (sem dados).",
            "- H4: inconclusiva (sem dados).",
        ]

    df = correlations_df.copy()

    # H1: popularidade associada a melhor qualidade (menor LCOM/CBO).
    h1_lcom = df[(df["rq"] == "RQ01") & (df["quality_metric"] == "lcom_mean")]
    h1_cbo = df[(df["rq"] == "RQ01") & (df["quality_metric"] == "cbo_mean")]
    h1_supported = False
    for sample in [h1_lcom, h1_cbo]:
        if sample.empty:
            continue
        corr = _to_float(sample.iloc[0]["spearman_corr"])
        pvalue = _to_float(sample.iloc[0]["spearman_pvalue"])
        if corr is not None and pvalue is not None and corr < 0 and _is_significant(pvalue):
            h1_supported = True
            break

    # H2: maturidade associada a maior complexidade (CBO/DIT).
    h2_dit = df[(df["rq"] == "RQ02") & (df["quality_metric"] == "dit_mean")]
    h2_cbo = df[(df["rq"] == "RQ02") & (df["quality_metric"] == "cbo_mean")]
    h2_hits = 0
    h2_total = 0
    for sample in [h2_dit, h2_cbo]:
        if sample.empty:
            continue
        h2_total += 1
        corr = _to_float(sample.iloc[0]["spearman_corr"])
        pvalue = _to_float(sample.iloc[0]["spearman_pvalue"])
        if corr is not None and pvalue is not None and corr > 0 and _is_significant(pvalue):
            h2_hits += 1

    # H3: atividade associada a melhor manutenção (menor LCOM).
    h3_lcom = df[(df["rq"] == "RQ03") & (df["quality_metric"] == "lcom_mean")]
    h3_supported = False
    if not h3_lcom.empty:
        corr = _to_float(h3_lcom.iloc[0]["spearman_corr"])
        pvalue = _to_float(h3_lcom.iloc[0]["spearman_pvalue"])
        h3_supported = bool(corr is not None and pvalue is not None and corr < 0 and _is_significant(pvalue))

    # H4: tamanho associado a maior acoplamento e menor coesão (LCOM maior).
    h4_subset = df[df["rq"].isin(["RQ04_LOC", "RQ04_COMMENTS"])]
    h4_positive_hits = 0
    h4_total = 0
    for _, row in h4_subset.iterrows():
        quality_metric = str(row.get("quality_metric", ""))
        if quality_metric not in {"cbo_mean", "lcom_mean"}:
            continue
        corr = _to_float(row.get("spearman_corr"))
        pvalue = _to_float(row.get("spearman_pvalue"))
        if corr is None or pvalue is None:
            continue
        h4_total += 1
        if corr > 0 and _is_significant(pvalue):
            h4_positive_hits += 1

    verdicts = []
    verdicts.append("- H1: " + ("confirmada" if h1_supported else "refutada") + ".")

    if h2_total == 0:
        verdicts.append("- H2: inconclusiva.")
    elif h2_hits == h2_total:
        verdicts.append("- H2: confirmada.")
    elif h2_hits > 0:
        verdicts.append("- H2: parcialmente confirmada.")
    else:
        verdicts.append("- H2: refutada.")

    verdicts.append("- H3: " + ("confirmada" if h3_supported else "refutada") + ".")

    if h4_total == 0:
        verdicts.append("- H4: inconclusiva.")
    elif h4_positive_hits == h4_total:
        verdicts.append("- H4: confirmada.")
    elif h4_positive_hits > 0:
        verdicts.append("- H4: parcialmente confirmada.")
    else:
        verdicts.append("- H4: refutada.")

    return verdicts


def generate_final_report(
    dataset_csv_path: Path,
    summary_stats_csv_path: Path,
    correlations_csv_path: Path,
    report_output_path: Path,
) -> Path:
    dataset_df = _load_csv(dataset_csv_path)
    summary_df = _load_csv(summary_stats_csv_path)
    correlations_df = _load_csv(correlations_csv_path)

    if "status" in dataset_df.columns:
        success_df = dataset_df[dataset_df["status"].astype(str).str.lower() == "success"]
    else:
        success_df = dataset_df

    total_repos = len(dataset_df)
    analyzed_repos = len(success_df)
    failed_repos = total_repos - analyzed_repos

    rq01_df = correlations_df[correlations_df.get("rq", "") == "RQ01"] if not correlations_df.empty else pd.DataFrame()
    rq02_df = correlations_df[correlations_df.get("rq", "") == "RQ02"] if not correlations_df.empty else pd.DataFrame()
    rq03_df = correlations_df[correlations_df.get("rq", "") == "RQ03"] if not correlations_df.empty else pd.DataFrame()
    rq04_df = correlations_df[
        correlations_df.get("rq", "").isin(["RQ04_LOC", "RQ04_COMMENTS"])
    ] if not correlations_df.empty else pd.DataFrame()

    summary_table_df = _prepare_summary_table(summary_df)
    rq01_table_df = _prepare_rq_table(rq01_df)
    rq02_table_df = _prepare_rq_table(rq02_df)
    rq03_table_df = _prepare_rq_table(rq03_df)
    rq04_table_df = _prepare_rq_table(rq04_df)

    rq01_findings = _rq_findings_text(rq01_df, "RQ01")
    rq02_findings = _rq_findings_text(rq02_df, "RQ02")
    rq03_findings = _rq_findings_text(rq03_df, "RQ03")
    rq04_findings = _rq_findings_text(rq04_df, "RQ04")

    hypothesis_lines = _hypothesis_verdicts(correlations_df)

    figures_dir = report_output_path.parent / "output" / "figures"
    figure_paths = [
        "output/figures/rq01_stars_vs_cbo_mean.png",
        "output/figures/rq01_stars_vs_dit_mean.png",
        "output/figures/rq01_stars_vs_lcom_mean.png",
        "output/figures/rq02_age_years_vs_cbo_mean.png",
        "output/figures/rq02_age_years_vs_dit_mean.png",
        "output/figures/rq02_age_years_vs_lcom_mean.png",
        "output/figures/rq03_releases_vs_cbo_mean.png",
        "output/figures/rq03_releases_vs_dit_mean.png",
        "output/figures/rq03_releases_vs_lcom_mean.png",
        "output/figures/rq04_loc_repo_loc_vs_cbo_mean.png",
        "output/figures/rq04_loc_repo_loc_vs_dit_mean.png",
        "output/figures/rq04_loc_repo_loc_vs_lcom_mean.png",
        "output/figures/rq04_comments_repo_comment_lines_vs_cbo_mean.png",
        "output/figures/rq04_comments_repo_comment_lines_vs_dit_mean.png",
        "output/figures/rq04_comments_repo_comment_lines_vs_lcom_mean.png",
        "output/figures/correlation_heatmap_spearman.png",
    ]
    existing_figures = [p for p in figure_paths if (report_output_path.parent / p).exists()]

    stars_median = _summary_value(summary_df, "stars", "median")
    age_median = _summary_value(summary_df, "age_years", "median")
    releases_median = _summary_value(summary_df, "releases", "median")
    loc_median = _summary_value(summary_df, "repo_loc", "median")
    comments_median = _summary_value(summary_df, "repo_comment_lines", "median")
    cbo_median = _summary_value(summary_df, "cbo_mean", "median")
    dit_median = _summary_value(summary_df, "dit_mean", "median")
    lcom_median = _summary_value(summary_df, "lcom_mean", "median")

    rq01_lcom = _corr_value(correlations_df, "RQ01", "lcom_mean", "spearman_corr")
    rq01_cbo = _corr_value(correlations_df, "RQ01", "cbo_mean", "spearman_corr")
    rq02_dit = _corr_value(correlations_df, "RQ02", "dit_mean", "spearman_corr")
    rq02_lcom = _corr_value(correlations_df, "RQ02", "lcom_mean", "spearman_corr")
    rq03_lcom = _corr_value(correlations_df, "RQ03", "lcom_mean", "spearman_corr")
    rq03_cbo = _corr_value(correlations_df, "RQ03", "cbo_mean", "spearman_corr")
    rq04_loc_cbo = _corr_value(correlations_df, "RQ04_LOC", "cbo_mean", "spearman_corr")
    rq04_loc_lcom = _corr_value(correlations_df, "RQ04_LOC", "lcom_mean", "spearman_corr")
    rq04_com_cbo = _corr_value(correlations_df, "RQ04_COMMENTS", "cbo_mean", "spearman_corr")
    rq04_com_lcom = _corr_value(correlations_df, "RQ04_COMMENTS", "lcom_mean", "spearman_corr")

    report_lines = [
        "# Relatório Final - Lab02S02: Qualidade Interna de Repositórios Java Open-Source",
        "",
        "## 1. Introdução",
        "",
        "### 1.1 Contextualização",
        "",
        "Projetos open-source evoluem de forma colaborativa, com múltiplos contribuidores atuando em partes distintas do código ao longo do tempo.",
        "Nesse cenário, características de qualidade interna como acoplamento, coesão e estrutura de herança podem se degradar com o crescimento do sistema.",
        "A mensuração empírica dessas características permite avaliar como decisões e dinâmica de desenvolvimento se relacionam com a qualidade arquitetural.",
        "",
        "### 1.2 Problema Foco do Experimento",
        "",
        "Embora repositórios populares sejam amplamente estudados sob a ótica de atividade e adoção, ainda há lacunas na compreensão da relação entre",
        "métricas de processo (popularidade, maturidade, atividade e tamanho) e métricas de produto calculadas por análise estática.",
        "Este laboratório investiga essa relação em repositórios Java, utilizando a ferramenta CK para mensurar CBO, DIT e LCOM.",
        "",
        "### 1.3 Questões de Pesquisa",
        "",
        "- RQ01. Qual a relação entre a popularidade dos repositórios e as suas características de qualidade?",
        "- RQ02. Qual a relação entre a maturidade dos repositórios e as suas características de qualidade?",
        "- RQ03. Qual a relação entre a atividade dos repositórios e as suas características de qualidade?",
        "- RQ04. Qual a relação entre o tamanho dos repositórios e as suas características de qualidade?",
        "",
        "### 1.4 Hipóteses",
        "",
        "- H1 (RQ01): repositórios mais populares tendem a apresentar melhor qualidade estrutural (especialmente menor LCOM médio).",
        "- H2 (RQ02): repositórios mais maduros tendem a acumular maior complexidade estrutural (aumento de CBO/DIT).",
        "- H3 (RQ03): maior atividade (mais releases) tende a estar associada a melhor manutenção e menor LCOM médio.",
        "- H4 (RQ04): repositórios maiores (LOC/comentários) tendem a apresentar maior acoplamento e menor coesão.",
        "",
        "### 1.5 Objetivos",
        "",
        "Objetivo principal: analisar a relação entre métricas de processo e métricas de qualidade interna em repositórios Java open-source.",
        "",
        "Objetivos específicos:",
        "1. Consolidar as métricas por repositório para uma base única de análise.",
        "2. Calcular estatísticas descritivas globais (média, mediana, desvio padrão).",
        "3. Medir associação entre variáveis com correlações de Spearman e Pearson.",
        "4. Produzir visualizações para apoiar interpretação das RQs.",
        "5. Confrontar os resultados observados com as hipóteses formuladas.",
        "",
        "## 2. Metodologia",
        "",
        "### 2.1 Passo a Passo do Experimento",
        "",
        "1. Coleta dos top-1000 repositórios Java por estrelas no GitHub.",
        "2. Clonagem e execução do CK por repositório para extração de métricas de classe.",
        "3. Sumarização por repositório das métricas CBO, DIT e LCOM (média, mediana, desvio padrão).",
        "4. Consolidação com métricas de processo: estrelas, idade (anos), releases, LOC e linhas de comentários.",
        "5. Filtragem de repositórios com status de sucesso para garantir consistência estatística.",
        "6. Cálculo de correlações e geração de gráficos de dispersão e heatmap.",
        "",
        "### 2.2 Métricas e Unidades",
        "",
        "- Popularidade: número de estrelas.",
        "- Maturidade: idade do repositório em anos.",
        "- Atividade: número de releases.",
        "- Tamanho: linhas de código e linhas de comentários no repositório.",
        "- Qualidade interna: CBO, DIT e LCOM (resumo por repositório).",
        "",
        "### 2.3 Decisões Analíticas",
        "",
        "- Spearman foi priorizado na interpretação por maior robustez a distribuições assimétricas e outliers.",
        "- Pearson foi mantido como referência complementar para associação linear.",
        "- A análise considerou apenas repositórios com status success no dataset consolidado.",
        "",
        "## 3. Visualização dos Resultados",
        "",
        "### 3.1 Cobertura da Coleta",
        "",
        f"- Total de linhas no dataset consolidado: {total_repos}.",
        f"- Repositórios analisados com sucesso: {analyzed_repos}.",
        f"- Repositórios com falha no processamento: {failed_repos}.",
        "",
        "### 3.2 Resultados Tabulares",
        "",
        "Resumo descritivo global:",
        _format_df_markdown(summary_table_df),
        "",
        "Medianas de referência do dataset analisado:",
        f"- Estrelas: {_format_num(stars_median, 1)}",
        f"- Idade (anos): {_format_num(age_median, 2)}",
        f"- Releases: {_format_num(releases_median, 1)}",
        f"- LOC: {_format_num(loc_median, 1)}",
        f"- Linhas de comentários: {_format_num(comments_median, 1)}",
        f"- CBO médio por repositório: {_format_num(cbo_median, 3)}",
        f"- DIT médio por repositório: {_format_num(dit_median, 3)}",
        f"- LCOM médio por repositório: {_format_num(lcom_median, 3)}",
        "",
        "### 3.3 Correlações por RQ",
        "",
        "#### RQ01 - Popularidade vs Qualidade",
        _format_df_markdown(rq01_table_df),
        "",
        "#### RQ02 - Maturidade vs Qualidade",
        _format_df_markdown(rq02_table_df),
        "",
        "#### RQ03 - Atividade vs Qualidade",
        _format_df_markdown(rq03_table_df),
        "",
        "#### RQ04 - Tamanho vs Qualidade",
        _format_df_markdown(rq04_table_df),
        "",
        "### 3.4 Gráficos Gerados",
        "",
        *[f"- {path}" for path in existing_figures],
        "",
        "## 4. Discussão dos Resultados",
        "",
        "### 4.1 Confronto com as Questões de Pesquisa",
        "",
        "#### RQ01 - Popularidade e Qualidade",
        "Resultado observado: as correlações entre estrelas e qualidade são muito fracas, com destaque para LCOM (Spearman "
        + _format_num(rq01_lcom, 3)
        + ") e CBO (Spearman "
        + _format_num(rq01_cbo, 3)
        + ").",
        "Confronto com H1: a hipótese é refutada, pois não há evidência de que maior popularidade esteja associada a melhor qualidade interna.",
        "",
        "#### RQ02 - Maturidade e Qualidade",
        "Resultado observado: maturidade apresenta associação positiva com DIT (Spearman "
        + _format_num(rq02_dit, 3)
        + ") e também com LCOM (Spearman "
        + _format_num(rq02_lcom, 3)
        + "), sugerindo crescimento de complexidade em repositórios mais antigos.",
        "Confronto com H2: hipótese parcialmente confirmada, com evidência mais forte para profundidade de herança e coesão pior ao longo do tempo.",
        "",
        "#### RQ03 - Atividade e Qualidade",
        "Resultado observado: releases se associam positivamente com CBO (Spearman "
        + _format_num(rq03_cbo, 3)
        + ") e LCOM (Spearman "
        + _format_num(rq03_lcom, 3)
        + "), contrariando a expectativa de melhora estrutural com maior atividade.",
        "Confronto com H3: hipótese refutada, indicando que mais releases não significam, por si, menor acoplamento ou maior coesão.",
        "",
        "#### RQ04 - Tamanho e Qualidade",
        "Resultado observado: tamanho apresenta as maiores associações com qualidade, tanto por LOC quanto por linhas de comentários.",
        "Para LOC, CBO (Spearman "
        + _format_num(rq04_loc_cbo, 3)
        + ") e LCOM (Spearman "
        + _format_num(rq04_loc_lcom, 3)
        + ") crescem com o tamanho; para comentários, CBO (Spearman "
        + _format_num(rq04_com_cbo, 3)
        + ") e LCOM (Spearman "
        + _format_num(rq04_com_lcom, 3)
        + ") seguem tendência semelhante.",
        "Confronto com H4: hipótese confirmada, com evidência consistente de degradação estrutural em projetos maiores.",
        "",
        "### 4.2 Síntese das Hipóteses",
        "",
        *hypothesis_lines,
        "",
        "A síntese aponta que maturidade e, principalmente, tamanho explicam melhor a variação das métricas de qualidade do que popularidade isolada.",
        "",
        "## 5. Limitações e Ameaças à Validade",
        "",
        "- Parte dos repositórios falhou no processamento automático, reduzindo a cobertura efetiva da amostra.",
        "- Correlação não implica causalidade; os resultados indicam associação, não efeito causal.",
        "- Métricas agregadas por repositório ocultam heterogeneidade interna por módulo/pacote.",
        "- A presença de outliers (especialmente em LOC e LCOM) pode distorcer medidas lineares; por isso Spearman foi priorizado.",
        "",
        "## 6. Conclusão",
        "",
        "O experimento respondeu às quatro RQs com base em uma amostra ampla de repositórios Java e mostrou que qualidade interna se relaciona mais com escala e maturidade do que com popularidade.",
        "Como continuidade, recomenda-se segmentar a base por tipo de sistema e domínio para reduzir viés de mistura e aprofundar a interpretação causal.",
    ]

    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Relatório final gerado em: {report_output_path}")
    return report_output_path