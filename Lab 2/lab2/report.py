from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError


def _format_df_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sem dados disponíveis para esta seção._"
    return df.to_markdown(index=False)


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()


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

    rq01_df = correlations_df[correlations_df.get("rq", "") == "RQ01"] if not correlations_df.empty else pd.DataFrame()
    rq02_df = correlations_df[correlations_df.get("rq", "") == "RQ02"] if not correlations_df.empty else pd.DataFrame()
    rq03_df = correlations_df[correlations_df.get("rq", "") == "RQ03"] if not correlations_df.empty else pd.DataFrame()
    rq04_df = correlations_df[
        correlations_df.get("rq", "").isin(["RQ04_LOC", "RQ04_COMMENTS"])
    ] if not correlations_df.empty else pd.DataFrame()

    report_lines = [
        "# Relatório Final - Lab 2",
        "",
        "## 1. Introdução e Hipóteses",
        "",
        "Este relatório investiga a relação entre características do processo de desenvolvimento e métricas de qualidade em repositórios Java do GitHub.",
        "",
        "Hipóteses informais adotadas:",
        "- H1 (Popularidade): repositórios mais populares tendem a apresentar melhores indicadores de qualidade estrutural (especialmente menor LCOM médio).",
        "- H2 (Maturidade): repositórios mais antigos tendem a ter maior complexidade acumulada (aumento de CBO/DIT).",
        "- H3 (Atividade): maior número de releases pode estar associado a melhor manutenção e menor LCOM médio.",
        "- H4 (Tamanho): repositórios maiores (LOC/comentários) tendem a apresentar maior acoplamento e menor coesão média.",
        "",
        "## 2. Metodologia",
        "",
        "1. Seleção de repositórios: top-1000 repositórios Java por estrelas no GitHub.",
        "2. Métricas de processo coletadas por API: estrelas, releases, idade e tamanho (LOC/comentários).",
        "3. Métricas de qualidade coletadas com CK e sumarizadas por repositório: CBO, DIT e LCOM (média, mediana e desvio padrão).",
        "4. Análise estatística: correlações de Spearman (principal) e Pearson (complementar), com p-valor.",
        "5. Visualização: gráficos de dispersão por questão de pesquisa e matriz de correlação.",
        "",
        "## 3. Cobertura da Coleta",
        "",
        f"- Total de linhas no dataset consolidado: **{total_repos}**",
        f"- Repositórios analisados com status de sucesso: **{analyzed_repos}**",
        "",
        "## 4. Estatísticas Descritivas Gerais",
        "",
        _format_df_markdown(summary_df),
        "",
        "## 5. Resultados por Questão de Pesquisa",
        "",
        "### RQ01 - Popularidade vs Qualidade",
        "",
        _format_df_markdown(rq01_df),
        "",
        "### RQ02 - Maturidade vs Qualidade",
        "",
        _format_df_markdown(rq02_df),
        "",
        "### RQ03 - Atividade vs Qualidade",
        "",
        _format_df_markdown(rq03_df),
        "",
        "### RQ04 - Tamanho vs Qualidade",
        "",
        _format_df_markdown(rq04_df),
        "",
        "## 6. Discussão",
        "",
        "A interpretação principal deve considerar o sinal e magnitude das correlações de Spearman:",
        "- Correlação positiva: aumento conjunto entre as variáveis.",
        "- Correlação negativa: aumento de uma variável associado à redução da outra.",
        "- p-valor baixo (ex.: < 0,05): evidência estatística mais forte para a associação observada.",
        "",
        "Para métricas de qualidade em que valores menores são desejáveis (ex.: LCOM e CBO), correlações negativas com popularidade/atividade podem indicar tendência de melhor qualidade.",
        "",
        "## 7. Limitações e Ameaças à Validade",
        "",
        "- Possíveis falhas de coleta em parte dos 1000 repositórios (timeouts, estrutura incomum de projeto, falhas do CK).",
        "- Correlação não implica causalidade.",
        "- Métricas agregadas por repositório podem ocultar variações internas por módulo/pacote.",
        "",
        "## 8. Conclusão",
        "",
        "O pipeline implementado permite reproduzir a coleta, análise estatística e visualização para responder às quatro RQs do laboratório. A versão final do relatório deve ser revisada com foco na interpretação crítica dos resultados empíricos obtidos na execução completa.",
        "",
    ]

    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Relatório final gerado em: {report_output_path}")
    return report_output_path