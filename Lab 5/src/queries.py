"""Paired REST × GraphQL query definitions.

Each `QueryPair` describes one experimental object: a REST endpoint and a
GraphQL query that retrieve essentially the same fields about the same
resource. The GraphQL field selections were authored to mirror the default
response shape of the corresponding REST endpoint so the two payloads are as
comparable as possible.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List

from . import config


@dataclass(frozen=True)
class QueryPair:
    """One paired (REST, GraphQL) treatment over the same logical resource."""

    query_id: str
    label: str
    rest_endpoint: str        # URL path (relative to REST_BASE_URL)
    graphql_query: str
    graphql_variables: Dict[str, object]


# ─── Q1: Single user ─────────────────────────────────────────────────────────
Q1_GRAPHQL = """
query ($login: String!) {
  user(login: $login) {
    login
    name
    company
    blog
    location
    email
    bio
    twitterUsername
    avatarUrl
    url
    createdAt
    updatedAt
    repositories { totalCount }
    followers   { totalCount }
    following   { totalCount }
    gists       { totalCount }
  }
}
""".strip()

# ─── Q2: Single repository ───────────────────────────────────────────────────
Q2_GRAPHQL = """
query ($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    id
    name
    nameWithOwner
    description
    homepageUrl
    url
    isFork
    isArchived
    isPrivate
    isTemplate
    diskUsage
    forkCount
    stargazerCount
    watchers { totalCount }
    primaryLanguage { name }
    licenseInfo     { spdxId name }
    defaultBranchRef { name }
    createdAt
    updatedAt
    pushedAt
    issues       { totalCount }
    pullRequests { totalCount }
  }
}
""".strip()

# ─── Q3: List of a user's repositories (page of 30) ──────────────────────────
Q3_GRAPHQL = """
query ($login: String!, $first: Int!) {
  user(login: $login) {
    repositories(first: $first, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        id
        name
        nameWithOwner
        description
        url
        isFork
        isPrivate
        forkCount
        stargazerCount
        primaryLanguage { name }
        licenseInfo     { spdxId }
        createdAt
        updatedAt
        pushedAt
      }
    }
  }
}
""".strip()

# ─── Q4: List of a repository's issues (page of 30) ──────────────────────────
Q4_GRAPHQL = """
query ($owner: String!, $name: String!, $first: Int!) {
  repository(owner: $owner, name: $name) {
    issues(first: $first, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        id
        number
        title
        state
        url
        author { login }
        createdAt
        updatedAt
        closedAt
        comments { totalCount }
        labels(first: 20) { nodes { name } }
        milestone        { title }
      }
    }
  }
}
""".strip()

# ─── Q5: List of a repository's pull requests (page of 30) ───────────────────
Q5_GRAPHQL = """
query ($owner: String!, $name: String!, $first: Int!) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: $first, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        id
        number
        title
        state
        url
        author { login }
        createdAt
        updatedAt
        closedAt
        mergedAt
        isDraft
        comments { totalCount }
        commits  { totalCount }
        labels(first: 20) { nodes { name } }
        baseRefName
        headRefName
      }
    }
  }
}
""".strip()


def build_pairs() -> List[QueryPair]:
    """Materialize the five paired queries with the configured target objects."""
    return [
        QueryPair(
            query_id="Q1",
            label="user_profile",
            rest_endpoint=f"/users/{config.TARGET_USER_LOGIN}",
            graphql_query=Q1_GRAPHQL,
            graphql_variables={"login": config.TARGET_USER_LOGIN},
        ),
        QueryPair(
            query_id="Q2",
            label="repository_metadata",
            rest_endpoint=f"/repos/{config.TARGET_REPO_OWNER}/{config.TARGET_REPO_NAME}",
            graphql_query=Q2_GRAPHQL,
            graphql_variables={
                "owner": config.TARGET_REPO_OWNER,
                "name": config.TARGET_REPO_NAME,
            },
        ),
        QueryPair(
            query_id="Q3",
            label="user_repositories_list",
            rest_endpoint=(
                f"/users/{config.TARGET_USER_LOGIN}/repos"
                f"?per_page={config.LIST_PAGE_SIZE}&sort=created&direction=desc"
            ),
            graphql_query=Q3_GRAPHQL,
            graphql_variables={
                "login": config.TARGET_USER_LOGIN,
                "first": config.LIST_PAGE_SIZE,
            },
        ),
        QueryPair(
            query_id="Q4",
            label="repository_issues_list",
            rest_endpoint=(
                f"/repos/{config.LIST_REPO_OWNER}/{config.LIST_REPO_NAME}/issues"
                f"?per_page={config.LIST_PAGE_SIZE}&state=all&sort=created&direction=desc"
            ),
            graphql_query=Q4_GRAPHQL,
            graphql_variables={
                "owner": config.LIST_REPO_OWNER,
                "name": config.LIST_REPO_NAME,
                "first": config.LIST_PAGE_SIZE,
            },
        ),
        QueryPair(
            query_id="Q5",
            label="repository_pull_requests_list",
            rest_endpoint=(
                f"/repos/{config.LIST_REPO_OWNER}/{config.LIST_REPO_NAME}/pulls"
                f"?per_page={config.LIST_PAGE_SIZE}&state=all&sort=created&direction=desc"
            ),
            graphql_query=Q5_GRAPHQL,
            graphql_variables={
                "owner": config.LIST_REPO_OWNER,
                "name": config.LIST_REPO_NAME,
                "first": config.LIST_PAGE_SIZE,
            },
        ),
    ]
