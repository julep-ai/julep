from __future__ import annotations

import hashlib
import sys
from types import SimpleNamespace

import pytest

from julep.cas import (
    CASDigestError,
    CASIntegrityError,
    CASNotFound,
    CASStore,
    LocalDirCAS,
    S3CAS,
    cas_from_url,
)


class _FakeBody:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class _FakeNoSuchKey(Exception):
    pass


class _FakeClientError(Exception):
    def __init__(self, code: str) -> None:
        self.response = {"Error": {"Code": code}}


class _FakeS3Client:
    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.exceptions = SimpleNamespace(NoSuchKey=_FakeNoSuchKey, ClientError=_FakeClientError)

    def put_object(self, *, Bucket: str, Key: str, Body: bytes) -> None:
        self.objects[(Bucket, Key)] = Body

    def get_object(self, *, Bucket: str, Key: str) -> dict[str, _FakeBody]:
        try:
            data = self.objects[(Bucket, Key)]
        except KeyError as exc:
            raise _FakeNoSuchKey(Key) from exc
        return {"Body": _FakeBody(data)}

    def head_object(self, *, Bucket: str, Key: str) -> dict[str, object]:
        if (Bucket, Key) not in self.objects:
            raise _FakeClientError("404")
        return {}


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _local_path(store: LocalDirCAS, digest: str):
    return store.root / digest[:2] / digest[2:4] / digest


def test_local_dir_cas_round_trip(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    data = b"flow json bytes"
    digest = store.put(data)

    assert digest == _digest(data)
    assert store.has(digest)
    assert not store.has(_digest(b"missing"))
    assert store.get(digest) == data


def test_local_dir_cas_write_once_and_integrity_check(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    data = b"pure source"
    digest = store.put(data)

    assert store.put(data) == digest

    _local_path(store, digest).write_bytes(b"corrupted")
    with pytest.raises(CASIntegrityError):
        store.put(data)
    with pytest.raises(CASIntegrityError):
        store.get(digest)


def test_local_dir_cas_missing_and_malformed_digest(tmp_path) -> None:
    store = LocalDirCAS(tmp_path)
    missing = _digest(b"absent")

    with pytest.raises(CASNotFound):
        store.get(missing)
    assert not store.has(missing)

    for bad in ["", "abc", "g" * 64, "A" * 64, "sha256:" + missing]:
        with pytest.raises(CASDigestError):
            store.get(bad)
        with pytest.raises(CASDigestError):
            store.has(bad)


def test_cas_store_has_no_delete_remove_or_clear_api() -> None:
    for cls in (CASStore, LocalDirCAS, S3CAS):
        assert not hasattr(cls, "delete")
        assert not hasattr(cls, "remove")
        assert not hasattr(cls, "clear")


def test_s3_cas_round_trip_and_head_backed_has() -> None:
    client = _FakeS3Client()
    store = S3CAS("bucket", "prefix/", client=client)
    data = b"manifest"
    digest = store.put(data)

    assert digest == _digest(data)
    assert client.objects[("bucket", f"prefix/{digest}")] == data
    assert store.has(digest)
    assert not store.has(_digest(b"missing"))
    assert store.get(digest) == data


def test_s3_cas_write_once_mismatch_and_get_integrity() -> None:
    client = _FakeS3Client()
    store = S3CAS("bucket", client=client)
    data = b"env binary"
    digest = store.put(data)

    assert store.put(data) == digest

    client.objects[("bucket", digest)] = b"corrupted"
    with pytest.raises(CASIntegrityError):
        store.put(data)
    with pytest.raises(CASIntegrityError):
        store.get(digest)


def test_cas_from_url_file_and_s3(monkeypatch, tmp_path) -> None:
    file_store = cas_from_url(tmp_path.as_uri())
    assert isinstance(file_store, LocalDirCAS)
    assert file_store.root == tmp_path

    fake_client = _FakeS3Client()
    monkeypatch.setattr("julep.cas._make_default_client", lambda: fake_client)
    s3_store = cas_from_url("s3://bundle-bucket/path/to/cas")
    assert isinstance(s3_store, S3CAS)
    assert s3_store.bucket == "bundle-bucket"
    assert s3_store.prefix == "path/to/cas"


def test_cas_from_url_unknown_scheme_lists_supported_schemes() -> None:
    with pytest.raises(ValueError, match="supported schemes: file, s3"):
        cas_from_url("gs://bucket/prefix")


def test_s3_cas_missing_boto3_error_is_actionable(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "boto3", None)
    with pytest.raises(RuntimeError, match=r"julep\[store\]"):
        S3CAS("bucket")
