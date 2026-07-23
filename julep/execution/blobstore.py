"""Pure blob-durability contract for Temporal-backed agent execution.

Blob stores are content-addressed, immutable, integrity-checked on read, and
tenant-scoped. Production stores must also retain blobs for at least the
durable execution-record retention horizon, so garbage collection never removes
a blob reachable from a retained Temporal history or DBOS workflow. They must
encrypt blobs at rest when payloads are sensitive.

``InMemoryBlobStore`` is only the reference implementation for tests and local
use: it has no retention or garbage-collection policy, and it does not encrypt
payloads. This module intentionally imports no ``temporalio`` symbols, keeping
the contract importable and unit-testable without Temporal installed.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import stat
import tempfile
import threading
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote, urlparse

HASH_ALGO = "sha256"
_SHA256_HEX_LENGTH = 64


def _normalized_absolute_path(path: str | Path) -> Path:
    """Normalize ``.``/``..`` without touching the filesystem."""
    return Path(os.path.abspath(os.path.normpath(os.fspath(path))))


def _is_filesystem_root(path: Path) -> bool:
    return path == Path(path.anchor)


def _fsync_directory(path: Path) -> None:
    """Make directory-entry changes durable before a blob ref is returned."""
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


class BlobError(Exception):
    pass


class BlobNotFound(BlobError):
    pass


class BlobIntegrityError(BlobError):
    pass


class BlobImmutabilityError(BlobError):
    pass


class BlobTenantError(BlobError):
    pass


def content_ref(tenant: str, data: bytes) -> str:
    """Return the tenant-scoped sha256 content address for ``data``."""
    if not tenant or "/" in tenant:
        raise BlobTenantError(f"invalid blob tenant: {tenant!r}")

    digest = hashlib.sha256(data).hexdigest()
    return f"{tenant}/{HASH_ALGO}:{digest}"


def parse_ref(ref: str) -> tuple[str, str]:
    """Return ``(tenant, "sha256:<hex>")`` for a valid blob ref."""
    tenant, separator, rest = ref.partition("/")
    if not separator or not tenant:
        raise BlobTenantError(f"malformed blob ref: {ref!r}")

    algo, colon, digest = rest.partition(":")
    if colon != ":" or algo != HASH_ALGO:
        raise BlobTenantError(f"malformed blob ref: {ref!r}")

    if len(digest) != _SHA256_HEX_LENGTH or not digest:
        raise BlobTenantError(f"malformed blob ref: {ref!r}")

    if any(char not in "0123456789abcdef" for char in digest):
        raise BlobTenantError(f"malformed blob ref: {ref!r}")

    return tenant, f"{HASH_ALGO}:{digest}"


class BlobStore(Protocol):
    async def put(self, tenant: str, data: bytes) -> str: ...
    async def get(self, tenant: str, ref: str) -> bytes: ...


class InMemoryBlobStore:
    """Reference BlobStore backed by a ``dict`` from ref to bytes."""

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    async def put(self, tenant: str, data: bytes) -> str:
        ref = content_ref(tenant, data)
        if ref in self._blobs:
            if self._blobs[ref] == data:
                return ref
            raise BlobImmutabilityError(f"blob already exists with different bytes: {ref}")

        self._blobs[ref] = data
        return ref

    async def get(self, tenant: str, ref: str) -> bytes:
        ref_tenant, _ = parse_ref(ref)
        if ref_tenant != tenant:
            raise BlobTenantError(f"blob ref tenant {ref_tenant!r} does not match {tenant!r}")

        if ref not in self._blobs:
            raise BlobNotFound(f"blob not found: {ref}")

        stored = self._blobs[ref]
        if content_ref(tenant, stored) != ref:
            raise BlobIntegrityError(f"blob failed integrity check: {ref}")

        return stored


class LocalDirBlobStore:
    """Write-once blob store backed by a local or shared filesystem.

    Tenant names are hashed before they become path components. This preserves
    tenant isolation even for valid ref tenants such as ``..`` and prevents two
    tenants with identical content from resolving each other's physical object.
    Blocking filesystem operations, including initialization, run in a worker
    thread so activity event loops remain responsive. The configured root is an
    operator-trusted namespace; generated descendants reject observed symlinks,
    are private directories, and contain write-once ``0600`` files. This is not
    a sandbox against another same-identity process mutating paths concurrently.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = _normalized_absolute_path(root)
        if _is_filesystem_root(self.root):
            raise ValueError("blob-store path cannot use the filesystem root")
        self._initialize_lock = threading.Lock()
        self._directory_sync_lock = threading.Lock()
        self._synced_directory_entries: set[Path] = set()
        self._initialized = False

    async def initialize(self) -> None:
        """Create and validate the namespace without blocking the event loop."""
        await asyncio.to_thread(self._initialize)

    async def put(self, tenant: str, data: bytes) -> str:
        ref = content_ref(tenant, data)
        await self.initialize()
        await asyncio.to_thread(self._put, tenant, ref, data)
        return ref

    async def get(self, tenant: str, ref: str) -> bytes:
        ref_tenant, _digest = parse_ref(ref)
        if ref_tenant != tenant:
            raise BlobTenantError(
                f"blob ref tenant {ref_tenant!r} does not match {tenant!r}"
            )
        await self.initialize()
        return await asyncio.to_thread(self._get, tenant, ref)

    def _initialize(self) -> None:
        if self._initialized:
            return
        with self._initialize_lock:
            if self._initialized:
                return

            # Resolve existing symlinks in the operator-selected root exactly
            # once. Generated namespace components are rejected if symlinked.
            root = self.root.resolve(strict=False)
            if _is_filesystem_root(root):
                raise ValueError("blob-store path cannot use the filesystem root")
            self._create_root_chain(root)
            root = root.resolve(strict=True)
            if _is_filesystem_root(root):
                raise ValueError("blob-store path cannot use the filesystem root")

            self.root = root
            self._validate_root()
            self._ensure_directory_chain(root / "tenants")
            self._initialized = True

    def _create_root_chain(self, root: Path) -> None:
        """Create/validate the root chain and durably sync every entry."""
        anchor = Path(root.anchor)
        current = anchor
        for component in root.relative_to(anchor).parts:
            candidate = current / component
            created = False
            try:
                candidate_stat = os.lstat(candidate)
            except FileNotFoundError:
                try:
                    os.mkdir(candidate, 0o700)
                    created = True
                except FileExistsError:
                    candidate_stat = os.lstat(candidate)
                else:
                    candidate_stat = os.lstat(candidate)
            if not stat.S_ISDIR(candidate_stat.st_mode):
                raise BlobIntegrityError(
                    "blob-store root component is a symlink or not a directory: "
                    f"{candidate}"
                )
            if created and candidate_stat.st_mode & 0o077:
                raise BlobIntegrityError(
                    f"blob-store root component is not private: {candidate}"
                )
            self._sync_directory_entry(candidate)
            current = candidate

    def _sync_directory_entry(self, directory: Path) -> None:
        """Sync an entry once per instance, retrying any failed sync."""
        with self._directory_sync_lock:
            if directory in self._synced_directory_entries:
                return
            _fsync_directory(directory.parent)
            self._synced_directory_entries.add(directory)

    def _put(self, tenant: str, ref: str, data: bytes) -> None:
        path = self._path_for(tenant, ref)
        self._ensure_directory_chain(path.parent)
        try:
            stored = self._read_path(path, ref)
        except BlobNotFound:
            pass
        else:
            if stored == data and content_ref(tenant, stored) == ref:
                # A prior attempt may have published the hard link and then
                # failed its directory sync. Retrying must finish that commit.
                _fsync_directory(path.parent)
                return
            raise BlobImmutabilityError(
                f"blob already exists with different bytes: {ref}"
            )

        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                os.fchmod(handle.fileno(), 0o600)
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            try:
                # A hard link publishes the fully written object atomically and
                # fails instead of replacing an object won by a concurrent put.
                os.link(temporary, path)
            except FileExistsError:
                stored = self._read_path(path, ref)
                if stored != data or content_ref(tenant, stored) != ref:
                    raise BlobImmutabilityError(
                        f"blob already exists with different bytes: {ref}"
                    ) from None
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
        # Persist the final hard link and temporary-name removal before the ref
        # can enter durable workflow history.
        _fsync_directory(path.parent)

    def _get(self, tenant: str, ref: str) -> bytes:
        path = self._path_for(tenant, ref)
        stored = self._read_path(path, ref)
        if content_ref(tenant, stored) != ref:
            raise BlobIntegrityError(f"blob failed integrity check: {ref}")
        return stored

    def _ensure_directory_chain(self, directory: Path) -> None:
        """Create private descendants and reject pre-existing symlinks."""
        self._validate_root()
        try:
            relative = directory.relative_to(self.root)
        except ValueError as exc:
            raise BlobIntegrityError(
                f"blob directory escapes configured root: {directory}"
            ) from exc

        current = self.root
        for component in relative.parts:
            candidate = current / component
            try:
                os.mkdir(candidate, 0o700)
            except FileExistsError:
                candidate_stat = os.lstat(candidate)
                if not stat.S_ISDIR(candidate_stat.st_mode):
                    raise BlobIntegrityError(
                        f"blob namespace component is a symlink or not a directory: "
                        f"{candidate}"
                    ) from None
                if candidate_stat.st_mode & 0o077:
                    raise BlobIntegrityError(
                        f"blob namespace component is not a private directory: "
                        f"{candidate}"
                    ) from None
            self._sync_directory_entry(candidate)
            current = candidate

    def _validate_directory_chain(self, directory: Path) -> None:
        self._validate_root()
        try:
            relative = directory.relative_to(self.root)
        except ValueError as exc:
            raise BlobIntegrityError(
                f"blob directory escapes configured root: {directory}"
            ) from exc

        current = self.root
        for component in relative.parts:
            current /= component
            current_stat = os.lstat(current)
            if not stat.S_ISDIR(current_stat.st_mode):
                raise BlobIntegrityError(
                    f"blob namespace component is a symlink or not a directory: "
                    f"{current}"
                )
            if current_stat.st_mode & 0o077:
                raise BlobIntegrityError(
                    f"blob namespace component is not a private directory: {current}"
                )

    def _validate_root(self) -> None:
        root_stat = os.lstat(self.root)
        if not stat.S_ISDIR(root_stat.st_mode):
            raise BlobIntegrityError(
                f"blob-store root is a symlink or not a directory: {self.root}"
            )
        if root_stat.st_mode & 0o022:
            raise BlobIntegrityError(
                f"blob-store root is group/world writable: {self.root}"
            )

    def _read_path(self, path: Path, ref: str) -> bytes:
        try:
            self._validate_directory_chain(path.parent)
            path_stat = os.lstat(path)
        except FileNotFoundError as exc:
            raise BlobNotFound(f"blob not found: {ref}") from exc
        if not stat.S_ISREG(path_stat.st_mode):
            raise BlobIntegrityError(
                f"blob object is a symlink or not a regular file: {ref}"
            )
        if path_stat.st_mode & 0o077:
            raise BlobIntegrityError(
                f"blob object is not a private regular file: {ref}"
            )

        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(
            os, "O_NOFOLLOW", 0
        )
        try:
            descriptor = os.open(path, flags)
        except FileNotFoundError as exc:
            raise BlobNotFound(f"blob not found: {ref}") from exc
        except OSError as exc:
            raise BlobIntegrityError(f"blob object cannot be opened safely: {ref}") from exc
        with os.fdopen(descriptor, "rb") as handle:
            opened_stat = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened_stat.st_mode):
                raise BlobIntegrityError(f"blob object is not a regular file: {ref}")
            if opened_stat.st_mode & 0o077:
                raise BlobIntegrityError(
                    f"blob object is not a private regular file: {ref}"
                )
            return handle.read()

    def _path_for(self, tenant: str, ref: str) -> Path:
        ref_tenant, digest_ref = parse_ref(ref)
        if ref_tenant != tenant:
            raise BlobTenantError(
                f"blob ref tenant {ref_tenant!r} does not match {tenant!r}"
            )
        digest = digest_ref.removeprefix(f"{HASH_ALGO}:")
        tenant_digest = hashlib.sha256(tenant.encode("utf-8")).hexdigest()
        return (
            self.root
            / "tenants"
            / tenant_digest[:2]
            / tenant_digest
            / digest[:2]
            / digest[2:4]
            / digest
        )


def blob_store_from_url(url: str) -> BlobStore:
    """Build a durable blob store from an explicit URL.

    ``file://`` is intentionally the only v1 scheme. It is suitable for one
    host, or for multiple workers only when every replica mounts the exact same
    coherent filesystem. Object-store backends can be added without changing
    the ``BlobStore`` contract.
    """

    parsed = urlparse(url.strip())
    if parsed.scheme != "file":
        raise ValueError(
            f"unsupported blob-store URL {url!r}; supported schemes: file"
        )
    if parsed.netloc not in ("", "localhost"):
        raise ValueError(
            f"blob-store URL must be a local file URL, got host {parsed.netloc!r}"
        )
    if parsed.query or parsed.fragment:
        raise ValueError("blob-store file URL cannot contain a query or fragment")
    root = Path(unquote(parsed.path))
    if not root.is_absolute():
        raise ValueError("blob-store file URL must contain an absolute path")
    root = _normalized_absolute_path(root)
    if _is_filesystem_root(root):
        raise ValueError("blob-store file URL cannot use the filesystem root")
    return LocalDirBlobStore(root)


def _resolve_blob_store_configuration(
    explicit: BlobStore | None,
    url: str | None,
    *,
    explicit_source: str,
) -> BlobStore | None:
    """Resolve one blob-store source, rejecting ambiguous retained refs."""
    normalized_url = "" if url is None else url.strip()
    if not normalized_url:
        return explicit
    if explicit is not None:
        raise ValueError(
            f"blob store configured both by {explicit_source} and "
            "JULEP_BLOB_STORE_URL; choose exactly one"
        )
    return blob_store_from_url(normalized_url)


async def _initialize_blob_store(store: BlobStore | None) -> None:
    """Initialize the built-in filesystem backend off the event loop."""
    if isinstance(store, LocalDirBlobStore):
        await store.initialize()


__all__ = [
    "HASH_ALGO",
    "BlobError",
    "BlobImmutabilityError",
    "BlobIntegrityError",
    "BlobNotFound",
    "BlobStore",
    "BlobTenantError",
    "InMemoryBlobStore",
    "LocalDirBlobStore",
    "blob_store_from_url",
    "content_ref",
    "parse_ref",
]
