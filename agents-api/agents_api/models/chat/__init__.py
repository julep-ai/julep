"""
Module: agents_api/models/docs

This module is responsible for managing document-related operations within the application, particularly for agents and possibly other entities. It serves as a core component of the document management system, enabling features such as document creation, listing, deletion, and embedding of snippets for enhanced search and retrieval capabilities.

Main functionalities include:
- Creating new documents and associating them with agents or users.
- Listing documents based on various criteria, including ownership and metadata filters.
- Deleting documents by their unique identifiers.
- Embedding document snippets for retrieval purposes.

The module interacts with other parts of the application, such as the agents and users modules, to provide a comprehensive document management system. Its role is crucial in enabling document search, retrieval, and management features within the context of agents and users.

This documentation aims to provide clear, concise, and sufficient context for new developers or contributors to understand the module's role without needing to dive deep into the code immediately.
"""

# ruff: noqa: F401, F403, F405

from .gather_messages import gather_messages
from .get_cached_response import get_cached_response
from .prepare_chat_context import prepare_chat_context
from .set_cached_response import set_cached_response
