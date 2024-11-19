import cloudinary
from beartype import beartype

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

    try:
        # Configure Cloudinary with your credentials
        cloudinary.config(
            cloud_name=setup.cloudinary_cloud_name,
            api_key=setup.cloudinary_api_key,
            api_secret=setup.cloudinary_api_secret,
            **(setup.params or {}),
        )

        # Check if the file is an image or video
        transformed_url = cloudinary.utils.cloudinary_url(
            arguments.file, transformation=arguments.transformation
        )

        # Check if the transformed URL is present
        if not transformed_url or not transformed_url[0]:
            return CloudinaryOutput(transformed_url="The transformation failed")

    except cloudinary.exceptions.Error as e:
        # Handle Cloudinary specific exceptions
        raise RuntimeError(f"Cloudinary error occurred: {e}")

    except Exception as e:
        # Handle any other exceptions
        raise RuntimeError(f"An unexpected error occurred: {e}")

    # Return the result
    return CloudinaryOutput(transformed_url=transformed_url[0])
