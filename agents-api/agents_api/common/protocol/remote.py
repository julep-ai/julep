from typing import Any, Self

from pydantic import BaseModel
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from ...clients import sync_s3
    from ...env import blob_store_bucket
    from ...worker.codec import deserialize, serialize


class RemoteObject(BaseModel):
    key: str
    bucket: str

    @classmethod
    def from_value(cls, x: Any) -> Self:
        sync_s3.setup()

        serialized = serialize(x)

        key = sync_s3.add_object_with_hash(serialized)
        return RemoteObject(key=key, bucket=blob_store_bucket)

    def load(self) -> Any:
        sync_s3.setup()

        fetched = sync_s3.get_object(self.key)
        return deserialize(fetched)
