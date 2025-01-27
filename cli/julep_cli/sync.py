from pathlib import Path
from typing import Annotated

import typer

from .app import app


@app.command()
def sync(
    source: Annotated[
        Path,
        typer.Option(
            "--source",
            "-s",
            help="Source directory containing julep.yaml",
        ),
    ],
    overwrite: Annotated[
        str | None,
        typer.Option(
            "--overwrite",
            "-o",
            help="How to handle conflicts: 'local' or 'remote'",
        ),
    ] = None,
    watch: Annotated[
        bool,
        typer.Option(
            "--watch",
            "-w",
            help="Watch for changes and sync automatically",
        ),
    ] = False,
):
    """Synchronize local package with Julep platform"""
    if not (source / "julep.yaml").exists():
        typer.echo("Error: julep.yaml not found in source directory", err=True)
        raise typer.Exit(1)

    # TODO: Implement sync logic
