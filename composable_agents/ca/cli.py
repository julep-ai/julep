from __future__ import annotations

import json as _json
import subprocess as _subprocess
import sys as _sys
from pathlib import Path

import typer

from composable_agents.ca.config import load_config
from composable_agents.ca.doctor import overall_code, run_checks
from composable_agents.ca.langfuse_link import trace_url
from composable_agents.ca.lint import lint_agents
from composable_agents.ca.model import Module, build_module
from composable_agents.ca.resolve import resolve_agent
from composable_agents.ca.runcache import load_run, save_run
from composable_agents.ca.runner import run_agent_local
from composable_agents.ca.select import select
from composable_agents.ca.tracetree import render_tree
from composable_agents.projection import ProjectionEvent

app = typer.Typer(add_completion=True, no_args_is_help=True, help="Developer CLI for composable-agents modules.")

VERSION = "0.1.0"


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
def graph(selector: str = typer.Argument("", help="Selection expression (default: all).")) -> None:
    """Render the cross-agent dependency DAG as Graphviz DOT."""
    module = _module()
    chosen = {a.name for a in select(module, selector)}
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
) -> None:
    """Execute an agent locally and stream its terminal trace tree."""
    cfg = load_config(Path("."))
    rid = run_id or f"ca-{name}-local"
    resolved = resolve_agent(cfg, name)
    outcome = run_agent_local(resolved, _json.loads(input), run_id=rid)
    if outcome.error is not None:
        typer.echo(f"error: {outcome.error}", err=True)
        save_run(str(cfg.root), run_id=rid, agent=name, status="error", events=outcome.events)
        raise typer.Exit(1)
    typer.echo(render_tree(outcome.events))
    typer.echo(f"\noutput: {_json.dumps(outcome.value)}")
    save_run(str(cfg.root), run_id=rid, agent=name, status="done", events=outcome.events)


@app.command("lint")
def lint(
    selector: str = typer.Argument("", help="Selection expression (default: all)."),
    fail_severity: str = typer.Option("", "--fail-severity", help="error|warning|info (default: config)."),
) -> None:
    """Lint selected agents (structural validation + severity gating)."""
    cfg = load_config(Path("."))
    module = build_module(cfg)
    names = [a.name for a in select(module, selector)]
    floor = fail_severity or cfg.fail_severity
    findings, code = lint_agents(cfg, names, fail_severity=floor)
    for f in findings:
        typer.echo(f"{f.severity.upper():7} {f.agent}: {f.code} — {f.message}")
    if not findings:
        typer.echo("clean")
    raise typer.Exit(code)


@app.command("test")
def test_cmd(
    selector: str = typer.Argument("", help="Selection expression (default: all)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the pytest command without running."),
) -> None:
    """Run pytest for the selected agents (matches test names by agent name via -k)."""
    cfg = load_config(Path("."))
    module = build_module(cfg)
    names = [a.name for a in select(module, selector)]
    cmd = [_sys.executable, "-m", "pytest", "-q"]
    if names:
        cmd += ["-k", " or ".join(names)]
    if dry_run:
        typer.echo(" ".join(cmd))
        raise typer.Exit(0)
    raise typer.Exit(_subprocess.run(cmd, cwd=str(cfg.root)).returncode)


@app.command("trace")
def trace(run_id: str = typer.Argument(..., help="Run id from a prior `ca run` (or a deployed run).")) -> None:
    """Render a cached run's trace tree and print its Langfuse deep link."""
    cfg = load_config(Path("."))
    cached = load_run(str(cfg.root), run_id)
    if cached is not None:
        events = [ProjectionEvent.from_json(e) for e in cached["events"]]
        typer.echo(render_tree(events))
    url = trace_url(run_id)
    if url:
        typer.echo(f"\nlangfuse: {url}")
    elif cached is None:
        typer.echo(f"error: no cached run {run_id!r} and LANGFUSE_HOST unset", err=True)
        raise typer.Exit(2)


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
    try:
        result = app(args=argv, standalone_mode=False)
    except SystemExit as exc:  # argparse-style callers expect an int
        return int(exc.code or 0)
    except typer.Exit as exc:
        return int(exc.exit_code)
    return int(result) if isinstance(result, int) else 0
