"""WORKER_CONTEXT_FACTORY for the REMOTE session demo worker pod.

Imports ``examples/session_demo.py`` so the worker registers the EXACT same
reasoner + pure source (``session_demo.assistant`` / ``.prep`` / ``.post``) that
the driver pins at deploy time. Pure identity is content-addressed over
``inspect.getsource(fn)``, so the worker MUST register byte-identical source or
``verifyPures`` rejects the run as drift. Importing the same module guarantees
that. Supplies a ``WorkerContext`` with an InMemorySessionStore + the REAL
multi-provider any-llm caller.

Single-replica InMemorySessionStore is intentional: it is process-local, so the
worker Deployment is pinned to replicas=1.
"""

from __future__ import annotations

import sys
from typing import Any

# session_demo.py is baked at /app/session_demo.py in the image.
sys.path.insert(0, "/app")

import session_demo  # noqa: E402,F401  (registers reasoner + pures at import)


def make_context() -> Any:
    """WORKER_CONTEXT_FACTORY entrypoint for the session-demo pod replica."""
    from composable_agents.execution.effects import WorkerContext
    from composable_agents.execution.llm import make_llm_caller
    from composable_agents.execution.session_store import InMemorySessionStore

    return WorkerContext(
        session_store=InMemorySessionStore(empty_value=[]),
        llm=make_llm_caller(),
    )
