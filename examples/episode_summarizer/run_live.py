"""Command-line entry point for the full-stack episode-summarizer live harness."""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence

from .harness import (
    DEFAULT_SUMMARIZER_MODEL,
    LIVE_ONE_LINER_MODEL,
    HarnessUnavailable,
    run_live_e2e,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Publish and run the episode-summarizer application through "
            "Postgres, Temporal, the Julep API, an authenticated MCP server, and "
            "live Anthropic models."
        )
    )
    parser.add_argument(
        "--summarizer-model",
        default=DEFAULT_SUMMARIZER_MODEL,
        help=f"Anthropic summarizer model (default: {DEFAULT_SUMMARIZER_MODEL})",
    )
    parser.add_argument(
        "--one-liner-model",
        default=LIVE_ONE_LINER_MODEL,
        help=f"Anthropic one-liner model (default: {LIVE_ONE_LINER_MODEL})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=180,
        help="maximum seconds to wait for the run's SSE terminal event (default: 180)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = asyncio.run(
            run_live_e2e(
                summarizer_model=args.summarizer_model,
                one_liner_model=args.one_liner_model,
                timeout_s=args.timeout,
            )
        )
    except HarnessUnavailable as exc:
        print(f"episode-summarizer live harness unavailable: {exc}")
        return 2

    print(f"run_id: {result.run_id}")
    print(f"SSE projection events: {result.sse_event_count}")
    print(f"wall time: {result.wall_seconds:.2f}s")
    print(f"models: {json.dumps(result.model_ids, sort_keys=True)}")
    print("summaries:")
    for episode_id, summary in result.summaries.items():
        print(f"  {episode_id}: {summary}")
    print("one-liners:")
    for episode_id, one_liner in result.one_liners.items():
        print(f"  {episode_id}: {one_liner}")
    print("tally:")
    print(json.dumps(result.result_value, indent=2, sort_keys=True))
    if result.trace_output:
        print("trace:")
        print(result.trace_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
