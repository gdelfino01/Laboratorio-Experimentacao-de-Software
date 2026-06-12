"""Experiment runner — paired, randomized, with warmup and throttling.

For each `(iteration, query_pair)` the runner:
  1. Sorteia uniformly the order of treatments (REST→GraphQL or vice versa).
  2. Issues the two paired requests with a small sleep in between.
  3. Records two `Measurement` objects sharing the same `iteration` index.

Warm-up iterations are executed first and **discarded** from the output so
cold-start effects (DNS, TLS handshake, server cache miss) do not contaminate
the measurements analyzed in Sprint 2.
"""

from __future__ import annotations

import csv
import random
import time
from dataclasses import asdict
from pathlib import Path
from typing import List

from . import config
from .github_api import Measurement, call_graphql, call_rest
from .queries import QueryPair, build_pairs


def _execute_pair(iteration: int, pair: QueryPair) -> List[dict]:
    """Run REST and GraphQL for one paired query in randomized order."""
    treatments = ["REST", "GRAPHQL"]
    random.shuffle(treatments)

    rows: List[dict] = []
    for treatment in treatments:
        if treatment == "REST":
            measurement = call_rest(pair.rest_endpoint)
        else:
            measurement = call_graphql(
                pair.graphql_query, pair.graphql_variables, label=pair.label
            )

        rows.append(_to_row(iteration, pair, measurement))
        time.sleep(config.DEFAULT_SLEEP_BETWEEN_CALLS_SEC)

    return rows


def _to_row(iteration: int, pair: QueryPair, m: Measurement) -> dict:
    base = asdict(m)
    base["iteration"] = iteration
    base["query_id"] = pair.query_id
    base["query_label"] = pair.label
    return {key: base.get(key, "") for key in config.CSV_FIELDS}


def _check_rate_limit_floor(last_remaining: int | None) -> None:
    """Abort if remaining quota fell below the configured floor (default 10%)."""
    if last_remaining is None:
        return
    # GitHub authenticated quota: 5000/h on REST; 5000 points/h on GraphQL.
    # Either way we abort if remaining is in the bottom 10% absolute.
    floor = int(5000 * config.DEFAULT_RATE_LIMIT_FLOOR_PCT)
    if last_remaining < floor:
        raise RuntimeError(
            f"Rate limit too low ({last_remaining} remaining < {floor}); aborting."
        )


def run_experiment(
    repetitions: int,
    warmup: int,
    output_path: Path,
    seed: int | None = None,
) -> None:
    """Execute warmup + repetitions × paired queries, persisting only valid runs."""
    if seed is not None:
        random.seed(seed)

    pairs = build_pairs()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(
        f"[runner] {len(pairs)} paired queries × {repetitions} repetitions "
        f"({warmup} warmup) = {len(pairs) * repetitions * 2} valid measurements"
    )

    # ── Warmup (discarded) ──────────────────────────────────────────────────
    for w in range(1, warmup + 1):
        print(f"[runner]  warmup {w}/{warmup}...")
        for pair in pairs:
            _execute_pair(iteration=-w, pair=pair)

    # ── Measurement phase ───────────────────────────────────────────────────
    last_remaining: int | None = None

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=config.CSV_FIELDS)
        writer.writeheader()

        for iteration in range(1, repetitions + 1):
            for pair in pairs:
                rows = _execute_pair(iteration=iteration, pair=pair)
                for row in rows:
                    writer.writerow(row)
                    if row.get("rate_limit_remaining") not in ("", None):
                        last_remaining = int(row["rate_limit_remaining"])

                f.flush()
                _check_rate_limit_floor(last_remaining)

            print(
                f"[runner]  iteration {iteration}/{repetitions} done "
                f"(remaining quota: {last_remaining})"
            )

    print(f"[runner] saved → {output_path}")
