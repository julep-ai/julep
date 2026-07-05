"""T7 — worker registration of the durable-session activities + the claim-check
data converter helper.

Fast unit tests: no Temporal server is stood up. We check that the activity
callables are registered on ``worker.ACTIVITIES`` and that
``claim_check_converter`` returns a :class:`DataConverter` whose
``payload_codec`` is a :class:`ClaimCheckCodec` bound to the given blob store /
tenant / threshold.
"""

from __future__ import annotations

import pytest

pytest.importorskip("temporalio")

from temporalio.converter import DataConverter

from julep.execution import worker as worker_mod
from julep.execution.activities import (
    commitState,
    loadState,
    putBlob,
)
from julep.execution.blobstore import InMemoryBlobStore
from julep.execution.codec import ClaimCheckCodec
from julep.execution.worker import claim_check_converter


def test_durable_activities_registered() -> None:
    for act in (loadState, commitState, putBlob):
        assert act in worker_mod.ACTIVITIES


def test_claim_check_converter_returns_dataconverter() -> None:
    conv = claim_check_converter(InMemoryBlobStore(), tenant="t")
    assert isinstance(conv, DataConverter)


def test_claim_check_converter_installs_codec() -> None:
    blob_store = InMemoryBlobStore()
    conv = claim_check_converter(blob_store, tenant="acme", threshold_bytes=4096)

    codec = conv.payload_codec
    assert isinstance(codec, ClaimCheckCodec)
    assert codec._blob_store is blob_store
    assert codec._tenant == "acme"
    assert codec._threshold_bytes == 4096


def test_claim_check_converter_default_threshold() -> None:
    codec = claim_check_converter(InMemoryBlobStore(), tenant="t").payload_codec
    assert isinstance(codec, ClaimCheckCodec)
    assert codec._threshold_bytes == 131072


def test_claim_check_converter_exported() -> None:
    assert "claim_check_converter" in worker_mod.__all__
