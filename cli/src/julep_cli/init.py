import io
import shutil
import zipfile
from pathlib import Path
from typing import Annotated

import requests
import typer
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from .app import app, console, error_console


@app.command()
def init(
    template: Annotated[
        str,
        typer.Option(
            "--template",
            "-t",
            help="Name of the template to use from the library repository",
        ),
    ] = "hello-world",
    path: Annotated[
        Path,
        typer.Option(
            "--path",
            "-p",
            help="Destination directory for the initialized project (default: current directory)",
        ),
    ] = Path.cwd(),
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip confirmation prompt",
        ),
    ] = False,
):
    """Initialize a new Julep project by copying a template from the library repository.

    This will:
    1. Copy the specified template folder from the /library repository
    2. Create a new project in the destination directory
    3. Ensure the destination contains a valid julep.yaml file
    """
    repo_url = "https://github.com/julep-ai/library"
    branch = "main"
    template_url = f"{repo_url}/archive/refs/heads/{branch}.zip"

    # If not using --yes flag, confirm before proceeding
    if not yes:
        proceed = typer.confirm(
            f"This will initialize a new Julep project with template '{template}' in '{path}'. Proceed?",
            default=True,
        )
        if not proceed:
            console.print(
                Text("Initialization cancelled.", style="bold red")
            )
            raise typer.Exit

    try:
        # Download the repository as a zip file
        console.print(Text("Downloading template...", style="bold cyan"))
        response = requests.get(template_url)
        response.raise_for_status()

        # Extract the zip file
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Construct the path to the template folder within the zip
            repo_prefix = f"library-{branch}/"
            template_folder = f"{repo_prefix}{template}/"

            # Extract only the specified template folder
            console.print(Text(f"Extracting template '{template}' to {path}", style="bold green"))

            for file_info in z.infolist():
                if file_info.filename.startswith(template_folder):
                    # Remove the leading directory path
                    z.extract(file_info, path)

                    library_repo_prefix = path / f"library-{branch}"
                    # Move the inner template directory to the destination directory
                    extracted_template_path = library_repo_prefix / template
                    final_destination = path / template

                    # Ensure the final destination directory exists
                    final_destination.mkdir(parents=True, exist_ok=True)

                    # Copy files from the extracted template path to the final destination
                    shutil.copytree(extracted_template_path,
                                    final_destination, dirs_exist_ok=True)

                    # Remove the extracted template directory and its parent
                    shutil.rmtree(library_repo_prefix)

    except requests.exceptions.RequestException as e:
        error_console.print(
            Text(f"Failed to download template: {e}", style="bold red"))
        raise typer.Exit(1)
    except zipfile.BadZipFile as e:
        error_console.print(
            Text(f"Failed to extract template: {e}", style="bold red"))
        raise typer.Exit(1)

    julep_yaml = path / template / "julep.yaml"
    if not julep_yaml.exists():
        error_console.print(Text(
            "Error: 'julep.yaml' not found in the destination directory", style="bold red"))
        raise typer.Exit(1)

    console.print(
        Text(
            f"Successfully initialized new Julep project with template '{template}' in {path}",
            style="bold green",
        )
    )

    # Try to open and display the README if it exists
    readme_path = path / template / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text()
        markdown = Markdown(readme_content)
        console.print(Panel(markdown, title=Text("Project README", style="bold blue")))
