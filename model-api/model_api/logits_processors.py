import torch

from .tokens import tag_start_id_map

allowed_tag_start_token_id = list(tag_start_id_map.values())


def drop_disallowed_tokens(
    previously_generated_tokens: list[int],
    next_token_logits: torch.Tensor,
) -> torch.Tensor:
    if len(previously_generated_tokens) > 0:
        return next_token_logits

    next_token_logits_copy = next_token_logits.clone()

    # Creating a mask that is True for all elements except those at token indices of allowed
    mask = torch.ones_like(next_token_logits_copy, dtype=torch.bool)
    mask[allowed_tag_start_token_id] = False

    # Setting all except allowed to -inf
    next_token_logits_copy[mask] = float("-inf")

    return next_token_logits_copy
