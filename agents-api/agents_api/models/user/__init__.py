"""
This module is responsible for managing user data in the CozoDB database. It provides functionalities to create, retrieve, list, and update user information.

Functions:
- create_user_query: Creates a new user in the CozoDB database, accepting parameters such as user ID, developer ID, name, about, and optional metadata.
- get_user_query: Retrieves a user's information from the CozoDB database by their user ID and developer ID.
- list_users_query: Lists users associated with a specific developer, with support for pagination and metadata-based filtering.
- patch_user_query: Updates a user's information in the CozoDB database, allowing for changes to fields such as name, about, and metadata.
"""

# ruff: noqa: F401, F403, F405

from .create_or_update_user import create_or_update_user
from .create_user import create_user
from .get_user import get_user
from .list_users import list_users
from .patch_user import patch_user
from .update_user import update_user
