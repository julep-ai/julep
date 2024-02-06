import os

from modal import Image, Secret, Stub, method, asgi_app

from samantha_api.web import create_app

MODEL_DIR = "/model"
BASE_MODEL = "julep-ai/samantha-1-turbo"


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


image = (
    Image.from_registry("nvidia/cuda:12.1.1-base-ubuntu22.04", add_python="3.10")
    .pip_install(
        "vllm==0.3.0",
        "huggingface_hub==0.20.3",
        "hf-transfer==0.1.5",
        "torch==2.1.2",
        "prometheus-client==0.19.0",
        "psutil==5.9.8",
        "starlette-exporter==0.17.1",
        "environs==10.3.0",
        "pynvml==11.5.0",
        "fastapi==0.109.2",
        "sentry-sdk==1.40.1",
        "jsonschema==4.21.1",
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
)

stub = Stub("example-vllm-inference", image=image)


@stub.function(
    gpu="A100",
    secrets=[
        Secret.from_name("huggingface-secret"),
        Secret.from_name("samantha-model-api"),
    ],
)
@asgi_app()
def get_app():
    API_KEY = os.environ["API_KEY"]
    REVISION = os.environ["REVISION"]
    BACKLOG = os.environ["BACKLOG"]
    BLOCK_SIZE = os.environ["BLOCK_SIZE"]
    MAX_MODEL_LEN = os.environ["MAX_MODEL_LEN"]
    MODEL_NAME = os.environ["MODEL_NAME"]

    app, args = create_app(
        [
            "--model",
            MODEL_NAME,
            "--tokenizer",
            MODEL_NAME,
            "--revision",
            REVISION,
            "--backlog",
            BACKLOG,
            "--block-size",
            BLOCK_SIZE,
            "--max-model-len",
            MAX_MODEL_LEN,
            "--trust-remote-code",
        ]
    )

    return app
