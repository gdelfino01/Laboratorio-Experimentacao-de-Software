import csv
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .config import (
    DEFAULT_PRS_CSV,
    DEFAULT_REPO_FAILURES_CSV,
    PR_DATASET_FIELDS,
    PULL_REQUESTS_QUERY,
    REPOSITORY_SELECTION_QUERY,
)
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

            merged_prs_data = node.get("mergedPullRequests") or {}
            merged_prs = _safe_int(merged_prs_data.get("totalCount"))
            
            closed_prs_data = node.get("closedPullRequests") or {}
            closed_prs = _safe_int(closed_prs_data.get("totalCount"))
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
    reviews_data = pr.get("reviews") or {}
    reviews_count = _safe_int(reviews_data.get("totalCount"))
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
        "participants_count": _safe_int((pr.get("participants") or {}).get("totalCount")),
        "comments_count": _safe_int((pr.get("comments") or {}).get("totalCount")),
        "reviews_count": reviews_count,
    }


def _append_failure_row(failure_path: Path, repo_name: str, error_message: str) -> None:
    failure_path = Path(failure_path)
    failure_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not failure_path.exists()

    with failure_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["repo_name_with_owner", "error_message"],
            extrasaction="ignore",
        )
        if write_header:
            writer.writeheader()
        writer.writerow({"repo_name_with_owner": repo_name, "error_message": error_message})


def fetch_pull_requests_dataset(
    selected_repositories: Iterable[Dict[str, Any]],
    pr_page_size: int,
    sleep_seconds: float,
    max_prs_per_repo: Optional[int] = None,
    output_path: Optional[Path] = None,
    checkpoint_path: Optional[Path] = None,
    failure_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Fetch PR dataset with optional incremental saving and checkpointing.

    This writes per-repo results to `output_path` after each repository is
    processed and stores processed repository names in `checkpoint_path`.
    If a checkpoint file exists, already-processed repositories are skipped.
    """

    dataset: List[Dict[str, Any]] = []

    output_path = Path(output_path) if output_path is not None else Path(DEFAULT_PRS_CSV)
    checkpoint_path = Path(checkpoint_path) if checkpoint_path is not None else (output_path.parent / "checkpoint_prs.txt")
    failure_path = Path(failure_path) if failure_path is not None else Path(DEFAULT_REPO_FAILURES_CSV)

    # Load checkpointed repo names (if any)
    processed_repos = set()
    if checkpoint_path.exists():
        try:
            with checkpoint_path.open("r", encoding="utf-8") as f:
                for ln in f:
                    name = ln.strip()
                    if name:
                        processed_repos.add(name)
        except Exception:
            # ignore and start fresh
            processed_repos = set()

    # Prepare CSV file: write header if not exists
    write_header = not output_path.exists()
    ensure_parent = output_path.parent
    ensure_parent.mkdir(parents=True, exist_ok=True)
    csv_file = open(output_path, "a", newline="", encoding="utf-8")
    csv_writer = csv.DictWriter(csv_file, fieldnames=PR_DATASET_FIELDS, extrasaction="ignore")
    if write_header:
        csv_writer.writeheader()

    try:
        for repo in selected_repositories:
            name_with_owner = repo.get("name_with_owner") or repo.get("nameWithOwner")
            if not name_with_owner:
                continue

            # skip if already processed according to checkpoint
            if name_with_owner in processed_repos:
                print(f"Skipping (checkpoint) {name_with_owner}...")
                continue

            try:
                owner, name = split_name_with_owner(name_with_owner)
                seen_pr_numbers = set()
                kept_for_repo = 0

                print(f"Collecting PRs for {name_with_owner}...")
                repo_rows: List[Dict[str, Any]] = []
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
                            repo_rows.append(row)
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

                # after finishing a repo, append repo_rows to the CSV and update checkpoint
                if repo_rows:
                    for r in repo_rows:
                        csv_writer.writerow(r)
                    csv_file.flush()

                try:
                    with checkpoint_path.open("a", encoding="utf-8") as ck:
                        ck.write(name_with_owner + "\n")
                except Exception:
                    pass

                print(f"   kept PRs for {name_with_owner}: {kept_for_repo}")

            except Exception as repo_error:
                error_message = str(repo_error)
                print(f"   ERROR collecting {name_with_owner}: {error_message}")
                print(f"   Skipping {name_with_owner} and continuing...")
                try:
                    _append_failure_row(failure_path, name_with_owner, error_message)
                except Exception:
                    pass
                try:
                    with checkpoint_path.open("a", encoding="utf-8") as ck:
                        ck.write(name_with_owner + "\n")
                except Exception:
                    pass
    finally:
        try:
            csv_file.close()
        except Exception:
            pass

    print(f"Total PR rows collected: {len(dataset)}")
    return dataset
