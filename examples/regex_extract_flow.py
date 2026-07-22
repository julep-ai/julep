"""Regex email extraction batch — a deterministic code-as-data demo flow.

No reasoners, no tools: the application is custom pures plus the ``each``
combinator, so the published artifact store bundle (``flowJson`` + pure source) *is* the
entire app. The extraction pure declares its third-party dependency (``regex``)
with a PEP 723 ``# /// script`` block, so the bundle carries an ``envHash`` and
the worker resolves a pre-initialized wasm env component by that hash before
running the pure in wasm.

The pure remains deterministic and JSON-in/JSON-out: the same source runs
natively when the host has ``regex`` installed, and in the wasm env tier when a
worker resolves the bundle.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from julep import Deployment, deploy, each, flow, pure

# A small inbox with mixed case and duplicate addresses so canonical
# lowercasing, dedupe, and sorting all affect the final output.
MESSAGES: list[dict[str, Any]] = [
    {"id": "m1", "text": "Contact Ada@Example.com, ops@example.com, and ADA@example.com."},
    {"id": "m2", "text": "Noise only; no address here."},
    {"id": "m3", "text": "Escalate to Grace.Hopper@Navy.mil or ops@example.com ASAP."},
    {"id": "m4", "text": "cc: team+alerts@example.co.uk, grace.hopper@navy.mil"},
]


@pure("cad.demo.extract_emails.v1")
# /// script
# dependencies = ["regex==2024.11.6"]
# requires-python = ">=3.11"
# ///
def extract_emails(record: dict[str, Any]) -> dict[str, Any]:
    import regex

    text = str(record["text"])
    pattern = r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
    emails = sorted({match.lower() for match in regex.findall(pattern, text, regex.IGNORECASE)})
    return {"emails": emails, "count": len(emails)}


@pure("cad.demo.merge_extractions.v1")
def merge_extractions(results: list[dict[str, Any]]) -> dict[str, Any]:
    all_emails: set[str] = set()
    total_matches = 0
    rows_with_email = 0
    for result in results:
        emails = [str(email) for email in result["emails"]]
        all_emails.update(emails)
        count = int(result["count"])
        total_matches += count
        if count:
            rows_with_email += 1
    return {
        "rows": len(results),
        "rowsWithEmail": rows_with_email,
        "totalMatches": total_matches,
        "emails": sorted(all_emails),
    }


@flow
def extract_one(record: dict[str, Any]) -> dict[str, Any]:
    return extract_emails(record)


@flow
def batch(records: list[dict[str, Any]]) -> dict[str, Any]:
    return each(extract_one, records, max_parallel=4, reducer=merge_extractions)


def build() -> Deployment:
    return deploy(batch, tools=[])


async def run_demo(records: list[dict[str, Any]] | None = None) -> Any:
    return await build().adry_run(records or MESSAGES)


def main() -> None:
    result = asyncio.run(run_demo())
    print("Email rollup:")
    print(json.dumps(result.value, indent=2))


if __name__ == "__main__":
    main()
