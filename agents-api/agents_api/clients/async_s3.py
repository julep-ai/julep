from beartype import beartype
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import botocore
    from aiobotocore.session import get_session
    from async_lru import alru_cache
    from xxhash import xxh3_64_hexdigest as xxhash_key

    from ..env import (
        blob_store_bucket,
        blob_store_cutoff_kb,
        s3_access_key,
        s3_endpoint,
        s3_secret_key,
    )


@alru_cache(maxsize=1024)
async def list_buckets() -> list[str]:
    session = get_session()

    async with session.create_client(
        "s3",
        endpoint_url=s3_endpoint,
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
    ) as client:
        data = await client.list_buckets()
        buckets = [bucket["Name"] for bucket in data["Buckets"]]
        return buckets


@alru_cache(maxsize=1)
async def setup():
    session = get_session()

    async with session.create_client(
        "s3",
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        endpoint_url=s3_endpoint,
    ) as client:
        if blob_store_bucket not in await list_buckets():
            await client.create_bucket(Bucket=blob_store_bucket)


@alru_cache(maxsize=10_000)
async def exists(key: str) -> bool:
    session = get_session()

    async with session.create_client(
        "s3",
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        endpoint_url=s3_endpoint,
    ) as client:
        try:
            await client.head_object(Bucket=blob_store_bucket, Key=key)
            return True
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                raise e


@beartype
async def add_object(key: str, body: bytes, replace: bool = False) -> None:
    session = get_session()

    async with session.create_client(
        "s3",
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        endpoint_url=s3_endpoint,
    ) as client:
        if replace:
            await client.put_object(Bucket=blob_store_bucket, Key=key, Body=body)
            return

        if await exists(key):
            return

        await client.put_object(Bucket=blob_store_bucket, Key=key, Body=body)


@alru_cache(maxsize=256 * 1024 // max(1, blob_store_cutoff_kb))  # 256mb in cache
@beartype
async def get_object(key: str) -> bytes:
    session = get_session()

    async with session.create_client(
        "s3",
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        endpoint_url=s3_endpoint,
    ) as client:
        response = await client.get_object(Bucket=blob_store_bucket, Key=key)
        body = await response["Body"].read()
        return body


@beartype
async def delete_object(key: str) -> None:
    session = get_session()

    async with session.create_client(
        "s3",
        aws_access_key_id=s3_access_key,
        aws_secret_access_key=s3_secret_key,
        endpoint_url=s3_endpoint,
    ) as client:
        await client.delete_object(Bucket=blob_store_bucket, Key=key)


@beartype
async def add_object_with_hash(body: bytes, replace: bool = False) -> str:
    key = xxhash_key(body)
    await add_object(key, body, replace=replace)

    return key
