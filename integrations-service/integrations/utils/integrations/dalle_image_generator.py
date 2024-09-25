from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper

from ...models import DalleImageGeneratorArguments, DalleImageGeneratorSetup


async def dalle_image_generator(
    setup: DalleImageGeneratorSetup, arguments: DalleImageGeneratorArguments
) -> str:
    """
    Generates an image using DALL-E based on a provided prompt.
    """

    assert isinstance(setup, DalleImageGeneratorSetup), "Invalid setup"
    assert isinstance(arguments, DalleImageGeneratorArguments), "Invalid arguments"

    # FIXME: Fix OpenAI API Key error

    dalle = DallEAPIWrapper(api_key=setup.api_key)
    prompt = arguments.prompt
    if not prompt:
        raise ValueError("Prompt parameter is required for DALL-E image generation")
    return dalle.run(prompt)
