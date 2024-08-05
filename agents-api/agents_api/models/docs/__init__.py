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

from .create_doc import create_doc
from .delete_doc import delete_doc
from .embed_snippets import embed_snippets
from .get_doc import get_doc
from .list_docs import list_docs
from .search_docs_by_embedding import search_docs_by_embedding
from .search_docs_by_text import search_docs_by_text
