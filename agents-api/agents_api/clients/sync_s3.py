import os
from functools import lru_cache

from beartype import beartype
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import botocore
    from xxhash import xxh3_64_hexdigest as xxhash_key

    from ..env import blob_store_bucket


@lru_cache(maxsize=1)
def setup():
    # INIT S3 #
    s3_access_key = os.environ.get("S3_ACCESS_KEY")
    s3_secret_key = os.environ.get("S3_SECRET_KEY")
    s3_endpoint = os.environ.get("S3_ENDPOINT")

    session = botocore.session.Session()
    client = session.create_client(
        "s3",
        endpoint_url=s3_endpoint,
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        config=botocore.config.Config(
            signature_version="s3v4", retries={"max_attempts": 3}
        ),
    )

    try:
        client.head_bucket(Bucket=blob_store_bucket)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            try:
                client.create_bucket(Bucket=blob_store_bucket)
            except botocore.exceptions.ClientError as create_err:
                if create_err.response["Error"]["Code"] != "BucketAlreadyExists":
                    raise create_err
        else:
            raise e

    return client


@lru_cache(maxsize=1024)
def list_buckets() -> list[str]:
    client = setup()

    data = client.list_buckets()
    return [bucket["Name"] for bucket in data["Buckets"]]


@lru_cache(maxsize=10_000)
def exists(key: str) -> bool:
    client = setup()

    try:
        client.head_object(Bucket=blob_store_bucket, Key=key)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise e


@beartype
def add_object(key: str, body: bytes, replace: bool = False) -> None:
    client = setup()

    if replace:
        client.put_object(Bucket=blob_store_bucket, Key=key, Body=body)
        return

    if exists(key):
        return

    client.put_object(Bucket=blob_store_bucket, Key=key, Body=body)


@beartype
def get_object(key: str) -> bytes:
    client = setup()

    response = client.get_object(Bucket=blob_store_bucket, Key=key)
    return response["Body"].read()


@beartype
def delete_object(key: str) -> None:
    client = setup()
    client.delete_object(Bucket=blob_store_bucket, Key=key)


@beartype
def add_object_with_hash(body: bytes, replace: bool = False) -> str:
    key = xxhash_key(body)
    add_object(key, body, replace=replace)

    return key
