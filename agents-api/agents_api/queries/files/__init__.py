"""
The `files` module within the `queries` package provides SQL query functions for managing files
in the PostgreSQL database. This includes operations for:

- Creating new files
- Retrieving file details
- Listing files with filtering and pagination
- Deleting files and their associations
"""

from .create_file import create_file
from .delete_file import delete_file
from .get_file import get_file
from .list_files import list_files

__all__ = [
    "create_file",
    "delete_file", 
    "get_file",
    "list_files"
] 