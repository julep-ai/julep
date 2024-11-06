"""
The routers module of the agents-api application is responsible for handling HTTP routing for different parts of the application. It orchestrates the request-response cycle by directing incoming HTTP requests to the appropriate handler functions based on the request's URL.

Sub-modules within the routers module:
- `agents`: Handles routing for agent-related operations, including CRUD (Create, Read, Update, Delete) actions and agent tool management. It provides endpoints for managing agents, their documentation, and tools.
- `sessions`: Manages routing for session-related operations. This includes creating, updating, and deleting sessions, as well as handling chat functionalities and history within sessions. It is essential for managing interactive sessions between agents and users.
- `users`: Responsible for routing user-related operations. This encompasses user creation, update, deletion, and managing user documents. It ensures that user data can be properly managed and accessed as needed.
- `jobs`: Deals with routing for job status inquiries. This allows users to check the status of asynchronous jobs, providing insights into the progress and outcomes of long-running operations.

Each sub-module defines its own set of API endpoints and is responsible for handling requests and responses related to its domain, ensuring a modular and organized approach to API development.
"""

# ruff: noqa: F401

# TODO: Create a router for developers
# SCRUM-21

from .agents import router as agents_router
from .docs import router as docs_router
from .internal import router as internal_router
from .jobs import router as jobs_router
from .sessions import router as sessions_router
from .tasks import router as tasks_router
from .users import router as users_router
