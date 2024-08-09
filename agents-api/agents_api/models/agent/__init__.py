"""
The `agent` module within the `agents-api` package provides a comprehensive suite of functionalities for managing agents in the CozoDB database. This includes:

- Creating new agents and their associated tools.
- Updating existing agents and their settings.
- Retrieving details about specific agents or a list of agents.
- Deleting agents from the database.

Additionally, the module supports operations related to agent tools, including creating, updating, and patching tools associated with agents.

This module serves as the backbone for agent management within the CozoDB ecosystem, facilitating a wide range of operations necessary for the effective handling of agent data.
"""

# ruff: noqa: F401, F403, F405

from .create_agent import create_agent
from .create_or_update_agent import create_or_update_agent
from .delete_agent import delete_agent
from .get_agent import get_agent
from .list_agents import list_agents
from .patch_agent import patch_agent
from .update_agent import update_agent
