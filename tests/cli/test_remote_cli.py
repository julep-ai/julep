from __future__ import annotations

import time
from importlib import import_module

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from starlette.testclient import TestClient

from julep.client import JulepClient
from julep.cli.main import main
from tests.server.conftest import server_factory as server_factory


def _event(run_id: str, event_id: str, event_type: str) -> dict[str, object]:
    return {
        "workflow_id": f"run-{run_id}",
        "segment_seq": 0,
        "event_id": event_id,
        "run_id": run_id,
        "type": event_type,
        "node": "root",
        "cid": "root-1",
        "ts": time.time(),
        "causes": [],
        "value_ref": None,
        "shape": None,
        "cost": None,
        "error": None,
        "attrs": {"terminal": True} if event_type == "Did" else {},
    }


def test_remote_status_and_trace(
    server_factory,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    harness = server_factory()
    run_id = "remote-run"
    assert harness.store.create_run(
        run_id=run_id,
        idempotency_key="idem-remote-run",
        workflow_id=f"run-{run_id}",
        session_id=f"run-{run_id}",
        release_hash="sha256:" + "a" * 64,
        pipeline="summary",
        application="memory",
        principal={"key": "alice"},
        input_ref=None,
        status="running",
        started_at=time.time(),
    ) == "created"
    harness.store.insert_events(
        [_event(run_id, "planned", "Planned"), _event(run_id, "did", "Did")]
    )
    harness.store.set_run_status(run_id, "completed", finished_at=time.time())

    with TestClient(harness.app) as transport_client:
        client = JulepClient(api_key="alice-token", client=transport_client)
        main_module = import_module("julep.cli.main")
        monkeypatch.setattr(main_module, "_remote_client", lambda _url, _key: client)
        assert main(["status", "--remote"]) == 0
        status_output = capsys.readouterr().out
        assert run_id in status_output
        assert "completed" in status_output

        assert main(["trace", "--remote", run_id]) == 0
        assert "root" in capsys.readouterr().out


def test_remote_status_requires_api_url(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("JULEP_API_URL", raising=False)
    monkeypatch.delenv("JULEP_API_KEY", raising=False)
    assert main(["status", "--remote"]) == 2
    assert "--api-url or JULEP_API_URL" in capsys.readouterr().err
