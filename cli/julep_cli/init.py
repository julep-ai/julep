import io
import shutil
import zipfile
from pathlib import Path
from typing import Annotated

import requests
import typer

from .app import app


@app.command()
def init(
    template: Annotated[
        str,
        typer.Option(
            "--template",
            "-t",
            help="Template name to use",
        ),
    ] = "hello-world",
    output_dir: Annotated[
        Path,
        typer.Option(
            "--destination",
            "-o",
            help="Destination directory",
        ),
    ] = Path.cwd(),
):
    """Initialize a new Julep project"""
    repo_url = "https://github.com/julep-ai/library"
    branch = "main"
    template_url = f"{repo_url}/archive/refs/heads/{branch}.zip"

    try:
        # Download the repository as a zip file
        response = requests.get(template_url)
        response.raise_for_status()

        # Extract the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Construct the path to the template folder within the zip
            repo_prefix = f"library-{branch}/"
            template_folder = f"{repo_prefix}{template}/"

            # Extract only the specified template folder
            typer.echo(f"Extracting template '{template}' to {output_dir}")

            for file_info in z.infolist():
                if file_info.filename.startswith(template_folder):
                    # Remove the leading directory path
                    z.extract(file_info, output_dir)

                    library_repo_prefix = output_dir / f"library-{branch}"
                    # Move the inner template directory to the destination directory
                    extracted_template_path = library_repo_prefix / template
                    final_destination = output_dir / template

                    # Ensure the final destination directory exists
                    final_destination.mkdir(parents=True, exist_ok=True)

                    # Move files from the extracted template path to the final destination
                    for item in extracted_template_path.iterdir():
                        item.rename(final_destination / item.name)

                    # Remove the extracted template directory and its parent
                    shutil.rmtree(library_repo_prefix)

    except requests.exceptions.RequestException as e:
        typer.echo(f"Failed to download template: {e}", err=True)
        raise typer.Exit(1)
    except zipfile.BadZipFile as e:
        typer.echo(f"Failed to extract template: {e}", err=True)
        raise typer.Exit(1)

    julep_toml = output_dir / template / "julep.toml"
    if not julep_toml.exists():
        typer.echo("Error: 'julep.toml' not found in the destination directory", err=True)
        raise typer.Exit(1)

    typer.echo(f"Initialized new Julep project with template '{template}' in {output_dir}")
