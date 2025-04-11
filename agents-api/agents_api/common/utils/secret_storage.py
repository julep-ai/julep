"""Secret storage class for accessing secrets in expressions."""

import asyncio
import logging
from uuid import UUID

import asyncpg

from ...autogen.openapi_model import GetSecretRequest
from ...queries.secrets.get import get_secret_query

logger: logging.Logger = logging.getLogger(__name__)


class SecretStorage:
    """A class that provides access to secrets in expressions.

    This class is used in base_evaluate to provide access to secrets
    in expressions. When an attribute is accessed, it will look up
    the secret in the database and return its value.

    Example:
        secret = SecretStorage(developer_id=developer_id)
        api_key = secret.OPENAI_API_KEY  # Returns the value of the OPENAI_API_KEY secret
    """

    def __init__(self, developer_id: UUID | None = None, agent_id: UUID | None = None):
        """Initialize the secret storage.

        Args:
            developer_id: ID of the developer who owns the secrets
            agent_id: ID of the agent associated with the secrets
        """
        self._developer_id = developer_id
        self._agent_id = agent_id

    def __getattribute__(self, name: str) -> str:
        """Get a secret by name.

        This method is called when an attribute is accessed on the SecretStorage instance.
        It queries the database for a secret with the given name.

        Args:
            name: Name of the secret to retrieve

        Returns:
            str: The secret value

        Raises:
            AttributeError: If the secret doesn't exist or cannot be retrieved
        """
        try:
            return asyncio.run(
                get_secret_query(
                    developer_id=self._developer_id,
                    agent_id=self._agent_id,
                    data=GetSecretRequest(name=name),
                ),
            )
        except asyncpg.PostgresError as e:
            logger.exception("Error retrieving secret: %s", e)
            msg = f"Secret '{name}' not found"
            raise AttributeError(msg) from e
