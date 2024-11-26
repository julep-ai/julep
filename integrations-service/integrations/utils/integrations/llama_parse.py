import base64
import uuid

from beartype import beartype
from llama_parse import LlamaParse
from tenacity import retry, stop_after_attempt, wait_exponential

from ...autogen.Tools import LlamaParseFetchArguments, LlamaParseSetup
from ...env import llama_api_key  # Import env to access environment variables
from ...models import LlamaParseFetchOutput


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def parse(
    setup: LlamaParseSetup, arguments: LlamaParseFetchArguments
) -> LlamaParseFetchOutput:
    """
    Parse and extract content from files using LlamaParse.
    """

    assert isinstance(setup, LlamaParseSetup), "Invalid setup"
    assert isinstance(arguments, LlamaParseFetchArguments), "Invalid arguments"

    # Use walrus operator to simplify assignment and condition
    if (api_key := setup.llamaparse_api_key) == "DEMO_API_KEY":
        api_key = llama_api_key

    parser = LlamaParse(
        api_key=api_key,  # Use the local variable instead
        result_type=arguments.result_format,
        num_workers=arguments.num_workers,
        language=arguments.language,
    )

    # Simplify filename assignment using or operator
    extra_info = {"file_name": arguments.filename or str(uuid.uuid4())}

    # Parse the document (decode inline)
    documents = await parser.aload_data(
        base64.b64decode(arguments.file), 
        extra_info=extra_info
    )

    return LlamaParseFetchOutput(documents=documents)
