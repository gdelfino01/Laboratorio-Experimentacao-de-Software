"""CLI entrypoint for the GraphQL vs REST experiment.

Usage examples
--------------
    py src/main.py --repetitions 3 --warmup 1            # smoke test
    py src/main.py --repetitions 30 --warmup 3           # full run
    py src/main.py --repetitions 30 --output output/x.csv --seed 42

Run with `--list-queries` to inspect the paired queries without contacting
the network.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as `py src/main.py ...` from the Lab 5 root.
_THIS = Path(__file__).resolve()
sys.path.insert(0, str(_THIS.parent.parent))

from src import config            # noqa: E402
from src.experiment import run_experiment  # noqa: E402
from src.queries import build_pairs        # noqa: E402


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="GraphQL vs REST controlled experiment (Lab 05)."
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=config.DEFAULT_REPETITIONS,
        help="Number of paired iterations per query (default: %(default)s).",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=config.DEFAULT_WARMUP_ITERATIONS,
        help="Discarded warmup iterations (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=config.DEFAULT_OUTPUT_CSV,
        help="CSV output path (default: %(default)s).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible treatment ordering.",
    )
    parser.add_argument(
        "--list-queries",
        action="store_true",
        help="Print the paired query definitions and exit (no network calls).",
    )
    return parser


def _print_pairs() -> None:
    pairs = build_pairs()
    print(f"Defined {len(pairs)} paired queries:\n")
    for p in pairs:
        print(f"  {p.query_id} — {p.label}")
        print(f"     REST:    GET {p.rest_endpoint}")
        first_line = next(
            (ln.strip() for ln in p.graphql_query.splitlines() if ln.strip()),
            "<empty>",
        )
        print(f"     GraphQL: {first_line}")
        print(f"     vars:    {p.graphql_variables}\n")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.list_queries:
        _print_pairs()
        return 0

    if args.repetitions < 1:
        print("error: --repetitions must be >= 1", file=sys.stderr)
        return 2
    if args.warmup < 0:
        print("error: --warmup must be >= 0", file=sys.stderr)
        return 2

    run_experiment(
        repetitions=args.repetitions,
        warmup=args.warmup,
        output_path=args.output,
        seed=args.seed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
