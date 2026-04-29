from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GRAPHQL_URL = "https://api.github.com/graphql"

DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_SELECTED_REPOS_CSV = DEFAULT_OUTPUT_DIR / "selected_repositories_top200.csv"
DEFAULT_PRS_CSV = DEFAULT_OUTPUT_DIR / "pull_requests_review_dataset.csv"
DEFAULT_SUMMARY_CSV = DEFAULT_OUTPUT_DIR / "sprint2_summary_stats.csv"
DEFAULT_DRAFT_REPORT_MD = Path("RELATORIO.md")

DEFAULT_TARGET_REPOSITORIES = 200
DEFAULT_MIN_REPO_PRS = 100
DEFAULT_REPO_PAGE_SIZE = 25
DEFAULT_PR_PAGE_SIZE = 50

DEFAULT_REPO_SLEEP_SECONDS = 1.0
DEFAULT_PR_SLEEP_SECONDS = 0.2

# We keep this broad and rank by stars so the script can find popular projects in general.
DEFAULT_REPOSITORY_SEARCH_QUERY = "stars:>100 sort:stars-desc"

REPOSITORY_SELECTION_FIELDS = [
    "selection_rank",
    "name_with_owner",
    "url",
    "stars",
    "merged_prs",
    "closed_prs",
    "total_merged_closed_prs",
    "meets_min_prs",
]

PR_DATASET_FIELDS = [
    "repo_rank",
    "repo_name_with_owner",
    "repo_url",
    "pr_number",
    "pr_url",
    "pr_state",
    "created_at",
    "closed_at",
    "merged_at",
    "final_activity_at",
    "analysis_time_hours",
    "changed_files",
    "additions",
    "deletions",
    "total_lines_changed",
    "description_length",
    "participants_count",
    "comments_count",
    "reviews_count",
]

SUMMARY_FIELDS = [
    "group",
    "metric",
    "count",
    "median",
    "mean",
    "min",
    "max",
]

REPOSITORY_SELECTION_QUERY = """
query ($queryString: String!, $pageSize: Int!, $cursor: String) {
  rateLimit {
    cost
    remaining
    resetAt
  }
  search(query: $queryString, type: REPOSITORY, first: $pageSize, after: $cursor) {
    pageInfo {
      endCursor
      hasNextPage
    }
    nodes {
      ... on Repository {
        nameWithOwner
        url
        stargazerCount
        mergedPullRequests: pullRequests(states: MERGED) {
          totalCount
        }
        closedPullRequests: pullRequests(states: CLOSED) {
          totalCount
        }
      }
    }
  }
}
"""

PULL_REQUESTS_QUERY = """
query (
  $owner: String!,
  $name: String!,
  $state: PullRequestState!,
  $pageSize: Int!,
  $cursor: String
) {
  repository(owner: $owner, name: $name) {
    pullRequests(
      states: [$state],
      first: $pageSize,
      after: $cursor,
      orderBy: {field: CREATED_AT, direction: DESC}
    ) {
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes {
        number
        url
        state
        createdAt
        closedAt
        mergedAt
        changedFiles
        additions
        deletions
        body
        participants {
          totalCount
        }
        comments {
          totalCount
        }
        reviews {
          totalCount
        }
      }
    }
  }
}
"""
