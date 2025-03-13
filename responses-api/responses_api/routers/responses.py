"""Router for the /responses endpoint."""

import logging
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from responses_api.env import config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/responses",
    tags=["Responses"],
)

# These models are placeholders until we generate the actual models from the OpenAPI spec
class CreateResponse(BaseModel):
    """Request model for creating a response."""
    
    model: str
    input: Union[str, List[Dict[str, Any]]]
    include: Optional[List[str]] = None
    parallel_tool_calls: Optional[bool] = True
    store: Optional[bool] = True
    stream: Optional[bool] = False
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = None
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    instructions: Optional[str] = None
    previous_response_id: Optional[str] = None
    reasoning: Optional[Dict[str, Any]] = None
    text: Optional[Dict[str, Any]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = "auto"
    tools: Optional[List[Dict[str, Any]]] = None
    truncation: Optional[str] = "disabled"
    metadata: Optional[Dict[str, Any]] = None

class ResponseUsage(BaseModel):
    """Usage information for a response."""
    
    input_tokens: int
    input_tokens_details: Dict[str, int]
    output_tokens: int
    output_tokens_details: Dict[str, int]
    total_tokens: int

class Response(BaseModel):
    """Response model for a created response."""
    
    id: str
    object: str = "response"
    created_at: int
    status: str
    error: Optional[Dict[str, Any]] = None
    incomplete_details: Optional[Dict[str, Any]] = None
    instructions: Optional[str] = None
    max_output_tokens: Optional[int] = None
    model: str
    output: List[Dict[str, Any]]
    parallel_tool_calls: bool = True
    previous_response_id: Optional[str] = None
    reasoning: Optional[Dict[str, Any]] = None
    store: Optional[bool] = True
    temperature: float = 1.0
    text: Optional[Dict[str, Any]] = None
    tool_choice: Union[str, Dict[str, Any]] = "auto"
    tools: List[Dict[str, Any]] = []
    top_p: float = 1.0
    truncation: str = "disabled"
    usage: ResponseUsage
    user: Optional[str] = None
    metadata: Dict[str, Any] = {}

async def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify the API key."""
    if not config.API_KEY:
        return
    
    if not authorization:
        raise HTTPException(status_code=401, detail="API key required")
    
    if authorization != f"Bearer {config.API_KEY}":
        raise HTTPException(status_code=401, detail="Invalid API key")

@router.post("", response_model=Response)
async def create_response(
    request: Request,
    body: CreateResponse,
    api_key: None = Depends(verify_api_key),
):
    """Create a model response."""
    logger.info(f"Creating response with model: {body.model}")
    
    # This is a placeholder implementation
    # In a real implementation, we would call the LLM service
    
    if body.stream:
        return StreamingResponse(
            content=stream_response(body),
            media_type="text/event-stream",
        )
    
    # Return a mock response for now
    return {
        "id": "resp_123456789",
        "object": "response",
        "created_at": 1741476542,
        "status": "completed",
        "error": None,
        "incomplete_details": None,
        "instructions": body.instructions,
        "max_output_tokens": None,
        "model": body.model,
        "output": [
            {
                "type": "message",
                "id": "msg_123456789",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": "This is a placeholder response from the Responses API.",
                        "annotations": []
                    }
                ]
            }
        ],
        "parallel_tool_calls": body.parallel_tool_calls or True,
        "previous_response_id": body.previous_response_id,
        "reasoning": body.reasoning,
        "store": body.store or True,
        "temperature": body.temperature or 1.0,
        "text": body.text,
        "tool_choice": body.tool_choice or "auto",
        "tools": body.tools or [],
        "top_p": body.top_p or 1.0,
        "truncation": body.truncation or "disabled",
        "usage": {
            "input_tokens": 10,
            "input_tokens_details": {
                "cached_tokens": 0
            },
            "output_tokens": 10,
            "output_tokens_details": {
                "reasoning_tokens": 0
            },
            "total_tokens": 20
        },
        "user": body.user,
        "metadata": body.metadata or {}
    }

async def stream_response(body: CreateResponse):
    """Stream a response."""
    # This is a placeholder implementation
    # In a real implementation, we would stream the response from the LLM service
    
    # Yield the response.created event
    yield f'event: response.created\ndata: {{"type":"response.created","response":{{"id":"resp_123456789","object":"response","created_at":1741476542,"status":"in_progress","error":null,"incomplete_details":null,"instructions":null,"max_output_tokens":null,"model":"{body.model}","output":[],"parallel_tool_calls":true,"previous_response_id":null,"reasoning":{{"effort":null,"summary":null}},"store":true,"temperature":1.0,"text":{{"format":{{"type":"text"}}}},"tool_choice":"auto","tools":[],"top_p":1.0,"truncation":"disabled","usage":null,"user":null,"metadata":{{}}}}}}\n\n'
    
    # Yield the response.in_progress event
    yield f'event: response.in_progress\ndata: {{"type":"response.in_progress","response":{{"id":"resp_123456789","object":"response","created_at":1741476542,"status":"in_progress","error":null,"incomplete_details":null,"instructions":null,"max_output_tokens":null,"model":"{body.model}","output":[],"parallel_tool_calls":true,"previous_response_id":null,"reasoning":{{"effort":null,"summary":null}},"store":true,"temperature":1.0,"text":{{"format":{{"type":"text"}}}},"tool_choice":"auto","tools":[],"top_p":1.0,"truncation":"disabled","usage":null,"user":null,"metadata":{{}}}}}}\n\n'
    
    # Yield the response.output_item.added event
    yield 'event: response.output_item.added\ndata: {"type":"response.output_item.added","output_index":0,"item":{"id":"msg_123456789","type":"message","status":"in_progress","role":"assistant","content":[]}}\n\n'
    
    # Yield the response.content_part.added event
    yield 'event: response.content_part.added\ndata: {"type":"response.content_part.added","item_id":"msg_123456789","output_index":0,"content_index":0,"part":{"type":"output_text","text":"","annotations":[]}}\n\n'
    
    # Yield the response.output_text.delta events
    text = "This is a placeholder response from the Responses API."
    for char in text:
        yield f'event: response.output_text.delta\ndata: {{"type":"response.output_text.delta","item_id":"msg_123456789","output_index":0,"content_index":0,"delta":"{char}"}}\n\n'
    
    # Yield the response.output_text.done event
    yield f'event: response.output_text.done\ndata: {{"type":"response.output_text.done","item_id":"msg_123456789","output_index":0,"content_index":0,"text":"{text}"}}\n\n'
    
    # Yield the response.content_part.done event
    yield f'event: response.content_part.done\ndata: {{"type":"response.content_part.done","item_id":"msg_123456789","output_index":0,"content_index":0,"part":{{"type":"output_text","text":"{text}","annotations":[]}}}}\n\n'
    
    # Yield the response.output_item.done event
    yield f'event: response.output_item.done\ndata: {{"type":"response.output_item.done","output_index":0,"item":{{"id":"msg_123456789","type":"message","status":"completed","role":"assistant","content":[{{"type":"output_text","text":"{text}","annotations":[]}}]}}}}\n\n'
    
    # Yield the response.completed event
    yield f'event: response.completed\ndata: {{"type":"response.completed","response":{{"id":"resp_123456789","object":"response","created_at":1741476542,"status":"completed","error":null,"incomplete_details":null,"instructions":null,"max_output_tokens":null,"model":"{body.model}","output":[{{"id":"msg_123456789","type":"message","status":"completed","role":"assistant","content":[{{"type":"output_text","text":"{text}","annotations":[]}}]}}],"parallel_tool_calls":true,"previous_response_id":null,"reasoning":{{"effort":null,"summary":null}},"store":true,"temperature":1.0,"text":{{"format":{{"type":"text"}}}},"tool_choice":"auto","tools":[],"top_p":1.0,"truncation":"disabled","usage":{{"input_tokens":10,"output_tokens":10,"output_tokens_details":{{"reasoning_tokens":0}},"total_tokens":20}},"user":null,"metadata":{{}}}}}}\n\n' 