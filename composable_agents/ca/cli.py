from __future__ import annotations

import enum as _enum
import json as _json
import subprocess as _subprocess
import sys as _sys
from datetime import datetime, timezone
from pathlib import Path

import click
import typer

from composable_agents.ca.config import load_config
from composable_agents.ca.deploy import deploy_agents
from composable_agents.ca.doctor import overall_code, run_checks
from composable_agents.ca.langfuse_link import trace_url
from composable_agents.ca.lint import lint_agents
from composable_agents.ca.model import Module, build_module
from composable_agents.ca.resolve import resolve_agent
from composable_agents.ca.runcache import load_run, save_run
from composable_agents.ca.runner import RunOutcome, run_agent_local
from composable_agents.ca.select import select
from composable_agents.ca.status import status_exit_code, status_for_env
from composable_agents.ca.temporal_run import run_on_env
from composable_agents.ca.tracetree import render_tree
from composable_agents.projection import ProjectionEvent

app = typer.Typer(add_completion=True, no_args_is_help=True, help="Developer CLI for composable-agents modules.")

VERSION = "0.1.0"


class _FailSeverity(str, _enum.Enum):
    error = "error"
    warning = "warning"
    info = "info"


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Print ca version and exit."),
) -> None:
    if version:
        typer.echo(f"ca {VERSION}")
        raise typer.Exit(0)


def _module(root: str | None = None) -> Module:
    cfg = load_config(Path(root or "."))
    return build_module(cfg)


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


@app.command("run")
def run(
    name: str = typer.Argument(..., help="Agent name."),
    input: str = typer.Option("null", "--input", help="JSON-encoded input value."),
    run_id: str = typer.Option("", "--run-id", help="Run id (default: ca-<name>-local)."),
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
        # a fixed 'ca-<name>-local' id: that collides/dedups across runs and is
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
    rid = run_id or f"ca-{name}-local"
    resolved = resolve_agent(cfg, name)
    outcome = run_agent_local(resolved, parsed, run_id=rid)
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
    rows = status_for_env(cfg, env)
    if selector.strip() or exclude.strip():
        module = build_module(cfg)
        names = {a.name for a in select(module, selector, exclude=exclude)}
        rows = [row for row in rows if row.name in names]
    for row in rows:
        typer.echo(f"{row.name:24} {row.state:11} {row.deployed_hash or '-'}")
    raise typer.Exit(status_exit_code(rows))


@app.command("lint")
def lint(
    selector: str = typer.Argument("", help="Selection expression (default: all)."),
    exclude: str = typer.Option("", "--exclude", help="Exclude expression."),
    fail_severity: _FailSeverity | None = typer.Option(  # noqa: B008
        None, "--fail-severity", help="error|warning|info (default: config)."
    ),
) -> None:
    """Lint selected agents (structural validation + severity gating)."""
    cfg = load_config(Path("."))
    module = build_module(cfg)
    names = [a.name for a in select(module, selector, exclude=exclude)]
    floor = fail_severity.value if fail_severity is not None else cfg.fail_severity
    findings, code = lint_agents(cfg, names, fail_severity=floor)
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


@app.command("trace")
def trace(run_id: str = typer.Argument(..., help="Run id from a prior `ca run` (or a deployed run).")) -> None:
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
    """Preflight: discovery, git, Langfuse, Temporal."""
    cfg = load_config(Path("."))
    checks = run_checks(cfg)
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
        from typer._click.exceptions import ClickException as _TyperClickException

        click_exceptions = (*click_exceptions, _TyperClickException)
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
