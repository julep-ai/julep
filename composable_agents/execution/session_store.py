"""Pure session durability contract for Temporal-backed agent execution.

Concurrency is not this store's job. The design binds ``session_id`` to the
Temporal workflow id 1:1, so there is one running execution per workflow id and
mutual exclusion belongs to Temporal. The cursor compare-and-swap here exists
only for crash-recovery idempotency (invariant 1), letting a retried committed
write return the original cursor instead of appending a duplicate revision.

Stored state and blobs are JSON-canonical: values are serialized with
``json.dumps(sort_keys=True)``, so refs from ``put_blob`` are content addresses
of the canonical JSON encoding — not of raw bytes — and are intentionally
distinct from the wire codec's refs (``codec.py`` addresses raw Temporal
Payload protobuf bytes). Non-JSON-serializable values are rejected: the
``TypeError`` from ``json.dumps`` propagates, and that loud failure is intended.
"""

from __future__ import annotations

import json
from typing import Any, Optional, Protocol

from .. import agent_loop as al
from .blobstore import BlobStore, InMemoryBlobStore

Cursor = int


class SessionStoreError(Exception):
    pass


class CursorConflict(SessionStoreError):
    pass


class SessionStore(Protocol):
    async def load(self, session_id: str, cursor: Cursor) -> al.AgentState: ...
    async def commit(self, session_id: str, base: Cursor, state: al.AgentState, state_hash: str) -> Cursor: ...
    async def put_blob(self, tenant: str, value: Any) -> str: ...
    async def get_blob(self, tenant: str, ref: str) -> Any: ...


class _Revision:
    def __init__(
        self,
        cursor: Cursor,
        base: Cursor,
        state_json: dict[str, Any],
        state_hash: str,
    ) -> None:
        self.cursor = cursor
        self.base = base
        self.state_json = state_json
        self.state_hash = state_hash


class InMemorySessionStore:
    def __init__(self, blob_store: Optional[BlobStore] = None) -> None:
        self._blob_store = blob_store or InMemoryBlobStore()
        self._revisions: dict[str, list[_Revision]] = {}

    async def load(self, session_id: str, cursor: Cursor) -> al.AgentState:
        if cursor == 0:
            return al.AgentState()

        revisions = self._revisions.get(session_id)
        if revisions is None:
            raise SessionStoreError(f"session cursor not found: {session_id!r}@{cursor}")

        for revision in revisions:
            if revision.cursor == cursor:
                return al.AgentState.from_json(revision.state_json)

        raise SessionStoreError(f"session cursor not found: {session_id!r}@{cursor}")

    async def commit(
        self,
        session_id: str,
        base: Cursor,
        state: al.AgentState,
        state_hash: str,
    ) -> Cursor:
        actual_hash = al.state_fingerprint(state)
        if actual_hash != state_hash:
            raise SessionStoreError(
                f"state_hash mismatch: expected {state_hash!r}, got {actual_hash!r}"
            )

        revisions = self._revisions.setdefault(session_id, [])
        head = revisions[-1].cursor if revisions else 0

        for revision in revisions:
            if revision.base == base and revision.state_hash == state_hash:
                return revision.cursor

        if base != head:
            raise CursorConflict(f"stale cursor: base={base}, head={head}")

        cursor = head + 1
        revisions.append(_Revision(cursor, base, state.to_json(), state_hash))
        return cursor

    async def put_blob(self, tenant: str, value: Any) -> str:
        """Store ``value`` as canonical JSON; the ref addresses that encoding.

        JSON-canonical, not byte-lossless: non-JSON values raise ``TypeError``
        loudly, and the ref-space is distinct from the wire codec's
        (``codec.py``), which addresses raw Temporal Payload protobuf bytes.
        """
        data = json.dumps(value, sort_keys=True).encode()
        return await self._blob_store.put(tenant, data)

    async def get_blob(self, tenant: str, ref: str) -> Any:
        """Load and ``json.loads`` a blob written by :meth:`put_blob`."""
        data = await self._blob_store.get(tenant, ref)
        return json.loads(data)


__all__ = [
    "Cursor",
    "SessionStoreError",
    "CursorConflict",
    "SessionStore",
    "InMemorySessionStore",
]
