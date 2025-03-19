"""Database queries for Secrets."""

__all__ = [
    "create_secret",
    "delete_secret",
    "get_secret",
    "get_secret_by_name",
    "list_secrets",
    "patch_secret",
    "update_secret",
]

from .create_secret import create_secret
from .delete_secret import delete_secret
from .get_secret import get_secret, get_secret_by_name
from .list_secrets import list_secrets
from .patch_secret import patch_secret
from .update_secret import update_secret
