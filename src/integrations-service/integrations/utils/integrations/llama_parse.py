import base64
import uuid

from beartype import beartype
from llama_parse import LlamaParse
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import LlamaParseFetchArguments, LlamaParseSetup
from ...models import LlamaParseFetchOutput


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def parse(
    setup: LlamaParseSetup,
    arguments: LlamaParseFetchArguments,
) -> LlamaParseFetchOutput:
    """
    Parse and extract content from files using LlamaParse.
    """

    api_key = setup.llamaparse_api_key

    # get the additional params
    params = (
        {**setup.params, **arguments.params}
        if setup.params and arguments.params
        else setup.params or arguments.params
    )

    parser = LlamaParse(
        api_key=api_key,  # Use the local variable instead
        **(params or {}),
    )

    if isinstance(arguments.file, str) and arguments.base64:
        extra_info = {"file_name": arguments.filename or str(uuid.uuid4())}
        # Parse the document (decode inline)
        documents = await parser.aload_data(
            base64.b64decode(arguments.file),
            extra_info=extra_info,
        )
    else:
        extra_info = {"file_name": arguments.filename} if arguments.filename else None
        # Parse the document (decode inline)
        documents = await parser.aload_data(arguments.file, extra_info=extra_info)

    return LlamaParseFetchOutput(documents=documents)
