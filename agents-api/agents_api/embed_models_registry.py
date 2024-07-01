import tiktoken
import numpy as np
from typing import TypedDict, Any
from dataclasses import dataclass
from tokenizers import Tokenizer
from agents_api.clients.model import openai_client
from agents_api.clients.embed import embed
from agents_api.exceptions import (
    ModelNotSupportedError,
    PromptTooBigError,
    UnknownTokenizerError,
)
from agents_api.env import docs_embedding_service_url


def normalize_l2(x):
    x = np.array(x)
    if x.ndim == 1:
        norm = np.linalg.norm(x)
        if norm == 0:
            return x
        return x / norm
    else:
        norm = np.linalg.norm(x, 2, axis=1, keepdims=True)
        return np.where(norm == 0, x, x / norm)


class EmbeddingInput(TypedDict):
    instruction: str | None
    text: str


@dataclass
class EmbeddingModel:
    embedding_service_url: str | None
    embedding_provider: str
    embedding_model_name: str
    original_embedding_dimensions: int
    output_embedding_dimensions: int
    context_window: int
    tokenizer: Any

    @classmethod
    def from_model_name(cls, model_name: str):
        try:
            return _embedding_model_registry[model_name]
        except KeyError:
            raise ModelNotSupportedError(model_name)

    def _token_count(self, text: str) -> int:
        tokenize = getattr(self.tokenizer, "tokenize", None)
        if tokenize:
            return len(tokenize(text))

        encode = getattr(self.tokenizer, "encode", None)
        if encode:
            return len(encode(text))

        raise UnknownTokenizerError

    def preprocess(self, inputs: list[EmbeddingInput]) -> list[str]:
        """Maybe use this function from embed() to truncate (if needed) or raise an error"""
        result: list[str] = []

        for i in inputs:
            instruction = i.get("instruction", "")
            sep = " " if len(instruction) else ""
            result.append(f"{instruction}{sep}{i['text']}")

        token_count = self._token_count(" ".join(result))
        if token_count > self.context_window:
            raise PromptTooBigError(token_count, self.context_window)

        return result

    async def embed(
        self, inputs: list[EmbeddingInput]
    ) -> list[np.ndarray | list[float]]:
        input = self.preprocess(inputs)
        embeddings: list[np.ndarray | list[float]] = []

        if self.embedding_provider == "julep":
            embeddings = await embed(
                input,
                embedding_service_url=self.embedding_service_url
                or docs_embedding_service_url,
                embedding_model_name=self.embedding_model_name,
            )
        elif self.embedding_provider == "openai":
            embeddings = (
                await openai_client.embeddings.create(
                    input=input, model=self.embedding_model_name
                )
                .data[0]
                .embedding
            )

        return self.normalize(embeddings)

    def normalize(
        self, embeddings: list[np.ndarray | list[float]]
    ) -> list[np.ndarray | list[float]]:
        return [
            (
                e
                if len(e) <= self.original_embedding_dimensions
                else normalize_l2(e[: self.original_embedding_dimensions])
            )
            for e in embeddings
        ]


_embedding_model_registry = {
    "text-embedding-3-small": EmbeddingModel(
        embedding_service_url=None,
        embedding_provider="openai",
        embedding_model_name="text-embedding-3-small",
        original_embedding_dimensions=1024,
        output_embedding_dimensions=1024,
        context_window=8192,
        tokenizer=tiktoken.encoding_for_model("text-embedding-3-small"),
    ),
    "text-embedding-3-large": EmbeddingModel(
        embedding_service_url=None,
        embedding_provider="openai",
        embedding_model_name="text-embedding-3-large",
        original_embedding_dimensions=1024,
        output_embedding_dimensions=1024,
        context_window=8192,
        tokenizer=tiktoken.encoding_for_model("text-embedding-3-large"),
    ),
    "Alibaba-NLP/gte-large-en-v1.5": EmbeddingModel(
        embedding_service_url=docs_embedding_service_url,
        embedding_provider="julep",
        embedding_model_name="Alibaba-NLP/gte-large-en-v1.5",
        original_embedding_dimensions=1024,
        output_embedding_dimensions=1024,
        context_window=8192,
        tokenizer=Tokenizer.from_pretrained("Alibaba-NLP/gte-large-en-v1.5"),
    ),
    "BAAI/bge-m3": EmbeddingModel(
        embedding_service_url=docs_embedding_service_url,
        embedding_provider="julep",
        embedding_model_name="BAAI/bge-m3",
        original_embedding_dimensions=1024,
        output_embedding_dimensions=1024,
        context_window=8192,
        tokenizer=Tokenizer.from_pretrained("BAAI/bge-m3"),
    ),
    "BAAI/llm-embedder": EmbeddingModel(
        embedding_service_url=docs_embedding_service_url,
        embedding_provider="julep",
        embedding_model_name="BAAI/llm-embedder",
        original_embedding_dimensions=1024,
        output_embedding_dimensions=1024,
        context_window=8192,
        tokenizer=Tokenizer.from_pretrained("BAAI/llm-embedder"),
    ),
}
