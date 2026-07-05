"""Authoring-side flow for the CAS bundle round-trip spike."""

from __future__ import annotations

from julep import arr, pure, seq

PURE_NAMES = ("cas.normalize_input.v1", "cas.render_summary.v1")
AUTHORING_INPUT = {
    "name": "Ada",
    "scores": [3, 5, 8],
    "tags": ["spike", "cas"],
}


@pure("cas.normalize_input.v1")
def normalize_input(value):
    scores = [int(item) for item in value["scores"]]
    return {
        "name": str(value["name"]).strip().title(),
        "scoreTotal": sum(scores),
        "scoreCount": len(scores),
        "tags": sorted(str(tag).lower() for tag in value.get("tags", [])),
    }


@pure("cas.render_summary.v1")
def render_summary(value):
    return {
        "summary": f"{value['name']}:{value['scoreTotal']}/{value['scoreCount']}",
        "tags": ",".join(value["tags"]),
    }


FLOW = seq(arr("cas.normalize_input.v1"), arr("cas.render_summary.v1"))
