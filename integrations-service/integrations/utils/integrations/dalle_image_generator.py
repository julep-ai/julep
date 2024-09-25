from langchain_community.utilities.dalle_image_generator import DallEAPIWrapper

from ...models import DalleImageGeneratorArguments


async def dalle_image_generator(arguments: DalleImageGeneratorArguments) -> str:
    """
    Generates an image using DALL-E based on a provided prompt.
    """
    # FIXME: Fix OpenAI API Key error

    dalle = DallEAPIWrapper()
    prompt = arguments.prompt
    if not prompt:
        raise ValueError("Prompt parameter is required for DALL-E image generation")
    return dalle.run(prompt)
