from functools import cache
import os
import pickle

import torch

from .tokens import tag_start_id_map


@cache
def load_function_classifier(
    path: str = os.path.join(os.path.dirname(__file__), "./function_classifier.sklearn")
):
    """
    Load the classifier model from disk.
    """

    with open(path, "rb") as f:
        return pickle.load(f)


def classify_function_call(logit_tensor: torch.Tensor) -> bool:
    """
    Classify the input logit tensor as a function call or not.
    """

    # Load the classifier
    classifier = load_function_classifier()

    # Get input
    valid_tag_start_ids = list(tag_start_id_map.values())

    # Only get the logits for the valid tag start ids
    input = logit_tensor[valid_tag_start_ids]

    # Convert to numpy (bfloat16 is not supported by numpy)
    input = input.to(dtype=torch.float16).numpy()

    # Reshape since the classifier expects a 2D array
    # (1, -1) means 1 row and as many columns as needed
    input = input.reshape(1, -1)

    # Get prediction
    output = classifier.predict(input)
    prediction = output[0]
    prediction = bool(prediction)

    return prediction
