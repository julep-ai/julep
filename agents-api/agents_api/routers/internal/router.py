from fastapi import APIRouter, Request
from google.protobuf import json_format
from temporalio.api.common.v1 import Payloads

from ...worker.codec import PydanticEncodingPayloadConverter

router: APIRouter = APIRouter()

converter = PydanticEncodingPayloadConverter()


# Decode route
@router.post("/temporal/decode", tags=["temporal"])
async def decode_payloads(req: Request) -> dict:
    body = json_format.Parse(await req.body(), Payloads())
    payloads = body.payloads

    decoded_payloads = []

    for p in payloads:
        data = converter.from_payload(p)

        if hasattr(data, "model_dump"):
            data = data.model_dump()

        decoded_payloads.append({"data": data, "metadata": p.metadata})

    return {"payloads": decoded_payloads}
