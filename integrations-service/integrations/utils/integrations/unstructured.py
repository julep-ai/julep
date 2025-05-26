import base64
import uuid

import unstructured_client
from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential
from unstructured_client.models import operations, shared

from ...autogen.Tools import UnstructuredPartitionArguments, UnstructuredSetup
from ...models import UnstructuredParseOutput


@beartype
@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    stop=stop_after_attempt(4),
)
async def parse(
    setup: UnstructuredSetup,
    arguments: UnstructuredPartitionArguments,
) -> UnstructuredParseOutput:
    """
    Parse documents into structured elements using Unstructured.io.
    """

    api_key = setup.unstructured_api_key

    # Create a new client with all available parameters
    client = unstructured_client.UnstructuredClient(
        api_key_auth=api_key,
        server_url=setup.server_url,
        server=setup.server,
        url_params=setup.url_params,
        timeout_ms=setup.timeout_ms,
    )

    # Decode the base64 encoded file
    try:
        decoded_file = base64.b64decode(arguments.file)
    except Exception as e:
        msg = f"Failed to decode base64 encoded file: {e}"
        raise RuntimeError(msg)

    # Process file
    req = operations.PartitionRequest(
        partition_parameters=shared.PartitionParameters(
            files=shared.Files(
                content=decoded_file,
                file_name=arguments.filename or f"{uuid.uuid4()}.txt",
            ),
            **(
                arguments.partition_params
                if hasattr(arguments, "partition_params") and arguments.partition_params
                else {}
            ),
        )
    )

    try:
        # Make the API call
        result = await client.general.partition_async(request=req)
        return UnstructuredParseOutput(
            content_type=result.content_type,
            status_code=result.status_code,
            csv_elements=result.csv_elements or None,
            content=result.elements or None,
        )
    except Exception as e:
        # Return error information instead of raising HTTP exception
        msg = f"Error executing Unstructured method: {e}"
        raise RuntimeError(msg)
