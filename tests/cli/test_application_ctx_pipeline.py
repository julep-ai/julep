from __future__ import annotations

import dataclasses
import hashlib
import shutil
from pathlib import Path

import pytest

pytest.importorskip("jinja2")

from julep.cli import application as application_module
from julep.cli.application import (
    apply_configured_application,
    release_queue_lines,
    resolve_application,
)
from julep.cli.config import load_config
from julep.app_deploy import release_from_bytes
from julep.declarations import load_declarations
from julep.execution.policy import ExecutionPolicy
from julep.registry import DEFAULT_REGISTRY, Registry

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _copy_summary_project(root: Path, *, application: str | None = None) -> None:
    package = root / "prompts" / "summary.ctx"
    package.parent.mkdir()
    shutil.copytree(FIXTURES / "summarizer.ctx", package)
    application_line = f'application = "{application}"\n' if application else ""
    (root / "pyproject.toml").write_text(
        "[tool.julep]\n"
        + application_line
        + "\n[tool.julep.pipeline.summary]\n"
        + 'ctx = "prompts/summary.ctx"\n'
        + 'lane = "summary"\n',
        encoding="utf-8",
    )


def test_zero_code_ctx_application_compiles_portable_declarations(tmp_path: Path) -> None:
    _copy_summary_project(tmp_path)
    cfg = load_config(tmp_path)
    application = resolve_application(cfg, cfg.envs["local"])
    assert application.name == tmp_path.name.lower().replace("_", "-")
    assert [pipeline.name for pipeline in application.pipelines] == ["summary"]

    saved_reasoners = dict(DEFAULT_REGISTRY.reasoners)
    saved_renderers = dict(DEFAULT_REGISTRY.renderers)
    saved_declarations = dict(DEFAULT_REGISTRY.renderer_declarations)
    try:
        compiled = application.compile()
        pipeline = compiled.pipelines[0]
        blob = pipeline.runtime_declarations_blob
        assert blob is not None
        fresh = Registry()
        load_declarations(
            blob,
            expected_hash="sha256:" + hashlib.sha256(blob).hexdigest(),
            registry=fresh,
        )
        assert application.pipelines[0].reasoner_names[0] in fresh.reasoners
        assert fresh.renderers
    finally:
        DEFAULT_REGISTRY.reasoners.clear()
        DEFAULT_REGISTRY.reasoners.update(saved_reasoners)
        DEFAULT_REGISTRY.renderers.clear()
        DEFAULT_REGISTRY.renderers.update(saved_renderers)
        DEFAULT_REGISTRY.renderer_declarations.clear()
        DEFAULT_REGISTRY.renderer_declarations.update(saved_declarations)


def test_zero_code_ctx_deployment_uses_release_scoped_declarations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_summary_project(tmp_path)
    cfg = load_config(tmp_path)
    env = dataclasses.replace(
        cfg.envs["local"],
        release_store=(tmp_path / "releases").as_uri(),
        temporal_address="temporal:7233",
        worker_context_factory="ctx_worker:build_context",
        payload_encryption_secret="temporal-payload-codec",
        helm_chart="oci://registry.example/julep/worker@sha256:" + "f" * 64,
    )
    monkeypatch.setenv("JULEP_BUNDLE_SIGNING_KEY", "0" * 64)
    compiled = application_module.compile_application(cfg, env)

    _chart, _worker_environment, deployment_config = (
        application_module._resolve_deployment_config(cfg, env, compiled)
    )

    assert cfg.application is None
    assert compiled.runtime_declarations_hash is not None
    assert deployment_config["workerApplication"] is None
    assert deployment_config["workerRuntimeDeclarationsHash"] is None


def test_zero_code_ctx_apply_reconciles_without_worker_spec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_summary_project(tmp_path)
    cfg = load_config(tmp_path)
    env = dataclasses.replace(
        cfg.envs["local"],
        release_store=(tmp_path / "releases").as_uri(),
        temporal_address="temporal:7233",
        worker_context_factory="ctx_worker:build_context",
        payload_encryption_secret="temporal-payload-codec",
        helm_chart="oci://registry.example/julep/worker@sha256:" + "f" * 64,
        worker_image="registry.example/julep@sha256:" + "e" * 64,
    )
    monkeypatch.setenv("JULEP_BUNDLE_SIGNING_KEY", "0" * 64)
    commands: list[list[str]] = []
    reconciler_type = application_module.HelmLaneReconciler

    def reconciler_with_capture(**kwargs):
        return reconciler_type(
            **kwargs,
            runner=lambda args: commands.append(list(args)),
        )

    monkeypatch.setattr(
        application_module,
        "HelmLaneReconciler",
        reconciler_with_capture,
    )

    release, results = application_module.apply_configured_application(cfg, env)

    assert release.deployment_config["workerApplication"] is None
    assert release.deployment_config["workerRuntimeDeclarationsHash"] is None
    assert release.pipelines[0].runtime_declarations_ref is not None
    assert len(results) == 1
    flattened = [argument for command in commands for argument in command]
    assert not any(value.startswith("worker.applicationSpec=") for value in flattened)
    assert not any(
        value.startswith("worker.runtimeDeclarationsHash=") for value in flattened
    )


def _publish_only_env(tmp_path: Path, cfg):
    """A minimal env with only a release store — no helm/k8s/worker-image."""
    return dataclasses.replace(
        cfg.envs["local"],
        release_store=(tmp_path / "releases").as_uri(),
    )


def test_publish_only_works_without_deploy_sections(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _copy_summary_project(tmp_path)
    cfg = load_config(tmp_path)
    env = _publish_only_env(tmp_path, cfg)
    monkeypatch.setenv("JULEP_BUNDLE_SIGNING_KEY", "0" * 64)

    release, results = apply_configured_application(cfg, env, publish_only=True)

    assert results == ()
    assert release.worker_image is None
    assert dict(release.deployment_config) == {"queues": {"summary": "summary"}}
    # The release round-trips byte-identically through the manifest codec.
    assert release_from_bytes(release.manifest_bytes).release_hash == release.release_hash
    assert release_from_bytes(release.manifest_bytes).worker_image is None
    # One release-scoped queue line per lane, even with no reconciliation.
    lines = release_queue_lines(release)
    assert [lane for lane, _queue in lines] == ["summary"]
    assert lines[0][1].startswith("summary-r")


def test_publish_only_carries_pipeline_policy_into_release(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _copy_summary_project(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.julep]\n"
        "\n[tool.julep.pipeline.summary]\n"
        'ctx = "prompts/summary.ctx"\n'
        'lane = "summary"\n'
        "\n[tool.julep.pipeline.summary.policy]\n"
        "reasoner_max_attempts = 1\n"
        "reasoner_timeout_s = 300\n",
        encoding="utf-8",
    )
    cfg = load_config(tmp_path)
    env = _publish_only_env(tmp_path, cfg)
    monkeypatch.setenv("JULEP_BUNDLE_SIGNING_KEY", "0" * 64)

    release, _ = apply_configured_application(cfg, env, publish_only=True)

    expected = ExecutionPolicy(reasoner_max_attempts=1, reasoner_timeout_s=300)
    assert release.pipelines[0].execution_policy == expected
    # The policy survives the release manifest round-trip (frozen into the release).
    round_tripped = release_from_bytes(release.manifest_bytes)
    assert round_tripped.pipelines[0].execution_policy == expected


def test_apply_without_publish_only_still_requires_worker_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _copy_summary_project(tmp_path)
    cfg = load_config(tmp_path)
    env = _publish_only_env(tmp_path, cfg)
    monkeypatch.setenv("JULEP_BUNDLE_SIGNING_KEY", "0" * 64)

    with pytest.raises(ValueError, match="worker_image"):
        apply_configured_application(cfg, env, publish_only=False)


def test_apply_without_publish_only_still_requires_temporal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _copy_summary_project(tmp_path)
    cfg = load_config(tmp_path)
    env = dataclasses.replace(
        cfg.envs["local"],
        release_store=(tmp_path / "releases").as_uri(),
        worker_image="registry.example/julep@sha256:" + "e" * 64,
    )
    monkeypatch.setenv("JULEP_BUNDLE_SIGNING_KEY", "0" * 64)

    with pytest.raises(ValueError, match="temporal_address"):
        apply_configured_application(cfg, env, publish_only=False)


def test_ctx_pipeline_collision_with_code_application_is_loud(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _copy_summary_project(tmp_path, application="code_app:application")
    (tmp_path / "code_app.py").write_text(
        """\
from julep.app import Application, PipelineSpec
from julep.dotctx import Reasoner
from julep.dsl import think

reasoner = Reasoner("code-reasoner", "openai/gpt-test", system="test")
application = Application(
    "code-app",
    (PipelineSpec("summary", think(reasoner.name), reasoners=(reasoner,)),),
)
""",
        encoding="utf-8",
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    cfg = load_config(tmp_path)
    with pytest.raises(ValueError, match="collide"):
        resolve_application(cfg, cfg.envs["local"])
