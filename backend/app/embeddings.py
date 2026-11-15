from typing import Protocol


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

