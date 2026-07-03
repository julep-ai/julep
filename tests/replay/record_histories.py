"""Regenerate the Temporal workflow replay corpus.

Run with:

    uv run python tests/replay/record_histories.py

The generated histories under ``tests/replay/histories/*.json`` are committed
and replayed at HEAD. Regenerate them only in the same PR that adds a
``workflow.patched(...)`` compatibility gate or intentionally changes the
Build-ID / worker-versioning story. Never regenerate histories just to "fix the
test"; a replay failure is evidence of a nondeterministic workflow change.
"""

from __future__ import annotations

import asyncio
import json
import pathlib
from dataclasses import dataclass
from typing import Any, ClassVar, Optional

from temporalio import activity, workflow
from temporalio.client import WorkflowHistory
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Replayer, Worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions

from composable_agents import (
    DEFAULT_REGISTRY,
    Reasoner,
    arr,
    call,
    each,
    freeze,
    manifest_to_json,
    mcp,
    par,
    register_pure,
    seq,
    sub,
)
from composable_agents.contracts import McpAnnotations
from composable_agents.derived import recv as recv_leaf
from composable_agents.execution.activities import WorkerContext, configure
from composable_agents.execution.batch_provider import BatchProvider, register_batch_provider
from composable_agents.execution.bundle_runner import BundleResolvingWorkflowRunner
from composable_agents.execution.debounce import submit_debounced
from composable_agents.execution.harness import (
    AgentInput,
    AgentWorkflow,
    ExecutionPolicy,
    SessionInput,
    SessionWorkflow,
    start_flow,
)
from composable_agents.execution.reasoner_batch import (
    BatchDispatchContext,
    ReasonerCall,
    install_batch_dispatch_context,
    provider_safe_custom_id,
    submit_reasoner_batch,
)
from composable_agents.execution.session_store import InMemorySessionStore
from composable_agents.execution.worker import ACTIVITIES, WORKFLOWS, build_worker
from composable_agents.freeze import McpServerSnapshot, McpSnapshot, McpToolSpec
from composable_agents.session import scan

HISTORIES_DIR = pathlib.Path(__file__).parent / "histories"
CORPUS: list[str] = [
    "flow_par_each_sub",
    "session_multi_turn",
    "session_store",
    "agent_loop",
    "debounce",
    "batch_collector",
    "batch_poll",
]


@dataclass
class FakeMessage:
    content: Optional[str] = None
    parsed: Any = None


@dataclass
class FakeChoice:
    message: FakeMessage


@dataclass
class FakeCompletion:
    choices: list[FakeChoice]


@workflow.defn(name="ReasonerBatchReceiver")
class ReceiverWorkflow:
    def __init__(self) -> None:
        self._inbox: list[dict[str, Any]] = []

    @workflow.signal(name="submitReasonerResult")
    def submit_reasoner_result(self, item: Any) -> None:
        self._inbox.append(dict(item))

    @workflow.run
    async def run(self) -> Any:
        await workflow.wait_condition(lambda: bool(self._inbox))
        reply = self._inbox[0]["reply"]
        if isinstance(reply, dict) and "__ca_meta__" in reply:
            return reply["reply"]
        return reply


class FakeBatch(BatchProvider):
    values: ClassVar[dict[str, Any]] = {}
    requests_by_batch: ClassVar[dict[str, list[dict[str, Any]]]] = {}
    # BatchPoll workflow ids observed in ``submit`` (runs in the submitBatch
    # activity under the detached BatchPoll child), captured so the recorder can
    # locate the poll workflow's history without depending on a signal-with-start
    # handle exposing its run id.
    poll_workflow_ids: ClassVar[list[str]] = []

    def build_request(
        self,
        custom_id: str,
        reasoner: Any,
        value: Any,
        *,
        transcript: Any = None,
        dispatch: Any = None,
    ) -> dict[str, Any]:
        del reasoner, transcript, dispatch
        type(self).values[custom_id] = value
        return {"custom_id": custom_id}

    async def submit(self, requests: list[dict[str, Any]]) -> str:
        type(self).poll_workflow_ids.append(activity.info().workflow_id or "")
        type(self).requests_by_batch["bx"] = list(requests)
        return "bx"

    async def poll_status(self, batch_id: str) -> str:
        assert batch_id == "bx"
        return "completed"

    async def results(self, batch_id: str) -> Any:
        assert batch_id == "bx"
        for request in type(self).requests_by_batch[batch_id]:
            custom_id = str(request["custom_id"])
            value = type(self).values[custom_id]
            yield (
                custom_id,
                FakeCompletion(choices=[FakeChoice(FakeMessage(content=str(value)))]),
            )


def _snapshot(*tools: str) -> McpSnapshot:
    ann = McpAnnotations(read_only_hint=True, idempotent_hint=True)
    return McpSnapshot(servers={
        "srv": McpServerSnapshot(
            server="srv",
            version="1",
            tools={tool: McpToolSpec(input_schema={}, annotations=ann) for tool in tools},
        )
    })


def _session_echo_step(value: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    carrier = value["carrier"]
    msg = value["msg"]
    n = (carrier or 0) + 1
    return (n, {"echo": msg, "turn": n})


async def _mcp(
    server: str,
    tool: str,
    value: Any,
    idempotency_key: str,
    principal: Optional[dict[str, Any]] = None,
) -> Any:
    del server, idempotency_key, principal
    if tool == "double":
        return value * 2
    if tool == "inc":
        return value + 1
    if tool == "echo":
        return value
    raise ValueError(tool)


def setup_registries() -> None:
    if "test.corpus_session_step" not in DEFAULT_REGISTRY.pures:
        register_pure("test.corpus_session_step", _session_echo_step)
    DEFAULT_REGISTRY.register_reasoner(
        Reasoner(name="corpus_ctrl", model="test", system="decide")
    )
    DEFAULT_REGISTRY.register_reasoner(
        Reasoner(name="corpus_echo", model="fake:m", system="", reply=None)
    )
    # The collector key exercises provider="corpusfake"; submitBatch selects the
    # adapter from the rendered reasoner model ("fake:m") in the current runtime.
    register_batch_provider("fake", FakeBatch)
    register_batch_provider("corpusfake", FakeBatch)


def _shared_runner() -> BundleResolvingWorkflowRunner:
    return BundleResolvingWorkflowRunner(
        inner=SandboxedWorkflowRunner(
            restrictions=SandboxRestrictions.default.with_passthrough_modules(
                "composable_agents",
                "wasmtime",
            )
        ),
        store=None,
    )


def make_replayer() -> Replayer:
    setup_registries()
    return Replayer(workflows=WORKFLOWS, workflow_runner=_shared_runner())


async def _record_flow_par_each_sub(client: Any) -> WorkflowHistory:
    # Covers all three FlowWorkflow fan-out operators in one history: par
    # (static fan-out), each (dynamic per-element fan-out), and sub (child
    # workflow). Input is a list so `each` has elements to iterate.
    child = freeze(call(mcp("srv", "echo")), _snapshot("echo"))
    subflows = {
        "child": {
            "flowJson": child.flow.to_json(),
            "manifestJson": manifest_to_json(child.manifest),
        }
    }
    fr = freeze(
        par(each(call(mcp("srv", "inc"))), sub("child")),
        _snapshot("inc"),
    )
    ctx = WorkerContext(mcp_call=_mcp, llm=None, subflows=subflows)
    async with build_worker(client, ctx, task_queue="corpus-flow"):
        handle = await start_flow(
            client,
            fr.flow.to_json(),
            manifest_to_json(fr.manifest),
            session_id="corpus-flow",
            input=[1, 2],
            task_queue="corpus-flow",
        )
        await handle.result()
        hist = await handle.fetch_history()
    return hist


async def _record_session_multi_turn(client: Any) -> WorkflowHistory:
    turn = seq(recv_leaf("in"), arr("test.corpus_session_step"))
    session = scan(turn, init=0, in_channel="in", out_channel="out")
    fr = freeze(session.body, McpSnapshot())
    store = InMemorySessionStore(empty_value=0)
    ctx = WorkerContext(session_store=store, mcp_call=None)
    async with build_worker(client, ctx, task_queue="corpus-session"):
        handle = await client.start_workflow(
            SessionWorkflow.run,
            SessionInput(
                session_id="corpus-session",
                flow_json=fr.flow.to_json(),
                manifest_json=manifest_to_json(fr.manifest),
                init=0,
                in_channel="in",
                out_channel="out",
                policy=ExecutionPolicy().to_json(),
            ),
            id="corpus-session",
            task_queue="corpus-session",
        )
        await handle.execute_update("send", {"channel": "in", "value": "a"})
        await handle.execute_update("send", {"channel": "in", "value": "b"})
        await handle.execute_update("close", {})
        await handle.result()
        hist = await handle.fetch_history()
    return hist


async def _record_session_store(client: Any) -> WorkflowHistory:
    # Store-backed carrier: state_cursor set (no carrier) forces _load_carrier to
    # schedule the loadValue activity at start; history_threshold=1 forces a
    # continue-as-new after the first turn, which schedules the commitValue
    # activity. We record the FIRST run so both loadValue and commitValue plus the
    # CONTINUED_AS_NEW boundary land in the corpus.
    turn = seq(recv_leaf("in"), arr("test.corpus_session_step"))
    session = scan(turn, init=0, in_channel="in", out_channel="out")
    fr = freeze(session.body, McpSnapshot())
    store = InMemorySessionStore(empty_value=0)
    ctx = WorkerContext(session_store=store, mcp_call=None)
    async with build_worker(client, ctx, task_queue="corpus-session-store"):
        handle = await client.start_workflow(
            SessionWorkflow.run,
            SessionInput(
                session_id="corpus-session-store",
                flow_json=fr.flow.to_json(),
                manifest_json=manifest_to_json(fr.manifest),
                init=0,
                in_channel="in",
                out_channel="out",
                policy=ExecutionPolicy().to_json(),
                state_cursor=0,
                history_threshold=1,
            ),
            id="corpus-session-store",
            task_queue="corpus-session-store",
        )
        await handle.execute_update("send", {"channel": "in", "value": "a"})
        await handle.execute_update("close", {})
        await handle.result()
        first_run_id = handle.first_execution_run_id
        assert first_run_id, "session-store handle has no first_execution_run_id"
        hist = await client.get_workflow_handle(
            handle.id, run_id=first_run_id
        ).fetch_history()
    return hist


async def _record_agent_loop(client: Any) -> WorkflowHistory:
    agents = {
        "corpus_ctrl": {
            "config": {"maxRounds": 6, "budget": {"cost": 1000}, "continueAsNewAfter": 2},
            "grantedTools": ["srv/double"],
            "grantedSubflows": ["child"],
        }
    }

    async def _agent_llm(reasoner: Any, value: dict[str, Any]) -> Any:
        if reasoner.name == "corpus_ctrl":
            n = len(value.get("trace", []))
            if n == 0:
                return {"tool": "srv/double", "input": value["input"]}
            if n == 1:
                return {"sub": "child", "input": value["input"]}
            return {"done": True, "output": value["input"]}
        return value

    child = freeze(call(mcp("srv", "inc")), _snapshot("inc"))
    subflows = {
        "child": {
            "flowJson": child.flow.to_json(),
            "manifestJson": manifest_to_json(child.manifest),
        }
    }
    ctx = WorkerContext(mcp_call=_mcp, llm=_agent_llm, subflows=subflows, agents=agents)
    async with build_worker(client, ctx, task_queue="corpus-agent"):
        handle = await client.start_workflow(
            AgentWorkflow.run,
            AgentInput(
                controller="corpus_ctrl",
                session_id="corpus-agent",
                input=5,
                policy=ExecutionPolicy().to_json(),
            ),
            id="corpus-agent",
            task_queue="corpus-agent",
        )
        await handle.result()
        first_run_id = handle.first_execution_run_id
        assert first_run_id, "agent handle has no first_execution_run_id"
        hist = await client.get_workflow_handle(
            handle.id, run_id=first_run_id
        ).fetch_history()
    return hist


async def _record_debounce(client: Any) -> WorkflowHistory:
    fr = freeze(each(call(mcp("srv", "inc"))), _snapshot("inc"))
    ctx = WorkerContext(mcp_call=_mcp, llm=None)
    async with build_worker(client, ctx, task_queue="corpus-debounce"):
        handle = await submit_debounced(
            client,
            fr.flow.to_json(),
            manifest_to_json(fr.manifest),
            key="corpus-debounce",
            item=1,
            quiet_s=1,
            task_queue="corpus-debounce",
        )
        await handle.result()
        hist = await handle.fetch_history()
    return hist


async def _record_batch(client: Any) -> dict[str, WorkflowHistory]:
    tq = "corpus-batch"
    FakeBatch.values.clear()
    FakeBatch.requests_by_batch.clear()
    FakeBatch.poll_workflow_ids.clear()
    ctx = WorkerContext(mcp_call=None, llm=None)
    configure(ctx)
    install_batch_dispatch_context(BatchDispatchContext(client=client, task_queue=tq))
    worker = Worker(
        client,
        task_queue=tq,
        workflows=[*WORKFLOWS, ReceiverWorkflow],
        activities=ACTIVITIES,
        workflow_runner=_shared_runner(),
    )
    async with worker:
        receiver = await client.start_workflow(
            ReceiverWorkflow.run,
            id="corpus-receiver",
            task_queue=tq,
        )
        custom_id = provider_safe_custom_id("corpus-receiver:0:think@1")
        collector_handle = await submit_reasoner_batch(
            client,
            provider="corpusfake",
            qos="BATCH",
            principal=None,
            call=ReasonerCall(
                reasoner="corpus_echo",
                value=7,
                cid="think@1",
                reply_to="corpus-receiver",
                custom_id=custom_id,
            ),
            quiet_s=600,
            max_items=1,
            max_wait_s=600,
            task_queue=tq,
        )
        await receiver.result()
        del collector_handle
        collector_id = "batch:corpusfake:BATCH:"
        # The BatchPoll child id is f"{collector_id}:p{seq}:{collector_run_id}"
        # (reasoner_batch.py). Recover both the poll id and the collector's
        # first-run id (the run that fired the batch) from the workflow id the
        # provider saw inside the submitBatch activity.
        assert FakeBatch.poll_workflow_ids, "BatchPoll never ran; nothing to record"
        poll_id = FakeBatch.poll_workflow_ids[0]
        marker = ":p0:"
        assert marker in poll_id, f"unexpected BatchPoll id shape: {poll_id!r}"
        collector_run_id = poll_id.split(marker, 1)[1]
        hist_coll = await client.get_workflow_handle(
            collector_id,
            run_id=collector_run_id,
        ).fetch_history()
        hist_poll = await client.get_workflow_handle(poll_id).fetch_history()
    return {
        "batch_collector": hist_coll,
        "batch_poll": hist_poll,
    }


async def record_all() -> None:
    setup_registries()
    HISTORIES_DIR.mkdir(parents=True, exist_ok=True)
    written: list[pathlib.Path] = []
    print("starting time-skipping replay corpus recorder", flush=True)
    async with await WorkflowEnvironment.start_time_skipping() as env:
        scenarios: dict[str, WorkflowHistory] = {}
        for name, record in (
            ("flow_par_each_sub", _record_flow_par_each_sub),
            ("session_multi_turn", _record_session_multi_turn),
            ("session_store", _record_session_store),
            ("agent_loop", _record_agent_loop),
            ("debounce", _record_debounce),
        ):
            print(f"recording {name}", flush=True)
            scenarios[name] = await record(env.client)
            print(f"recorded {name}", flush=True)
        print("recording batch_collector and batch_poll", flush=True)
        scenarios.update(await _record_batch(env.client))
        print("recorded batch_collector and batch_poll", flush=True)
    # ``to_json`` drops the workflow id, but replay reconstructs
    # ``workflow.info().workflow_id`` from the id passed to ``from_json`` — and
    # some workflows derive child ids from it (e.g. BatchCollector's poll child).
    # Persist a name -> real workflow id manifest so the replay test supplies the
    # recorded id, not the corpus basename.
    manifest: dict[str, str] = {}
    for name in CORPUS:
        hist = scenarios[name]
        path = HISTORIES_DIR / f"{name}.json"
        path.write_text(hist.to_json())
        manifest[name] = hist.workflow_id
        written.append(path)
    manifest_path = HISTORIES_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    written.append(manifest_path)
    print("wrote replay histories:")
    for path in written:
        print(f"  {path}")


if __name__ == "__main__":
    asyncio.run(record_all())
