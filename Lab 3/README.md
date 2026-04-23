# Lab 3

1. Build the list of selected repositories.
2. Create the pull request dataset with the required metrics.

Repository selection constraints:
- top popular repositories by stars
- exactly target size (default: 200)
- each repository must have at least 100 PRs considering MERGED + CLOSED

Pull request selection constraints:
- state in {MERGED, CLOSED}
- at least 1 review (`reviews.totalCount >= 1`)
- review process took more than 1 hour (`final_activity_at - created_at > 1h`)

Metrics collected per PR:
- size: changed files, additions, deletions, total lines changed
- analysis time: hours between creation and final activity
- description: body length in characters (markdown text)
- interactions: participants count, comments count
- number of reviews: reviews count

## Files

- `main.py`: entrypoint
- `lab3/cli.py`: command line interface
- `lab3/config.py`: constants and GraphQL queries
- `lab3/github_api.py`: GitHub GraphQL client with retry/backoff
- `lab3/github_data.py`: data collection and filtering logic
- `lab3/io_utils.py`: CSV read/write helpers

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure token exists in `.env` (project root or Lab 3 root):

```env
GITHUB_TOKEN="your_token_here"
```

## Commands

### 1) Select repositories (default target: 200)

```bash
python main.py collect-repos \
  --target-repositories 200 \
  --min-repo-prs 100 \
  --output output/selected_repositories_top200.csv
```

### 2) Collect PR dataset from selected repositories

```bash
python main.py collect-prs \
  --repos-csv output/selected_repositories_top200.csv \
  --output output/pull_requests_review_dataset.csv
```

### 3) Run Sprint 1 end-to-end

```bash
python main.py sprint1 \
  --target-repositories 200 \
  --min-repo-prs 100 \
  --selected-repos-output output/selected_repositories_top200.csv \
  --prs-output output/pull_requests_review_dataset.csv
```

## Useful optional args

- `--search-query`: custom query to change repository scope
- `--max-prs-per-repo`: cap PRs per repository for smoke tests
- `--repo-limit`: only on `collect-prs`, reads first N repositories from CSV
- `--sleep-seconds`, `--repo-sleep-seconds`, `--pr-sleep-seconds`: request pacing

## Output CSV schema

Selected repositories CSV (`selected_repositories_top200.csv`):
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
