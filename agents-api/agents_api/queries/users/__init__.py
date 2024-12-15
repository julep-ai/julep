"""
The `user` module within the `queries` package provides SQL query functions for managing users
in the TimescaleDB database. This includes operations for:

- Creating new users
- Updating existing users
- Retrieving user details
- Listing users with filtering and pagination
- Deleting users
"""

from .create_or_update_user import create_or_update_user_query
from .create_user import create_user
from .delete_user import delete_user_query
from .get_user import get_user_query
from .list_users import list_users_query
from .patch_user import patch_user_query
from .update_user import update_user_query

__all__ = [
    "create_user",
    "create_or_update_user_query",
    "delete_user_query",
    "get_user_query",
    "list_users_query",
    "patch_user_query",
    "update_user_query",
]
