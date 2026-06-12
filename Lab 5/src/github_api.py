"""Instrumented HTTP clients for the GitHub REST and GraphQL APIs.

Both clients return a `Measurement` capturing the wall-clock duration of the
request and the size of the response body, so that the experiment runner can
treat them uniformly.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests

from . import config


@dataclass
class Measurement:
    """One observed (treatment, query) execution."""

    treatment: str            # "REST" or "GRAPHQL"
    endpoint: str             # URL or operation label
    status_code: int
    response_time_ms: float
    response_bytes: int
    rate_limit_remaining: Optional[int]
    timestamp_utc: str
    error: str = ""


def _require_token() -> str:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise EnvironmentError(
            "GITHUB_TOKEN missing. Copy .env.example to .env and set the token."
        )
    return token


def _common_headers() -> dict:
    """Headers shared by both clients.

    `Cache-Control: no-cache` mitigates server-side caching as a confounder.
    """
    return {
        "Authorization": f"Bearer {_require_token()}",
        "Cache-Control": "no-cache",
        "User-Agent": "puc-minas-lab05-graphql-vs-rest",
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_rate_limit_remaining(response: requests.Response) -> Optional[int]:
    raw = response.headers.get("X-RateLimit-Remaining")
    try:
        return int(raw) if raw is not None else None
    except ValueError:
        return None


def call_rest(rest_endpoint: str) -> Measurement:
    """Issue a GET against the REST API and time the round trip."""
    url = f"{config.REST_BASE_URL}{rest_endpoint}"
    headers = _common_headers()
    headers["Accept"] = "application/vnd.github+json"

    started_at = _now_iso()
    t0 = time.perf_counter()
    try:
        response = requests.get(url, headers=headers, timeout=60)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return Measurement(
            treatment="REST",
            endpoint=url,
            status_code=response.status_code,
            response_time_ms=round(elapsed_ms, 3),
            response_bytes=len(response.content),
            rate_limit_remaining=_parse_rate_limit_remaining(response),
            timestamp_utc=started_at,
        )
    except requests.RequestException as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return Measurement(
            treatment="REST",
            endpoint=url,
            status_code=-1,
            response_time_ms=round(elapsed_ms, 3),
            response_bytes=0,
            rate_limit_remaining=None,
            timestamp_utc=started_at,
            error=str(exc),
        )


def call_graphql(query: str, variables: dict, label: str) -> Measurement:
    """Issue a POST against the GraphQL endpoint and time the round trip."""
    headers = _common_headers()
    headers["Content-Type"] = "application/json"

    payload = {"query": query, "variables": variables}

    started_at = _now_iso()
    t0 = time.perf_counter()
    try:
        response = requests.post(
            config.GRAPHQL_URL, json=payload, headers=headers, timeout=60
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return Measurement(
            treatment="GRAPHQL",
            endpoint=f"{config.GRAPHQL_URL}#{label}",
            status_code=response.status_code,
            response_time_ms=round(elapsed_ms, 3),
            response_bytes=len(response.content),
            rate_limit_remaining=_parse_rate_limit_remaining(response),
            timestamp_utc=started_at,
        )
    except requests.RequestException as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return Measurement(
            treatment="GRAPHQL",
            endpoint=f"{config.GRAPHQL_URL}#{label}",
            status_code=-1,
            response_time_ms=round(elapsed_ms, 3),
            response_bytes=0,
            rate_limit_remaining=None,
            timestamp_utc=started_at,
            error=str(exc),
        )
