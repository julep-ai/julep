from fastapi import Request, Response, HTTPException, status
from typing import List, Iterable
from google.protobuf import json_format
from fastapi.responses import JSONResponse
from temporalio.api.common.v1 import Payloads, Payload
from temporalio.converter import PayloadCodec
from ...worker.codec import PydanticEncodingPayloadConverter
from fastapi import APIRouter

class CodecInstantion(PayloadCodec):
    def __init__(self) -> None:
        super().__init__()
        self.converter = PydanticEncodingPayloadConverter() 

    async def encode(self, payloads: Iterable[Payload]) -> List[Payload]:
        return [
            self.converter.to_payload(p)
            for p in payloads
        ]

    async def decode(self, payloads: Iterable[Payload]) -> List[Payload]:
        ret: List[Payload] = []
        for p in payloads:
            payload_data = self.converter.from_payload(p)
            ret.append(Payload.FromString(bytes(payload_data)))
        return ret

# Assuming Payloads and Payload are properly defined, and EncryptionCodec class is implemented
router: APIRouter = APIRouter()
# codec instantiation
codec = CodecInstantion()

# CORS middleware
async def cors_middleware(req: Request) -> Response:
    origin = req.headers.get("origin")
    # Set specific CORS headers for requests from "*
    if origin == "*":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "content-type,x-namespace",
        }
        return Response(status_code=200, headers=headers)
    return Response(status_code=status.HTTP_400_BAD_REQUEST)  # Forbidden for other origins

# Encode route
@router.post("/encode", tags=["encryption"])
async def encode_payloads(req: Request) -> Response:
    if req.headers.get("Content-Type") != "application/json":
        raise HTTPException(status_code=400, detail="Invalid content type")
    
    payloads = json_format.Parse(await req.read(), Payloads())

    # Apply encoding
    encoded_payloads = Payloads(payloads=await codec.encode(payloads.payloads))
    print(encoded_payloads)

    response = JSONResponse(content=json_format.MessageToDict(encoded_payloads))    
    print(response)
    # response = await cors_middleware(response)

    return response

# Decode route
@router.post("/decode", tags=["decryption"])
async def decode_payloads(req: Request)-> Response:
    if req.headers.get("Content-Type") != "application/json":
        raise HTTPException(status_code=400, detail="Invalid content type")

    payloads = json_format.Parse(await req.read(), Payloads())

    # Apply decoding
    decoded_payloads = Payloads(payloads=await codec.decode(payloads.payloads))

    print(decoded_payloads)
    response = JSONResponse(content=json_format.MessageToDict(decoded_payloads))

    print(response)
    # response = await cors_middleware(response)
    
    return response