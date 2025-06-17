from __future__ import annotations

import json

from ward import test

from .fixtures import make_request, test_agent
from .utils import patch_testing_temporal


@test("event stream yields transitions and closing")
async def _(make_request=make_request, agent=test_agent):
    task_data = {
        "name": "stream test",
        "description": "simple stream task",
        "input_schema": {"type": "object", "additionalProperties": True},
        "main": [{"kind_": "evaluate", "evaluate": {"output": "_"}}],
    }

    async with patch_testing_temporal():
        # create task
        resp = make_request(
            method="POST",
            url=f"/agents/{agent.id}/tasks",
            json=task_data,
        )
        resp.raise_for_status()
        task_id = resp.json()["id"]

        # start execution
        exec_resp = make_request(
            method="POST",
            url=f"/tasks/{task_id}/executions",
            json={"input": {}},
        )
        exec_resp.raise_for_status()
        execution_id = exec_resp.json()["id"]

        # stream events
        with make_request(
            method="GET",
            url=f"/executions/{execution_id}/transitions.stream",
            params={"next_page_token": ""},
            stream=True,
        ) as stream_resp:
            events = []
            for line in stream_resp.iter_lines():
                if line and line.startswith(b"data:"):
                    events.append(json.loads(line[5:]))
                    if events[-1].get("closing"):
                        break

        assert any("transition" in e.get("data", {}) for e in events)
        assert any(e.get("closing") for e in events)


@test("event stream returns child workflow events")
async def _(make_request=make_request, agent=test_agent):
    task_data = {
        "name": "child stream test",
        "description": "child workflow",
        "input_schema": {"type": "object", "additionalProperties": True},
        "main": [
            {
                "kind_": "map_reduce",
                "map_reduce": {
                    "map": {"prompt": [{"content": "hi", "role": "user"}]},
                    "over": "$ [1]",
                    "parallelism": 1,
                },
            }
        ],
    }

    async with patch_testing_temporal():
        resp = make_request(
            method="POST",
            url=f"/agents/{agent.id}/tasks",
            json=task_data,
        )
        resp.raise_for_status()
        task_id = resp.json()["id"]

        exec_resp = make_request(
            method="POST",
            url=f"/tasks/{task_id}/executions",
            json={"input": {}},
        )
        exec_resp.raise_for_status()
        execution_id = exec_resp.json()["id"]

        with make_request(
            method="GET",
            url=f"/executions/{execution_id}/transitions.stream",
            params={"next_page_token": ""},
            stream=True,
        ) as stream_resp:
            events = []
            for line in stream_resp.iter_lines():
                if line and line.startswith(b"data:"):
                    events.append(json.loads(line[5:]))
                    if events[-1].get("closing"):
                        break

        assert len(events) > 1
