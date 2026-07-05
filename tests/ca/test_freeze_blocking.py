"""The freeze child must REFUSE to publish/record a deployment that strict
deploy would reject (blocking diagnostics present).

We drive ``_freeze_agent`` in-process with a stub ``deploy`` so we do not need a
real flow that triggers a blocking diagnostic. The contract under test:

* when ``blocking(dep.diagnostics)`` is non-empty, ``_freeze_agent`` returns an
  ``{"error": ...}`` payload carrying the prod-gap summary, and
* it never calls ``dep.publish`` in that case.
"""

from __future__ import annotations

import importlib
from typing import Any

from julep.ca import _resolve_child
from julep.validate import Diagnostic

# ``julep.deploy`` the NAME is rebound to the deploy() function in the
# package __init__, so import the underlying module object explicitly to patch it.
deploy_mod = importlib.import_module("julep.deploy")


class _StubFlow:
    """Minimal stand-in for a FlowLike that _freeze_agent introspects."""

    name = "blocked"
    _tools: tuple[Any, ...] = ()

    def to_ir(self) -> "_StubNode":
        return _StubNode()


class _StubNode:
    def tool_refs(self) -> list[Any]:
        return []


class _StubDeployment:
    def __init__(self, diagnostics: list[Diagnostic]) -> None:
        self.diagnostics = diagnostics
        self.published_with: list[Any] = []
        self.artifact_components = {"pureSourceHashes": {"std.init": "sha256:aa"}}
        self.artifact_hash = "sha256:should-not-be-used"
        self.flow_json: dict[str, Any] = {"name": "blocked"}
        self.manifest_json: dict[str, Any] = {}
        self.bundle_ref = None

    def prod_gap_summary(self) -> str:
        return "in prod this would block: 1 ungated dangerous/approval call"

    def publish(self, store: Any) -> dict[str, Any]:  # pragma: no cover - must not run
        self.published_with.append(store)
        return {}


def test_freeze_rejects_blocking_and_does_not_publish(monkeypatch, tmp_path) -> None:
    blocking_diag = Diagnostic(code="E_APPROVAL", node_id="n1", message="needs gate")
    stub = _StubDeployment(diagnostics=[blocking_diag])

    def _fake_deploy(
        node: Any, snapshot: Any, *, strict: bool = True, queue: Any = None
    ) -> _StubDeployment:
        # ca freeze must call deploy with strict=False (so it can surface the gap
        # itself) and then reject explicitly.
        assert strict is False
        return stub

    monkeypatch.setattr(deploy_mod, "deploy", _fake_deploy)

    result = _resolve_child._freeze_agent(_StubFlow(), modules=[], cas=str(tmp_path / "cas"))

    assert "error" in result
    assert "block" in result["error"]
    # The blocking deployment was never published / recorded.
    assert stub.published_with == []
    assert not (tmp_path / "cas").exists()


def test_freeze_publishes_when_no_blocking_diagnostics(monkeypatch, tmp_path) -> None:
    warn = Diagnostic(code="W_PAR", node_id="n1", message="just a warning", severity="warning")
    stub = _StubDeployment(diagnostics=[warn])

    def _fake_deploy(
        node: Any, snapshot: Any, *, strict: bool = True, queue: Any = None
    ) -> _StubDeployment:
        return stub

    monkeypatch.setattr(deploy_mod, "deploy", _fake_deploy)
    # Make snapshot_from_tools a no-op so we never touch the real CAS machinery
    # beyond the stub publish.
    monkeypatch.setattr(
        "julep.agent.snapshot_from_tools", lambda tools: object()
    )
    # publish=False keeps this purely in-process (no real CAS write).
    result = _resolve_child._freeze_agent(
        _StubFlow(), modules=[], cas=str(tmp_path / "cas"), publish=False
    )

    assert "error" not in result
    assert result["pinned_pures"] == {"std.init": "sha256:aa"}
    assert result["artifact_hash"] == "sha256:should-not-be-used"
    # Read-only path never publishes.
    assert stub.published_with == []
