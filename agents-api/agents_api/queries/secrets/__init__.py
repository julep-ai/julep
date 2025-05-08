"""Query functions for secrets."""

from .create import create_secret
from .delete import delete_secret
from .get_by_name import get_secret_by_name
from .list import list_secrets
from .update import update_secret

__all__ = [
    "create_secret",
    "delete_secret",
    "get_secret_by_name",
    "list_secrets",
    "update_secret",
]
