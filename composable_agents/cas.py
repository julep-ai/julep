"""Content-addressed stores for code-as-data artifact distribution.

CAS objects are immutable and are never deleted within workflow-history
retention; any future garbage collection must take leases against live artifact
hashes before removing anything. Replay depends on these bytes remaining
available, so this module intentionally exposes no delete API.
"""

from __future__ import annotations

import hashlib
import importlib
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class CASError(Exception):
    pass


class CASNotFound(CASError):
    pass


class CASIntegrityError(CASError):
    pass


class CASDigestError(CASError):
    pass


class CASStore(Protocol):
    def put(self, data: bytes) -> str: ...
    def get(self, digest: str) -> bytes: ...
    def has(self, digest: str) -> bool: ...


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_digest(digest: str) -> None:
    if _SHA256_HEX.fullmatch(digest) is None:
        raise CASDigestError(f"expected full lowercase sha256 hex digest, got {digest!r}")


class LocalDirCAS:
    """Write-once sha256-addressed CAS backed by a local directory."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, data: bytes) -> str:
        digest = _digest(data)
        path = self._path_for(digest)
        path.parent.mkdir(parents=True, exist_ok=True)

        if path.exists():
            stored = path.read_bytes()
            actual = _digest(stored)
            if actual != digest or stored != data:
                raise CASIntegrityError(f"CAS object failed integrity check: {digest}")
            return digest

        fd, tmp_name = tempfile.mkstemp(prefix=f".{digest}.", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(data)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_name, path)
        except BaseException:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass
            raise
        return digest

    def get(self, digest: str) -> bytes:
        path = self._path_for(digest)
        try:
            data = path.read_bytes()
        except FileNotFoundError as e:
            raise CASNotFound(f"CAS object not found: {digest}") from e

        actual = _digest(data)
        if actual != digest:
            raise CASIntegrityError(f"CAS object failed integrity check: {digest}")
        return data

    def has(self, digest: str) -> bool:
        return self._path_for(digest).exists()

    def _path_for(self, digest: str) -> Path:
        _validate_digest(digest)
        return self.root / digest[:2] / digest[2:4] / digest


def _make_default_client() -> Any:
    try:
        boto3 = importlib.import_module("boto3")
    except ModuleNotFoundError as e:
        raise RuntimeError(
            "S3 CAS requires boto3; install it with pip install 'composable-agents[store]'"
        ) from e
    return boto3.client("s3")


class S3CAS:
    """Write-once sha256-addressed CAS backed by S3."""

    def __init__(self, bucket: str, prefix: str = "", *, client: Any | None = None) -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.client = client if client is not None else _make_default_client()

    def put(self, data: bytes) -> str:
        digest = _digest(data)
        try:
            stored = self.get(digest)
        except CASNotFound:
            self.client.put_object(Bucket=self.bucket, Key=self._key_for(digest), Body=data)
            return digest

        if stored != data:
            raise CASIntegrityError(f"CAS object failed integrity check: {digest}")
        return digest

    def get(self, digest: str) -> bytes:
        key = self._key_for(digest)
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key)
        except Exception as e:
            if self._is_not_found(e):
                raise CASNotFound(f"CAS object not found: {digest}") from e
            raise

        body = obj["Body"]
        data = body.read() if hasattr(body, "read") else body
        if not isinstance(data, bytes):
            raise CASIntegrityError(f"CAS object body is not bytes: {digest}")

        actual = _digest(data)
        if actual != digest:
            raise CASIntegrityError(f"CAS object failed integrity check: {digest}")
        return data

    def has(self, digest: str) -> bool:
        key = self._key_for(digest)
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
        except Exception as e:
            if self._is_not_found(e):
                return False
            raise
        return True

    def _key_for(self, digest: str) -> str:
        _validate_digest(digest)
        if not self.prefix:
            return digest
        return f"{self.prefix}/{digest}"

    def _is_not_found(self, exc: Exception) -> bool:
        exceptions = getattr(self.client, "exceptions", None)
        no_such_key = getattr(exceptions, "NoSuchKey", None)
        if no_such_key is not None and isinstance(exc, no_such_key):
            return True

        response = getattr(exc, "response", None)
        if isinstance(response, dict):
            error = response.get("Error")
            if isinstance(error, dict):
                code = str(error.get("Code", ""))
                return code in {"404", "NoSuchKey", "NotFound"}
        return False


def cas_from_url(url: str) -> CASStore:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        return LocalDirCAS(Path(parsed.path))
    if parsed.scheme == "s3":
        prefix = parsed.path.lstrip("/")
        return S3CAS(parsed.netloc, prefix)
    raise ValueError(f"unsupported CAS URL {url!r}; supported schemes: file, s3")
