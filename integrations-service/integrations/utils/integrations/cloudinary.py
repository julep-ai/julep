import base64

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
from ...env import (  # Import env to access environment variables
    cloudinary_api_key,
    cloudinary_api_secret,
    cloudinary_cloud_name,
)
from ...models.cloudinary import CloudinaryEditOutput, CloudinaryUploadOutput


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def media_upload(
    setup: CloudinarySetup, arguments: CloudinaryUploadArguments
) -> CloudinaryUploadOutput:
    """
    Upload media to Cloudinary.
    """
    assert isinstance(setup, CloudinarySetup), "Invalid setup"
    assert isinstance(arguments, CloudinaryUploadArguments), "Invalid arguments"

    try:
        # Configure Cloudinary with credentials
        cloudinary.config(
            cloud_name=setup.cloudinary_cloud_name
            if setup.cloudinary_cloud_name != "DEMO_CLOUD_NAME"
            else cloudinary_cloud_name,
            api_key=setup.cloudinary_api_key
            if setup.cloudinary_api_key != "DEMO_API_KEY"
            else cloudinary_api_key,
            api_secret=setup.cloudinary_api_secret
            if setup.cloudinary_api_secret != "DEMO_API_SECRET"
            else cloudinary_api_secret,
            **(setup.params or {}),
        )

        # Upload the file
        upload_params = arguments.upload_params or {}
        if arguments.public_id:
            upload_params["public_id"] = arguments.public_id

        result = cloudinary.uploader.upload(arguments.file, **upload_params)

        meta_data = {
            key: value
            for key, value in result.items()
            if key not in ["secure_url", "public_id"]
        }

        if arguments.return_base64:
            async with aiohttp.ClientSession() as session:
                async with session.get(result["secure_url"]) as response:
                    if response.status == 200:
                        content = await response.read()
                        base64_encoded = base64.b64encode(content).decode("utf-8")
                        result["base64"] = base64_encoded
                    else:
                        raise RuntimeError(
                            f"Failed to download file from URL: {result['secure_url']}"
                        )
        return CloudinaryUploadOutput(
            url=result["secure_url"],
            public_id=result["public_id"],
            meta_data=meta_data,
            base64=result["base64"] if arguments.return_base64 else None,
        )

    except cloudinary.exceptions.Error as e:
        raise RuntimeError(f"Cloudinary error occurred: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def media_edit(
    setup: CloudinarySetup, arguments: CloudinaryEditArguments
) -> CloudinaryEditOutput:
    """
    Edit media in Cloudinary.
    """
    assert isinstance(setup, CloudinarySetup), "Invalid setup"
    assert isinstance(arguments, CloudinaryEditArguments), "Invalid arguments"

    try:
        # Configure Cloudinary with credentials
        cloudinary.config(
            cloud_name=setup.cloudinary_cloud_name
            if setup.cloudinary_cloud_name != "DEMO_CLOUD_NAME"
            else cloudinary_cloud_name,
            api_key=setup.cloudinary_api_key
            if setup.cloudinary_api_key != "DEMO_API_KEY"
            else cloudinary_api_key,
            api_secret=setup.cloudinary_api_secret
            if setup.cloudinary_api_secret != "DEMO_API_SECRET"
            else cloudinary_api_secret,
            **(setup.params or {}),
        )

        # Generate transformed URL
        transformed_url = cloudinary.utils.cloudinary_url(
            arguments.public_id, transformation=arguments.transformation
        )
        if not transformed_url or not transformed_url[0]:
            return CloudinaryEditOutput(
                transformed_url="The transformation failed",
                base64=None,
            )
        if arguments.return_base64:
            async with aiohttp.ClientSession() as session:
                async with session.get(transformed_url[0]) as response:
                    if response.status == 200:
                        content = await response.read()
                        base64_encoded = base64.b64encode(content).decode("utf-8")
                        transformed_url_base64 = base64_encoded
                    else:
                        raise RuntimeError(
                            f"Failed to download file from URL: {transformed_url[0]}"
                        )

        return CloudinaryEditOutput(
            transformed_url=transformed_url[0],
            base64=transformed_url_base64 if arguments.return_base64 else None,
        )

    except cloudinary.exceptions.Error as e:
        raise RuntimeError(f"Cloudinary error occurred: {e}")
    except Exception as e:
        raise RuntimeError(f"An unexpected error occurred: {e}")
