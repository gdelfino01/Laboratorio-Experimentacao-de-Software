import json
import csv
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "Dataset Original")
OUTPUT_DIR = os.path.join(BASE_DIR, "Dataset CSV")


def load_json(filename):
    with open(os.path.join(INPUT_DIR, filename), encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1. summary_package-lock.json  →  summary_by_tool.csv
#    Uma linha por ferramenta de segurança (dependabot, renovate, snyk, none)
# ---------------------------------------------------------------------------
def convert_summary():
    data = load_json("summary_package-lock.json")
    rows = []

    for tool, stats in data["by_dependency_bot"].items():
        sev = stats["cve_severity_distribution"]
        total_cves = stats["total_cves"]
        high_critical = sev.get("HIGH", 0) + sev.get("CRITICAL", 0)

        rows.append({
            "tool": tool,
            "repos": stats["repos"],
            "total_direct_dependencies": stats["total_direct_dependencies"],
            "total_resolved_versions": stats["total_resolved_versions"],
            "repos_with_any_vuln": stats["repos_with_any_vuln"],
            "vulnerable_dependencies": stats["vulnerable_dependencies"],
            "vulnerable_subdependencies": stats["vulnerable_subdependencies"],
            "total_cves": total_cves,
            "cve_low": sev.get("LOW", 0),
            "cve_medium": sev.get("MEDIUM", 0),
            "cve_high": sev.get("HIGH", 0),
            "cve_critical": sev.get("CRITICAL", 0),
            "cve_unknown": sev.get("UNKNOWN", 0),
            # M4: percentual de dependências vulneráveis
            "pct_vulnerable_deps": round(
                stats["vulnerable_dependencies"] / stats["total_direct_dependencies"] * 100, 2
            ) if stats["total_direct_dependencies"] else 0,
            # M7: Vulnerability Severity Score (crítica+alta / total CVEs)
            "severity_score_high_critical_pct": round(
                high_critical / total_cves * 100, 2
            ) if total_cves else 0,
        })

    out_path = os.path.join(OUTPUT_DIR, "summary_by_tool.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] summary_by_tool.csv  ({len(rows)} linhas)")


# ---------------------------------------------------------------------------
# 1b. summary_package-lock.json  →  summary_by_category.csv
#     Uma linha por categoria de bot (update, update_security, etc.)
# ---------------------------------------------------------------------------
def convert_summary_by_category():
    data = load_json("summary_package-lock.json")
    rows = []

    for category, stats in data["by_dependency_bot_category"].items():
        sev = stats["cve_severity_distribution"]
        total_cves = stats["total_cves"]
        high_critical = sev.get("HIGH", 0) + sev.get("CRITICAL", 0)

        rows.append({
            "category": category,
            "repos": stats["repos"],
            "total_direct_dependencies": stats["total_direct_dependencies"],
            "total_resolved_versions": stats["total_resolved_versions"],
            "repos_with_any_vuln": stats["repos_with_any_vuln"],
            "vulnerable_dependencies": stats["vulnerable_dependencies"],
            "vulnerable_subdependencies": stats["vulnerable_subdependencies"],
            "total_cves": total_cves,
            "cve_low": sev.get("LOW", 0),
            "cve_medium": sev.get("MEDIUM", 0),
            "cve_high": sev.get("HIGH", 0),
            "cve_critical": sev.get("CRITICAL", 0),
            "cve_unknown": sev.get("UNKNOWN", 0),
            "pct_vulnerable_deps": round(
                stats["vulnerable_dependencies"] / stats["total_direct_dependencies"] * 100, 2
            ) if stats["total_direct_dependencies"] else 0,
            "severity_score_high_critical_pct": round(
                high_critical / total_cves * 100, 2
            ) if total_cves else 0,
        })

    out_path = os.path.join(OUTPUT_DIR, "summary_by_category.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] summary_by_category.csv  ({len(rows)} linhas)")


# ---------------------------------------------------------------------------
# 2. vulnerable_dependencies.json  →  vulnerable_dependencies_flat.csv
#    Uma linha por par (repositório × dependência vulnerável × CVE)
# ---------------------------------------------------------------------------
def convert_vulnerable_dependencies():
    data = load_json("vulnerable_dependencies.json")
    rows = []

    for entry in data["results"]:
        dep = entry["dependency"]
        cve_details = entry.get("details", {}).get("cve_details", [])

        if not cve_details:
            # Registra a dependência sem CVE detalhado (só OSV)
            rows.append({
                "repo_full_name": entry["repo_full_name"],
                "repo_html_url": entry["repo_html_url"],
                "dep_name": dep["name"],
                "dep_resolved_version": dep["resolved_version"],
                "dep_spec": dep["spec"],
                "dep_kind": dep["kind"],
                "is_subdependency": dep["is_subdependency"],
                "parent_dependency": dep.get("parent_dependency") or "",
                "cve_id": "",
                "cvss_base_score": "",
                "severity": "",
                "fix_available": entry.get("fix_available", ""),
                "latest_version": entry.get("latest_version", ""),
            })
        else:
            for cve in cve_details:
                rows.append({
                    "repo_full_name": entry["repo_full_name"],
                    "repo_html_url": entry["repo_html_url"],
                    "dep_name": dep["name"],
                    "dep_resolved_version": dep["resolved_version"],
                    "dep_spec": dep["spec"],
                    "dep_kind": dep["kind"],
                    "is_subdependency": dep["is_subdependency"],
                    "parent_dependency": dep.get("parent_dependency") or "",
                    "cve_id": cve.get("cve_id", ""),
                    "cvss_base_score": cve.get("cvss_base_score", ""),
                    "severity": cve.get("severity", ""),
                    "fix_available": entry.get("fix_available", ""),
                    "latest_version": entry.get("latest_version", ""),
                })

    out_path = os.path.join(OUTPUT_DIR, "vulnerable_dependencies_flat.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] vulnerable_dependencies_flat.csv  ({len(rows)} linhas)")


# ---------------------------------------------------------------------------
# 3. dependencies_with_vulnerabilites.json  →  deps_with_vulns_flat.csv
#    Uma linha por par (repositório × dependência × OSV advisory × CVE)
# ---------------------------------------------------------------------------
def convert_dependencies_with_vulnerabilities():
    data = load_json("dependencies_with_vulnerabilites.json")
    rows = []

    for repo in data["results"]:
        repo_path = repo["repo_path"]
        # Extrai "owner/repo" do caminho completo
        repo_name = "/".join(repo_path.rstrip("/").split("/")[-2:])

        for vuln in repo["vulnerabilities"]:
            dep = vuln["dependency"]
            osv_list = vuln.get("osv", [])

            if not osv_list:
                rows.append({
                    "repo_name": repo_name,
                    "dep_name": dep["name"],
                    "dep_version": dep["version"],
                    "dep_dev": dep["dev"],
                    "parent_dependency": dep.get("parent_dependency") or "",
                    "osv_id": "",
                    "osv_summary": "",
                    "cve_ids": "",
                    "has_nvd_link": False,
                })
            else:
                for osv in osv_list:
                    rows.append({
                        "repo_name": repo_name,
                        "dep_name": dep["name"],
                        "dep_version": dep["version"],
                        "dep_dev": dep["dev"],
                        "parent_dependency": dep.get("parent_dependency") or "",
                        "osv_id": osv.get("osv_id", ""),
                        "osv_summary": osv.get("summary", ""),
                        "cve_ids": "; ".join(osv.get("cves", [])),
                        "has_nvd_link": len(osv.get("nvd", [])) > 0,
                    })

    out_path = os.path.join(OUTPUT_DIR, "deps_with_vulns_flat.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] deps_with_vulns_flat.csv  ({len(rows)} linhas)")


if __name__ == "__main__":
    convert_summary()
    convert_summary_by_category()
    convert_vulnerable_dependencies()
    convert_dependencies_with_vulnerabilities()
    print("\nTodos os CSVs gerados com sucesso.")
