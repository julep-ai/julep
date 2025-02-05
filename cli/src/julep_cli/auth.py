from enum import StrEnum
from typing import Annotated

import jwt
from typer import Exit, Option

from .app import app, console, error_console
from .utils import get_config, save_config

current_config = get_config()
current_environment = current_config.get("environment") or "production"
subdomain = "dev" if current_environment == "dev" else "api"
api_endpoint = f"https://{subdomain}.julep.ai"
dashboard_url = f"https://dashboard{'-dev' if current_environment == 'dev' else ''}.julep.ai"


class Environment(StrEnum):
    production = "production"
    dev = "dev"


def is_valid_jwt(token: str) -> bool:
    """Check if a string is a valid JWT format."""
    try:
        # Decode without verifying signature
        jwt.decode(token, options={"verify_signature": False})

        return True
    except (ValueError, jwt.DecodeError):
        return False


@app.command()
def auth(
    api_key: Annotated[
        str,
        Option(
            "--api-key",
            "-k",
            help=f"See {dashboard_url}",
            envvar="JULEP_API_KEY",
        ),
        {"validate": lambda x: x is not None and is_valid_jwt(x)},
    ],
    environment: Annotated[
        Environment,
        Option(
            "--environment",
            "-e",
            help="Environment",
            envvar="JULEP_ENVIRONMENT",
        ),
        {"default": current_environment},  # Used inside the questionary prompt
    ],
):
    """
    Authenticate with the Julep platform.

    Saves your API key to ~/.config/julep/config.yml for use with other commands.
    The API key can be found in your Julep account settings.
    """

    if not api_key:
        error_console.print("[red]No API key provided[/red]", highlight=True)
        raise Exit(1)

    config = get_config()
    config["api_key"] = api_key
    config["environment"] = str(environment)
    save_config(config)

    console.print(
        f"Successfully authenticated with [green]{environment}[/green] environment!",
        highlight=True,
    )
