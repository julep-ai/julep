"""Query functions for secrets."""

from .create import create_secret
from .delete import delete_secret
from .list import list_secrets
from .update import update_secret

__all__ = [
    "create_secret",
    "delete_secret",
    "list_secrets",
    "update_secret",
]
