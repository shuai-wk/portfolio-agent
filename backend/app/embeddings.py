import math
import zlib
from typing import Protocol

from openai import OpenAI

from .config import Settings


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class MockEmbedder:
    def __init__(self, dim: int) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        for index, char in enumerate(text):
            vector[index % self.dim] += ord(char) / 255.0
        norm = max(1.0, sum(value * value for value in vector) ** 0.5)
        return [round(value / norm, 6) for value in vector]


class LexicalEmbedder:
    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        normalized = text.lower()
        for index in range(len(normalized) - 1):
            gram = normalized[index : index + 2]
            vector[zlib.crc32(gram.encode("utf-8")) % self.dim] += 1.0
        for index in range(len(normalized) - 2):
            gram = normalized[index : index + 3]
            vector[zlib.crc32(gram.encode("utf-8")) % self.dim] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class OpenAICompatibleEmbedder:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=self.model, input=text)
        return [float(value) for value in response.data[0].embedding]


def build_embedder(settings: Settings) -> Embedder:
    if settings.embedding_api_key and settings.embedding_model:
        return OpenAICompatibleEmbedder(
            settings.embedding_base_url,
            settings.embedding_api_key,
            settings.embedding_model,
        )
    return LexicalEmbedder()

