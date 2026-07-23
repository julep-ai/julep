from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from julep.app_deploy import (
    ApplicationRelease,
    ApplicationReleaseError,
    HelmLaneReconciler,
    build_lane_deployment_config,
)
from julep.server.settings import ServerSettings

from .conftest import make_release


def _helm_release_and_settings(tmp_path: Path) -> tuple[ApplicationRelease, ServerSettings]:
    chart = tmp_path / "chart"
    chart.mkdir()
    (chart / "Chart.yaml").write_text("name: julep-worker\n", encoding="utf-8")
    worker_application = "pkg.mod:app"
    declarations_hash = "sha256:" + "a" * 64
    worker_environment = {"JULEP_EXECUTION_STORE_DSN_ALIAS": "primary"}
    worker_secret_environment = {
        "JULEP_EXTERNAL_API_TOKEN": {
            "secret_name": "external-api",
            "key": "token",
        }
    }
    deployment_config = build_lane_deployment_config(
        chart=str(chart),
        namespace="julep",
        temporal_address="temporal:7233",
        temporal_namespace="julep",
        worker_context_factory="pkg.mod:factory",
        worker_application=worker_application,
        worker_runtime_declarations_hash=declarations_hash,
        worker_service_account=None,
        worker_priority_class=None,
        payload_encryption_secret="temporal-payload-codec",
        worker_environment=worker_environment,
        worker_secret_environment=worker_secret_environment,
        lanes=("summary",),
        queue_by_lane={"summary": "summary"},
    )
    release = replace(make_release(), deployment_config=deployment_config)
    settings = ServerSettings(
        helm_chart=str(chart),
        kubernetes_namespace="julep",
        temporal_address="temporal:7233",
        temporal_namespace="julep",
        worker_context_factory="pkg.mod:factory",
        worker_application=worker_application,
        worker_runtime_declarations_hash=declarations_hash,
        worker_environment=worker_environment,
        worker_secret_environment=worker_secret_environment,
        payload_encryption_secret="temporal-payload-codec",
    )
    return release, settings


def test_build_reconciler_preserves_published_worker_configuration(tmp_path: Path) -> None:
    release, settings = _helm_release_and_settings(tmp_path)

    reconciler = settings.build_reconciler()

    assert isinstance(reconciler, HelmLaneReconciler)
    assert reconciler.worker_application == settings.worker_application
    assert (
        reconciler.worker_runtime_declarations_hash
        == settings.worker_runtime_declarations_hash
    )
    assert reconciler.worker_environment == settings.worker_environment
    assert reconciler.worker_secret_environment == settings.worker_secret_environment
    reconciler._validate_deployment_config(release, "summary", task_queue="summary")


def test_build_reconciler_rejects_worker_configuration_drift(tmp_path: Path) -> None:
    release, settings = _helm_release_and_settings(tmp_path)
    drifted = replace(
        settings,
        worker_environment={"JULEP_EXECUTION_STORE_DSN_ALIAS": "replica"},
    ).build_reconciler()

    assert isinstance(drifted, HelmLaneReconciler)
    with pytest.raises(ApplicationReleaseError, match="does not match"):
        drifted._validate_deployment_config(release, "summary", task_queue="summary")


def test_server_settings_parse_worker_configuration_from_files_and_env(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.julep.server]
worker_application = "pkg.config:app"
worker_runtime_declarations_hash = "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

[tool.julep.server.worker_environment]
JULEP_EXECUTION_STORE_DSN_ALIAS = "config-store"

[tool.julep.server.worker_secret_environment.JULEP_EXTERNAL_API_TOKEN]
secret_name = "config-secret"
key = "token"
""",
        encoding="utf-8",
    )
    base_env = {"TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED": "false"}

    configured = ServerSettings.from_env(base_env, root=tmp_path)

    assert configured.worker_application == "pkg.config:app"
    assert configured.worker_runtime_declarations_hash == "sha256:" + "a" * 64
    assert configured.worker_environment == {
        "JULEP_EXECUTION_STORE_DSN_ALIAS": "config-store"
    }
    assert configured.worker_secret_environment == {
        "JULEP_EXTERNAL_API_TOKEN": {
            "secret_name": "config-secret",
            "key": "token",
        }
    }

    overridden = ServerSettings.from_env(
        {
            **base_env,
            "JULEP_SERVER_WORKER_APPLICATION": "pkg.env:app",
            "JULEP_SERVER_WORKER_RUNTIME_DECLARATIONS_HASH": "sha256:" + "b" * 64,
            "JULEP_SERVER_WORKER_ENVIRONMENT": (
                '{"JULEP_EXECUTION_STORE_DSN_ALIAS":"env-store"}'
            ),
            "JULEP_SERVER_WORKER_SECRET_ENVIRONMENT": (
                '{"JULEP_EXTERNAL_API_TOKEN":'
                '{"secret_name":"env-secret","key":"credential"}}'
            ),
        },
        root=tmp_path,
    )

    assert overridden.worker_application == "pkg.env:app"
    assert overridden.worker_runtime_declarations_hash == "sha256:" + "b" * 64
    assert overridden.worker_environment == {
        "JULEP_EXECUTION_STORE_DSN_ALIAS": "env-store"
    }
    assert overridden.worker_secret_environment == {
        "JULEP_EXTERNAL_API_TOKEN": {
            "secret_name": "env-secret",
            "key": "credential",
        }
    }


@pytest.mark.parametrize(
    ("env_name", "value", "match"),
    [
        ("JULEP_SERVER_WORKER_ENVIRONMENT", "[]", "JSON object"),
        (
            "JULEP_SERVER_WORKER_ENVIRONMENT",
            '{"JULEP_EXECUTION_STORE_DSN_ALIAS": 1}',
            "non-empty strings",
        ),
        (
            "JULEP_SERVER_WORKER_SECRET_ENVIRONMENT",
            '{"JULEP_EXTERNAL_API_TOKEN":{"secret_name":"","key":"token"}}',
            "non-empty secret_name and key",
        ),
    ],
)
def test_server_settings_reject_invalid_worker_environment_json(
    tmp_path: Path,
    env_name: str,
    value: str,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        ServerSettings.from_env(
            {
                "TEMPORAL_PAYLOAD_ENCRYPTION_REQUIRED": "false",
                env_name: value,
            },
            root=tmp_path,
        )
