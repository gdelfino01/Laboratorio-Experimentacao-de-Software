import json

d = json.load(open('Dataset Original/summary_package-lock.json'))

# Check by_dependency_bot_category
cats = d['by_dependency_bot_category']
total = sum(v['repos'] for v in cats.values())
print(f"Soma repos por categoria: {total}")
print(f"Total repos: {d['total_repos']}")
print()
print("=== Categorias de bot ===")
for k, v in cats.items():
    pct = round(v['vulnerable_dependencies'] / v['total_direct_dependencies'] * 100, 2)
    print(f"  {k}: {v['repos']} repos, deps={v['total_direct_dependencies']}, vuln={v['vulnerable_dependencies']}, pct_vuln={pct}%")

print()
print("=== Mapeamento bot -> categoria ===")
for bot, cat_list in d['dependency_bot_categories'].items():
    print(f"  {bot} -> {cat_list}")

# Check with_dependabot (top-level field that may include overlap)
wd = d.get('with_dependabot', {})
print(f"\nwith_dependabot.repos = {wd.get('repos', 'N/A')}")
print(f"by_dependency_bot.dependabot.repos = {d['by_dependency_bot']['dependabot']['repos']}")
