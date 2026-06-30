"""Macrocluster labeling pipeline -- a mem-mcp workflow as a ``@flow`` definition.

A compact porting example for
``apps/memory-api/mcp_memory_server/workflows/cluster_labeling.py``. The real
workflow labels a store-scoped macrocluster snapshot only if the cluster map is
unchanged by the time generation finishes. This example keeps that consistency
shape intact: one global snapshot read up front, bounded per-cluster model work,
then one transactional CAS-guarded replacement of the whole label snapshot.

Structure notes:

* ``read_macrocluster_snapshot`` returns the global staleness anchor: store id,
  merge version, a snapshot signature, and the cluster member rows. Store
  ``store-stale`` simulates a concurrent merge immediately after that read.
* ``each(label_one(snapshot=snapshot), clusters, max_parallel=3)`` mirrors the
  product's label concurrency. The body closure-captures the snapshot handle, so
  the item has the same global consistency context without re-reading the store.
* Inside ``label_one`` the label reasoner and keyword reasoner both consume the same
  cluster source and neither depends on the other. The arrow sees the split: the
  DAG compiler may infer effect-fenced parallelism for those two reasoner steps.
  In the real workflow this maps to the label pass plus the one-liner pass; this
  cookbook variant uses label + keywords to make the independent split obvious.
* ``write_label_snapshot`` is the only write. It re-fetches merge version and
  signature, then either replaces all labels for the snapshot or writes none.
  The call sets ``retries=`` because the tool is declared idempotent and models
  the product's retryable CAS-write contract.
* ``switch`` handles the universal status idiom on the new frontend surface:
  success / stale_snapshot / not_found. The production workflow also has
  disabled and empty exits; this mini-port keeps the batch small and maps the
  missing-store case to ``not_found``.
* ``run_demo()`` is a keyless dry run with deterministic fake reasoners and an
  in-process store, matching the episode example's import-safe conventions.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Any

from composable_agents import (
    Reasoner,
    Deployment,
    deploy,
    each,
    flow,
    pure,
    switch,
    think,
    tool,
)

MODEL = "anthropic:claude-haiku-4-5-20251001"

LABELER = "macrocluster_labeler"
KEYWORDER = "macrocluster_keyworder"

# One clean store, one store edited between read and write, and one missing id.
STORE_BATCH = ["store-clean", "store-stale", "store-missing"]


# --------------------------------------------------------------------------- #
# The "macrocluster tables": in-process stand-ins for the product DB.
# --------------------------------------------------------------------------- #
_SEED: dict[str, list[dict[str, Any]]] = {
    "store-clean": [
        {
            "macroclusterId": "macro-10",
            "members": [
                {
                    "name": "KEDA queue scaler",
                    "content": (
                        "Temporal workers stayed at zero because the ScaledObject "
                        "watched the wrong task queue name."
                    ),
                    "sourceType": "incident",
                },
                {
                    "name": "Queue depth alert",
                    "content": (
                        "The team added an alert for task queues with messages "
                        "older than five minutes."
                    ),
                    "sourceType": "runbook",
                },
            ],
        },
        {
            "macroclusterId": "macro-20",
            "members": [
                {
                    "name": "Prompt versioning",
                    "content": (
                        "Summary prompts need version markers so stale outputs "
                        "can be regenerated after prompt changes."
                    ),
                    "sourceType": "planning",
                },
                {
                    "name": "Summary ledger",
                    "content": (
                        "Add prompt_version to the summary ledger before the next "
                        "memory release."
                    ),
                    "sourceType": "decision",
                },
            ],
        },
    ],
    "store-stale": [
        {
            "macroclusterId": "macro-30",
            "members": [
                {
                    "name": "Duplicate billing",
                    "content": (
                        "A retry without an idempotency key double-charged "
                        "customers; the fix adds a nonce uniqueness constraint."
                    ),
                    "sourceType": "incident",
                },
                {
                    "name": "Webhook replay test",
                    "content": (
                        "Regression coverage now replays the duplicate webhook "
                        "and expects one charge."
                    ),
                    "sourceType": "test",
                },
            ],
        }
    ],
}

# store-stale simulates clustering changing while labels are in flight.
_CONCURRENT_EDIT_ID = "store-stale"

_store: dict[str, dict[str, Any]] = {}


def _snapshot_signature(clusters: list[dict[str, Any]]) -> str:
    payload = json.dumps(clusters, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def reset_store() -> None:
    """Re-seed the macrocluster store (call before each demo run)."""
    _store.clear()
    for store_id, clusters in _SEED.items():
        rows = json.loads(json.dumps(clusters))
        _store[store_id] = {
            "mergeVersion": 1,
            "clusters": rows,
            "signature": _snapshot_signature(rows),
            "labels": {},
            "edited": False,
        }


reset_store()


# --------------------------------------------------------------------------- #
# Tools (the product's DB steps).
# --------------------------------------------------------------------------- #
@tool(effect="read", idempotent=True)
def read_macrocluster_snapshot(store_id: str) -> dict[str, Any]:
    """Fetch the current macrocluster snapshot and its CAS guard fields."""
    row = _store.get(store_id)
    if row is None:
        return {
            "storeId": store_id,
            "found": False,
            "context": {
                "storeId": store_id,
                "mergeVersion": None,
                "snapshotSignature": None,
            },
            "clusters": [],
        }

    clusters = json.loads(json.dumps(row["clusters"]))
    for cluster in clusters:
        cluster["memberCount"] = len(cluster["members"])
    snapshot = {
        "storeId": store_id,
        "found": True,
        "context": {
            "storeId": store_id,
            "mergeVersion": row["mergeVersion"],
            "snapshotSignature": row["signature"],
        },
        "clusters": clusters,
    }
    if store_id == _CONCURRENT_EDIT_ID and not row["edited"]:
        row["mergeVersion"] += 1
        row["clusters"][0]["members"].append(
            {
                "name": "Late merge",
                "content": "A new member landed after the label workflow read.",
                "sourceType": "merge",
            }
        )
        row["signature"] = _snapshot_signature(row["clusters"])
        row["edited"] = True
    return snapshot


@tool(effect="write", idempotent=True)
def write_label_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """Replace all labels iff the macrocluster snapshot is still current."""
    store_id = payload["storeId"]
    row = _store.get(store_id)
    if row is None:
        return {
            "storeId": store_id,
            "status": "not_found",
            "clusterCount": 0,
        }

    context = payload["context"]
    if (
        row["mergeVersion"] != context["mergeVersion"]
        or row["signature"] != context["snapshotSignature"]
    ):
        return {
            "storeId": store_id,
            "status": "stale_snapshot",
            "mergeVersion": context["mergeVersion"],
            "currentMergeVersion": row["mergeVersion"],
            "clusterCount": 0,
        }

    labels = {
        label["macroclusterId"]: {
            "label": label["label"],
            "summary": label["summary"],
            "keywords": label["keywords"],
            "memberCount": label["memberCount"],
        }
        for label in payload["labels"]
    }
    row["labels"] = labels
    return {
        "storeId": store_id,
        "status": "success",
        "mergeVersion": row["mergeVersion"],
        "snapshotSignature": row["signature"],
        "clusterCount": len(labels),
    }


TOOLS = [read_macrocluster_snapshot, write_label_snapshot]


# --------------------------------------------------------------------------- #
# Reasoners (the product's cluster labeling passes), declared as deployable objects.
# --------------------------------------------------------------------------- #
LABELER_R = Reasoner(
    name=LABELER,
    model=MODEL,
    system=(
        "You label macroclusters for a memory store. The user message is a "
        "JSON object with member names and content. Produce a concise label "
        "and a one-sentence summary of the shared theme. Reply with exactly "
        'one JSON object: {"label": "...", "summary": "..."}.'
    ),
    reply={
        "type": "object",
        "properties": {
            "label": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": ["label", "summary"],
    },
    max_tokens=512,
)

KEYWORDER_R = Reasoner(
    name=KEYWORDER,
    model=MODEL,
    system=(
        "You extract search keywords for macrocluster labels. The user "
        "message is a JSON object with member names and content. Return "
        "three short keywords that would help retrieve this cluster. Reply "
        'with exactly one JSON object: {"keywords": ["...", "...", "..."]}.'
    ),
    reply={
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
            }
        },
        "required": ["keywords"],
    },
    max_tokens=256,
)


# --------------------------------------------------------------------------- #
# Pures (status branching and batch rollup) -- pinned by source hash.
# --------------------------------------------------------------------------- #
@pure("cluster_label_write_status")
def cluster_label_write_status(written: dict[str, Any]) -> str:
    return str(written["status"])


@pure("collect_labeled_clusters")
def collect_labeled_clusters(labels: list[dict[str, Any]]) -> dict[str, Any]:
    return {"labels": labels, "clusterCount": len(labels)}


@pure("cluster_label_success")
def cluster_label_success(written: dict[str, Any]) -> dict[str, Any]:
    return {
        "storeId": written["storeId"],
        "status": "success",
        "clusterCount": written["clusterCount"],
    }


@pure("cluster_label_stale_snapshot")
def cluster_label_stale_snapshot(written: dict[str, Any]) -> dict[str, Any]:
    return {
        "storeId": written["storeId"],
        "status": "stale_snapshot",
        "clusterCount": 0,
    }


@pure("cluster_label_not_found")
def cluster_label_not_found(written: dict[str, Any]) -> dict[str, Any]:
    return {
        "storeId": written["storeId"],
        "status": "not_found",
        "clusterCount": 0,
    }


@pure("tally_cluster_label_statuses")
def tally_cluster_label_statuses(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    return {"counts": counts, "results": results}


# --------------------------------------------------------------------------- #
# The flow.
# --------------------------------------------------------------------------- #
@flow
def label_one(cluster: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    context = snapshot["context"]
    source = context | cluster
    label = think(LABELER_R, source)
    keywords = think(KEYWORDER_R, source)
    labeled = source | label | keywords
    return labeled


@flow
def success(written: dict[str, Any]) -> dict[str, Any]:
    status = cluster_label_success(written)
    return status


@flow
def stale_snapshot(written: dict[str, Any]) -> dict[str, Any]:
    status = cluster_label_stale_snapshot(written)
    return status


@flow
def not_found(written: dict[str, Any]) -> dict[str, Any]:
    status = cluster_label_not_found(written)
    return status


@flow
def label_store(store_id: str) -> dict[str, Any]:
    snapshot = read_macrocluster_snapshot(store_id)
    clusters = snapshot["clusters"]
    labeled = each(
        label_one(snapshot=snapshot),
        clusters,
        max_parallel=3,
        reducer=collect_labeled_clusters,
    )
    write_input = snapshot | labeled
    written = write_label_snapshot(
        write_input,
        retries=3,
        retry_interval_s=1,
        backoff_rate=2,
    )
    return switch(
        cluster_label_write_status,
        written,
        cases={
            "success": success,
            "stale_snapshot": stale_snapshot,
            "not_found": not_found,
        },
    )


@flow
def batch(store_ids: list[str]) -> dict[str, Any]:
    return each(
        label_store,
        store_ids,
        max_parallel=2,
        reducer=tally_cluster_label_statuses,
    )


def build() -> Deployment:
    return deploy(batch, tools=TOOLS, reasoners=[LABELER_R, KEYWORDER_R])


# --------------------------------------------------------------------------- #
# Keyless dry run: deterministic fake reasoners on InMemoryEnv.
# --------------------------------------------------------------------------- #
def _fake_labeler(value: dict[str, Any]) -> dict[str, Any]:
    first = value["members"][0]["name"]
    return {
        "label": f"Cluster: {first}",
        "summary": f"{value['memberCount']} memories about {first}.",
    }


def _fake_keyworder(value: dict[str, Any]) -> dict[str, Any]:
    names = [member["name"].split()[0].lower() for member in value["members"]]
    return {"keywords": names[:3]}


async def run_demo(batch: list[str] | None = None) -> Any:
    reset_store()
    deployment = build()
    return await deployment.adry_run(
        batch or STORE_BATCH,
        reasoners={LABELER: _fake_labeler, KEYWORDER: _fake_keyworder},
    )


def main() -> None:
    result = asyncio.run(run_demo())
    print("Cluster labeling rollup:")
    print(json.dumps(result.value, indent=2))


if __name__ == "__main__":
    main()
