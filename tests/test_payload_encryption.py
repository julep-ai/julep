"""Payload-key validation must not import the optional Temporal runtime."""

from __future__ import annotations

import subprocess
import sys

import pytest

from julep import HAVE_TEMPORAL


@pytest.mark.skipif(not HAVE_TEMPORAL, reason="temporalio not installed")
def test_temporal_codec_reexports_neutral_keyring_contract() -> None:
    from julep._payload_encryption import (
        PayloadEncryptionError,
        parse_aes_gcm_keyring,
    )
    from julep.execution.codec import (
        PayloadEncryptionError as CodecPayloadEncryptionError,
    )
    from julep.execution.codec import (
        parse_aes_gcm_keyring as codec_parse_aes_gcm_keyring,
    )

    assert CodecPayloadEncryptionError is PayloadEncryptionError
    assert codec_parse_aes_gcm_keyring is parse_aes_gcm_keyring


def test_payload_key_consumers_work_without_temporalio() -> None:
    code = """
import builtins
import tempfile

real_import = builtins.__import__

def block_temporal(name, *args, **kwargs):
    if name.split('.')[0] == 'temporalio':
        raise ImportError('temporalio blocked by test')
    return real_import(name, *args, **kwargs)

builtins.__import__ = block_temporal

from julep._payload_encryption import parse_aes_gcm_keyring
from julep.secrets import VaultCipher, VaultConfigurationError
from julep.server.settings import ServerSettings

key = 'ab' * 32
assert parse_aes_gcm_keyring(f'payload={key}') == {'payload': key}

shared = {
    'JULEP_VAULT_KEYS': f'vault={key}',
    'JULEP_VAULT_KEY_ID': 'vault',
    'TEMPORAL_PAYLOAD_KEYS': f'payload={key}',
    'TEMPORAL_PAYLOAD_KEY_ID': 'payload',
}
try:
    VaultCipher.from_env(shared)
except VaultConfigurationError as exc:
    assert 'distinct key material' in str(exc)
else:
    raise AssertionError('vault accepted reused payload key material')

with tempfile.TemporaryDirectory() as root:
    try:
        ServerSettings.from_env(shared, root=root)
    except ValueError as exc:
        assert 'distinct key material' in str(exc)
    else:
        raise AssertionError('server settings accepted reused payload key material')
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
