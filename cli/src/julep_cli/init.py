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
from rich.tree import Tree

from .app import app, console, error_console


@app.command()
def init(
    template: Annotated[
        str,
        typer.Option(
            "--template",
            "-t",
            help="Name of the template to use from the library repository (or 'empty' for an empty project)",
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
    """
    Initialize a new Julep project.

    This command downloads a predefined template from the library repository.
    The default template is "hello-world".

    Steps performed:
      1. Downloads and extracts the specified template folder.
      2. Validates that a 'julep.yaml' file exists.
      3. Displays a directory tree of the created project.
      4. Prints instructions to change directory into the project,
         and optionally opens a new shell there.
    """
    if not yes:
        proceed = typer.confirm(
            f"This will initialize a new Julep project in '{path}' with template '{template}'. Proceed?",
            default=True,
        )
        if not proceed:
            console.print(Text("Initialization cancelled.", style="bold red"), highlight=True)
            raise typer.Exit

    branch = "main"
    repo_url = "https://github.com/julep-ai/library"
    template_url = f"{repo_url}/archive/refs/heads/{branch}.zip"

    try:
        console.print(Text("Downloading template...", style="bold cyan"))
        response = requests.get(template_url)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            repo_prefix = f"library-{branch}/"
            template_folder = f"{repo_prefix}{template}/"

            found = any(info.filename.startswith(template_folder) for info in z.infolist())
            if not found:
                error_console.print(
                    Text(f"Template '{template}' not found in repository", style="bold red"),
                    highlight=True,
                )
                raise typer.Exit(1)

            for file_info in z.infolist():
                if file_info.filename.startswith(template_folder):
                    z.extract(file_info, path)

        library_repo_prefix = path / f"library-{branch}"
        extracted_template_path = library_repo_prefix / template
        final_destination = path / template

        # Warn the user if final_destination exists and is not empty (files will be merged)
        if final_destination.exists() and any(final_destination.iterdir()):
            if not yes:
                proceed_existing = typer.confirm(
                    f"Warning: The directory '{final_destination}' already exists and is not empty. Merging files may cause accidental data loss. Do you want to proceed?",
                    default=False,
                )
                if not proceed_existing:
                    console.print(
                        Text("Initialization cancelled.", style="bold red"),
                        highlight=True,
                    )
                    raise typer.Exit(1)
            else:
                console.print(
                    Text(
                        f"Warning: The directory '{final_destination}' already exists and is not empty. Files will be merged.",
                        style="bold yellow",
                    ),
                    highlight=True,
                )
        final_destination.mkdir(parents=True, exist_ok=True)

        shutil.copytree(extracted_template_path, final_destination, dirs_exist_ok=True)
        shutil.rmtree(library_repo_prefix)

    except requests.exceptions.RequestException as e:
        error_console.print(
            Text(f"Failed to download template: {e}", style="bold red"),
            highlight=True,
        )
        raise typer.Exit(1)
    except zipfile.BadZipFile as e:
        error_console.print(
            Text(f"Failed to extract template: {e}", style="bold red"),
            highlight=True,
        )
        raise typer.Exit(1)

    julep_yaml = final_destination / "julep.yaml"
    if not julep_yaml.exists():
        error_console.print(
            Text("Error: 'julep.yaml' not found in the project directory", style="bold red"),
            highlight=True,
        )
        raise typer.Exit(1)

    console.print(
        Text(
            f"Successfully initialized new Julep project with template '{template}' in {path}",
            style="bold green",
        ),
        highlight=True,
    )

    def print_directory_tree(directory: Path) -> None:
        tree = Tree(f":open_file_folder: [bold]{directory.name}")

        def add_tree(branch, path: Path):
            for item in sorted(path.iterdir(), key=lambda x: x.name):
                if item.is_dir():
                    subtree = branch.add(f":open_file_folder: [bold]{item.name}/")
                    add_tree(subtree, item)
                else:
                    branch.add(item.name)

        add_tree(tree, directory)
        console.print(tree)

    print_directory_tree(final_destination)

    cd_instruction = f"cd {final_destination.resolve()}"
    console.print(
        Text(f"To start working on your project, run: {cd_instruction}", style="bold green"),
        highlight=True,
    )

    # Python runs as a separate process, and any directory changes it makes only apply to that process.
    # Once the script exits, the original shell remains unchanged.
    # The only way to persist a directory change is by running cd directly in the shell.
    # if typer.confirm("Would you like to change to the project directory?", default=False):
    #     try:
    #         # Change current working directory to the final destination
    #         os.chdir(final_destination)
    #         console.print(
    #             Text(f"Changed working directory to {final_destination.resolve()}", style="bold green")
    #         )

    #         # Launch an interactive shell in the project directory.
    #         # This will spawn a child shell, and when you exit it, you'll return here.
    #         shell = os.environ.get("SHELL")
    #         if shell:
    #             subprocess.run([shell])
    #         else:
    #             subprocess.run("/bin/sh")
    #     except Exception as e:
    #         error_console.print(
    #             Text(f"Failed to change directory and launch shell: {e}", style="bold red")
    #         )

    # get the readme file
    readme_path = final_destination / "README.md"

    if readme_path.exists():
        readme_content = readme_path.read_text()
        markdown = Markdown(readme_content)
        console.print(
            Panel(markdown, title=Text("Project README", style="bold blue")), highlight=True
        )
