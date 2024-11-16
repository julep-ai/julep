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
    setup: LlamaParseSetup, arguments: LlamaParseFetchArguments
) -> LlamaParseFetchOutput:
    """
    Parse and extract content from files using LlamaParse.
    """

    assert isinstance(setup, LlamaParseSetup), "Invalid setup"
    assert isinstance(arguments, LlamaParseFetchArguments), "Invalid arguments"

    parser = LlamaParse(
        api_key=setup.llamaparse_api_key,
        result_type=arguments.result_format,
        num_workers=arguments.num_workers,
        language=arguments.language,
    )

    # Decode base64 file content
    file_content = base64.b64decode(arguments.file)
    extra_info = {
        "file_name": arguments.filename if arguments.filename else str(uuid.uuid4())
    }

    # Parse the document
    documents = await parser.aload_data(file_content, extra_info=extra_info)

    return LlamaParseFetchOutput(documents=documents)
