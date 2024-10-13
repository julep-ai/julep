"""
The `models` module of the agents API is responsible for handling all data operations with the CozoDB database.
It implements CRUD operations across entities like agents, documents, entries, sessions, tools, and users, ensuring 
efficient data management for the API. 

This module also integrates with the `common` module for exception handling and utility functions to provide robust 
error management and reusable components.
"""

# Disable specific linting rules for better clarity in error handling
# ruff: noqa: F401, F403, F405

import agents_api.models.agent as agent
import agents_api.models.developer as developer
import agents_api.models.docs as docs
import agents_api.models.entry as entry
import agents_api.models.execution as execution
import agents_api.models.session as session
import agents_api.models.task as task
import agents_api.models.tools as tools
import agents_api.models.user as user

# Utility Imports
from ..common.utils import cozo

# Improved Error Handling with Contextual Information
class DatabaseError(Exception):
    """Custom exception for database errors with context information."""
    def __init__(self, message, context=None):
        self.context = context
        super().__init__(f"DatabaseError: {message} Context: {context}")


def handle_database_exception(func):
    """Decorator to handle database exceptions and provide detailed error messages."""
    @wraps(func)  # No need for setattr(__wrapped__)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise DatabaseError(str(e), context=f"Function: {func.__name__}, Args: {args}, Kwargs: {kwargs}") from e
    return wrapper


@handle_database_exception
def create_agent(data):
    # function logic
    pass

@handle_database_exception
def update_agent(agent_id, data):
    # function logic
    pass

@handle_database_exception
def delete_agent(agent_id):
    # function logic
    pass
