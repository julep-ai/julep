"""
The `queries` module of the agents API is designed to encapsulate all data interactions with the PostgreSQL database. It provides a structured way to perform CRUD (Create, Read, Update, Delete) operations and other specific data manipulations across various entities such as agents, documents, entries, sessions, tools, and users.

Each sub-module within this module corresponds to a specific entity and contains functions and classes that implement SQL queries for interacting with the database. These interactions include creating new records, updating existing ones, retrieving data for specific conditions, and deleting records. The operations are crucial for the functionality of the agents API, enabling it to manage and process data effectively for each entity.

This module also integrates with the `common` module for exception handling and utility functions, ensuring robust error management and providing reusable components for data processing and query construction.
"""

# ruff: noqa: F401, F403, F405

from . import agents as agents
from . import developers as developers
from . import docs as docs
from . import entries as entries
from . import executions as executions
from . import files as files
from . import sessions as sessions
from . import tasks as tasks
from . import tools as tools
from . import users as users

