"""Configuration constants for the GraphQL vs REST experiment."""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ─── API endpoints ────────────────────────────────────────────────────────────
REST_BASE_URL = "https://api.github.com"
GRAPHQL_URL = "https://api.github.com/graphql"

# ─── Fixed targets (kept constant across all iterations to remove the resource
#     itself as a source of variability) ─────────────────────────────────────
TARGET_USER_LOGIN = "octocat"
TARGET_REPO_OWNER = "octocat"
TARGET_REPO_NAME = "Hello-World"

# Repo with a meaningful volume of issues / PRs, so list endpoints return
# representative payload sizes.
LIST_REPO_OWNER = "facebook"
LIST_REPO_NAME = "react"

LIST_PAGE_SIZE = 30

# ─── Defaults for the experiment runner ──────────────────────────────────────
DEFAULT_REPETITIONS = 30
DEFAULT_WARMUP_ITERATIONS = 3
DEFAULT_SLEEP_BETWEEN_CALLS_SEC = 0.6
DEFAULT_RATE_LIMIT_FLOOR_PCT = 0.10  # abort if remaining quota drops below 10%

# ─── Output ──────────────────────────────────────────────────────────────────
DEFAULT_OUTPUT_DIR = Path("output")
DEFAULT_OUTPUT_CSV = DEFAULT_OUTPUT_DIR / "experiment_runs.csv"

CSV_FIELDS = [
    "iteration",
    "query_id",
    "query_label",
    "treatment",
    "endpoint",
    "status_code",
    "response_time_ms",
    "response_bytes",
    "rate_limit_remaining",
    "timestamp_utc",
    "error",
]
