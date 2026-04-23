import os
import time
from typing import Any, Dict

import requests

from .config import GRAPHQL_URL


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise EnvironmentError(f"Set {name} in .env before running the collector.")
    return value


def get_headers() -> Dict[str, str]:
    token = require_env("GITHUB_TOKEN")
    return {"Authorization": f"Bearer {token}"}


def _is_rate_limited(message: str) -> bool:
    lowered = message.lower()
    keywords = [
        "rate limit",
        "secondary rate limit",
        "abuse detection",
    ]
    return any(keyword in lowered for keyword in keywords)


def _backoff_seconds(attempt: int) -> int:
    # Exponential backoff with a cap to avoid very long waits in local runs.
    return min(60, (2**attempt) * 5)


def run_query(query: str, variables: Dict[str, Any], max_attempts: int = 6) -> Dict[str, Any]:
    last_error = ""

    for attempt in range(max_attempts):
        wait_seconds = _backoff_seconds(attempt)

        try:
            response = requests.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=get_headers(),
                timeout=90,
            )
        except requests.exceptions.Timeout:
            last_error = "timeout"
            print(f"   Timeout on attempt {attempt + 1}/{max_attempts}; waiting {wait_seconds}s...")
            time.sleep(wait_seconds)
            continue
        except requests.exceptions.ConnectionError:
            last_error = "connection error"
            print(
                f"   Connection error on attempt {attempt + 1}/{max_attempts}; waiting {wait_seconds}s..."
            )
            time.sleep(wait_seconds)
            continue

        if response.status_code == 401:
            raise RuntimeError("Invalid or expired token. Check GITHUB_TOKEN in .env")

        if response.status_code in (502, 503, 504):
            last_error = f"http {response.status_code}"
            print(
                f"   HTTP {response.status_code} on attempt {attempt + 1}/{max_attempts}; "
                f"waiting {wait_seconds}s..."
            )
            time.sleep(wait_seconds)
            continue

        if response.status_code == 403 and _is_rate_limited(response.text):
            last_error = "rate limited"
            print(
                f"   Rate limit on attempt {attempt + 1}/{max_attempts}; waiting {wait_seconds}s..."
            )
            time.sleep(wait_seconds)
            continue

        if response.status_code != 200:
            last_error = f"http {response.status_code}: {response.text[:250]}"
            print(
                f"   HTTP {response.status_code} on attempt {attempt + 1}/{max_attempts}; "
                f"waiting {wait_seconds}s..."
            )
            time.sleep(wait_seconds)
            continue

        try:
            data = response.json()
        except ValueError:
            last_error = "non-json response"
            print(f"   Non-JSON response on attempt {attempt + 1}/{max_attempts}; waiting {wait_seconds}s...")
            time.sleep(wait_seconds)
            continue

        errors = data.get("errors", [])
        if errors:
            message = " | ".join(error.get("message", "unknown graphql error") for error in errors)
            last_error = message

            if _is_rate_limited(message):
                print(
                    f"   GraphQL rate-limit error on attempt {attempt + 1}/{max_attempts}; "
                    f"waiting {wait_seconds}s..."
                )
                time.sleep(wait_seconds)
                continue

            raise RuntimeError(f"GraphQL error: {message}")

        return data

    raise RuntimeError(f"Max attempts exceeded. Last error: {last_error or 'unknown'}")
