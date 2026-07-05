from __future__ import annotations

from typing import Any

from julep import Reasoner, pure
from julep import tool as native_tool

from .core import each, flow, think
from .core import tool as flow_tool

LABEL_REASONER = "cluster_labeler"
KEYWORDS_REASONER = "cluster_keywords"

STORE_CONTEXT: dict[str, Any] = {
    "storeId": "store-a",
    "mergeVersion": 7,
    "snapshotSignature": "snapshot-a",
}

CLUSTERS: list[dict[str, Any]] = [
    {
        "clusterId": 10,
        "clusterKey": "cluster-10",
        "members": ["Ada", "Ben"],
    },
    {
        "clusterId": 20,
        "clusterKey": "cluster-20",
        "members": ["Cy", "Dee"],
        "simulateStale": True,
    },
]

_store: dict[str, Any] = {}


def reset_store() -> None:
    _store.clear()
    _store.update(
        {
            "store-a": {
                "mergeVersion": 7,
                "snapshotSignature": "snapshot-a",
                "labels": {},
            }
        }
    )


def store_labels() -> dict[str, Any]:
    return dict(_store["store-a"]["labels"])


reset_store()

LABEL_REASONER_OBJECT = Reasoner(
    name=LABEL_REASONER,
    model="anthropic:claude-haiku-4-5-20251001",
    system=(
        "Label a memory macrocluster from representative member names. "
        "Reply with one JSON object."
    ),
    reply={
        "type": "object",
        "properties": {
            "label": {"type": "string"},
            "summary": {"type": "string"},
        },
        "required": ["label", "summary"],
    },
)

KEYWORDS_REASONER_OBJECT = Reasoner(
    name=KEYWORDS_REASONER,
    model="anthropic:claude-haiku-4-5-20251001",
    system=(
        "Extract short searchable keywords for a memory macrocluster. "
        "Reply with one JSON object."
    ),
    reply={
        "type": "object",
        "properties": {"keywords": {"type": "array", "items": {"type": "string"}}},
        "required": ["keywords"],
    },
)


def _assign(value: Any, key: str) -> dict[str, Any]:
    if isinstance(value, list) and len(value) == 2 and isinstance(value[0], dict):
        env, item = value
        copied = dict(env)
        copied[key] = item
        return copied
    return {key: value}


@pure("spike.assign_store_context")
def spike_assign_store_context(value: Any) -> dict[str, Any]:
    return _assign(value, "store_context")


@pure("spike.assign_cluster")
def spike_assign_cluster(value: Any) -> dict[str, Any]:
    return _assign(value, "cluster")


@pure("spike.assign_label_source")
def spike_assign_label_source(value: Any) -> dict[str, Any]:
    return _assign(value, "label_source")


@pure("spike.assign_label")
def spike_assign_label(value: Any) -> dict[str, Any]:
    return _assign(value, "label")


@pure("spike.assign_keywords")
def spike_assign_keywords(value: Any) -> dict[str, Any]:
    return _assign(value, "keywords")


@pure("spike.assign_write_payload")
def spike_assign_write_payload(value: Any) -> dict[str, Any]:
    return _assign(value, "write_payload")


@pure("spike.pluck_store_context")
def spike_pluck_store_context(env: dict[str, Any]) -> Any:
    return env["store_context"]


@pure("spike.pluck_cluster")
def spike_pluck_cluster(env: dict[str, Any]) -> Any:
    return env["cluster"]


@pure("spike.pluck_label_source")
def spike_pluck_label_source(env: dict[str, Any]) -> Any:
    return env["label_source"]


@pure("spike.pluck_label")
def spike_pluck_label(env: dict[str, Any]) -> Any:
    return env["label"]


@pure("spike.pluck_keywords")
def spike_pluck_keywords(env: dict[str, Any]) -> Any:
    return env["keywords"]


@pure("spike.pluck_write_payload")
def spike_pluck_write_payload(env: dict[str, Any]) -> Any:
    return env["write_payload"]


@pure("spike.pack_label_one_store_context_cluster")
def spike_pack_label_one_store_context_cluster(cluster: dict[str, Any]) -> dict[str, Any]:
    return {"store_context": dict(STORE_CONTEXT), "cluster": dict(cluster)}


@pure("spike.unpack_label_one_args")
def spike_unpack_label_one_args(packed: dict[str, Any]) -> dict[str, Any]:
    return {
        "store_context": packed["store_context"],
        "cluster": packed["cluster"],
    }


@pure("spike.merge_store_context_cluster")
def spike_merge_store_context_cluster(env: dict[str, Any]) -> dict[str, Any]:
    return {**env["store_context"], **env["cluster"]}


@pure("spike.merge_label_source_keywords")
def spike_merge_label_source_keywords(env: dict[str, Any]) -> dict[str, Any]:
    return {**env["label_source"], **env["label"], **env["keywords"]}


@pure("tally_cluster_statuses")
def tally_cluster_statuses(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    return {"counts": counts, "results": results}


@native_tool(effect="write", idempotent=True, name="write_cluster_label")
def _write_cluster_label(payload: dict[str, Any]) -> dict[str, Any]:
    row = _store[payload["storeId"]]
    if payload.get("simulateStale"):
        row["mergeVersion"] += 1
    if (
        row["mergeVersion"] != payload["mergeVersion"]
        or row["snapshotSignature"] != payload["snapshotSignature"]
    ):
        return {
            "clusterKey": payload["clusterKey"],
            "status": "stale_snapshot",
            "currentMergeVersion": row["mergeVersion"],
            "expectedMergeVersion": payload["mergeVersion"],
        }
    row["labels"][payload["clusterKey"]] = {
        "keywords": payload["keywords"],
        "label": payload["label"],
        "summary": payload["summary"],
    }
    return {"clusterKey": payload["clusterKey"], "status": "success"}


write_cluster_label_tool = _write_cluster_label
write_cluster_label = flow_tool(write_cluster_label_tool)
TOOLS = [write_cluster_label_tool]


def _fake_labeler(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "label": f"Memory cluster {value['clusterId']}",
        "summary": ", ".join(value["members"]),
    }


def _fake_keywords(value: dict[str, Any]) -> dict[str, Any]:
    return {"keywords": list(value["members"][:2])}


@flow
def label_one(store_context, cluster):
    label_source = store_context | cluster
    label = think(LABEL_REASONER, label_source)
    keywords = think(KEYWORDS_REASONER, label_source)
    _ = label  # Consumed by spike.merge_label_source_keywords via the env.
    write_payload = label_source | keywords
    return write_cluster_label(write_payload)


BATCH = each(label_one(STORE_CONTEXT), max_parallel=3, reducer=tally_cluster_statuses)
