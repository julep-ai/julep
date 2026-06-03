"""Structural transforms over the IR.

Two jobs that have to happen before validation can assume a clean tree:

* :func:`detect_cycles` — the IR is supposed to be a finite *tree*; recursion in
  the evaluated program only enters through the looping ops. A host-language
  knot (a node reachable from itself) would make ``to_json`` recurse forever, so
  we catch it up front by object identity.
* :func:`normalize_ids` — reassign every node a deterministic, position-encoded
  id (``$``, ``$.L``, ``$.R.B`` ...). Runs on an already-unshared tree (post JSON
  round-trip), so ids are unique by construction and identical structures get
  identical ids across hosts. The projection's ``causes`` reference these ids,
  so uniqueness is load-bearing.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from .ir import Node


def detect_cycles(flow: Node) -> Optional[list[str]]:
    """Return the id path of the first cycle found, or None if the flow is a tree.

    Uses object identity, so sharing the *same* node object on a back-edge is
    caught. (Sharing a subtree across sibling branches is a DAG, not a cycle, and
    is unshared by the freeze round-trip.)
    """
    on_path: set[int] = set()
    path_ids: list[str] = []

    def visit(n: Node) -> Optional[list[str]]:
        oid = id(n)
        if oid in on_path:
            return path_ids + [n.id]
        on_path.add(oid)
        path_ids.append(n.id)
        for child in n.children():
            found = visit(child)
            if found is not None:
                return found
        on_path.discard(oid)
        path_ids.pop()
        return None

    return visit(flow)


_SLOTS = ("left", "right", "body", "plan")
_SLOT_TAG = {"left": "L", "right": "R", "body": "B", "plan": "P"}


def normalize_ids(flow: Node, prefix: str = "$") -> Node:
    """Return a copy of ``flow`` with deterministic, unique path-based ids.

    Must be called on a tree with no shared node objects (call it after the
    JSON round-trip in :func:`composable_agents.freeze.freeze`).
    """

    def rebuild(n: Node, node_id: str) -> Node:
        new = replace(n, id=node_id)
        for slot in _SLOTS:
            child = getattr(n, slot)
            if child is not None:
                setattr(new, slot, rebuild(child, f"{node_id}.{_SLOT_TAG[slot]}"))
        if n.cases is not None:
            new.cases = {
                key: rebuild(n.cases[key], f"{node_id}.C[{key}]")
                for key in sorted(n.cases)
            }
        if n.default is not None:
            new.default = rebuild(n.default, f"{node_id}.D")
        return new

    return rebuild(flow, prefix)


def collect_duplicate_ids(flow: Node) -> list[str]:
    """Ids that appear on more than one node (should be empty post-normalize)."""
    seen: dict[str, int] = {}
    for n in flow.walk():
        seen[n.id] = seen.get(n.id, 0) + 1
    return sorted(i for i, c in seen.items() if c > 1)
