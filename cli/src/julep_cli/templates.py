import io
import os
import time
from multiprocessing.context import TimeoutError

from github import Auth, Github, GithubException
from joblib import Memory, Parallel, delayed
from rich.text import Text
from ruamel.yaml import YAML

from .utils import CONFIG_DIR, console

GH_ACCESS_TOKEN = os.getenv("GH_ACCESS_TOKEN")

cachedir = str(CONFIG_DIR / "templates.cache")
memory = Memory(cachedir, verbose=0)
yaml = YAML(typ="safe")
templates = []


@memory.cache
def fetch_library_templates():
    """
    Get the list of templates available in the library repository.
    """

    gh = Github(
        auth=Auth.Token(GH_ACCESS_TOKEN) if GH_ACCESS_TOKEN else None,
        lazy=True,
        timeout=3,
        retry=None,
    )

    repo = gh.get_repo("julep-ai/library")
    root_dirs = [d for d in repo.get_contents(".") if d.type == "dir"]

    def get_file_content(path: str) -> str:
        time.sleep(1)
        return repo.get_contents(path).decoded_content.decode("utf-8")

    with Parallel(n_jobs=-2, timeout=2.0, return_as="generator") as par:
        dir_contents = [*par(delayed(repo.get_contents)(d.path) for d in root_dirs)]
        has_julep_yaml = [
            any(x.path.endswith("julep.yaml") for x in dir) for dir in dir_contents
        ]
        template_names, paths = zip(*[
            (dir.name, dir.path)
            for dir, has_julep in zip(root_dirs, has_julep_yaml)
            if has_julep
        ])
        yamls = [*par(delayed(get_file_content)(path + "/julep.yaml") for path in paths)]
        configs = [yaml.load(io.StringIO(yaml_content)) for yaml_content in yamls]

    return [
        {
            "name": name,
            "path": path,
            "config": config,
        }
        for name, path, config in zip(template_names, paths, configs)
    ]


with console.status("Fetching library templates..."):
    try:
        templates = fetch_library_templates()

    except (GithubException, TimeoutError) as _e:
        console.print(Text("Failed to fetch library templates", style="italic yellow"))
