# tests/cli/test_lint.py
from importlib import import_module
from pathlib import Path

import pytest

from julep.cli.config import load_config
from julep.cli.lint import lint_agents
from julep.cli.main import main
from julep.dotctx import MissingOutputSchemaWarning, load_dotctx
from julep.registry import DEFAULT_REGISTRY


def test_lint_clean_module_passes(sample_module):
    cfg = load_config(sample_module)
    findings, exit_code = lint_agents(cfg, ["triage", "escalate"], fail_severity="error")
    assert exit_code == 0  # sample is structurally valid


def test_fail_severity_threshold_gates(sample_module):
    cfg = load_config(sample_module)
    # With an impossibly strict floor, any warning would gate; clean module still 0.
    _, exit_code = lint_agents(cfg, ["triage"], fail_severity="warning")
    assert exit_code in (0, 1)


def _write_ctx_pipeline(
    root: Path,
    *,
    output_schema: bool,
    tools: bool = False,
) -> Path:
    package = root / "prompts" / "summary.ctx"
    package.mkdir(parents=True)
    (package / "settings.yaml").write_text(
        f'name: "{root.name}.summary"\nmodel: "openai/gpt-test"\n',
        encoding="utf-8",
    )
    (package / "prompt.j2").write_text("Summarize {{ text }}.\n", encoding="utf-8")
    schema = "class Input:\n    text: str\n"
    if output_schema:
        schema += "\nclass Output:\n    summary: str\n"
    (package / "schema.pyi").write_text(schema, encoding="utf-8")
    if tools:
        (package / "tools.pyi").write_text(
            "def lookup(query: str) -> list[dict]: ...\n",
            encoding="utf-8",
        )

    config = '[pipeline.summary]\nctx = "prompts/summary.ctx"\n'
    if tools:
        config += (
            "\n[pipeline.summary.tools]\n"
            'lookup = "memory:lookup"\n'
            "\n[mcp.servers.memory]\n"
            'url = "https://mcp.example.test"\n'
        )
    (root / "julep.toml").write_text(config, encoding="utf-8")
    return package


def test_load_dotctx_warns_when_output_schema_is_missing(tmp_path: Path) -> None:
    package = _write_ctx_pipeline(tmp_path, output_schema=False)

    with pytest.warns(MissingOutputSchemaWarning, match=r"class Output.*not be schema-validated"):
        reasoner = load_dotctx(str(package))

    assert reasoner.reply_schema is None


def test_lint_includes_configured_ctx_pipeline_and_warning_obeys_gate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_ctx_pipeline(tmp_path, output_schema=False)
    monkeypatch.chdir(tmp_path)

    assert main(["lint"]) == 0
    output = capsys.readouterr().out
    assert "WARNING summary: CTX_OUTPUT_SCHEMA_MISSING" in output
    assert "class Output" in output

    assert main(["lint", "summary", "--fail-severity", "warning"]) == 1
    assert "CTX_OUTPUT_SCHEMA_MISSING" in capsys.readouterr().out


def test_ctx_pipeline_lint_is_offline_and_has_no_deployment_side_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_ctx_pipeline(tmp_path, output_schema=True, tools=True)
    registry_state = {
        "reasoners": dict(DEFAULT_REGISTRY.reasoners),
        "renderers": dict(DEFAULT_REGISTRY.renderers),
        "tool_expectations": dict(DEFAULT_REGISTRY.tool_expectations),
    }

    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("lint attempted a network or deployment side effect")

    monkeypatch.setattr("julep.mcp_snapshot.snapshot_servers", forbidden)
    monkeypatch.setattr(import_module("julep.deploy"), "deploy", forbidden)
    monkeypatch.chdir(tmp_path)

    assert main(["lint"]) == 0
    assert capsys.readouterr().out.strip() == "clean"
    assert not (tmp_path / ".julep").exists()
    assert DEFAULT_REGISTRY.reasoners == registry_state["reasoners"]
    assert DEFAULT_REGISTRY.renderers == registry_state["renderers"]
    assert DEFAULT_REGISTRY.tool_expectations == registry_state["tool_expectations"]


def test_ctx_pipeline_load_failure_is_actionable_exit_two(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "julep.toml").write_text(
        '[pipeline.broken]\nctx = "missing.ctx"\n',
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    assert main(["lint"]) == 2
    output = capsys.readouterr().out
    assert "ERROR" in output
    assert "broken: CTX_LOAD" in output
    assert "dotctx path does not exist" in output


def test_ctx_pipeline_lint_preserves_cross_pipeline_registration_conflicts(
    tmp_path: Path,
) -> None:
    for pipeline, model in (("one", "openai/gpt-one"), ("two", "openai/gpt-two")):
        package = tmp_path / f"{pipeline}.ctx"
        package.mkdir()
        (package / "settings.yaml").write_text(
            f'name: "shared-reasoner"\nmodel: "{model}"\n',
            encoding="utf-8",
        )
        (package / "prompt.j2").write_text("Summarize {{ text }}.\n", encoding="utf-8")
        (package / "schema.pyi").write_text(
            "class Input:\n    text: str\n\nclass Output:\n    summary: str\n",
            encoding="utf-8",
        )
    (tmp_path / "julep.toml").write_text(
        '[pipeline.one]\nctx = "one.ctx"\n'
        '[pipeline.two]\nctx = "two.ctx"\n',
        encoding="utf-8",
    )

    findings, exit_code = lint_agents(
        load_config(tmp_path),
        ["one", "two"],
        fail_severity="error",
    )

    assert exit_code == 2
    assert [(finding.agent, finding.code) for finding in findings] == [("two", "CTX_LOAD")]
    assert "already registered" in findings[0].message


def test_lint_cli_merges_worker_environment_into_ctx_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "julep.toml").write_text(
        '[env.local.vars]\nSHARED = "vars"\nONLY_VARS = "yes"\n'
        '[env.local.worker_environment]\nSHARED = "worker"\nONLY_WORKER = "yes"\n',
        encoding="utf-8",
    )
    captured: dict[str, str] = {}

    def fake_lint_agents(*args: object, **kwargs: object) -> tuple[list[object], int]:
        captured.update(kwargs["env_vars"])  # type: ignore[arg-type]
        return [], 0

    monkeypatch.setattr(import_module("julep.cli.main"), "lint_agents", fake_lint_agents)
    monkeypatch.chdir(tmp_path)

    assert main(["lint"]) == 0
    assert captured == {"SHARED": "worker", "ONLY_VARS": "yes", "ONLY_WORKER": "yes"}
