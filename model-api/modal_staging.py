import os

from modal import Image, Secret, Stub, asgi_app, gpu

## Needed so that modal knows to package this directory

import model_api  # noqa: F401


###############
## Constants ##
###############

MODEL_DIR = "/model"
BASE_MODEL = "julep-ai/samantha-1-turbo"


###########
## Tasks ##
###########


def download_model_to_folder():
    from huggingface_hub import snapshot_download
    from transformers.utils import move_cache

    os.makedirs(MODEL_DIR, exist_ok=True)

    snapshot_download(
        BASE_MODEL,
        local_dir=MODEL_DIR,
        token=os.environ["HF_TOKEN"],
    )
    move_cache()


###########
## Image ##
###########

image = (
    Image.from_registry("nvidia/cuda:12.1.1-base-ubuntu22.04", add_python="3.10")
    .apt_install()
    .pip_install(
        "transformers==4.38.1",
        "huggingface_hub==0.20.3",
        "hf-transfer==0.1.5",
    )
    # Use the barebones hf-transfer package for maximum download speeds. No progress bar, but expect 700MB/s.
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
    .run_function(
        download_model_to_folder,
        secrets=[
            Secret.from_name("huggingface-secret"),
            Secret.from_name("samantha-model-api"),
        ],
        timeout=60 * 20,
    )
    .pip_install(
        "vllm==0.3.2",
        "starlette-exporter==0.17.1",
        "environs==10.3.0",
        "pynvml==11.5.0",
        "sentry-sdk==1.40.6",
        "jsonschema==4.21.1",
        "lm-format-enforcer==0.8.3",
        "interegular==0.3.3",
        "pydantic[email]==2.6.3",
        "scikit-learn==1.4.0",
    )
    .copy_local_dir("./artifacts", "/root/artifacts")
)


################
## Entrypoint ##
################

stub = Stub("model-api", image=image)


@stub.function(
    gpu=gpu.L4(),
    container_idle_timeout=300,
    allow_concurrent_inputs=5,
    keep_warm=0,
    concurrency_limit=1,
    timeout=120,
    secrets=[
        Secret.from_name("huggingface-secret"),
        Secret.from_name("samantha-model-api"),
    ],
)
@asgi_app()
def get_app():
    from model_api.web import create_app

    assert os.environ["API_KEY"]
    REVISION = os.environ["REVISION"]
    BLOCK_SIZE = os.environ["BLOCK_SIZE"]
    MAX_MODEL_LEN = os.environ["MAX_MODEL_LEN"]
    MODEL_NAME = os.environ["MODEL_NAME"]

    app = create_app(
        [
            "--model",
            MODEL_NAME,
            "--tokenizer",
            MODEL_NAME,
            "--revision",
            REVISION,
            "--block-size",
            BLOCK_SIZE,
            "--max-model-len",
            MAX_MODEL_LEN,
            "--trust-remote-code",
        ]
    )

    return app
