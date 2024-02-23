import re
import string
import random
from typing import AsyncIterator, Any

from interegular.patterns import _ParsePattern
from lmformatenforcer import CharacterLevelParser
from lmformatenforcer.integrations.vllm import (
    build_vllm_logits_processor,
)
from lmformatenforcer.integrations.transformers import (
    build_token_enforcer_tokenizer_data,
)
from lmformatenforcer import TokenEnforcerTokenizerData
from pydantic import BaseModel
from vllm import LLM
from vllm.outputs import RequestOutput

from .protocol import SamplingParams
from .conversion.datatypes import ChatML


ListOrStrList = str | list[str]

remove_last_space_re = re.compile(r"[^ ]+ {1}$")


def build_vllm_token_enforcer_tokenizer_data(tokenizer) -> TokenEnforcerTokenizerData:
    # In some vLLM versions the tokenizer is wrapped in a TokenizerGroup
    if tokenizer.__class__.__name__ == "TokenizerGroup":
        tokenizer = tokenizer.tokenizer  # noqa
    return build_token_enforcer_tokenizer_data(tokenizer)


def vllm_with_character_level_parser(
    engine: LLM,
    tokenizer,
    prompt: ListOrStrList,
    sampling_params: SamplingParams,
    request_id: str,
    parser: CharacterLevelParser | None = None,
) -> AsyncIterator[RequestOutput]:
    tokenizer_data = build_vllm_token_enforcer_tokenizer_data(tokenizer)

    if parser:
        logits_processor = build_vllm_logits_processor(tokenizer_data, parser)
        sampling_params.logits_processors = [logits_processor]

    return engine.generate(prompt, sampling_params, request_id)


class FunctionCallResult(BaseModel):
    name: str
    arguments: dict[str, Any]


def rescale_temperature(
    temperature: float,
    scaling_factor: float,
    power: float = 1.0,
) -> float:
    return (temperature**power) * scaling_factor


def validate_interegular_regex(pattern: str) -> bool:
    try:
        _ParsePattern(pattern).parse()
        return True
    except Exception:
        return False


def random_tool_id(n: int = 8) -> str:
    return "tool-" + "".join(random.choices(string.digits, k=n))


def remove_last_space(prompt: str):
    if remove_last_space_re.search(prompt):
        return prompt[:-1]

    return prompt


def flatten(lst):
    result = []
    for i in lst:
        if isinstance(i, list):
            result.extend(flatten(i))
        else:
            result.append(i)

    return result


def escape_special_tokens(messages: ChatML, tokens: list[str]):
    for m in messages:
        if m.content is None:
            continue

        for t in tokens:
            m.content = m.content.replace(t, f"{t[0]} {t[1:]}")
