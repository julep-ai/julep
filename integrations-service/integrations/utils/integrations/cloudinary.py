import cloudinary
import cloudinary.uploader
from beartype import beartype
from cloudinary.utils import cloudinary_url
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import CloudinaryFetchArguments, CloudinarySetup
from ...models import CloudinaryOutput


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def media_edit(
    setup: CloudinarySetup, arguments: CloudinaryFetchArguments
) -> CloudinaryOutput:
    """
    Edit media in Cloudinary.
    """
    assert isinstance(setup, CloudinarySetup), "Invalid setup"
    assert isinstance(arguments, CloudinaryFetchArguments), "Invalid arguments"

    # import cloudinary

    # Configure Cloudinary with your credentials
    cloudinary.config(
        cloud_name=setup.cloudinary_cloud_name,
        api_key=setup.cloudinary_api_key,
        api_secret=setup.cloudinary_api_secret,
        **(setup.params or {}),
    )

    # Perform a basic upload or transformation
    response = cloudinary.uploader.upload(
        arguments.file, transformation=arguments.transformation
    )

    # Return the result
    return CloudinaryOutput(result=response["result"])
