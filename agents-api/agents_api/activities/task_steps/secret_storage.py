"""Secret storage class for accessing secrets in expressions."""

from typing import Any
from uuid import UUID

from asyncpg import Connection

from ...queries.secrets import get_secret_by_name


class SecretStorage:
    """A class that provides access to secrets in expressions.
    
    This class is used in base_evaluate to provide access to secrets
    in expressions. When an attribute is accessed, it will look up
    the secret in the database and return its value.
    
    Example:
        secret = SecretStorage(conn, developer_id)
        api_key = secret.OPENAI_API_KEY  # Returns the value of the OPENAI_API_KEY secret
    """

    def __init__(self, conn: Connection, developer_id: UUID):
        """Initialize the secret storage.
        
        Args:
            conn: Database connection
            developer_id: ID of the developer who owns the secrets
        """
        self._conn = conn
        self._developer_id = developer_id

    def __getattr__(self, name: str) -> str:
        """Get a secret by name.
        
        Args:
            name: Name of the secret to get
            
        Returns:
            The secret value
            
        Raises:
            AttributeError: If the secret doesn't exist
        """
        try:
            return get_secret_by_name(self._conn, self._developer_id, name)
        except ValueError as e:
            raise AttributeError(f"Secret {name} not found") from e 