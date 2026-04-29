# Lab 3 - Code Review Activity on GitHub

This folder now covers:
- Sprint 1: repository selection + PR-level dataset collection
- Sprint 2: complete dataset generation + first draft of the final report with initial hypotheses

## Dataset filters

Repository constraints:
- popular repositories ranked by stars
- target size (default: 200)
- each repository must have at least 100 PRs considering MERGED + CLOSED

Pull request constraints:
- state in {MERGED, CLOSED}
- at least 1 review (`reviews.totalCount >= 1`)
- review process took more than 1 hour (`final_activity_at - created_at > 1h`)

Metrics collected per PR:
- size: changed files, additions, deletions, total lines changed
- analysis time: hours between creation and final activity
- description: body length in characters (markdown text)
- interactions: participants count, comments count
- review volume: reviews count

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Set token in `.env` (repo root or Lab 3 root):

```env
GITHUB_TOKEN="your_token_here"
```

## Commands

### Sprint 1 commands

Select repositories:

```bash
python main.py collect-repos \
  --target-repositories 200 \
  --min-repo-prs 100 \
  --output output/selected_repositories_top200.csv
```

Collect PR dataset:

```bash
python main.py collect-prs \
  --repos-csv output/selected_repositories_top200.csv \
  --output output/pull_requests_review_dataset.csv
```

Run Sprint 1 end-to-end:

```bash
python main.py sprint1 \
  --target-repositories 200 \
  --min-repo-prs 100 \
  --selected-repos-output output/selected_repositories_top200.csv \
  --prs-output output/pull_requests_review_dataset.csv
```

### Sprint 2 commands

Generate draft report from existing CSVs:

```bash
python main.py generate-report-draft \
  --repos-csv output/selected_repositories_top200.csv \
  --prs-csv output/pull_requests_review_dataset.csv \
  --summary-output output/sprint2_summary_stats.csv \
  --report-output RELATORIO.md
```

Run Sprint 2 end-to-end (collection + report draft):

```bash
python main.py sprint2 \
  --target-repositories 200 \
  --min-repo-prs 100 \
  --selected-repos-output output/selected_repositories_top200.csv \
  --prs-output output/pull_requests_review_dataset.csv \
  --summary-output output/sprint2_summary_stats.csv \
  --report-output RELATORIO.md
```

## Useful optional args

- `--search-query`: custom query to change repository scope
- `--max-prs-per-repo`: cap PRs per repository for smoke tests
- `--repo-limit`: only on `collect-prs`, reads first N repositories from CSV
- `--sleep-seconds`, `--repo-sleep-seconds`, `--pr-sleep-seconds`: request pacing

## Output artifacts

Repository list CSV (`selected_repositories_top200.csv`):
- `selection_rank`
- `name_with_owner`
- `url`
- `stars`
- `merged_prs`
- `closed_prs`
- `total_merged_closed_prs`
- `meets_min_prs`

PR dataset CSV (`pull_requests_review_dataset.csv`):
- `repo_rank`
- `repo_name_with_owner`
- `repo_url`
- `pr_number`
- `pr_url`
- `pr_state`
- `created_at`
- `closed_at`
- `merged_at`
- `final_activity_at`
- `analysis_time_hours`
- `changed_files`
- `additions`
- `deletions`
- `total_lines_changed`
- `description_length`
- `participants_count`
- `comments_count`
- `reviews_count`

Sprint 2 summary CSV (`sprint2_summary_stats.csv`):
- `group`
- `metric`
- `count`
- `median`
- `mean`
- `min`
- `max`

Sprint 2 report draft (`RELATORIO.md`):
- initial hypotheses (RQ01-RQ08)
- methodology and filters
- dataset coverage
- median summaries for all PRs, MERGED and CLOSED
