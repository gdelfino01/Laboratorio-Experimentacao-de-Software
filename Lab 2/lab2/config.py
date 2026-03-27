from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GRAPHQL_URL = "https://api.github.com/graphql"
SEARCH_QUERY = "language:Java stars:>100 sort:stars-desc"
DEFAULT_TOTAL_REPOS = 1000
DEFAULT_PAGE_SIZE = 25
DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_WORKSPACE_DIR = Path("w")
DEFAULT_CK_DIR = Path("tools") / "ck"

QUERY = """
query ($queryString: String!, $pageSize: Int!, $cursor: String) {
  rateLimit {
    cost
    remaining
    resetAt
  }
  search(query: $queryString, type: REPOSITORY, first: $pageSize, after: $cursor) {
    repositoryCount
    pageInfo {
      endCursor
      hasNextPage
    }
    nodes {
      ... on Repository {
        nameWithOwner
        url
        createdAt
        stargazerCount
        forkCount
        watchers {
          totalCount
        }
        releases {
          totalCount
        }
        isArchived
        isFork
      }
    }
  }
}
"""
