from __future__ import annotations

import typer

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


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns a process exit code (does not call sys.exit)."""
    try:
        app(args=argv, standalone_mode=False)
    except SystemExit as exc:  # argparse-style callers expect an int
        return int(exc.code or 0)
    except typer.Exit as exc:
        return int(exc.exit_code)
    return 0
