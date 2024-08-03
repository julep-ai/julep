"""
The `entry` module is responsible for managing entries related to agents' activities and interactions within the 'cozodb' database. It provides a comprehensive set of functionalities for adding, deleting, summarizing, and retrieving entries, as well as processing them to retrieve memory context based on embeddings.

Key functionalities include:
- Adding entries to the database.
- Deleting entries from the database based on session IDs.
- Summarizing entries and managing their relationships.
- Retrieving entries from the database, including top-level entries and entries based on session IDs.
- Processing entries to retrieve memory context based on embeddings.

The module utilizes pandas DataFrames for handling query results and integrates with the CozoClient for database operations, ensuring efficient and effective management of entries.
"""

# ruff: noqa: F401, F403, F405

from .create_entries import create_entries
from .delete_entries import delete_entries
from .get_history import get_history
from .list_entries import list_entries
