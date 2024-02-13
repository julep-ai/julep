import argparse
import asyncio
from contextlib import suppress
from http import HTTPStatus
import json
import logging
import time
from typing import AsyncGenerator, Optional, Annotated

from aioprometheus.asgi.starlette import metrics
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, BackgroundTasks, Request, Depends
from fastapi.responses import Response, JSONResponse, StreamingResponse
from fastapi.exceptions import RequestValidationError
from jsonschema.exceptions import ValidationError
from lmformatenforcer import JsonSchemaParser
from pydantic import UUID4, Field, BaseModel
import sentry_sdk

from vllm.engine.metrics import add_global_metrics_labels
from vllm.engine.arg_utils import AsyncEngineArgs
from vllm.engine.async_llm_engine import AsyncLLMEngine
from vllm.utils import random_uuid
from vllm.transformers_utils.tokenizer import get_tokenizer
from vllm.entrypoints.openai.protocol import (
    CompletionRequest,
    CompletionResponse,
    CompletionResponseChoice,
    CompletionResponseStreamChoice,
    CompletionStreamResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatCompletionResponseStreamChoice,
    ChatCompletionStreamResponse,
    ChatMessage,
    DeltaMessage,
    ErrorResponse,
    LogProbs,
    ModelCard,
    ModelList,
    ModelPermission,
    UsageInfo,
)
from vllm.outputs import RequestOutput

from .conversion.conversions import to_prompt, parse_message
from .conversion.datatypes import ChatML

from .conversion.exceptions import (
    InvalidPromptException,
    InvalidFunctionName,
)
from .logger import logger
from .env import (
    sentry_dsn,
    temperature_scaling_factor,
    temperature_scaling_power,
)

from .metrics import (
    tokens_per_user_metric,
    generation_time_metric,
    generated_tokens_per_second_metric,
    MetricsMiddleware,
)
from .dependencies.auth import get_api_key
from .dependencies.developer import get_developer_id, get_developer_email
from .dependencies.exceptions import InvalidHeaderFormat
from .utils import (
    validate_functions,
    vllm_with_character_level_parser,
    FunctionCallResult,
    rescale_temperature,
)


engine = None
engine_model_config = None
tokenizer = None
served_model = None


model_settings = {
    "julep-ai/samantha-1-turbo": {
        "section_start_tag": "<|im_start|>",
        "section_end_tag": "<|im_end|>",
    }
}


if not sentry_dsn:
    print("Sentry DSN not found. Sentry will not be enabled.")
else:
    sentry_sdk.init(
        dsn=sentry_dsn,
        enable_tracing=True,
    )


DEFAULT_MAX_TOKENS = 4000


class ChatMessage(ChatMessage):
    name: str | None = None


class DeltaMessage(DeltaMessage):
    name: str | None = None


class ChatCompletionResponseChoice(ChatCompletionResponseChoice):
    message: ChatMessage


class ChatCompletionResponseStreamChoice(ChatCompletionResponseStreamChoice):
    delta: DeltaMessage


class ChatCompletionStreamResponse(ChatCompletionStreamResponse):
    choices: list[ChatCompletionResponseStreamChoice]


class ResponseFormat(BaseModel):
    type_: str = Field(..., alias="type")


class ChatCompletionRequest(ChatCompletionRequest):
    functions: list[dict] | None = None
    function_call: str | None = None
    response_format: ResponseFormat | None = None
    max_tokens: int | None = DEFAULT_MAX_TOKENS
    spaces_between_special_tokens: Optional[bool] = False
    messages: ChatML
    temperature: Optional[float] = 0.0


class CompletionRequest(CompletionRequest):
    spaces_between_special_tokens: Optional[bool] = False
    temperature: Optional[float] = 0.0


class EndpointFilter(logging.Filter):
    def __init__(self, endpoints: list[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._endpoints = endpoints

    def filter(self, record: logging.LogRecord) -> bool:
        return all([record.getMessage().find(e) == -1 for e in self._endpoints])


logging.getLogger("uvicorn.access").addFilter(
    EndpointFilter(["/docs", "/status", "/metrics"]),
)


app = FastAPI(dependencies=[Depends(get_api_key)])


TIMEOUT_KEEP_ALIVE = 30  # seconds.
AGENT_NAME = "Samantha"


def create_logprobs(
    token_ids: list[int],
    id_logprobs: list[dict[int, float]],
    initial_text_offset: int = 0,
) -> LogProbs:
    """Create OpenAI-style logprobs."""
    logprobs = LogProbs()
    last_token_len = 0
    for token_id, id_logprob in zip(token_ids, id_logprobs):
        token = tokenizer.convert_ids_to_tokens(token_id)
        logprobs.tokens.append(token)
        logprobs.token_logprobs.append(id_logprob[token_id])
        if len(logprobs.text_offset) == 0:
            logprobs.text_offset.append(initial_text_offset)
        else:
            logprobs.text_offset.append(logprobs.text_offset[-1] + last_token_len)
        last_token_len = len(token)

        logprobs.top_logprobs.append(
            {tokenizer.convert_ids_to_tokens(i): p for i, p in id_logprob.items()}
        )
    return logprobs


async def check_length(request, prompt, model_config):
    if hasattr(model_config.hf_config, "max_sequence_length"):
        context_len = model_config.hf_config.max_sequence_length
    elif hasattr(model_config.hf_config, "seq_length"):
        context_len = model_config.hf_config.seq_length
    elif hasattr(model_config.hf_config, "max_position_embeddings"):
        context_len = model_config.hf_config.max_position_embeddings
    elif hasattr(model_config.hf_config, "seq_length"):
        context_len = model_config.hf_config.seq_length
    else:
        context_len = 2048

    input_ids = tokenizer(prompt).input_ids
    token_num = len(input_ids)

    if token_num + request.max_tokens > context_len:
        return create_error_response(
            HTTPStatus.BAD_REQUEST,
            f"This model's maximum context length is {context_len} tokens. "
            f"However, you requested {request.max_tokens + token_num} tokens "
            f"({token_num} in the messages, "
            f"{request.max_tokens} in the completion). "
            f"Please reduce the length of the messages or completion.",
        )
    else:
        return None


@app.exception_handler(InvalidPromptException)
async def invalid_prompt_exception_handler(
    request: Request, exc: InvalidPromptException
):
    return JSONResponse(
        status_code=400,
        content={"error": {"message": str(exc), "code": "invalid prompt"}},
    )


@app.exception_handler(json.decoder.JSONDecodeError)
async def json_decode_error_handler(
    request: Request, exc: json.decoder.JSONDecodeError
):
    return JSONResponse(
        status_code=400,
        content={"error": {"message": str(exc), "code": "invalid json input"}},
    )


@app.exception_handler(InvalidFunctionName)
async def invalid_function_name_handler(request: Request, exc: InvalidFunctionName):
    return JSONResponse(
        status_code=400,
        content={"error": {"message": str(exc), "code": "invalid function call"}},
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": {"message": str(exc), "code": "invalid functions parameter"}},
    )


@app.exception_handler(InvalidHeaderFormat)
async def invalid_dev_header_error_handler(request: Request, exc: InvalidHeaderFormat):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": "The API key used has invalid metadata. Please contact support for fixing this issue",
                "code": "invalid API key",
            }
        },
    )


def create_error_response(
    status_code: HTTPStatus,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        ErrorResponse(
            message=message,
            type="invalid_request_error",
            code=status_code.value,
        ).dict(),
        status_code=status_code.value,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):  # pylint: disable=unused-argument
    return create_error_response(HTTPStatus.BAD_REQUEST, str(exc))


async def check_model(request) -> Optional[JSONResponse]:
    if request.model == served_model:
        return
    ret = create_error_response(
        HTTPStatus.NOT_FOUND,
        f"The model `{request.model}` does not exist.",
    )
    return ret


@app.get("/v1/models")
async def show_available_models():
    """Show available models. Right now we only have one model."""
    model_cards = [
        ModelCard(
            id=served_model,
            root=served_model,
            permission=[ModelPermission()],
        )
    ]
    return ModelList(data=model_cards)


def _write_metrics(
    total_gen_time: float,
    total_tokens: float,
    developer: UUID4 | None = None,
    email: UUID4 | None = None,
):
    developer = str(developer)
    email = str(email)
    generation_time_metric.set({"developer": developer, "email": email}, total_gen_time)
    tokens_per_user_metric.add({"developer": developer, "email": email}, total_tokens)
    generated_tokens_per_second_metric.set(
        {"developer": developer, "email": email}, total_tokens / total_gen_time
    )


@app.post("/v1/completions")
async def completions(
    raw_request: Request,
    background_tasks: BackgroundTasks,
    x_developer_id: Annotated[UUID4 | None, Depends(get_developer_id)] = None,
    x_developer_email: Annotated[UUID4 | None, Depends(get_developer_email)] = None,
) -> Response:
    """Completion API similar to OpenAI's API.

    See https://platform.openai.com/docs/api-reference/completions/create
    for the API specification. This API mimics the OpenAI Completion API.

    NOTE: Currently we do not support the following features:
        - echo (since the vLLM engine does not currently support
          getting the logprobs of prompt tokens)
        - suffix (the language models we currently support do not support
          suffix)
        - logit_bias (to be supported by vLLM engine)
    """
    request = CompletionRequest(**await raw_request.json())
    logger.info(f"Received completion request: {request}")

    error_check_ret = await check_model(request)
    if error_check_ret is not None:
        return error_check_ret

    if request.echo:
        # We do not support echo since the vLLM engine does not
        # currently support getting the logprobs of prompt tokens.
        return create_error_response(
            HTTPStatus.BAD_REQUEST, "echo is not currently supported"
        )

    if request.suffix is not None:
        # The language models we currently support do not support suffix.
        return create_error_response(
            HTTPStatus.BAD_REQUEST, "suffix is not currently supported"
        )

    if request.logit_bias is not None:
        # TODO: support logit_bias in vLLM engine.
        return create_error_response(
            HTTPStatus.BAD_REQUEST, "logit_bias is not currently supported"
        )

    model_name = request.model
    request_id = f"cmpl-{random_uuid()}"
    if isinstance(request.prompt, list):
        if len(request.prompt) == 0:
            return create_error_response(
                HTTPStatus.BAD_REQUEST, "please provide at least one prompt"
            )
        if len(request.prompt) > 1:
            return create_error_response(
                HTTPStatus.BAD_REQUEST,
                "multiple prompts in a batch is not currently supported",
            )
        prompt = request.prompt[0]
    else:
        prompt = request.prompt
    created_time = int(time.time())
    sampling_params = request.to_sampling_params()

    # Rescale the temperature
    sampling_params.temperature = rescale_temperature(
        sampling_params.temperature,
        temperature_scaling_factor,
        power=temperature_scaling_power,  # Set it to lower than 1.0 to punish high temperatures more
    )

    result_generator = engine.generate(
        prompt,
        sampling_params,
        request_id,
    )

    # Similar to the OpenAI API, when n != best_of, we do not stream the
    # results. In addition, we do not stream the results when use beam search.
    stream = (
        request.stream
        and (request.best_of is None or request.n == request.best_of)
        and not request.use_beam_search
    )

    async def abort_request() -> None:
        await engine.abort(request_id)

    def create_stream_response_json(
        index: int,
        text: str,
        logprobs: Optional[LogProbs] = None,
        finish_reason: Optional[str] = None,
    ) -> str:
        choice_data = CompletionResponseStreamChoice(
            index=index,
            text=text,
            logprobs=logprobs,
            finish_reason=finish_reason,
        )
        response = CompletionStreamResponse(
            id=request_id,
            created=created_time,
            model=model_name,
            choices=[choice_data],
        )
        response_json = response.json()

        return response_json

    async def completion_stream_generator() -> AsyncGenerator[str, None]:
        previous_texts = [""] * request.n
        previous_num_tokens = [0] * request.n
        start = time.time()
        async for res in result_generator:
            res: RequestOutput
            for output in res.outputs:
                i = output.index
                delta_text = output.text[len(previous_texts[i]) :]
                if request.logprobs is not None:
                    logprobs = create_logprobs(
                        output.token_ids[previous_num_tokens[i] :],
                        output.logprobs[previous_num_tokens[i] :],
                        len(previous_texts[i]),
                    )
                else:
                    logprobs = None
                previous_texts[i] = output.text
                previous_num_tokens[i] = len(output.token_ids)
                response_json = create_stream_response_json(
                    index=i,
                    text=delta_text,
                    logprobs=logprobs,
                )
                yield f"data: {response_json}\n\n"
                if output.finish_reason is not None:
                    logprobs = LogProbs() if request.logprobs is not None else None
                    response_json = create_stream_response_json(
                        index=i,
                        text="",
                        logprobs=logprobs,
                        finish_reason=output.finish_reason,
                    )
                    yield f"data: {response_json}\n\n"

        total_gen_time = time.time() - start
        total_tokens = sum(previous_num_tokens)
        background_tasks.add_task(
            _write_metrics,
            total_gen_time,
            total_tokens,
            x_developer_id,
            x_developer_email,
        )

        yield "data: [DONE]\n\n"

    # Streaming response
    if stream:
        background_tasks = BackgroundTasks()
        # Abort the request if the client disconnects.
        background_tasks.add_task(abort_request)
        return StreamingResponse(
            completion_stream_generator(),
            media_type="text/event-stream",
            background=background_tasks,
        )

    # Non-streaming response
    final_res: RequestOutput = None
    start = time.time()
    async for res in result_generator:
        if await raw_request.is_disconnected():
            # Abort the request if the client disconnects.
            await abort_request()
            return create_error_response(HTTPStatus.BAD_REQUEST, "Client disconnected")
        final_res = res

    tokens_gen_time = time.time() - start

    assert final_res is not None
    choices = []
    for output in final_res.outputs:
        if request.logprobs is not None:
            logprobs = create_logprobs(output.token_ids, output.logprobs)
        else:
            logprobs = None
        choice_data = CompletionResponseChoice(
            index=output.index,
            text=output.text,
            logprobs=logprobs,
            finish_reason=output.finish_reason,
        )
        choices.append(choice_data)

    num_prompt_tokens = len(final_res.prompt_token_ids)
    num_generated_tokens = sum(len(output.token_ids) for output in final_res.outputs)
    total_tokens = num_prompt_tokens + num_generated_tokens

    background_tasks.add_task(
        _write_metrics,
        tokens_gen_time,
        total_tokens,
        x_developer_id,
        x_developer_email,
    )

    usage = UsageInfo(
        prompt_tokens=num_prompt_tokens,
        completion_tokens=num_generated_tokens,
        total_tokens=total_tokens,
    )

    response = CompletionResponse(
        id=request_id,
        created=created_time,
        model=model_name,
        choices=choices,
        usage=usage,
    )

    if request.stream:
        # When user requests streaming but we don't stream, we still need to
        # return a streaming response with a single event.
        response_json = response.json()

        async def fake_stream_generator() -> AsyncGenerator[str, None]:
            yield f"data: {response_json}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            fake_stream_generator(), media_type="text/event-stream"
        )

    return response


@app.post("/v1/chat/completions")
async def chat_completions(
    raw_request: Request,
    background_tasks: BackgroundTasks,
    x_developer_id: Annotated[UUID4 | None, Depends(get_developer_id)] = None,
    x_developer_email: Annotated[UUID4 | None, Depends(get_developer_email)] = None,
) -> Response:
    """Completion API similar to OpenAI's API.

    See  https://platform.openai.com/docs/api-reference/chat/create
    for the API specification. This API mimics the OpenAI ChatCompletion API.

    NOTE: Currently we do not support the following features:
        - function_call (Users should implement this by themselves)
        - logit_bias (to be supported by vLLM engine)
    """
    request = ChatCompletionRequest(**await raw_request.json())
    logger.info(f"Received chat completion request: {request}")

    if request.functions:
        validate_functions(request.functions)

    error_check_ret = await check_model(request)
    if error_check_ret is not None:
        return error_check_ret

    if request.logit_bias is not None:
        # TODO: support logit_bias in vLLM engine.
        return create_error_response(
            HTTPStatus.BAD_REQUEST,
            "logit_bias is not currently supported",
        )

    bos = model_settings[request.model]["section_start_tag"]
    eos = model_settings[request.model]["section_end_tag"]
    prompt = to_prompt(
        request.messages,
        bos=bos,
        eos=eos,
        functions=request.functions,
        function_call=request.function_call,
    )

    append_fcall_prefix = False

    if request.functions and request.function_call and request.function_call != "auto":
        with suppress(IndexError):
            if prompt.split("\n")[-1].startswith('{"name":'):
                append_fcall_prefix = True

    # prompt = await get_gen_prompt(request)
    error_check_ret = await check_length(request, prompt, engine_model_config)
    if error_check_ret is not None:
        return error_check_ret

    model_name = request.model
    request_id = f"cmpl-{random_uuid()}"
    created_time = int(time.time())
    sampling_params = request.to_sampling_params()

    # Rescale the temperature
    sampling_params.temperature = rescale_temperature(
        sampling_params.temperature,
        temperature_scaling_factor,
        power=temperature_scaling_power,  # Set it to lower than 1.0 to punish high temperatures more
    )

    if (
        request.response_format is not None
        and request.response_format.type_ == "json_object"
    ):
        result_generator = vllm_with_character_level_parser(
            engine,
            tokenizer,
            prompt,
            sampling_params,
            request_id,
            parser=JsonSchemaParser(
                (
                    FunctionCallResult.model_json_schema()
                    if request.function_call is not None
                    and request.function_call not in ("none", "auto")
                    else {}
                ),
            ),
        )

    else:
        result_generator = engine.generate(
            prompt,
            sampling_params,
            request_id,
        )

    async def abort_request() -> None:
        await engine.abort(request_id)

    def create_stream_response_json(
        index: int,
        text: str,
        role: str = "assistant",
        name: Optional[str] = None,
        finish_reason: Optional[str] = None,
    ) -> str:
        choice_data = ChatCompletionResponseStreamChoice(
            index=index,
            delta=DeltaMessage(role=role, content=text, name=name),
            finish_reason=finish_reason,
        )
        response = ChatCompletionStreamResponse(
            id=request_id,
            created=created_time,
            model=model_name,
            choices=[choice_data],
        )
        response_json = response.json()

        return response_json

    async def completion_stream_generator() -> AsyncGenerator[str, None]:
        # First chunk with role
        # for i in range(request.n):
        #     choice_data = ChatCompletionResponseStreamChoice(
        #         index=i,
        #         delta=DeltaMessage(role="assistant"),
        #         finish_reason=None,
        #     )
        #     chunk = ChatCompletionStreamResponse(
        #         id=request_id, choices=[choice_data], model=model_name
        #     )
        #     data = chunk.json(exclude_unset=True)
        #     yield f"data: {data}\n\n"

        previous_texts = [""] * request.n
        previous_num_tokens = [0] * request.n
        start = time.time()
        role = "assistant"
        name = None
        async for res in result_generator:
            res: RequestOutput
            for idx, output in enumerate(res.outputs):
                i = output.index
                delta_text = output.text[len(previous_texts[i]) :]
                if not idx:
                    if append_fcall_prefix:
                        delta_text = f'{{"name": "{request.function_call}",{delta_text}'

                    msg = parse_message(delta_text).dict()
                    role = msg.get(
                        "role",
                        "assistant" if not append_fcall_prefix else "function_call",
                    )
                    name = msg.get("name")

                    for i in range(request.n):
                        choice_data = ChatCompletionResponseStreamChoice(
                            index=i,
                            delta=DeltaMessage(role=role),
                            finish_reason=None,
                        )
                        chunk = ChatCompletionStreamResponse(
                            id=request_id, choices=[choice_data], model=model_name
                        )
                        data = chunk.json(exclude_unset=True)
                        yield f"data: {data}\n\n"

                previous_texts[i] = output.text
                previous_num_tokens[i] = len(output.token_ids)
                response_json = create_stream_response_json(
                    index=i,
                    text=delta_text,
                    role=role,
                    name=name,
                )
                yield f"data: {response_json}\n\n"
                if output.finish_reason is not None:
                    response_json = create_stream_response_json(
                        index=i,
                        text="",
                        role=role,
                        name=name,
                        finish_reason=output.finish_reason,
                    )
                    yield f"data: {response_json}\n\n"

        total_gen_time = time.time() - start
        total_tokens = sum(previous_num_tokens)

        background_tasks.add_task(
            _write_metrics,
            total_gen_time,
            total_tokens,
            x_developer_id,
            x_developer_email,
        )

        yield "data: [DONE]\n\n"

    # Streaming response
    if request.stream:
        background_tasks = BackgroundTasks()
        # Abort the request if the client disconnects.
        background_tasks.add_task(abort_request)
        return StreamingResponse(
            completion_stream_generator(),
            media_type="text/event-stream",
            background=background_tasks,
        )

    # Non-streaming response
    final_res: RequestOutput = None
    start = time.time()
    async for res in result_generator:
        if await raw_request.is_disconnected():
            # Abort the request if the client disconnects.
            await abort_request()
            return create_error_response(HTTPStatus.BAD_REQUEST, "Client disconnected")
        final_res = res

    tokens_gen_time = time.time() - start

    assert final_res is not None
    choices = []
    for output in final_res.outputs:
        msg = parse_message(output.text).dict()
        choice_data = ChatCompletionResponseChoice(
            index=output.index,
            message=ChatMessage(
                role=msg.get(
                    "role", "assistant" if not append_fcall_prefix else "function_call"
                ),
                name=msg.get("name"),
                content=(
                    f'{{"name": "{request.function_call}",{msg.get("content", "")}'
                    if append_fcall_prefix
                    else msg.get("content", "")
                ),
            ),
            finish_reason=output.finish_reason,
        )
        choices.append(choice_data)

    num_prompt_tokens = len(final_res.prompt_token_ids)
    num_generated_tokens = sum(len(output.token_ids) for output in final_res.outputs)
    total_tokens = num_prompt_tokens + num_generated_tokens
    usage = UsageInfo(
        prompt_tokens=num_prompt_tokens,
        completion_tokens=num_generated_tokens,
        total_tokens=total_tokens,
    )

    background_tasks.add_task(
        _write_metrics,
        tokens_gen_time,
        total_tokens,
        x_developer_id,
        x_developer_email,
    )

    response = ChatCompletionResponse(
        id=request_id,
        created=created_time,
        model=model_name,
        choices=choices,
        usage=usage,
    )

    if request.stream:
        # When user requests streaming but we don't stream, we still need to
        # return a streaming response with a single event.
        response_json = response.json()

        async def fake_stream_generator() -> AsyncGenerator[str, None]:
            yield f"data: {response_json}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(
            fake_stream_generator(),
            media_type="text/event-stream",
        )

    return response


@app.get("/status")
async def status():
    return {"status": "ok"}


@app.post("/me")
async def me():
    return {"status": "ok"}


app.add_middleware(
    MetricsMiddleware,
    exclude_paths=["/metrics", "/docs", "/status"],
)

app.add_route("/metrics", metrics)


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins="*",
    allow_methods="*",
    allow_headers="*",
)
# app.add_middleware(
#     BaseHTTPMiddleware,
#     dispatch=make_logging_middleware(
#         exclude_urls=["/status", "/docs", "/openapi.json"]
#     ),
# )
# # TODO: should we enable this middleware for completion endpoints only?
# app.add_middleware(
#     BaseHTTPMiddleware,
#     dispatch=make_billing_middleware(
#         exclude_urls=[
#             "/status",
#             "/v1/models",
#             "/docs",
#             "/openapi.json",
#             "/metrics",
#         ]
#     ),
# )


def create_app(args=None):
    global engine, engine_model_config, tokenizer, served_model

    parser = argparse.ArgumentParser(
        description="vLLM OpenAI-Compatible RESTful API server."
    )
    parser.add_argument(
        "--log-stats", type=bool, default=True, help="log stats metrics"
    )
    parser.add_argument(
        "--served-model-name",
        type=str,
        default=None,
        help="The model name used in the API. If not "
        "specified, the model name will be the same as "
        "the huggingface name.",
    )

    parser = AsyncEngineArgs.add_cli_args(parser)
    args = parser.parse_args(args=args)

    logger.info(f"args: {args}")

    if args.served_model_name is not None:
        served_model = args.served_model_name
    else:
        served_model = args.model

    engine_args = AsyncEngineArgs.from_cli_args(args)
    engine = AsyncLLMEngine.from_engine_args(engine_args)
    engine_model_config = asyncio.run(engine.get_model_config())

    # A separate tokenizer to map token IDs to strings.
    tokenizer = get_tokenizer(
        engine_args.tokenizer,
        tokenizer_mode=engine_args.tokenizer_mode,
        trust_remote_code=engine_args.trust_remote_code,
    )

    add_global_metrics_labels(model_name=engine_args.model)

    return app
