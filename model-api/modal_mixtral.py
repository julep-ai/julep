import os

from modal import Image, Secret, Stub, asgi_app, gpu


###############
## Constants ##
###############

MODEL_DIR = os.environ.get("MODEL_DIR", "/model")
MODEL_NAME = os.environ.get("MODEL_NAME", "TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-AWQ")

MAX_NUM_SEQS = int(os.environ.get("MAX_NUM_SEQS", 1))
MAX_MODEL_LEN = int(os.environ.get("MAX_MODEL_LEN", 4096))


###########
## Tasks ##
###########


def download_model_to_folder():
    from huggingface_hub import snapshot_download
    from transformers.utils import move_cache

    os.makedirs(MODEL_DIR, exist_ok=True)

    snapshot_download(
        MODEL_NAME,
        local_dir=MODEL_DIR,
    )

    move_cache()


###########
## Image ##
###########

image = (
    Image.from_registry("nvidia/cuda:12.1.1-base-ubuntu22.04", add_python="3.10")
    .apt_install()
    .pip_install(
        "vllm<0.4",
        "huggingface-hub",
        "hf-transfer",
    )
    # Use the barebones hf-transfer package for maximum download speeds. No progress bar, but expect 700MB/s.
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_function(
        download_model_to_folder,
        timeout=60 * 20,
        secrets=[
            Secret.from_name("mixtral-configuration"),
        ],
    )
)


################
## Entrypoint ##
################

stub = Stub("mixtral-api", image=image)


@stub.function(
    gpu=gpu.A100(size="80GB"),
    container_idle_timeout=600,
    allow_concurrent_inputs=25,
    keep_warm=0,
    timeout=120,
    secrets=[
        Secret.from_name("mixtral-configuration"),
    ],
)
@asgi_app()
def get_app():
    from fastapi.responses import JSONResponse
    from vllm.engine.arg_utils import AsyncEngineArgs
    from vllm.engine.async_llm_engine import AsyncLLMEngine
    from vllm.entrypoints.openai.serving_chat import OpenAIServingChat
    from vllm.entrypoints.openai.serving_completion import OpenAIServingCompletion

    import vllm.entrypoints.openai.api_server as vllm_api_server

    engine_args = AsyncEngineArgs(
        model=MODEL_NAME,
        max_num_seqs=MAX_NUM_SEQS,
        quantization="awq",
        enforce_eager=True,
        dtype="float16",
        kv_cache_dtype="fp8_e5m2",
        # enable_prefix_caching=True,
        gpu_memory_utilization=0.95,
        max_model_len=MAX_MODEL_LEN,
    )

    served_model = "mixtral"
    response_role = "assistant"
    lora_modules = []
    chat_template = None

    engine = vllm_api_server.engine = AsyncLLMEngine.from_engine_args(engine_args)
    vllm_api_server.openai_serving_chat = OpenAIServingChat(
        engine, served_model, response_role, lora_modules, chat_template
    )

    vllm_api_server.openai_serving_completion = OpenAIServingCompletion(
        engine, served_model, lora_modules
    )

    @vllm_api_server.app.middleware("http")
    async def authentication(request, call_next):
        valid_api_key = os.environ["API_KEY"]

        if not request.url.path.startswith("/v1"):
            return await call_next(request)

        if request.headers.get("Authorization") != "Bearer " + valid_api_key:
            return JSONResponse(content={"error": "Unauthorized"}, status_code=401)

        return await call_next(request)

    return vllm_api_server.app
