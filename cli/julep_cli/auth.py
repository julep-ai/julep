import os
from typing import Annotated

import typer

from cli.julep_cli.utils import get_config, save_config

from .app import app


@app.command()
def auth(
    api_key: Annotated[
        str | None,
        typer.Option(
            "--api-key",
            "-k",
            help="Your Julep API key",
            prompt="Please enter your Julep API key"
            if not os.getenv("JULEP_API_KEY")
            else False,
        ),
    ] = None,
):
    """Authenticate with the Julep platform"""
    api_key = api_key or os.getenv("JULEP_API_KEY")

    if not api_key:
        typer.echo("No API key provided", err=True)
        raise typer.Exit(1)

    config = get_config()
    config["api_key"] = api_key
    save_config(config)

    typer.echo("Successfully authenticated!")
