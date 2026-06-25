"""The package ``__version__`` is derived from the installed distribution.

Hardcoding the version in ``__init__.py`` lets it drift from the version declared
in ``pyproject.toml`` (and therefore from what ``pip`` reports). It must instead be
read from the installed distribution metadata so the two can never disagree.
"""

from importlib.metadata import version

import composable_agents


def test_module_version_matches_distribution_metadata() -> None:
    assert composable_agents.__version__ == version("composable-agents")
