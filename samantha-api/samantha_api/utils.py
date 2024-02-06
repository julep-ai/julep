from lmformatenforcer import CharacterLevelParser
from lmformatenforcer.integrations.vllm import (
    build_vllm_logits_processor, 
)
from lmformatenforcer.integrations.transformers import (
    build_token_enforcer_tokenizer_data,
)
from lmformatenforcer import TokenEnforcerTokenizerData
from typing import Union, List, Optional, Any
from vllm import SamplingParams, LLM
from pydantic import BaseModel
from jsonschema import validate


ListOrStrList = Union[str, List[str]]


_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Function name",
            },
            "description": {
                "type": "string",
                "description": "Function description",
            },
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                    },
                    "properties": {
                        "type": "object",
                    },
                    "required": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True,
                    },
                },
                "required": [
                    "type",
                    "properties",
                ],
            },
        },
        "required": [
            "name",
            "description",
            "parameters",
        ],
    },
}


def validate_functions(functions: list[dict]):
    validate(instance=functions, schema=_schema)


def build_vllm_token_enforcer_tokenizer_data(llm: LLM) -> TokenEnforcerTokenizerData:
    tokenizer = llm.get_tokenizer()
    # In some vLLM versions the tokenizer is wrapped in a TokenizerGroup
    if tokenizer.__class__.__name__ == 'TokenizerGroup':
        tokenizer = tokenizer.tokenizer  # noqa
    return build_token_enforcer_tokenizer_data(tokenizer)


def vllm_with_character_level_parser(
    engine: LLM,
    prompt: ListOrStrList,
    sampling_params: SamplingParams,
    request_id: str,
    parser: Optional[CharacterLevelParser] = None,
) -> ListOrStrList:
    tokenizer_data = build_vllm_token_enforcer_tokenizer_data(engine)
    
    if parser:
        logits_processor = build_vllm_logits_processor(tokenizer_data, parser)
        sampling_params.logits_processors = [logits_processor]

    results = engine.generate(prompt, sampling_params, request_id)
    if isinstance(prompt, str):
        return results[0].outputs[0].text
    else:
        return [result.outputs[0].text for result in results]


class FunctionCallResult(BaseModel):
    name: str
    arguments: dict[str, Any]
