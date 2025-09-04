import base64
import uuid
from typing import Any

import unstructured_client
from beartype import beartype
from tenacity import retry, stop_after_attempt, wait_exponential
from unstructured_client.models import operations, shared

from ...autogen.Tools import UnstructuredPartitionArguments, UnstructuredSetup
from ...models import UnstructuredParseOutput


def to_unstructured_strategy(
    value: Any, default: shared.Strategy | None = None
) -> shared.Strategy | None:
    """
    Convert a user-provided strategy (string/enum) to unstructured_client.models.shared.Strategy.

    Accepts common aliases and ignores case, spaces, and dashes.
    Returns `default` if value is None or unrecognized.
    """
    if value is None:
        return default
    if isinstance(value, shared.Strategy):
        return value

    s = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "hires": "hi_res",
        "hires_ocr": "hi_res",
        "highres": "hi_res",
        "high_res": "hi_res",
        "ocr": "ocr_only",
        "ocronly": "ocr_only",
        "od": "od_only",
        "odonly": "od_only",
        "object_detection_only": "od_only",
    }
    s = aliases.get(s, s)

    mapping = {
        "fast": shared.Strategy.FAST,
        "hi_res": shared.Strategy.HI_RES,
        "auto": shared.Strategy.AUTO,
        "ocr_only": shared.Strategy.OCR_ONLY,
        "od_only": shared.Strategy.OD_ONLY,
        "vlm": shared.Strategy.VLM,
    }
    return mapping.get(s, default)


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
    # AIDEV-NOTE: Extract and convert strategy/chunking_strategy explicitly for proper API handling
    params = (
        arguments.partition_params
        if hasattr(arguments, "partition_params") and arguments.partition_params
        else {}
    )

    # Extract strategy and chunking_strategy for explicit handling
    # AIDEV-NOTE: Use .get() instead of .pop() to avoid mutating params on retries
    strategy = to_unstructured_strategy(params.get("strategy", None))
    chunking_strategy = params.get("chunking_strategy", None)

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
    # Build partition parameters with explicit strategy and chunking_strategy
    partition_params = {
        "files": shared.Files(
            content=decoded_file,
            file_name=arguments.filename or f"{uuid.uuid4()}.txt",
        ),
    }

    # Add strategy and chunking_strategy explicitly if provided
    if strategy is not None:
        partition_params["strategy"] = strategy
    if chunking_strategy is not None:
        partition_params["chunking_strategy"] = chunking_strategy

    # Spread the rest of the parameters (excluding strategy and chunking_strategy)
    partition_params.update({
        k: v for k, v in params.items() if k not in ["strategy", "chunking_strategy"]
    })

    req = operations.PartitionRequest(
        partition_parameters=shared.PartitionParameters(**partition_params)
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
