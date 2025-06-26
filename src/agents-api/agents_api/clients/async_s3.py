from beartype import beartype
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    import botocore
    from aiobotocore.client import AioBaseClient
    from async_lru import alru_cache
    from xxhash import xxh3_64_hexdigest as xxhash_key

    from ..env import blob_store_bucket


@alru_cache(maxsize=1)
async def setup() -> AioBaseClient:
    from ..app import app

    client: AioBaseClient | None = getattr(app.state, "s3_client", None)
    if client is None:
        msg = "S3 client not initialized"
        raise RuntimeError(msg)

    try:
        await client.head_bucket(Bucket=blob_store_bucket)
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            try:
                await client.create_bucket(Bucket=blob_store_bucket)
            except botocore.exceptions.ClientError as create_err:
                if create_err.response["Error"]["Code"] != "BucketAlreadyExists":
                    raise create_err
        else:
            raise e

    return client


@alru_cache(maxsize=1024)
async def list_buckets() -> list[str]:
    client = await setup()

    data = await client.list_buckets()
    return [bucket["Name"] for bucket in data["Buckets"]]


@alru_cache(maxsize=10_000)
async def exists(key: str) -> bool:
    client = await setup()

    try:
        await client.head_object(Bucket=blob_store_bucket, Key=key)
        return True
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise e


@beartype
async def add_object(key: str, body: bytes, replace: bool = False) -> None:
    client = await setup()

    if replace:
        await client.put_object(Bucket=blob_store_bucket, Key=key, Body=body)
        return

    if await exists(key):
        return

    await client.put_object(Bucket=blob_store_bucket, Key=key, Body=body)


@beartype
async def get_object(key: str) -> bytes:
    client = await setup()

    response = await client.get_object(Bucket=blob_store_bucket, Key=key)
    return await response["Body"].read()


@beartype
async def delete_object(key: str) -> None:
    client = await setup()
    await client.delete_object(Bucket=blob_store_bucket, Key=key)


@beartype
async def add_object_with_hash(body: bytes, replace: bool = False) -> str:
    key = xxhash_key(body)
    await add_object(key, body, replace=replace)

    return key
