import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .config import PULL_REQUESTS_QUERY, REPOSITORY_SELECTION_QUERY
from .github_api import run_query


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def split_name_with_owner(name_with_owner: str) -> Tuple[str, str]:
    if "/" not in name_with_owner:
        raise ValueError(f"Invalid nameWithOwner: {name_with_owner}")
    owner, name = name_with_owner.split("/", 1)
    return owner, name


def _parse_iso_date(date_string: str) -> datetime:
    return datetime.fromisoformat(date_string.replace("Z", "+00:00"))


def _hours_between(start_date: Optional[str], end_date: Optional[str]) -> Optional[float]:
    if not start_date or not end_date:
        return None

    start = _parse_iso_date(start_date)
    end = _parse_iso_date(end_date)
    delta_seconds = (end - start).total_seconds()

    if delta_seconds < 0:
        return None

    return round(delta_seconds / 3600, 3)


def _final_activity_at(pr: Dict[str, Any]) -> Optional[str]:
    state = (pr.get("state") or "").upper()

    if state == "MERGED":
        return pr.get("mergedAt") or pr.get("closedAt")

    return pr.get("closedAt") or pr.get("mergedAt")


def fetch_selected_repositories(
    target_repositories: int,
    min_repo_prs: int,
    page_size: int,
    search_query: str,
    sleep_seconds: float,
) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    seen_names = set()
    cursor = None
    scanned = 0

    while len(selected) < target_repositories:
        variables = {
            "queryString": search_query,
            "pageSize": page_size,
            "cursor": cursor,
        }

        print(f"Scanning repositories... selected={len(selected)}/{target_repositories}")
        data = run_query(REPOSITORY_SELECTION_QUERY, variables)

        search_data = data["data"]["search"]
        rate_limit = data["data"].get("rateLimit", {})

        for node in search_data.get("nodes", []):
            if not node:
                continue

            name_with_owner = node.get("nameWithOwner")
            if not name_with_owner or name_with_owner in seen_names:
                continue

            seen_names.add(name_with_owner)
            scanned += 1

            merged_prs = _safe_int(node.get("mergedPullRequests", {}).get("totalCount"))
            closed_prs = _safe_int(node.get("closedPullRequests", {}).get("totalCount"))
            total_prs = merged_prs + closed_prs

            if total_prs < min_repo_prs:
                continue

            selected.append(
                {
                    "selection_rank": len(selected) + 1,
                    "name_with_owner": name_with_owner,
                    "url": node.get("url", ""),
                    "stars": _safe_int(node.get("stargazerCount")),
                    "merged_prs": merged_prs,
                    "closed_prs": closed_prs,
                    "total_merged_closed_prs": total_prs,
                    "meets_min_prs": True,
                }
            )

            if len(selected) >= target_repositories:
                break

        print(
            "   rate remaining:",
            rate_limit.get("remaining", "?"),
            "| cost:",
            rate_limit.get("cost", "?"),
            "| scanned:",
            scanned,
        )

        if len(selected) >= target_repositories:
            break

        if not search_data.get("pageInfo", {}).get("hasNextPage"):
            break

        cursor = search_data["pageInfo"].get("endCursor")
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    if len(selected) < target_repositories:
        print(
            f"Warning: only {len(selected)} repositories matched the constraints "
            f"(target was {target_repositories})."
        )

    return selected


def _build_pr_row(repo: Dict[str, Any], pr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    reviews_count = _safe_int(pr.get("reviews", {}).get("totalCount"))
    if reviews_count < 1:
        return None

    final_activity_at = _final_activity_at(pr)
    analysis_time_hours = _hours_between(pr.get("createdAt"), final_activity_at)
    if analysis_time_hours is None or analysis_time_hours <= 1.0:
        return None

    additions = _safe_int(pr.get("additions"))
    deletions = _safe_int(pr.get("deletions"))

    return {
        "repo_rank": _safe_int(repo.get("selection_rank") or repo.get("rank")),
        "repo_name_with_owner": repo.get("name_with_owner") or repo.get("nameWithOwner", ""),
        "repo_url": repo.get("url", ""),
        "pr_number": _safe_int(pr.get("number")),
        "pr_url": pr.get("url", ""),
        "pr_state": pr.get("state", ""),
        "created_at": pr.get("createdAt", ""),
        "closed_at": pr.get("closedAt", ""),
        "merged_at": pr.get("mergedAt", ""),
        "final_activity_at": final_activity_at or "",
        "analysis_time_hours": analysis_time_hours,
        "changed_files": _safe_int(pr.get("changedFiles")),
        "additions": additions,
        "deletions": deletions,
        "total_lines_changed": additions + deletions,
        "description_length": len(pr.get("body") or ""),
        "participants_count": _safe_int(pr.get("participants", {}).get("totalCount")),
        "comments_count": _safe_int(pr.get("comments", {}).get("totalCount")),
        "reviews_count": reviews_count,
    }


def fetch_pull_requests_dataset(
    selected_repositories: Iterable[Dict[str, Any]],
    pr_page_size: int,
    sleep_seconds: float,
    max_prs_per_repo: Optional[int] = None,
) -> List[Dict[str, Any]]:
    dataset: List[Dict[str, Any]] = []

    for repo in selected_repositories:
        name_with_owner = repo.get("name_with_owner") or repo.get("nameWithOwner")
        if not name_with_owner:
            continue

        owner, name = split_name_with_owner(name_with_owner)
        seen_pr_numbers = set()
        kept_for_repo = 0

        print(f"Collecting PRs for {name_with_owner}...")

        for state in ("MERGED", "CLOSED"):
            cursor = None

            while True:
                if max_prs_per_repo is not None and kept_for_repo >= max_prs_per_repo:
                    break

                variables = {
                    "owner": owner,
                    "name": name,
                    "state": state,
                    "pageSize": pr_page_size,
                    "cursor": cursor,
                }

                data = run_query(PULL_REQUESTS_QUERY, variables)
                repo_data = data.get("data", {}).get("repository")
                if not repo_data:
                    print(f"   Skipping {name_with_owner}: repository data unavailable")
                    break

                pr_connection = repo_data["pullRequests"]
                nodes = pr_connection.get("nodes", [])

                for pr in nodes:
                    if not pr:
                        continue

                    pr_number = _safe_int(pr.get("number"))
                    if pr_number in seen_pr_numbers:
                        continue

                    row = _build_pr_row(repo, pr)
                    if row is None:
                        continue

                    dataset.append(row)
                    seen_pr_numbers.add(pr_number)
                    kept_for_repo += 1

                    if max_prs_per_repo is not None and kept_for_repo >= max_prs_per_repo:
                        break

                if max_prs_per_repo is not None and kept_for_repo >= max_prs_per_repo:
                    break

                if not pr_connection.get("pageInfo", {}).get("hasNextPage"):
                    break

                cursor = pr_connection["pageInfo"].get("endCursor")
                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)

        print(f"   kept PRs for {name_with_owner}: {kept_for_repo}")

    print(f"Total PR rows collected: {len(dataset)}")
    return dataset
