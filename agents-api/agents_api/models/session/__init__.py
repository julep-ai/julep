"""The session module is responsible for managing session data in the 'cozodb' database. It provides functionalities to create, retrieve, list, update, and delete session information. This module utilizes the `CozoClient` for database interactions, ensuring that sessions are uniquely identified and managed through UUIDs.

Key functionalities include:
- Creating new sessions with specific metadata.
- Retrieving session information based on developer and session IDs.
- Listing all sessions with optional filters for pagination and metadata.
- Updating session data, including situation, summary, and metadata.
- Deleting sessions and their associated data from the database.

This module plays a crucial role in the application by facilitating the management of session data, which is essential for tracking and analyzing user interactions and behaviors within the system."""

# ruff: noqa: F401, F403, F405

from .count_sessions import count_sessions
from .create_or_update_session import create_or_update_session
from .create_session import create_session
from .delete_session import delete_session
from .get_session import get_session
from .list_sessions import list_sessions
from .patch_session import patch_session
from .prepare_session_data import prepare_session_data
from .update_session import update_session
