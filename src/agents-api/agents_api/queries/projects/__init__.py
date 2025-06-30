"""
The `project` module within the `queries` package provides a comprehensive suite of SQL query functions for managing projects in the PostgreSQL database. This includes:

- Creating new projects
- Updating existing projects
- Retrieving details about specific projects
- Listing projects with filtering and pagination
- Deleting projects from the database

Each function in this module constructs and returns SQL queries along with their parameters for database operations.
"""

from .create_project import create_project
from .list_projects import list_projects

__all__ = [
    "create_project",
    "list_projects",
]
