import csv
import argparse
import warnings
import statistics
from pathlib import Path
from collections import Counter, defaultdict

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go

warnings.filterwarnings("ignore")


# ─── CLI ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Dashboard CVE/Node.js – Interativo")
parser.add_argument("--data_dir", default=".", help="Diretório com os CSVs")
parser.add_argument("--port",     default=8050, type=int, help="Porta do servidor")
args = parser.parse_args()

DATA_DIR = Path(args.data_dir)


# ─── Paleta ───────────────────────────────────────────────────────────────────
DARK_BG    = "#0D1B2A"
PANEL_BG   = "#1A2B3C"
ACCENT1    = "#2E75B6"
ACCENT2    = "#F4A100"
ACCENT3    = "#2ECC71"
ACCENT4    = "#E74C3C"
TEXT_MAIN  = "#E8EDF2"
TEXT_DIM   = "#8A9BB0"
GRID_COLOR = "#253547"

SEV_COLORS = {
    "LOW":      "#2ECC71",
    "MEDIUM":   "#F4A100",
    "HIGH":     "#E67E22",
    "CRITICAL": "#E74C3C",
    "UNKNOWN":  "#7F8C8D",
}

TOOL_COLORS = {
    "dependabot": "#2E75B6",
    "renovate":   "#2ECC71",
    "snyk":       "#9B59B6",
    "codeql":     "#F39C12",
    "mend":       "#1ABC9C",
    "npm_audit":  "#3498DB",
    "pyup":       "#D35400",
    "none":       "#E74C3C",
}

TOOL_LABELS = {
    "dependabot": "Dependabot",
    "renovate":   "Renovate",
    "snyk":       "Snyk",
    "codeql":     "CodeQL",
    "mend":       "Mend",
    "npm_audit":  "npm audit",
    "pyup":       "PyUp",
    "none":       "Sem ferramenta",
}

CAT_COLORS = {
    "update_security":      "#2E75B6",
    "update":               "#2ECC71",
    "security_scanner":     "#9B59B6",
    "security_automation":  "#F39C12",
    "security_remediation": "#1ABC9C",
    "audit_automation":     "#3498DB",
    "none":                 "#E74C3C",
}

CAT_LABELS = {
    "update_security":      "Update + Security",
    "update":               "Update",
    "security_scanner":     "Security Scanner",
    "security_automation":  "Security Automation",
    "security_remediation": "Security Remediation",
    "audit_automation":     "Audit Automation",
    "none":                 "Sem ferramenta",
}

tools_ordered = ["dependabot", "renovate", "snyk", "codeql", "mend", "npm_audit", "pyup", "none"]
tool_labels   = [TOOL_LABELS[t] for t in tools_ordered]
cats_ordered  = ["update_security", "update", "security_scanner", "security_automation",
                 "security_remediation", "audit_automation", "none"]
cat_labels    = [CAT_LABELS[c] for c in cats_ordered]
sev_labels    = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]


# ─── Helpers ──────────────────────────────────────────────────────────────────
def read_csv(filename):
    path = DATA_DIR / filename
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pct(a, b):
    return round(a / b * 100, 1) if b else 0.0


BASE_LAYOUT = dict(
    paper_bgcolor=PANEL_BG,
    plot_bgcolor=PANEL_BG,
    font=dict(color=TEXT_MAIN, family="Inter, Roboto, sans-serif"),
    margin=dict(l=15, r=15, t=45, b=15),
    hoverlabel=dict(bgcolor=DARK_BG, bordercolor=PANEL_BG, font_size=12),
)


# ─── Carrega dados ────────────────────────────────────────────────────────────
print("Carregando dados...")
summary   = read_csv("summary_by_tool.csv")
vuln_flat = read_csv("vulnerable_dependencies_flat.csv")
cat_summary = read_csv("summary_by_category.csv")

tool_data = {r["tool"]: r for r in summary}
cat_data  = {r["category"]: r for r in cat_summary}

M1 = sum(int(r["repos"]) for r in summary)
M2 = sum(int(r["total_direct_dependencies"]) for r in summary)
M3 = sum(int(r["vulnerable_dependencies"]) for r in summary)
M4 = pct(M3, M2)
total_cves      = sum(int(r["total_cves"]) for r in summary)
repos_with_vuln = sum(int(r["repos_with_any_vuln"]) for r in summary)

# M5
direct_vuln = [r for r in vuln_flat if r.get("is_subdependency", "False") == "False"]
dep_fix_map = defaultdict(set)
for r in direct_vuln:
    key = (r["repo_full_name"], r["dep_name"], r["dep_resolved_version"])
    dep_fix_map[key].add(r["fix_available"])
with_fix    = sum(1 for v in dep_fix_map.values() if "True"  in v)
without_fix = sum(1 for v in dep_fix_map.values() if "True" not in v)
M5 = pct(with_fix, len(dep_fix_map))

# M6
sev_counter = Counter(r["severity"].strip().upper() or "UNKNOWN" for r in vuln_flat)
sev_counter["UNKNOWN"] = sev_counter.get("UNKNOWN", 0) + sev_counter.pop("", 0)
sev_values = [sev_counter.get(s, 0) for s in sev_labels]
total_sev  = sum(sev_values)
sev_pcts   = [pct(v, total_sev) for v in sev_values]

# M7
M7 = pct(sev_counter.get("HIGH", 0) + sev_counter.get("CRITICAL", 0), total_sev)

# M9
tool_vuln_pct = [
    pct(int(tool_data[t]["vulnerable_dependencies"]),
        int(tool_data[t]["total_direct_dependencies"]))
    if t in tool_data else 0 for t in tools_ordered
]
tool_repos    = [int(tool_data[t]["repos"]) if t in tool_data else 0 for t in tools_ordered]
deps_by_tool  = [int(tool_data[t]["total_direct_dependencies"]) if t in tool_data else 0 for t in tools_ordered]
repos_vuln_pct = [
    pct(int(tool_data[t]["repos_with_any_vuln"]), int(tool_data[t]["repos"]))
    if t in tool_data else 0 for t in tools_ordered
]
repos_vuln_abs = [int(tool_data[t]["repos_with_any_vuln"]) if t in tool_data else 0 for t in tools_ordered]

kind_counter = Counter(r["dep_kind"] for r in vuln_flat if r.get("dep_kind"))

sev_by_tool = {}
for row in summary:
    t      = row["tool"]
    total_t = int(row["total_cves"]) or 1
    sev_by_tool[t] = {
        s: pct(int(row.get(f"cve_{s.lower()}", 0)), total_t)
        for s in sev_labels if f"cve_{s.lower()}" in row
    }

none_pct = tool_vuln_pct[tools_ordered.index("none")]
dep_pct  = tool_vuln_pct[tools_ordered.index("dependabot")]
diff     = round(none_pct - dep_pct, 2)

# ─── RQ3: "Any bot" vs "None" ────────────────────────────────────────────────
any_bot_rows = [r for r in summary if r["tool"] != "none"]
any_bot_repos = sum(int(r["repos"]) for r in any_bot_rows)
any_bot_deps  = sum(int(r["total_direct_dependencies"]) for r in any_bot_rows)
any_bot_vuln  = sum(int(r["vulnerable_dependencies"]) for r in any_bot_rows)
any_bot_pct   = pct(any_bot_vuln, any_bot_deps)
none_row      = tool_data["none"]
none_deps     = int(none_row["total_direct_dependencies"])
none_vuln     = int(none_row["vulnerable_dependencies"])
none_pct_rq3  = pct(none_vuln, none_deps)
rq3_diff      = round(none_pct_rq3 - any_bot_pct, 2)

# ─── RQ4: Dados por categoria ────────────────────────────────────────────────
cat_vuln_pct = [
    pct(int(cat_data[c]["vulnerable_dependencies"]),
        int(cat_data[c]["total_direct_dependencies"]))
    if c in cat_data else 0 for c in cats_ordered
]
cat_repos = [int(cat_data[c]["repos"]) if c in cat_data else 0 for c in cats_ordered]
cat_repos_vuln_pct = [
    pct(int(cat_data[c]["repos_with_any_vuln"]), int(cat_data[c]["repos"]))
    if c in cat_data else 0 for c in cats_ordered
]
cat_sev_score = [
    float(cat_data[c]["severity_score_high_critical_pct"]) if c in cat_data else 0
    for c in cats_ordered
]

sev_by_cat = {}
for row in cat_summary:
    c = row["category"]
    total_c = int(row["total_cves"]) or 1
    sev_by_cat[c] = {
        s: pct(int(row.get(f"cve_{s.lower()}", 0)), total_c)
        for s in sev_labels if f"cve_{s.lower()}" in row
    }

repo_cve_counter = Counter(r["repo_full_name"] for r in vuln_flat)
repo_cve_values = list(repo_cve_counter.values())

repo_cve_median = statistics.median(repo_cve_values)
repo_cve_mean = statistics.mean(repo_cve_values)
repo_cve_q1 = statistics.quantiles(repo_cve_values, n=4)[0]
repo_cve_q3 = statistics.quantiles(repo_cve_values, n=4)[2]

cvss_scores = []
for r in vuln_flat:
    score_str = r.get("cvss_base_score", "").strip()
    if score_str:
        try:
            cvss_scores.append(float(score_str))
        except ValueError:
            pass

cvss_median = statistics.median(cvss_scores) if cvss_scores else 0
cvss_mean = statistics.mean(cvss_scores) if cvss_scores else 0

print("  Dados processados. Iniciando dashboard interativo...")


# ─── Figuras ──────────────────────────────────────────────────────────────────
def fig_donut_tool():
    fig = go.Figure(go.Pie(
        values=tool_repos, labels=tool_labels, hole=0.55,
        marker=dict(colors=[TOOL_COLORS[t] for t in tools_ordered],
                    line=dict(color=DARK_BG, width=2)),
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>%{value:,} repos<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Distribuição por Ferramenta (M1)", font_size=13, x=0.01, xanchor="left"),
        showlegend=True,
        legend=dict(orientation="h", y=-0.22, font=dict(size=9, color=TEXT_DIM)),
        annotations=[dict(text=f"<b>{M1:,}</b><br>repos", x=0.5, y=0.5,
                          showarrow=False, font=dict(size=14, color=TEXT_MAIN), align="center")],
    )
    return fig


def fig_bar_deps_by_tool():
    fig = go.Figure(go.Bar(
        x=deps_by_tool, y=tool_labels, orientation="h",
        marker=dict(color=[TOOL_COLORS[t] for t in tools_ordered]),
        text=[f"{v:,}" for v in deps_by_tool], textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:,} deps diretas<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Total Deps. Diretas por Grupo (M2)", font_size=13, x=0.01, xanchor="left"),
        xaxis=dict(gridcolor=GRID_COLOR, color=TEXT_DIM),
        yaxis=dict(color=TEXT_DIM, autorange="reversed"),
        showlegend=False,
    )
    return fig


def fig_bar_dep_kind():
    kinds  = ["dependencies", "devDependencies"]
    k_vals = [kind_counter.get(k, 0) for k in kinds]
    k_pcts = [pct(v, sum(k_vals)) for v in k_vals]
    fig = go.Figure(go.Bar(
        x=["Runtime\n(dependencies)", "Dev\n(devDependencies)"],
        y=k_pcts,
        marker=dict(color=[ACCENT4, ACCENT2]),
        text=[f"{v:.1f}%" for v in k_pcts], textposition="outside",
        customdata=k_vals,
        hovertemplate="<b>%{x}</b><br>%{y:.1f}% dos CVEs<br>%{customdata:,} ocorrências<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="CVEs por Tipo de Dependência", font_size=13, x=0.01, xanchor="left"),
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_DIM, title="% dos CVEs"),
        xaxis=dict(color=TEXT_DIM),
        showlegend=False,
    )
    return fig


def fig_donut_vuln():
    fig = go.Figure(go.Pie(
        values=[M3, M2 - M3], labels=["Com CVE", "Sem CVE"], hole=0.55,
        marker=dict(colors=[ACCENT4, ACCENT3], line=dict(color=DARK_BG, width=2)),
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>%{value:,} deps<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Deps. Vulneráveis vs Seguras (M3/M2 — M4)", font_size=13, x=0.01, xanchor="left"),
        showlegend=True,
        legend=dict(orientation="h", y=-0.18, font=dict(size=9, color=TEXT_DIM)),
        annotations=[dict(text=f"<b>{M4}%</b><br>vulneráveis", x=0.5, y=0.5,
                          showarrow=False, font=dict(size=14, color=ACCENT4), align="center")],
    )
    return fig


def fig_bar_repos_vuln_pct():
    fig = go.Figure(go.Bar(
        x=tool_labels, y=repos_vuln_pct,
        marker=dict(color=[TOOL_COLORS[t] for t in tools_ordered]),
        text=[f"{v:.1f}%" for v in repos_vuln_pct], textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:.1f}% com ≥1 vuln<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="% Repositórios com ≥1 Vuln por Grupo", font_size=13, x=0.01, xanchor="left"),
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_DIM, title="% de repositórios", range=[0, 110]),
        xaxis=dict(color=TEXT_DIM),
        showlegend=False,
    )
    return fig


def fig_donut_fix():
    fig = go.Figure(go.Pie(
        values=[with_fix, without_fix], labels=["Com fix", "Sem fix"], hole=0.55,
        marker=dict(colors=[ACCENT3, ACCENT4], line=dict(color=DARK_BG, width=2)),
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>%{value:,} deps<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Deps. Vulneráveis com Fix Disponível (M5)", font_size=13, x=0.01, xanchor="left"),
        showlegend=True,
        legend=dict(orientation="h", y=-0.18, font=dict(size=9, color=TEXT_DIM)),
        annotations=[dict(text=f"<b>{M5}%</b><br>com fix", x=0.5, y=0.5,
                          showarrow=False, font=dict(size=14, color=ACCENT3), align="center")],
    )
    return fig


def fig_bar_severity(selected_tools=None):
    if selected_tools:
        # Recalcula para subset de ferramentas
        rows_sub = [r for r in vuln_flat
                    if any(r.get("repo_full_name", "").startswith(t) or True
                           for t in tools_ordered)
                    and r.get("tool", r.get("dep_kind", "")) in selected_tools
                    ]
        sc = Counter(r["severity"].strip().upper() or "UNKNOWN"
                     for r in vuln_flat
                     if r.get("repo_full_name") in {
                         v["repo_full_name"] for v in vuln_flat
                         if any(td.get("tool") in selected_tools
                                for td in summary if td.get("tool") in selected_tools)
                     })
    # usa global sempre — filtragem por ferramenta em gráfico dedicado
    cols  = [SEV_COLORS[s] for s in sev_labels]
    fig = go.Figure(go.Bar(
        x=sev_labels, y=sev_pcts,
        marker=dict(color=cols),
        text=[f"{v:.1f}%" for v in sev_pcts], textposition="outside",
        customdata=sev_values,
        hovertemplate="<b>%{x}</b><br>%{y:.1f}% dos CVEs<br>%{customdata:,} ocorrências<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Distribuição CVEs por Severidade (M6 – CVSS)", font_size=13, x=0.01, xanchor="left"),
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_DIM, title="% do total de CVEs"),
        xaxis=dict(color=TEXT_DIM),
        showlegend=False,
    )
    return fig


def fig_donut_severity():
    cols = [SEV_COLORS[s] for s in sev_labels]
    fig = go.Figure(go.Pie(
        values=sev_values, labels=sev_labels, hole=0.55,
        marker=dict(colors=cols, line=dict(color=DARK_BG, width=2)),
        textinfo="percent",
        hovertemplate="<b>%{label}</b><br>%{value:,} CVEs<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Proporção por Nível (M6 – CVSS)", font_size=13, x=0.01, xanchor="left"),
        showlegend=True,
        legend=dict(orientation="h", y=-0.22, font=dict(size=8, color=TEXT_DIM)),
        annotations=[dict(text=f"<b>{M7}%</b><br>alto+crítico<br>(M7)", x=0.5, y=0.5,
                          showarrow=False, font=dict(size=13, color=ACCENT4), align="center")],
    )
    return fig


def fig_stacked_sev_by_tool(highlight_tool=None):
    fig = go.Figure()
    for sev in sev_labels:
        vals      = [sev_by_tool.get(t, {}).get(sev, 0) for t in tools_ordered]
        opacities = [1.0 if (highlight_tool is None or t == highlight_tool) else 0.35
                     for t in tools_ordered]
        colors    = [SEV_COLORS[sev]] * len(tools_ordered)
        fig.add_trace(go.Bar(
            name=sev, x=tool_labels, y=vals,
            marker=dict(color=colors, opacity=opacities),
            hovertemplate=f"<b>{sev}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
        ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Severidade por Grupo de Ferramenta (M6 por grupo)", font_size=13, x=0.01, xanchor="left"),
        barmode="stack",
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_DIM,
                   title="% dos CVEs (por ferramenta)", range=[0, 115]),
        xaxis=dict(color=TEXT_DIM),
        legend=dict(font=dict(size=8, color=TEXT_DIM), orientation="h", y=-0.28),
    )
    return fig


def fig_bar_tool_vuln_pct(highlight_tool=None):
    opacities = [1.0 if (highlight_tool is None or t == highlight_tool) else 0.4
                 for t in tools_ordered]
    fig = go.Figure(go.Bar(
        x=tool_labels, y=tool_vuln_pct,
        marker=dict(color=[TOOL_COLORS[t] for t in tools_ordered], opacity=opacities),
        text=[f"{v:.1f}%" for v in tool_vuln_pct], textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:.2f}% deps. vulneráveis<extra></extra>",
    ))
    fig.add_hline(y=M4, line_dash="dash", line_color=TEXT_DIM, line_width=1.2,
                  annotation_text=f"Média: {M4}%", annotation_font_color=TEXT_DIM)
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="% Deps. Vulneráveis por Ferramenta", font_size=13, x=0.01, xanchor="left"),
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_DIM, title="% deps. vulneráveis"),
        xaxis=dict(color=TEXT_DIM),
        showlegend=False,
    )
    return fig


def fig_bar_repos_vuln_abs(highlight_tool=None):
    opacities = [1.0 if (highlight_tool is None or t == highlight_tool) else 0.4
                 for t in tools_ordered]
    fig = go.Figure(go.Bar(
        x=tool_labels, y=repos_vuln_abs,
        marker=dict(color=[TOOL_COLORS[t] for t in tools_ordered], opacity=opacities),
        text=[f"{v:,}" for v in repos_vuln_abs], textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:,} repos com ≥1 vuln<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Repos com ≥1 Vuln por Ferramenta (absoluto)", font_size=13, x=0.01, xanchor="left"),
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_DIM, title="Número de repositórios"),
        xaxis=dict(color=TEXT_DIM),
        showlegend=False,
    )
    return fig


def fig_rq3_comparison():
    """Bar chart comparing 'Com Bot' vs 'Sem Bot' % vulnerable deps."""
    labels = ["Com Bot (qualquer)", "Sem Bot"]
    values = [any_bot_pct, none_pct_rq3]
    colors = [ACCENT3, TOOL_COLORS["none"]]
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=colors),
        text=[f"{v:.1f}%" for v in values], textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:.2f}% deps. vulneráveis<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="% Deps. Vulneráveis: Bot vs Sem Bot", font_size=13, x=0.01, xanchor="left"),
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_DIM, title="% deps. vulneráveis"),
        xaxis=dict(color=TEXT_DIM),
        showlegend=False,
    )
    return fig


def fig_rq4_cat_vuln_pct():
    """Bar chart of pct_vulnerable_deps by category."""
    cats_no_none = [c for c in cats_ordered if c != "none"]
    labels_no_none = [CAT_LABELS[c] for c in cats_no_none]
    values_no_none = [pct(int(cat_data[c]["vulnerable_dependencies"]),
                          int(cat_data[c]["total_direct_dependencies"]))
                      for c in cats_no_none]
    colors = [CAT_COLORS[c] for c in cats_no_none]
    fig = go.Figure(go.Bar(
        x=labels_no_none, y=values_no_none,
        marker=dict(color=colors),
        text=[f"{v:.1f}%" for v in values_no_none], textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:.2f}% deps. vulneráveis<extra></extra>",
    ))
    fig.add_hline(y=none_pct_rq3, line_dash="dash", line_color=TOOL_COLORS["none"], line_width=1.5,
                  annotation_text=f"Sem Bot: {none_pct_rq3}%", annotation_font_color=TOOL_COLORS["none"])
    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="% Deps. Vulneráveis por Categoria de Bot", font_size=13, x=0.01, xanchor="left"),
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_DIM, title="% deps. vulneráveis"),
        xaxis=dict(color=TEXT_DIM),
        showlegend=False,
    )
    return fig


def fig_rq4_severity_by_cat():
    """Stacked bar of severity distribution by category (excluding none)."""
    cats_no_none = [c for c in cats_ordered if c != "none"]
    labels_no_none = [CAT_LABELS[c] for c in cats_no_none]
    fig = go.Figure()
    for s in sev_labels:
        vals = [sev_by_cat.get(c, {}).get(s, 0) for c in cats_no_none]
        fig.add_trace(go.Bar(
            name=s, x=labels_no_none, y=vals,
            marker_color=SEV_COLORS[s],
            hovertemplate=f"<b>%{{x}}</b><br>{s}: %{{y:.1f}}%<extra></extra>",
        ))
    fig.update_layout(
        **BASE_LAYOUT,
        barmode="stack",
        title=dict(text="Distribuição de Severidade por Categoria", font_size=13, x=0.01, xanchor="left"),
        yaxis=dict(gridcolor=GRID_COLOR, color=TEXT_DIM, title="% dos CVEs"),
        xaxis=dict(color=TEXT_DIM),
        legend=dict(orientation="h", y=-0.25, x=0.5, xanchor="center"),
    )
    return fig


# ─── Layout helpers ───────────────────────────────────────────────────────────
def kpi_card(value, label, color, sub=None):
    children = [
        html.Div(value, style={
            "color": color, "fontSize": "26px", "fontWeight": "bold",
            "letterSpacing": "-0.5px",
        }),
        html.Div(label, style={
            "color": TEXT_DIM, "fontSize": "10px", "marginTop": "5px",
            "textAlign": "center", "whiteSpace": "pre-line", "lineHeight": "1.4",
        }),
    ]
    if sub:
        children.append(html.Div(sub, style={
            "color": TEXT_DIM, "fontSize": "9px", "marginTop": "3px",
            "fontStyle": "italic",
        }))
    return html.Div(children, style={
        "backgroundColor": PANEL_BG,
        "border": f"1.5px solid {color}",
        "borderRadius": "12px",
        "padding": "18px 12px",
        "textAlign": "center",
        "flex": "1",
        "minWidth": "130px",
        "transition": "transform 0.2s, box-shadow 0.2s",
    })


def section_hdr(label, color):
    return html.Div(label, style={
        "color": color, "fontSize": "13px", "fontWeight": "bold",
        "margin": "8px 20px 8px",
        "paddingLeft": "12px",
        "borderLeft": f"4px solid {color}",
        "lineHeight": "1.8",
    })


def chart_row(*graphs, padding="0 20px 14px"):
    return html.Div(list(graphs), style={
        "display": "flex", "gap": "14px", "padding": padding,
    })


def chart_card(fig, graph_id, height="310px"):
    return html.Div(
        dcc.Graph(
            figure=fig, id=graph_id,
            config={"displayModeBar": "hover", "displaylogo": False},
            style={"height": height},
        ),
        style={
            "backgroundColor": PANEL_BG, "borderRadius": "10px",
            "padding": "4px", "flex": "1", "minWidth": "0",
        },
    )


# ─── App ──────────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    title="CVE Dashboard — Node.js",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.layout = html.Div([

    # ── Header ────────────────────────────────────────────────────────────────
    html.Div([
        html.H1(
            "CVE Dependency Analysis — Node.js GitHub Projects",
            style={"color": TEXT_MAIN, "fontSize": "21px", "fontWeight": "bold",
                   "margin": "0", "letterSpacing": "-0.3px"},
        ),
        html.P(
            "Sprint 3 · Lab04S03 — PUC Minas — Gustavo Delfino & Matheus Caetano · 2026",
            style={"color": TEXT_DIM, "fontSize": "11px", "margin": "5px 0 0"},
        ),
        # Filtro de ferramenta (afeta RQ3 charts)
        html.Div([
            html.Span("Filtrar por ferramenta: ",
                      style={"color": TEXT_DIM, "fontSize": "11px", "marginRight": "8px"}),
            dcc.Dropdown(
                id="filter-tool",
                options=[{"label": TOOL_LABELS[t], "value": t} for t in tools_ordered],
                placeholder="Todas as ferramentas",
                clearable=True,
                style={
                    "width": "220px", "fontSize": "12px",
                    "backgroundColor": PANEL_BG, "color": DARK_BG,
                    "border": f"1px solid {GRID_COLOR}", "borderRadius": "8px",
                },
            ),
        ], style={"display": "flex", "alignItems": "center", "marginTop": "10px",
                  "justifyContent": "center"}),
    ], style={"textAlign": "center", "padding": "22px 20px 14px",
              "borderBottom": f"1px solid {GRID_COLOR}"}),

    # ── KPIs ──────────────────────────────────────────────────────────────────
    html.Div([
        kpi_card(f"{M1:,}",          "Repositórios\nanalisados (M1)",        ACCENT1),
        kpi_card(f"{M2:,}",          "Dependências\ndiretas (M2)",            ACCENT1),
        kpi_card(f"{M3:,}",          "Deps. com ≥1 CVE\n(M3)",               ACCENT4),
        kpi_card(f"{M4}%",           "% Deps.\nvulneráveis (M4)",             ACCENT4, "~43 em cada 100"),
        kpi_card(f"{total_cves:,}",  "Total de CVEs\nmapeados",               ACCENT2),
        kpi_card(f"{M5}%",           "Deps. vuln. com\nfix disponível (M5)",  ACCENT3, "fix já existe"),
    ], style={"display": "flex", "gap": "14px", "padding": "16px 20px 10px"}),

    # ── Caracterização ────────────────────────────────────────────────────────
    section_hdr("Caracterização do Dataset", ACCENT1),
    chart_row(
        chart_card(fig_donut_tool(),       "chart-donut-tool"),
        chart_card(fig_bar_deps_by_tool(), "chart-bar-deps"),
        chart_card(fig_bar_dep_kind(),     "chart-bar-kind"),
    ),

    # ── RQ1 ───────────────────────────────────────────────────────────────────
    section_hdr("RQ1 — Qual a frequência de dependências vulneráveis em projetos Node.js?", ACCENT1),
    html.P(
        "Investigamos a proporção de dependências diretas com ao menos uma CVE registrada, "
        "a disponibilidade de correções e a distribuição do número de CVEs por repositório.",
        style={"color": TEXT_DIM, "fontSize": "11px", "margin": "0 24px 10px",
               "lineHeight": "1.5"},
    ),
    chart_row(
        chart_card(fig_donut_vuln(),           "chart-donut-vuln"),
        chart_card(fig_bar_repos_vuln_pct(),   "chart-bar-repos-vuln"),
        chart_card(fig_donut_fix(),            "chart-donut-fix"),
    ),
    # KPIs complementares RQ1
    html.Div([
        kpi_card(f"{repo_cve_median:.0f}", "Mediana CVEs\npor repo", ACCENT1),
        kpi_card(f"{repo_cve_mean:.1f}", "Média CVEs\npor repo", ACCENT1),
        kpi_card(f"Q1={repo_cve_q1:.0f}", "1º Quartil\nCVEs/repo", TEXT_DIM),
        kpi_card(f"Q3={repo_cve_q3:.0f}", "3º Quartil\nCVEs/repo", TEXT_DIM),
        kpi_card(f"{len(repo_cve_counter):,}", "Repos com\n≥1 CVE", ACCENT4),
    ], style={"display": "flex", "gap": "14px", "padding": "6px 20px 14px"}),

    # ── RQ2 ───────────────────────────────────────────────────────────────────
    section_hdr("RQ2 — Qual a distribuição de severidade (CVSS) das CVEs encontradas?", ACCENT2),
    html.P(
        "Analisamos o perfil de severidade das vulnerabilidades identificadas usando scores CVSS, "
        "comparando a distribuição entre tipos de dependência e ferramentas de segurança.",
        style={"color": TEXT_DIM, "fontSize": "11px", "margin": "0 24px 10px",
               "lineHeight": "1.5"},
    ),
    chart_row(
        chart_card(fig_bar_severity(),       "chart-bar-sev"),
        chart_card(fig_donut_severity(),     "chart-donut-sev"),
        chart_card(fig_stacked_sev_by_tool(), "chart-stacked-sev"),
    ),
    # KPIs complementares RQ2
    html.Div([
        kpi_card(f"{cvss_median:.1f}", "Mediana\nScore CVSS", ACCENT2),
        kpi_card(f"{cvss_mean:.1f}", "Média\nScore CVSS", ACCENT2),
        kpi_card(f"{M7}%", "HIGH + CRITICAL\n(M7)", ACCENT4),
        kpi_card(f"{len(cvss_scores):,}", "CVEs com\nscore CVSS", TEXT_DIM),
        kpi_card(f"{total_sev:,}", "Total CVEs\nanalisados", ACCENT2),
    ], style={"display": "flex", "gap": "14px", "padding": "6px 20px 14px"}),

    # ── RQ3 ───────────────────────────────────────────────────────────────────
    section_hdr("RQ3 — A utilização de bots está associada a menor incidência de vulnerabilidades?", ACCENT3),
    html.P(
        "Comparamos a taxa de dependências vulneráveis em repositórios que utilizam "
        "qualquer ferramenta automatizada (bot) versus repositórios sem nenhuma ferramenta.",
        style={"color": TEXT_DIM, "fontSize": "11px", "margin": "0 24px 10px",
               "lineHeight": "1.5"},
    ),
    chart_row(
        chart_card(fig_rq3_comparison(),     "chart-rq3-comparison"),
        chart_card(fig_bar_tool_vuln_pct(),  "chart-bar-tool-vuln"),
        chart_card(fig_bar_repos_vuln_abs(), "chart-bar-repos-abs"),
    ),
    # KPIs RQ3
    html.Div([
        kpi_card(f"{any_bot_pct:.1f}%", "% Vuln.\nCom Bot", ACCENT3),
        kpi_card(f"{none_pct_rq3:.1f}%", "% Vuln.\nSem Bot", ACCENT4),
        kpi_card(f"−{rq3_diff} p.p.", "Diferença\n(Sem − Com)", ACCENT3),
        kpi_card(f"{any_bot_repos:,}", "Repos\ncom bot", ACCENT1),
        kpi_card(f"{int(none_row['repos']):,}", "Repos\nsem bot", TEXT_DIM),
    ], style={"display": "flex", "gap": "14px", "padding": "6px 20px 14px"}),

    # ── RQ4 ───────────────────────────────────────────────────────────────────
    section_hdr("RQ4 — Existem diferenças entre categorias de bots quanto ao impacto nas vulnerabilidades?", ACCENT2),
    html.P(
        "Agrupamos as ferramentas em categorias funcionais e comparamos a taxa de dependências "
        "vulneráveis e a distribuição de severidade entre elas.",
        style={"color": TEXT_DIM, "fontSize": "11px", "margin": "0 24px 10px",
               "lineHeight": "1.5"},
    ),
    chart_row(
        chart_card(fig_rq4_cat_vuln_pct(),     "chart-rq4-cat-vuln"),
        chart_card(fig_rq4_severity_by_cat(),  "chart-rq4-sev-cat"),
    ),
    # KPIs RQ4
    html.Div([
        kpi_card(f"{min(v for c, v in zip(cats_ordered, cat_vuln_pct) if c != 'none'):.1f}%",
                 "Menor %\n(Update)", ACCENT3),
        kpi_card(f"{max(v for c, v in zip(cats_ordered, cat_vuln_pct) if c != 'none'):.1f}%",
                 "Maior %\n(Sec. Automation)", ACCENT4),
        kpi_card(f"{max(cat_vuln_pct) - min(v for c, v in zip(cats_ordered, cat_vuln_pct) if c != 'none'):.1f} p.p.",
                 "Amplitude\nentre categorias", ACCENT2),
        kpi_card("6", "Categorias\nde bot", ACCENT1),
    ], style={"display": "flex", "gap": "14px", "padding": "6px 20px 14px"}),

    # Footer
    html.Div(
        f"Total de {total_cves:,} CVEs analisados em {M1:,} repositórios Node.js · PUC Minas 2026",
        style={"color": TEXT_DIM, "fontSize": "10px", "textAlign": "center",
               "padding": "16px", "borderTop": f"1px solid {GRID_COLOR}"},
    ),

], style={
    "backgroundColor": DARK_BG,
    "minHeight": "100vh",
    "fontFamily": "'Inter', 'Roboto', sans-serif",
})


# ─── Callbacks ────────────────────────────────────────────────────────────────
@app.callback(
    Output("chart-bar-tool-vuln",  "figure"),
    Output("chart-bar-repos-abs",  "figure"),
    Input("filter-tool", "value"),
)
def update_rq3(selected_tool):
    return (
        fig_bar_tool_vuln_pct(highlight_tool=selected_tool),
        fig_bar_repos_vuln_abs(highlight_tool=selected_tool),
    )


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n  ✓ Dashboard disponível em: http://localhost:{args.port}")
    print("  Pressione Ctrl+C para parar.\n")
    app.run(debug=False, port=args.port, host="0.0.0.0")
