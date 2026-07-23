"""Tests for the blob-durability contract (design note "The blob-durability
contract"). The store is pure (no Temporal); async methods are driven via
``asyncio.run`` inside sync test functions — the repo has no asyncio pytest
plugin (see tests/test_e2e_temporal.py for the pattern).
"""

from __future__ import annotations

import asyncio
import hashlib
import stat
from pathlib import Path

import pytest

import julep.execution.blobstore as blobstore_module

from julep.execution.blobstore import (
    HASH_ALGO,
    BlobImmutabilityError,
    BlobIntegrityError,
    BlobNotFound,
    BlobTenantError,
    InMemoryBlobStore,
    LocalDirBlobStore,
    blob_store_from_url,
    content_ref,
    parse_ref,
)


def test_hash_algo_is_sha256() -> None:
    assert HASH_ALGO == "sha256"


def test_content_ref_format() -> None:
    data = b"hello world"
    digest = hashlib.sha256(data).hexdigest()
    ref = content_ref("acme", data)
    assert ref == f"acme/sha256:{digest}"


def test_content_ref_rejects_empty_tenant() -> None:
    with pytest.raises(BlobTenantError):
        content_ref("", b"x")


def test_content_ref_rejects_tenant_with_slash() -> None:
    with pytest.raises(BlobTenantError):
        content_ref("ac/me", b"x")


def test_parse_ref_round_trip() -> None:
    ref = content_ref("acme", b"payload")
    tenant, digest = parse_ref(ref)
    assert tenant == "acme"
    assert digest == "sha256:" + hashlib.sha256(b"payload").hexdigest()
    # Reassembling from the parts yields the original ref.
    assert f"{tenant}/{digest}" == ref


@pytest.mark.parametrize(
    "bad",
    [
        "no-slash-or-colon",
        "acme/md5:deadbeef",  # wrong algo
        "acme/sha256",  # missing :hex
        "/sha256:abcd",  # empty tenant
        "acme/sha256:",  # empty hex
        "",
    ],
)
def test_parse_ref_malformed_raises(bad: str) -> None:
    with pytest.raises(BlobTenantError):
        parse_ref(bad)


def test_put_get_byte_round_trip() -> None:
    store = InMemoryBlobStore()
    data = b"the quick brown fox"

    async def go() -> bytes:
        ref = await store.put("acme", data)
        assert ref == content_ref("acme", data)
        return await store.get("acme", ref)

    assert asyncio.run(go()) == data


def test_identical_bytes_dedup() -> None:
    store = InMemoryBlobStore()
    data = b"dedup me"

    async def go() -> tuple[str, str]:
        ref1 = await store.put("acme", data)
        ref2 = await store.put("acme", data)
        return ref1, ref2

    ref1, ref2 = asyncio.run(go())
    assert ref1 == ref2
    # Dedup: only one backing entry for identical bytes.
    assert len(store._blobs) == 1


def test_immutability_violation_raises() -> None:
    store = InMemoryBlobStore()
    data = b"original"
    ref = asyncio.run(store.put("acme", data))
    # Forge a collision: same ref, different bytes, by poking the backing dict.
    store._blobs[ref] = b"tampered-different-length"

    async def go() -> None:
        await store.put("acme", data)

    with pytest.raises(BlobImmutabilityError):
        asyncio.run(go())


def test_integrity_violation_raises() -> None:
    store = InMemoryBlobStore()
    data = b"trustworthy"
    ref = asyncio.run(store.put("acme", data))
    # Corrupt the stored bytes via the test seam (the backing dict).
    store._blobs[ref] = b"corrupted"

    async def go() -> bytes:
        return await store.get("acme", ref)

    with pytest.raises(BlobIntegrityError):
        asyncio.run(go())


def test_tenant_mismatch_raises() -> None:
    store = InMemoryBlobStore()
    ref = asyncio.run(store.put("acme", b"secret"))

    async def go() -> bytes:
        # A different tenant must not read acme's blob by presenting acme's ref.
        return await store.get("other", ref)

    with pytest.raises(BlobTenantError):
        asyncio.run(go())


def test_missing_ref_raises_not_found() -> None:
    store = InMemoryBlobStore()
    absent = content_ref("acme", b"never-stored")

    async def go() -> bytes:
        return await store.get("acme", absent)

    with pytest.raises(BlobNotFound):
        asyncio.run(go())


def test_local_dir_store_survives_reconstruction_and_deduplicates(
    tmp_path: Path,
) -> None:
    root = tmp_path / "blobs"
    data = b"durable transcript observation"
    first = LocalDirBlobStore(root)
    assert not root.exists()  # construction never blocks on filesystem setup

    async def write() -> tuple[str, str]:
        return await first.put("acme", data), await first.put("acme", data)

    ref, duplicate = asyncio.run(write())
    assert ref == duplicate == content_ref("acme", data)

    second = LocalDirBlobStore(root)
    assert asyncio.run(second.get("acme", ref)) == data


def test_local_dir_store_concurrent_puts_are_idempotent(tmp_path: Path) -> None:
    root = tmp_path / "blobs"
    first = LocalDirBlobStore(root)
    second = LocalDirBlobStore(root)

    async def write() -> tuple[str, str]:
        left, right = await asyncio.gather(
            first.put("acme", b"same payload"),
            second.put("acme", b"same payload"),
        )
        return left, right

    left, right = asyncio.run(write())
    assert left == right
    assert asyncio.run(first.get("acme", left)) == b"same payload"
    files = [path for path in root.rglob("*") if path.is_file()]
    assert len(files) == 1
    assert not files[0].name.startswith(".")


def test_local_dir_store_keeps_identical_content_tenant_scoped(
    tmp_path: Path,
) -> None:
    store = LocalDirBlobStore(tmp_path / "blobs")
    data = b"shared bytes"
    acme_ref = asyncio.run(store.put("acme", data))
    other_ref = content_ref("other", data)

    assert asyncio.run(store.get("acme", acme_ref)) == data
    with pytest.raises(BlobNotFound):
        asyncio.run(store.get("other", other_ref))


def test_local_dir_store_hashes_tenant_path_components(tmp_path: Path) -> None:
    root = tmp_path / "blobs"
    store = LocalDirBlobStore(root)
    ref = asyncio.run(store.put("..", b"contained"))

    assert asyncio.run(store.get("..", ref)) == b"contained"
    files = [path for path in root.rglob("*") if path.is_file()]
    assert len(files) == 1
    assert files[0].resolve().is_relative_to(root.resolve())
    assert not (tmp_path / ("sha256:" + "0" * 64)).exists()


def test_local_dir_store_detects_on_disk_corruption(tmp_path: Path) -> None:
    root = tmp_path / "blobs"
    store = LocalDirBlobStore(root)
    ref = asyncio.run(store.put("acme", b"trustworthy"))
    (stored_path,) = [path for path in root.rglob("*") if path.is_file()]
    stored_path.write_bytes(b"corrupted")

    with pytest.raises(BlobIntegrityError):
        asyncio.run(store.get("acme", ref))


def test_local_dir_store_rejects_symlinked_namespace(tmp_path: Path) -> None:
    root = tmp_path / "blobs"
    outside = tmp_path / "outside"
    outside.mkdir()
    store = LocalDirBlobStore(root)
    asyncio.run(store.initialize())
    ref = content_ref("acme", b"external bytes")
    path = store._path_for("acme", ref)
    path.parent.parent.mkdir(parents=True)
    path.parent.symlink_to(outside, target_is_directory=True)
    (outside / path.name).write_bytes(b"external bytes")

    with pytest.raises(BlobIntegrityError, match="symlink|directory"):
        asyncio.run(store.get("acme", ref))


def test_local_dir_store_publishes_private_files_and_directories(
    tmp_path: Path,
) -> None:
    root = tmp_path / "blobs"
    store = LocalDirBlobStore(root)
    asyncio.run(store.put("acme", b"private"))
    files = [path for path in root.rglob("*") if path.is_file()]
    directories = [root, *[path for path in root.rglob("*") if path.is_dir()]]

    assert len(files) == 1
    assert stat.S_IMODE(files[0].stat().st_mode) == 0o600
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o700 for path in directories)


def test_local_dir_store_syncs_published_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = LocalDirBlobStore(tmp_path / "blobs")
    asyncio.run(store.initialize())
    synced: list[Path] = []
    monkeypatch.setattr(blobstore_module, "_fsync_directory", synced.append)

    ref = asyncio.run(store.put("acme", b"durable"))

    assert store._path_for("acme", ref).parent in synced


def test_local_dir_store_retries_directory_sync_after_published_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = LocalDirBlobStore(tmp_path / "blobs")
    asyncio.run(store.initialize())
    ref = content_ref("acme", b"durable retry")
    path = store._path_for("acme", ref)
    store._ensure_directory_chain(path.parent)
    original = blobstore_module._fsync_directory
    attempts = 0

    def fail_first_publish_sync(directory: Path) -> None:
        nonlocal attempts
        if directory == path.parent:
            attempts += 1
            if attempts == 1:
                raise OSError("simulated directory fsync failure")
        original(directory)

    monkeypatch.setattr(
        blobstore_module, "_fsync_directory", fail_first_publish_sync
    )
    with pytest.raises(OSError, match="simulated"):
        asyncio.run(store.put("acme", b"durable retry"))

    assert path.is_file()
    assert asyncio.run(store.put("acme", b"durable retry")) == ref
    assert attempts == 2


def test_local_dir_store_syncs_each_new_root_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "one" / "two" / "blobs"
    synced: list[Path] = []
    original = blobstore_module._fsync_directory

    def record_sync(directory: Path) -> None:
        synced.append(directory)
        original(directory)

    monkeypatch.setattr(blobstore_module, "_fsync_directory", record_sync)
    asyncio.run(LocalDirBlobStore(root).initialize())

    assert tmp_path in synced
    assert tmp_path / "one" in synced
    assert tmp_path / "one" / "two" in synced
    assert root in synced  # the newly created tenants entry


def test_local_dir_store_retries_failed_root_entry_sync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "one" / "two" / "blobs"
    store = LocalDirBlobStore(root)
    original = blobstore_module._fsync_directory
    attempts = 0

    def fail_first_root_sync(directory: Path) -> None:
        nonlocal attempts
        if directory == tmp_path:
            attempts += 1
            if attempts == 1:
                raise OSError("simulated root-entry fsync failure")
        original(directory)

    monkeypatch.setattr(blobstore_module, "_fsync_directory", fail_first_root_sync)
    with pytest.raises(OSError, match="root-entry"):
        asyncio.run(store.initialize())

    asyncio.run(store.initialize())
    assert attempts == 2


def test_local_dir_store_retries_failed_shard_entry_sync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "blobs"
    store = LocalDirBlobStore(root)
    asyncio.run(store.initialize())
    original = blobstore_module._fsync_directory
    attempts = 0
    tenants = root / "tenants"

    def fail_first_shard_sync(directory: Path) -> None:
        nonlocal attempts
        if directory == tenants:
            attempts += 1
            if attempts == 1:
                raise OSError("simulated shard-entry fsync failure")
        original(directory)

    monkeypatch.setattr(blobstore_module, "_fsync_directory", fail_first_shard_sync)
    with pytest.raises(OSError, match="shard-entry"):
        asyncio.run(store.put("acme", b"shard retry"))

    ref = asyncio.run(store.put("acme", b"shard retry"))
    assert asyncio.run(store.get("acme", ref)) == b"shard retry"
    assert attempts == 2


def test_local_dir_store_rejects_public_namespace_permissions(
    tmp_path: Path,
) -> None:
    root = tmp_path / "blobs"
    tenants = root / "tenants"
    tenants.mkdir(parents=True)
    tenants.chmod(0o777)

    with pytest.raises(BlobIntegrityError, match="private directory"):
        asyncio.run(LocalDirBlobStore(root).initialize())


def test_local_dir_store_rejects_public_object_permissions(tmp_path: Path) -> None:
    root = tmp_path / "blobs"
    store = LocalDirBlobStore(root)
    ref = asyncio.run(store.put("acme", b"private"))
    path = store._path_for("acme", ref)
    path.chmod(0o644)

    with pytest.raises(BlobIntegrityError, match="private regular file"):
        asyncio.run(store.get("acme", ref))


def test_blob_store_from_url_builds_file_store(tmp_path: Path) -> None:
    store = blob_store_from_url(tmp_path.as_uri())
    assert isinstance(store, LocalDirBlobStore)
    assert store.root == tmp_path


@pytest.mark.parametrize(
    "url",
    ["file:///tmp/..", "file:///var/%2e%2e"],
)
def test_blob_store_from_url_rejects_normalized_filesystem_root(url: str) -> None:
    with pytest.raises(ValueError, match="filesystem root"):
        blob_store_from_url(url)


def test_local_dir_store_rejects_symlink_to_filesystem_root(tmp_path: Path) -> None:
    link = tmp_path / "root-link"
    link.symlink_to(Path("/"), target_is_directory=True)
    try:
        store = blob_store_from_url(link.as_uri())
        assert isinstance(store, LocalDirBlobStore)

        with pytest.raises(ValueError, match="filesystem root"):
            asyncio.run(store.initialize())
    finally:
        link.unlink()


@pytest.mark.parametrize("url", ["s3://bucket/prefix", "gs://bucket/prefix"])
def test_blob_store_from_url_rejects_unsupported_schemes(url: str) -> None:
    with pytest.raises(ValueError, match="supported schemes: file"):
        blob_store_from_url(url)


def test_blob_store_from_url_rejects_non_local_file_host() -> None:
    with pytest.raises(ValueError, match="local file URL"):
        blob_store_from_url("file://remote-host/var/lib/julep/blobs")


@pytest.mark.parametrize(
    "url",
    [
        "file:relative/blobs",
        "file:///var/lib/julep/blobs?mode=unsafe",
        "file:///var/lib/julep/blobs#fragment",
    ],
)
def test_blob_store_from_url_rejects_ambiguous_file_urls(url: str) -> None:
    with pytest.raises(ValueError):
        blob_store_from_url(url)
