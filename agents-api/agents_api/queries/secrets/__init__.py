"""Query functions for secrets."""

from .create import create_secret
from .delete import delete_secret
from .list import list_secrets
from .update import update_secret
from .get_by_name import get_secret_by_name

__all__ = [
    "create_secret",
    "delete_secret",
    "list_secrets",
    "update_secret",
    "get_secret_by_name",
]
