from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from conftest import run
from julep.contracts import McpAnnotations
from julep.dotctx import Reasoner
from julep.execution.effects import WorkerContext
from julep.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec
from julep.local import (
    LocalExecutionConfigurationError,
    LocalExecutionUnsupported,
    LocalPipelineNotFound,
    arun_local_pipeline,
    prepare_local_pipeline,
    run_local_pipeline,
)
from julep.qos import QoSTier
from julep.registry import Registry


def _reasoner_project(root: Path) -> None:
    package = root / "summary.ctx"
    package.mkdir()
    (package / "settings.yaml").write_text(
        """
model: test:summary
system: Summarize the supplied value.
reply_schema:
  type: object
  properties:
    answer:
      type: string
  required: [answer]
""".strip(),
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        """
[tool.julep]

[tool.julep.pipeline.summary]
ctx = "summary.ctx"
""".strip(),
        encoding="utf-8",
    )


def _tool_agent_project(root: Path) -> None:
    package = root / "agent.ctx"
    package.mkdir()
    (package / "settings.yaml").write_text(
        """
model: test:agent
max_rounds: 2
""".strip(),
        encoding="utf-8",
    )
    (package / "prompt.j2").write_text(
        """
<<< role:system >>>
Use lookup once, then finish.
<<< role:user >>>
{{ value }}
""".strip(),
        encoding="utf-8",
    )
    (package / "schema.pyi").write_text(
        """
class Input:
    query: str

class Output:
    answer: str
""".strip(),
        encoding="utf-8",
    )
    (package / "tools.pyi").write_text(
        """
def lookup(query: str) -> dict:
    \"\"\"Look up one query.\"\"\"
    ...
""".strip(),
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        """
[tool.julep]

[tool.julep.mcp.servers.srv]
url = "http://mcp.test"

[tool.julep.pipeline.agent]
ctx = "agent.ctx"

[tool.julep.pipeline.agent.tools]
lookup = "srv:lookup"
""".strip(),
        encoding="utf-8",
    )


def _lookup_snapshot() -> McpSnapshot:
    return McpSnapshot(
        servers={
            "srv": McpServerSnapshot(
                server="srv",
                version="1",
                tools={
                    "lookup": McpToolSpec(
                        input_schema={
                            "type": "object",
                            "properties": {"query": {"type": "string"}},
                            "required": ["query"],
                        },
                        annotations=McpAnnotations(
                            read_only_hint=True,
                            idempotent_hint=True,
                        ),
                    )
                },
            )
        }
    )


def test_async_configured_pipeline_uses_canonical_caller_and_principal(
    tmp_path: Path,
) -> None:
    _reasoner_project(tmp_path)
    seen: dict[str, Any] = {}

    async def llm(
        reasoner: Any,
        value: Any,
        principal: Any,
        transcript: Any,
        dispatch: Any,
    ) -> Any:
        seen.update(
            reasoner=reasoner,
            value=value,
            principal=principal,
            transcript=transcript,
            dispatch=dispatch,
        )
        return {"answer": value["text"].upper()}

    result = run(
        arun_local_pipeline(
            "summary",
            {"text": "hello", "transcript": ["ordinary business input"]},
            project_root=tmp_path,
            llm=llm,
            principal={"tenant": "acme"},
        )
    )

    assert result == {"answer": "HELLO"}
    assert seen["reasoner"].name == "summary.ctx"
    assert seen["value"]["transcript"] == ["ordinary business input"]
    assert seen["principal"] == {"tenant": "acme"}
    assert seen["transcript"] is None
    assert seen["dispatch"].qos is QoSTier.STANDARD


def test_prepared_pipeline_is_reusable_and_sync_context_supplies_llm(
    tmp_path: Path,
) -> None:
    _reasoner_project(tmp_path)
    calls: list[Any] = []

    async def llm(
        _reasoner: Any,
        value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
    ) -> Any:
        calls.append(value)
        return {"answer": str(value["n"])}

    prepared = prepare_local_pipeline("summary", project_root=tmp_path)
    artifact_hash = prepared.artifact_hash

    assert prepared.run({"n": 1}, context=WorkerContext(llm=llm)) == {
        "answer": "1"
    }
    assert prepared.run({"n": 2}, context=WorkerContext(llm=llm)) == {
        "answer": "2"
    }
    assert prepared.artifact_hash == artifact_hash
    assert calls == [{"n": 1}, {"n": 2}]


def test_tool_agent_uses_frozen_defs_mcp_context_and_principal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("jinja2")
    _tool_agent_project(tmp_path)
    monkeypatch.setattr(
        "julep.mcp_snapshot.snapshot_servers",
        lambda *_args, **_kwargs: _lookup_snapshot(),
    )
    model_calls: list[dict[str, Any]] = []
    effect_calls: list[dict[str, Any]] = []

    async def llm(
        reasoner: Any,
        value: Any,
        principal: Any,
        transcript: Any,
        dispatch: Any,
        **kwargs: Any,
    ) -> Any:
        model_calls.append(
            {
                "reasoner": reasoner,
                "value": value,
                "principal": principal,
                "transcript": transcript,
                "dispatch": dispatch,
                "tools": kwargs.get("tools"),
            }
        )
        if len(model_calls) == 1:
            return {
                "tool_calls": [
                    {
                        "id": "lookup-1",
                        "tool": "lookup",
                        "input": value["input"],
                    }
                ]
            }
        observation = value["input"][0]["output"]
        return {"done": True, "output": {"answer": observation["found"]}}

    async def mcp(
        server: str,
        tool: str,
        value: Any,
        cid: str,
        principal: Any,
        secrets: Any,
        input_schema_validated: bool,
    ) -> Any:
        effect_calls.append(
            {
                "server": server,
                "tool": tool,
                "value": value,
                "cid": cid,
                "principal": principal,
                "secrets": secrets,
                "validated": input_schema_validated,
            }
        )
        return {"found": value["query"].upper()}

    result = run(
        arun_local_pipeline(
            "agent",
            {"query": "julep"},
            project_root=tmp_path,
            llm=llm,
            context=WorkerContext(mcp_call=mcp),
            principal={"tenant": "acme"},
        )
    )

    assert result["status"] == "done"
    assert result["output"] == {"answer": "JULEP"}
    assert model_calls[0]["tools"][0]["function"]["name"] == "lookup"
    assert model_calls[0]["principal"] == {"tenant": "acme"}
    assert effect_calls == [
        {
            "server": "srv",
            "tool": "lookup",
            "value": {"query": "julep"},
            "cid": effect_calls[0]["cid"],
            "principal": {"tenant": "acme"},
            "secrets": None,
            "validated": True,
        }
    ]


def test_tool_agent_rejects_caller_without_tools_extension(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("jinja2")
    _tool_agent_project(tmp_path)
    monkeypatch.setattr(
        "julep.mcp_snapshot.snapshot_servers",
        lambda *_args, **_kwargs: _lookup_snapshot(),
    )

    async def strict_five(
        _reasoner: Any,
        _value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
    ) -> Any:
        return {"done": True, "output": {"answer": "unused"}}

    async def mcp(*_args: Any) -> Any:
        return {}

    with pytest.raises(LocalExecutionConfigurationError, match="tools= keyword"):
        run(
            arun_local_pipeline(
                "agent",
                {"query": "julep"},
                project_root=tmp_path,
                llm=strict_five,
                context=WorkerContext(mcp_call=mcp),
            )
        )


def test_local_pipeline_errors_are_typed_and_actionable(tmp_path: Path) -> None:
    _reasoner_project(tmp_path)

    with pytest.raises(LocalPipelineNotFound, match="configured pipelines: summary"):
        prepare_local_pipeline("missing", project_root=tmp_path)

    with pytest.raises(LocalPipelineNotFound, match="unknown environment 'prod'"):
        prepare_local_pipeline("summary", project_root=tmp_path, env="prod")

    with pytest.raises(LocalExecutionConfigurationError, match="pass llm="):
        run(arun_local_pipeline("summary", {}, project_root=tmp_path))

    async def llm(
        _reasoner: Any,
        _value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
    ) -> Any:
        return {"answer": "unused"}

    registry = Registry()
    registry.register_reasoner(Reasoner("summary.ctx", "test:different"))
    prepared = prepare_local_pipeline("summary", project_root=tmp_path)
    with pytest.raises(LocalExecutionConfigurationError, match="compiled declaration"):
        prepared.run(context=WorkerContext(llm=llm, registry=registry))


def test_sync_helper_rejects_an_active_event_loop(tmp_path: Path) -> None:
    _reasoner_project(tmp_path)

    async def llm(
        _reasoner: Any,
        _value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
    ) -> Any:
        return {"answer": "ok"}

    async def inside_loop() -> None:
        with pytest.raises(LocalExecutionConfigurationError, match="active event loop"):
            run_local_pipeline("summary", {}, project_root=tmp_path, llm=llm)

    asyncio.run(inside_loop())


def test_transcript_scoped_agent_fails_before_model_io(tmp_path: Path) -> None:
    (tmp_path / "foreground_app.py").write_text(
        """
from julep import (
    Application,
    ContextPolicy,
    ContextScope,
    PipelineSpec,
    Reasoner,
    app,
)

reasoner = Reasoner("scoped", "test:scoped")
application = Application(
    "foreground-test",
    [
        PipelineSpec(
            name="scoped",
            flow=app(
                "scoped",
                max_rounds=1,
                ctx=ContextPolicy(
                    scope=ContextScope.WHOLE_SESSION,
                    max_tokens=128,
                ),
            ),
            reasoners=(reasoner,),
        )
    ],
)
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.julep]
src = ["."]
application = "foreground_app:application"
""".strip(),
        encoding="utf-8",
    )
    called = False

    async def llm(
        _reasoner: Any,
        _value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
    ) -> Any:
        nonlocal called
        called = True
        return {"done": True, "output": "unused"}

    prepared = prepare_local_pipeline("scoped", project_root=tmp_path)
    with pytest.raises(LocalExecutionUnsupported, match="transcript-scoped"):
        prepared.run({}, llm=llm)
    assert called is False
