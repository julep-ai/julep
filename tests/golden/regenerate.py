"""Regenerate the pinned §13 golden corpus from the current builders."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .fixtures import FIXTURE_BUILDERS
from .snapshot import snapshot_fixture

GOLDEN_HASHES_PATH = Path(__file__).with_name("golden_hashes.json")


def build_golden_hashes() -> dict[str, dict[str, Any]]:
    corpus: dict[str, dict[str, Any]] = {}
    skipped: list[str] = []

    for name in sorted(FIXTURE_BUILDERS):
        fixture = FIXTURE_BUILDERS[name]()
        if fixture.skip_reason:
            skipped.append(f"{name}: {fixture.skip_reason}")
            continue

        snapshot = snapshot_fixture(fixture)
        corpus[name] = {
            **snapshot.hashes,
            "shapeValues": snapshot.payload["shapes"],
            "toolHashesCount": len(snapshot.payload["toolHashes"]),
        }

    if skipped:
        joined = "\n".join(f"- {reason}" for reason in skipped)
        raise RuntimeError(f"Skipped fixtures cannot be pinned:\n{joined}")

    return corpus


def render_golden_hashes(corpus: dict[str, dict[str, Any]]) -> str:
    return json.dumps(corpus, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update",
        action="store_true",
        help=f"rewrite {GOLDEN_HASHES_PATH.relative_to(Path.cwd())}",
    )
    args = parser.parse_args()

    rendered = render_golden_hashes(build_golden_hashes())
    if args.update:
        GOLDEN_HASHES_PATH.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
