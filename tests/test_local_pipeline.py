from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from conftest import run
from julep import (
    AttemptMeta,
    CapabilityManifest,
    CompiledPipeline,
    EmbeddedRun,
    InMemoryProjection,
    LlmCallMeta,
    LlmResult,
    LlmUsage,
    LocalPipeline,
    PipelineSpec,
    ProjectionEvent,
    Ann,
    app,
    call,
    deploy,
    seq,
    think,
    tool,
)
from julep.dsl import native
from julep.contracts import McpAnnotations
from julep.dotctx import Reasoner
from julep.execution.effects import WorkerContext
from julep.execution.blobstore import InMemoryBlobStore
from julep.errors import AgentTerminalError, ToolInputValidation
from julep.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec
from julep.local import (
    LocalExecutionConfigurationError,
    LocalExecutionUnsupported,
    LocalPipelineNotFound,
    arun_local_pipeline,
    prepare_local_pipeline,
    run_local_pipeline,
)
from julep.llm import with_model_ladder
from julep.qos import QoSTier
from julep.projection import EventType
from julep.registry import Registry
from julep.trajectory import InMemoryTrajectoryStore
from julep.typed import seq as typed_seq


@tool(effect="read", idempotent=True, name="batch_e_increment")
def _increment(value: int) -> int:
    return value + 1


@tool(effect="read", idempotent=True, name="batch_e_raise")
def _raise_tool(_value: Any) -> Any:
    raise RuntimeError("batch-e-boom")


async def configured_test_llm(
    _reasoner: Any,
    value: Any,
    _principal: Any,
    _transcript: Any,
    _dispatch: Any,
) -> Any:
    return {"answer": f"configured:{value['source']}"}


class _EventSink:
    def __init__(self) -> None:
        self.events: list[ProjectionEvent] = []

    def append(self, event: ProjectionEvent) -> None:
        self.events.append(event)


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


def _direct_effect_project(root: Path) -> None:
    module_name = f"direct_effect_app_{abs(hash(str(root)))}"
    (root / f"{module_name}.py").write_text(
        """
import asyncio

from julep import (
    Application,
    PipelineSpec,
    call,
    mcp,
    snapshot_from_listings,
    tool,
)

@tool(effect="read", idempotent=True)
async def async_upper(value):
    await asyncio.sleep(0)
    return value.upper()

typed_snapshot = snapshot_from_listings(
    {
        "srv": {
            "typed": {
                "inputSchema": {
                    "type": "object",
                    "properties": {"query": {"type": "string"}},
                    "required": ["query"],
                }
            }
        }
    }
)

application = Application(
    "direct-effects",
    [
        PipelineSpec(
            name="async-native",
            flow=async_upper,
            tools=(async_upper,),
        ),
        PipelineSpec(
            name="typed-mcp",
            flow=call(mcp("srv", "typed")),
            snapshot=typed_snapshot,
        ),
    ],
)
""".strip(),
        encoding="utf-8",
    )
    (root / "pyproject.toml").write_text(
        """
[tool.julep]
src = ["."]
application = "{module_name}:application"
""".strip().format(module_name=module_name),
        encoding="utf-8",
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


def test_local_pipeline_agent_enforces_deployment_max_calls_across_rounds() -> None:
    reasoner = Reasoner("limited-controller", "test:limited")
    snapshot = _lookup_snapshot()
    flow = app(
        reasoner.name,
        tools=["lookup"],
        tool_aliases={"lookup": "srv/lookup"},
        max_rounds=3,
        native_tools=True,
    )
    capabilities = CapabilityManifest.from_dict(
        {"tools": [{"name": "srv/lookup", "maxCalls": 1}]}
    )
    spec = PipelineSpec(
        name="limited-agent",
        flow=flow,
        reasoners=(reasoner,),
        capabilities=capabilities,
        snapshot=snapshot,
    )
    prepared = LocalPipeline(
        name=spec.name,
        environment="local",
        compiled=CompiledPipeline(
            spec=spec,
            deployment=deploy(
                flow,
                snapshot=snapshot,
                capabilities=capabilities,
            ),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={reasoner.name: reasoner},
    )
    model_calls = 0
    effect_calls = 0

    async def llm(
        _reasoner: Any,
        _value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
        **_kwargs: Any,
    ) -> Any:
        nonlocal model_calls
        model_calls += 1
        return {
            "tool_calls": [
                {
                    "id": f"lookup-{model_calls}",
                    "tool": "lookup",
                    "input": {"query": "julep"},
                }
            ]
        }

    async def mcp_call(*_args: Any, **_kwargs: Any) -> Any:
        nonlocal effect_calls
        effect_calls += 1
        return {"found": "JULEP"}

    with pytest.raises(AgentTerminalError) as exc_info:
        prepared.run(
            {"query": "julep"},
            llm=llm,
            context=WorkerContext(mcp_call=mcp_call),
        )

    assert exc_info.value.result["status"] == "denied"
    assert exc_info.value.result["reason"] == "tool 'lookup' exceeded maxCalls=1"
    assert model_calls == 2
    assert effect_calls == 1


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


def test_configured_local_pipeline_awaits_async_native_tool(tmp_path: Path) -> None:
    _direct_effect_project(tmp_path)
    prepared = prepare_local_pipeline("async-native", project_root=tmp_path)

    assert prepared.run("julep") == "JULEP"


def test_configured_local_pipeline_validates_frozen_mcp_before_dispatch(
    tmp_path: Path,
) -> None:
    _direct_effect_project(tmp_path)
    calls: list[dict[str, Any]] = []

    async def mcp(
        server: str,
        tool: str,
        value: Any,
        cid: str,
        principal: Any,
        secrets: Any,
        input_schema_validated: bool,
    ) -> Any:
        calls.append(
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
        return {"result": value["query"]}

    prepared = prepare_local_pipeline("typed-mcp", project_root=tmp_path)
    context = WorkerContext(mcp_call=mcp)

    assert prepared.run({"query": "ok"}, context=context) == {"result": "ok"}
    assert calls[0]["validated"] is True

    with pytest.raises(ToolInputValidation, match="srv/typed"):
        prepared.run({"query": 7}, context=context)
    assert len(calls) == 1


def test_configured_local_pipeline_rejects_mixed_controller_tool_surfaces() -> None:
    model_called = False
    reasoner = Reasoner("shared-controller", "test:shared")
    snapshot = _lookup_snapshot()
    flow = seq(
        app(
            reasoner.name,
            tools=["lookup"],
            tool_aliases={"lookup": "srv/lookup"},
            max_rounds=1,
            native_tools=True,
        ),
        app(reasoner.name, max_rounds=1),
    )
    spec = PipelineSpec(
        name="mixed-controller-surface",
        flow=flow,
        reasoners=(reasoner,),
        snapshot=snapshot,
    )
    prepared = LocalPipeline(
        name=spec.name,
        environment="local",
        compiled=CompiledPipeline(
            spec=spec,
            deployment=deploy(flow, snapshot=snapshot),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={reasoner.name: reasoner},
    )

    async def llm(
        _reasoner: Any,
        _value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
        *,
        tools: Any = None,
    ) -> Any:
        del tools
        nonlocal model_called
        model_called = True
        return {"done": True, "output": "unused"}

    async def mcp_call(*_args: Any, **_kwargs: Any) -> Any:
        return {"unused": True}

    with pytest.raises(
        LocalExecutionConfigurationError,
        match="different frozen tool surfaces",
    ):
        prepared.run({}, llm=llm, context=WorkerContext(mcp_call=mcp_call))
    assert model_called is False


def test_local_pipeline_rejects_toolful_agent_and_think_reasoner_reuse() -> None:
    reasoner = Reasoner("shared-think-controller", "test:shared")
    snapshot = _lookup_snapshot()
    flow = seq(
        think(reasoner.name),
        app(
            reasoner.name,
            tools=["lookup"],
            tool_aliases={"lookup": "srv/lookup"},
            max_rounds=1,
            native_tools=True,
        ),
    )
    spec = PipelineSpec(
        name="mixed-think-agent-surface",
        flow=flow,
        reasoners=(reasoner,),
        snapshot=snapshot,
    )
    prepared = LocalPipeline(
        name=spec.name,
        environment="local",
        compiled=CompiledPipeline(
            spec=spec,
            deployment=deploy(flow, snapshot=snapshot),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={reasoner.name: reasoner},
    )
    model_called = False

    async def llm(
        _reasoner: Any,
        _value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
        **_kwargs: Any,
    ) -> Any:
        nonlocal model_called
        model_called = True
        return {"done": True, "output": "unused"}

    async def mcp_call(*_args: Any, **_kwargs: Any) -> Any:
        return {"unused": True}

    with pytest.raises(
        LocalExecutionConfigurationError,
        match="both ordinary foreground reasoning and a native-tool agent",
    ):
        prepared.run({}, llm=llm, context=WorkerContext(mcp_call=mcp_call))
    assert model_called is False


def test_local_pipeline_non_native_agent_does_not_send_provider_tools() -> None:
    reasoner = Reasoner("legacy-controller", "test:legacy")
    snapshot = _lookup_snapshot()
    flow = app(
        reasoner.name,
        tools=["lookup"],
        tool_aliases={"lookup": "srv/lookup"},
        max_rounds=2,
    )
    spec = PipelineSpec(
        name="legacy-agent",
        flow=flow,
        reasoners=(reasoner,),
        snapshot=snapshot,
    )
    prepared = LocalPipeline(
        name=spec.name,
        environment="local",
        compiled=CompiledPipeline(
            spec=spec,
            deployment=deploy(flow, snapshot=snapshot),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={reasoner.name: reasoner},
    )
    model_calls = 0
    effect_calls = 0

    async def strict_five_argument_llm(
        _reasoner: Any,
        _value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
    ) -> Any:
        nonlocal model_calls
        model_calls += 1
        if model_calls == 1:
            return {"tool": "lookup", "input": {"query": "julep"}}
        return {"done": True, "output": "done"}

    async def mcp_call(*_args: Any, **_kwargs: Any) -> Any:
        nonlocal effect_calls
        effect_calls += 1
        return {"found": "JULEP"}

    result = prepared.run(
        {"query": "julep"},
        llm=strict_five_argument_llm,
        context=WorkerContext(mcp_call=mcp_call),
    )

    assert result["status"] == "done"
    assert result["output"] == "done"
    assert model_calls == 2
    assert effect_calls == 1


def test_local_pipeline_rejects_agent_subflows_before_model_io() -> None:
    reasoner = Reasoner("subflow-controller", "test:subflow")
    snapshot = _lookup_snapshot()
    flow = app(
        reasoner.name,
        subflows=["child"],
        max_rounds=1,
    )
    spec = PipelineSpec(
        name="agent-subflow",
        flow=flow,
        reasoners=(reasoner,),
        snapshot=snapshot,
    )
    prepared = LocalPipeline(
        name=spec.name,
        environment="local",
        compiled=CompiledPipeline(
            spec=spec,
            deployment=deploy(flow, snapshot=snapshot),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={reasoner.name: reasoner},
    )
    model_called = False

    async def llm(
        _reasoner: Any,
        _value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
    ) -> Any:
        nonlocal model_called
        model_called = True
        return {"sub": "child", "input": {}}

    with pytest.raises(LocalExecutionUnsupported, match="agent subflows"):
        prepared.run({}, llm=llm)
    assert model_called is False


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


def test_embedded_value_envelope_projection_and_sync_parity() -> None:
    flow = typed_seq(_increment, _increment).to_ir()
    prepared = LocalPipeline(
        name="two-step",
        environment="local",
        compiled=CompiledPipeline(
            spec=PipelineSpec(name="two-step", flow=flow, tools=(_increment,)),
            deployment=deploy(flow, tools=(_increment,)),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={},
    )
    projection = InMemoryProjection()

    assert run(prepared.arun(1)) == 3
    detailed = run(prepared.arun_detailed(1, projection=projection))
    sync_detailed = prepared.run_detailed(1)

    assert isinstance(detailed, EmbeddedRun)
    assert detailed.value == sync_detailed.value == 3
    assert detailed.projection is projection
    assert detailed.artifact_hash == prepared.artifact_hash
    assert sync_detailed.artifact_hash == prepared.artifact_hash

    async def inside_loop() -> None:
        with pytest.raises(LocalExecutionConfigurationError, match="active event loop"):
            prepared.run_detailed(1)

    asyncio.run(inside_loop())


def test_embedded_sink_order_and_failure_projection() -> None:
    successful = deploy(typed_seq(_increment, _increment).to_ir(), tools=(_increment,))
    sink = _EventSink()

    assert run(successful.adry_run(1, sink=sink)).value == 3
    assert [event.type for event in sink.events] == [
        EventType.PLANNED,
        EventType.PLANNED,
        EventType.DID,
        EventType.PLANNED,
        EventType.DID,
        EventType.DID,
    ]

    failing_flow = call(native(_raise_tool.name))
    failing_spec = PipelineSpec(name="failing", flow=failing_flow, tools=(_raise_tool,))
    failing = LocalPipeline(
        name="failing",
        environment="local",
        compiled=CompiledPipeline(
            spec=failing_spec,
            deployment=deploy(failing_flow, tools=(_raise_tool,)),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={},
    )
    failure_sink = _EventSink()
    projection = InMemoryProjection()
    with pytest.raises(RuntimeError, match="batch-e-boom"):
        run(failing.arun_detailed(None, sink=failure_sink, projection=projection))

    assert [event.type for event in failure_sink.events] == [
        EventType.PLANNED,
        EventType.FAILED,
    ]
    assert projection.failures()[0].error == "RuntimeError('batch-e-boom')"


def test_embedded_worker_context_records_trajectory_and_attempts(
    tmp_path: Path,
) -> None:
    _reasoner_project(tmp_path)
    trajectory = InMemoryTrajectoryStore()
    blobs = InMemoryBlobStore()
    attempts = []

    def redact(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: "[local-redacted]" if key == "secret" else child
                for key, child in value.items()
            }
        return value

    async def llm(
        _reasoner: Any,
        value: Any,
        _principal: Any,
        _transcript: Any,
        _dispatch: Any,
    ) -> Any:
        return {"answer": value["text"], "secret": "model-secret"}

    context = WorkerContext(
        llm=llm,
        on_attempt=attempts.append,
        trajectory_sink=trajectory,
        trajectory_blob_store=blobs,
        redactor=redact,
    )
    result = prepare_local_pipeline("summary", project_root=tmp_path).run_detailed(
        {"text": "hello", "secret": "input-secret"},
        context=context,
        run_id="embedded-observed",
    )

    assert result.value["answer"] == "hello"
    assert [attempt.outcome for attempt in attempts] == ["ok"]
    run_record = trajectory.get_trajectory_run("embedded-observed")
    assert run_record is not None
    assert run_record.status == "completed"
    [step] = trajectory.list_trajectory_steps("embedded-observed")
    assert step.op == "think"
    assert step.input_ref is not None
    assert step.output_ref is not None
    stored_input = json.loads(
        run(blobs.get("embedded-observed", step.input_ref)).decode()
    )
    stored_output = json.loads(
        run(blobs.get("embedded-observed", step.output_ref)).decode()
    )
    assert stored_input["secret"] == "[local-redacted]"
    assert stored_output["secret"] == "[local-redacted]"


def test_embedded_model_ladder_attempt_callback_fires_once(tmp_path: Path) -> None:
    _reasoner_project(tmp_path)
    attempts = []
    callback = attempts.append

    async def base(reasoner: Reasoner, *_args: Any, **_kwargs: Any) -> LlmResult:
        return LlmResult(
            reply={"answer": "ok"},
            meta=LlmCallMeta(served_model=reasoner.model, provider="test"),
        )

    caller = with_model_ladder(base, models=[], on_attempt=callback)
    prepare_local_pipeline("summary", project_root=tmp_path).run_detailed(
        {"text": "hello"},
        context=WorkerContext(llm=caller, on_attempt=callback),
    )

    assert [attempt.outcome for attempt in attempts] == ["ok"]


def test_embedded_llm_result_usage_and_unknown_cost_are_projected(
    tmp_path: Path,
) -> None:
    _reasoner_project(tmp_path)

    async def llm(*_args: Any, **_kwargs: Any) -> LlmResult:
        return LlmResult(
            reply={"answer": "ok"},
            meta=LlmCallMeta(
                served_model="test:served",
                provider="unknown-provider",
                input_tokens=11,
                output_tokens=7,
                total_tokens=18,
                attempts=(AttemptMeta("test:served", "unknown-provider", "ok", 11, 7),),
            ),
        )

    detailed = prepare_local_pipeline("summary", project_root=tmp_path).run_detailed(
        {"text": "hello"}, llm=llm
    )
    [did] = [event for event in detailed.projection.events() if event.type is EventType.DID]

    assert did.attrs["llm.usage"] == {"input": 11, "output": 7, "total": 18}
    assert did.attrs["llm.cost.status"] == "unknown"
    assert detailed.projection.cost_by_shape() == {}


def test_embedded_run_aggregates_usage_and_mixed_cost_without_charging_derived() -> None:
    flow = seq(think("first"), think("second"))
    first = Reasoner("first", "test:first")
    second = Reasoner("second", "test:second")
    prepared = LocalPipeline(
        name="metered",
        environment="local",
        compiled=CompiledPipeline(
            spec=PipelineSpec(name="metered", flow=flow, reasoners=(first, second)),
            deployment=deploy(flow, tools=(), reasoners=(first, second)),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={
            "first": first,
            "second": second,
        },
    )

    async def llm(reasoner: Reasoner, *_args: Any, **_kwargs: Any) -> LlmResult:
        first = reasoner.name == "first"
        usage = LlmUsage(
            prompt_tokens=10 if first else 20,
            completion_tokens=2 if first else 3,
            total_tokens=12 if first else 23,
            cache_read_tokens=1 if first else 4,
            cache_creation_tokens=0,
        )
        return LlmResult(
            reply=f"{reasoner.name}-reply",
            meta=LlmCallMeta(
                served_model=reasoner.model,
                provider="test",
                usage=usage,
                cost=0.01 if first else 0.02,
                cost_status="reported" if first else "derived",
            ),
        )

    detailed = prepared.run_detailed("hello", llm=llm)

    assert detailed.usage == LlmUsage(30, 5, 35, 5, 0)
    assert detailed.usage_complete is True
    assert detailed.total_cost == pytest.approx(0.03)
    assert detailed.cost_status == "mixed"
    assert detailed.cost_complete is True
    # Only the reported leg remains a projection charge. The pricing-map
    # derivation is metadata, so durable Event.cost semantics do not change.
    assert sum(detailed.projection.cost_by_shape().values()) == pytest.approx(0.01)


def test_embedded_run_totals_are_scoped_to_reused_projection_invocation() -> None:
    reasoner = Reasoner("metered", "test:metered")
    flow = think(reasoner.name)
    prepared = LocalPipeline(
        name="metered",
        environment="local",
        compiled=CompiledPipeline(
            spec=PipelineSpec(name="metered", flow=flow, reasoners=(reasoner,)),
            deployment=deploy(flow, tools=(), reasoners=(reasoner,)),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={reasoner.name: reasoner},
    )

    async def llm(*_args: Any, **_kwargs: Any) -> LlmResult:
        return LlmResult(
            reply="ok",
            meta=LlmCallMeta(
                served_model=reasoner.model,
                provider="test",
                usage=LlmUsage(8, 2, 10),
                cost=0.01,
                cost_status="reported",
            ),
        )

    projection = InMemoryProjection()
    prepared.run_detailed("first", llm=llm, projection=projection)
    second = prepared.run_detailed("second", llm=llm, projection=projection)

    assert second.usage == LlmUsage(8, 2, 10)
    assert second.total_cost == pytest.approx(0.01)


def test_embedded_run_totals_include_unattributed_agent_controller_calls() -> None:
    reasoner = Reasoner("controller", "test:controller")
    flow = app(reasoner.name, max_rounds=1)
    spec = PipelineSpec(name="agent", flow=flow, reasoners=(reasoner,))
    prepared = LocalPipeline(
        name=spec.name,
        environment="local",
        compiled=CompiledPipeline(
            spec=spec,
            deployment=deploy(flow, tools=(), reasoners=(reasoner,)),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={reasoner.name: reasoner},
    )

    async def llm(*_args: Any, **_kwargs: Any) -> LlmResult:
        return LlmResult(
            reply={"done": True, "output": "done"},
            meta=LlmCallMeta(
                served_model=reasoner.model,
                provider="test",
                usage=LlmUsage(12, 3, 15),
                cost=0.02,
                cost_status="reported",
            ),
        )

    detailed = prepared.run_detailed({}, llm=llm)

    assert not any("llm.usage" in event.attrs for event in detailed.projection.events())
    assert detailed.usage == LlmUsage(12, 3, 15)
    assert detailed.total_cost == pytest.approx(0.02)


def test_failed_foreground_primitive_is_retained_in_trajectory() -> None:
    flow = call(native(_raise_tool.name))
    spec = PipelineSpec(name="failing", flow=flow, tools=(_raise_tool,))
    prepared = LocalPipeline(
        name=spec.name,
        environment="local",
        compiled=CompiledPipeline(
            spec=spec,
            deployment=deploy(flow, tools=(_raise_tool,)),
            declared_schema_hash="test",
            compiled_schema_hash="test",
        ),
        reasoners={},
    )
    trajectory = InMemoryTrajectoryStore()

    with pytest.raises(RuntimeError, match="batch-e-boom"):
        prepared.run_detailed(
            None,
            context=WorkerContext(trajectory_sink=trajectory),
            run_id="failed-primitive",
        )

    [step] = trajectory.list_trajectory_steps("failed-primitive")
    assert step.op == "prim"
    assert step.status == "failed"
    assert step.error == "RuntimeError('batch-e-boom')"


def test_deployment_retry_uses_injected_backoff_and_none_sleeper() -> None:
    flow = call(
        native(_raise_tool.name),
        ann=Ann(max_attempts=3, retry_interval_s=0.25, backoff_rate=2.0),
    )
    deployment = deploy(flow, tools=(_raise_tool,))
    sleeps: list[float] = []

    async def sleeper(interval: float) -> None:
        sleeps.append(interval)

    with pytest.raises(RuntimeError, match="batch-e-boom"):
        run(deployment.adry_run(None, sleeper=sleeper))
    assert sleeps == [0.25, 0.5]

    with pytest.raises(RuntimeError, match="batch-e-boom"):
        run(deployment.adry_run(None, sleeper=None))


def test_load_pipeline_fixture_names_env_exports_and_kubernetes_name_escape(
    tmp_path: Path,
) -> None:
    import julep
    import julep.embedded as embedded

    fixture = Path(__file__).parent / "fixtures/memmcp/episode_summary.ctx"
    seen: list[tuple[str, str]] = []

    async def llm(reasoner: Any, value: Any, *_args: Any) -> Any:
        seen.append((reasoner.model, value["episode_id"]))
        return "summary"

    default = embedded.load_pipeline(fixture, env={"SUMMARY_MODEL": "test:env"})
    explicit = embedded.load_pipeline(
        fixture, name="custom-summary", env={"SUMMARY_MODEL": "test:env"}
    )
    assert default.name == "episode_summary"
    assert explicit.name == "custom-summary"
    assert default.run({"episode_id": "42"}, llm=llm) == "summary"
    assert seen == [("test:env", "42")]

    invalid_root = tmp_path / "---"
    copied_ctx = invalid_root / "episode_summary.ctx"
    shutil.copytree(fixture, copied_ctx)
    (invalid_root / "pyproject.toml").write_text(
        '[tool.julep]\n\n[tool.julep.pipeline.summary]\nctx = "episode_summary.ctx"\n'
        '\n[tool.julep.env.local.vars]\nSUMMARY_MODEL = "test:env"\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="application name|Kubernetes|label"):
        prepare_local_pipeline("summary", project_root=invalid_root)
    assert embedded.load_pipeline(copied_ctx, env={"SUMMARY_MODEL": "test:env"}).run(
        {"episode_id": "43"}, llm=llm
    ) == "summary"

    assert julep.EmbeddedRun is embedded.EmbeddedRun
    assert julep.LlmResult is LlmResult
    assert embedded.WorkerContext is WorkerContext


def test_configured_llm_precedence_and_prepare_time_resolution(tmp_path: Path) -> None:
    _reasoner_project(tmp_path)
    config_path = tmp_path / "pyproject.toml"
    config_path.write_text(
        config_path.read_text(encoding="utf-8").replace(
            "[tool.julep]\n", f'[tool.julep]\nllm_caller = "{__name__}:configured_test_llm"\n'
        ),
        encoding="utf-8",
    )
    prepared = prepare_local_pipeline("summary", project_root=tmp_path)

    async def context_llm(*_args: Any, **_kwargs: Any) -> Any:
        return {"answer": "context"}

    async def explicit_llm(*_args: Any, **_kwargs: Any) -> Any:
        return {"answer": "explicit"}

    assert prepared.run({"source": "cfg"}) == {"answer": "configured:cfg"}
    assert prepared.run({"source": "ctx"}, context=WorkerContext(llm=context_llm)) == {
        "answer": "context"
    }
    assert prepared.run(
        {"source": "explicit"},
        llm=explicit_llm,
        context=WorkerContext(llm=context_llm),
    ) == {"answer": "explicit"}
    assert prepared.configured_llm is configured_test_llm

    unconfigured_root = tmp_path / "unconfigured"
    unconfigured_root.mkdir()
    _reasoner_project(unconfigured_root)
    with pytest.raises(LocalExecutionConfigurationError, match=r"\[tool\.julep\] llm_caller"):
        prepare_local_pipeline("summary", project_root=unconfigured_root).run({})
