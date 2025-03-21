"""Database queries for Secrets."""

__all__ = [
    "PatchSecretInput",
    "Secret",
    "SecretInput",
    "UpdateSecretInput",
    "create_secret",
    "delete_secret",
    "get_secret",
    "get_secret_by_name",
    "list_secrets",
    "patch_secret",
    "update_secret",
]

from .create_secret import Secret, SecretInput, create_secret
from .delete_secret import delete_secret
from .get_secret import get_secret, get_secret_by_name
from .list_secrets import list_secrets
from .patch_secret import PatchSecretInput, patch_secret
from .update_secret import UpdateSecretInput, update_secret
