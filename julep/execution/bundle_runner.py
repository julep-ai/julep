"""WorkflowRunner wrapper that resolves artifact-store bundle refs before workflow code.

Bundle-sourced pures are read synchronously from the process registry while the
workflow interpreter runs. On replay, activity bodies are not re-executed, so the
registry must be populated in the worker thread before sandboxed workflow code
starts.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from temporalio.bridge.proto.workflow_activation import WorkflowActivation
from temporalio.bridge.proto.workflow_completion import WorkflowActivationCompletion
from temporalio.worker import WorkflowInstance, WorkflowRunner
from temporalio.worker._workflow_instance import WorkflowInstanceDetails

from ..artifact_store import ArtifactStore
from ..registry import DEFAULT_REGISTRY, Registry
from ..worker_store import bundle_ref_entries, resolve_entries
from .harness import FlowInput


def _flow_bundle_entries(value: Any) -> list[tuple[str, str]]:
    if isinstance(value, FlowInput):
        return bundle_ref_entries(value.bundle)
    if isinstance(value, dict):
        return bundle_ref_entries(value.get("bundle"))
    return bundle_ref_entries(getattr(value, "bundle", None))


class BundleResolvingWorkflowRunner(WorkflowRunner):
    """Resolve ``FlowInput.bundle`` refs before the sandboxed workflow runs."""

    def __init__(
        self,
        *,
        inner: WorkflowRunner,
        store: ArtifactStore | None,
        registry: Registry = DEFAULT_REGISTRY,
    ) -> None:
        self.inner = inner
        self.store = store
        self.registry = registry

    def prepare_workflow(self, defn: Any) -> None:
        self.inner.prepare_workflow(defn)

    def set_worker_level_failure_exception_types(
        self,
        types: Sequence[type[BaseException]],
    ) -> None:
        self.inner.set_worker_level_failure_exception_types(types)

    def create_instance(self, det: WorkflowInstanceDetails) -> WorkflowInstance:
        return _BundleResolvingInstance(
            self.inner.create_instance(det),
            det=det,
            store=self.store,
            registry=self.registry,
        )


class _BundleResolvingInstance(WorkflowInstance):
    def __init__(
        self,
        inner: WorkflowInstance,
        *,
        det: WorkflowInstanceDetails,
        store: ArtifactStore | None,
        registry: Registry,
    ) -> None:
        self.inner = inner
        self.store = store
        self.registry = registry
        self._payload_converter = det.payload_converter_class()

    def activate(self, act: WorkflowActivation) -> WorkflowActivationCompletion:
        self._resolve_activation_bundles(act)
        return self.inner.activate(act)

    def _resolve_activation_bundles(self, act: WorkflowActivation) -> None:
        if self.store is None:
            return
        for job in act.jobs:
            if not job.HasField("initialize_workflow"):
                continue
            init = job.initialize_workflow
            if init.workflow_type != "FlowWorkflow" or not init.arguments:
                continue
            try:
                values = self._payload_converter.from_payloads(
                    [init.arguments[0]],
                    [FlowInput],
                )
            except Exception:
                continue
            if not values:
                continue
            entries = _flow_bundle_entries(values[0])
            if entries:
                resolve_entries(self.store, entries, registry=self.registry)

    def get_serialization_context(self, command_info: Any) -> Any:
        return self.inner.get_serialization_context(command_info)

    def get_external_store_context(self, command_info: Any) -> Any:
        return self.inner.get_external_store_context(command_info)

    def get_info(self) -> Any:
        return self.inner.get_info()

    def get_thread_id(self) -> int | None:
        return self.inner.get_thread_id()
