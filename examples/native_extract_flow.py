"""Native dependency extraction batch — a deterministic code-as-data demo flow.

No reasoners, no tools: the application is custom pures plus the ``each``
combinator, so the published artifact store bundle (``flowJson`` + pure source) *is* the
entire app. The extraction pure declares an off-list third-party dependency
(``numpy``) with a PEP 723 ``# /// script`` block, so the bundle records the pure
as a native-tier dependency pure when it is granted by ``JULEP_PURE_NATIVE_DEPS``.

The pure remains deterministic and JSON-in/JSON-out: the dependency import
happens inside the pure body, and workers execute it on the native uv-venv tier
behind the explicit native dependency grant.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from julep import Deployment, deploy, each, flow, pure

ROWS: list[dict[str, Any]] = [
    {"id": "r1", "scores": [4, 8, 15, 16]},
    {"id": "r2", "scores": [23, 42]},
    {"id": "r3", "scores": [5, 5, 10]},
]


@pure("cad.demo.native_summarize_scores.v1")
# /// script
# dependencies = ["numpy==2"]
# requires-python = ">=3.11"
# ///
def summarize_scores(record: dict[str, Any]) -> dict[str, Any]:
    import numpy as np

    scores = np.array([int(score) for score in record["scores"]], dtype=np.int64)
    total = int(scores.sum())
    return {
        "id": str(record["id"]),
        "count": int(scores.size),
        "total": total,
        "maximum": int(scores.max(initial=0)),
    }


@pure("cad.demo.native_merge_summaries.v1")
def merge_summaries(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = 0
    count = 0
    maximum = 0
    ids: list[str] = []
    for result in results:
        ids.append(str(result["id"]))
        total += int(result["total"])
        count += int(result["count"])
        maximum = max(maximum, int(result["maximum"]))
    return {
        "rows": len(results),
        "count": count,
        "total": total,
        "maximum": maximum,
        "ids": sorted(ids),
    }


@flow
def summarize_one(record: dict[str, Any]) -> dict[str, Any]:
    return summarize_scores(record)


@flow
def batch(records: list[dict[str, Any]]) -> dict[str, Any]:
    return each(summarize_one, records, max_parallel=4, reducer=merge_summaries)


def build() -> Deployment:
    return deploy(batch, tools=[])


async def run_demo(records: list[dict[str, Any]] | None = None) -> Any:
    return await build().adry_run(records or ROWS)


def main() -> None:
    result = asyncio.run(run_demo())
    print("Native score rollup:")
    print(json.dumps(result.value, indent=2))


if __name__ == "__main__":
    main()
