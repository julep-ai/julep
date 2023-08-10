from textwrap import dedent
from pycozo.client import Client

cozo_client = Client("http", options={"host": "http://127.0.0.1:9070"})

import torch.nn.functional as F

from torch import Tensor
from transformers import AutoTokenizer, AutoModel

from .keywords import extract_keywords


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


to_belief_chatml_msg = lambda bfs: dict(
    role="system", name="information", content=" ".join(bfs)
)


def get_matching_beliefs(
    chatml,  #: ChatML,
    confidence: float = 0.8,
    n: int = 10,
    k: int = 2,
    window_size: int = 3,
    character_ids: list[str] = [],  # TODO
    exclude_roles: list[str] = [],
):
    # TODO: Hardcoded for now, Diwank's character id
    diwank_character_id = "d5f6a824-efbd-4945-b267-d9cd12cada77"
    # if diwank_character_id not in character_ids:
    #     return []

    # Extract text window from conversation chatml
    chatml = chatml[-window_size:]

    text = "\n".join(
        [
            f"{message.get('name', message['role'])}: {message['content']}"
            for message in chatml
            if message["role"] not in exclude_roles
        ]
    )

    # Prepare embedding for search
    radius = 1.0 - confidence
    [query_embedding] = embed([text], "passage")

    # TODO: Filter by characters
    # TODO: Apply mmr
    # Embedding search
    hnsw_query = dedent(
        f"""
    ?[belief, valence, dist, character_id] := ~beliefs:embedding_space{{ belief, valence, character_id |
        query: vec({query_embedding}),
        k: {n},
        ef: 20,
        radius: {radius},
        bind_distance: dist
    }}

    :order -valence
    :order dist
    """
    )

    # Embedding seach results
    hnsw_results = cozo_client.run(hnsw_query)

    # Now mix up for character_ids
    groups = [
        group.tolist() for _, group in hnsw_results.groupby(["character_id"])["belief"]
    ]

    k_hnsw_results = []
    i = 0
    while len(k_hnsw_results) < k and len(groups) > 0:
        group_idx = i % len(groups)
        group = groups[group_idx]

        if not len(group):
            groups.pop(group_idx)
            continue

        item = group.pop(0)
        k_hnsw_results.append(item)
        i += 1

    # FTS query
    keywords = " ".join([keyword for keyword, _ in extract_keywords(text)])

    # TODO: Filter by character_ids
    fts_query = dedent(
        f"""
    ?[belief, valence, score, character_id] := ~beliefs:summary {{ belief, valence, character_id |
        query: "{keywords}",
        k: {n},
        score_kind: 'tf_idf',
        bind_score: score
    }}
    
    :order -valence
    :order -score
    :limit {k}
    """
    )

    # Embedding seach results
    fts_results = cozo_client.run(fts_query)
    fts_results = fts_results["belief"].tolist()

    # Combine results
    results = k_hnsw_results + fts_results

    print(f"{len(results)} matching beliefs found for ```{text}```")

    return results
