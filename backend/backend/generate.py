import torch
from threading import Thread
from transformers import (
    LlamaForCausalLM,
    LlamaTokenizer,
    StoppingCriteriaList,
    StoppingCriteria,
    TextIteratorStreamer,
)


class StopOnTokens(StoppingCriteria):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._stop_token_ids = kwargs.get("stop_token_ids", [])

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs):
        for stop_id in self._stop_token_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False


def _convert_input(input_: dict) -> str:
    return input_


model_name = "julep-ai/samantha-13b-ds-03"
model = LlamaForCausalLM.from_pretrained(
    model_name, 
    device_map="auto", 
    torch_dtype=torch.bfloat16,
)
tokenizer = LlamaTokenizer.from_pretrained(
    model_name, 
    use_fast=False,
)  # Fast version is buggy


def generate(prompt, stopping_criteria: list[str] | None = None, **kwargs):
    stop_token_ids = []
    if stopping_criteria:
        stop_token_ids = tokenizer.convert_tokens_to_ids(stopping_criteria)

    inputs = tokenizer(
        _convert_input(prompt), 
        return_tensors="pt",
    ).to(0)

    stopping_criteria = StoppingCriteriaList([
        StopOnTokens(stop_token_ids=stop_token_ids),
    ])
    streamer = TextIteratorStreamer(tokenizer)

    generation_args = dict(
        inputs, 
        stopping_criteria=stopping_criteria, 
        streamer=streamer, 
        **kwargs,
    )
    thread = Thread(target=model.generate, kwargs=generation_args)
    thread.start()

    for idx, new_text in enumerate(streamer):
        if not idx:
            continue

        yield new_text
