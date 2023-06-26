from textwrap import dedent
from pycozo.client import Client

cozo_client = Client("http", options={"host": "http://127.0.0.1:9070"})

import torch.nn.functional as F

from torch import Tensor
from transformers import AutoTokenizer, AutoModel


def average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-base-v2")
model = AutoModel.from_pretrained("intfloat/e5-base-v2")


def embed(batch: list[str], instruction: str):
    input_texts = [f"{instruction}: {text}" for text in batch]

    # Tokenize the input texts
    batch_dict = tokenizer(
        input_texts, max_length=512, padding=True, truncation=True, return_tensors="pt"
    )

    outputs = model(**batch_dict)
    embeddings = average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])

    # (Optionally) normalize embeddings
    embeddings = F.normalize(embeddings, p=2, dim=1)

    return embeddings.tolist()


def get_matching_beliefs(
    chatml,  #: ChatML,
    confidence=0.8,
    n=10,
    k=3,
    exclude_roles: list[str] = [],
):
    text = "\n".join(
        [
            f"{message.get('name', message['role'])}: {message['content']}"
            for message in chatml
            if message["role"] not in exclude_roles
        ]
    )

    radius = 1.0 - confidence
    [query_embedding] = embed([text], "passage")

    query = dedent(
        f"""
    ?[belief, valence, dist] := ~beliefs:embedding_space{{ belief, valence |
        query: vec({query_embedding}),
        k: {n},
        ef: 20,
        radius: {radius},
        bind_distance: dist
    }}

    :order -valence
    :order dist
    :limit {k}
    """
    )

    results = cozo_client.run(query)
    results = results["belief"].tolist()

    print(f"{len(results)} matching beliefs found for ```{text}```")

    return results


to_belief_chatml_msg = lambda bfs: dict(
    role="system", name="information", content=" ".join(bfs)
)
