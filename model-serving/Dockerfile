FROM vllm/vllm-openai:v0.5.0 as base


# Define the entrypoint
ENV MODEL_NAME julep-ai/Hermes-2-Theta-Llama-3-8B
ENV TP_SIZE 1
ENV MAX_MODEL_LEN 8192
ENV MAX_NUM_SEQS 1
ENV GPU_MEMORY_UTILIZATION 0.95
ENV DTYPE bfloat16
ENV MODEL_API_KEY myauthkey
ENTRYPOINT python3 -m vllm.entrypoints.openai.api_server --model $MODEL_NAME --tensor-parallel-size $TP_SIZE --enforce-eager --gpu-memory-utilization $GPU_MEMORY_UTILIZATION --max-model-len $MAX_MODEL_LEN --max-num-seqs $MAX_NUM_SEQS --dtype $DTYPE --trust-remote-code --api_key=$MODEL_API_KEY
