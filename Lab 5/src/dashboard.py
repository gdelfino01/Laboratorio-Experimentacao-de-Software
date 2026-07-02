"""Interactive dashboard for the GraphQL vs REST experiment (Lab 05).

Displays the experiment results using Plotly Dash with interactive charts,
summary cards, and statistical tables.

Usage
-----
    py src/dashboard.py                          # default CSV
    py src/dashboard.py --port 8051              # custom port

Then open http://localhost:8050 in your browser.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import dash
from dash import dcc, html, dash_table
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# ---- Paths ----------------------------------------------------------------
_LAB5_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_CSV = _LAB5_ROOT / "output" / "experiment_runs.csv"
STATS_TESTS_CSV = _LAB5_ROOT / "output" / "stats_hypothesis_tests.csv"
STATS_DESC_CSV = _LAB5_ROOT / "output" / "stats_descriptive.csv"
STATS_DESC_Q_CSV = _LAB5_ROOT / "output" / "stats_descriptive_per_query.csv"

# ---- Color palette ---------------------------------------------------------
REST_COLOR = "#3b82f6"       # blue
GRAPHQL_COLOR = "#f97316"    # orange
BG_COLOR = "#0f172a"         # dark navy
CARD_BG = "#1e293b"          # slate-800
CARD_BORDER = "#334155"      # slate-700
TEXT_COLOR = "#e2e8f0"       # slate-200
TEXT_MUTED = "#94a3b8"       # slate-400
ACCENT_GREEN = "#22c55e"
ACCENT_RED = "#ef4444"
GRID_COLOR = "#1e293b"

TREATMENT_COLORS = {"REST": REST_COLOR, "GRAPHQL": GRAPHQL_COLOR}

QUERY_LABELS = {
    "Q1": "user_profile",
    "Q2": "repository_metadata",
    "Q3": "user_repositories_list",
    "Q4": "repository_issues_list",
    "Q5": "repository_pull_requests_list",
}


# ============================================================================
# Data loading
# ============================================================================

def load_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = df[df["status_code"] == 200].copy()
    df["response_time_ms"] = pd.to_numeric(df["response_time_ms"], errors="coerce")
    df["response_bytes"] = pd.to_numeric(df["response_bytes"], errors="coerce")
    return df


def load_stats_tests(csv_path: Path) -> pd.DataFrame | None:
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None


def load_stats_desc(csv_path: Path) -> pd.DataFrame | None:
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return None


# ============================================================================
# Layout helpers
# ============================================================================

def _plotly_dark_layout(fig: go.Figure, title: str = "") -> go.Figure:
    """Apply consistent dark theme to a Plotly figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=TEXT_COLOR)),
        paper_bgcolor=CARD_BG,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR, family="Inter, system-ui, sans-serif"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=TEXT_COLOR),
        ),
        margin=dict(l=50, r=30, t=60, b=50),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    )
    return fig


def _stat_card(title: str, value: str, subtitle: str = "", color: str = TEXT_COLOR) -> html.Div:
    """A summary metric card."""
    return html.Div(
        className="stat-card",
        children=[
            html.Div(title, className="stat-label"),
            html.Div(value, className="stat-value", style={"color": color}),
            html.Div(subtitle, className="stat-subtitle") if subtitle else None,
        ],
    )


# ============================================================================
# Chart builders
# ============================================================================

def build_boxplot_overall(df: pd.DataFrame, metric: str, title: str, ylabel: str) -> go.Figure:
    fig = go.Figure()
    for treatment, color in TREATMENT_COLORS.items():
        subset = df[df["treatment"] == treatment][metric]
        fig.add_trace(go.Box(
            y=subset, name=treatment,
            marker_color=color, line_color=color,
            boxmean="sd",
            hovertemplate=f"<b>{treatment}</b><br>{ylabel}: %{{y:.1f}}<extra></extra>",
        ))
    _plotly_dark_layout(fig, title)
    fig.update_yaxes(title_text=ylabel)
    fig.update_xaxes(title_text="Tratamento")
    return fig


def build_boxplot_per_query(df: pd.DataFrame, metric: str, title: str, ylabel: str) -> go.Figure:
    queries = sorted(df["query_id"].unique())
    fig = make_subplots(
        rows=1, cols=len(queries),
        subplot_titles=[f"{q} ({QUERY_LABELS.get(q, '')})" for q in queries],
        shared_yaxes=False,
    )
    for i, qid in enumerate(queries, 1):
        for treatment, color in TREATMENT_COLORS.items():
            subset = df[(df["query_id"] == qid) & (df["treatment"] == treatment)][metric]
            fig.add_trace(
                go.Box(
                    y=subset, name=treatment,
                    marker_color=color, line_color=color,
                    showlegend=(i == 1),
                    hovertemplate=f"<b>{treatment} - {qid}</b><br>{ylabel}: %{{y:.1f}}<extra></extra>",
                ),
                row=1, col=i,
            )
        fig.update_xaxes(showticklabels=False, row=1, col=i)
    _plotly_dark_layout(fig, title)
    fig.update_yaxes(title_text=ylabel, row=1, col=1)
    fig.update_layout(height=400)
    # Fix subplot title colors
    for ann in fig.layout.annotations:
        ann.font.color = TEXT_MUTED
        ann.font.size = 11
    return fig


def build_barplot_medians(df: pd.DataFrame, metric: str, title: str, ylabel: str) -> go.Figure:
    medians = (
        df.groupby(["query_id", "treatment"])[metric]
        .median()
        .reset_index()
        .rename(columns={metric: "median"})
    )
    fig = go.Figure()
    for treatment, color in TREATMENT_COLORS.items():
        sub = medians[medians["treatment"] == treatment]
        fig.add_trace(go.Bar(
            x=sub["query_id"], y=sub["median"],
            name=treatment, marker_color=color,
            text=sub["median"].apply(lambda v: f"{v:,.0f}"),
            textposition="outside",
            textfont=dict(color=TEXT_MUTED, size=10),
            hovertemplate=f"<b>{treatment}</b><br>Query: %{{x}}<br>{ylabel}: %{{y:,.1f}}<extra></extra>",
        ))
    _plotly_dark_layout(fig, title)
    fig.update_yaxes(title_text=ylabel)
    fig.update_xaxes(title_text="Query")
    fig.update_layout(barmode="group")
    return fig


def build_reduction_bar(df: pd.DataFrame) -> go.Figure:
    """Bar chart showing % reduction in response size for each query."""
    queries = sorted(df["query_id"].unique())
    reductions = []
    for qid in queries:
        rest_med = df[(df["query_id"] == qid) & (df["treatment"] == "REST")]["response_bytes"].median()
        gql_med = df[(df["query_id"] == qid) & (df["treatment"] == "GRAPHQL")]["response_bytes"].median()
        pct = ((rest_med - gql_med) / rest_med) * 100 if rest_med > 0 else 0
        reductions.append({
            "query_id": qid,
            "reduction_pct": round(pct, 1),
            "rest_bytes": rest_med,
            "gql_bytes": gql_med,
        })
    rdf = pd.DataFrame(reductions)

    fig = go.Figure(go.Bar(
        x=rdf["query_id"], y=rdf["reduction_pct"],
        marker_color=[ACCENT_GREEN if r > 50 else "#facc15" for r in rdf["reduction_pct"]],
        text=rdf["reduction_pct"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        textfont=dict(color=TEXT_COLOR, size=12),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "REST: %{customdata[0]:,.0f} bytes<br>"
            "GraphQL: %{customdata[1]:,.0f} bytes<br>"
            "Reducao: %{y:.1f}%<extra></extra>"
        ),
        customdata=np.stack([rdf["rest_bytes"], rdf["gql_bytes"]], axis=-1),
    ))
    _plotly_dark_layout(fig, "Reducao do Tamanho da Resposta por Query (GraphQL vs REST)")
    fig.update_yaxes(title_text="Reducao (%)", range=[0, 105])
    fig.update_xaxes(title_text="Query")
    return fig


def build_scatter_timeline(df: pd.DataFrame) -> go.Figure:
    """Scatter plot of response time over iterations."""
    fig = go.Figure()
    for treatment, color in TREATMENT_COLORS.items():
        sub = df[df["treatment"] == treatment].sort_values("iteration")
        fig.add_trace(go.Scatter(
            x=sub["iteration"], y=sub["response_time_ms"],
            mode="markers",
            name=treatment,
            marker=dict(color=color, size=5, opacity=0.6),
            hovertemplate=(
                f"<b>{treatment}</b><br>"
                "Iteracao: %{x}<br>"
                "Tempo: %{y:.1f} ms<br>"
                "Query: %{customdata}<extra></extra>"
            ),
            customdata=sub["query_id"],
        ))
    _plotly_dark_layout(fig, "Tempo de Resposta por Iteracao")
    fig.update_xaxes(title_text="Iteracao")
    fig.update_yaxes(title_text="Tempo de Resposta (ms)")
    return fig


def build_stats_table(stats_df: pd.DataFrame | None) -> html.Div:
    """Build a styled DataTable with hypothesis test results."""
    if stats_df is None:
        return html.Div("Arquivo stats_hypothesis_tests.csv nao encontrado.", style={"color": ACCENT_RED})

    display_df = stats_df.copy()
    display_df["p_value"] = display_df["p_value"].apply(
        lambda p: f"{p:.6f}" if p > 0.000001 else "< 0.000001"
    )
    display_df["cliff_delta"] = display_df["cliff_delta"].apply(lambda d: f"{d:+.4f}")
    display_df["reject_H0"] = display_df["reject_H0"].apply(
        lambda r: "Rejeitada" if r else "Nao rejeitada"
    )
    display_df.columns = [
        "RQ", "Metrica", "Escopo", "N Pares",
        "Wilcoxon W", "p-valor", "Decisao H0",
        "Cliff's delta", "Magnitude"
    ]

    return dash_table.DataTable(
        data=display_df.to_dict("records"),
        columns=[{"name": c, "id": c} for c in display_df.columns],
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": CARD_BG,
            "color": TEXT_COLOR,
            "fontWeight": "bold",
            "borderBottom": f"2px solid {CARD_BORDER}",
            "textAlign": "center",
            "fontFamily": "Inter, system-ui, sans-serif",
        },
        style_cell={
            "backgroundColor": BG_COLOR,
            "color": TEXT_COLOR,
            "border": f"1px solid {CARD_BORDER}",
            "textAlign": "center",
            "padding": "8px 12px",
            "fontFamily": "Inter, system-ui, sans-serif",
            "fontSize": "13px",
        },
        style_data_conditional=[
            {
                "if": {"filter_query": '{Decisao H0} = "Rejeitada"'},
                "backgroundColor": "rgba(239, 68, 68, 0.15)",
                "color": ACCENT_RED,
                "fontWeight": "bold",
            },
            {
                "if": {"filter_query": '{Decisao H0} = "Nao rejeitada"'},
                "backgroundColor": "rgba(34, 197, 94, 0.15)",
                "color": ACCENT_GREEN,
            },
            {
                "if": {"filter_query": '{Magnitude} = "large"'},
                "color": ACCENT_RED,
                "fontWeight": "bold",
            },
        ],
    )


# ============================================================================
# CSS
# ============================================================================

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

body {
    background-color: %(bg)s;
    color: %(text)s;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    margin: 0;
    padding: 0;
}

.dashboard-container {
    max-width: 1280px;
    margin: 0 auto;
    padding: 24px 32px;
}

.dashboard-header {
    text-align: center;
    padding: 32px 0 16px;
    border-bottom: 1px solid %(border)s;
    margin-bottom: 32px;
}

.dashboard-header h1 {
    font-size: 28px;
    font-weight: 700;
    margin: 0 0 8px;
    background: linear-gradient(135deg, %(blue)s, %(orange)s);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.dashboard-header p {
    color: %(muted)s;
    font-size: 14px;
    margin: 0;
}

.cards-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
}

.stat-card {
    background: %(card)s;
    border: 1px solid %(border)s;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.stat-label {
    font-size: 12px;
    font-weight: 500;
    color: %(muted)s;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
}

.stat-value {
    font-size: 28px;
    font-weight: 700;
    line-height: 1.2;
}

.stat-subtitle {
    font-size: 11px;
    color: %(muted)s;
    margin-top: 4px;
}

.section-title {
    font-size: 20px;
    font-weight: 600;
    color: %(text)s;
    margin: 40px 0 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid %(border)s;
}

.chart-container {
    background: %(card)s;
    border: 1px solid %(border)s;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 24px;
}

.charts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-bottom: 24px;
}

@media (max-width: 900px) {
    .charts-grid {
        grid-template-columns: 1fr;
    }
}

.table-container {
    background: %(card)s;
    border: 1px solid %(border)s;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 24px;
    overflow-x: auto;
}

.footer {
    text-align: center;
    color: %(muted)s;
    font-size: 12px;
    padding: 24px 0;
    border-top: 1px solid %(border)s;
    margin-top: 32px;
}

.rq-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 600;
    margin-right: 8px;
}

.rq-badge-rq1 {
    background: rgba(59, 130, 246, 0.2);
    color: %(blue)s;
}

.rq-badge-rq2 {
    background: rgba(249, 115, 22, 0.2);
    color: %(orange)s;
}

/* ── Tab styling ─────────────────────────────────────── */

.custom-tabs-container {
    border-bottom: 2px solid %(border)s;
    margin-bottom: 28px;
}

.custom-tabs-container .tab {
    background: transparent;
    border: none;
    color: %(muted)s;
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 14px;
    font-weight: 500;
    padding: 12px 24px;
    cursor: pointer;
    transition: color 0.2s, border-color 0.2s;
    border-bottom: 3px solid transparent;
    margin-bottom: -2px;
}

.custom-tabs-container .tab:hover {
    color: %(text)s;
}

.custom-tabs-container .tab--selected {
    color: %(blue)s !important;
    border-bottom: 3px solid %(blue)s !important;
    background: transparent !important;
    font-weight: 600;
}

.tab-content {
    animation: fadeIn 0.3s ease-in-out;
    min-height: 60vh;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.explanation-box {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(249, 115, 22, 0.06));
    border: 1px solid %(border)s;
    border-left: 4px solid %(blue)s;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 24px;
    font-size: 13.5px;
    line-height: 1.7;
    color: %(muted)s;
}

.explanation-box strong {
    color: %(text)s;
}

.explanation-box code {
    background: rgba(59, 130, 246, 0.15);
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 12.5px;
    color: %(blue)s;
}

.conclusion-card {
    background: %(card)s;
    border: 1px solid %(border)s;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
}

.conclusion-card h3 {
    margin: 0 0 12px;
    font-size: 16px;
    font-weight: 600;
    color: %(text)s;
}

.conclusion-card p {
    margin: 0 0 8px;
    font-size: 13.5px;
    line-height: 1.6;
    color: %(muted)s;
}

.conclusion-card .highlight {
    color: %(orange)s;
    font-weight: 600;
}
""" % {
    "bg": BG_COLOR,
    "text": TEXT_COLOR,
    "muted": TEXT_MUTED,
    "card": CARD_BG,
    "border": CARD_BORDER,
    "blue": REST_COLOR,
    "orange": GRAPHQL_COLOR,
}


# ============================================================================
# App layout builder
# ============================================================================

def build_app(df: pd.DataFrame, stats_tests: pd.DataFrame | None) -> dash.Dash:
    app = dash.Dash(
        __name__,
        title="Lab 05 - GraphQL vs REST Dashboard",
        update_title=None,
    )

    # ---- Compute summary metrics -------------------------------------------
    n_total = len(df)
    n_iterations = df["iteration"].nunique()
    n_queries = df["query_id"].nunique()

    rest_time_med = df[df["treatment"] == "REST"]["response_time_ms"].median()
    gql_time_med = df[df["treatment"] == "GRAPHQL"]["response_time_ms"].median()

    rest_size_med = df[df["treatment"] == "REST"]["response_bytes"].median()
    gql_size_med = df[df["treatment"] == "GRAPHQL"]["response_bytes"].median()
    size_reduction = ((rest_size_med - gql_size_med) / rest_size_med) * 100

    time_diff_pct = ((gql_time_med - rest_time_med) / rest_time_med) * 100

    # ---- Build charts ------------------------------------------------------
    box_time_overall = build_boxplot_overall(
        df, "response_time_ms",
        "RQ1 - Tempo de Resposta (Geral)",
        "Tempo (ms)",
    )
    box_size_overall = build_boxplot_overall(
        df, "response_bytes",
        "RQ2 - Tamanho da Resposta (Geral)",
        "Tamanho (bytes)",
    )
    box_time_query = build_boxplot_per_query(
        df, "response_time_ms",
        "RQ1 - Tempo de Resposta por Query",
        "Tempo (ms)",
    )
    box_size_query = build_boxplot_per_query(
        df, "response_bytes",
        "RQ2 - Tamanho da Resposta por Query",
        "Tamanho (bytes)",
    )
    bar_time = build_barplot_medians(
        df, "response_time_ms",
        "Mediana do Tempo de Resposta por Query",
        "Tempo (ms)",
    )
    bar_size = build_barplot_medians(
        df, "response_bytes",
        "Mediana do Tamanho da Resposta por Query",
        "Tamanho (bytes)",
    )
    reduction_bar = build_reduction_bar(df)
    scatter = build_scatter_timeline(df)
    stats_table = build_stats_table(stats_tests)

    # ---- Tab content builders ----------------------------------------------
    tab_style = {
        "borderBottom": "none",
        "borderTop": "none",
        "borderLeft": "none",
        "borderRight": "none",
        "backgroundColor": "transparent",
        "color": TEXT_MUTED,
        "fontFamily": "Inter, system-ui, sans-serif",
        "fontSize": "14px",
        "fontWeight": "500",
        "padding": "12px 24px",
    }
    tab_selected_style = {
        **tab_style,
        "color": REST_COLOR,
        "fontWeight": "600",
        "borderBottom": f"3px solid {REST_COLOR}",
    }

    # ── Tab 1: Visao Geral ──────────────────────────────────────────
    tab_overview = dcc.Tab(
        label="\U0001f4ca  Visao Geral",
        style=tab_style,
        selected_style=tab_selected_style,
        children=html.Div(className="tab-content", children=[
            html.Div(className="explanation-box", children=[
                html.Strong("Sobre o experimento: "),
                "Este dashboard apresenta os resultados de um experimento controlado "
                "comparando ",
                html.Strong("REST"),
                " e ",
                html.Strong("GraphQL"),
                " como tecnologias de consulta a APIs. "
                "Foram realizadas ",
                html.Code(f"{n_iterations} iteracoes"),
                f" para cada uma das {n_queries} queries pareadas, "
                f"totalizando ",
                html.Strong(f"{n_total} medicoes validas"),
                ". Cada iteracao executa a mesma consulta logica em ambos os "
                "tratamentos (REST e GraphQL) em ordem aleatorizada para evitar "
                "vieses de ordenacao.",
            ]),

            html.Div(className="cards-row", children=[
                _stat_card(
                    "Medicoes Validas", f"{n_total}",
                    f"{n_iterations} iteracoes x {n_queries} queries x 2",
                ),
                _stat_card(
                    "Mediana Tempo REST",
                    f"{rest_time_med:,.0f} ms",
                    "",
                    REST_COLOR,
                ),
                _stat_card(
                    "Mediana Tempo GraphQL",
                    f"{gql_time_med:,.0f} ms",
                    f"{abs(time_diff_pct):.0f}% {'mais lento' if time_diff_pct > 0 else 'mais rapido'}",
                    GRAPHQL_COLOR,
                ),
                _stat_card(
                    "Reducao Tamanho",
                    f"{size_reduction:.0f}%",
                    f"REST {rest_size_med:,.0f} -> GraphQL {gql_size_med:,.0f} bytes",
                    ACCENT_GREEN,
                ),
            ]),

            html.Div(className="conclusion-card", children=[
                html.H3("\u2728 Principais Descobertas"),
                html.P([
                    html.Strong("RQ1 (Tempo): "),
                    f"A mediana do tempo de resposta do GraphQL foi "
                    f"de {gql_time_med:,.0f} ms contra {rest_time_med:,.0f} ms "
                    f"do REST. ",
                    "Embora a diferenca seja estatisticamente significativa "
                    "(p < 0.05), o tamanho do efeito (Cliff's delta) e ",
                    html.Span("negligivel", className="highlight"),
                    ", indicando que na pratica a performance e semelhante.",
                ]),
                html.P([
                    html.Strong("RQ2 (Tamanho): "),
                    f"O GraphQL reduziu o tamanho das respostas em ",
                    html.Span(f"{size_reduction:.0f}%", className="highlight"),
                    f" na mediana geral. O efeito e ",
                    html.Span("large", className="highlight"),
                    ", confirmando que o GraphQL transfere "
                    "significativamente menos dados ao solicitar apenas os "
                    "campos necessarios.",
                ]),
            ]),

            html.Div(className="chart-container", children=[
                dcc.Graph(figure=scatter, config={"displayModeBar": False}),
            ]),

            html.Div(className="explanation-box", children=[
                html.Strong("Sobre o grafico acima: "),
                "O scatter plot mostra o tempo de resposta de cada medicao ao "
                "longo das iteracoes. Ele permite identificar tendencias "
                "temporais, outliers e verificar a estabilidade das medicoes.",
            ]),
        ]),
    )

    # ── Tab 2: RQ1 - Tempo de Resposta ─────────────────────────────
    tab_rq1 = dcc.Tab(
        label="\u23f1  RQ1 - Tempo de Resposta",
        style=tab_style,
        selected_style=tab_selected_style,
        children=html.Div(className="tab-content", children=[
            html.H2([
                html.Span("RQ1", className="rq-badge rq-badge-rq1"),
                "Consultas GraphQL possuem desempenho (tempo de resposta) "
                "comparavel a consultas REST?",
            ], className="section-title"),

            html.Div(className="explanation-box", children=[
                html.Strong("O que estamos medindo: "),
                "O tempo de resposta (em milissegundos) de cada requisicao, "
                "medido do envio da request HTTP ate o recebimento completo "
                "do corpo da resposta. ",
                html.Strong("Boxplots"),
                " mostram a distribuicao (mediana, quartis e outliers). ",
                html.Strong("Graficos de barras"),
                " comparam as medianas por query para facilitar a leitura.",
            ]),

            html.Div(className="charts-grid", children=[
                html.Div(className="chart-container", children=[
                    dcc.Graph(figure=box_time_overall, config={"displayModeBar": False}),
                ]),
                html.Div(className="chart-container", children=[
                    dcc.Graph(figure=bar_time, config={"displayModeBar": False}),
                ]),
            ]),

            html.Div(className="chart-container", children=[
                dcc.Graph(figure=box_time_query, config={"displayModeBar": False}),
            ]),

            html.Div(className="explanation-box", children=[
                html.Strong("Interpretacao: "),
                "Queries simples (Q1, Q2) apresentam tempos semelhantes entre "
                "REST e GraphQL. Queries que retornam listas (Q3, Q5) tendem a "
                "ser mais lentas no GraphQL devido ao overhead do resolver. "
                "Ja a Q4 (issues) e mais rapida no GraphQL, possivelmente porque "
                "o REST retorna um payload muito maior que precisa de mais tempo "
                "de transferencia.",
            ]),
        ]),
    )

    # ── Tab 3: RQ2 - Tamanho da Resposta ───────────────────────────
    tab_rq2 = dcc.Tab(
        label="\U0001f4e6  RQ2 - Tamanho da Resposta",
        style=tab_style,
        selected_style=tab_selected_style,
        children=html.Div(className="tab-content", children=[
            html.H2([
                html.Span("RQ2", className="rq-badge rq-badge-rq2"),
                "Respostas GraphQL sao menores que respostas REST equivalentes?",
            ], className="section-title"),

            html.Div(className="explanation-box", children=[
                html.Strong("O que estamos medindo: "),
                "O tamanho do corpo da resposta HTTP em bytes. "
                "O GraphQL permite solicitar apenas os campos necessarios "
                "(eliminando over-fetching), enquanto o REST retorna todos os "
                "campos definidos pela API. O grafico de reducao (%) mostra "
                "quanto menor e a resposta GraphQL em relacao a REST para cada query.",
            ]),

            html.Div(className="charts-grid", children=[
                html.Div(className="chart-container", children=[
                    dcc.Graph(figure=box_size_overall, config={"displayModeBar": False}),
                ]),
                html.Div(className="chart-container", children=[
                    dcc.Graph(figure=reduction_bar, config={"displayModeBar": False}),
                ]),
            ]),

            html.Div(className="chart-container", children=[
                dcc.Graph(figure=box_size_query, config={"displayModeBar": False}),
            ]),

            html.Div(className="chart-container", children=[
                dcc.Graph(figure=bar_size, config={"displayModeBar": False}),
            ]),

            html.Div(className="explanation-box", children=[
                html.Strong("Interpretacao: "),
                "A reducao de tamanho e consistente em todas as queries, "
                "com destaque para Q4 e Q5 que possuem payloads REST muito "
                "grandes (issues e pull requests incluem dezenas de campos "
                "desnecessarios). O GraphQL elimina essa ",
                html.Strong("over-fetching"),
                ", reduzindo drasticamente o volume de dados transferidos.",
            ]),
        ]),
    )

    # ── Tab 4: Testes Estatisticos ─────────────────────────────────
    tab_stats = dcc.Tab(
        label="\U0001f9ea  Testes Estatisticos",
        style=tab_style,
        selected_style=tab_selected_style,
        children=html.Div(className="tab-content", children=[
            html.H2(
                "Testes Estatisticos (Wilcoxon Signed-Rank)",
                className="section-title",
            ),

            html.Div(className="explanation-box", children=[
                html.Strong("Metodologia: "),
                "Como os dados nao seguem distribuicao normal (confirmado pelo "
                "teste de Shapiro-Wilk), utilizamos o teste nao-parametrico de ",
                html.Strong("Wilcoxon Signed-Rank"),
                " para amostras pareadas. O nivel de significancia adotado e ",
                html.Code("alpha = 0.05"),
                ". Quando ",
                html.Code("p < 0.05"),
                ", rejeitamos H0 (hipotese nula de que nao ha diferenca). "
                "O tamanho do efeito e medido pelo ",
                html.Strong("Cliff's delta"),
                ": negligible (|d| < 0.147), small (< 0.33), "
                "medium (< 0.474) e large (>= 0.474).",
            ]),

            html.Div(className="table-container", children=[stats_table]),

            html.Div(className="explanation-box", children=[
                html.Strong("Como ler a tabela: "),
                html.Br(),
                html.Strong("\u2022 RQ"),
                " — Questao de pesquisa (RQ1 = tempo, RQ2 = tamanho).",
                html.Br(),
                html.Strong("\u2022 Escopo"),
                " — 'overall' agrega todas as queries; Q1-Q5 sao analises individuais.",
                html.Br(),
                html.Strong("\u2022 p-valor"),
                " — Probabilidade de observar tal diferenca se H0 fosse verdadeira. "
                "Quanto menor, mais forte a evidencia contra H0.",
                html.Br(),
                html.Strong("\u2022 Cliff's delta"),
                " — Magnitude do efeito. Valores positivos indicam REST > GraphQL; "
                "negativos indicam GraphQL > REST.",
                html.Br(),
                html.Strong("\u2022 Decisao H0"),
                " — ",
                html.Span("Rejeitada", style={"color": ACCENT_RED, "fontWeight": "bold"}),
                " = diferenca significativa; ",
                html.Span("Nao rejeitada", style={"color": ACCENT_GREEN}),
                " = sem evidencia de diferenca.",
            ]),
        ]),
    )

    # ---- Layout ------------------------------------------------------------
    app.index_string = """<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>""" + CUSTOM_CSS + """</style>
</head>
<body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>"""

    app.layout = html.Div(className="dashboard-container", children=[
        # ── Header ──────────────────────────────────────────────────────
        html.Div(className="dashboard-header", children=[
            html.H1("GraphQL vs REST"),
            html.P("Lab 05 - Experimento Controlado | Dashboard de Resultados"),
        ]),

        # ── Tabs ───────────────────────────────────────────────────────
        dcc.Tabs(
            id="dashboard-tabs",
            value="tab-overview",
            className="custom-tabs-container",
            children=[tab_overview, tab_rq1, tab_rq2, tab_stats],
        ),

        # ── Footer ─────────────────────────────────────────────────────
        html.Div(className="footer", children=[
            "Lab 05 - Laboratorio de Experimentacao de Software | "
            "PUC Minas | GraphQL vs REST - Experimento Controlado"
        ]),
    ])

    return app


# ============================================================================
# Main
# ============================================================================

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch the experiment dashboard.")
    parser.add_argument(
        "--input", type=Path, default=DEFAULT_INPUT_CSV,
        help="Path to the experiment CSV (default: %(default)s).",
    )
    parser.add_argument(
        "--port", type=int, default=8050,
        help="Port to serve the dashboard on (default: %(default)s).",
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Run in Dash debug mode (auto-reload).",
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

    df = load_data(csv_path)
    stats_tests = load_stats_tests(STATS_TESTS_CSV)

    print(f"Loaded {len(df)} measurements from {csv_path}")
    print(f"Starting dashboard on http://localhost:{args.port}")

    app = build_app(df, stats_tests)
    app.run(debug=args.debug, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
