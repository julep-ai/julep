from functools import cache, lru_cache

from beartype import beartype
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import boto3
    import botocore
    from xxhash import xxh3_64_hexdigest as xxhash_key

    from ..env import (
        blob_store_bucket,
        blob_store_cutoff_kb,
        s3_access_key,
        s3_endpoint,
        s3_secret_key,
    )


@cache
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=s3_endpoint,
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
    )


def list_buckets() -> list[str]:
    client = get_s3_client()
    data = client.list_buckets()
    buckets = [bucket["Name"] for bucket in data["Buckets"]]

    return buckets


@cache
def setup():
    client = get_s3_client()
    if blob_store_bucket not in list_buckets():
        client.create_bucket(Bucket=blob_store_bucket)


@lru_cache(maxsize=10_000)
def exists(key: str) -> bool:
    client = get_s3_client()

    try:
        client.head_object(Bucket=blob_store_bucket, Key=key)
        return True

    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        else:
            raise e


@beartype
def add_object(key: str, body: bytes, replace: bool = False) -> None:
    client = get_s3_client()

    if replace:
        client.put_object(Bucket=blob_store_bucket, Key=key, Body=body)
        return

    if exists(key):
        return

    client.put_object(Bucket=blob_store_bucket, Key=key, Body=body)


@lru_cache(maxsize=256 * 1024 // max(1, blob_store_cutoff_kb))  # 256mb in cache
@beartype
def get_object(key: str) -> bytes:
    client = get_s3_client()
    return client.get_object(Bucket=blob_store_bucket, Key=key)["Body"].read()


@beartype
def delete_object(key: str) -> None:
    client = get_s3_client()
    client.delete_object(Bucket=blob_store_bucket, Key=key)


@beartype
def add_object_with_hash(body: bytes, replace: bool = False) -> str:
    key = xxhash_key(body)
    add_object(key, body, replace=replace)

    return key
