from __future__ import annotations

import asyncio as _asyncio
import enum as _enum
import json as _json
import subprocess as _subprocess
import sys as _sys
from datetime import datetime, timezone
from pathlib import Path

import click
import typer

from julep.cli import schedule as _schedule
from julep.cli.application import (
    apply_configured_application,
    observe_application,
    plan_configured_application,
)
from julep.cli.config import JulepConfig, EnvConfig, load_config
from julep.cli.chat import chat_command
from julep.cli.deploy import deploy_agents
from julep.cli.doctor import legacy_checks, overall_code, run_checks
from julep.cli.langfuse_link import trace_url
from julep.cli.lint import lint_agents
from julep.cli.listen import listen_command
from julep.cli.model import Module, build_module
from julep.cli.runcache import load_run, save_run
from julep.cli.runner import RunOutcome, run_agent_local
from julep.cli.select import select
from julep.cli.status import status_exit_code, status_for_env
from julep.cli.temporal_run import run_on_env
from julep.cli.tracetree import render_tree
from julep.cli.trigger import trigger_command
from julep.bundle import BundleError
from julep.cas import CASError
from julep.projection import ProjectionEvent

app = typer.Typer(add_completion=True, no_args_is_help=True, help="Developer CLI for julep modules.")
schedule_app = typer.Typer(
    no_args_is_help=True,
    help="Manage Temporal cron schedules from julep.toml.",
)
app.add_typer(schedule_app, name="schedule")
app.command("chat")(chat_command)
app.command("listen")(listen_command)
app.command("trigger")(trigger_command)

_EVAL_TAG_OPTION = typer.Option(
    [], "--tag", help="Run only samples carrying this tag (repeatable; any-match)."
)
_EVAL_SAMPLE_NAME_OPTION = typer.Option(
    [],
    "--sample-name",
    help="Run only samples with this exact name (repeatable; unknown names exit 4).",
)


def _package_version() -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version("julep")
    except PackageNotFoundError:  # editable/source checkout without metadata
        return "unknown"


VERSION = _package_version()


class _FailSeverity(str, _enum.Enum):
    error = "error"
    warning = "warning"
    info = "info"


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Print julep version and exit."),
) -> None:
    if version:
        typer.echo(f"julep {VERSION}")
        raise typer.Exit(0)


def _module(root: str | None = None) -> Module:
    cfg = load_config(Path(root or "."))
    return build_module(cfg)


def _resolve_schedule_env(cfg: JulepConfig, env: str) -> EnvConfig:
    if env not in cfg.envs:
        typer.echo(f"error: unknown env {env!r}", err=True)
        raise typer.Exit(2)
    resolved = cfg.envs[env]
    if resolved.temporal_address is None:
        typer.echo(
            f"error: env {env!r} has no temporal_address; schedules require a Temporal env",
            err=True,
        )
        raise typer.Exit(2)
    return resolved


@schedule_app.command("apply")
def schedule_apply(env: str = typer.Option("local", "--env", help="Environment name.")) -> None:
    cfg = load_config(Path("."))
    resolved = _resolve_schedule_env(cfg, env)
    scheds = _schedule.schedules_for_env(cfg, env)
    if not scheds:
        typer.echo(f"no schedules configured for env {env!r}")
        raise typer.Exit(0)
    try:
        results = _schedule.apply_schedules(cfg, resolved, scheds)
    except ValueError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from None
    for name, action in results:
        typer.echo(f"{name}  {action}  {_schedule.schedule_id(env, name)}")


@schedule_app.command("ls")
def schedule_ls(env: str = typer.Option("local", "--env", help="Environment name.")) -> None:
    cfg = load_config(Path("."))
    resolved = _resolve_schedule_env(cfg, env)
    scheds = _schedule.schedules_for_env(cfg, env)
    server = _schedule.fetch_server_schedules(resolved)
    rows = _schedule.schedule_drift(env, scheds, server)
    for row in rows:
        detail = f"  {row.detail}" if row.detail else ""
        typer.echo(f"{row.name:24} {row.state:9} {row.schedule_id}{detail}")
    if any(row.state != "in-sync" for row in rows):
        raise typer.Exit(3)


@schedule_app.command("rm")
def schedule_rm(
    name: str = typer.Argument(..., help="Schedule name."),
    env: str = typer.Option("local", "--env", help="Environment name."),
) -> None:
    cfg = load_config(Path("."))
    resolved = _resolve_schedule_env(cfg, env)
    sid = _schedule.schedule_id(env, name)
    if _schedule.remove_schedule(resolved, name):
        typer.echo(f"removed {sid}")
    else:
        typer.echo(f"no schedule {sid}")


def _eval_env_vars(env: str) -> dict[str, str]:
    """Env vars for ``$env`` resolution during eval.

    A standalone ``.ctx`` outside any Julep project resolves to ``{}`` (the default
    ``--env local`` needs no project). Inside a project an unknown ``--env`` is a
    loud teaching error (G-8), matching every other command; a malformed
    julep.toml/pyproject surfaces as a config error rather than a silent ``{}``.
    """
    root = Path(".")
    if not ((root / "pyproject.toml").is_file() or (root / "julep.toml").is_file()):
        return {}
    try:
        cfg = load_config(root)
    except Exception as exc:  # noqa: BLE001 - malformed project config is loud, never silent
        typer.echo(f"error: could not load Julep project config: {exc}", err=True)
        raise typer.Exit(4) from None
    if env in cfg.envs:
        return dict(cfg.envs[env].vars)
    known = ", ".join(sorted(cfg.envs)) or "local"
    typer.echo(
        f"error: unknown env {env!r}; define it under [env.{env}] in julep.toml or "
        f"[tool.julep.env.{env}] in pyproject.toml (known: {known})",
        err=True,
    )
    raise typer.Exit(4)


@app.command("ls")
def ls(
    selector: str = typer.Argument("", help="Selection expression (default: all)."),
    exclude: str = typer.Option("", "--exclude", help="Exclude expression."),
) -> None:
    """List agents in the module."""
    module = _module()
    agents = select(module, selector, exclude=exclude)
    for a in agents:
        tags = f"  [{','.join(a.tags)}]" if a.tags else ""
        typer.echo(f"{a.name:24} {a.kind:6}{tags}")


@app.command("show")
def show(name: str = typer.Argument(..., help="Agent name.")) -> None:
    """Show one agent's kind, source location, tags, and cross-agent calls."""
    module = _module()
    try:
        a = module.by_name(name)
    except KeyError:
        typer.echo(f"error: agent {name!r} not found", err=True)
        raise typer.Exit(2) from None
    typer.echo(f"{a.name}  ({a.kind})")
    typer.echo(f"  source: {a.file}:{a.line}")
    typer.echo(f"  tags:   {', '.join(a.tags) or '(none)'}")
    typer.echo(f"  calls:  {', '.join(a.calls) or '(none)'}")


@app.command("graph")
def graph(
    selector: str = typer.Argument("", help="Selection expression (default: all)."),
    exclude: str = typer.Option("", "--exclude", help="Exclude expression."),
) -> None:
    """Render the cross-agent dependency DAG as Graphviz DOT."""
    module = _module()
    chosen = {a.name for a in select(module, selector, exclude=exclude)}
    lines = ["digraph agents {", "  rankdir=LR;"]
    for a in module.agents:
        if a.name in chosen:
            lines.append(f'  "{a.name}";')
    for a in module.agents:
        if a.name not in chosen:
            continue
        for callee in a.calls:  # a calls callee -> edge callee -> a
            if callee in chosen:
                lines.append(f'  "{callee}" -> "{a.name}";')
    lines.append("}")
    typer.echo("\n".join(lines))


@app.command(
    "artifact",
    add_help_option=False,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def artifact_command(ctx: typer.Context) -> None:
    """Validate, freeze, inspect, run, or graph a JSON artifact."""
    from julep.cli.artifact import main as artifact_main

    raise typer.Exit(artifact_main(ctx.args, prog="julep artifact"))


@app.command("run")
def run(
    name: str = typer.Argument(..., help="Agent name."),
    input: str = typer.Option("null", "--input", help="JSON-encoded input value."),
    run_id: str = typer.Option("", "--run-id", help="Run id (default: julep-<name>-local)."),
    env: str = typer.Option("local", "--env", help="Environment name."),
) -> None:
    """Execute an agent locally and stream its terminal trace tree."""
    cfg = load_config(Path("."))
    try:
        parsed = _json.loads(input)
    except _json.JSONDecodeError as exc:
        typer.echo(f"error: invalid --input JSON: {exc}", err=True)
        raise typer.Exit(2) from None
    if env not in cfg.envs:
        typer.echo(f"error: unknown env {env!r}", err=True)
        raise typer.Exit(2)
    if env != "local":
        # Pass through an explicit --run-id, but for a cloud env DO NOT fabricate
        # a fixed 'julep-<name>-local' id: that collides/dedups across runs and is
        # mislabelled 'local'. An empty id lets run_on_env mint a unique,
        # env-scoped session id.
        result = run_on_env(cfg, name, cfg.envs[env], parsed, run_id=run_id or None)
        if isinstance(result, RunOutcome):
            if result.error is not None:
                typer.echo(f"error: {result.error}", err=True)
                save_run(
                    str(cfg.root), run_id=result.run_id, agent=name, status="error", events=result.events
                )
                raise typer.Exit(1)
            typer.echo(render_tree(result.events))
            typer.echo(f"\noutput: {_json.dumps(result.value, default=str)}")
            save_run(
                str(cfg.root), run_id=result.run_id, agent=name, status="done", events=result.events
            )
            url = trace_url(result.run_id)
            if url:
                typer.echo(f"\nlangfuse: {url}")
            return
        typer.echo(f"output: {_json.dumps(result, default=str)}")
        return
    rid = run_id or f"julep-{name}-local"
    outcome = run_agent_local(cfg, name, parsed, run_id=rid, env_vars=cfg.envs[env].vars)
    if outcome.error is not None:
        typer.echo(f"error: {outcome.error}", err=True)
        save_run(str(cfg.root), run_id=rid, agent=name, status="error", events=outcome.events)
        raise typer.Exit(1)
    typer.echo(render_tree(outcome.events))
    typer.echo(f"\noutput: {_json.dumps(outcome.value)}")
    save_run(str(cfg.root), run_id=rid, agent=name, status="done", events=outcome.events)


@app.command("deploy")
def deploy(
    selector: str = typer.Argument("", help="Selection expression (default: all)."),
    exclude: str = typer.Option("", "--exclude", help="Exclude expression."),
    env: str = typer.Option("local", "--env", help="Environment name."),
) -> None:
    """Freeze, publish, and record selected agents for an environment."""
    cfg = load_config(Path("."))
    if env not in cfg.envs:
        typer.echo(f"error: unknown env {env!r}", err=True)
        raise typer.Exit(2)
    module = build_module(cfg)
    names = [a.name for a in select(module, selector, exclude=exclude)]
    if not names:
        typer.echo("no agents matched")
        raise typer.Exit(0)
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        records = deploy_agents(cfg, names, env, now_iso=now_iso)
    except RuntimeError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from None
    for record in records:
        typer.echo(f"{record.agent}  {record.artifact_hash[:19]}")


@app.command("plan")
def plan(
    env: str = typer.Option("local", "--env", help="Application environment name."),
    json_output: bool = typer.Option(False, "--json", help="Emit machine-readable JSON."),
    mcp_snapshot: bool = typer.Option(
        False,
        "--mcp-snapshot",
        help="Fetch configured MCP tools/list schemas before compiling.",
    ),
) -> None:
    """Compile an application and show artifact, schema, lane, and runtime drift."""
    cfg = load_config(Path("."))
    if env not in cfg.envs:
        typer.echo(f"error: unknown env {env!r}", err=True)
        raise typer.Exit(2)
    try:
        application_plan = plan_configured_application(
            cfg,
            cfg.envs[env],
            mcp_snapshot=mcp_snapshot,
        )
    except (BundleError, CASError, ImportError, RuntimeError, TypeError, ValueError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from None
    payload = application_plan.to_json()
    if json_output:
        typer.echo(_json.dumps(payload, indent=2, sort_keys=True))
    else:
        artifact = payload["artifact"]
        typer.echo(
            f"artifact  {'drift' if artifact['drift'] else 'clean':9} "
            f"{artifact['desired']}"
        )
        for name, drift in payload["mcpSchema"].items():
            typer.echo(f"mcp       {name:24} {'drift' if drift else 'clean'}")
        image = payload["workerImage"]
        typer.echo(
            f"image     {'drift' if image['drift'] else 'clean':9} "
            f"{image['desired'] or '-'}"
        )
        for lane, state in payload["release"].items():
            typer.echo(f"release   {lane:24} {state}")
        for lane, state in payload["deploymentConfig"].items():
            typer.echo(f"config    {lane:24} {state}")
        for lane, state in payload["helmKeda"].items():
            typer.echo(f"helm/keda {lane:24} {state}")
        for lane, state in payload["runtime"].items():
            typer.echo(f"runtime   {lane:24} {state}")


@app.command("apply")
def apply_application(
    env: str = typer.Option(..., "--env", help="Application environment name."),
    publish_only: bool = typer.Option(
        False,
        "--publish-only",
        help="Publish immutable artifacts without reconciling lane Helm releases.",
    ),
    mcp_snapshot: bool = typer.Option(
        False,
        "--mcp-snapshot",
        help="Fetch configured MCP tools/list schemas before publishing.",
    ),
) -> None:
    """Publish an immutable release and reconcile inactive lane workers."""
    cfg = load_config(Path("."))
    if env not in cfg.envs:
        typer.echo(f"error: unknown env {env!r}", err=True)
        raise typer.Exit(2)
    try:
        release, lanes = apply_configured_application(
            cfg,
            cfg.envs[env],
            publish_only=publish_only,
            mcp_snapshot=mcp_snapshot,
        )
    except (BundleError, CASError, ImportError, RuntimeError, TypeError, ValueError) as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(1) from None
    typer.echo(f"release   {release.release_hash}")
    typer.echo(f"artifact  {release.application_artifact_hash}")
    for lane in lanes:
        typer.echo(f"lane      {lane.lane:24} {lane.release_name}  {lane.task_queue}")
    if not lanes:
        typer.echo("lanes     not reconciled (--publish-only)")
    typer.echo("traffic   unchanged")


@app.command("status")
def status(
    selector: str = typer.Argument("", help="Selection expression (default: all)."),
    exclude: str = typer.Option("", "--exclude", help="Exclude expression."),
    env: str = typer.Option("local", "--env", help="Environment name."),
) -> None:
    """Show deployment status and drift for an environment."""
    cfg = load_config(Path("."))
    if env not in cfg.envs:
        typer.echo(f"error: unknown env {env!r}", err=True)
        raise typer.Exit(2)
    if cfg.application is not None and not selector.strip() and not exclude.strip():
        try:
            observed = observe_application(cfg, cfg.envs[env])
            application_plan = plan_configured_application(
                cfg,
                cfg.envs[env],
                observed=observed,
            )
        except (BundleError, CASError, RuntimeError, TypeError, ValueError) as exc:
            typer.echo(f"error: {exc}", err=True)
            raise typer.Exit(1) from None
        typer.echo(f"application {application_plan.application}")
        typer.echo(f"artifact    {application_plan.desired_artifact_hash}")
        typer.echo(f"release     {observed.release_hash or '-'}")
        for lane, state in sorted(observed.lanes.items()):
            typer.echo(
                f"{lane:24} helm={state.helm_ready!s:5} "
                f"k8s={state.worker_ready!s:5} keda={state.keda_ready!s:5} "
                f"backlog={state.temporal_backlog!s:5} running={state.temporal_running!s:5}"
            )
            if state.detail:
                typer.echo(f"  {state.detail}")
        drift = (
            application_plan.artifact_drift
            or application_plan.worker_image_drift
            or any(application_plan.mcp_schema_drift.values())
            or any(
                value != "clean"
                for value in application_plan.deployment_config_drift.values()
            )
            or any(value != "clean" for value in application_plan.release_drift.values())
            or any(value != "ready" for value in application_plan.helm_keda_drift.values())
            or any(value != "healthy" for value in application_plan.runtime_drift.values())
        )
        raise typer.Exit(3 if drift else 0)
    rows = status_for_env(cfg, env)
    if selector.strip() or exclude.strip():
        module = build_module(cfg)
        names = {a.name for a in select(module, selector, exclude=exclude)}
        rows = [row for row in rows if row.name in names]
    for row in rows:
        typer.echo(f"{row.name:24} {row.state:11} {row.deployed_hash or '-'}")
    raise typer.Exit(status_exit_code(rows))


@app.command("worker")
def worker(
    smoke_test_seconds: float = typer.Option(
        0.0,
        "--smoke-test-seconds",
        min=0.0,
        help=(
            "Positive: verify Temporal, poll for this many seconds, then drain "
            "and exit. Zero (default): run continuously."
        ),
    ),
) -> None:
    """Run a Temporal worker from the explicit environment contract."""

    from julep.execution.serve import (
        WorkerServeSettings,
        serve,
        smoke_test_worker,
    )

    settings = WorkerServeSettings.from_env()
    if smoke_test_seconds > 0:
        _asyncio.run(
            smoke_test_worker(settings, poll_seconds=smoke_test_seconds)
        )
    else:
        _asyncio.run(serve(settings))


@app.command("lint")
def lint(
    selector: str = typer.Argument("", help="Selection expression (default: all)."),
    exclude: str = typer.Option("", "--exclude", help="Exclude expression."),
    env: str = typer.Option("local", "--env", help="Environment name (queue-lane target)."),
    fail_severity: _FailSeverity | None = typer.Option(  # noqa: B008
        None, "--fail-severity", help="error|warning|info (default: config)."
    ),
) -> None:
    """Lint selected agents (structural validation + severity gating)."""
    cfg = load_config(Path("."))
    if env not in cfg.envs:
        typer.echo(f"error: unknown env {env!r}", err=True)
        raise typer.Exit(2)
    module = build_module(cfg)
    names = [a.name for a in select(module, selector, exclude=exclude)]
    floor = fail_severity.value if fail_severity is not None else cfg.fail_severity
    # --env defaults to local, preserving the deterministic default target.
    env_cfg = cfg.envs[env]
    findings, code = lint_agents(
        cfg,
        names,
        fail_severity=floor,
        env_vars=env_cfg.vars,
        queues=env_cfg.queues,
        queue_env=env,
    )
    for f in findings:
        typer.echo(f"{f.severity.upper():7} {f.agent}: {f.code} — {f.message}")
    if not findings:
        typer.echo("clean")
    raise typer.Exit(code)


@app.command("test")
def test_cmd(
    selector: str = typer.Argument("", help="Selection expression (default: all)."),
    exclude: str = typer.Option("", "--exclude", help="Exclude expression."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the pytest command without running."),
) -> None:
    """Run pytest for the selected agents.

    Agent names are passed to pytest via ``-k``, which uses substring matching:
    a test whose id merely *contains* a selected agent's name will also run, so
    the gate may cover slightly more tests than the exact selection.
    """
    cfg = load_config(Path("."))
    module = build_module(cfg)
    names = [a.name for a in select(module, selector, exclude=exclude)]
    cmd = [_sys.executable, "-m", "pytest", "-q"]
    if names:
        cmd += ["-k", " or ".join(names)]
    elif selector.strip():
        # An explicit selector that matched nothing must NOT fall through to a
        # full-suite run; report and exit cleanly.
        typer.echo("no agents matched")
        raise typer.Exit(0)
    if dry_run:
        typer.echo(" ".join(cmd))
        raise typer.Exit(0)
    raise typer.Exit(_subprocess.run(cmd, cwd=str(cfg.root)).returncode)


@app.command("eval")
def eval_cmd(
    ctx_path: str = typer.Argument(..., help="Path to a .ctx package with an eval.py."),
    env: str = typer.Option("local", "--env", help="Environment name (for $env resolution)."),
    limit: int = typer.Option(-1, "--limit", help="Max samples (-1 = all)."),
    tag: list[str] = _EVAL_TAG_OPTION,
    sample_name: list[str] = _EVAL_SAMPLE_NAME_OPTION,
    json_out: str = typer.Option("", "--json", help="Write the JSON report to this path."),
    baseline: str = typer.Option("", "--baseline", help="Baseline report JSON to diff against."),
) -> None:
    """Run a .ctx package's eval suite with a threshold + baseline regression gate.

    Exit codes: 0 pass, 2 below threshold, 3 regression vs --baseline, 4 broken
    eval config / unknown --env (setup error, never a model regression).
    """
    from julep.cli.evalrun import diff_reports, run_eval_sync

    env_vars = _eval_env_vars(env)
    try:
        report = run_eval_sync(
            ctx_path,
            env_vars=env_vars,
            limit=(None if limit < 0 else limit),
            tags=(tag or None),
            sample_names=(sample_name or None),
        )
    except ValueError as exc:
        # A broken/misconfigured eval (missing eval.py, non-.ctx dir, malformed
        # eval.yaml, or an error from user sample()/score() code) is a SETUP
        # failure, distinct from a model regression: exit 4, never 2 (reserved for
        # below-threshold) or 3 (baseline regression).
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(4) from None

    for s in report.scores:
        mark = "pass" if s.passed else "FAIL"
        typer.echo(f"  {s.id:32} {s.score:.3f} {mark}")
    verdict = "PASS" if report.passed else "BELOW THRESHOLD"
    typer.echo(
        f"{report.ctx}  model={report.model}  mean={report.mean:.3f}  "
        f"threshold={report.threshold:.3f}  {verdict}"
    )
    if json_out:
        Path(json_out).write_text(_json.dumps(report.to_json(), indent=2), encoding="utf-8")

    if baseline:
        base = _json.loads(Path(baseline).read_text(encoding="utf-8"))
        regressed, mean_regressed = diff_reports(base, report.to_json())
        if regressed or mean_regressed:
            typer.echo("regression vs baseline:", err=True)
            for sid in regressed:
                typer.echo(f"  REGRESSED {sid}", err=True)
            if mean_regressed:
                typer.echo(
                    f"  mean dropped {float(base.get('mean', 0.0)):.3f} -> {report.mean:.3f}",
                    err=True,
                )
            raise typer.Exit(3)

    if not report.passed:
        raise typer.Exit(2)


@app.command("trace")
def trace(
    run_id: str = typer.Argument(
        ..., help="Run id from a prior `julep run` (or a deployed run)."
    ),
) -> None:
    """Render a cached run's trace tree and print its Langfuse deep link."""
    cfg = load_config(Path("."))
    cached = load_run(str(cfg.root), run_id)
    if cached is None:
        # No local cache for this run id is a usage error, regardless of whether
        # trace_url() could fabricate a deep link from the (hashed) run id.
        typer.echo(f"error: no cached run {run_id!r}", err=True)
        raise typer.Exit(2)

    events = [ProjectionEvent.from_json(e) for e in cached["events"]]
    tree = render_tree(events)
    if tree:
        typer.echo(tree)
    else:
        # Failed/early-exit runs often have no captured events; surface the
        # cached status instead of echoing a blank line.
        typer.echo(f"run {run_id!r} status={cached['status']} (no trace events captured)")
    url = trace_url(run_id)
    if url:
        typer.echo(f"\nlangfuse: {url}")


@app.command("doctor")
def doctor() -> None:
    """Preflight: migration state, discovery, git, Langfuse, Temporal."""
    root = Path(".").resolve()
    preflight = legacy_checks(root)
    if any(check.name == "legacy-config" for check in preflight):
        checks = preflight
    else:
        checks = run_checks(load_config(root))
    for c in checks:
        mark = "ok " if c.ok else "WARN"
        typer.echo(f"[{mark}] {c.name}: {c.detail}")
    raise typer.Exit(overall_code(checks))


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code (does not call sys.exit).

    With ``standalone_mode=False`` click does not raise on ``typer.Exit``; it
    *returns* the exit code, so we propagate that return value.
    """
    # Recent Typer (>=0.13) vendors its own copy of Click under ``typer._click``,
    # so the usage/no-args errors it raises are NOT instances of the top-level
    # ``click`` package's exceptions. Catch both so a usage error is converted to
    # a clean exit code regardless of which Click the installed Typer uses.
    click_exceptions: tuple[type[BaseException], ...] = (click.exceptions.ClickException,)
    try:  # pragma: no cover - import shape depends on the installed Typer version
        from importlib import import_module

        typer_click_exception = vars(import_module("typer._click.exceptions"))["ClickException"]
        click_exceptions = (*click_exceptions, typer_click_exception)
    except Exception:  # noqa: BLE001 - older Typer reuses the real click package
        pass

    try:
        result = app(args=argv, standalone_mode=False)
    except SystemExit as exc:  # argparse-style callers expect an int
        return int(exc.code or 0)
    except typer.Exit as exc:
        return int(exc.exit_code)
    except click_exceptions as exc:
        # Unknown command / missing args / bad option: print the usage error and
        # return its conventional exit code (2) instead of leaking a traceback.
        # ``exc`` is a (real or Typer-vendored) ClickException; both expose
        # ``show()`` and ``exit_code`` even though they are distinct classes.
        exc.show()  # type: ignore[attr-defined]
        return int(exc.exit_code)  # type: ignore[attr-defined]
    return int(result) if isinstance(result, int) else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
