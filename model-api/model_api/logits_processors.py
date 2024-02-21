import torch

from .function_classifier import classify_function_call
from .tokens import tag_start_id_map

allowed_tag_start_token_id = list(tag_start_id_map.values())


def drop_disallowed_start_tags(
    previously_generated_tokens: list[int],
    next_token_logits: torch.Tensor,
) -> torch.Tensor:
    """
    Logits processor that sets the next token logits to -inf for all tokens that
    do NOT correspond to allowed tag start tokens.
    """

    if len(previously_generated_tokens) > 0:
        return next_token_logits

    next_token_logits_copy = next_token_logits.clone()

    # Creating a mask that is True for all elements except those at token indices of allowed
    mask = torch.ones_like(next_token_logits_copy, dtype=torch.bool)
    mask[allowed_tag_start_token_id] = False

    # Setting all except allowed to -inf
    next_token_logits_copy[mask] = float("-inf")

    return next_token_logits_copy


def fix_function_call_prediction(
    previously_generated_tokens: list[int],
    next_token_logits: torch.Tensor,
) -> torch.Tensor:
    """
    Logits processor that either allows or disallows the generation of function calls.
    """

    if len(previously_generated_tokens) > 0:
        return next_token_logits

    next_token_logits_copy = next_token_logits.clone()
    is_function_call = classify_function_call(next_token_logits_copy)
    correct_tag_id = tag_start_id_map["function_call" if is_function_call else "me"]

    # Creating a mask that is True for all elements except the corrected tag
    mask = torch.ones_like(next_token_logits_copy, dtype=torch.bool)
    mask[correct_tag_id] = False

    # Setting all except allowed to negative inf
    next_token_logits_copy[mask] = float("-inf")

    return next_token_logits_copy
