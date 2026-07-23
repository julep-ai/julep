"""Generic code-as-data worker context.

Point a container worker at this factory to run flows that arrive entirely as
data::

    WORKER_CONTEXT_FACTORY=julep.execution.bundle_worker:make_context

At startup it resolves every bundle named in ``JULEP_BUNDLES`` (see
:func:`julep.worker_store.load_bundles_from_env`), registering each
bundle's custom pures into the process registry, fail-closed against the
``JULEP_BUNDLE_ALLOWED_SIGNERS`` allowlist, *before* any workflow task is accepted.
It then returns a minimal :class:`WorkerContext`.

This is the worker for flows whose only runtime-arriving code is custom pures
plus ``flowJson`` — no baked tools or reasoners. A flow that calls tools or reasoners
wires its own ``WORKER_CONTEXT_FACTORY`` that injects those live callers and
calls :func:`load_bundles_from_env` the same way.
"""

from __future__ import annotations

from ..registry import DEFAULT_REGISTRY, Registry
from ..worker_store import load_bundles_from_env
from .effects import WorkerContext

__all__ = ["make_context"]


def make_context(*, registry: Registry = DEFAULT_REGISTRY) -> WorkerContext:
    """Resolve env-named bundles into ``registry`` and return a generic context."""
    load_bundles_from_env(registry=registry)
    return WorkerContext()
