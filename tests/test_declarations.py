from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Iterator

import pytest

pytest.importorskip("jinja2")

from julep import HAVE_TEMPORAL
from julep.app import Application, ApplicationDefinitionError, PipelineSpec
from julep.app_deploy import WorkflowStartOptions, publish_application
from julep.cas import LocalDirCAS
from julep.declarations import DeclarationError, declarations_blob, load_declarations
from julep.dotctx import Reasoner
from julep.dotctx_rich import load_rich_dotctx
from julep.dsl import think
from julep.execution import effects
from julep.execution.effects import InvokeReasonerInput, WorkerContext
from julep.ir import canonical_json
from julep.prompt import rendered_user_for
from julep.registry import DEFAULT_REGISTRY, Registry, RendererDeclaration, RendererEntry

FIXTURES = Path(__file__).parent / "fixtures"


def _blob_hash(blob: bytes) -> str:
    return "sha256:" + hashlib.sha256(blob).hexdigest()


@contextmanager
def _preserve_default_registry(
    reasoner_name: str,
    renderer_names: tuple[str, ...] = (),
) -> Iterator[None]:
    existing_reasoner = DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
    existing_renderers: dict[str, RendererEntry] = {}
    existing_declarations: dict[str, RendererDeclaration] = {}
    for name in renderer_names:
        renderer = DEFAULT_REGISTRY.renderers.pop(name, None)
        if renderer is not None:
            existing_renderers[name] = renderer
        declaration = DEFAULT_REGISTRY.renderer_declarations.pop(name, None)
        if declaration is not None:
            existing_declarations[name] = declaration
    try:
        yield
    finally:
        DEFAULT_REGISTRY.reasoners.pop(reasoner_name, None)
        for name in renderer_names:
            DEFAULT_REGISTRY.renderers.pop(name, None)
            DEFAULT_REGISTRY.renderer_declarations.pop(name, None)
        if existing_reasoner is not None:
            DEFAULT_REGISTRY.reasoners[reasoner_name] = existing_reasoner
        DEFAULT_REGISTRY.renderers.update(existing_renderers)
        DEFAULT_REGISTRY.renderer_declarations.update(existing_declarations)


def test_load_declarations_rejects_blob_hash_mismatch() -> None:
    reasoner = Reasoner("declarations-hash-mismatch", "model-a", system="hello")
    blob = declarations_blob([reasoner], registry=Registry())

    with pytest.raises(DeclarationError, match="blob hash mismatch"):
        load_declarations(
            blob + b"corrupt",
            expected_hash=_blob_hash(blob),
            registry=Registry(),
        )


def test_load_declarations_rejects_boolean_schema_version() -> None:
    reasoner = Reasoner("declarations-boolean-schema", "model-a", system="hello")
    payload = json.loads(declarations_blob([reasoner], registry=Registry()))
    payload["schemaVersion"] = True
    blob = canonical_json(payload).encode()

    with pytest.raises(DeclarationError, match="unsupported declarations blob schema"):
        load_declarations(blob, expected_hash=_blob_hash(blob), registry=Registry())


def test_load_declarations_rejects_renderer_inputs_inconsistent_with_hash() -> None:
    author_registry = Registry()
    rich = load_rich_dotctx(
        str(FIXTURES / "summarizer.ctx"),
        registry=author_registry,
    )
    payload = json.loads(declarations_blob([rich.reasoner], registry=author_registry))
    renderer = next(iter(payload["renderers"].values()))
    renderer["source"] = ""
    tampered = canonical_json(payload).encode("utf-8")

    with pytest.raises(DeclarationError, match="hash material does not match"):
        load_declarations(
            tampered,
            expected_hash=_blob_hash(tampered),
            registry=Registry(),
        )


def test_rich_renderer_rebuilds_from_blob_without_source_files(tmp_path: Path) -> None:
    package = tmp_path / "portable-researcher.ctx"
    shutil.copytree(FIXTURES / "researcher.ctx", package)
    author_registry = Registry()
    rich = load_rich_dotctx(str(package), registry=author_registry)
    renderer_names = tuple(rich.renderer_names.values())
    context = {"persona": "skeptic", "question": "why?"}
    expected = {
        role: author_registry.get_renderer(name)(context).encode("utf-8")
        for role, name in rich.renderer_names.items()
    }
    blob = declarations_blob([rich.reasoner], registry=author_registry)
    shutil.rmtree(package)

    target = Registry()
    with _preserve_default_registry(rich.reasoner.name, renderer_names):
        load_declarations(blob, expected_hash=_blob_hash(blob), registry=target)

        assert target.get_reasoner(rich.reasoner.name) == rich.reasoner
        for role, name in rich.renderer_names.items():
            assert target.get_renderer(name)(context).encode("utf-8") == expected[role]
            assert DEFAULT_REGISTRY.get_renderer(name)(context).encode("utf-8") == expected[role]
            assert (
                target.renderer_source_hash_of(name)
                == author_registry.renderer_source_hash_of(name)
            )


def test_worker_application_conflict_with_cas_declaration_is_loud() -> None:
    name = "declarations-worker-application-conflict"
    released = Reasoner(name, "model-release", system="release")
    blob = declarations_blob([released], registry=Registry())
    worker_application = Application(
        "worker-cross-check",
        [
            PipelineSpec(
                "pipeline",
                think(name),
                reasoners=(Reasoner(name, "model-worker", system="worker"),),
            )
        ],
    )

    with _preserve_default_registry(name):
        worker_application.register_runtime_declarations(
            expected_hash=worker_application.runtime_declarations_hash
        )

        with pytest.raises(ApplicationDefinitionError, match="conflicts with the verified"):
            load_declarations(
                blob,
                expected_hash=_blob_hash(blob),
                registry=Registry(),
            )


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_batch_submit_hydrates_and_derives_provider_inside_activity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from julep.execution import reasoner_batch
    from julep.execution.reasoner_batch import (
        BatchDispatchContext,
        ReasonerCall,
        SubmitReasonerBatchInput,
        install_batch_dispatch_context,
        submitReasonerBatch,
    )

    name = "declarations-batch-provider"
    reasoner = Reasoner(name, "openai:gpt-5", system="batch")
    blob = declarations_blob([reasoner], registry=Registry())
    store = LocalDirCAS(tmp_path / "cas")
    digest = store.put(blob)
    declarations_ref = {"hash": f"sha256:{digest}", "size": len(blob)}
    captured: dict[str, object] = {}

    class Client:
        async def start_workflow(self, workflow, batch_input, **kwargs):
            captured["input"] = batch_input
            captured["kwargs"] = kwargs
            return "handle"

    previous_context = effects._CTX
    previous_batch_context = reasoner_batch._BATCH_CTX
    with _preserve_default_registry(name):
        monkeypatch.setenv("STORE_URL", f"file://{store.root}")
        effects.configure(WorkerContext(registry=Registry()))
        install_batch_dispatch_context(BatchDispatchContext(client=Client()))
        try:
            asyncio.run(
                submitReasonerBatch(
                    SubmitReasonerBatchInput(
                        provider="",
                        qos="BATCH",
                        principal_key="",
                        call=ReasonerCall(
                            reasoner=name,
                            value={"input": "hello"},
                            custom_id="batch-provider",
                            reply_to="workflow",
                            runtime_declarations_ref=declarations_ref,
                        ),
                    )
                )
            )
        finally:
            effects.configure(previous_context)
            reasoner_batch._BATCH_CTX = previous_batch_context

    batch_input = captured["input"]
    assert batch_input.provider == "openai"
    assert batch_input.pending == []
    call = captured["kwargs"]["start_signal_args"][0]
    assert call.runtime_declarations_ref == declarations_ref


def test_published_pipeline_hydrates_on_generic_worker_with_prompt_byte_parity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    package = tmp_path / "released-researcher.ctx"
    shutil.copytree(FIXTURES / "researcher.ctx", package)
    author_registry = Registry()
    rich = load_rich_dotctx(str(package), registry=author_registry)
    renderer_names = tuple(rich.renderer_names.values())
    value = {"persona": "skeptic", "question": "why?"}
    expected_system = author_registry.get_renderer(rich.renderer_names["system"])(value).encode()
    expected_user = author_registry.get_renderer(rich.renderer_names["user"])(value).encode()
    store = LocalDirCAS(tmp_path / "cas")
    previous_context = effects._CTX

    with _preserve_default_registry(rich.reasoner.name, renderer_names):
        DEFAULT_REGISTRY.register_reasoner(rich.reasoner)
        for name in renderer_names:
            DEFAULT_REGISTRY.renderers[name] = author_registry.renderers[name]
            DEFAULT_REGISTRY.renderer_declarations[name] = (
                author_registry.renderer_declarations[name]
            )
        compiled = Application(
            "portable-release",
            [
                PipelineSpec(
                    "research",
                    think(rich.reasoner.name),
                    reasoners=(rich.reasoner,),
                )
            ],
        ).compile()
        compiled_pipeline = compiled.pipelines[0]
        assert compiled_pipeline.runtime_declarations_blob is not None
        without_blob_change = replace(
            compiled_pipeline,
            runtime_declarations_blob=b"not part of the artifact",
        )
        assert without_blob_change.to_json() == compiled_pipeline.to_json()
        assert replace(compiled, pipelines=(without_blob_change,)).artifact_hash == (
            compiled.artifact_hash
        )
        release = publish_application(
            compiled,
            store,
            worker_image="registry.example/portable@sha256:" + "b" * 64,
            signing_key="0" * 64,
        )
        declarations_ref = release.pipelines[0].runtime_declarations_ref
        assert declarations_ref is not None

        DEFAULT_REGISTRY.reasoners.pop(rich.reasoner.name, None)
        for name in renderer_names:
            DEFAULT_REGISTRY.renderers.pop(name, None)
            DEFAULT_REGISTRY.renderer_declarations.pop(name, None)
        shutil.rmtree(package)

        captured: dict[str, bytes] = {}

        async def llm(reasoner, call_value, _principal, _transcript, _dispatch):
            captured["system"] = reasoner.system.encode("utf-8")
            rendered_user = rendered_user_for(reasoner, call_value)
            assert rendered_user is not None
            captured["user"] = rendered_user.encode("utf-8")
            return "ok"

        monkeypatch.setenv("STORE_URL", f"file://{store.root}")
        monkeypatch.delenv("WORKER_APPLICATION", raising=False)
        monkeypatch.delenv("WORKER_RUNTIME_DECLARATIONS_HASH", raising=False)
        effects.configure(WorkerContext(llm=llm, registry=Registry()))
        try:
            if HAVE_TEMPORAL:
                from julep.execution import harness

                started: dict[str, object] = {}

                class Client:
                    async def start_workflow(self, workflow, flow_input, **kwargs):
                        started["input"] = flow_input
                        return "handle"

                handle = asyncio.run(
                    release.pipelines[0].start(
                        Client(),
                        session_id="released-prompt",
                        input=value,
                        options=WorkflowStartOptions(require_payload_encryption=False),
                    )
                )
                assert handle == "handle"

                async def execute_activity(fn, payload, **kwargs):
                    if fn.__name__ == "resolveQoS":
                        return await effects.resolveQoS(payload)
                    if fn.__name__ == "invokeReasoner":
                        return await effects.invokeReasoner(payload)
                    return None

                monkeypatch.setattr(
                    harness.workflow,
                    "execute_activity",
                    execute_activity,
                )
                result = asyncio.run(harness.FlowWorkflow().run(started["input"]))
            else:
                result = asyncio.run(
                    effects.invokeReasoner(
                        InvokeReasonerInput(
                            reasoner=rich.reasoner.name,
                            value=value,
                            cid="released-prompt",
                            runtime_declarations_ref=dict(declarations_ref),
                        )
                    )
                )
        finally:
            effects.configure(previous_context)

        assert result == "ok"
        assert captured == {"system": expected_system, "user": expected_user}
