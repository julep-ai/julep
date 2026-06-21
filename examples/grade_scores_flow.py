"""Grade-scores batch — a deterministic code-as-data demo flow.

No reasoners, no tools: the whole application is custom pures plus the ``each``
combinator, so the published CAS bundle (``flowJson`` + pure source) *is* the
entire app. A generic worker that has never seen this code resolves the bundle
at startup (``CA_BUNDLES``) and runs it with byte-identical, key-free output.

* ``run_demo()`` is the keyless local dry run on ``InMemoryEnv``.
* On Temporal, ``build().run(client, ...)`` drives the same frozen artifact; the
  generic worker materialises the three pures below from the signed bundle.

See ``tooling/k3d-cad-demo/`` for the publish-and-run-on-k3d harness.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from composable_agents import Deployment, deploy, each, flow, pure

# A small roster with a deliberately messy row (whitespace + string score) so the
# normalize pure earns its place.
SCORES: list[dict[str, Any]] = [
    {"name": "Ada", "score": 91},
    {"name": " Linus ", "score": "82"},
    {"name": "Grace", "score": 73},
    {"name": "Edsger", "score": 58},
    {"name": "Katherine", "score": 88},
]


@pure("cad.demo.normalize_record.v1")
def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    return {"name": str(record["name"]).strip(), "score": int(record["score"])}


@pure("cad.demo.grade_one.v1")
def grade_one(record: dict[str, Any]) -> dict[str, Any]:
    score = record["score"]
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"
    return {
        "name": record["name"],
        "score": score,
        "grade": grade,
        "passed": score >= 60,
    }


@pure("cad.demo.tally_grades.v1")
def tally_grades(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    passed = 0
    for result in results:
        counts[result["grade"]] = counts.get(result["grade"], 0) + 1
        if result["passed"]:
            passed += 1
    total = len(results)
    return {
        "graded": results,
        "tally": dict(sorted(counts.items())),
        "passed": passed,
        "passRate": round(passed / total, 3) if total else 0.0,
    }


@flow
def grade_record(record: dict[str, Any]) -> dict[str, Any]:
    clean = normalize_record(record)
    return grade_one(clean)


@flow
def batch(records: list[dict[str, Any]]) -> dict[str, Any]:
    return each(grade_record, records, max_parallel=4, reducer=tally_grades)


def build() -> Deployment:
    return deploy(batch, tools=[])


async def run_demo(records: list[dict[str, Any]] | None = None) -> Any:
    return await build().adry_run(records or SCORES)


def main() -> None:
    result = asyncio.run(run_demo())
    print("Grade rollup:")
    print(json.dumps(result.value, indent=2))


if __name__ == "__main__":
    main()
