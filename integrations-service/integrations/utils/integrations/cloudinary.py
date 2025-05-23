import base64
import uuid

import aiohttp
import cloudinary
import cloudinary.uploader
from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import (
    CloudinaryEditArguments,
    CloudinarySetup,
    CloudinaryUploadArguments,
)
from ...models.cloudinary import CloudinaryEditOutput, CloudinaryUploadOutput


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def media_upload(
    setup: CloudinarySetup,
    arguments: CloudinaryUploadArguments,
) -> CloudinaryUploadOutput:
    """
    Upload media to Cloudinary.
    """
    api_key = setup.cloudinary_api_key
    api_secret = setup.cloudinary_api_secret
    cloud_name = setup.cloudinary_cloud_name

    try:
        # Configure Cloudinary with credentials
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            **(setup.params or {}),
        )

        # Upload the file
        upload_params = arguments.upload_params or {}
        upload_params["public_id"] = (
            arguments.public_id if arguments.public_id else str(uuid.uuid4())
        )

        result = cloudinary.uploader.upload(arguments.file, **upload_params)

        meta_data = {
            key: value
            for key, value in result.items()
            if key not in ["secure_url", "public_id"]
        }

        if arguments.return_base64:
            async with (
                aiohttp.ClientSession() as session,
                session.get(result["secure_url"]) as response,
            ):
                if response.status == 200:
                    content = await response.read()
                    base64_encoded = base64.b64encode(content).decode("utf-8")
                    result["base64"] = base64_encoded
                else:
                    msg = f"Failed to download file from URL: {result['secure_url']}"
                    raise RuntimeError(msg)

        return CloudinaryUploadOutput(
            url=result["secure_url"],
            public_id=result["public_id"],
            meta_data=meta_data,
            base64=result["base64"] if arguments.return_base64 else None,
        )

    except cloudinary.exceptions.Error as e:
        msg = f"Cloudinary error occurred: {e}"
        raise RuntimeError(msg)
    except Exception as e:
        msg = f"An unexpected error occurred: {e}"
        raise RuntimeError(msg)


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def media_edit(
    setup: CloudinarySetup,
    arguments: CloudinaryEditArguments,
) -> CloudinaryEditOutput:
    """
    Edit media in Cloudinary.
    """
    api_key = setup.cloudinary_api_key
    api_secret = setup.cloudinary_api_secret
    cloud_name = setup.cloudinary_cloud_name

    try:
        # Configure Cloudinary with credentials
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            **(setup.params or {}),
        )

        # Generate transformed URL
        transformed_url = cloudinary.utils.cloudinary_url(
            arguments.public_id,
            transformation=arguments.transformation,
        )
        if not transformed_url or not transformed_url[0]:
            return CloudinaryEditOutput(
                transformed_url="The transformation failed",
                base64=None,
            )
        if arguments.return_base64:
            async with (
                aiohttp.ClientSession() as session,
                session.get(transformed_url[0]) as response,
            ):
                if response.status == 200:
                    content = await response.read()
                    base64_encoded = base64.b64encode(content).decode("utf-8")
                    transformed_url_base64 = base64_encoded
                else:
                    msg = f"Failed to download file from URL: {transformed_url[0]}"
                    raise RuntimeError(msg)

        return CloudinaryEditOutput(
            transformed_url=transformed_url[0],
            base64=transformed_url_base64 if arguments.return_base64 else None,
        )

    except cloudinary.exceptions.Error as e:
        msg = f"Cloudinary error occurred: {e}"
        raise RuntimeError(msg)
    except Exception as e:
        msg = f"An unexpected error occurred: {e}"
        raise RuntimeError(msg)
