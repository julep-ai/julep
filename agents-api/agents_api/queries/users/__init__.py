"""
The `user` module within the `queries` package provides SQL query functions for managing users
in the TimescaleDB database. This includes operations for:

- Creating new users
- Updating existing users
- Retrieving user details
- Listing users with filtering and pagination
- Deleting users
"""

from .create_or_update_user import create_or_update_user
from .create_user import create_user
from .delete_user import delete_user
from .get_user import get_user
from .list_users import list_users
from .patch_user import patch_user
from .update_user import update_user

__all__ = [
    "create_user",
    "create_or_update_user",
    "delete_user",
    "get_user",
    "list_users",
    "patch_user",
    "update_user",
]
