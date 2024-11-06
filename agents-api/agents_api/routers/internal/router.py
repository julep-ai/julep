from fastapi import APIRouter, Request
from google.protobuf import json_format
from temporalio.api.common.v1 import Payloads

from ...worker.codec import PydanticEncodingPayloadConverter

router: APIRouter = APIRouter()

converter = PydanticEncodingPayloadConverter()


# Decode route
@router.post("/temporal/decode", tags=["temporal"])
async def decode_payloads(req: Request):
    """Decodes a list of payloads from the request body.

    Args:
        req (Request): The request containing the payloads to decode.

    Returns:
        dict: A dictionary containing the decoded payloads, including any errors encountered.
    """
    body = json_format.Parse(await req.body(), Payloads())
    payloads = body.payloads
    decoded_payloads = []

    for p in payloads:
        # Attempt to decode the payload
        data = converter.from_payload(p)

        # Handle Pydantic models
        if hasattr(data, "model_dump"):
            data = data.model_dump()

        # Handle bytes data
        elif isinstance(data, bytes):
            try:
                data = data.decode("utf-8")
            except UnicodeDecodeError:
                # If it's not UTF-8 encoded text, leave it as bytes
                data = str(data)

        # Convert metadata more safely
        metadata = {}
        for k, v in p.metadata.items():
            try:
                metadata[k] = v.decode() if isinstance(v, bytes) else v
            except UnicodeDecodeError:
                metadata[k] = str(v)

        decoded_payloads.append({"data": data, "metadata": metadata})

    return {"payloads": decoded_payloads}
