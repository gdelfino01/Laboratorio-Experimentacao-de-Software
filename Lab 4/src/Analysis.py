import csv
import json
import argparse
from collections import Counter, defaultdict
from pathlib import Path


# ─── CLI ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Calcula métricas M1–M9 do estudo CVE/Node.js")
parser.add_argument("--data_dir", default=".", help="Diretório com os CSVs de entrada")
parser.add_argument("--output", default="metrics_output.json", help="Arquivo JSON de saída")
args = parser.parse_args()

DATA_DIR = Path(args.data_dir)


# ─── Funções auxiliares ───────────────────────────────────────────────────────
def read_csv(filename):
    path = DATA_DIR / filename
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pct(num, den):
    return round(num / den * 100, 2) if den else 0.0


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ─── Carrega dados ────────────────────────────────────────────────────────────
print("Carregando CSVs...")
vuln_flat   = read_csv("vulnerable_dependencies_flat.csv")
summary     = read_csv("summary_by_tool.csv")

try:
    deps_flat = read_csv("deps_with_vulns_flat.csv")
except FileNotFoundError:
    deps_flat = []
    print("  [AVISO] deps_with_vulns_flat.csv não encontrado — M2 vem do summary_by_tool")

print(f"  vulnerable_dependencies_flat : {len(vuln_flat):>8} linhas")
print(f"  deps_with_vulns_flat         : {len(deps_flat):>8} linhas")
print(f"  summary_by_tool              : {len(summary):>8} linhas")


# ─────────────────────────────────────────────────────────────────────────────
# M1 — Total de repositórios analisados
# ─────────────────────────────────────────────────────────────────────────────
section("M1 – Total de repositórios analisados")

M1 = sum(int(r["repos"]) for r in summary)
print(f"  M1 = {M1:,}")


# ─────────────────────────────────────────────────────────────────────────────
# M2 — Total de dependências diretas (package.json)
# ─────────────────────────────────────────────────────────────────────────────
section("M2 – Total de dependências diretas")

M2 = sum(int(r["total_direct_dependencies"]) for r in summary)
print(f"  M2 = {M2:,}")


# ─────────────────────────────────────────────────────────────────────────────
# M3 — Dependências com ≥ 1 CVE registrado
# ─────────────────────────────────────────────────────────────────────────────
section("M3 – Dependências com ≥ 1 CVE")

M3 = sum(int(r["vulnerable_dependencies"]) for r in summary)
print(f"  M3 = {M3:,}")


# ─────────────────────────────────────────────────────────────────────────────
# M4 — % dependências vulneráveis (M3 / M2)
# ─────────────────────────────────────────────────────────────────────────────
section("M4 – % Dependências vulneráveis")

M4 = pct(M3, M2)
print(f"  M4 = {M4}%  ({M3:,} / {M2:,})")


# ─────────────────────────────────────────────────────────────────────────────
# M5 — % dependências vulneráveis com fix disponível
# Fonte: vulnerable_dependencies_flat.csv, campo fix_available, is_subdependency==False
# ─────────────────────────────────────────────────────────────────────────────
section("M5 – % Dependências vulneráveis com fix disponível")

direct_vuln = [r for r in vuln_flat if r.get("is_subdependency", "False") == "False"]

# Agrupa por (repo, dep_name, dep_resolved_version) para contar instâncias únicas
dep_fix_map = defaultdict(set)
for r in direct_vuln:
    key = (r["repo_full_name"], r["dep_name"], r["dep_resolved_version"])
    dep_fix_map[key].add(r["fix_available"])

total_vuln_instances = len(dep_fix_map)
with_fix    = sum(1 for v in dep_fix_map.values() if "True"  in v)
without_fix = sum(1 for v in dep_fix_map.values() if "True" not in v)

M5 = pct(with_fix, total_vuln_instances)
print(f"  Instâncias únicas vulneráveis (diretas) : {total_vuln_instances:,}")
print(f"  Com fix disponível                       : {with_fix:,}")
print(f"  Sem fix disponível                       : {without_fix:,}")
print(f"  M5 = {M5}%")


# ─────────────────────────────────────────────────────────────────────────────
# M6 — Distribuição de CVEs por nível de severidade CVSS
# ─────────────────────────────────────────────────────────────────────────────
section("M6 – Distribuição de CVEs por severidade")

severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN", ""]
sev_counter = Counter(r["severity"].strip().upper() for r in vuln_flat)

# Normaliza vazio para UNKNOWN
sev_counter["UNKNOWN"] = sev_counter.get("UNKNOWN", 0) + sev_counter.pop("", 0)

total_cves_raw = sum(sev_counter.values())
M6 = {}
for sev in ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]:
    count = sev_counter.get(sev, 0)
    M6[sev] = {"count": count, "pct": pct(count, total_cves_raw)}
    print(f"  {sev:<10}: {count:>8,}  ({M6[sev]['pct']:>5.1f}%)")

print(f"  {'TOTAL':<10}: {total_cves_raw:>8,}")


# ─────────────────────────────────────────────────────────────────────────────
# M7 — Vulnerability Severity Score (crítico + alto / total CVEs)
# ─────────────────────────────────────────────────────────────────────────────
section("M7 – Vulnerability Severity Score")

high_crit = M6["HIGH"]["count"] + M6["CRITICAL"]["count"]
M7 = pct(high_crit, total_cves_raw)
print(f"  (CRITICAL + HIGH) = {high_crit:,}")
print(f"  Total CVEs        = {total_cves_raw:,}")
print(f"  M7 = {M7}%")


# ─────────────────────────────────────────────────────────────────────────────
# M8 — Repos com Dependabot que ainda têm dependências vulneráveis
# ─────────────────────────────────────────────────────────────────────────────
section("M8 – Repos com Dependabot que ainda têm vulns")

dep_row   = next((r for r in summary if r["tool"] == "dependabot"), None)
M8_repos  = int(dep_row["repos_with_any_vuln"]) if dep_row else 0
M8_total  = int(dep_row["repos"])                if dep_row else 0
M8_pct    = pct(M8_repos, M8_total)
print(f"  Repos Dependabot com ≥1 vuln : {M8_repos} de {M8_total} ({M8_pct}%)")


# ─────────────────────────────────────────────────────────────────────────────
# M9 — % deps. vulneráveis por grupo de ferramenta
# ─────────────────────────────────────────────────────────────────────────────
section("M9 – Comparação entre grupos (% deps. vulneráveis)")

M9 = {}
print(f"  {'Ferramenta':<15} {'Repos':>7} {'Deps. diretas':>15} {'Vuln. deps':>12} {'M4 (%)':>8}")
print(f"  {'-'*60}")
for r in summary:
    tool   = r["tool"]
    repos  = int(r["repos"])
    deps   = int(r["total_direct_dependencies"])
    vdeps  = int(r["vulnerable_dependencies"])
    p      = pct(vdeps, deps)
    M9[tool] = {"repos": repos, "total_deps": deps, "vuln_deps": vdeps, "pct_vuln": p}
    print(f"  {tool:<15} {repos:>7,} {deps:>15,} {vdeps:>12,} {p:>7.2f}%")

# Diferença Dependabot vs None
if "dependabot" in M9 and "none" in M9:
    diff = round(M9["none"]["pct_vuln"] - M9["dependabot"]["pct_vuln"], 2)
    print(f"\n  Diferença (none - dependabot) = {diff} p.p.")


# ─────────────────────────────────────────────────────────────────────────────
# Análise de double counting
# ─────────────────────────────────────────────────────────────────────────────
section("Verificação de consistência / double counting")

repos_by_tool = {r["tool"]: int(r["repos"]) for r in summary}
total_by_group = sum(repos_by_tool.values())
print(f"  Soma dos grupos (by_tool) : {total_by_group:,}")
print(f"  M1 (total_repos)          : {M1:,}")
if total_by_group == M1:
    print("  ✓ Grupos mutuamente exclusivos — sem double counting")
else:
    print(f"  ⚠ Diferença de {abs(total_by_group - M1)} repos — investigar sobreposição de grupos")

unique_repos_in_vuln = len(set(r["repo_full_name"] for r in vuln_flat))
print(f"\n  Repos únicos em vulnerable_dependencies_flat : {unique_repos_in_vuln:,}")
print(f"  Repos com alguma vuln (sum summary)          : {sum(int(r['repos_with_any_vuln']) for r in summary):,}")


#    
# Exporta resultados
# ─────────────────────────────────────────────────────────────────────────────
output = {
    "M1_total_repos": M1,
    "M2_total_direct_deps": M2,
    "M3_deps_with_cve": M3,
    "M4_pct_vuln_deps": M4,
    "M5_pct_vuln_with_fix": M5,
    "M6_severity_distribution": M6,
    "M7_severity_score_high_critical": M7,
    "M8_dependabot_repos_with_vuln": {"count": M8_repos, "total": M8_total, "pct": M8_pct},
    "M9_by_tool": M9,
}

output_path = Path(args.output)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n{'='*60}")
print(f"  Métricas exportadas para: {output_path}")
print('='*60)