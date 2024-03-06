import os

from modal import Image, Secret, Stub, asgi_app, gpu


###############
## Constants ##
###############

MODEL_DIR = "/model"
MODEL_NAME = "TheBloke/Nous-Hermes-2-Mixtral-8x7B-DPO-AWQ"


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
    secrets=[],
)
@asgi_app()
def get_app():
    from vllm.engine.arg_utils import AsyncEngineArgs
    from vllm.engine.async_llm_engine import AsyncLLMEngine
    from vllm.entrypoints.openai.serving_chat import OpenAIServingChat
    from vllm.entrypoints.openai.serving_completion import OpenAIServingCompletion

    import vllm.entrypoints.openai.api_server as vllm_api_server

    engine_args = AsyncEngineArgs(
        model=MODEL_NAME,
        max_num_seqs=1,
        quantization="awq",
        enforce_eager=True,
        dtype="float16",
        kv_cache_dtype="fp8_e5m2",
        # enable_prefix_caching=True,
        gpu_memory_utilization=0.95,
        max_model_len=4096,
    )

    served_model = "mixtral"
    response_role = "assistant"
    lora_modules = []
    chat_template = None

    engine = vllm_api_server.engine = AsyncLLMEngine.from_engine_args(engine_args)
    openai_serving_chat = vllm_api_server.openai_serving_chat = OpenAIServingChat(
        engine, served_model, response_role, lora_modules, chat_template
    )
    openai_serving_completion = (
        vllm_api_server.openai_serving_completion
    ) = OpenAIServingCompletion(engine, served_model, lora_modules)

    return vllm_api_server.app
